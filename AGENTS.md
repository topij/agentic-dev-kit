<!-- devkit-source: kit-own — this is the KIT's own entry point, not a rendered one. ./init.sh replaces it with yours; delete this line to claim the file. -->

# AGENTS.md — agentic-dev-kit

The contract every session in this repo runs under, for **both** runtimes. Codex
and other agents that read `AGENTS.md` load this file directly; Claude Code reads
`CLAUDE.md`, which imports it. One file, two bindings — do not copy any of it
into a runtime-specific file.

## Verification

**`make test` is the verification command for this repo.** It runs `lint` and
`check-syntax` before the suite, and a failure in either stops it there — no pytest, and
so no summary line. **`check-syntax` does not cover what its name suggests**: it hands a
list of filenames to one `bash -n`, which parses the first and takes the rest as that
script's arguments, so every file after the first goes unchecked — locally and in CI
alike, since both run the same line. `#561` names them. A green run is not evidence
those scripts parse. The suite itself (`scripts/lib/state_paths/tests` +
`scripts/tests`) gets pytest and PyYAML from `uv run --with pytest --with pyyaml`;
`lint` supplies `ruff` separately, through `uvx`. **Raise your tool timeout before
starting the run** — a default timeout can cut the run off partway, and how that
truncation surfaces differs by runtime. pytest's summary line prints the elapsed time
for the run you actually did.

**`make test-fast` is not a verification command.** It runs the same `lint` and
`check-syntax`, then the suite without the `evidence`-marked tests (all of
`test_live_validation_bundle.py`, and the tree-copying tests #875 picked). Use it in the
inner loop; a verification claim still names `make test` and its result. The skipped
tests include guards, among them the lane launcher's authority checks, the self-merge
refusals and the live-validation bundle verifier's refusals, so a change to a guarded
path runs `make test` even in the inner loop.

The probes an agent reaches for first fail here in a way that reads as "pytest is
unavailable in this environment". None of them is evidence of that:

- `uv run pytest` → `error: Failed to spawn: pytest` (pytest is not a project dependency)
- `python3 -m pytest` → `No module named pytest` (the system Python has no pytest)

A bare `python` is a different trap rather than another of these — it may not exist at
all, and `command not found` says nothing about pytest either way.

Do not conclude tests cannot run locally, and do not defer verification to CI, without
having run `make test`. When claiming something is verified, name the command that
established it and its actual result — #54 tracks making this a standing rule. When
that result is a figure, or a verdict resting on one, *Numbers in prose* below governs
how you write it.

## Numbers in prose

This binds **every surface a session writes**: commit messages, PR bodies, code
comments, docstrings, issue text, review replies, the narrative docs, and anything else
someone reads later. **Apply the scope and not the list.**

- **Do not write a number that describes current state.** If a reader can count it,
  write the enumeration. If a command prints it, name the command.
- **Stamp a measured figure with its command, its revision and its date, or drop it.**
  The revision is a sha, never `HEAD`, a branch or "latest". When the claim precedes the
  commit that carries it, the revision is the one you ran against.
- **A verdict resting on a figure takes the same stamp.** `over budget`, `converged`,
  `passing`, `clean` and *"`make test` → green"* are the number wearing a word. Stamped
  (*"`make test` at `<sha>` on `<date>` → green"*) it is an observation that keeps;
  unstamped it is a claim about now.
- **A quantity word is a number.** *"several"*, *"most"*, *"nearly all"* make the same
  claim and go stale the same way.
- **A constant is exempt; a reading is not.** A constant is *declared*: the value the
  system is **to** use, written where that is decided. A reading is what one look at the
  system returned. Being written down or being stable does not make a reading a
  constant. **Apply the test and not a list.**
- **A dated narrative event is not a reading.** *"It cost two sessions time on
  2026-08-09"* says what happened. *"As of `<date>`, the suite has `<n>` tests"* says
  what is, and takes the stamp.
- **Ask whether you counted it or read it.** A counted figure does not go in. A read
  figure goes in stamped, read back out of the run you name. If you cannot point at that
  output, re-run to get it.

This meets *Verification* without either rule yielding: Verification requires the
command and its actual result, and this section governs the form that result takes.
`wrap-up.md` carries the handoff's own copy of this rule and also asks a verification
claim to name the directory it ran in. Where both apply, satisfy both, and treat a change
to one as a reason to read the other.

## Prose that goes false

*Numbers in prose* governs what you **write**. This governs a sentence already in the
record that your diff did not touch but that is false at the sha you ship. It binds the
same surfaces. A stale code comment is out of scope. Do both reads below, because
neither catches the other's case.

1. **Find what your own commit made false.** Re-read the whole paragraph your diff
   lands in, not only the changed line. Then grep the record for the subject you changed
   and correct it wherever else it is asserted. Dated sections record what was decided
   then; until `#696` settles that convention, put the correction on the entry the dated
   section points at.
2. **Find what the outside world made false.** For each sentence that could go false
   while the repository sits untouched (a pull request or issue being open, a branch or
   temporary tree existing, someone owing something, a tracker state, a remote's head),
   re-check it at the sha you ship and state what you found, or drop it. Dating the
   observation does not date an instruction built on it. **Apply the test and not the
   list.**

Where the false sentence is a figure, a quantity word or a verdict resting on one,
*Numbers in prose* governs its form. Enforcement is reading; `#120` tracks a cheaper
terminal check. This binds this repository only: it has no `wrap-up.md` counterpart.

The incidents and reasoning behind both sections, and the limits on widening them, are
in [`docs/kit-record-prose.md`](docs/kit-record-prose.md). Read it when a case is not
settled by the rules above.

## Ground rules

- `main` is protected: never commit to it directly. Branch and open a PR — and opening
  the PR is not done; watch it to green and review-clean (`pr-watch`).
  **Cockpit work branches `chore/<slug>` or `feat/<slug>`, never `dev/<scope>`.**
  `dev/` is `vcs.dev_branch_prefix` — the prefix reserved for isolated lanes — and
  `scripts/hooks/pre-push` refuses any push from a `dev/*` branch that touches
  `docs/kit-handoff.md` or `docs/kit-friction-log.md`. A wrap-up commit on a `dev/*`
  branch is blocked by the repo's own hook.
- **Open completed work ready for review by default.** Ready status invites review;
  it does not authorize merge. Draft is only for `pr-watch`'s bounded exception where
  a material unfinished-work window must already exist on the remote pull request. The
  run that opens it owns the ready transition; risk, broad scope, human review, and
  operator-held merge authority are not draft reasons by themselves. Run
  `pr-watch --assert-ready` after ready creation or transition, before review polling.
- **Behavioral changes to `scripts/pr_watch.py`, `scripts/dev_session.sh`,
  `scripts/launch_lane.py`, or the profile named by
  `parallel.claude_settings_profile` (`config/claude-lane-settings.json` in this
  repository) are safety-critical.** Read and apply
  `docs/agentic-dev-kit/safety-critical-changes.md` completely before changing any
  gate, launch-authority, or merge-authority path. This precise root instruction is
  the Codex binding; Claude's
  path-scoped rule binds the same shared file. `review.safety_critical_paths` in
  `config/dev-model.yaml` is the declared list of these files, and a pull request
  that changes one of them, or that config file itself, owes the two-lens fallback
  review. Do not restate its doctrine here or in
  either runtime adapter.
- **Every new tracker ticket states its execution environment** (`cloud`, `local`,
  or `unknown`), required inputs, and verification prerequisites before its payload
  is presented. Follow
  [`ticket-execution-environment.md`](docs/agentic-dev-kit/ticket-execution-environment.md);
  `session-start` uses it to choose work compatible with its current environment.
- All configuration lives in `config/dev-model.yaml`; skills and engines read it from
  there. Never hardcode a value that belongs in it.
- The living plan is `docs/kit-handoff.md` — read at session start, updated at wrap-up.
  New friction is recorded in `docs/kit-friction-log.md`.
- **If a change is observable, the PR that makes it adds its own changelog fragment** —
  a new file `changelog.d/<slug>.md` — `<slug>` being the branch name after its last `/`
  — under a name no earlier fragment used, never
  an entry in the frozen `CHANGELOG.md` (`#1009`); `CHANGELOG.md`'s header says how a
  fragment is named. Observable means a repo pinning the old contract breaks: a report or return
  **shape**, **gate semantics** (`converged` / `mergeable` / `done`, a hook's exit code),
  a `config/dev-model.yaml` **key**, or an engine's **CLI surface**. Start the fragment
  with a `## ` heading, and say what the adopter must *do*; it needs no PR number, so a
  lane can write it before its PR exists. The rationale belongs in the comment beside
  the code, not there. Nothing stamps entries after the
  merge, so one omitted here reaches the adopter as a red test after a file copy with no
  way to tell a kit break from a pinned old contract (`#430`). A change with no
  adopter-visible consequence gets no entry — that silence is the changelog's contract.
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

The failure looks like the tool or the filesystem misbehaving, not like a wrong
directory (`#399`). Both `upgrade.md` and `adopt.md` clone the kit to a second tree in
their Step 0. `upgrade.md` binds `$REPO`/`$KIT` and anchors its writes, and `#480`
reports that anchoring as fail-open. `adopt.md` states its copies mostly in prose;
hardening it is `#399`'s remaining half. The occurrences are recorded in
[`docs/kit-record-prose.md`](docs/kit-record-prose.md).

## Runtime parity

This repo is the kit itself, so its own two-runtime setup is the worked example:

- The runtime-neutral workflow definitions live in `docs/agentic-dev-kit/workflows/`.
  `.claude/skills/` and `.agents/skills/` are thin bindings over them.
- **A workflow's behaviour is changed in the shared doc, never in one binding.**
  A change made in an adapter reaches one runtime and silently not the other,
  which is the failure `#243` and `#273` are filed about.
- Doctrine that must reach every runtime does not belong in `.claude/rules/` —
  Claude Code alone reads that directory.
