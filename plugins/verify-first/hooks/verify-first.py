#!/usr/bin/env python3
"""UserPromptSubmit hook: put the right verification rule next to the prompt.

Two rules, two different costs, so two different triggers.

claim-check is nine lines and applies to almost any request, so it goes in every
time. research-first is a page and only earns its place when the user is
actually asking you to choose something — injected on every prompt it becomes
noise, and a rule that reads as noise gets ignored within a day. That is the
failure mode this file exists to avoid.

Silent no-op on any failure: this must never block a prompt.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONTEXT = os.path.join(HERE, "..", "context")

# Prompts that are asking for a choice, in English and Persian. Tuned to fire on
# "which should I use" and not on "fix this typo" -- a false positive costs a
# page of context and trains the reader to skim past it.
ASKS_FOR_A_CHOICE = re.compile(
    r"""
      recommend | suggest | \bbest\b | \bbetter\b | alternative
    | should\s+(?:i|we|it)\s+(?:use|pick|choose|go)
    | which\s+\w+\s+(?:should|do\s+you|would)
    | what(?:'s|\s+is)\s+the\s+(?:best|right|recommended|standard)
    | compare\b | \bvs\.?\b | \bversus\b
    | latest\s+version | up\s*-?\s*to\s*-?\s*date | deprecated | superseded
    | \bmigrate\s+to\b | \bswitch\s+to\b
    | پیشنهاد | توصیه | بهترین | بهتره | جایگزین | مقایسه
    | کدوم | کدام
    | چی\s+(?:استفاده|بزن|بذار|انتخاب)
    | راهکار | راه\s*حل
    | جدیدتر | به\s*روزتر | آخرین\s+نسخه | منسوخ
    """,
    re.I | re.X,
)


def read(name: str) -> str:
    try:
        with open(os.path.join(CONTEXT, name), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    prompt = payload.get("prompt") or ""

    parts = [read("claim-check.md")]
    if ASKS_FOR_A_CHOICE.search(prompt):
        parts.append(read("research-first.md"))

    context = "\n\n---\n\n".join(p for p in parts if p)
    if not context:
        return

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            },
            "suppressOutput": True,
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
