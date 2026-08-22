<!-- devkit-source: kit-own — this is the KIT's own entry point, not a rendered one. ./init.sh replaces it with yours; delete this line to claim the file. -->

# AGENTS.md — agentic-dev-kit

The contract every session in this repo runs under, for **both** runtimes. Codex
and other agents that read `AGENTS.md` load this file directly; Claude Code reads
`CLAUDE.md`, which imports it. One file, two bindings — do not copy any of it
into a runtime-specific file.

## Verification

**`make test` is the verification command for this repo.** It runs `lint` and
`check-syntax` first, and a failure in either stops it there — no pytest, and so no
summary line. The suite itself (`scripts/lib/state_paths/tests` + `scripts/tests`) gets
pytest and PyYAML from `uv run --with pytest --with pyyaml`; `lint` supplies `ruff`
separately, through `uvx`. **Raise your tool timeout before starting the run** — a
default timeout can cut the run off partway, and how that truncation surfaces differs by
runtime. pytest's summary line prints the elapsed time for the run you actually did.

The two probes an agent reaches for first both fail here in a way that reads as
"pytest is unavailable in this environment". Neither is evidence of that:

- `uv run pytest` → `error: Failed to spawn: pytest` (pytest is not a project dependency)
- `python3 -m pytest` → `No module named pytest` (the system Python has no pytest)

Do not conclude tests cannot run locally, and do not defer verification to CI, without
having run `make test`. When claiming something is verified, name the command that
established it and its actual result — #54 tracks making this a standing rule. When
that result is a figure, or a verdict resting on one, *Numbers in prose* below governs
how you write it.

## Numbers in prose

**A number describing current state does not go in prose.** If a reader can count it,
write the enumeration and let them; if a command prints it, name the command. This
binds **every surface a session writes**: commit messages, PR bodies, code comments,
docstrings, issue text, review replies, and the narrative docs. The handoff was never
the problem — `wrap-up.md` has bound that one all along. Every other surface in that
list, the rest of the narrative docs included, this section reaches first. The shape it
takes is a commit that grows a list and leaves the number describing it alone: the list
is the thing being edited, the number is prose beside it, and the edit never reaches it
(`#546` enumerates the occurrences).

**A measured figure is stamped with its command, its revision and its date, or it is
dropped.** Those three are the stamp; everything below means this one and restates it
nowhere. The stamp is what makes a sentence a different kind of claim, not decoration on
the same kind. *"The helper recognises three forms"* says what is true now, so the next
commit falsifies it without touching it; *"`make test` at `<sha>` on `<date>` printed
`<n> passed`"* says what one run did, and nothing later can falsify that. An unstamped
figure is a current-state claim however it was meant, because no reader can date it.

**A constant is untouched by this. A reading is not.** A constant is fixed in advance
and reads the same for everyone: a documented exit code, a configured budget ceiling, a
pinned version, an issue number. A reading is what one look at the system returned: the
status your run exited with, the live count against that ceiling, the version actually
installed, what a config key resolved to on this machine. **Every pair there is one word
apart, so apply the test and not the list** — the list only illustrates the test, and no
list of exempt values can be complete. A reading takes the stamp, whatever it is spelled
as.

**Naming the command covers the number and not the verdict built on it.** Dropping the
digit while keeping the judgement it supported is the halfway remedy, and it is the half
that failed: *"over budget — `check_doc_budget.py` prints the live figure"* has no
figure left in it and was false within hours anyway (`#258`). `over budget`,
`converged`, `passing`, `clean` are the same claim as the number they replaced, wearing
a word.

So a verdict is not the cheap way out of the rule above. **A verdict takes that same
stamp, and nothing weaker.** Stamped, it is an observation and it keeps; standing loose
in a document, it is a claim about now that nobody will re-check. Drop it, or stamp it —
the same two exits the number had.

**So the question to ask of a number you are about to write is whether you counted it
or read it.** Counted — off a list, off your sense of the session, off what you believe
you just added — it does not go in: write the enumeration, or name the command that
prints it. Read out of the output of a run, it goes in stamped. A number in prose is
one of those or it is a defect.

**A quantity word is a number.** *"several tests failed"*, *"most of the forms"*,
*"nearly all of them"* make the same current-state claim, go stale the same way, and
have no digit in them to catch a reader's eye. The rule is about the claim, not the
notation — the same reason a verdict does not escape it.

**Where this meets Verification, and how that resolves.** Verification asks for the
command *and its actual result*, which is exactly what invites a figure into the
sentence. Neither rule yields: Verification still requires the command and the result,
and this section governs the form that result takes, whether it is a figure or a verdict
resting on one. **`actual` is the operative word — read the result back out of the run
you are naming.** If you cannot point at the output the figure came from, because the
run has scrolled or because you are counting what you believe you just added, you do not
have the figure, and re-running to read it is the only way to get it. A figure written
from expectation is the defect this section is mostly about, and the harder one to
catch, because a stamp beside it reads as compliance. And note what is *not* the way
out: *"`make test` → green"* does not escape the rule by having no digit in it.
Unstamped, it is `over budget` one command over. Stamped — *"`make test` at `<sha>` on
`<date>` → green"* — it is fine, and a pass or a failure is a result Verification
accepts; it does not additionally require the count.

`wrap-up.md` carries the handoff's application of this rule ("an event is not a
tally") and stays self-contained rather than pointing here, because it ships to
adopters whose `AGENTS.md` is their own file and need not carry this section. This
section is the general rule and that is its handoff-specific case. **It is not a
subset**: `wrap-up.md` also asks a verification claim to name *the directory it ran in*,
which is not in the stamp above and which this repo's two-tree hazard makes load-bearing
on its own. Where both apply, satisfy both. Neither may contradict the other, and a
change to one is a reason to read the other.

## Ground rules

- `main` is protected: never commit to it directly. Branch and open a PR — and opening
  the PR is not done; watch it to green and review-clean (`pr-watch`).
  **Cockpit work branches `chore/<slug>` or `feat/<slug>`, never `dev/<scope>`.**
  `dev/` is `vcs.dev_branch_prefix` — the prefix reserved for isolated lanes — and
  `scripts/hooks/pre-push` refuses any push from a `dev/*` branch that touches
  `docs/kit-handoff.md` or `docs/kit-friction-log.md`. A wrap-up commit on a `dev/*`
  branch is blocked by the repo's own hook.
- All configuration lives in `config/dev-model.yaml`; skills and engines read it from
  there. Never hardcode a value that belongs in it.
- The living plan is `docs/kit-handoff.md` — read at session start, updated at wrap-up.
  New friction is recorded in `docs/kit-friction-log.md`.
- **If a change is observable, the PR that makes it adds its own `CHANGELOG.md` entry.**
  Observable means a repo pinning the old contract breaks: a report or return **shape**,
  **gate semantics** (`converged` / `mergeable` / `done`, a hook's exit code), a
  `config/dev-model.yaml` **key**, or an engine's **CLI surface**. Head the entry with
  this PR's number, newest first, and say what the adopter must *do*; the rationale
  belongs in the comment beside the code, not there. Nothing stamps entries after the
  merge, so one omitted here reaches the adopter as a red test after a file copy with no
  way to tell a kit break from a pinned old contract (`#430`). A change with no
  adopter-visible consequence gets no entry — that silence is the file's contract.
- Never write a GitHub closing keyword (`close` / `fix` / `resolve` and their forms)
  adjacent to an issue number you do not intend to close — on any surface (PR body,
  commit message, squash message), in any form, even negated or inside code spans.
  Write "#N stays open" instead.

## Working across two trees

Verifying in a throwaway clone, measuring against an adopter checkout, upgrading a
second repo — any task with a second tree in play. **A `cd` outlives the command that
made it**, so every later relative path resolves in the wrong tree.

- **Absolute paths for every write.** Bind the two roots to variables once
  (`REPO=/abs/path`, `KIT=/abs/path`) and write through them. A bare `cp x y` or
  `./init.sh` is the failure.
- **Assert `pwd` before the first write of a sequence**, not after. After is a
  post-mortem.
- **Verify at the destination.** Hash the file where it was supposed to land
  (`shasum -a 256 "$REPO/path"`) rather than reading `git status` from wherever the
  shell happens to be.

This is a rule because the failure **mimics** something else. It does not look like a
wrong directory; it looks like the tool or the filesystem misbehaving. It cost two
sessions time on 2026-08-09 in two repos: one put `cp` and `./init.sh` into a
verification clone and read as filesystem corruption (`stat` reporting one inode for
two paths, ten minutes spent suspecting a sandbox overlay); the other ran kit greps
inside an adopter checkout and briefly "found" that adopter's variable in
`scripts/dev_session.sh`. Both sessions were doing the right thing — verify in a copy
first — and were defeated by shell state, not reasoning (`#399`).

`fallback-review-panel.md` rule 7 has carried this for review lenses since before
either occurrence; nothing carried it for workflows. **Both `upgrade.md` and `adopt.md`
clone the kit to a second tree** in their Step 0, and `adopt.md` Step 1 then sends you
to read files inside it. Only `upgrade.md` is hardened so far — it binds `$REPO`/`$KIT`
and anchors its writes — because that is where the occurrence landed and where the
writes are literal shell. `adopt.md` states its copies mostly in prose, which narrows
the blast radius without removing it; hardening it is `#399`'s remaining half.

## Runtime parity

This repo is the kit itself, so its own two-runtime setup is the worked example:

- The runtime-neutral workflow definitions live in `docs/agentic-dev-kit/workflows/`.
  `.claude/commands/` and `.agents/skills/` are thin bindings over them.
- **A workflow's behaviour is changed in the shared doc, never in one binding.**
  A change made in an adapter reaches one runtime and silently not the other,
  which is the failure `#243` and `#273` are filed about.
- Doctrine that must reach every runtime does not belong in `.claude/rules/` —
  Claude Code alone reads that directory.
