# Changelog

Each plugin versions independently; entries here group what shipped together.

## 2026-08-11 — persian-rendering 0.3.3

- **A number after a Latin word no longer jumps in front of it.** "این فاز روی
  shahab ۲ دقیقه طول کشید" was rendering as "این فاز روی ۲ shahab دقیقه" — the
  number read as though it belonged to whatever came before. Unicode's rule W7
  hands a number to the last strong character before it, so the number joined the
  Latin word's left-to-right run, and that run lays out internally with the number
  on the word's right, which is where a right-to-left reader arrives first.
  Nothing to do with Persian digits: `۲` and `2` are both bidi class EN and both
  did it. The word is now isolated, which puts the number back on its left.
  Only that shape is wrapped — a Latin word with a number right after it — not
  every Latin run, and the text itself is untouched, so copying a message still
  gives exactly what it gave before.

### فارسی

«این فاز روی shahab ۲ دقیقه طول کشید» رندر می‌شد «این فاز روی ۲ shahab دقیقه».
قانون W7 یونیکد عدد رو می‌چسبونه به آخرین حرف قوی قبلش، یعنی عدد جذب کلمه‌ی
لاتین می‌شد و ته اون تیکه‌ی چپ‌به‌راست می‌نشست — سمت راستِ کلمه، همون‌جایی که
چشم فارسی‌خون اول می‌رسه. ربطی به فارسی بودن رقم نداشت؛ `۲` و `2` هر دو همین
کار رو می‌کردن. حالا کلمه‌ی لاتین isolate می‌شه و عدد برمی‌گرده سر جاش.

## 2026-08-11 — persian-rendering 0.3.2

- **The caret no longer strands itself across the composer.** Press Enter in the
  input and the browser wraps the new line in a bare `<div>`. `unicode-bidi` is
  not an inherited property, so that div kept the element's `ltr` while the
  visible mirror layer — one text node under the plaintext rule — drew the same
  line right-to-left. The caret sat the width of the composer away from its own
  glyphs: clicking never reached the text, and the only way out was to cut the
  text, paste it back, and hope. Measured at 584px in the report that found it.
  Blocks inside the editable now get the same rule. Mention chips are left
  alone deliberately — they are spans the editable has no counterpart for.

### فارسی

تو اینپوت که Enter می‌زدی، مرورگر خط جدید رو تو یه `<div>` می‌پیچید. چون
`unicode-bidi` ارث نمی‌رسه، اون div چپ‌به‌راست می‌موند و خط فارسی داخلش می‌رفت
چپ — درحالی‌که لایه‌ی مرئی همون خط رو راست می‌کشید. یعنی caret به عرض یه
اینپوت از متن خودش فاصله می‌گرفت و هر جا کلیک می‌کردی نمی‌رسید بهش. حالا
بلاک‌های داخل اینپوت هم همون قاعده رو می‌گیرن.

## 2026-08-10 — persian-rendering 0.3.1

- The app renders bidi control characters (RLM, LRM, the isolate pair) as
  visible `\uXXXX` escape text — a deliberate spoofing defence in its
  sanitizer. Models sprinkle exactly those marks into Persian output, so
  answers arrived dotted with six-character noise. Direction is measured per
  block here, which makes the marks pointless: the escape text is now removed
  from prose. Inside backticks it survives, for when the character itself is
  the topic. Only the uppercase-hex form the sanitizer emits is touched.

### فارسی

اون `\uXXXX`هایی که وسط جواب فارسی سبز می‌شدن، متنِ اسکیپ‌شده‌ی همون
کاراکترهای کنترلی جهت بودن — خود اکستنشن عمداً نشونشون می‌ده که کسی باهاشون
متن جعل نکنه. چون جهت رو این plugin خودش حساب می‌کنه، این علامت‌ها به هیچ
دردی نمی‌خورن؛ از نثر پاک می‌شن. تو بک‌تیک بمونه، می‌مونه.

## 2026-08-10 — persian-rendering 0.3.0 · persian-style 0.2.0 · verify-first 0.4.0

### persian-rendering 0.3.0

- **The plan preview is patched too** (landed as 0.2.0 earlier the same day).
  It is a second webview whose HTML lives as a template literal inside
  `extension.js`, so the chat-panel patch never reached it. Same font and
  direction treatment, with the font inlined as a `data:` URI because that
  webview's CSP allows nothing else.
- **Your configured fonts survive the patch.** The stylesheet used to replace
  the panel's font variables with a hardcoded stack, which threw away whatever
  you had set — a Fira Code setting died the moment the patch landed. The
  script now reads the real `--vscode-*` values and rebuilds the stacks with
  Vazirmatn slotted in just before the generic family, so it only ever
  supplies the Arabic-script glyphs nothing earlier in the list has.
- The patcher also looks in the VSCodium (`~/.vscode-oss`) and
  openvscode-server extension directories.
- New `/fa-doctor` command: re-runs the patcher verbosely, greps the patch
  markers, checks `python3`, and names the failing step instead of leaving you
  to bisect font problems by hand.

### persian-style 0.2.0

- Persian inside code fences or inline code no longer triggers the guide. An
  English message that pastes a Persian error string keeps its English answer.
- The guide gained its missing boundary: the spoken register is for the chat
  only — commit messages, code comments, docs and issue text follow the repo's
  own language and tone.

### verify-first 0.4.0

- **The Persian trigger patterns now understand ZWNJ.** «می‌خوام»، «می خوام»
  and «میخوام» are one word, but `\s` does not match the half-space, so the
  patterns missed the standard spelling of exactly the words they were written
  for. Every joint now accepts space, ZWNJ, or nothing.
- New intent openers: «قراره»، «بیا»، «نیاز داریم».
- version-guard covers three more ecosystems: Cargo inline tables
  (`{ version = "1.0" }`), `go.mod` require lines, and Gemfile `gem` pins.
- version-guard no longer fires on a bare `"version"` key — that is the file's
  *own* version, and a guard that trips on every routine `plugin.json` bump
  trains everyone to skim past it.
- First test suites: `tests/test-verify-first.py` (22 trigger cases, ZWNJ
  first) and `tests/test-version-guard.py` (17 pattern cases, catches and
  exemptions both).

### فارسی

فونتی که خودت تنظیم کردی دیگه دور ریخته نمی‌شه؛ وزیرمتن فقط گلیف فارسی رو پر
می‌کنه. الگوهای فارسی verify-first حالا نیم‌فاصله رو می‌فهمن — «می‌خوام» هم
trigger حساب می‌شه، که قبلاً نمی‌شد. فارسیِ داخل code block هم دیگه جواب رو
فارسی نمی‌کنه. برای عیب‌یابی رندر هم `/fa-doctor` اضافه شده که کل زنجیره رو چک
می‌کنه و می‌گه کجا خرابه.

## 2026-08-06 — first release

- persian-rendering 0.1.1: bundled Vazirmatn (Non-Latin build), per-block
  direction decided by counting strong characters instead of trusting the
  first one, code blocks pinned left-to-right.
- persian-style 0.1.1: the spoken-register guide, injected only when the
  message contains Persian.
- verify-first 0.3.0: claim-check on every prompt, the version-pin guard on
  `Write`/`Edit`, and the research rule injected only when a prompt actually
  picks something — including "I want to build X", the shape a technology
  choice usually arrives in, question mark or not.
