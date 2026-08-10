#!/usr/bin/env python3
"""PreToolUse hook: catch dependency versions being written from memory.

The failure this exists for is silent. A version that was current when the model
was trained still looks right in a diff -- nobody notices until CI breaks or a
CVE lands. So instead of trusting the model to remember the rule, detect the
moment it is about to write a pin and put the rule back in front of it.

Reminds by default. Set CPDK_VERSION_GUARD=block to make it a hard stop instead;
blocking is stricter but a false positive stalls real work, so it is opt-in.

Silent no-op on any failure: a broken guard must never wedge the Write tool.
"""

import json
import os
import re
import sys

# High-signal shapes only. A bare number, a date, or a version inside prose does
# not fire -- the cost of a false positive here is an interrupted edit.
PATTERNS = [
    # The leading `- ` matters: in a workflow, `uses:` is nearly always a YAML
    # list item, and without it this misses the single most common case.
    (re.compile(r"^\s*-?\s*uses:\s*\S+@[\w.\-]+", re.M), "action pin (uses:)"),
    (re.compile(r"^\s*(?:FROM|image:)\s+\S+:[\w.\-]+", re.M | re.I), "container tag"),
    # `"version"` itself is excluded: that key is the file's *own* version --
    # every plugin.json or package.json bump tripped this before, and a guard
    # that fires on routine bumps gets ignored by the time it matters.
    (re.compile(r'"(?!version")[^"\s]+"\s*:\s*"[~^>=<]*\d+\.\d+[\w.\-]*"'), "npm-style dependency"),
    (re.compile(r"^\s*[\w.\-]+\s*(?:==|>=|~=)\s*\d+\.\d+", re.M), "python requirement"),
    (re.compile(r'^\s*version\s*=\s*"[~^>=<]*\d+\.\d+', re.M), "version = pin"),
    # `version = "..."` has its own rule above; excluding it here keeps a single
    # line from being reported twice.
    (re.compile(r'^\s*(?!version\b)[\w\-]+\s*=\s*"\d+(?:\.\d+)*"\s*$', re.M), "mise/toml runtime pin"),
    # Cargo's other dependency shape: `serde = { version = "1.0", ... }`.
    (re.compile(r'\{[^{}\n]*\bversion\s*=\s*"[~^>=<]*\d+\.\d+'), "cargo inline pin"),
    # Module paths always contain a slash (github.com/x/y); requiring one keeps
    # prose like "upgrade gin v1.10.0" from firing.
    (re.compile(r"^\s*(?:require\s+)?[\w.\-]+(?:/[\w.\-]+)+\s+v\d+\.\d+\.\d+", re.M), "go module pin"),
    (re.compile(r"""^\s*gem\s+['"][\w\-]+['"]\s*,\s*['"][~><=\s]*\d+\.\d+""", re.M), "gem pin"),
    (re.compile(r"\b[\w@/.\-]+@\d+\.\d+\.\d+\b"), "pkg@x.y.z"),
    (re.compile(r'^\s*(?:chart|appVersion|targetRevision):\s*"?v?\d+\.\d+', re.M), "chart/gitops pin"),
]

REMINDER = """This write pins dependency versions: {found}.

Before it lands, confirm each against the source of truth rather than memory --
`api.github.com/repos/<o>/<r>/releases/latest`, the registry's tag list,
`npm view <pkg> version`, `mise ls-remote <tool>`. Training data goes stale here
and the mistake is invisible in review.

If you already checked these in this session, say so and carry on. If you cannot
reach the network, keep the value but tell the user it is unverified."""


def content_of(payload: dict) -> str:
    tool = payload.get("tool_name") or ""
    src = payload.get("tool_input") or {}
    if tool == "Write":
        return src.get("content") or ""
    if tool == "Edit":
        return src.get("new_string") or ""
    if tool == "NotebookEdit":
        return src.get("new_source") or ""
    return ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    text = content_of(payload)
    if not text:
        return

    found = []
    for pattern, label in PATTERNS:
        if pattern.search(text) and label not in found:
            found.append(label)
    if not found:
        return

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": REMINDER.format(found=", ".join(found)),
        },
        "suppressOutput": True,
    }

    if os.environ.get("CPDK_VERSION_GUARD") == "block":
        out["hookSpecificOutput"]["permissionDecision"] = "ask"
        out["hookSpecificOutput"]["permissionDecisionReason"] = (
            "Unverified version pin ({}). Check it against the registry first.".format(
                ", ".join(found)
            )
        )

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
