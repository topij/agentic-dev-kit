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

Last updated: 2026-09-03 — the live-validation verifier is repo-only, the friction
inbox was triaged, and the adopter pilot's Codex write pass is next.

## Latest session — 2026-09-03 (`#662` and friction triage, in a Codex session)

**Theme —** The verifier received its repo-only manifest role, the approved friction
entries graduated, and Phase 5 passed to its initial adopter write rehearsal.

- **Runtime —** Codex desktop. This was the parity-sensitive implementation session
  after the preceding Claude Code sessions. It applied the shared workflow definitions
  through implementation and review without adding a runtime-specific workflow change.

- **PR `#670` delivered `#662`'s repo-only route.** It assigned the verifier, its test,
  and its evidence page a manifest role that keeps their hashes in the kit checkout's
  self-check but excludes them from adopter inspection, install baselines, and upgrade
  offers. The stale saved-plan link was removed in the same PR.

- **The approved friction entries graduated through PR `#673`.** `TRI-01` and
  `TRI-02` became `#671` and `#672`; `TRI-03`, `TRI-04`, and `TRI-05` remain parked.
  The entries already accounted for by `#393` stayed active. The triage run used the
  LLM-only, agent-executed route and retained its completed merge receipt.

- **The parked inbox still needs a later disposition pass.**
  `uv run scripts/check_doc_budget.py` at
  `e55ae691d948b525ffba0919acd6f960c16b98f2` on 2026-09-03 prescribed
  `triage-friction-log`; a future run must preserve the parked decisions unless the
  operator supplies fresh exact dispositions.

- **Runtime choice for the initial write pass is deliberate.** The pilot's read-only
  pass ran in Claude Code; its write pass should run through Codex's `$upgrade` binding
  so the Phase 5 claim is tested at the existing Codex adopter. Writes to cs-toolkit
  still require that repository operator's explicit approval, and its pull request
  keeps separate merge authority.

▶ Next: `$session-start` — then, with explicit cs-toolkit write approval, run the
initial adopter pilot write pass in Codex. Bind `$REPO` to cs-toolkit and `$KIT` to a
fresh clone of the kit's configured protected branch at `/tmp/agentic-dev-kit`, the path
used by Upgrade Step 5. Record `$REPO`'s canonical origin URL and require it to match the
approved cs-toolkit remote; assert `pwd` is in `$REPO` immediately before every write.
Invoke `$upgrade` in `$REPO` while following `$KIT`'s workflow; it must leave the
repo-owned lane forks untouched. Separately run reconciliation based on the upgrade
branch; preserve runtime-neutral local policy and open a PR when that stage has a diff.
Record the kit source SHA plus every created PR identity, base name, and head.
For a no-change stage, record its exact invocation, successful no-change output, input
and output SHA, tree equality, and clean status; its input must equal the preceding
stage's output. Do not manufacture an empty PR. Do not claim the Phase 5 exit: `#243`,
`#631`, `#608`, and `#255` remain. After those land, the final replay must use the
then-current kit source, confirm each created PR's base-name and ancestry chain, record
any no-change stage, and verify the final adopter head.
At the exit decision, capture one authoritative tuple containing the kit source and
configured protected head, the adopter repository's canonical origin URL, adopter
protected head, exact resulting adopter head, and every created adopter PR's identity,
base name and head. Require the origin URL to match the approved cs-toolkit remote and the
kit source to equal the configured protected head in that tuple. Include each no-change
stage's invocation, output, input/output equality, tree-equality check, clean status,
and preceding-stage linkage. Verify every ancestry edge and the adopter condition
defined in the maintained parity plan against those immutable SHAs, then capture the
full tuple again and require it to be byte-identical.
A mismatch requires replay. Publish both snapshots and the stamped verification result
before the kit wrap-up PR merges; later ref movement is a separate event and does not
rewrite the observation. The wrap-up records that event without treating its own commit
as the replay source. Do not merge any created adopter PR without separate authority.

______________________________________________________________________

## Session — 2026-09-03 (two parallel lanes, in a Claude Code session)

**Theme —** The pilot's findings became changes. Two isolated lanes fixed the instrument
defects the read-only pass found, and the review that landed them cost more rounds than
the changes did — which is now its own tracker item.

- **Runtime —** Claude Code, model `claude-opus-5[1m]` as this session's own system
  prompt names it; effort not read. The session ran unattended from the operator's
  "run the rest autonomously" onward.

- **PR `#668` (squash `015908a`) fixed `#661` and its second occurrence.** `inspect`
  trusts a `required_by` edge only where the installed dependent is byte-identical to
  the comparison manifest, so a dependency the kit gained after an adopter's baseline
  stops reading as a broken install. The lens-definition remedy now branches on whether
  `panel_prompt.py` is installed rather than prescribing an engine the adopter lacks.
  The narrowing buys no silence: a dependent failing the byte check still reports
  `differs`/`stale`/`locally-edited` and still exits `1`.

- **PR `#667` (squash `2aa1912`) delivered `#604` and `#603`.** `--record-review
  --disposition` posts one comment at the recorded head under an engine-fixed heading,
  and every poll's report grows `evidence_findings[]` for a receipt with no matching
  comment and for a body stamp whose sha is not the head. Neither gates.

- **The lane's own panel caught a merge-gate bypass, and the cockpit nearly lost it.**
  `#667`'s first draft kept the engine's disposition out of `new_actionable` by matching
  the public marker text — an unauthenticated string in front of a predicate
  `dev_session.sh merge` reads, which GitHub's quote-reply reproduces by accident. The
  lane fixed it with a `seen` key written at post time. Then a session rate limit killed
  both lanes mid-task, and that fix was **committed but never pushed**: the forge held
  the vulnerable version while the lane's own last words said it was about to re-run its
  mutation battery. Reading the worktrees rather than the agents' final messages is what
  recovered it.

- **Review cost the session more than the code did.** `#665` took five panel rounds and
  `#667` three, each round triggered by fixing the previous round's finding, which moved
  the head and invalidated the evidence. `#666` was filed for that shape, including the
  part that argues against simply capping rounds: `#665`'s fourth round found a false
  claim in the pilot record that three earlier rounds had passed over.

- **`#662` was started and deliberately abandoned.** Its two routes differ in
  consequence — removing the three paths from `KIT_OWNED` drops them out of the drift
  check the issue wants kept, while the repo-only role it prefers needs `inspect` to
  distinguish its caller, since `test_kit_repo_self_check_is_clean` calls the same
  function an adopter does. That is a design decision in the instrument that gates every
  adopter's upgrade, so it was left for the operator with the analysis done rather than
  invented overnight. The branch was deleted; nothing is half-built.

- **Filed on the operator's approval of each exact payload:** occurrence comments on
  `#661`, `#393`, `#643`, `#510` and `#571`, and `#666` opened for the review-round
  loop. Each was read back from the tracker after landing. A later `#393` comment
  recorded a review lens independently reproducing that flake in its own clone.

- **Verified:** CI run `33700822303` at `912242eb1f96b85c6ebd3e88ff23323e9dff9958` on
  2026-09-03 printed `2432 passed, 3 skipped` with nothing failing, and CI was green at
  every merged head. Local `make test` on this machine reports one failure in
  `test_pr_followup_hook.py` in every run — the `#393` flake, which passes in isolation
  and which a lens reproduced and then failed to reproduce at the same sha. One local
  run was killed by the harness at roughly half the suite and is reported as incomplete,
  not green.

▶ Next: `session-start` — then `#662`'s route is the operator's call (repo-only role
versus dropping the three paths), and the adopter pilot's write pass still needs the
cs-toolkit operator's approval. The friction log is over budget and its graduation
still needs `triage-friction-log` with exact payload approval.

______________________________________________________________________

## Session — 2026-09-02 (cs-toolkit adopter pilot, read-only pass, in a Claude Code session)

**Theme —** Phase 5's exit test, first half. `/upgrade` Steps 0 and 1 ran against the
cs-toolkit adopter from a pinned kit clone. Nothing was written to the adopter. The
verification run then reproduced a parked friction entry under conditions that
contradict its parked hypothesis.

- **Runtime —** Claude Code, model `claude-opus-5[1m]` as this session's own system
  prompt names it; effort not read.

- **The pilot's findings live in the record, not here.**
  [`cs-toolkit-adopter-pilot-readonly_2026-09-02.md`](../saved_plans/cs-toolkit-adopter-pilot-readonly_2026-09-02.md)
  carries every reading with its command, the two tree bindings, and the three
  revisions they were taken against. `#661` is confirmed with its line
  (`scripts/kit_doctor.py:2652` filters `required_by` on the dependent's presence
  rather than on the installed version's requirement), and the same root cause has a
  second occurrence: `kit_doctor`'s lens-definition remedy prescribes
  `scripts/devkit/panel_prompt.py`, which `find` locates nowhere in the adopter.

- **What the pilot found that the sprint review did not predict:** `/upgrade` Step 1
  sends you to the adopter's installed engine first, which reports `intact` and names
  no new file, while the kit's engine reports `NOT intact` about the same tree — and
  Step 1's documented remedy for that under-reporting is a write, so a read-only pass
  cannot reach the complete view by the route the step names. `#607` is confirmed and
  invisible to every instrument: the adopter's lane engines are forks outside
  `paths.engines` and absent from its manifest, so `#598`'s BREAKING exit-`64` contract
  drifted unreported. And the adopter has already invented the mechanism the kit lacks
  — a repo-local runtime-neutral appendix, applied to `wrap-up` alone — while
  `session-start`'s Claude appendix, including the `origin/main` rule the appendix says
  cost that repo a duplicate ticket on 2026-08-10, reaches no Codex session.

- **A parked friction entry recurred, and its hypothesis did not survive.** The
  2026-09-01 inbox entry parked
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`
  on a concurrency correlation. It recurred here twice on a quiet tree with nothing
  running alongside, and passed standalone both times. The measured precondition
  (`json.loads` on the test's own input, in the suite's interpreter) raised
  `RecursionError: Stack overflow (used 8144 kB)`, so the assertion that fails is
  `out == ""` and not the exit code — the parse succeeded inside the suite where it
  raises in isolation. `test_init_sh.py:5100` already names this as `#393`'s shape and
  guards its own precondition by measuring it; the failing sibling does not.

- **`#510` fired on the session that was verifying.** The first run was
  `make test 2>&1 | tail -25`, so the harness reported exit `0` over an output ending
  `make: *** [test] Error 1`, and the `tail` discarded the traceback the friction
  entry's own recurrence instruction asks to keep. The second run retained full output
  and captured `make`'s status directly.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `679b197efc24e31a66e94f6d52b6b3e5f2a47855` on 2026-09-02 printed
  `1 failed, 2403 passed, 1 skipped, 3 warnings in 458.08s (0:07:38)` with `make`
  exiting `2`. **That stamp names the commit it ran at, not this PR's head.**
  What it does not cover is prose — this handoff file and the friction entry —
  over which `make test` carries no gate, so the run's scope is stated rather
  than extended. Deliberately no count of the commits in between: this sentence
  enumerated them once, later commits falsified the enumeration, and a review
  lens caught it — *Numbers in prose*'s own failure, met inside the paragraph
  policing stamps. The failure is the pre-existing one above: that commit's
  footprint is one `saved_plans/` file, that path is absent from
  `kit-manifest.json`, and no test reads it. It is also platform-dependent,
  not merely intermittent: the GitHub Actions `toolkit` job in run
  `33611571274`, at
  `53a40386e772e9dc0b7ad077bbff40369cfbc8d5` on 2026-09-02, printed
  `2402 passed, 3 skipped` with nothing failing, and the test that fails locally
  can be skipped by nothing — `grep -n 'pytest.skip\|skipif\|@pytest.mark.skip'`
  over `scripts/tests/test_pr_followup_hook.py` returns no rows — so it ran there
  and passed. Nothing was filed to the tracker.

▶ Next: `session-start` — then bring the pilot's write pass to the adopter operator
for approval, and decide whether the recurrence above graduates `#393` or opens its own
issue.

______________________________________________________________________

## Session — 2026-09-02 (parity sprint review, in a Claude Code session)

**Theme —** A review-only session: the Codex parity sprint was read against the tree, the
tracker, the merged pull requests and the cs-toolkit checkout, and the plan was
re-sequenced so the adopter pilot is the next slice rather than the last.

- **Runtime —** Claude Code, model `claude-fable-5-1` as the session's own system prompt
  names it; effort not read.

- **The review lives in the plan, not here.**
  [`codex-parity-plan_2026-08-23.md`](../saved_plans/codex-parity-plan_2026-08-23.md)
  gained a *Sprint review — 2026-09-02* section carrying the stamped readings, and its
  *Sprint status*, Phase 5 and Phase 6 lists and next starter were rewritten from it.
  No code changed; nothing was committed to `main`.

- **What the review found, each with its command in the plan:** the live-validation
  verifier and its test ship to adopters as manifest engine and test while nothing they
  verify ships; cs-toolkit is pinned at the 2026-08-22 kit and `kit_doctor` misreports it
  as broken because `required_by` is filtered on the dependent's presence rather than
  its installed version; review evidence for PR `#659` is recoverable only from
  gitignored state, the `#603` / `#604` shape recurring on the sprint's own exit
  evidence; pull-request data is fetched by hand in `session-start.md` and by engine in
  `pr_watch.py`; the same status facts are restated across the plan, the handoff and
  the parity matrix, with the matrix's headless-lane row a single table cell.

- **Re-sequencing decided in the plan:** the cs-toolkit adopter pilot moves from the end
  of Phase 6 to Phase 5's exit test, read-only pass first; withdrawing the verifier from
  the shipped manifest and putting review evidence on the pull request join Phase 5;
  `#631`, `#608` and `#255` are taken as declarations rather than mechanisms; the
  proportional opening pass (`#585`), suite marking and the learnings-memo distillation
  lead Phase 6.

- **Filed on the operator's approval of each exact payload, in this session:** `#661`
  (`kit_doctor`'s false "broken, not sized down" verdict), `#662` (the verifier ships
  with nothing to verify), `#663` (pull-request data fetched by hand and by engine), and
  occurrence comments on `#603`, `#604`, `#585` and `#243`. Each create and comment was
  read back from the tracker after landing — state, title, labels and body — against
  its approved payload. Nothing was parked; the friction inbox is unchanged and its
  graduation is still `triage-friction-log`'s sweep.

- **Verified:** `make test` was not run; the change is one `saved_plans/` document and
  this handoff. The plan's tables were checked for cell count and escaped pipes and the
  whole file for a closing keyword beside an issue number, by a script in the session
  scratchpad, in `/Users/topi/Coding/agentic-dev-kit` at
  `89dbb3e67497586254e913dc3f5fdf7f648746bd` on 2026-09-02.
  `uv run scripts/archive_plan_sessions.py --target-lines 400`, run in the same
  directory on the same date over that revision plus this session's uncommitted edits,
  moved the 2026-08-29 whole-tool Bash allow grants block into
  `kit-handoff-history.md`; `check_doc_budget.py` prints the live figures.

▶ Next: `session-start` — then the plan's next starter: the cs-toolkit adopter pilot,
read-only pass first, with `$REPO` and `$KIT` bound before anything else.

______________________________________________________________________

## Session — 2026-09-02 (retained Codex parallel-batch evidence, in a Codex session)

**Theme —** The Codex-only Phase 4 exit shipped as retained evidence: disjoint lanes,
exact-head reviews and operator-held merge authority can be recomputed from promoted bytes.

- **Runtime —** Codex desktop, assigned model `gpt-5.6-sol`, main reasoning effort `high`.

- **PR `#659` retained the parallel batch without merging its fixture work.** The
  bundle binds each lane's worktree and state root, Git head, launcher receipt,
  correctness and adversarial executions, forge readback, reconciliation refusal and
  complete claim-to-artifact map. Fixture PR `#1` and `#2` remain open in the private
  synthetic repository; the operator merge boundary is evidence, not exercised permission.

- **The promotion contract is independently recomputable.** The public verifier derives
  the retained source closure and semantic claims from Git-bound bytes, and the
  promotion receipt binds the resulting manifest. Review repairs made numeric values,
  formatted expressions and format specifications visible to the credential scanner,
  while preserving named runtime helpers and direct `Authorization` carriers. The
  review-lens regression guard also binds each retained prompt, worktree and launch argv
  to its declared lens.

- **The review stopped at the demonstrated boundary.** Exact-head adversarial and
  correctness rechecks reproduced the hostile cases and compatibility controls. The
  scanner repairs stayed at the demonstrated expression shapes instead of adding a
  general dataflow mechanism; the retained batch uses PR `#659`'s explicit plural
  reviewed-head evidence shape. PR `#659` carries the resulting `fallback:panel`
  receipt at `d0eac77185d808ef822ba7fefe3247de902927da`.

- **Verified:** `make test` in
  `/private/tmp/adk-codex-parallel-20260901.xlAufG/root-final-test-d0eac77` at
  `d0eac77185d808ef822ba7fefe3247de902927da` on 2026-09-02 printed
  `2405 passed in 367.84s (0:06:07)`; the merged squash is `4e63fd8`.

- **The session did not change tracker or friction state.** `#621`, `#631` and `#255`
  retain their live disposition questions; the overdue friction-log graduation still
  requires `triage-friction-log` and exact tracker-payload approval.

▶ Next: `session-start` — in a Claude Code session take `#243`'s field exercise of
`adopt`, `parallel`, `triage-friction-log` and `post-merge-systemize`; bind `$REPO` and
`$KIT` before `adopt` writes, and obtain the workflow-specific approvals before any
tracker or external write.

______________________________________________________________________

## Session — 2026-09-01 (runtime_mappings status declaration, in a Claude Code session)

**Theme —** `#255`'s disposition was settled against the tree rather than against the
plan's summary of it, and the one measured residue shipped. The session then found its
own disposition had been drawn too wide.

- **Runtime —** Claude Code 2.1.252, assigned model `claude-opus-5`, effort `xhigh`,
  read from this session's own transcript rather than from the prompt or argv.

- **PR `#657` (squash `b5bc17a`) closed the gap between `#255`'s proposal and its
  delivery.** `lens_compute` carried the per-runtime mechanical/advisory declaration on
  both install surfaces; `models.runtime_mappings` carried it on the reference config
  only, so a migrating adopter's config surface stated the values without their status.
  `init.sh` now emits it, and `_runtime_mappings_block` — written for that pin and
  wired to no assertion — became `_runtime_mappings_comment` behind a pin holding both
  surfaces. The emitted block moved to single quotes because the added comment text
  carries backticks.

- **`Makefile`'s mutation guidance was inverted for the files that PR touched.** It
  named `scripts/tests/` and `init.sh` as paths a mutation never trips the drift check
  on; both are in `kit-manifest.json`, so a mutation to either read as killed under
  plain `make test` with nothing behavioural catching it. Corrected to send a
  contributor to the manifest rather than to the comment's own list.

- **`#255` stays open, and the disposition comment that implied otherwise was too
  wide.** Both halves of its *Proposed* section are delivered for the two keys the
  issue's own comments name, but the Proposed states a general rule over every
  compute- or capability-selecting key. Enumerating those found two carrying no
  per-runtime status: `review.fallback_commands` (consumed by `pr_followup_hook.py`,
  agent-executed and so advisory — the issue's own "real consumer, zero mechanism"
  shape) and `runtime.launchers` (consumed by `dev_session.sh`). A correction comment
  is owed on the issue and was not posted this session.

- **The panel's convergence was not corroboration.** Both lenses filed no finding
  against the diff and both drew the same overstated conclusion from the same probe.
  Recorded with the enumeration lesson in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

- **The sprint boundary held.** This session did not start `#631` or the retained Codex
  parallel-batch Phase 4 run, and `saved_plans/claude-side-assessment_2026-08-26.md`
  stayed operator-owned and unstaged.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `da142620a02d16d31e3231249d627b8fd194daa9` on 2026-09-01 printed
  `2374 passed in 514.92s (0:08:34)` on a quiet tree; the merged squash is `b5bc17a`.

▶ Next: `session-start` — then take `#243`'s Claude-side field exercise of `adopt`,
`parallel`, `triage-friction-log` and `post-merge-systemize` as the opening slice, and
settle `#255`'s two remaining undeclared keys.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
