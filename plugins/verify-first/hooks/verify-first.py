#!/usr/bin/env python3
"""UserPromptSubmit hook: keep the two verification rules next to the prompt.

Loaded once at session start these fade; re-injected per prompt they don't.
That is the whole reason this is a hook and not a CLAUDE.md paragraph.

Silent no-op on any failure: this must never block a prompt.
"""

import json
import os
import sys

RULES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "context", "verify-first.md"
)


def main() -> None:
    try:
        json.load(sys.stdin)
    except Exception:
        return

    try:
        with open(RULES, encoding="utf-8") as fh:
            rules = fh.read()
    except OSError:
        return

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": rules,
            },
            "suppressOutput": True,
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
