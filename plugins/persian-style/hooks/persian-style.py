#!/usr/bin/env python3
"""UserPromptSubmit hook: inject the Persian writing-style guide, but only when
the prompt is actually in Persian.

Why a hook and not CLAUDE.md: a style rule has to apply to the first sentence of
every Persian answer. Loaded once at session start it fades -- in the session
that prompted this, the rule was in CLAUDE.md and the answer still came out in
literary register. Re-injecting it next to the message it governs fixes that,
and costs nothing on English-only sessions.

Silent no-op on any failure: a broken style hook must never block a prompt.
"""

import json
import os
import re
import sys

# Relative to this file, not to $HOME: ${CLAUDE_PLUGIN_ROOT} changes on every
# plugin update, so nothing here may hardcode an absolute path.
GUIDE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "style", "persian.md"
)

# Arabic, Arabic Supplement/Extended-A, Presentation Forms A/B. Escapes rather
# than literal characters: the ranges are invisible or unrenderable in a source
# file, and a stray one is impossible to spot by eye.
# Deliberately excluded: U+200C (ZWNJ) and U+FEFF (BOM), both of which turn up in
# pasted text that is otherwise entirely English.
PERSIAN = re.compile(
    "[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-ﻼ]"
)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    prompt = payload.get("prompt") or ""
    if not PERSIAN.search(prompt):
        return

    try:
        with open(GUIDE, encoding="utf-8") as fh:
            guide = fh.read()
    except OSError:
        return

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": guide,
            },
            "suppressOutput": True,
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
