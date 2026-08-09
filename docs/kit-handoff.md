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

Last updated: 2026-08-09 — **cs-toolkit's Phase 3 is merged and its findings are worked
back into the kit.** Six of its seven issues are closed — `#385` (the one with an adopter
blocked behind it), `#382`, `#383`, `#379`, `#381`, `#386` — across four merged PRs.
`#380` is the seventh and is blocked on a Codex CLI this host cannot start. Four issues
are new: `#388`, `#392`, `#393` and `#395`. The adopter can take `init.sh` again — `#385`
carries the measured before/after and the refresh steps. The convergence plan now records
Phase 3 as done and carries the two defects a session following it found.

## Latest session — 2026-08-09 (the adopter's Phase 3 findings, worked back into the kit)

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

▶ Next: **`#388`, then `#363`.** `#388` has a named consumer — cs-toolkit will hit it the
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

## Session — 2026-08-08 (the adopter's memo, checked rather than executed)

**Theme —** cs-toolkit's Phase 0 handed the kit a memo of findings. Two of its
load-bearing claims did not survive being re-derived, and the work that followed was
smaller and better aimed than the memo proposed.

- **PR `#361` merged.** Facts in `docs/kit-convergence-plan.md` and this file that a
  reader would have acted on: Phase 3 no longer waits on cs-toolkit; "the only divergence
  currently invisible to tooling" was false, `init.sh` being the counterexample; and
  `adopt`/`upgrade` already have shared definitions with bindings on both runtimes since
  `#330`. The adopter memo is committed beside the plan as
  `docs/adopter-forcing-function-memo_2026-08-07.md`, preserved as the adopter's account
  with its superseded recommendation marked rather than rewritten.
- **PR `#362` merged — `#360` closed.** `init.sh` is tracked in `KIT_OWNED` and the
  manifest, so the file that performs every install is inside the measurement. Verified
  with `make test` in `/Users/topi/Coding/agentic-dev-kit`, and end-to-end by running the
  new doctor with `--root` against `/Users/topi/Coding/in-parallel/cs-toolkit`.
- **PR `#366` merged — `#359` closed.** The Codex registration no longer runs `python3`
  against a path built from an empty string. Both surfaces changed together because
  `test_the_advisory_matches_the_registrations_it_describes` requires it.
- **Filed this session: `#363`, `#364`, `#365`, `#367`, `#368`.** Occurrence comment on
  `#350`; the measurement that refutes `#358`'s proposed remedy is a comment on `#358`.

**Learned**

- **The memo's two false claims failed in opposite directions, and both came from reading
  a document instead of the tree.** It reported the kit has no coverage of the hook
  registrations — it has two real tests, and the true gap is that they compare *text*,
  which is *why* `#359` shipped: when the command string itself is wrong, the advisory and
  the shipped file are wrong identically and every equality holds. And it recommended
  promoting `adopt`/`upgrade` extraction to a hard Phase 3 gate, which `#330` had
  finished — taken from this repo's own stale plan section. **A stale plan does not merely
  misinform; it produces confidently-scoped work that does not need doing.**
- **`#360`'s design question dissolved instead of being decided.** Its three-way choice
  rested on an adopter's `init.sh` being *expected* to diverge. cs-toolkit's copy is
  byte-identical to kit commit `7485512b`, so the delta is version drift with no local
  rendering — which makes a tracked copy report `stale`, not `locally-edited`. No new role,
  no file split.
- **`KIT_OWNED` lives in the engine, not the manifest**, so `--manifest` cannot backport a
  newly tracked path. Found by running the adopter's *own* vendored doctor first and
  getting a different file list than the kit's.
- **Every panel round found the previous round's fix weaker than it claimed** — a regex
  guard defeated by execution, a parametrization that exercised a flag without reaching its
  branch, a positive control that did not discriminate its own path, a stub whose harness
  could break silently, and an assertion that could never fail. The doctrine predicts this
  about fix rounds; it held every round.
- **A mutation harness can report kills that never happened.** Cloning a branch before
  committing the fix meant the revert step restored the *unfixed* file, so two reported
  kills were that state failing again — and they were hiding two genuine coverage gaps.
  `#367`.
- **A stale PR *description* is worse than a stale comment**, because a reviewer reads it
  top-down before the diff. `#366`'s body asserted a rationale the code had already
  retracted.
- **One finding was beyond anything this machine could run:** the `exec` control in a new
  test was shell-dependent, and `/bin/dash` — `/bin/sh` on most Linux runners — tail-call
  optimises where the local shell forks. It would have failed there and passed here.

**Open, and owned by nothing yet**

- **`#358` is the remaining pre-Phase-3 item** — two prose paths plus a coverage question
  whose proposed remedy is refuted on the ticket, with the viable narrower form identified.
- ~~**The friction inbox still awaits `triage-friction-log`**~~ — **swept 2026-08-08**, see
  the block above; nothing was added to it this session, because everything issue-shaped
  was filed to the tracker instead.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#368`, `#367`, `#365`, `#364`, `#363`, `#358`, `#356`, `#350`,
  `#346`, `#304`, `#291`, `#290`, `#287`, `#283`, `#273`, `#243`, `#248`, `#264`, `#236`,
  `#231`, `#213`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`,
  `#169`, `#143`, `#46`, `#36`.

▶ Next: **`#358`, then Phase 3 in cs-toolkit.** `#358` is two lines in
`fallback-review-panel.md` plus the doctrine-scoped guard its comment thread already
measures. Then Phase 3, from a session rooted in `/Users/topi/Coding/in-parallel/cs-toolkit`
— read `docs/kit-convergence-plan.md`'s pre-Phase-3 section first. What that session
must do beyond the upgrade: install `docs/agentic-dev-kit/workflows/adopt.md` and
`upgrade.md` there (its manifest lists both as declined, so it has no installed workflow
doc to follow), and refresh its vendored `kit_doctor.py` — until that is replaced, its own
doctor cannot see `init.sh` however current the manifest is.

______________________________________________________________________

## Session — 2026-08-07 (`#353`, and a boundary its author could not settle)

**Theme —** A two-paragraph doc correction whose own review ran four rounds, found two
defects the branch had introduced, and ended on a classification the author was
disqualified from deciding.

- **PR `#353` merged (`63dd892`).** `docs/kit-convergence-plan.md` corrected on two
  facts a cs-toolkit session would have acted on: that repo registers the hook
  `$CLAUDE_PROJECT_DIR`-relative, not by absolute path as the plan said, and the hook's
  import closure is one module already vendored there byte-identical, so Phase 0 carries
  one file rather than a file plus dependencies. Verified with `make test` in
  `/Users/topi/Coding/agentic-dev-kit`, re-run at each committed head.
- **Its review found two regressions this branch introduced, and fixed both.** Round 1
  (full panel): the corrected measurement left the Agreed-sequence bullet contradicting
  it. Round 2 (full panel): the `Verified state` header's date range no longer covered a
  paragraph the branch had inserted under it.
- **A lens disputed the author's safety-critical draw; the operator upheld it.** Round 3
  was a single-lens record-prose delta pass, which confirmed the prose class and disputed
  the boundary. The operator's resolution is on the PR — required to be theirs, not a
  relayed account. Round 4 ran the dual form's second lens; both lenses confirmed both
  draws. Receipt `fallback:delta`, both lenses, bound to `2475dbd` — the head that
  merged, which the squash then rewrote.
- **CodeRabbit was rate-limited on both surfaces throughout and its coverage stayed
  empty**, so the panel carried this review end to end.
- **Filed this session: `#356`.** Occurrence comments on `#346` and `#120`.
- **`#352`, `#354` and `#355` landed on `main` during this session from elsewhere** —
  not this session's work; recorded so the trail has it.

**Learned**

- **The dual form leaks its own independence, through artifacts the doctrine mandates.**
  The second delta lens read the first's verdicts by running `gh pr view` to check
  whether the operator resolution artifact existed — an artifact the doctrine requires,
  on the surface the doctrine requires the verdicts to be posted to. It disclosed this
  unprompted, and nothing else would have caught it: the exposure leaves no trace in git,
  the receipt, or `pr_watch` state. So that receipt's draw-2 disjointness is self-attested
  rather than structural, which is said on the PR. `#356`.
- **One passage, four consecutive fix rounds, each introducing a fresh defect into the
  text it was repairing** — `45d7b05` → `a7ec719` → `9fed796` → `e623196`. The first two
  are pre-squash commits from the branch that landed as `274eed9`: real, reachable in the
  object DB, not ancestors of `main`. `#305`'s argument with better evidence than `#305`
  carries.
- **A planning document reached the safety-critical class by argument, never by
  binding.** The path list names four engines; it names neither this document nor the
  hook whose relocation the document instructs — and that hook cites the doctrine in its
  own docstring. `#346`.

**Open, and owned by nothing yet**

- **The critical path is unchanged and still leaves this repo**: Phase 3 needs
  cs-toolkit's Phase 0 and its fixer predicate. Both re-verified live this session — the
  fork is still 66 lines at `scripts/hooks/`, `.codex/hooks.json` is still absent, and
  that repo's `pr-watch.md` still reads `done`.
- **The friction inbox is over budget and its triage is overdue**; this session added a
  fourth consecutive occurrence to its bot-quota entry, which is the decision the sweep
  is waiting on.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#356`, `#350`, `#346`, `#304`, `#291`, `#243`, `#273`, `#290`,
  `#283`, `#287`, `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`,
  `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: ~~**cs-toolkit's Phase 0**~~ — **done 2026-08-07**, merged there as `2ab63d255`.
The block above is left as written: it is an accurate record of what was true that day,
and its "still leaves this repo" reading was correct until Phase 0 merged that evening.
The live next step is in the 2026-08-08 trail at the top of this file — the three kit
items Phase 0 surfaced (`#360`+`#304`, `#359`, `#358`), then Phase 3.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

