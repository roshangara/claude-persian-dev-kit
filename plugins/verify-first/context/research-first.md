This message involves picking something — a tool, a library, a version, an
approach. **Do not name one from memory.** Find out what the current answer is
first, then answer.

Your training data has a cutoff. In this exact spot — which tool people actually
use for this today — it is both stale and confident, which is the worst
combination. A recommendation that was right two years ago still *sounds* right.

## Two sizes of question, two depths of check

**"What version / is this still maintained?"** — one lookup. Hit the registry,
get the number, move on.

**"I want to build X" / "we need a Y"** — this is a technology choice, even when
it is not phrased as a question. Before you name anything:

1. **Look at what they already run.** Read the repo, the config, the infra
   notes. Recommending a greenfield tool to someone who already operates one is
   the most common way this goes wrong, and it is entirely avoidable.
2. **Search for the current landscape.** Not "is X good" — *what are people
   using for this now*. You are checking whether your first instinct is still
   the answer, so look before you form the recommendation, not after.
3. **Check the one you land on is alive.** Last release date, open issues,
   whether it was deprecated or absorbed into something else.

If you skipped all three and named a tool anyway, you guessed. Say so.

## Where to ask

| what | where |
|---|---|
| the current landscape | a web search — what shipped in the last year or two |
| GitHub release, activity | `api.github.com/repos/<o>/<r>/releases/latest`, commit dates |
| container tag | the registry's tag list, or `crane ls <image>` |
| npm / PyPI | `npm view <pkg> version`, `pypi.org/pypi/<pkg>/json` |
| language runtime | `mise registry`, `mise ls-remote <tool>` |
| an API's shape | its current docs, not your memory of them |
| what they already run | this repo, its config, its docs — read, don't guess |

## Don't spend a lookup on

This repo's own code (read it instead), a concept that does not change, a
decision already made, or the mechanics of something you are simply using rather
than choosing.

## Answering

Name what you checked and when: "latest is 5.2.1, three weeks old, still active"
carries weight that "I recommend v5" does not.

Recommend **one** thing and say why. Name the runner-up in a sentence if it
genuinely competes — do not lay out five options and hand the decision back.

If something you were about to suggest has been superseded, say what replaced it
and why. Finding that is the entire point of looking.

If you cannot reach the network, answer anyway and say plainly which part is
unverified. Never stall on this.
