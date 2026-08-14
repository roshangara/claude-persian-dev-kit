# claude-persian-dev-kit

Three Claude Code plugins. Two make Persian usable; one makes Claude check
things instead of remembering them.

They are independent — install only what you want.

## Install

```
/plugin marketplace add roshangara/claude-persian-dev-kit
/plugin install persian-rendering@persian-dev-kit
/plugin install persian-style@persian-dev-kit
/plugin install verify-first@persian-dev-kit
```

**Then start a new session.** Hooks are registered when a session begins, so
nothing installed mid-session takes effect until you restart Claude Code. For
`persian-rendering` there is a second step after that: reload the editor window
(`Developer: Reload Window`), because the browser is still holding the old
webview bundle.

If the font has not changed, it is almost always one of those two — see
[Troubleshooting](#troubleshooting).

Updates: Claude Code checks the marketplace shortly after a session starts,
but for a third-party marketplace like this one auto-update is **off** until
you enable it once — `/plugin` → Marketplaces → this marketplace →
Enable auto-update. After that, new versions download on their own and apply
at the next launch (or immediately with `/reload-plugins`). Without it, update
by hand: `claude plugin update <plugin>@persian-dev-kit`, then restart.
`/plugin marketplace update` only refreshes the catalog — it does not update
installed plugins.

---

## persian-rendering

Persian in the Claude Code VS Code panel is hard to read out of the box. Two
separate causes, both fixed here.

**No Persian font.** The panel's font stack is Latin-only, so Persian falls
through to whatever the machine happens to have. This plugin bundles
[Vazirmatn](https://github.com/rastikerdar/vazirmatn) — the *Non-Latin* build,
which contains only Arabic-script glyphs, so Latin text keeps coming from the
system font and nothing else changes appearance. It is served from the
extension itself, so you do not install anything locally and it works from any
browser you open the workspace in.

Your own font settings survive. The script reads the fonts you configured —
`--vscode-editor-font-family` and friends — and slots Vazirmatn in just before
the generic family, so a Fira Code setting keeps rendering the code blocks and
Vazirmatn only ever supplies the Arabic-script glyphs nothing else offers. It
has to sit *before* `monospace`: whatever font that generic resolves to on the
machine may carry Arabic glyphs of its own, and any font earlier in the list
that has the glyph wins.

**Direction decided by the first character.** The panel uses
`unicode-bidi: plaintext`, which takes a block's direction from its *first
strong character*. A paragraph like

> **Agentless.** روی سرور مقصد هیچ چیزی نصب نمی‌شود…

is 85 Persian letters and 12 Latin ones, but because it opens with `A` the whole
block lays out left-to-right and becomes unreadable. CSS cannot count
characters, so this plugin measures each block in JavaScript and writes an
explicit direction.

The measurement has a few deliberate choices:

- **Inline code doesn't count.** `python3` and `network_cli` are not evidence
  that a sentence is English.
- **Context beats ratio.** A list item inside a Persian list is Persian, even if
  it is only a shell command. Judged alone it would go left-to-right and drift
  to the far edge of the list.
- **Persian wins ties.** A standalone block goes Persian unless Latin outweighs
  it more than two to one — technical Persian carries a lot of English, and a
  plain majority decides headings like `Variables و اولویت‌شان` by one letter.
- **Code blocks stay left-to-right**, always. A Persian comment must not flip
  the line.
- **A number after a Latin word gets that word isolated.** Unicode's rule W7
  gives a number to the last strong character before it, so "روی shahab ۲ دقیقه"
  renders as "روی ۲ shahab دقیقه" — the number arrives before the word it belongs
  to. Both `۲` and `2` do this; they are the same bidi class. Only that shape is
  wrapped, and only the direction changes, never the text.

One more cleanup rides along: the app deliberately renders bidi control
characters (RLM, LRM, the isolate pair) as visible `\uXXXX` escape text — a
spoofing defence. Models sprinkle those marks into Persian output, so answers
arrive dotted with six-character noise. Since direction is measured per block
here, the marks serve no purpose at all: the escape text is removed from
prose. In backticks it survives, which is where it belongs when you are
actually discussing the character.

### The plan preview is a second webview

Claude Code renders a plan for review in its own tab, and that tab is a separate
webview (`claudePlanPreview`) whose entire HTML document — stylesheet included —
is a template literal inside `extension.js`. Nothing in `webview/` is involved.
So Persian came out right in the session and wrong in the plan: that template
carries no `unicode-bidi`, no `direction`, no `text-align`, and takes its font
from `--vscode-markdown-font-family`.

It gets the same treatment now, from `patch-plan-webview.py`: the stylesheet
appended to the template's own `<style>`, and `fa-bidi.js` added as a
`<script nonce="{{NONCE}}">`. Two things are specific to this webview:

- **The font has to be inline.** Its CSP is `default-src 'none'` with no
  `font-src`, and the extension never calls `asWebviewUri` for this panel, so a
  URL to a file next to the bundle cannot load. The woff2 goes in as a `data:`
  URI (48 KB, 64 KB encoded) and `font-src data:` is added to the CSP — the only
  part of this that loosens anything, and it admits fonts already inside the
  document.
- **Spacing had to become logical.** The template's `padding-left: 32px` on
  lists and `border-left` on blockquotes put the bullet indent and the quote bar
  on the wrong side of a right-to-left block. Same values as
  `padding-inline-start` and `border-inline-start`.

This part needs `python3`: the edits land in the middle of a template literal,
where a `sed` one-liner would be guesswork. Without it the chat panel is still
patched and only the plan tab stays as it was.

### How it applies

A `SessionStart` hook runs `apply-patch.sh`, which appends the CSS and JS to the
extension's webview bundle and patches the plan preview inside `extension.js`. It
keeps a pristine `.orig` of each file and rebuilds from it every run, so it is
idempotent and safe to run repeatedly.

Running on every session start is the point: **the Claude Code extension updates
roughly daily, and each update replaces the files this patches.**

Reload the window (`Developer: Reload Window`) after the first run.

### If you use the terminal instead of the panel

This fixes the panel only. Persian in the integrated terminal stays broken and
cannot be fixed here — xterm.js has no bidirectional text support, and a
cell-based terminal breaks Arabic letter joining by construction.

### Config

| variable | effect |
|---|---|
| `CPDK_EXTENSIONS_DIR` | patch only this extensions directory |
| `CPDK_VERBOSE` | print what was patched |

Without an override it looks in the code-server, VS Code Server, VS Code
desktop, VSCodium, openvscode-server, Cursor and Windsurf extension
directories. It exits 0 and says nothing when no Claude Code extension is
installed.

### Checking it worked

`/fa-doctor` does the whole check in one go: it re-runs the patcher verbosely,
greps the patch markers in every extension it can find, confirms `python3` is
there for the plan tab, and says exactly which step is broken if one is.

`tests/render-test-fa.txt` and `tests/render-test-en.txt` are prompts. Paste one
into a fresh session and it produces every element Claude Code can render —
headings, nested lists, tables, blockquotes, code blocks, links, tool calls,
diffs — each in both a Persian-first and a Latin-first variant.

That split is the point. Every bug found while building this came from the same
place: a block that opens with a Latin word but is mostly Persian. The English
file is the regression check — English must stay untouched.

The plan tab is a separate check, because it is a separate webview: ask for a
plan in Persian in plan mode and read the review tab that opens. Paragraphs
right-aligned with the bullet indent on the right, code blocks still
left-to-right, and Persian in Vazirmatn rather than a fallback face.

### Undo

```
for f in <ext>/webview/index.{css,js} <ext>/extension.js; do cp -f "$f.orig" "$f"; done
```

`apply-patch.sh` writes those `.orig` copies on first run and never overwrites
them, so this restores the extension exactly as it shipped.

---

## persian-style

Makes Claude write Persian, rather than English wearing Persian words.

The failure it fixes is structural, not lexical: sentences whose vocabulary is
Persian but whose skeleton is English — calques, forty-word sentences, passive
voice, `توسط` everywhere, bookish register nobody speaks.

The guide is injected **only when your message actually contains Persian**, so
an English-only session pays nothing for it. Persian inside code fences or
inline code does not count — an English message that pastes a Persian error
string must not flip the answer's language.

The register is for the chat only. The guide's last rule says so explicitly:
commit messages, code comments, docs and issue text follow the repo's own
language and tone, never the spoken register.

Why a hook and not a `CLAUDE.md` rule: a style rule has to govern the first
sentence of the answer. Loaded once at session start it fades — in the session
this came out of, the rule *was* in `CLAUDE.md` and the reply still arrived in
literary register. Re-injecting it next to the message it governs is what
actually works.

The register is opinionated: everyday spoken Persian, second person singular.
Edit `plugins/persian-style/style/persian.md` to taste — it is one file.

### Alongside another style plugin

`UserPromptSubmit` hooks add up rather than replace each other, so this runs
next to whatever else you have on that event. It owns one axis only —
**register**: spoken rather than bookish, Persian structure rather than
translated English. It says nothing about how long an answer should be. A
terseness plugin such as [caveman](https://github.com/JuliusBrussee/caveman)
owns length, and the two compose: three of the rules here — short sentences,
active voice, break up noun chains — pull the same direction.

Two things to know when you stack them:

- **The guide is ~52 lines of input on every Persian message.** A compression
  plugin saves output tokens; this spends input ones. Different budgets, but if
  you are reading a token-savings number, that is where part of it went.
- **Keep the object marker.** Dropping articles is an English move. `رو` carries
  grammatical role in Persian, and a fragment without it reads wrong — the
  `را → رو` row in the guide is about which form to use, not whether to write
  one.

---

## verify-first

Three rules. Each one fires on a trigger — none of them is an always-on mode.
That distinction is the whole design: a rule that shows up when it is irrelevant
reads as noise, and within a day it gets skimmed past.

| rule | fires when | costs |
|---|---|---|
| check the claim | every prompt | ~570 characters |
| research before recommending | the prompt asks you to choose | ~2 KB, only then |
| don't pin from memory | a `Write`/`Edit` contains a version | nothing until it does |

**Check a claim before building on it.** When your message rests on a verifiable
premise, Claude checks it instead of agreeing. Short enough to carry on every
prompt. Not a licence to argue — a preference or a decision you already made is
yours.

**Research before recommending.** Fires on two shapes, because a technology
choice usually arrives as the second one:

- *asking* — "which queue should we use", "what's the best", "is this deprecated"
- *building* — "I want to implement DNS", "we need a job scheduler",
  "let's set up centralized logging"

The second has no question mark and none of the recommendation words in it, but
it is still a decision about what to use. Matching only the first shape was this
plugin's biggest hole.

The Persian patterns accept every joining a compound actually gets typed with —
ZWNJ, space, or nothing: «می‌خوام», «می خوام» and «میخوام» all match. `\s` does
not match ZWNJ, so the earlier patterns silently missed the *standard* spelling
of exactly the words they were written for. `tests/test-verify-first.py` holds
the trigger cases, ZWNJ ones first.

The rule scales with the question. A version check is one registry call. A "we
need an X" is three steps before anything gets named: read what they already
run, search what the current landscape actually is, then check the thing you
landed on is still alive. It ends with "if you skipped those and named a tool
anyway, you guessed — say so."

It also says what *not* to look up, asks for one recommendation rather than a
survey, and treats an unreachable network as "answer and flag it", never as a
reason to stall.

English and Persian phrasings both. Ordinary work — `fix`, `run`, `commit`,
"why is this failing" — is filtered out even when it contains a word like
*install*.

**Never write a version from memory.** A `PreToolUse` hook scans every `Write`
and `Edit` for dependency pins — `uses: owner/repo@v4`, `FROM node:22`,
`"react": "^18.2.0"`, `requests==2.31.0`, `version = "5.31.0"`, a `go.mod`
require line, a Gemfile `gem`, a Cargo `{ version = "1.0" }` — and puts the
rule back in front of Claude at the moment it is about to write one.

A `"version"` key by itself is exempt: that is the file's *own* version, and a
guard that fires on every routine `plugin.json` bump trains everyone to skim
past it — this repo's own release commits used to trip it three times over.
`tests/test-version-guard.py` pins the catches and the exemptions both.

This one is worth the machinery because the failure is silent. A version that
was current when the model was trained still *looks* right in a diff. Nobody
notices until CI breaks or a CVE lands.

| variable | effect |
|---|---|
| `CPDK_VERSION_GUARD=block` | ask for confirmation instead of just reminding |

Reminding is the default: blocking is stricter, but one false positive stalls
real work.

---

## فارسی

سه تا plugin برای کلود کد. دوتاش فارسی رو قابل استفاده می‌کنه، سومی کاری می‌کنه
که کلود به‌جای اتکا به حافظه، چیزها رو چک کنه. هر کدوم مستقلن.

**persian-rendering** — دو تا مشکل رو حل می‌کنه. اول فونت: پنل استک فونت لاتین
داره و فارسی می‌افته روی هرچی سیستم داشته باشه. فونت وزیرمتن (نسخه‌ی Non-Latin
که فقط گلیف فارسیه) از خود اکستنشن سرو می‌شه، پس روی لپ‌تاپت لازم نیست چیزی نصب
کنی. دوم جهت متن: پنل جهت هر بلوک رو از **اولین حرفش** می‌گیره، برای همین
پاراگرافی که با یه کلمه‌ی انگلیسی شروع می‌شه ولی بقیه‌ش فارسیه چپ‌چین می‌شه و
ناخوانا. این plugin به‌جای اولین حرف، کاراکترها رو می‌شمره — و محتوای `code` رو
حساب نمی‌کنه، چون `python3` دلیل انگلیسی بودن جمله نیست.

تبِ **plan** یه webview جداست و CSS خودش رو داره — داخل `extension.js`، نه
`webview/`. برای همین فارسی تو session درست بود و تو پلن نه. اون هم وصله می‌شه:
همون script اندازه‌گیری اونجا هم می‌ره، فونت هم به‌صورت `data:` تزریق می‌شه چون
CSPـش `default-src 'none'` ـه و فونت از فایل بیرونی اصلاً load نمی‌شه. این تیکه
`python3` لازم داره؛ اگه نباشه panel وصله می‌شه و فقط تب پلن دست‌نخورده می‌مونه.

فونتی که خودت تو تنظیمات VS Code گذاشتی سر جاش می‌مونه: script استک واقعی رو از
متغیرهای `--vscode-*` می‌خونه و وزیرمتن رو فقط قبل از generic اضافه می‌کنه — پس
مثلاً Fira Code همچنان کد رو رندر می‌کنه و وزیرمتن فقط گلیف‌های فارسی رو می‌ده.

وصله سر هر سشن دوباره اعمال می‌شه، چون اکستنشن تقریباً روزانه آپدیت می‌شه و هر
آپدیت وصله رو پاک می‌کنه. بعد از اولین اجرا یه بار `Developer: Reload Window`
بزن. هر وقت شک کردی وصله هست یا نه، `/fa-doctor` رو بزن — کل زنجیره رو چک
می‌کنه و می‌گه کجاش خرابه.

**ترمینال درست نمی‌شه.** xterm.js پشتیبانی bidi نداره و این وصله فقط panel رو
می‌گیره.

**persian-style** — کاری می‌کنه فارسی بنویسه، نه انگلیسیِ ترجمه‌شده. راهنما فقط
وقتی تزریق می‌شه که پیامت واقعاً حرف فارسی داشته باشه — فارسیِ داخل code block
حساب نیست، پس پیام انگلیسی‌ای که فقط یه ارور فارسی رو نقل می‌کنه جواب رو فارسی
نمی‌کنه. لحن خودمونی هم فقط مال چته: کامیت و کامنت و doc به زبون خود ریپو
می‌مونه.

hookهای `UserPromptSubmit` روی هم جمع می‌شن، جای هم رو نمی‌گیرن. این plugin فقط
مسئول **لحن**ـه — خودمونی به‌جای کتابی. کاری به طول جواب نداره. اگه یه plugin
دیگه مثل [caveman](https://github.com/JuliusBrussee/caveman) داری که جواب رو
کوتاه می‌کنه، این دوتا با هم می‌سازن؛ سه تا از قاعده‌های همین راهنما — جمله‌ی
کوتاه، فعل معلوم، شکستن زنجیره‌ی اضافه — هم‌جهت اونن. دو تا نکته: راهنما هر پیام
فارسی حدود ۵۲ خط input می‌خوره، و «رو» رو نباید بندازی. حذف article کار انگلیسیه؛
تو فارسی «رو» نقش دستوری داره و بی‌اون جمله غلط خونده می‌شه.

**verify-first** — قبل از اینکه نسخه‌ای بنویسه، مجبورش می‌کنه از رجیستری بپرسه
نه از حافظه. الگوهای فارسیش حالا نیم‌فاصله رو هم می‌فهمن: «می‌خوام» و «می خوام»
و «میخوام» هر سه trigger حساب می‌شن — قبلاً `\s` نیم‌فاصله رو نمی‌گرفت و دقیقاً
املای استاندارد از دستش می‌رفت.

---

## Troubleshooting

**The font did not change.** In order of how often it is the answer:

1. **You did not restart the session.** Hooks register at session start, so the
   patch never ran. Quit Claude Code, start it again.
2. **You did not reload the window.** The patch is on disk but the browser still
   has the old bundle. `Developer: Reload Window`.
3. **The plugin failed to load.** `claude plugin list` — look for
   `Status: ✔ enabled` and `Version: 0.3.0` or newer. Anything older, run
   `claude plugin update persian-rendering@persian-dev-kit`.

`/fa-doctor` walks all of this for you and names the failing step.

**The panel is fine but the plan tab is not.** Those are two different webviews.
Run the patch with `CPDK_VERBOSE=1` and look for `patched plan preview`. If it
says `plan preview skipped`, there is no `python3` on `PATH`. If it says `plan
preview not patched`, the template inside `extension.js` no longer matches what
the patcher expects — it restores the original rather than write a broken bundle,
so please open an issue with your extension version.

**The caret in the input is nowhere near the text.** Fixed in 0.3.2 — update and
reload the window. If it comes back, the two layers of the composer have gone out
of step again; the invisible one owns the caret and the visible one owns the
glyphs. This dumps both, so an issue can say what actually differed:

```js
const e = document.querySelector('[class*="messageInput_"]');
const m = document.querySelector('[class*="mentionMirror_"]');
copy(JSON.stringify({ editHTML: e.innerHTML, mirrorText: m.textContent }))
```

Run it in `Developer: Open Webview Developer Tools` while the input is in the
broken state. Meanwhile, cutting the text and pasting it back rebuilds the DOM
and clears it.

To see what the patch actually did, run it by hand:

```
CPDK_VERBOSE=1 ~/.claude/plugins/cache/persian-dev-kit/persian-rendering/*/scripts/apply-patch.sh
```

It names each extension it patched, or says it found none. If it found none,
your editor keeps extensions somewhere this does not look — set
`CPDK_EXTENSIONS_DIR` to that directory and please open an issue with the path.

## Licence

Code: MIT — see [LICENSE](LICENSE).
Bundled font: SIL OFL 1.1 — see [NOTICE](NOTICE).

This patches the Claude Code extension **in place on your own machine**. No
Anthropic code is redistributed here.
