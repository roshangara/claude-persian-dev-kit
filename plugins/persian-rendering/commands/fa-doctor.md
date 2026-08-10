---
description: Check the Persian rendering patch end to end and report what, if anything, is broken
---

Diagnose the persian-rendering patch on this machine. Work through the checks
below with shell commands, then report — in the language the user has been
writing — what is healthy and what is not, with the one fix for anything broken.
Do not change any file except by re-running the patcher itself.

1. **Find the patcher and run it verbosely.** It ships with this plugin:

   ```
   ls ~/.claude/plugins/cache/*/persian-rendering/*/scripts/apply-patch.sh
   ```

   Run the newest match with `CPDK_VERBOSE=1` and show its output. It names
   every extension directory it patched, says `patched plan preview` or why
   not, and exits 0 even when it finds nothing.

2. **Confirm the patch is on disk.** For each extension directory the patcher
   named (or, if it named none, each `anthropic.claude-code-*` directory under
   the usual extension roots):

   ```
   grep -c 'fa-bidi-patch' <ext>/webview/index.css <ext>/webview/index.js <ext>/extension.js
   ```

   Expected: 2 in each webview file (a BEGIN and an END marker), 4 in
   `extension.js` (stylesheet and script each carry a pair). Also confirm
   `<ext>/webview/Vazirmatn-NL-var.woff2` exists.

3. **Check `python3` is on PATH** — without it the chat panel is patched but
   the plan preview is not.

4. **Interpret the result.**
   - Patcher found no extension: the editor keeps extensions somewhere else.
     Ask the user where, suggest setting `CPDK_EXTENSIONS_DIR` to it.
   - Markers present but the panel still shows the wrong font: the browser is
     holding the old bundle — the fix is `Developer: Reload Window`, nothing
     else.
   - `plan preview not patched`: the extension changed the plan template;
     the patcher restored the original on purpose. Ask the user to open an
     issue at https://github.com/roshangara/claude-persian-dev-kit with the
     extension version from the directory name.
   - Everything present: say so, and remind that a window reload is needed
     once after the first patch of each new extension version.
