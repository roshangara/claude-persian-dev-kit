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

Updates arrive when you run `/plugin marketplace update`, or automatically if
you set `autoUpdate` on the marketplace in your settings.

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

### How it applies

A `SessionStart` hook runs `apply-patch.sh`, which appends the CSS and JS to the
extension's webview bundle. It keeps a pristine `.orig` of each file and rebuilds
from it every run, so it is idempotent and safe to run repeatedly.

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
desktop, Cursor and Windsurf extension directories. It exits 0 and says nothing
when no Claude Code extension is installed.

### Checking it worked

`tests/render-test-fa.txt` and `tests/render-test-en.txt` are prompts. Paste one
into a fresh session and it produces every element Claude Code can render —
headings, nested lists, tables, blockquotes, code blocks, links, tool calls,
diffs — each in both a Persian-first and a Latin-first variant.

That split is the point. Every bug found while building this came from the same
place: a block that opens with a Latin word but is mostly Persian. The English
file is the regression check — English must stay untouched.

### Undo

```
for f in <ext>/webview/index.{css,js}; do cp -f "$f.orig" "$f"; done
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
an English-only session pays nothing for it.

Why a hook and not a `CLAUDE.md` rule: a style rule has to govern the first
sentence of the answer. Loaded once at session start it fades — in the session
this came out of, the rule *was* in `CLAUDE.md` and the reply still arrived in
literary register. Re-injecting it next to the message it governs is what
actually works.

The register is opinionated: everyday spoken Persian, second person singular.
Edit `plugins/persian-style/style/persian.md` to taste — it is one file.

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
`"react": "^18.2.0"`, `requests==2.31.0`, `version = "5.31.0"` — and puts the
rule back in front of Claude at the moment it is about to write one.

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

وصله سر هر سشن دوباره اعمال می‌شه، چون اکستنشن تقریباً روزانه آپدیت می‌شه و هر
آپدیت وصله رو پاک می‌کنه. بعد از اولین اجرا یه بار `Developer: Reload Window`
بزن.

**ترمینال درست نمی‌شه.** xterm.js پشتیبانی bidi نداره و این وصله فقط panel رو
می‌گیره.

**persian-style** — کاری می‌کنه فارسی بنویسه، نه انگلیسیِ ترجمه‌شده. راهنما فقط
وقتی تزریق می‌شه که پیامت واقعاً حرف فارسی داشته باشه.

**verify-first** — قبل از اینکه نسخه‌ای بنویسه، مجبورش می‌کنه از رجیستری بپرسه
نه از حافظه.

---

## Troubleshooting

**The font did not change.** In order of how often it is the answer:

1. **You did not restart the session.** Hooks register at session start, so the
   patch never ran. Quit Claude Code, start it again.
2. **You did not reload the window.** The patch is on disk but the browser still
   has the old bundle. `Developer: Reload Window`.
3. **The plugin failed to load.** `claude plugin list` — look for
   `Status: ✔ enabled` and `Version: 0.1.1` or newer. Anything older, run
   `claude plugin update persian-rendering@persian-dev-kit`.

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
