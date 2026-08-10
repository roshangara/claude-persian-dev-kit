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

# Persian compounds join with a space, a ZWNJ (U+200C), or nothing at all --
# «می‌خوام», «می خوام» and «میخوام» are the same word. \s does not match ZWNJ
# (it is a format character, not whitespace), so every joint in a Persian
# pattern must allow all three. The escape rather than the literal: ZWNJ is
# invisible in source and a stray one is impossible to spot by eye.
J = r"[\s‌]*"

# Asking for a choice outright: "which one", "what's best", "recommend".
ASKS_FOR_A_CHOICE = re.compile(
    rf"""
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
    | راهکار | راه{J}حل
    | جدیدتر | به{J}روزتر | آخرین\s+نسخه | منسوخ
    """,
    re.I | re.X,
)

# Intending to build something. "I want to implement DNS" is a technology choice
# with no question mark in it and none of the words above -- and it is the most
# common way the choice actually arrives. Missing these was the real gap.
INTENDS_TO_BUILD = re.compile(
    rf"""
      (?:want\s+to|need\s+to|going\s+to|plan(?:ning)?\s+to|let'?s|
         help\s+me|how\s+do\s+i|how\s+can\s+i)
      \s+ (?:\w+\s+){{0,3}}?
      (?:set\s*up|setup|build|implement|deploy|install|configure|stand\s+up|
         spin\s+up|add|introduce|create|migrate|replace|host|run)
    | \bwe\s+need\s+(?:a|an|some)\b
    | \bfrom\s+scratch\b
    | (?:می{J}خوا(?:م|هم|یم|هیم|ستم)|باید|لازمه|قراره|بیا(?:ید)?\b|
         نیاز\s+داریم|کمکم\s+کن)
      [\s\S]{{0,40}}?
      (?:پیاده{J}سازی|راه{J}بند|راه{J}انداز|بالا\s*بیار|ست{J}آپ|
         نصب\s+کن|مستقر|اضافه\s+کن|جایگزین|از\s+صفر|بساز)
    | نیاز\s+داریم
    """,
    re.I | re.X,
)

# Ordinary work that happens to contain a build word. "fix the script that
# installs X" is not a technology choice. Cheaper to exclude these than to
# tighten the patterns above until they start missing real cases.
ORDINARY_WORK = re.compile(
    r"""
      ^\s*(?:fix|debug|run|read|show|explain|commit|push|rename|revert|
             format|lint|test)\b
    | \b(?:typo|این\s+خطا|این\s+ارور|چرا\s+کار\s+نمی)\b
    | ^\s*(?:این|اون)\s+(?:فایل|خط|تابع|بخش)
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
    choosing = ASKS_FOR_A_CHOICE.search(prompt) or INTENDS_TO_BUILD.search(prompt)
    if choosing and not ORDINARY_WORK.search(prompt):
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
