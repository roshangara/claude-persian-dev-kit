This message is asking you to pick or recommend something — a tool, a library, a
version, an approach. Check that your answer is still true before you give it.

## One lookup, not a research project

Check what goes stale. Skip what doesn't.

| goes stale — check it | doesn't — don't waste a call |
|---|---|
| the current version or tag | what a for-loop does |
| whether a project is still maintained | which sort is stable |
| what the recommended approach is *today* | how TCP works |
| whether a flag, API, or option still exists | this repo's own code — read it |
| whether something was deprecated or replaced | a decision already made |

One targeted lookup per thing you are actually about to recommend. If you
checked it earlier in this session, that still counts — don't check twice.

## Where to ask

| what | where |
|---|---|
| GitHub release | `api.github.com/repos/<owner>/<repo>/releases/latest` |
| container tag | the registry's tag list, or `crane ls <image>` |
| npm | `npm view <pkg> version` |
| PyPI | `pypi.org/pypi/<pkg>/json` |
| language runtime | `mise registry`, `mise ls-remote <tool>` |
| an API's shape | its current docs, not your memory of them |
| "is this still the way" | the project's own README or changelog |

## What to say back

Name what you checked, and say it plainly: "latest is 5.2.1, three weeks old"
is worth more than "I recommend v5". If the answer you were about to give has
been superseded, say what replaced it and why — finding that is the entire point
of looking.

Two things not to do:

- Don't hedge everything into a survey. Recommend one thing, say why, and note
  the runner-up in a sentence if it genuinely competes.
- Don't stall when the network is unreachable. Give your best answer, and say
  which part is unverified and why.

## When this does not apply

Reading a file, running a command, explaining a concept, or continuing work the
user already scoped. This fires on choosing, not on doing.
