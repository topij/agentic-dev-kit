# Task — close `#602` in `topij/agentic-dev-kit`

You are a headless lane on the **agentic-dev-kit repository itself**, in your own
worktree on your own `dev/*` branch. Your pull request is **merged by the operator**,
never by you.

## Read these first

Your settings sources were deliberately emptied, so this repository's `CLAUDE.md` and
`AGENTS.md` did **not** load into your context. Read them yourself before you write
anything — they are the contract you are working under:

```
cat AGENTS.md
cat docs/agentic-dev-kit/workflows/post-merge-systemize.md
cat .claude/commands/post-merge-systemize.md
cat .agents/skills/post-merge-systemize/SKILL.md
cat .claude/commands/session-start.md .claude/commands/wrap-up.md
cat .agents/skills/session-start/SKILL.md .agents/skills/wrap-up/SKILL.md
cat docs/agentic-dev-kit/runtime-parity.md
```

Two sections of `AGENTS.md` bind everything you write: **Numbers in prose** (a number
describing current state does not go in prose — write the enumeration or name the
command) and the **CHANGELOG** ground rule. They apply to your commit message and your
PR body, not only to the files you edit.

## The defect

`#602`. `#595` correctly cut `.claude/commands/post-merge-systemize.md` to a thin
binding. Three things fell out, and `#596`/`#599` — which harmonised the other
bindings — did not pick them up:

1. **The rule-destination translation is gone.** The old Claude command routed rules to
   `CLAUDE.md` / `.claude/rules/`. The shared workflow speaks only of "the narrowest
   shared repository source" and names no runtime's rule layer — confirm that yourself:
   `grep -in 'CLAUDE.md\|AGENTS.md\|rules/' docs/agentic-dev-kit/workflows/post-merge-systemize.md`.
   So a Claude session running this workflow has no instruction telling it where a rule
   goes. That is exactly the "invocation and mechanism translation" that
   `docs/agentic-dev-kit/runtime-parity.md` permits an adapter to carry.
2. **The Claude binding still says "Resolve configuration from the repository root and
   `config/dev-model.yaml`".** `#596` told adopters not to retain an instruction to
   read only the tracked file, and rewrote the other bindings to "merged configuration
   defined by the shared workflow".
3. **The Codex skill still carries a numbered-step body**, including a policy line
   ("Never create or modify a tracker item without explicit operator confirmation")
   that its Claude twin does not have, while `#596`/`#599` thinned the other Codex
   skills to the Claude shape.

## What to build

**a. Add the rule-destination translation to both bindings** — one line each, and each
runtime's own destination: the Claude binding names `CLAUDE.md` / `.claude/rules/`, the
Codex skill names `AGENTS.md`. This is a translation of a mechanism, not new doctrine:
do not add a rule the shared workflow does not already impose, and do not move the
decision of *what* is a shared rule out of the shared doc.

**b. Align the Claude binding's config wording** with the merged-configuration wording
`#596`/`#599` gave the other bindings. Use those bindings as the reference; do not
invent a third phrasing.

**c. Thin the Codex skill to the shared shape.** Take the other Codex skills as the
model. Deciding where the policy line in item 3 goes is part of the task, and it is a
judgement, not a deletion: if the constraint it states is already carried by the shared
workflow, dropping it from the adapter loses nothing; if it is not, dropping it loses a
real guarantee and you must say so in your PR body rather than dropping it quietly.
Check the shared workflow before you decide, and record what you found.

**d. Pin both bodies** the way `_assert_bookend_adapter_semantics` pins the bookends —
`scripts/tests/test_portability.py`, and read `_bookend_adapter_body` and
`test_bookend_adapter_hostile_mutations_are_rejected` beside it. Follow that shape:
an exact-body assertion plus hostile mutations that must be rejected. A test that only
asserts a substring is present is not this shape; the bookend pin asserts the flattened
body **equals** the expected string, which is what makes a silent reword fail.
`test_post_merge_systemize_is_shared_thin_and_config_owned` already exists in that file
and caps the bindings' line counts — keep your edits inside those caps, or raise a cap
deliberately and say why in the PR body.

## What you cannot do, and what to do about it

Your permission profile grants file editing inside your worktree, `git`, `gh`, and
`uv run scripts/pr_watch.py`. It does **not** grant `make` or a bare `uv run pytest`,
so **you cannot run this repository's test suite locally.** Do not try to route around
that, and do not claim a verification you did not perform.

What this means concretely:
- CI is your verification. Push, open the PR, and drive CI to green — the lane contract
  above already binds you to poll it yourself.
- If CI fails, read the failure with `gh run view`, fix, and push again.
- In your final text, state plainly that the suite was not run locally and name CI as
  what verified the change. `AGENTS.md`'s Verification section requires you to name the
  command and its actual result; the honest form here names the CI run.

## Ground rules that bind you specifically

- Branch: you are already on your lane branch. Run `git branch --show-current` before
  every commit, as the contract says. Never commit to `main`.
- **Never edit `docs/kit-handoff.md` or `docs/kit-friction-log.md`.** The repository's
  pre-push hook refuses a push from a `dev/*` branch that touches either, so doing it
  will hard-fail your push. Your handoff goes in the PR body.
- Add a `CHANGELOG.md` entry if and only if this change is observable in the sense
  `AGENTS.md` and `CHANGELOG.md`'s own header define. Adapter prose that changes what
  an agent is told is a real candidate; decide it against those two files' stated test
  and justify your decision in the PR body either way. Head an entry with your PR
  number, newest first.
- Never write a GitHub closing keyword next to an issue number you do not intend to
  close. `#602` **is** the issue this PR closes, so a closing keyword for `#602` is
  correct. For any other issue you mention, write "#N stays open".
- Do not merge. Mark ready, drive to green, and stop.

## Your final text

The lane contract makes your final text the durable channel back to the cockpit. Put in
it, explicitly:
- The PR number and URL.
- What you changed in each of the four items, and the judgement you made in item **c**.
- Whether you added a CHANGELOG entry and the reasoning either way.
- The CI result you actually observed, and the statement that the suite did not run
  locally.
- Anything about the launcher, the profile, or the workflow that got in your way — this
  lane is the first real headless task on this launcher, and friction you hit is a
  finding the cockpit needs. Report it even if you worked around it.
