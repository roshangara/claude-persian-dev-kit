#!/usr/bin/env python3
"""Trigger tests for the verify-first prompt hook.

Run from anywhere: `python3 tests/test-verify-first.py`. No framework, exit 1 on
the first failure summary.

The cases that matter most are the ZWNJ ones. Persian compounds join with a
space, a ZWNJ (U+200C) or nothing — «می‌خوام», «می خوام», «میخوام» are one word
— and \\s does not match ZWNJ, so a pattern written with \\s* alone silently
misses the most standard spelling. That bug shipped in 0.3.0.
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "..", "plugins", "verify-first", "hooks", "verify-first.py")

spec = importlib.util.spec_from_file_location("verify_first", HOOK)
vf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vf)

ZWNJ = "‌"

# (prompt, should research-first fire)
CASES = [
    # ZWNJ spellings — the standard way Persian is actually typed.
    ("می" + ZWNJ + "خوام یه DNS داخلی راه" + ZWNJ + "اندازی کنم", True),
    ("می" + ZWNJ + "خوایم logging مرکزی پیاده" + ZWNJ + "سازی کنیم", True),
    ("راه" + ZWNJ + "حل چیه برای کش کردن؟", True),
    ("به" + ZWNJ + "روزترین نسخه node چنده؟", True),
    # Space and joined spellings of the same words.
    ("می خوام یه DNS داخلی راه اندازی کنم", True),
    ("میخوام یه message queue نصب کنم", True),
    # Other Persian intent shapes.
    ("باید یه job scheduler نصب کنیم", True),
    ("قراره یه مانیتورینگ از صفر بسازیم", True),
    ("به یه ابزار backup نیاز داریم", True),
    ("کدوم queue بهتره؟", True),
    ("چی استفاده کنم برای صف؟", True),
    # English asking and building shapes.
    ("I want to implement DNS", True),
    ("we need a job scheduler", True),
    ("which database should we use", True),
    ("is redis deprecated?", True),
    ("let's set up centralized logging", True),
    # Ordinary work must NOT fire, even when it contains a build word.
    ("fix the install script", False),
    ("run the deploy and show me the log", False),
    ("این خطا رو ببین چرا کار نمی" + ZWNJ + "کنه", False),
    ("این فایل رو یه نگاه بنداز", False),
    ("کاری که روی پروژه کردیم رو بررسی کن ببین درست هست یا نه", False),
    ("commit and push", False),
]


def fires(prompt: str) -> bool:
    choosing = vf.ASKS_FOR_A_CHOICE.search(prompt) or vf.INTENDS_TO_BUILD.search(prompt)
    return bool(choosing and not vf.ORDINARY_WORK.search(prompt))


def main() -> int:
    failed = 0
    for prompt, want in CASES:
        got = fires(prompt)
        if got != want:
            failed += 1
            print(f"FAIL want={want} got={got}  {prompt!r}")
    total = len(CASES)
    print(f"{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
