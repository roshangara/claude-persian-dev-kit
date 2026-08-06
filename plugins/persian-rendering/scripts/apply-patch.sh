#!/usr/bin/env bash
# Patch the Claude Code VS Code extension so Persian renders correctly in the
# panel: a bundled Persian webfont, and per-block direction decided by counting
# rather than by the first strong character.
#
# Idempotent. Every run rebuilds from a pristine .orig copy, so it is safe to
# call on every session start -- which is the point: the extension updates
# roughly daily and each update replaces the files this patches.
#
# Exits 0 when there is nothing to patch. This runs as a SessionStart hook and
# most machines that install the plugin will not have the extension at all.

set -uo pipefail

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS="$(cd "$SELF/../assets" && pwd)"

log() { [ -n "${CPDK_VERBOSE:-}" ] && printf '%s\n' "$*" >&2; return 0; }

# Every place a VS Code family editor keeps extensions. CPDK_EXTENSIONS_DIR
# overrides the lot, for a code-server started with --extensions-dir.
roots=()
if [ -n "${CPDK_EXTENSIONS_DIR:-}" ]; then
  roots+=("$CPDK_EXTENSIONS_DIR")
else
  roots+=(
    "$HOME/.local/share/code-server/extensions"
    "$HOME/.vscode-server/extensions"
    "$HOME/.vscode-server-insiders/extensions"
    "$HOME/.vscode/extensions"
    "$HOME/.vscode-insiders/extensions"
    "$HOME/.cursor/extensions"
    "$HOME/.windsurf/extensions"
  )
fi

shopt -s nullglob
patched=0

for root in "${roots[@]}"; do
  [ -d "$root" ] || continue

  for ext in "$root"/anthropic.claude-code-*/; do
    css="$ext/webview/index.css"
    js="$ext/webview/index.js"
    [ -f "$css" ] && [ -f "$js" ] || continue
    [ -w "$css" ] && [ -w "$js" ] || { log "not writable, skipping: $ext"; continue; }

    # One pristine copy per extension version. Written once, then treated as the
    # source of truth -- never patch a patched file.
    [ -f "$css.orig" ] || cp -p "$css" "$css.orig"
    [ -f "$js.orig" ] || cp -p "$js" "$js.orig"

    cp -f "$ASSETS/Vazirmatn-NL-var.woff2" "$ext/webview/" || continue

    cp -f "$css.orig" "$css" && cat "$ASSETS/fa-bidi.css" >> "$css"
    cp -f "$js.orig" "$js" && cat "$ASSETS/fa-bidi.js" >> "$js"

    patched=$((patched + 1))
    log "patched: $(basename "$ext")"
  done
done

if [ "$patched" -eq 0 ]; then
  log "no Claude Code extension found; nothing to do"
  exit 0
fi

log "patched $patched extension(s) -- reload the window to see it"
exit 0
