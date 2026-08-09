# agentic-dev-kit — Living Plan (Handoff)

> **Forward-looking handoff (Principle #1).** Read this at the start of every session
> (`/session-start`); update it at the end (`/wrap-up`). This file — not an agent's
> memory, not a scratch note — is the single source of truth for what's done, in
> progress, and next.
>
> **Why `kit-*.md` and not `handoff.md`:** `docs/handoff.md` is the *skeleton shipped to
> adopters*, rendered from `docs/templates/` by `init.sh`. If this repo pointed its own
> plan at that file, every session block here would ship into adopters' repos and the
> unrendered marker would be gone. An adopter's config uses the plain names; only the
> template repo needs this indirection.
>
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`).

Last updated: 2026-08-10 — **the install-path lane is merged** (`#401`, `4fc394f`).
`#397`, `#380` and `#398` are closed with their verification on the tracker; `#399` stays
open for its `adopt.md` half. `#380`'s acceptance is finally met — the Codex SessionStart
hooks fire in a **trusted** session, not under the bypass flag. New: `#402`, `#403`,
`#404`, `#405`. The next lane is `cluster:merge-gate`, unchanged and now unblocked.

## Latest session — 2026-08-10 (the install-path lane, and a gate the panel kept breaking)

**Theme —** four install-path items shipped in one PR. The work was small; the review was
not, and what it found is the more useful half. The `#398` template gate drew a defect in
round after round, every one inside the previous round's remediation.

- **`#397` closed.** `init.sh`'s `--no-clobber` summary aborted under `set -eu` between
  the file list and the four echoes explaining the action. Swept `init.sh` for the shape:
  no other instance. The similar lines in `dev_session.sh` and `reconcile_sessions.sh` are
  a **different shape and not this bug** — a standalone `while` whose last body statement
  is a falsy `&&` chain exits 0 under `set -e`; only one ending a **pipeline** exits 1.
  Verified in both directions, which is what stopped a false ticket against those files.
- **`#380` closed, acceptance met.** `init.sh` prints a Codex SessionStart registration
  and the kit's own `.codex/hooks.json` carries it. The fire-check ran in a **trusted**
  session with no bypass flag; the issue carries the before/after. Settled there too:
  `SessionStart` takes **no** `matcher` key (Codex accepts Claude's shape and then never
  fires), a project-level `.codex/hooks.json` **is** read, and project trust is **not**
  hook trust — the probe repo had `trust_level = "trusted"` and the hook still did not run.
- **`#398` closed.** The template refresh is gated on the declared set, keyed on
  `kit_commit`. `adopt.md`'s bullet had the same shape via its rationale rather than its
  instruction.
- **`#399` partly.** The cross-tree rule is in `AGENTS.md` and `upgrade.md` is bound to it
  — `$REPO`/`$KIT` in Step 0, `$REPO`-anchored writes, a `cd` that fails the run.
  **`adopt.md` is not hardened** and the issue stays open for it.
- **Filed:** `#402` (`kit_doctor`'s four manifest reads catch two exception types; a deep
  JSON array crashes the diagnostic), `#403` (the record-prose carve-out has no disposal
  for a claim that is *false* but marked imprecision), `#404` (the panel's scratch
  namespace collides on a same-head re-run), `#405` (nothing checks a round was posted —
  two were not, while four commits cited them). Occurrence comments on `#77` and `#399`.

**Learned**

- **A predicate restated where nothing executes it does not converge by patching.** The
  `#398` gate reimplements manifest semantics in doc-embedded Python, next to
  `kit_doctor.py`, which owns that schema. Read the `## Fallback panel — round N` headers
  on `#401` for the sequence; each fix drew the next defect. `init.sh`'s own
  `register_pr_hook` comment already names this pattern and its only known ending —
  delete the predicate, do not guard it better — and it went unrecognised for most of the
  loop while each round's fix was treated as the last one needed.
  **The structural fix is Step 2 asking the engine instead of re-deriving**, which needs a
  `kit_doctor` surface that does not exist; it gets its own PR.
- **Two guards were the same class one type over.** The manifest read enumerated exception
  types twice and was holed twice — `JSONDecodeError` escaped, then `RecursionError`
  escaped `(OSError, ValueError)`. `except Exception` closed the class. `#402` is the same
  enumeration, unfixed, in the engine.
- **A fix round can over-apply a finding as easily as under-apply it.** Round 2 found that
  the gate's refusal did not stop the workflow; the fix made *every* refusal stop it, which
  blocked the config migration for any adopter carrying a deliberate local patch — a state
  `record_install_manifest` writes by design. The narrower reading was available and not
  taken.
- **A `trap … EXIT` bounds damage in time, not against a concurrent reader.** A background
  job held a temporarily-lowered doc budget while `git add -A` ran for an unrelated commit,
  and the bad value merged into the branch before being restored. The trap fired correctly;
  the window was simply open. Caught by `git status`, not by any test — the budget check is
  warn-only, so a nonsense budget fails nothing.
- **The panel's own doctrine bit back, correctly.** A record-prose finding marked
  *imprecision below HIGH* must be **logged, not fixed** — and the rule says "as the lens
  marked it" precisely so the author cannot relabel to justify the cheaper disposal. I
  relabelled; two lenses caught it independently. `#403` is the gap that made the choice
  genuinely hard: the claim was *false*, and logging a falsehood ships it.

**Open, and owned by nothing yet**

- **`#399`'s `adopt.md` half** — it clones to the same second tree in Step 0 and Step 1
  sends you to read inside it, with no `$REPO`/`$KIT` binding.
- **`#402`, `#403`, `#404`, `#405`** as filed. `#403` is the one worth a decision rather
  than a fix.
- **`#395`, `#388`, `#358`** unchanged by this session.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**

▶ Next: **`cluster:merge-gate`** — `#190` and `#39` together (one guard, one change), then
`#95` separately. It was the handoff's first-named `Next` before this lane and is now
unblocked; `init.sh` and `pr_watch.py` do not touch, so nothing here supersedes it.

______________________________________________________________________

## Session — 2026-08-09 (the adopter's Phase 3 findings, worked back into the kit)

**Theme —** cs-toolkit's Phase 3 filed seven kit issues and left an adopter holding
`init.sh`. Six were worked and all four PRs merged; the seventh needs a runtime this host
cannot start. The panel found far more than the issues did, and the HIGHs clustered
entirely in the one feature that was new code rather than a correction.

- **`#387` merged (`ccbed71`) — `#385`, the blocking one.** `init.sh` no longer imposes a
  `reports/` ignore. The seeding splits into *hygiene* (unconditional, always-wins — a
  leak helps nobody) and *policy*, which declines to write when the repo disagrees: it
  already tracks files the entry would hide (asked of `git ls-files -i -c --exclude=`, so
  git's own matcher answers) or already carries a rule for that path. `state/` and
  `reports/` are anchored too.
- **`#389` merged (`dd2c001`) — `#379`, `#381`, `#386`'s `kit_doctor` half, `#383` item 2.** `kit_doctor` reports whether each hook registration
  RESOLVES, per surface, and only a dead path reaches the exit code. Not by hash: those
  files are the adopter's, which is why `init.sh` only prints them (`#303`), and hashing
  would report every adopter `locally-edited` forever — `#286`'s failure. A declined
  `pre-push` now reads `· declined (recorded in not_installed)`.
- **`#390` merged (`d2cd509`) — `#382`.** `adopt.md` and `upgrade.md` stopped telling
  operators the installer is manifest-untracked. The convergence plan records Phase 3 as
  merged and carries its two defects: a phase cs-toolkit does not declare, and SessionStart
  wiring assigned to both the kit and the adopter.
- **`#391` merged (`99ef579`) — `#383`, and the `init.sh` half of `#386`.** The installer's
  comment scanner no longer closes a double-quoted scalar at an escaped quote, which had
  `set_field` re-attaching a fragment of the adopter's own value as a comment.
- **Filed: `#388`** (no state for a kit-owned file installed but PINNED — `--record-install`
  refuses it and drops the whole `not_installed` declaration; reproduced against a clone of
  the adopter), **`#392`** (a registration built from an unknown shell variable is
  `unresolvable` and never reaches the exit code) and **`#393`** (a test that depends on
  `json.loads` raising `RecursionError`, which stops being true on 3.14). Occurrence
  comment on `#88`.
- **`#380` is blocked, not skipped.** `codex-cli 0.42.0` here cannot start a session
  (`400`, "requires a newer version of Codex"), so the fire-check is still owed. The
  `matcher` half is settled: the one real `SessionStart` registration on this machine
  carries **no `matcher` key at all**, against what the plan assumed from documentation.

**Learned**

- **A regression test can be masked by its own fixture.** `#387`'s flagship test was
  written to catch the anchoring defect and did not: its fixture pre-seeded a rule that
  made the guard return before anchoring was ever exercised, so reverting the fix left it
  green. Found by a lens mutating the line, not by reading. Three more of the same shape
  followed in one session — a property named in a comment and pinned by nothing — which is
  a pattern, not four accidents.
- **A liveness check that lies is worse than one that stays silent.** `#389`'s first
  version reported `✓ resolves` for `…/pr_followup_hook.py.disabled`, because the token
  stopped at the kit's filename and the real file exists. Renaming is the most ordinary way
  to disable a hook. Before the feature the doctor said nothing; with the bug it said
  something false, confidently — `#379`'s own failure mode, manufactured by `#379`'s fix.
- **Two rounds later the same guess failed at the other end**, and that is the more useful
  lesson: a hand-rolled scan of a shell command will keep disagreeing with the shell, in
  shapes nobody enumerates in advance. The fix that held was deleting the guess — `shlex`
  is the shell's own lexer and it is in the standard library. Patching the instance twice
  cost two rounds; replacing the mechanism cost one.
- **Volatile figures went stale three times in one session**, each caught by a lens: a
  tracked-file count, a grep count, and a doctor report that this session's own manifest
  bump falsified. Every one is now the command that produces it.
- **The adopter's review bot is not the only free audit.** CodeRabbit was rate-limited on
  every PR, so the panel was the gate throughout — more than a dozen rounds across the
  four. Count them from the `## Fallback panel — round N` headers on each PR rather than
  from a figure here; two figures in this very block were wrong when a lens counted them.
  The severity did not decay the way a fix-round sequence is supposed to: `#389`'s HIGHs
  kept arriving into its final rounds. Its round-10 comment carries the round-by-round
  table; read the count there rather than here, because three drafts of this sentence
  carried three different numbers and a lens had to recount from the PR to settle it.
  Every one of them came from a lens executing the changed path rather than reading it.

**Open, and owned by nothing yet**

- **`#395` is the open design question `#389` leaves behind**, and it is the one worth
  reading the PR comments for. Ten panel rounds; nine found something real, and six of
  those nine carried at least one HIGH — all of one class: the check disagreeing with a
  real shell about which file gets executed. Each is fixed and pinned. The residual is structural — the check
  judges any path-shaped word inside a hook command, so a path merely *mentioned* reads
  as invoked — and narrowing it to the shapes `init.sh` prints is a trade (it would lose
  the ability to judge a hand-written registration), which is why it is a ticket and not
  a fix round.
- **`#380` needs a host with a working `codex-cli`.** Nothing else unblocks it.
- **`#388` is the next adopter-facing gap**: cs-toolkit hand-maintains a manifest entry
  because of it, and re-running `--record-install` there silently undoes that.
- **`#358` remains untouched**, as it was last session.

### Later the same day — the July-cohort sweep

**94 issues re-derived against `main` at `40eef8b`, 17 closed (18%).** The sweep was run
because filing was outrunning closing about 5:1 and 94 issues were ≥8 days old in a repo
worked daily. Six read-only agents re-derived each premise with a command rather than
reading the issue text; every close carries that command in a comment.

- **Closed:** `#27` `#33` `#37` `#72` `#75` `#93` `#106` `#112` `#121` `#123` `#124`
  `#136` `#146` `#163` `#178` `#183` `#187`. `#72` is the instructive one — it was filed
  against behaviour that already shipped.
- **Routed as decisions, not defects:** `#4` (describes a service scaffold this repo does
  not have), `#167` (the split shipped; the rest is its own "what a repair needs to
  decide"), `#169` (draft-vs-ready default).
- **31 of the remaining 74 are labelled into five clusters** — `cluster:merge-gate` (3),
  `cluster:pre-push` (5), `cluster:suite-integrity` (7), `cluster:doctrine` (8),
  `cluster:review-signal` (9); `#36` carries two, so 32 assignments over 31 issues. Counted
  with `gh issue list --state open --label "cluster:<name>" --limit 300`, not estimated —
  a first draft of this line claimed all 74 and a lens counted it.
  **43 are deliberately unlabelled**: no evidence-backed cluster emerged for them during
  the sweep, and inventing one to reach a round number would make the labels worse than
  useless. So the labels are an index of what the sweep *found*, not of the backlog — a
  session picking a cluster gets a real work package; a session wanting the rest still has
  to read.

**The sweep's real finding is that the backlog is not stale.** An 18% close rate means the
pile is unworked rather than rotten, so triage is not the lever. Two pre-sweep claims were
wrong — **one projection and one truncated measurement**, and the distinction matters
because they fail differently. "Expect 40–50 closes" was a forecast drawn from a sample
chosen *because* it looked fixed. "Open issues: 30" was an observation, taken from a `gh`
call that silently hit its default limit; nothing about it was a guess, which is what made
it convincing.

**What the clusters say, ordered by what they threaten:**

- **`cluster:merge-gate` is the one that matters.** Three independent routes make
  `mergeable`/`converged` true when they should not: `#190` (losing or corrupting the
  state file disables the false-settle guard — and a *fresh clone* reaches that with no
  failed write), `#39` (the guard is one poll wide), `#95` (unanchored substring bot
  matching lets a PR forge a check that cancels its own reviewer's block). This is the
  kit's central promise, and cs-toolkit runs the engine.
- **`cluster:pre-push`** — five issues on one file, and `#36` was mutation-verified during
  the sweep: `exit 1` → `exit 0` and 1084 tests still pass. The kit's one mandatory
  protection is unpinned.
- **`cluster:suite-integrity`** — `#135` is quoted in `test_mutation_gate.py`'s own
  docstring as unresolved. While this cluster stands, every "fixed" verdict anywhere is
  softer than it reads.
- **`cluster:doctrine`** — `#141` and `#142` both build on `#56`, which was never
  implemented. Sequence `#56` first or they compound on nothing.

### Later still — Codex hooks settled, and the adopter's refresh merged

**`#380` is no longer blocked; it is ready to build.** The 0.42.0 that could not start a
session was a stale Homebrew *formula* shadowing the real CLI. On `codex-cli 0.147.0`, a
probe with both hooks registered in a throwaway repo's `.codex/hooks.json`:

- **A project-level `.codex/hooks.json` IS read.** That assumption had been carried
  unverified since Phase 0.
- **`SessionStart` fires with NO `matcher` key** — matching the shipping third-party
  registration and contradicting what the convergence plan assumed from documentation.
  Carrying Claude's matcher shape over would ship a hook that silently never fires.
- **`PostToolUse` with `matcher: "^Bash$"` fires, dispatched by Codex.** First time the
  kit's own Codex shape has been observed firing *by the runtime* rather than verified by
  running its command string through a shell — the caveat the Phase 3 memo left open.
- **The gate is hook TRUST, not support.** An untrusted hook is skipped silently; the first
  probe run looked like "not read" for that reason alone. `init.sh` already names the
  `/hooks` trust step, and that advisory should say a skipped hook is indistinguishable
  from a broken one.

Evidence is on `#380`. **One caution for whoever builds it:** the shape was proven with
`--dangerously-bypass-hook-trust`, a diagnostic no adopter will use. Acceptance must be
"fires in a *trusted* session", or it verifies a condition nobody reproduces.

**cs-toolkit's refresh merged** (`in-parallel-oy/cs-toolkit#1887`) — all four STALE files
taken, the `#385` hold retired, the 20 declines unchanged, and `#46`/Phase 2B still
deliberately declined. It sent two things back:

- **`#397`, new** — `init.sh` runs under `set -eu`, and the `--no-clobber` summary's loop
  can exit non-zero on its last iteration, aborting the script after listing the files that
  need action and before the four lines explaining the action. **Found by CodeRabbit
  reviewing the adopter's PR** — the "an adopter's review bot audits the kit" mechanism the
  Phase 3 memo named, firing a second time.
- **A correction to `#388`'s repro** — re-run against `40eef8b` it now exits **1**, where
  this repo recorded 0, and it **writes the downgraded manifest before failing**. The defect
  is unchanged; the stale exit code is the kind of detail that turns a workaround into false
  confidence. Their rule is the better one: when a tool's failure mode is "writes the wrong
  artifact", assert the artifact — exit codes are advisory.
- **`#398`, new** — `upgrade.md` Step 2 copies `docs/templates/*.tmpl` unconditionally. In a
  repo where those six are *declined*, that silently converts six deliberate decisions into
  installs, and `--record-install` then makes it permanent: 20 declines become 14, with
  nothing recording that anything was reversed. They spotted it before acting and declined
  the instruction.
- **`#399`, new, and it is a pattern not an incident** — a persisted `cd` sent writes into a
  verification clone. It happened **twice on 2026-08-09**, in two repos, to two sessions:
  theirs put `cp` and `./init.sh` in the clone (presenting as filesystem corruption — one
  inode for two paths, ten minutes lost to suspecting a sandbox overlay); this repo's
  session ran kit greps inside cs-toolkit and briefly "found" `CS_TOOLKIT_SESSIONS_DIR` in
  the kit's `dev_session.sh`. The panel contract has this rule for lenses; **no workflow has
  it**, and `upgrade.md` sends the operator to a second tree and then speaks in relative
  paths.

**And their sixth learning was about this session's own prompt.** Source: that session's
memo, delivered as a rendered artifact rather than committed anywhere — see the provenance
note below, which is the more useful half. It reports that the prompt's opening precondition
("on branch `codex/support-docs-launch-refresh` with uncommitted work") was false at run
time: the repo was on a clean `main`, and the branch held seven *committed* commits with no
worktree.

Both checkable halves hold, and here are the commands. The branch is seven commits ahead —
`git rev-list --count origin/main..origin/codex/support-docs-launch-refresh` → `7`. And the
precondition was true when written: the session that wrote the prompt measured
`git status --porcelain | wc -l` → `9` on that branch, minutes before. So nobody was wrong;
the state moved between the measurement and the reading. That is the point: **a precondition
in a brief is an observation with a timestamp**, the Phase 3 memo's rule about shas
generalised — and it bites hardest when the false precondition authorises a *protective*
manoeuvre, because the protection is what gets applied to a state that no longer exists.

**`#380` and `#397` are the same file**, which makes them one session — and `init.sh` work
is disjoint from `cluster:merge-gate`'s `pr_watch.py`, so the two can run in parallel lanes.

▶ Next: **`cluster:merge-gate`** — `#190` and `#39` together (one guard, one change), then
`#95` separately — **and `#380`+`#397` as a parallel lane, since `init.sh` and
`pr_watch.py` do not touch.** Superseding the pointer below: `#388` has no *current* consumer now that
cs-toolkit has unpinned `init.sh` — it remains the named **future** one, and will hit this
the next time it pins a file — while `#363` waits behind a gate that can currently be
defeated three ways.

______________________________________________________________________

▶ Superseded by the sweep above, kept for the reasoning: **`#388`, then `#363`.** `#388` has a named consumer — cs-toolkit will hit it the
next time it pins a file, and re-running `--record-install` there silently undoes the
hand-maintained entry it keeps because of this — and its shape is decided: a third state
beside `files` and `not_installed`, plus a refusal that does not take the declared scope
with it. `#363` is the Claude registration hardening the adopter carried rather than
forking, and `#389` has now shipped the instrument that would report it dead.

______________________________________________________________________

## Session — 2026-08-08 (the tenth triage sweep, and what re-derivation changed)

**Theme —** The friction inbox graduated to the tracker. The sweep's value was in the
routing rather than the volume: reading the tracker before drafting changed two of the
seven entries' destinations, in opposite directions.

- **PR `#375` merged (`453900e`).** The inbox is swept into
  `docs/kit-friction-log-archive.md` under `Graduated 2026-08-08`; the active file keeps
  its H1, intro and the new marker. Run in LLM-only mode — `#6`'s engine is still not
  vendored, so the parse, draft, sweep and PR were done against the workflow prose by hand.
- **Filed this session: `#370`, `#371`, `#372`, `#373`, `#374`, `#376`.** Occurrence
  comments on `#305` and `#115`. The cockpit mutation-harness entry needed no write —
  `#326` already carried both the occurrence and its "do not mutate the live tree" reframe.
- **The approval binds to what the operator saw.** Session A stored the drafted proposals;
  Session B replayed those against the DM reply rather than re-deriving them. Every write
  was re-read from the tracker after landing per `#138`, compared **by body**, with both
  commented issues confirmed still open.
- **The archived text round-trips byte-exact against the draft-time snapshot**, and that
  snapshot still matched the live inbox at finalize — checked in
  `/Users/topi/Coding/agentic-dev-kit` before the commit, so no entry was swept unfiled and
  nothing was added in the draft window.

**Learned**

- **An entry can read as already handled and not be, and grep is what gets it wrong.** The
  `panel_prompt.py` entry said the panel doctrine never names the engine. `git grep
  panel_prompt` now hits `fallback-review-panel.md`, so a grep-level check would have
  archived it as done. That hit is inside a `lens_compute` config aside; "Running it" step 2
  still tells you to hand-author every lens prompt. The claim's *wording* went stale while
  its substance stood — the opposite direction from a claim that is simply false, and only
  re-derivation separates them. `#373`.
- **The bot was available, and reproduced two of its own tickets while being so.** After
  four sessions of quota outages CodeRabbit reviewed this head clean, so no panel was
  warranted — treating a successful review as an outage is the inverse of Principle #5's
  error. Its clean verdict arrived as a comment rather than a review, leaving `coverage`
  empty (`#44`), and `mergeable` then demanded a receipt that no configured literal honestly
  describes (`#350`). Recorded `coderabbit`, per this repo's own receipt history, rather than
  asserting a `fallback:` pass that never ran.
- **Four entries were one story and did not want one ticket.** The quota cluster split by
  what each part actually routes to: the missing observability (`#370`), a false claim in
  `config/dev-model.yaml` about the panel being "the real substitute" (`#371`), and the
  operator decision itself (`#372`) — which four entries had deliberately declined to file,
  and which needed a home once its evidence moved to the archive.
- **A workflow that DMs through the operator's own token cannot tell its own messages from
  theirs.** Every message in the thread carried the operator's user id, including the
  skill's "still waiting" reminder — whose text contains a bare `skip`, which the skill's
  own grammar defines as bulk-cancel. An engine implementing that grammar literally would
  read its own reminder as the operator aborting the batch, and say so with a success
  message. `#376`.

**Open, and owned by nothing yet**

- **`#358` is the remaining pre-Phase-3 item** — untouched by this session.
- **The friction inbox holds no un-graduated entries**; this session's own finding was
  issue-shaped and went to the tracker as `#376` rather than to the inbox.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#376`, `#374`, `#373`, `#372`, `#371`, `#370`, `#368`, `#367`,
  `#365`, `#364`, `#363`, `#358`, `#356`, `#350`, `#346`, `#304`, `#291`, `#290`, `#287`,
  `#283`, `#273`, `#243`, `#248`, `#264`, `#236`, `#231`, `#213`, `#209`, `#211`, `#120`,
  `#216`, `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`, `#46`, `#36`.

▶ Next: **`#358`, then Phase 3 in cs-toolkit** — unchanged by this session; the block below
carries the detail, including what that session must do beyond the upgrade.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

