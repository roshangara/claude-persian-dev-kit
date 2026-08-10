#!/usr/bin/env python3
"""Patch the plan preview webview inside the extension host bundle.

The chat panel is one webview and `apply-patch.sh` fixes it by appending to
`webview/index.css` and `webview/index.js`. The plan preview -- the tab Claude
Code opens for "Ready for review" -- is a *second* webview whose entire HTML
document, stylesheet included, is a template literal inside `extension.js`.
Nothing in the webview directory is involved, which is why Persian was correct
in the session and wrong in the plan.

Three edits to that one template, located from a CSP string that appears exactly
once in the bundle:

  1. `font-src data:` added to the CSP, so an @font-face can load at all
  2. the stylesheet appended to the template's own <style>
  3. fa-bidi.js -- the same measuring script the chat panel gets -- added as a
     <script nonce="{{NONCE}}"> before </body>

The nonce placeholder is safe to write: the extension fills every occurrence
with `replaceAll` when it builds the HTML.

Usage: patch-plan-webview.py <extension.js.orig> <extension.js> <assets dir>

Exits 0 and touches nothing when the bundle does not look like it should -- a
future release that renames or restructures this template must not leave a
half-patched file behind.
"""

import base64
import re
import sys
from pathlib import Path

CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; "
    "script-src 'nonce-{{NONCE}}'; img-src data:;"
)
CSP_PATCHED = CSP.replace("img-src data:;", "img-src data:; font-src data:;")

MARKER = "===== BEGIN fa-bidi-patch ====="


def for_template_literal(text: str) -> str:
    """Escape text so a JS template literal reproduces it character for character.

    The assets land inside a backtick string, where three things are not
    literal. A backtick ends it and a ${ starts an interpolation -- both obvious.
    The third is not: a template literal also processes escapes, and an unknown
    one collapses to the bare letter, so the regex /\\S/ in fa-bidi.js would
    reach the webview as /S/ and match every character instead of every
    non-space. Backslashes go first, or the escapes added below get escaped too.
    """
    return text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: patch-plan-webview.py <src> <dst> <assets>", file=sys.stderr)
        return 2

    src, dst, assets = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])

    try:
        bundle = src.read_text(encoding="utf-8")
        css = (assets / "fa-plan.css").read_text(encoding="utf-8")
        js = (assets / "fa-bidi.js").read_text(encoding="utf-8")
        font = base64.b64encode((assets / "Vazirmatn-NL-var.woff2").read_bytes())
    except OSError as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 1

    # Exactly once, or this is not the bundle this was written against. The main
    # panel's CSP is assembled from variables and cannot collide with a literal.
    if bundle.count(CSP) != 1:
        print(
            f"plan preview CSP found {bundle.count(CSP)} times, expected 1 "
            "-- skipping the plan webview",
            file=sys.stderr,
        )
        return 1

    anchor = bundle.index(CSP)

    style_close = bundle.find("</style>", anchor)
    body_close = bundle.find("</body>", anchor)
    if style_close < 0 or body_close < 0 or body_close < style_close:
        print("plan preview template has an unexpected shape -- skipping", file=sys.stderr)
        return 1

    css = css.replace("__FONT_BASE64__", font.decode("ascii"))

    # A stray </script> inside the injected source would end the tag early. The
    # asset has none today; assert rather than trust it forever.
    if re.search(r"</\s*script", js, re.IGNORECASE):
        print("fa-bidi.js contains a closing script tag -- skipping", file=sys.stderr)
        return 1

    css = for_template_literal(css)
    script = (
        '<script nonce="{{NONCE}}">\n' + for_template_literal(js) + "\n</script>\n"
    )

    # Both offsets come from the same untouched string, so splice in one pass
    # rather than editing twice and shifting the second offset.
    out = (
        bundle[:style_close]
        + css
        + bundle[style_close:body_close]
        + script
        + bundle[body_close:]
    )
    out = out.replace(CSP, CSP_PATCHED, 1)

    # One BEGIN marker from each injected asset, and no placeholder left behind.
    if out.count(MARKER) != 2 or "__FONT_BASE64__" in out or CSP_PATCHED not in out:
        print("injection produced an unexpected result -- skipping", file=sys.stderr)
        return 1

    try:
        dst.write_text(out, encoding="utf-8")
    except OSError as exc:
        print(f"cannot write {dst}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
