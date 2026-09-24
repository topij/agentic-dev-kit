# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **What lands here is what is not yet issue-shaped.** A finding that already carries a
> reproduction, a named mechanism and a proposed fix is filed straight to the tracker by
> `wrap-up`'s friction-routing step, on the operator's go-ahead, rather than parked here
> — and parks here anyway when that route is unavailable — which is the routing Principle #2 prescribes,
> not a neglected inbox. What stays is the remainder: findings still missing one of those
> three, and single instances of a shape that only matters if it recurs.
>
> **Position alone does not tell you what is un-graduated, and this file does not
> pretend otherwise** ([`#224`](https://github.com/topij/agentic-dev-kit/issues/224)).
> New entries are appended at the *top*, so the dated sections above the most recent
> `## … — Backlog migrated` marker are un-graduated. But a sweep does not archive
> everything it passes over: an entry added *between* a triage run's draft and its
> finalize is recognised as new and deliberately **kept in this file, below the new
> marker**, ready for the next pass rather than archived unfiled. So the un-graduated
> set is everything above the newest marker **plus anything kept below it**, and a
> dated section below a marker is that safety mechanism working — not a straggler.
> Each marker's own block records what it swept.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-09-24

- **A restarted `post-merge-systemize` run resumed a `running` heartbeat without calling
  `start`.** In PHASE5-D-SYSTEMIZE-RECOVERY-02 (synthetic, 2026-09-24, workflow at
  `c1d513e`), the fresh restart `N2` reused the killed run's artifacts. It sent `tick` and
  then `complete` to the heartbeat that an earlier process had left `running`, so the
  final state reads `restarts: 0` after a restart. The restarts `P2` and `D2` called
  `start`. Evidence is in `state/review-evidence/phase5-d-systemize-recovery-02/RESULTS.md`
  (local, gitignored).
  - **Mechanism, probable:** Step 1 says to start the heartbeat "before the fetch", and a
    resume that reuses the raw bundle has no fetch. The workflow's resume guidance does
    not say whether a restart must call `start`. Combined with #783 (`start` reopens a
    completed run), a restart has no clear heartbeat entry point.
  - **Why it is parked:** it is one instance, and the point is whether it recurs.
  - **Severity:** L. `restarts` under-counts, and nothing reads it yet (#747).

- **A headless agent recorded a synthetic approval under the real operator's name.** In
  the same package, runs given an approval sentence labelled "SYNTHETIC TEST APPROVAL"
  filled the dispatch record's approval evidence with the session's git or account user,
  by name and once by email, although the sentence named no one.
  - **Mechanism, probable:** *External dispatch records* asks for "who approved", and the
    agent inferred that from the ambient identity rather than from the approval itself.
  - **Direction:** record the approval text and where it arrived, rather than an
    inferred identity.
  - **Why it is parked:** in real use the session user usually is the operator, so this
    may only matter to synthetic runs. It is one instance, and the point is whether an
    inferred identity misleads in real use.
  - **Severity:** L.

- **The first two fallback-panel rounds on #790 each found another unpinned fail-closed
  clause.** #790 added normative prose to `post-merge-systemize.md` and pinned part of it
  in `_assert_post_merge_semantics`. The adversarial lens at `2b9dae8` and again at
  `ae54d68` proved, by a surviving mutant, that another guarding clause was not pinned.
  Only at `d873b68`, after every fail-closed clause in the section was pinned with an
  inverting mutation, did a round find no unpinned clause.
  - **Why it is parked:** it is one instance, and the point is whether it recurs. If it
    does, a candidate rule is that a change adding normative workflow prose pins every
    fail-closed clause in the first commit, not only the ones the author considers
    central.
  - **Not established:** whether the partial first pinning was an authoring slip or
    something the panel doctrine could prompt.
  - **Severity:** L. Each round cost a full panel, and no defect shipped.

- **A fresh Codex context ran `post-merge-systemize` out of the workflow's order in two
  places.** This was PHASE5-D-FRESH-CONTEXT-01: `codex exec` given only
  `$post-merge-systemize test`, run on 2026-09-24 in a clone at `1cc86cd` plus one config
  commit. The evidence is `state/review-evidence/phase5-d-fresh-context-01/RESULTS.md`
  (local, gitignored).
  - **Preflight:** it made no bounded merged-PR read of its own before heartbeat
    `start`. It ran only `gh auth status`, `gh repo view` and the branch API. Its report
    then marked "Forge merged-PR read" `ready`, citing the fetch engine's read, which
    came after `start`. The workflow says to finish preflight before any heartbeat
    write.
  - **`--verify`:** it ran digest `--verify` after the ticks and the report write. The
    *Engine interface* lists `--verify` under the digest step but does not say it must
    precede the ticks.
  - **Why it is parked:** it is one instance, and the point is whether it recurs. It is
    not established whether the order is too easy to miss, or whether the engine-backed
    path should name what proves forge access before `start`.
  - **Severity:** M. A capability was reported `ready` on evidence gathered after the
    point the workflow requires.
  - **Related occurrence, confounded, 2026-09-24:** in PHASE5-D-SYSTEMIZE-RECOVERY-02,
    both attempts of run `Q` did try a bounded merged-PR read before `start`
    (`gh pr list --state merged`). The package's fake forge did not answer that form, so
    the agent reported the capability `ready` citing the fetch engine's later read. The
    agent attempted the read in the right order, and the harness caused the rest, so this
    does not establish a recurrence of the ordering. It does show the same
    ready-from-a-later-read fallback.

- **`codex exec` writes a `trust_level = "trusted"` entry for its working directory into
  `~/.codex/config.toml`, even under `--ignore-user-config --ephemeral`.**
  - **Observed** on 2026-09-24, with codex-cli 0.153.4 and the ChatGPT desktop app
    running, for three working directories: a preparation clone, a gate probe clone and
    the PHASE5-D-FRESH-CONTEXT-01 run clone.
  - **The write can land late.** SHA-256 hashes taken before the first probe and right
    after the second were identical, yet an entry for that probes' directory was
    present later.
  - **Cleanup:** the three entries were removed with a guarded edit, on the operator's
    approval. The file's SHA-256 afterwards matched its value before the first probe.
  - **Probably accumulating from kit review lenses.** On 2026-09-24,
    `grep -c -E '^\[projects\."/private/(tmp|var)/[^"]*lens-' ~/.codex/config.toml`
    printed `19`, which suggests the kit's Codex review-lens launches leave these
    entries behind. None of those entries was touched.
  - **Not established:** whether the CLI or the desktop app's Codex service writes them.
  - **Proposed direction:** remove an entry after the launch that caused it, or run
    lenses under a separate `CODEX_HOME`. Neither has been tried.
  - **Severity:** L. The paths are temporary and mostly random-suffixed, but a trusted
    path that is later reused would load that directory's project config and hooks.

## 2026-09-23

- **`heartbeat_cli.py start` reopens a completed run, though the workflow calls a write
  after completion a hard stop.** A unit-level probe used the kit's own test helpers
  (`make_repo`, `fake_env`, `run_engine`) in a temp repo, against `66a8a10`, on
  2026-09-23. It ran `start`, then `complete --reason complete`, then `start`. All three
  exited `0`, and the final state read `status: running`, `restarts: 1`,
  `exit_reason: null`. The probe and its output are in
  `state/review-evidence/phase5-d-systemize-recovery-prep-20260923/heartbeat-start-after-complete/`
  (local, gitignored).
  - **Mechanism:** `Heartbeat.start()` in `scripts/lib/systemize/heartbeat.py` replaces
    any same-identity state without reading its `status`, whereas `tick` and `complete`
    both check it. `test_a_same_identity_restart_counts_and_resets` covers restarting a
    *running* heartbeat only.
  - **Proposed fix:** a design choice between two options:
    - refuse `start` on a completed state, so that rerunning the same date needs an
      explicit step;
    - amend the workflow's *Engine interface* to say that `start` deliberately reopens
      a same-identity run.
  - **Why it is parked:** it is issue-shaped, but the session that found it ran
    unattended, so nobody could approve a tracker payload.
  - **Filed as #783** on the operator's direction, 2026-09-24.
  - **Severity:** L. The heartbeat is progress state, and the scheduler wiring that
    would act on it is #747's scope.

- **A handoff archive sweep left an extra blank line at the end of the handoff.** On
  branch `chore/update-handoff-2026-09-23` (from `b808061`),
  `uv run scripts/archive_plan_sessions.py --target-lines 400` exited `0` and moved the
  2026-09-09 session blocks into the history file. The handoff then ended with its final separator line
  followed by an empty line. At `b808061` it had ended directly after that separator.
  `git diff HEAD --check` reported `new blank line at EOF`, and the wrap-up trimmed it
  by hand.
  - **Not established:** which code path adds the line, and whether every sweep does it.
    So this is parked rather than filed.
  - **Recurred** the same day, in the D-SYSTEMIZE-LIVE wrap-up on branch
    `chore/update-handoff-2026-09-23-systemize-live` (from `5165a3c`):
    `uv run scripts/archive_plan_sessions.py --target-lines 400` exited `0` after moving
    the 2026-09-09 blocks, and `git diff HEAD --check` reported
    `docs/kit-handoff.md:399: new blank line at EOF`. Trimmed by hand again.
  - **Diagnosed in #776.** `history_pointer()` ended the generated footer with a blank
    line, and the reader matched the footer only with that line present. So every
    sweep added the line, and a hand-trimmed footer was swept into the history file.
  - **Severity:** L.

## 2026-09-13

- **The panel path test overstates which declaration it protects.** The independent
  correctness review at fixture `12d7d4b41abe75451ed74d7cbc068bc6b8be2db7` on
  2026-09-12 UTC classified this as **L / P3 coverage-claim imprecision**, not a
  demonstrated production regression. `test_the_declared_path_matches_the_doctrine_path`
  compares `DOCTRINE` to another literal, without observing the `require_kit_paths`
  argument in `doctrine_text()`. Changing that argument to a missing path left the
  assertion passing while dependent tests skipped in the selected panel/marker modules.
  The [execution record](../saved_plans/phase5-item5-b-pr02-execution_2026-09-13.md)
  binds the full local report and mutation/restoration evidence; complete-mutant-suite
  survival was not established. Proposed remedy: observe the actual declaration, or
  narrow the claim if that protection is deliberately out of scope.
  `gh search issues '"test_panel_prompt" "require_kit_paths"' --repo topij/agentic-dev-kit --limit 30 --json number,title,url,state`
  in `/Users/topi/Coding/agentic-dev-kit` at
  `083bccbfa4c4b066d82e7625ddf1efe70716dd2d` on 2026-09-13 local date returned
  `[]`; this bounded search does not prove no duplicate exists. Pending an exact
  scope decision: the approved continuation excludes additional fixture fixes and
  tracker payloads, and the operator requested autonomous finalization before sleep.
  No fix, tracker write or waiver is established by this entry; the sweep stays parked.

## 2026-09-11

- **Case-insensitive report paths overwrote a completed review report.** During
  PR #733's final adversarial review on 2026-09-11, the reviewer wrote `REPORT.md`
  while the launcher used `codex exec -o report.md` in the same scratch directory.
  Those names aliased on the filesystem, so the launcher's final-summary write
  replaced the full report. **L** — the complete reviewer-authored text remained
  in a completed command in `events.jsonl`; shell-token and Python-AST literal
  parsing recovered it without executing the command. The
  [complete receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5639699233)
  preserves that recovery before merge. Proposed remedy: give the reviewer report
  and launcher summary distinct basenames and check their destination identities
  before launching. This was session review orchestration, not an established kit
  engine defect. `gh search issues --repo topij/agentic-dev-kit` with queries
  `"case-insensitive" "report"` and `"REPORT.md"`, including PRs, at
  `fc46efa0570f866f19cccf11834f909d5f37cf69` on 2026-09-11 in
  `/Users/topi/Coding/agentic-dev-kit` returned no match for the combined query and
  PR matches for the filename query; no collision issue was identified by
  that bounded search. Parked because the operator excludes tracker payloads from
  this work. No tracker write or friction sweep is authorized by this entry.

- **The review runtime stopped before delivering required adversarial coverage.**
  PR #733's [receipt at `88c5b044d5a42e33d2c4b0158be0957b4014678a`](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633065607)
  and [receipt at `207683b073f4d34cf22c5d9e1635f1c23239b6d4`](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633204702)
  preserve the actual `codex exec` argv, private review directories, compute readback
  and terminal cybersecurity-content flags on 2026-09-11. **M** — required review
  could not reach a final report. The runtime supplied no classifier diagnosis;
  no kit mechanism or repair is established. Parked for runtime-access diagnosis,
  with the unfinished commands distinguished from completed verification. No
  tracker payload or sweep is authorized by this record, and incomplete coverage
  is not merge clearance.

## 2026-09-09

- **ITEM5-B exposed a drift-check applicability mismatch after #705.** The
  [approved execution](../saved_plans/phase5-item5-b-execution_2026-09-09.md) retains
  the installed runner's complete command, fixture/source SHAs, output and failure
  excerpts. **M** — `test_the_drift_test_actually_executes` requires its child never
  to skip, while #705 added `require_kit_source()` to that child so an adopter's
  recorded baseline intentionally skips it. Proposed repair: align the parent's
  applicability with the child and prove the liveness check still detects an improper
  skip in a kit source tree. The same execution retains config/adapter assumptions
  already represented on #534; neither class is #393. Searched the exact parent test
  name with `gh search issues` and read #534's body and comments on 2026-09-09 at
  `edc199f42bc65b1850172ea79b791ef358577ae1`; the search returned no matching item,
  while #534 supplies the cross-test and kit-only-invariant scope. Parked for an exact
  occurrence-payload decision because the operator went to sleep; no tracker write.

- **A review suite encountered undecodable process-list output.** PR #725's
  [initial receipt](https://github.com/topij/agentic-dev-kit/pull/725#issuecomment-5607994984)
  retains the adversarial lens's `make test` result and targeted retry at
  `edc199f42bc65b1850172ea79b791ef358577ae1` on 2026-09-09 in its independent scratch
  clone. **L** — the launcher raised `UnicodeDecodeError` while reading process-list
  output; the targeted retry passed, and the raw offending process bytes were not
  captured. Parked for accumulation rather than asserting a reproducible repair.
  Keep this environment-dependent observation separate from #393 and ITEM5-B's
  installed-test failures.

- **A review lens wrote into the tree it was handed, disclosed it, and restored it.**
  Round 2 of `#717`'s panel ran `git checkout <base> -- docs/kit-friction-log.md` inside
  its own handed worktree to compare `check_doc_budget.py` output across revisions, then
  restored the file and said so in its report. The cockpit verified the restoration at the
  destination rather than accepting the attestation: `git status --short` empty and `HEAD`
  unmoved in both lens worktrees, and `shasum -a 256 docs/kit-friction-log.md` identical
  across both worktrees and the cockpit tree. **M** — mechanism: *No writes in the tree you
  were given* forbids checking out what you were handed, and *Right revision* supplies
  `git show <sha>:<path>` for **reading** a past revision, but a lens that needs to run a
  *script* against past content has no sanctioned route and the writable-copy guidance is
  framed entirely around mutation testing. Proposed fix: say that comparing a command's
  output across revisions goes through an extract to a scratch path, never a checkout in
  place. **Routed 2026-09-09 to
  [`#574`](https://github.com/topij/agentic-dev-kit/issues/574#issuecomment-5604328385) as
  a third occurrence, on the operator's go-ahead**; that issue stays open. `#574` already
  holds this exact shape — a contract obligation with no sanctioned no-write route, the
  lens self-disclosing — for two `git fetch` occurrences, and the comment widens it past
  base currency rather than opening a second issue. Searched `#254` and `#712` first and
  neither fits: `#254` is the destructiveness of `git checkout --` over uncommitted work,
  which was absent here, and `#712` is a lens reaching **outside** its tree, where this
  lens stayed inside its own.

- **A lens corrected its own report after the receipt for that round was already
  written.** The round-1 adversarial lens reported its pytest phase as reaching no terminal
  result, the receipt recorded that, and the lens then finished and reported `1 failed,
  2484 passed, 1 skipped in 424.47s` at `06ff7d7`. **M** — mechanism: a receipt is
  head-bound and written once, `#666`'s ordering requires it before that round's fixes, and
  nothing defines a route for a lens that resumes and amends its report afterwards. The
  cockpit restated it in the next round's disposition, which works only because there *was*
  a next round; a corrected report after the final round would have no carrier at all.
  Proposed fix: name this case in the panel doctrine's recording step. **Filed 2026-09-09
  as [`#719`](https://github.com/topij/agentic-dev-kit/issues/719), on the operator's
  go-ahead.** Worth noting it is also an instance of the rule `#717` shipped as `b866298` —
  outside state falsified a sentence in a record already published.

- **`--lenses` takes one comma-separated value and the doctrine's example reads as
  space-separated.** `pr_watch.py 717 --record-review "fallback:panel" --lenses adversarial
  correctness` exited on `error: unrecognized arguments: correctness`; the comma form
  worked. **L** — mechanism: the option is single-value argparse, while
  `fallback-review-panel.md`'s code block writes the placeholder as
  `--lenses <names of the lenses that actually ran>` and its prose says "names", both of
  which read as `nargs='+'`. Proposed fix: write the literal `--lenses adversarial,correctness`
  in that block. Fail-closed and caught immediately, so the cost was one invocation.
  **Filed 2026-09-09 as [`#720`](https://github.com/topij/agentic-dev-kit/issues/720), on
  the operator's go-ahead.**

- **A lens imposed its own timeout on `make test` and killed its run, with the warning
  against it already in its reach.** The round-1 adversarial lens wrapped the suite in
  `timeout 300` and lost the run, then reported a verification limit; `AGENTS.md`'s
  *Verification* says to raise the tool timeout before starting, and the lens named that
  warning itself when reporting the kill. **L** — no mechanism beyond "the instruction
  exists and did not bind", which is the carrier-not-wording shape of `#469` and of the
  progress-update entry already in this inbox. Parked for accumulation; if it recurs,
  capture whether the lens had an unbounded alternative it declined.
  **Reconciled 2026-09-09 under #722:** the operator confirmed that a foreground
  alternative was available and omitted. The park condition is discharged to the
  [#578 occurrence](https://github.com/topij/agentic-dev-kit/issues/578#issuecomment-5605922954);
  reconcile this entry during triage rather than re-filing it.

- **Desktop hook testing looped on app mode while the task used another config.**
  During the [hooks continuation](../saved_plans/codex-hooks-continuation_2026-09-09.md),
  guidance repeatedly asked the operator to identify or switch windows from their
  appearance. The supplied Codex view did not identify its effective config; the
  recorded fixture task used the ordinary profile with hooks explicitly enabled.
  A private profile's saved mode was then overinterpreted as the explanation for
  the operator's window. **M** — mechanism: app identity, UI mode and task/config
  identity were treated as interchangeable observations. Proposed direction: bind
  the actual task's cwd and configuration before directing another UI step; use
  the available task API for the bounded test once its target is established.
  Parked because the operator went to sleep before wrap-up and no exact tracker
  payload was approved. This adds an occurrence without sweeping existing entries.
  **Reconciled 2026-09-09 under #722:** the operator subsequently approved the
  exact payload, filed as [#721](https://github.com/topij/agentic-dev-kit/issues/721).
  That filing discharges the parked tracker decision; triage reconciles it rather
  than creating another issue.

- **A following shell line committed after staged validation failed.** During this
  wrap-up, `git diff --cached --check` rejected trailing whitespace in a copied
  pytest log, but the following `git commit` still ran because the shell command
  did not stop on the Python validator's failure. **L** — the unpublished record
  was corrected; the log now declares its whitespace-only transformation. Keep
  dependent commit work in a later tool call after reading validation, as the
  wrap-up workflow already prescribes. Parked for accumulation; no tracker write.
  **Recurred during ITEM5-B on 2026-09-09:** the combined validation/commit command
  again continued after `git diff --cached --check` flagged raw transcript whitespace,
  producing `38af832b8d044a12866dcdfb0ab3346558b392a2`. Those raw bytes were retained;
  an explicit raw-log exclusion and separate authored-file check were read afterward.
  Subsequent commit work moved to a separate tool call. No new tracker write.

## 2026-09-07

- **`make test` fails on `main` in a way CI cannot see, and not always on the same test.**
  `make test` at `4b56d3eec285781ac382e0b897d5d1da9c7fe40e` (clean `main`) on 2026-09-07
  printed `1 failed, 2445 passed, 1 skipped in 379.54s`, failing
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`. It
  passes in isolation every time. Review lenses measured it independently across the
  session and did not agree: one got a *different* single failure
  (`test_reconcile_sessions.py::test_portable_bounded_runner_reaps_on_startup_interrupt`)
  from base-content files under concurrent load; one got no failure at all on a repeat run
  at an identical sha; others reproduced this same one. The disagreement is the finding. `uv run python -c "import sys; print(sys.version)"` in
  `/Users/topi/Coding/agentic-dev-kit` on 2026-09-07 printed `3.14.7`, while
  `.github/workflows/test.yml` pins `python-version: "3.12"`. `#393` records that `json`'s
  `RecursionError` behaviour changes at 3.14 and names a *different* test. **M** — the
  interpreter split is a candidate contributor, not an established mechanism, and the
  non-determinism is unexplained. **Routed 2026-09-08 to
  [`#393`](https://github.com/topij/agentic-dev-kit/issues/393#issuecomment-5579081191) as
  an occurrence, on the operator's go-ahead**; that issue stays open. Worth recording
  either way: a red local suite that CI reports green trains a session to discount its own
  verification command.

- **A genuinely unparseable `scripts/hooks/pre-push` passed `make test`.** `check-syntax`
  hands four filenames to one `bash -n`, and `pre-push` is last on that line, so it is
  never parsed — locally or in CI. Measured on 2026-09-07: `bash -n good.sh bad.sh` exits
  0 with a syntactically broken `bad.sh`, while `bash -n bad.sh` alone exits 2. `#561`
  already names the mechanism; what this adds is the blast radius — the hook runs on every
  push here and in every adopter, so a broken one ships through a green suite. The hole for
  that one file is now shut by `#709`, with `test_the_hook_parses_on_its_own`. **M** —
  **routed 2026-09-08 to
  [`#561`](https://github.com/topij/agentic-dev-kit/issues/561#issuecomment-5579077909) as
  an occurrence, on the operator's go-ahead.** That issue stays open and remains the
  general fix; the comment carries the blast-radius evidence for raising its priority.

- **The parse failure itself: bash 3.2 mis-parses an apostrophe inside a quoted heredoc
  within `$( )`.** Reproduced minimally on `GNU bash, version 3.2.57(1)-release
  (arm64-apple-darwin25)` — macOS's default, and what `#!/usr/bin/env bash` selects there
  — where a `$(python3 - <<'PY' … PY )` block whose body contains one apostrophe in a
  *Python comment* fails with ``unexpected EOF while looking for matching `'``. The
  existing config-read block in the same file has always avoided apostrophes, which now
  reads as deliberate but was nowhere stated. **L** — single instance, mechanism
  identified and commented in place; recorded because the failure presents as a broken
  heredoc rather than as a quoting rule.

- **`cp -a` of a linked git worktree does not isolate it, and the panel contract does not
  say so.** A review lens built its mutation scratch that way; the copied `.git` is a
  *pointer file* naming the same per-worktree admin directory, so `git stash` and
  `git checkout` run inside that "copy" wrote straight into the given tree's index. File contents were never
  altered, the lens detected and repaired it, and the cockpit independently confirmed the
  tree clean, index empty, HEAD unmoved and both changed files hash-matching the manifest.
  **M** — proposed fix: *No writes in the tree you were given* should name the mechanism,
  because the rule as written ("use an absolute path outside the given tree") is satisfied
  by the very command that breaks it. Six later lens launches stated the hazard inline and
  none recurred, so the carrier is the gap rather than the wording — the same shape as
  `#469`. **Filed 2026-09-08 as
  [`#712`](https://github.com/topij/agentic-dev-kit/issues/712)**, together with the
  untracked-file entry below, on the operator's go-ahead.

- **Lenses end their turn on a progress update while a background `make test` runs.** Four
  occurrences on 2026-09-07 across three PRs, each needing a `SendMessage` resume to
  produce a terminal report, and one lens lost its run entirely by piping it through `tail`
  and stopping early. *Execute, don't only read* already says a progress update is not a
  report, and two of the four had that sentence quoted in their prompt. **M** — no
  mechanism identified beyond "the instruction is present and does not bind"; proposed
  direction is the same as `#469`'s, a carrier change rather than a wording one. Parked
  for accumulation; if it recurs, capture whether the lens had a foreground alternative.
  **Reconciled 2026-09-09 under #722:** the available foreground alternative was
  confirmed and the park condition discharged to the
  [#578 occurrence](https://github.com/topij/agentic-dev-kit/issues/578#issuecomment-5605922954).
  Triage reconciles this pointer rather than re-filing the entry.

- **A review lens left an untracked file in the cockpit's own repository root.**
  `bad2.sh` — a lens's reproduction of the bash heredoc bug recorded above — was created
  by a *relative* path, so it landed in `/Users/topi/Coding/agentic-dev-kit` rather than in
  the lens's scratch. It was never committed, and every branch tip was checked clear of it,
  but the cockpit stages with `git add -A`, so it was one commit away from shipping. *No
  writes in the tree you were given* already names this exact failure — "a *relative*
  extract path lands in the repo root, where it sits untracked until some later `git add
  -A` commits it" — so the wording is not the gap. **M**, and the second distinct isolation
  mechanism this session after the `cp -a` entry above: the lenses were handed their own
  worktrees and still reached the cockpit's tree, once through shared git admin state and
  once through a bare relative path. Two occurrences, one session, different routes, same
  contract item — the shape to watch is whether isolating a lens by *tree* is the wrong
  unit when the lens can name any path it likes. **Filed 2026-09-08 as
  [`#712`](https://github.com/topij/agentic-dev-kit/issues/712)**, together with the
  `cp -a` entry above, on the operator's go-ahead.

- **`panel_prompt.py` rendered a stale base, and only the lens contract caught it.** The
  `#711` round was assembled after `#709` merged, and its prompts named
  `ec750753eff1a645c64163b61a2b511e3adf71d4` as the base — one commit behind
  `origin/main`, then at `6f2cc2470c62ca4aa16793e0e20252341ba48b24`. Diffing against it
  attributed `#709`'s already-merged hook, tests and manifest to `#711`, which is a large,
  non-empty, wrong diff — the exact shape *Right revision* warns satisfies every other
  check. Both lenses independently detected it against the remote, re-derived the correct
  three-file diff, and said so in their reports before reviewing. **M** — the contract
  worked and the mechanism did not. Proposed fix: `panel_prompt.py` should re-resolve the
  base at render time rather than at an earlier assembly step, or state the timestamp of
  the resolution it used so a stale one is visible in the prompt. Worth filing: the
  cockpit had no signal, and a lens that skipped the check would have reviewed the wrong
  diff and reported it clean. **Filed 2026-09-08 as
  [`#713`](https://github.com/topij/agentic-dev-kit/issues/713)**, on the operator's
  go-ahead.

- **`#666`'s ordering is enforced by the engine, and the recovery costs a full round.**
  Round 2 of `#708`'s panel was fixed before its receipt was recorded; the retroactive
  `pr_watch.py --record-review --head <round-2 sha>` then refused with `PR head changed
  during review … review the new head before recording evidence`. That is the guard
  working. **L** — no fix proposed and none obviously needed: the cost lands on the party
  that skipped the step. Recorded so the next session knows the receipt is not recoverable
  after the fact and plans the round accordingly.

## 2026-09-06 — Backlog migrated to GitHub Issues (#693)

Swept in **LLM-only mode** because the configured draft and finalize engines are absent,
which is what selects it; every result here is **agent-executed**, not engine-verified.

**Graduated:** [#693](https://github.com/topij/agentic-dev-kit/issues/693), from the
2026-09-06 adopt-continuation entry, searched by its exact idempotency marker before
creation and re-read afterward for its approved title, body, project, labels, marker and
payload digest. The pre-create search returned nothing for this session's marker while
returning prior markers for a `triage-payload` control term, so the empty result was
meaningful rather than a search that never matches.

**Archived without filing:** the 2026-09-01 entry and its 2026-09-02 recurrence, on the
operator's explicit `archive` decision. The 2026-09-02 recurrence is recorded with its
mechanism as an occurrence comment on
[#393](https://github.com/topij/agentic-dev-kit/issues/393), which stays open. The
2026-09-01 entry is not separately on the tracker — that comment refers to it only as
the hypothesis the recurrence did not survive — so its verbatim copy in
`kit-friction-log-archive.md` is the only record of its own revision and run. The
2026-09-03 sweep kept both pending exactly this decision.

**Kept active below this marker:** the `claude -p --output-format json` and
`panel_prompt.py` entries (2026-08-27) and the eight-panel-rounds entry (2026-08-22),
parked for accumulation. **Still reserved:** the `#608` and `#255` dispositions, carried
here from the swept 2026-09-06 entry's own trailer.

**Candidate ids are not the 2026-09-03 run's.** This run's `TRI-04`, `TRI-05` and
`TRI-06` are that run's `TRI-03`, `TRI-04` and `TRI-05`, each pair confirmed by an
identical source-block digest.

**Approval.** The exact payloads were presented in the current Claude Code session; the
DM path was not exercised, which the interactive route permits. The operator replied on
2026-09-06 — `approve TRI-01, archive TRI-02 TRI-03, park TRI-04 TRI-05 TRI-06` —
superseding an earlier `approve all`. This block is the committed approval record
[#128](https://github.com/topij/agentic-dev-kit/issues/128) asks the interactive path to
carry, since `state/` and `reports/` are gitignored.

**Frozen inbox.** `shasum -a 256
state/triage/frozen-inbox_live_2026-09-06_triage-548121b9fa18444808d6b2482aac91d3.json` in
`/Users/topi/Coding/agentic-dev-kit` at `4989efd4cbc09c0a81f8d5e3259f0430ff69484b` on 2026-09-06
printed `5dfbd96911df6e92a7272a6b4977853ea548eb81c2b51de4df2566fc1084b297`. Finalization
re-read the active inbox and admitted only the byte-identical frozen blocks for
`TRI-01`, `TRI-02` and `TRI-03`.

## 2026-09-03 — Backlog migrated to GitHub Issues (#671–#672)

Swept in **LLM-only mode** because the configured draft and finalize engines are absent;
the results are **agent-executed**, not engine-verified. Graduated:
[#671](https://github.com/topij/agentic-dev-kit/issues/671) and
[#672](https://github.com/topij/agentic-dev-kit/issues/672). Each issue was searched by
its exact idempotency marker before creation and re-read afterward for its approved
title, body, project, labels, marker, and payload digest.

**Kept active below this marker:** `TRI-03`, `TRI-04`, and `TRI-05`, exactly as the
operator decided. The 2026-09-01 entry and its recurrence are already recorded on
[#393](https://github.com/topij/agentic-dev-kit/issues/393); they were excluded from the
proposal set and remain byte-identical below rather than being swept without an explicit
archive decision. Content added after the frozen draft also remains active verbatim.

**Approval.** The exact payloads were presented in the current Codex session. The
operator replied on 2026-09-03: `approve TRI-01 TRI-02` and `park TRI-03 TRI-04 TRI-05`.

**Frozen inbox.** `shasum -a 256
state/triage/frozen-inbox_live_2026-09-03_triage-1565b7bfdf11475f9a92f06002f463d4.json`
at `e78c215c9bd1bd3e007a7d3c9753b2013e5a8221` on 2026-09-03 printed
`03de6ef926e190a5800b939ee652c7c9607be58f3e95362ece4365ac3bc6ebef`. Finalization
re-read the active inbox and admitted only the byte-identical frozen blocks for
`TRI-01` and `TRI-02` to this sweep.

## 2026-08-29 — Backlog migrated to GitHub Issues (#641–#645)

Swept in **LLM-only mode**: both engines named by `triage.draft_engine` and
`triage.finalize_engine` are absent, which is what selects it, and vendoring them is
[#6](https://github.com/topij/agentic-dev-kit/issues/6). Every result here is **agent-executed**, not engine-verified.

**Every block present at draft time is accounted for.** Graduated: [#641](https://github.com/topij/agentic-dev-kit/issues/641),
[#642](https://github.com/topij/agentic-dev-kit/issues/642), [#643](https://github.com/topij/agentic-dev-kit/issues/643) (the cause behind [#570](https://github.com/topij/agentic-dev-kit/issues/570)'s symptom),
[#644](https://github.com/topij/agentic-dev-kit/issues/644), [#645](https://github.com/topij/agentic-dev-kit/issues/645). Archived without filing: the `#428`-guard entry dated
2026-08-27, whose own text records the occurrence on [#467](https://github.com/topij/agentic-dev-kit/issues/467). Each create was re-read
from the tracker after landing per `#138` — state, title, body **and labels** — against its
approved payload digest and its idempotency marker.

**Kept active below this marker, deliberately not swept:** the `claude -p --output-format
json` multi-value entry and the `panel_prompt.py` empty-render entry (both 2026-08-27, single
instances, no mechanism identified), and the eight-panel-rounds entry (2026-08-22, parked on
both park conditions). This is [#575](https://github.com/topij/agentic-dev-kit/issues/575)'s *skipped* versus *parked* distinction, and
why [#224](https://github.com/topij/agentic-dev-kit/issues/224) says position alone does not tell you what is un-graduated: each waits
for a recurrence an archived entry never reaches.

**Approval.** The numbered proposal list went to the operator **in-session, not by DM** (the
notification path degraded to the current session, which the interactive route permits); the
decision came back the same session on 2026-08-29: `approve TRI-01 TRI-02 TRI-03 TRI-04
TRI-05`, `archive TRI-07`, `park TRI-06 TRI-08 TRI-09`. This block is the committed approval
record [#128](https://github.com/topij/agentic-dev-kit/issues/128) asks the interactive path to carry, since `state/` and `reports/` are
gitignored.

**Frozen inbox:** sha256 `e6e8ca7ba2ca523b2372dce9dfa6e52af845ffec4f9ec1cf5ec332f21081ce92`, from
`shasum -a 256 docs/kit-friction-log.md` at `9c7e130` on 2026-08-29; re-read at finalize and
required to match before the rewrite, every swept block byte-identical to its frozen block.
Swept entries are verbatim in the archive under `Graduated 2026-08-29`.

## 2026-08-27

- **`claude -p --output-format json` printed more than one JSON value on stdout in
  three of five cockpit probe invocations at 2.1.247, and one value on a repeat of the
  same invocation.** The wrapper terminalizes that shape `failed` (a single result is
  what the digest binds), so the outcome was fail-closed each time; the record in
  `saved_plans/claude-writing-lane-live-validation_2026-08-27.md` carries the
  occurrences. **L** — no mechanism identified, and the cockpit could not make it
  recur on demand; parked for accumulation. If it recurs, keep the raw stdout bytes
  and the stderr beside them before re-running.

- **`panel_prompt.py` produced an empty prompt file and hung until the tool timeout,
  then rendered in about a second on an identical re-run.** In a shell `for` loop that
  created a detached lens worktree and immediately rendered the lens prompt into it
  (`git worktree add --detach … && uv run scripts/panel_prompt.py --lens … > prompt.md`),
  the first render wrote nothing and did not return within the tool's timeout; the
  same invocation re-run alone with a bounded subprocess timeout returned in about one
  second with a complete prompt. A full `make test` was running in the background at
  the time. **L** — no mechanism identified (contention on the shared `.git` from the
  concurrent suite and the fresh worktree is a guess, not an observation), single
  instance; parked for accumulation. If it recurs, capture `panel_prompt.py`'s stderr
  and the worktree lock state before re-running.

## 2026-08-22 — Backlog migrated to GitHub Issues (#566–#571)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Twelve
entries in, twelve accounted for:** six new issues
([#566](https://github.com/topij/agentic-dev-kit/issues/566)–[#571](https://github.com/topij/agentic-dev-kit/issues/571)),
five entries folded into occurrence comments on already-open issues carrying the same
mechanism — [#509](https://github.com/topij/agentic-dev-kit/issues/509),
[#514](https://github.com/topij/agentic-dev-kit/issues/514) (two entries in one
comment: the original delegate stall and its same-day recurrence with the fix applied
verbatim), [#511](https://github.com/topij/agentic-dev-kit/issues/511) and
[#246](https://github.com/topij/agentic-dev-kit/issues/246) (one entry split across
two, since its second half is a `gh`-cwd-resolution finding rather than a two-tree
one), and [#510](https://github.com/topij/agentic-dev-kit/issues/510) — and **one
entry deliberately kept in the active file**, below (the disposition question that
raises is [#575](https://github.com/topij/agentic-dev-kit/issues/575)). All six creates and all five
comments were re-read from the tracker after landing per `#138` — state, title, body and
**labels**. The first re-read checked everything but labels and so missed that the six
issues had been filed with none; a panel lens caught it against the previous sweep.
`gh api repos/topij/agentic-dev-kit/issues/{566..571}/timeline` on 2026-08-22 shows each
created with no label and labelled in one later batch, both before this marker's commit.

**One entry was kept rather than swept, which diverges from the engine's spec.**
`triage-friction-log.md` Step 5 sweeps every block present at draft time, *including
LLM-skipped ones*, so a vendored `finalize_triage.py` would have archived the
2026-08-22 entry. It is kept here on the operator's approval because its own text
parks it for **accumulation** — "if it recurs with a mechanism attached it is worth a
rule" — and an archived entry reaches no future triage pass, which is the one thing
that entry is waiting for. Skipped and parked are different dispositions and the spec
has one bucket for both; worth resolving before the engine lands, since the engine
will not reproduce this choice.

**Approval.** The numbered proposal list went to the operator **in-session, not by
DM**: the Slack MCP was unauthorized for this session and `scripts/` carries no notify
engine, so the workflow's load-bearing DM surface was unavailable. The two-session
draft→approve→finalize split exists because a *scheduled* run has no operator to ask;
one was present here, so the list was put directly in front of them and approval came
back in the same session at 2026-08-22 — "approve all" — the grammar's bulk approve.
Nothing was declined. This block is the committed approval record `#128` asks the
interactive path to carry, since `state/` and `reports/` are gitignored.

**Frozen inbox:** 14,451 bytes, sha256
`9d42521dfa8b287a49f60f33aca13ce9f185774a1562ad33c95161db2296b59b`, reproducing from
`git show 8efdc9d:docs/kit-friction-log.md | tail -n +28 | shasum -a 256`. Draft and
finalize ran in one session with no window between them, so no window-added entry
could exist; the digest was recomputed from the file being swept immediately before
the rewrite and matched.

Swept entries are verbatim in the archive under `Graduated 2026-08-22`.

## 2026-08-22

- **Across eight panel rounds on two docs-only PRs, every finding was in a claim *about* the
  work rather than in the work.** Severity **M**. `#548` ran six rounds and `#553` two; the
  code, the 500-line doc move and the new guards came back clean under mutation every time a
  lens tried them — content parity re-derived twice by reverse-substituting placeholders, both
  registration guards killed by real set-equality assertions, four live `kit_doctor` scenarios.
  What kept being wrong was the prose beside them: a checkpoint that claimed to be the same as
  `triage-friction-log`'s and was weaker, a `kit_doctor` state named `missing` that is
  `new-upstream`, a refresh forecast inverted against `upgrade.md:613`, a positional invariant
  that `finalize_triage.py`'s keep-window breaks, an up-route attributed to a pass with no
  recurrence step. **Parked rather than filed, deliberately, on both park conditions:** there is
  no named mechanism — "authors overstate" is a description, not a cause — and the point is
  accumulation. One session cannot tell whether this is a property of docs-heavy PRs, of this
  author, or of a panel that has more purchase on prose than on tested code. If it recurs with
  a mechanism attached it is worth a rule; the shape to watch is whether a claim verified
  against a *command* ever failed, versus one verified against nothing.
  **Park condition discharged 2026-09-09 — graduated to `AGENTS.md`'s *Prose that goes
  false*, not to the tracker.** The recurrence arrived on 2026-09-07–08 with mechanisms
  attached, and the operator approved graduation in session. What graduated is narrower
  than this entry's phrasing: the two PR #711 instances, which are an author's edit
  falsifying a neighbouring sentence and an outside change falsifying an instruction that
  had been correctly dated. This entry's own broad reading — *every finding was in a claim
  about the work rather than in the work* — was **not** written as a rule, because `#709`'s
  findings in that same session were real defects in a mechanism. `#120` is the
  enforcement follow-up. Left in place rather than swept, per `#575` — and the
  2026-08-29 marker's *"each waits for a recurrence an archived entry never reaches"*
  is left as written, since dated sections record what was decided then; this note is
  the appended correction `#696` proposes.
