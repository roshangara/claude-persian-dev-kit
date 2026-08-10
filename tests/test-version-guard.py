#!/usr/bin/env python3
"""Pattern tests for the version-guard PreToolUse hook.

Run from anywhere: `python3 tests/test-version-guard.py`.

Two properties matter. Every real dependency-pin shape must be caught — that is
the plugin's whole job. And the file's *own* version must not be: a guard that
fires on every plugin.json bump trains everyone to ignore it.
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "..", "plugins", "verify-first", "hooks", "version-guard.py")

spec = importlib.util.spec_from_file_location("version_guard", HOOK)
vg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vg)

# (name, content, labels that must fire — [] means nothing may fire)
CASES = [
    ("uses list item", "      - uses: actions/checkout@v4", ["action pin (uses:)"]),
    ("dockerfile FROM", "FROM node:22-alpine", ["container tag"]),
    ("compose image", "    image: postgres:17.2", ["container tag"]),
    ("package.json dep", '    "react": "^18.2.0",', ["npm-style dependency"]),
    ("requirements.txt", "requests==2.31.0", ["python requirement"]),
    ("pyproject pin", 'version = "5.31.0"', ["version = pin"]),
    ("mise runtime", 'node = "22.11.0"', ["mise/toml runtime pin"]),
    ("cargo inline table", 'serde = { version = "1.0", features = ["derive"] }', ["cargo inline pin"]),
    ("go.mod require", "require github.com/gin-gonic/gin v1.10.0", ["go module pin"]),
    ("go.mod block line", "\tgithub.com/spf13/cobra v1.8.1", ["go module pin"]),
    ("Gemfile", 'gem "rails", "~> 7.1.3"', ["gem pin"]),
    ("helm chart.yaml", "appVersion: 1.16.0", ["chart/gitops pin"]),
    ("npx pin in a script", "npx prettier@3.3.2 --write .", ["pkg@x.y.z"]),
    # Own version, prose, and dates stay silent.
    ("own version bump", '  "version": "0.4.0",', []),
    ("plain prose", "release notes for the 2.5 series improved 3.14 handling", []),
    ("a date and a time", "backup ran 2026-08-10 at 02:30", []),
    ("go-looking prose", "upgrade gin v1.10.0 when you get a chance", []),
]


def hits(text: str) -> list:
    found = []
    for pattern, label in vg.PATTERNS:
        if pattern.search(text) and label not in found:
            found.append(label)
    return found


def main() -> int:
    failed = 0
    for name, text, want in CASES:
        got = hits(text)
        ok = set(want) <= set(got) if want else got == []
        if not ok:
            failed += 1
            print(f"FAIL {name}: want {want}, got {got}")
    total = len(CASES)
    print(f"{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
