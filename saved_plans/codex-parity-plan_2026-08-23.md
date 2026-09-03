# Codex parity plan — 2026-08-23

## Goal

Make Codex a first-class agentic-dev-kit runtime with the same workflow outcomes,
safety guarantees, review evidence, lane isolation, and upgrade behavior as Claude
Code. Runtime-specific files may differ in shape; their observable contract should
not.

## Sprint review — 2026-09-02

Read in a Claude Code session (model `claude-fable-5-1`) at
`89dbb3e67497586254e913dc3f5fdf7f648746bd` on 2026-09-02 against the tree, the
tracker, the merged pull requests, the cs-toolkit checkout at
`/Users/topi/Coding/in-parallel/cs-toolkit` (`$CS` below), and the since-deleted
`claude-side-assessment_2026-08-26.md`. No
code changed. Every figure below is a reading, names its command, and was taken at that
revision on that date unless the row says otherwise. The re-sequencing it recommends is
applied to *Sprint status* and *Delivery plan* below; the readings themselves are
history from the moment they were written and are not to be refreshed in place. Their
ordering and starter prose is likewise historical; only the maintained *Sprint status*
and *Delivery plan* sections are executable after the later updates recorded there.

### Verdict

Phases 1 through 4 delivered what the goal asked for, in the shape it asked for: one
shared definition per workflow, thin bindings on both runtimes, policy in
`config/dev-model.yaml`, tests derived from the parity declaration, and a Phase 4 exit a
reader can recompute from retained bytes. The method is the sprint's real asset: a claim
about what a runtime does is probed against the pinned client before it is written, and
the probes overturned the "no per-agent effort" sentence, the `Bash(:*)` reading and the
`.claude/` write assumption. What has gone wrong is proportion. The two closing slices
spent their bytes on evidence-retention machinery rather than on parity; that machinery
now ships to adopters as a kit engine although nothing in an adopter's tree is verifiable
by it; the review process that made the work trustworthy buys a full dual-lens panel for
every wrap-up record; and the one adopter the sprint exists for has received none of it.
Phases 5 and 6 are re-sequenced below so that the adopter pilot is the next slice rather
than the last.

### What is strong

- **The shape held.** Every workflow in the front matter of
  [`runtime-parity.md`](../docs/agentic-dev-kit/runtime-parity.md) is `aligned` or
  `companion`; `scripts/tests/test_kit_doctor.py`'s renderer test holds the shipped
  adapters byte-equal to what `scripts/lib/runtime_adapters.py` renders; and
  `session-start`, `wrap-up`, `parallel`, `triage-friction-log` and
  `post-merge-systemize` each carry an independently written second copy of their
  adapter body under appended-contrary-instruction mutations in
  `scripts/tests/test_portability.py`.
- **Live measurement before prose.** Each slice since `#609` produced its record from
  the runtime under test, and the record overturned a written claim more than once: the
  frontmatter `effort` carrier (`#623`), `Bash(:*)` granting nothing (`#639`), the
  `.claude/` refusal being neither a glob nor a dot-directory effect (`#626`), the
  accept-form probe that established nothing (`#632`). The lesson list in
  [`review-process-learnings_2026-08-24.md`](review-process-learnings_2026-08-24.md) is
  specific enough to be a test plan.
- **Deferrals became tracker items.** The 2026-08-26 memo found a tracker that had
  received nothing from the sprint. Since then every deferral named in a merged slice
  has an issue (`#601`–`#608`, `#615`–`#618`, `#627`–`#631`, `#641`–`#647`), and the
  2026-09-01 reconciliation retired `#365`, `#169`, `#466`, `#601`, `#605` and `#606`
  against merged evidence rather than against the plan.
- **Parity was dogfooded, not asserted.** The live handoff names the runtime each
  session ran in: Codex sessions shipped `#649`, `#651`, `#653`, `#655` and `#659`;
  Claude sessions shipped `#639`, `#646` and `#657`; all through the same shared
  workflows and the same `pr-watch` gate.
- **The Phase 4 exit is the right kind of evidence.** The parallel-batch promotion is
  bound to retained bytes and a fixture revision, and the bundle-walking test recomputes
  it on every `make test` in this repository.

### What is burning

**1. Evidence weight has overtaken parity work.**

| reading | command | value |
|---|---|---|
| tracked files under `saved_plans/`; tracked files in the repository | `git ls-files saved_plans \| wc -l`; `git ls-files \| wc -l` | 136; 262 |
| sprint pull requests; those that wrote to `saved_plans/` | `git log --oneline 9c49696..HEAD \| wc -l`; `git log --format=%h 9c49696..HEAD -- saved_plans \| wc -l` | 48; 36 |
| verifier engine; its test | `wc -l scripts/verify_live_validation_bundle.py scripts/tests/test_live_validation_bundle.py` | 2154; 4238 |
| additions in the two evidence slices | `gh pr view 651 --json additions`; `gh pr view 659 --json additions` | 11406; 15388 |

`scripts/verify_live_validation_bundle.py` and `scripts/tests/test_live_validation_bundle.py`
are `engine` and `test` in `kit-manifest.json`, so `/upgrade` offers them to every
adopter, while no `saved_plans/**` path and no `scripts/tests/fixtures/**` path is in the
manifest. An adopter receives the verifier and its bundle-walking tests
(`kit_repo_only`-marked, so they skip) and nothing for either to verify. The verifier is
sprint tooling for this repository; shipping it is a manifest decision that was never
made.

**2. The adopter has received nothing.**

| reading | command | value |
|---|---|---|
| cs-toolkit's recorded kit pin | `kit_commit` in `$CS/kit-manifest.json`; `git log -1 --date=short df32eb2` | `df32eb25a765…`, dated 2026-08-22 |
| kit commits on `main` since that pin | `git log --oneline df32eb2..HEAD \| wc -l` | 53 |
| kit_doctor against the adopter | `uv run scripts/kit_doctor.py --root $CS --manifest kit-manifest.json` | `6 unchanged, 15 differ, 1 missing`; `NOT intact … this install is broken, not sized down` |
| adapter report against the adopter | `uv run scripts/kit_doctor.py --root $CS --adapter-report --adapter-source .` | claude: `adopt` kit-current; `parallel`, `post-merge-systemize`, `pr-watch`, `session-start`, `triage-friction-log`, `upgrade`, `wrap-up` adopter-owned. codex: `adopt`, `parallel`, `pr-watch`, `session-start`, `upgrade`, `wrap-up` adopter-owned; `post-merge-systemize`, `triage-friction-log` missing |

The `broken` verdict is a false reading. The missing file is
`scripts/devkit/lib/runtime_adapters.py`, which the kit manifest declares as required by
`kit_doctor.py`, but `grep -c runtime_adapters $CS/scripts/devkit/kit_doctor.py` prints
`0`: the dependency check reads the kit's *current* dependency graph against the
adopter's *older* engine. That is an occurrence of `#236`'s shape (the upgrade instrument
misjudging the executed surface) and the first thing the pilot will meet. `#607` is
unscheduled, and Phase 6 still listed the pilot last.

**3. Verification and review cost.**

| reading | command | value |
|---|---|---|
| sprint commits that are handoff updates | `git log --format=%s 9c49696..HEAD \| grep -c handoff` | 20 of the 48 above |
| suite at sprint start, as the handoff history stamped it | `make test` at `d03bcf3` on 2026-08-23 | `1367 passed in 166.51s` |
| suite at sprint end, as the live handoff stamped it | `make test` at `d0eac77` on 2026-09-02 | `2405 passed in 367.84s` |
| learnings memo | `wc -l saved_plans/review-process-learnings_2026-08-24.md`; `grep -c '^## ' …` | 727; 18 |

The doctrine gives each of those handoff pull requests the full dual-lens opening panel
(`fallback-review-panel.md`: an initial review never takes a delta pass), and `#585`'s
2026-09-01 occurrence records `#658` doing exactly that beside the engine change it
followed. Every verification stamp is a serial quiet-tree run (`#623`'s rule), and two
lenses running the suite concurrently now produce a failure the cockpit does not (inbox
entry of 2026-09-01; `#644`). The learnings memo appends a section per pull request and
has promoted nothing to `docs/agentic-dev-kit/` since it was opened on 2026-08-24, which
its own header names as the condition for keeping it.

**4. Evidence hygiene regressed on the capstone.** `gh pr view 659 --json
body,headRefOid,reviews,comments` on 2026-09-02: the body stamps `make test` at
`0aab6d1`, the head is `d0eac77`, `reviews` is empty, and the only comment is the review
bot's auto-summary. The `fallback:panel` receipt for `d0eac77` exists in
`state/pr-watch/659.json`, which is gitignored, with `head`, `lenses`, `source` and
`recorded_at` and no findings. That is `#603` and `#604`, filed on 2026-08-26 from the
same shape on `#596` and `#599`, recurring on the sprint's own exit evidence. The
handoff's "PR `#659` carries the resulting receipt" is true of the local state directory
and not of the pull request.

**5. Both budgets are at the wall.** `uv run scripts/check_doc_budget.py` printed
`docs/kit-handoff.md 399/400 lines` and `docs/kit-friction-log.md is 165 lines (budget
~150)`. The next wrap-up archives before it can write, and the inbox graduation needs a
`triage-friction-log` run with exact tracker-payload approval.

**6. Status prose is written on every surface.** The `#659` fact is in this plan twice
(*Sprint status* item 7 and the Phase 4 exit paragraph), in the matrix's headless row,
and in the handoff's `Last updated` line, its 2026-09-02 theme line and that block's
first bullet. The `.claude/` refusal is on the matrix, this plan, `parallel-headless.md`
and `CHANGELOG.md`. `wc -c` on the matrix's headless-lane row prints `5724`: one table
cell carrying the whole evidence narrative. This plan's own *Phase 3 integration
inventory* restates the capability tables the three workflow docs carry, and its
preserved "next sprint starter" named `feat/codex-environment-capable-launcher`, merged
as `#609` on 2026-08-26.

### Duplication and DRY

**Forge reads.** There is no forge client under `scripts/lib/`. Wrappers with differing
failure contracts exist instead: `scripts/pr_watch.py:609` (`_gh`, raises on non-zero),
`scripts/dev_session.sh:166` (`_gh`, swallows stderr and status),
`scripts/reconcile_sessions.sh:211` (`_gh`, preserves status). Where the same pull
request is fetched twice:

- `docs/agentic-dev-kit/workflows/session-start.md:117` and `:136-138` send the agent to
  `gh pr list` and then, per open pull request, to `gh api` for `/reviews`,
  `/issues/<n>/comments` and `/pulls/<n>/comments`; `:240` then sends the red ones to
  `pr-watch`, whose `fetch_pr_view` (`scripts/pr_watch.py:1960`, `:1969`) reads the same
  surfaces again. The doc's reason (evidence must be independent of seen state) is
  right; the fetch is still done twice, once by hand and once by engine.
- `scripts/dev_session.sh:765` and `:780` spend `gh repo view` and `gh pr list`
  (including `headRefOid`) before every `pr-watch` and `merge`, then hand off to
  `pr_watch.py`, which re-reads `headRefOid` (`:1622`); `_collect_board` at `:529` reads
  `number,state,isDraft,reviewDecision,statusCheckRollup` per lane per frame, each also
  in `fetch_pr_view`'s list, with no plumbing between them. `cmd_merge` at `:900`
  consumes `pr_watch`'s `mergeable` rather than re-deriving it, so the discipline exists
  at the decision layer and not at the fetch layer.
- On the REST backend, `rest_pr_view` (`:1417`, `:1421`) and `fetch_check_details`
  (`:1778`, `:1782`) each fetch `pulls/{n}`, `commits/{sha}/check-runs` and
  `commits/{sha}/status` in one poll, and each re-runs `git remote get-url origin`. The
  `gh` branch avoids this by threading `head_sha=`; the REST branch declines that at
  `:1717-1721`.
- `scripts/hooks/pr_followup_hook.py:346` tells the agent to run
  `gh pr view <n> --json isDraft`, the read `_read_is_draft` (`scripts/pr_watch.py:1992`)
  performs inside the `--assert-draft` / `--assert-ready` the same message prescribes.

Not duplication, and not to be collapsed: inside one `gh`-backend poll, the
`statusCheckRollup` read beside `gh pr checks` and the second `headRefOid` read are
recorded correctness decisions (the comments at `scripts/pr_watch.py:1723-1735` and
`:1905-1934` name the incidents). `state/pr-watch/<n>.json` holds watch bookkeeping and
the receipt, never the report, so nothing downstream *could* read a persisted view
instead of fetching.

**Adapters.** Thin, with `post-merge-systemize`, `pr-watch` and `upgrade` carrying an
extra paragraph that restates the shared layer: the tier sentence at
`.claude/commands/post-merge-systemize.md:9-11` restates
`workflows/post-merge-systemize.md:110-113`; each runtime's `pr-watch` binding restates
its half of `fallback-review-panel.md:175-182`; `upgrade`'s is deliberate
(`workflows/upgrade.md:193-195` says not to delete it). The renderer is one template
frame over one hand-written context string per workflow per runtime in
`scripts/lib/runtime_adapters.py` (`_CURRENT_CONTEXTS`, `:41-122`) plus a frozen legacy
generation, so the frame is DRY and the bodies are Python string literals a Markdown
author will not find. `adopt`, `upgrade` and `pr-watch` have no appended-contrary-
instruction test of their own; they are pinned only through the renderer, so a
coordinated edit to adapter and renderer passes. Each skill's `description` is
duplicated between the two frontmatters and hand-written again in
`.agents/skills/<n>/agents/openai.yaml`. `fallback-review-panel.md:135` still cites
"`SKILL.md` step 5", which has not existed since the thinning. The lens definitions under
`.claude/agents/` are generated by `panel_prompt.py --agent-definition`, pinned by
`test_panel_prompt.py:1075`, and copied again as heredocs at `init.sh:1227-1272` pinned
by `test_init_sh.py:3189`.

**Status prose.** Item 6 above. The remedy is ownership, not deletion: the matrix owns
the capability claim and its evidence links, the handoff owns the session narrative,
this plan owns exits and order, and a fact appears once with pointers.

### Opportunities

This is the 2026-09-02 recommendation as written. Its order is superseded by the
maintained *Sprint status* and *Delivery plan* sections below.

1. **Run the adopter pilot now, as Phase 5's exit test.** The Phase 5 exit ("an existing
   Codex adopter can upgrade without retaining stale runtime behaviour or losing local
   policy") can only be established by an upgrade run, and cs-toolkit is that adopter:
   dual-runtime, and pinned at the 2026-08-22 revision in the table above. A read-only
   pass first (`kit_doctor` in both modes, `/upgrade` Steps 0–3 with `$REPO` and `$KIT`
   bound), a stamped record of what the instrument gets wrong (the `broken` verdict),
   then the writes on the adopter operator's approval. This is `#607`, `#236` and
   `#243`'s field exercise in one session, and it pulls Phase 6's pilot forward.
2. **Stop shipping sprint tooling.** Give `verify_live_validation_bundle.py`, its test
   and `live-validation-evidence.md` a repo-only role, or drop them from the manifest's
   `files`, so `/upgrade` stops offering an adopter an engine with nothing to verify. A
   `CHANGELOG.md` entry is required: an adopter who took it needs to know it is
   withdrawn.
3. **Put review evidence on the pull request, once.** `pr_watch.py --record-review`
   posts a fixed-heading disposition comment at the head it records, and the merge gate
   reports a receipt with no matching comment (`#604`) and a body stamp whose sha is not
   `headRefOid` (`#603`), reported and not gating. `gh pr view <n> --json comments` on
   `#637`, `#651` and `#653` on 2026-09-02 showed a different heading on each, so the
   check cannot be built until the heading is fixed by the engine that writes it.
4. **A proportional opening pass for record prose (`#585`).** A diff whose changed
   paths are all `paths.handoff`, `paths.handoff_history`, `paths.friction_log`,
   `saved_plans/**` and `CHANGELOG.md` opens with the deterministic checks (budgets,
   links, closing keywords, stamp sha) and one correctness lens; the adversarial lens is
   for executed change. That is the pass the handoff pull requests above would have
   taken.
5. **Measure the suite before splitting it.** `pytest --durations=30` on a quiet tree,
   stamped; then a registered `evidence` marker for the bundle-walkers and the copytree
   fixture tests, and a `make test-fast` that excludes them, with `make test` unchanged
   as the verification command. `pytest-xdist` is a separate decision; the
   intermittents (`#393`, `#644`, the 2026-09-01 inbox entry) argue against it until the
   tmp-dir mechanism is known.
6. **Session-start reads through the engine.** Replace the hand-rolled `gh api` trio in
   `session-start.md:136-138` with `pr_watch.py <n> --json --no-persist` per open pull
   request, if the engine's report exposes unfiltered review evidence; if it does not,
   that is the enhancement, and the doc keeps its seen-state independence either way.
   Leave the `gh`-backend poll alone; fold only the REST branch's repeated fetch.
7. **Decide rather than build.** `#631`: declare that the Claude lane profile is
   task-scoping, that the boundary is the worktree plus branch protection, and that the
   Codex mirror is `--sandbox workspace-write`, then take the tracker disposition; the
   alternative is a lane-side execution guard nobody has asked for. `#608`: a "not
   observed, not load-bearing" matrix row. `#255`: one test that enumerates config keys
   with a per-runtime sub-map and requires a status declaration, which is the mechanism
   the issue's *Proposed* section asks for.
8. **Distill the learnings memo.** Promote the rules that recurred (stamp at the merged
   head, design matrix before the panel, probe before prose, positive construction plus
   recomputed mutation per accepted finding) into `fallback-review-panel.md` as doctrine;
   archive the per-PR sections; stop appending one per pull request.
9. **Give every fact one owner.** Split the matrix's headless-lane cell into a
   per-runtime sub-table whose cells link to the records; cut this plan's *Sprint
   status* to exits, owners and order; drop the *Phase 3 integration inventory* from
   this plan (the workflow docs own it).
10. **Adapter bodies as Markdown, not Python.** Move `_CURRENT_CONTEXTS` to one template
    file per runtime under `docs/templates/` and render from there, so the body an
    author edits is the one the renderer ships; add the appended-instruction mutation
    for `adopt`, `upgrade` and `pr-watch`.

## Sprint status — reconciled 2026-09-01, re-sequenced 2026-09-02

The machine-readable inventory and current capability judgments live in
[`runtime-parity.md`](../docs/agentic-dev-kit/runtime-parity.md); this plan supplies
their delivery order and exit conditions. This maintained status section reconciles
merged repository state; the stamped pre-implementation baseline below remains the
historical observation it was and is not silently refreshed.

- [x] **Phase 1 — Declare the parity contract.** PR `#588` merged on 2026-08-23 with
  the maintained capability matrix, shared-workflow inventory, explicit exceptions,
  and declaration-derived structural checks.
- [x] **Phase 2 — Correct safety and lifecycle hooks.** PR `#588` removed the
  Claude-only memory checker from Codex. PR `#590` routed shared safety doctrine and
  merged on 2026-08-24 with trusted-client hook evidence, canonical installer wiring,
  and exact-string lifecycle enforcement in `kit_doctor`. The controlled record in
  [`codex-safety-doctrine-live-validation_2026-08-24.md`](codex-safety-doctrine-live-validation_2026-08-24.md)
  then established, for the stamped trusted client observation, that Codex supplied
  the root route and read and applied the shared doctrine for affected merge-authority
  work. It does not generalize one client observation. Interactive-TUI
  `systemMessage` presentation remains an explicit live-client gap.
- [x] **Phase 3 — Complete workflow and integration coverage.** PR `#595` merged the
  bounded `post-merge-systemize` extraction with a shared definition, thin runtime
  bindings, config-owned policy, equivalent durable artifacts, and explicit capability
  preflights. PR `#596` merged the same structured contract for `session-start` and
  `wrap-up`. PR `#599` merged the config-owned draft/approve/finalize matrix and the
  independently observed forge-provenance chain for `triage-friction-log`, closing the
  remaining structural exit.
- [x] **Phase 4 — Make delegation and parallel lanes equivalent.** PR `#598` delivered
  the kit-owned engine boundary; PR `#609` delivered the Codex wrapper, its live record,
  and the declared Claude gap; PR `#611` generalised the wrapper to Claude
  (`claude -p`) with a Claude-produced live record and moved the parity row's Claude
  cell to the observed mechanism; PR `#614` added the config-owned approval policy per
  runtime and the Claude trust route with a Claude-produced writing-lane record; PR
  `#620` added the Codex-authored writing-lane record without changing the launcher;
  PR `#623` calibrated the capability tiers per runtime from live probes and declared
  every compute key mechanical or advisory per runtime. Delivery order and current
  disposition:
  1. Done in PR `#611` (Claude through `claude -p`, config-declared transports, Codex
     pinned unchanged). The record observed no write or approval transition and found
     that a fresh lane worktree is an untrusted workspace to Claude — the shape of the
     next item.
  2. Done in PR `#614` for Claude: `parallel.<runtime>_approval_policy` and
     `parallel.claude_settings_profile`, the trust route (`--setting-sources ""` plus
     the cockpit-owned profile), the structural profile validator, denial read-back,
     and a writing-lane record — a lane that performed a scoped write and landed a PR
     through its own `pr-watch`. That slice did not observe the Codex value.
  3. Done in PR `#620`: the Codex-authored record observed the scoped write, exact
     per-command approval transitions, network-disabled and network-enabled outcomes,
     ready pull request, and cockpit `dev_session.sh pr-watch` receipt. It also found
     that action denials described in final prose do not reach
     `terminal.permission_denials` through `last-message-file`, and that user config
     reached the untrusted lanes while project config did not. The raw receipts,
     rollouts, and captures were removed with the fixture, so the parity cell records
     the historical observation without promoting it as durable capability evidence;
     `#621` owns the durable evidence-bundle follow-up.
  4. Done in PR `#623` (squash `92a3c15`): tiers calibrated from live probes of the
     pinned clients (Claude Code 2.1.247, codex-cli 0.149.1, 2026-08-27) —
     `runtime_mappings` advisory on both runtimes with values each client accepted
     (`claude.expensive: fable`, `codex.expensive: xhigh`); `lens_compute.claude`
     mechanical through the kit-owned `.claude/agents/<lens>.md` rendered by
     `panel_prompt.py --agent-definition` (the delegation tool itself has no effort
     parameter, so a plain subagent stays at the cockpit's effort); `lens_compute.codex`
     mechanical on the `codex exec` argv and read back from the rollout. The blanket
     "no per-agent effort" sentence is retired on the surface it was false on and kept
     on the one it was true on. Design and record:
     [`capability-tier-calibration-design_2026-08-27.md`](capability-tier-calibration-design_2026-08-27.md),
     [`capability-tier-calibration-live-validation_2026-08-27.md`](capability-tier-calibration-live-validation_2026-08-27.md).
     PR `#655` later delivered the adopter-side `kit_doctor` check for stale lens
     definitions. The already-running doctor owns expected rendering while the
     existing file report owns installed-engine drift.
  5. Done, as a fail-closed run: the first real headless task on the generalised
     launcher (no tracker item; `#602` was the task the lane performed, not the slice).
     The lane ran on this repository with the launcher and every shipped configuration
     value byte-identical, and terminalized `failed` on a non-empty denial list. That
     establishes for Claude what the Codex record could not — structured denial
     read-back with real denials in it — and found two boundaries no synthetic lane
     could reach: a lane cannot write under `.claude/`, which `Edit(**)` does not lift
     and which the same lane's successful `.agents/` and `scripts/tests/` edits rule out
     as a glob effect; and the read-only Bash class is a property of command shape, so a
     loop or a `;`-chained compound of otherwise-accepted commands is denied. The lane
     opened no pull request; the cockpit pushed its branch and opened `#625` only after
     writing the file the lane was refused, so what stays unobserved is a *lane* driving
     CI or earning a `pr-watch` receipt on a real repository — not CI on that branch.
     Design and record:
     [`first-real-headless-lane-design_2026-08-28.md`](first-real-headless-lane-design_2026-08-28.md),
     [`first-real-headless-lane-live-validation_2026-08-28.md`](first-real-headless-lane-live-validation_2026-08-28.md).
     Not built: a model or effort control on the wrapper, which the run gave no reason
     to add — the lane resolved to the product default and the task did not need
     another tier.
     Adopt now, mechanise later: the final verification stamp is a PR comment at the
     merged head, and a panel that ran leaves a disposition comment (`#603`, `#604`).
     Phase 5 owns `#236`, the `#243` narrowing (adapter generation), and `#631`; Phase 6
     takes `#607` as the adopter pilot and `#608`.
  6. Carried by PR `#651`: the repository-owned redacted evidence contract, hostile
     missing/altered/wrong-revision/claim-relabel mutations, and tracked positive
     control now refuse promotion when the retained bytes, complete claim-to-artifact
     map, independently expected applied compute for a claim that depends on it,
     review provenance, or binding are absent. A persistent Codex
     writing lane at source revision
     `bdfd6ee702a630f0575f0c186f51b3bbbcd1810a` produced descriptor-scoped worktree and
     state output, an open non-draft private pull request with GitHub `CLEAN` state,
     and an exact-head cockpit review
     receipt; the promotion retains the exact upstream and fixture source bytes those
     claims depend on and is bound to synthetic fixture revision
     `83d3b623305a691dd874df44ca92270daa62ade9`, repository, and head
     `5c4006d18e65e0443dc7b22f48c099ad07ce1da9`. The copied runtime attestation does not
     correlate its session to the launcher invocation, so its model, effort, and cwd
     remain historical and outside the promoted claim map. The 2026-08-27 record also
     stays historical and unpromoted. The retained record is
     [`codex-writing-lane-live-validation_2026-08-30.md`](codex-writing-lane-live-validation_2026-08-30.md).
     This implements `#621`'s durable-evidence contract for the bounded writing-lane
     claims. It does not establish the Phase 4 exit: the retained run is a writing
     lane, not the parallel batch the exit condition requires. The remaining exit is a
     retained, independently recomputable Codex parallel-batch run that demonstrates
     disjoint worktree and state-root identities, exact-head review evidence, and
     operator merge authority without merging.
  7. Done in PR `#659`: the Codex-produced parallel batch retains both descriptor and
     launcher identity chains, independent filesystem and Git read-backs, both exact
     reviewed heads and dual-lens receipts, operator merge refusals, reconciliation's
     held outcome, final open/unmerged forge state, exact source bytes and Git-object
     proofs, and a complete external path/provenance/digest control. The promoted
     claims and caveats are in
     [`codex-parallel-batch-live-validation_2026-09-01.md`](codex-parallel-batch-live-validation_2026-09-01.md).
- [ ] **Phase 5 — Align permissions, installation, and upgrades.** Merged deliveries
  now include PR `#632` for the measured Claude lane policy and permanent adapter-write
  asymmetry; PR `#635` for generated adapter refresh plus manifest-selected installed
  tests; PR `#637` for the templated cockpit grant advisory, open-ended SessionStart,
  and informational permission inspection; PR `#639` for the allow-side whole-tool
  rule measurement; and PR `#649` for the safety-critical classification of the
  configured lane profile; and PR `#655` for adopter-side stale lens-definition
  inspection. The exit is not yet established. `#236` retains the engine/doctrine
  same-function-different-path survey, `#243` retains field exercises for `adopt`,
  `parallel`, `triage-friction-log`, and `post-merge-systemize`, and `#631` retains the
  lane execution-boundary decision. The 2026-09-01 tracker reconciliation closed
  `#606`. `#255` needed implementation after all: PR `#657` carried the
  `runtime_mappings` status declaration to `init.sh`'s migration surface, which the
  reference config alone had carried. `#255` stays open on the general rule its
  *Proposed* section states rather than on the two keys its comments name —
  `review.fallback_commands` and `runtime.launchers` still declare no per-runtime
  status, and no mechanism yet prevents the next such key. **Re-sequenced on
  2026-09-02** (*Sprint review* above): the cs-toolkit adopter pilot moves from Phase 6
  into this phase as its exit test, because the exit is only establishable by an
  upgrade run; assigning the live-validation verifier a repo-only role and withdrawing
  it from the adopter-shipped set, plus putting review evidence on the pull request
  (`#603`, `#604`), join the phase; `#631` and `#608` are taken as declarations rather
  than mechanisms, while `#255` retains its general enforcement mechanism. Delivery
  order, updated on 2026-09-03 by operator direction after the repo-only delivery:
  1. [x] Adopter pilot, read-only pass first (`#607`, `#236`, `#243`).
  2. [x] `pr_watch.py --record-review` posting the disposition comment; stamp/head and
     receipt/comment mismatches reported.
  3. [x] Verifier, its test, and its evidence page assigned the repo-only manifest role,
     with the `CHANGELOG.md` entry.
  4. [ ] The initial pilot write pass, on the adopter operator's approval, followed by a
     separate fork-reconciliation stage based on the upgrade branch. Record the kit source
     SHA plus every created PR identity, base name, and head; record a no-change stage's
     input and output SHA, tree equality, and clean status instead of manufacturing a
     PR. File any residue. This pass does not establish the phase exit.
  5. [ ] The remaining `#243` field exercises completed, `#631` and `#608` decided on the
     tracker and matrix, and `#255`'s general mechanism delivered.
  6. [ ] Replay the write pass and fork reconciliation from the then-current kit source.
     For a stage with a diff, bind its PR identity, base and head and require the
     protected → upgrade → reconciliation chain for the PRs that exist. For a
     no-change stage, stamp its input and output SHA, tree equality, and clean status;
     never manufacture an empty PR. Verify the resulting adopter head against the
     condition. Movement of a bound adopter ref before the exit read-back invalidates
     the evidence. Capture one
     authoritative tuple containing the kit source and protected head, the adopter
     protected head, every created adopter PR's identity, base and head, and each
     no-change stage's input/output equality, tree-equality check, and clean status.
     Require the kit source to equal the protected head in both snapshots. Verify every
     ancestry edge and the adopter condition against those immutable SHAs, then capture
     the full tuple again and require it to be byte-identical. A mismatch requires
     replay. Publish both snapshots and the stamped verification result on the kit
     wrap-up PR before it merges. Later ref movement is a separate event; wrap-up records
     the observation without treating its own commit as the replay source.
- [ ] **Phase 6 — Gate parity and roll it out.** With the pilot pulled into Phase 5,
  this phase holds the cost and hygiene work the review found burning, then the gate:
  the proportional opening pass for record prose (`#585`); the suite measured and
  marked (`make test-fast` beside an unchanged `make test`); the learnings memo
  distilled into `fallback-review-panel.md`; the matrix's headless-lane cell split per
  runtime and this plan cut to exits and order; `session-start`'s forge reads routed
  through the engine; adapter bodies moved from `_CURRENT_CONTEXTS` to per-runtime
  templates with the missing hostile mutations; and only then adoption fixtures,
  trusted smoke coverage, maintained parity reporting, and the convergence plan
  archived behind the matrix.

This plan records the pre-implementation baseline. Its repository observations were
collected with `rg --files`, targeted `rg`, and
`uv run scripts/kit_doctor.py --json` at
`9c4969687f9adbec1eca55cbfb47955d85025026` on 2026-08-23. They intentionally describe
that revision; the delivery slices below are expected to change them.

## Phase 3 integration inventory — 2026-08-25

### `session-start`

- **Shared semantics:** gather the handoff, friction inbox, tracker, pull requests,
  repository state, CI/cron health, and project drift; classify traceable candidates;
  remediate false `Now` promotions; render one briefing and recommendation.
- **Runtime translation:** Claude passes `$ARGUMENTS`; Codex passes the user's request.
  Each runtime selects its own read mechanisms and may apply the configured model or
  effort mapping only when its launcher actually exposes that control.
- **Capabilities:** repository/config and repository-state reads are required. Forge,
  CI/cron, and tracker reads are always attempted and degrade visibly; forge readiness
  uses unfiltered review evidence, labels resolution the forge cannot prove, and
  represents detached HEAD explicitly.
  Configured drift reads degrade visibly when applicable. Archive and resolved-
  tracker reads are conditional before a `Now` promotion. Runtime compute selection is
  an optional enhancement.
- **Authority and artifacts:** the workflow is read-only and creates no durable state.
  The returned briefing is load-bearing; live sources, not an earlier response, are
  retry evidence. Non-interactive use renders once and exits.
- **Stops and mismatch:** required-source failure is a hard stop; optional-source gaps
  produce degraded success without false empty/clean claims. The Codex adapter repeated
  read-only and compute policy that belongs in the shared definition; this slice removed
  that duplicate.

### `wrap-up`

- **Shared semantics:** author and validate the living record, route session friction,
  preserve a next starter, enforce document budgets, stage named paths, and carry the
  record pull request through shared review follow-through.
- **Runtime translation:** Claude and Codex select native repository, forge, review, and
  tracker mechanisms. Invocation itself remains runtime-specific; capability policy and
  approval semantics do not.
- **Capabilities:** repository/config read and handoff write are required. The document-
  budget checker is required; the archive helper is conditional on its result. Forge PR
  write and `pr-watch` are conditional on any changed repository artifact. Tracker
  search/write is
  conditional and payload-approval-gated for an issue-shaped finding; an existing
  project-status artifact is an optional enhancement. Merge authority is conditional
  after the exact head becomes mergeable.
- **Authority and artifacts:** invocation authorizes the scoped repository record and its
  branch/PR path, not a merge. Tracker creates, modifications, and occurrence comments
  require the exact payload to be confirmed by the operator in the current interactive
  session. An interactive issue-shaped finding is searched and presented for that
  decision before parking. Durable evidence is every changed repository artifact,
  including an existing project-status artifact, its reviewed merge
  or exact operator-held head when changed, a parked friction entry, or an identifier
  actually returned and read back from the tracker.
- **Stops and mismatch:** a required failure preserves the record and stops before a
  false completion. Tracker unavailability, decline, silence, or ambiguity degrades to
  the friction inbox; incomplete and accumulating findings also take that route. Missing
  or insufficient merge authority holds a mergeable pull request for the operator; a
  policy-less non-lane pull request takes the operator default. Conditional capabilities
  classify at their trigger rather than before the record edit; unavailable forge or
  unsettled review paths preserve exact resume evidence as incomplete. First-match
  terminal precedence also keeps a degraded integration from masking an incomplete
  repository path or a failed or still-ambiguous authorized merge; a tracker-only write
  is successful completion, not a no-op, and isolated review plus self-merge stay on
  the cockpit's paired lane wrappers and shared state sandbox. The
  Codex adapter's generic external-mutation wording was weaker than the shared payload-
  specific gate; this slice removed that duplicate.

### `triage-friction-log`

- **Shared semantics:** draft proposals from a frozen inbox, obtain exact operator
  decisions, persist an approval session, file approved tracker payloads, and finalize a
  no-data-loss archive sweep on a reviewable branch.
- **Runtime translation:** Claude accepts `$ARGUMENTS`; Codex accepts the skill argument.
  Each runtime needs native tracker and notification clients, but neither adapter should
  choose their policy.
- **Capabilities:** repository/config, sandbox-aware state resolution, and an exact
  frozen inbox are required. Tracker write/read-back is conditional after exact-payload
  approval. Scheduled approval collection requires notification send/thread read, while
  interactive notification failure degrades to the current session. The configured
  draft/finalize pair is atomic; both absent selects an honest agent-executed LLM-only
  mode and a partial pair stops.
- **Authority and artifacts:** the frozen inbox, proposal report, approval-bound state,
  returned tracker identifiers, source/archive diff, and PR are resume evidence. Tracker
  writes require exact-payload approval; a standing workflow request is not approval.
  Commit, push, pull-request creation, `pr-watch`, archive sweep, and merge read-back
  consume the exact identity established by the preceding independently verified
  read-back rather than a locally self-consistent lifecycle record.
- **Stops and mismatch:** active approval state cannot be overwritten; missing frozen
  evidence never falls back to a whole-inbox sweep; changed approved payloads require a
  new decision; failed or ambiguous tracker/forge writes require destination read-back;
  partial tracker success holds before finalization; and test mode cannot write tracker,
  source documents, or forge state. Shared precedence distinguishes hard-stop,
  operator-held, degraded success, and successful completion. Both adapters now carry
  invocation/mechanism translation only.

### Slice boundary and next starter

PR `#596` merged the shared contract for `session-start` and `wrap-up`, whose
integration surface can use existing config, runtime-native mechanisms, and the shipped
helpers named by each definition without adding a dedicated pipeline configuration. It
did not add a partial triage config, pretend the missing engines are ready, or duplicate
approval policy in an adapter.

PR `#598` advances the shared lane primitive without claiming the Phase 3 exit. Its
read-only comparison of cs-toolkit commit
`4cf1ca914361b9912cd6bb1389e985d6e97ab3a0` (`#2086`) and its parent separated reusable
engine behavior from cs-toolkit policy/translation and unrelated application code. The
kit receives absolute headless roots, the descriptor environment replacement contract, durable
lane/base/class identity, exact repository/PR/base/head/fork binding, fail-closed forge
reads, operator-held evidence, resume-aware branch-tip checks, semantic/mutation
matrices, and adopter upgrade coverage. It does not receive cs-toolkit's operator-only
merge policy or `CS_TOOLKIT_*` namespace. The downstream checkout remains unchanged;
its repo-owned engines require a later explicit reconciliation PR rather than a normal
kit upgrade.

PR `#599` delivered the Phase 3 starter and closed the declared structural exit. The
starter it preserved (`feat/codex-environment-capable-launcher`) was consumed by PR
`#609` on 2026-08-26. The next sprint starter set by the 2026-09-02 review was consumed
by the read-only adopter pass later that day:

```text
In a Claude Code session, run the cs-toolkit adopter pilot read-only first. Bind
REPO=/Users/topi/Coding/in-parallel/cs-toolkit and KIT=<fresh clone of this repo at a
pinned sha> before anything else and assert pwd before every write. Run kit_doctor in
both modes from $KIT against $REPO and record the output stamped, including the false
"broken, not sized down" verdict on scripts/devkit/lib/runtime_adapters.py. Walk
/upgrade Steps 0-3 without writing. File what the instrument gets wrong as occurrences
on #236 and what the adapters need as occurrences on #243, on the operator's approval
of each payload. Stop before any write to $REPO; the write pass is its own session on
the adopter operator's go-ahead. Do not widen the kit in the same session.
```

## Pre-implementation assessment

### Aligned foundation

- `session-start`, `wrap-up`, `pr-watch`, `parallel`, `adopt`, `upgrade`, and
  `triage-friction-log` have runtime-neutral definitions under
  `docs/agentic-dev-kit/workflows/` and thin bindings under both
  `.claude/commands/` and `.agents/skills/`.
- `AGENTS.md` is the shared repository contract, and `CLAUDE.md` imports it rather
  than maintaining a second copy.
- The document-budget and PR-follow-through mechanisms have registrations for both
  runtimes.
- Review configuration already has runtime-specific fallback commands and compute
  mappings.

### Gaps to close

- `post-merge-systemize` remains a Claude-only command with no shared workflow or
  Codex skill.
- Claude has a path-scoped safety-doctrine binding under `.claude/rules/`; Codex
  relies on broader `AGENTS.md` prose and has no equivalent triggered binding in
  this repository.
- Codex SessionStart invokes `check_memory_budget.py`, although that engine explicitly
  targets Claude Code's external `MEMORY.md` and states that the artifact has no Codex
  equivalent.
- `init.sh` carries Codex hook guidance derived from an older measured client whose
  matcher and trust behavior did not match the documented surface reviewed for this
  baseline.
- Codex capability tiers vary reasoning effort but do not select a model, despite
  the documented subagent support for both controls reviewed for this baseline.
- The headless-lane contract requires worktree and environment replacement, while
  native Codex subagent dispatch does not itself provide that launch contract.
- Claude repository permissions are shipped in `.claude/settings.json`; the kit has
  no corresponding policy for trusted project `.codex/config.toml` or
  `.codex/rules/`.
- Tracker and notification workflows assume suitable CLI or MCP integrations, but
  Codex skill metadata declares no tool dependencies or preflight contract.
- `/upgrade` refreshes shared workflow definitions but keeps existing runtime
  adapters, so Codex metadata and adapter-specific fixes do not reliably reach
  adopters.
- Adapter coverage is maintained through a hardcoded test list rather than derived
  from the repository's declared runtime-parity contract.
- The repository has static coverage for Codex shapes but no trusted, end-to-end
  Codex smoke test covering instructions, skills, hooks, review, and isolated lanes.
- `docs/kit-convergence-plan.md` preserves historical status that is easy to misread
  as the live parity inventory, and README hook descriptions have drifted from
  the shipped Codex registration.

## Delivery plan

### Phase 1 — Declare the parity contract

- Add a maintained runtime-capability matrix covering workflows, persistent
  instructions, safety activation, hooks, permissions, model controls, subagents,
  external integrations, adoption, upgrade, and drift detection.
- Define parity as equivalent outcomes and safety guarantees rather than identical
  runtime configuration files.
- Declare every intentional exception in the matrix so absence cannot masquerade as
  support.
- Derive structural parity checks from that declaration instead of restating the
  expected adapter set in tests.

Done when every shipped workflow and enforcement mechanism has a declared Claude
path, Codex path, or explicit exception.

### Phase 2 — Correct safety and lifecycle hooks

- Stop registering the Claude memory-budget checker on Codex.
- Decide separately whether Codex needs an instruction-chain budget checker for
  `AGENTS.md`; do not relabel the Claude engine as portable.
- Revalidate Codex SessionStart, PostToolUse, matcher, timeout, output, and trust
  behavior against the supported client.
- Update installer guidance, hook comments, documentation, and tests from that live
  measurement.
- Bind safety-critical doctrine through concise shared `AGENTS.md` routing and nested
  instruction files where directory scoping is useful.
- Extend `kit_doctor` from path resolution to semantic registration checks.

Done when a clean trusted Codex checkout runs only the intended lifecycle hooks and
loads the safety doctrine for affected work.

### Phase 3 — Complete workflow and integration coverage

- [x] Extract `post-merge-systemize` into a shared workflow.
- [x] Replace the Claude implementation with a thin binding and add a Codex skill with
  UI metadata.
- [x] Define the workflow's capability contracts for forge, tracker, reviewer, and
  notification access.
- [x] Add explicit preflight behavior for unavailable tools and credentials.
- [x] Keep runtime tool selection in the adapters and capability preflight. Codex UI
  metadata uses the repository's supported `interface` shape; it does not claim a
  connector dependency that the client cannot mechanically require.
- [x] Apply the capability-contract pattern to `session-start` and `wrap-up` without
  moving their policy into adapters.
- [x] Apply the capability-contract pattern to `triage-friction-log` without moving its
  policy into adapters.

The bounded workflow slice is done when either runtime can execute the retro workflow
and produce the same durable artifacts. The phase is structurally complete:
`session-start`, `wrap-up`, and `triage-friction-log` carry explicit required,
degraded, held, resume, authority, and completion paths under shared definitions.

### Phase 4 — Make delegation and parallel lanes equivalent

- [x] Select a Codex lane launcher that sets worktree and complete lane environment,
  removes inherited identity, and binds child-observed identity plus final text to a
  one-shot receipt. The bounded launcher does not calibrate model, reasoning effort,
  or project permission mode.
- [x] Keep native subagents unsupported for headless state-writing lanes because their
  dispatch surface cannot apply the descriptor environment and observer/receipt chain;
  use the selected wrapper or remain attended.
- [x] Add a synthetic live check for lane worktree, repository, branch/base, state root,
  process, inherited-variable removal, and final-text binding at the stamped client.
- [x] Generalise the same wrapper contract to Claude through `claude -p`, with the
  runtime-under-test producing the live record (`#466`; PR `#611`).
- [x] Add config-owned approval/sandbox policy per runtime and the Claude trust route,
  with a Claude writing-lane live record (`#601`; PR `#614`).
- [x] Produce the Codex writing-lane live record from a Codex session before model or
  effort calibration (`#601`; PR `#620`). That 2026-08-27 record remains unpromoted
  because its raw fixture evidence was removed at cleanup; its historical observations
  stay bounded to that client and revision.
- [x] Rerun the Codex writing lane through the durable redacted bundle contract
  (`#621`; PR `#651`). The retained promotion binds the source revision, reviewed
  synthetic repository and head, client, persistent session carrier, independent
  redaction reviewer, authoritative observers, exact source bytes and their retained
  Git commit/tree membership proofs, destination digests, and exact-head review
  receipt. The uncorrelated model, effort, cwd, and session attestation remains a
  historical observation outside the promoted claim map. The receipt promotes only
  the complete independently expected claim objects and refuses absent, altered,
  ephemeral, wrong-revision, relabeled, or evidence-thinned carriers.
- [x] Calibrate both runtimes' neutral tiers and mechanically pass supported model/effort
  keys to fallback-review lenses (`#605`, `#255`).
- [x] Use the generalised launcher for the first real headless task only after those slices
  land (untracked; not `#602`).

Done when a Codex parallel batch preserves the same state isolation, review evidence,
and merge authority as Claude usage. The persistent 2026-08-30 writing-lane rerun does
not establish that exit. It retains source revision
`bdfd6ee702a630f0575f0c186f51b3bbbcd1810a`, reviewed synthetic head
`5c4006d18e65e0443dc7b22f48c099ad07ce1da9`, descriptor state, exact-head review
evidence, and operator merge class without merging, but contains no parallel-batch or
inter-lane observation. PR `#659` establishes the exit through the
[retained 2026-09-01 parallel-batch run](codex-parallel-batch-live-validation_2026-09-01.md):
its independently recomputable promotion binds disjoint lane worktrees and state roots,
scope-local exact-head reviews, operator-class merge refusal, reconciliation-held state,
and final open/unmerged fixture pull requests.

### Phase 5 — Align permissions, installation, and upgrades

- [x] Decide the shipped Claude lane allowances as repository policy and bind the Codex
  side by equivalent safety doctrine rather than copied command syntax (PR `#632`).
  The profile is task-scoping rather than a hostile-code boundary; `#631` owns the
  executable-boundary mechanism.
- [x] Make generated Claude and Codex adapters refreshable while preserving
  adopter-authored variants, and make upgrade verification select the manifest-declared
  installed tests (PR `#635`). `#236` keeps the engine/doctrine survey where path or
  slug cannot identify equivalent function.
- [x] Template the cockpit permission advisory on `paths.engines`, remove the narrow
  SessionStart matcher on both runtimes, inspect cockpit grant coverage without failing
  healthy adopters, and replace the unmeasured whole-tool rule with allow-side evidence
  (PRs `#637` and `#639`). The 2026-09-01 tracker reconciliation retired `#606`.
- [x] Treat the configured Claude lane profile as safety-critical adopter-owned policy
  through the Codex root binding and Claude path-scoped binding (PR `#649`). `#346` and
  `#434` remain separate workflow/test binding-coverage decisions.
- [ ] Exercise the remaining runtime-specific adapter translations through `adopt`,
  `parallel`, `triage-friction-log`, and `post-merge-systemize` (`#243`).
- [x] Inspect adopter-side generated lens definitions against their configured
  mechanical compute carrier without duplicating installed-engine drift (PR `#655`;
  `#255`'s general enforcement mechanism remains separate).
- [x] Complete the cs-toolkit adopter pilot's read-only pass from a pinned kit clone
  with `$REPO` and `$KIT` bound; its stamped instrument readings live in
  [`cs-toolkit-adopter-pilot-readonly_2026-09-02.md`](cs-toolkit-adopter-pilot-readonly_2026-09-02.md)
  (`#607`, `#236`; added 2026-09-02).
- [ ] Run the initial write pass on the adopter operator's approval and a separate
  fork-reconciliation stage based on its branch. Record the kit source SHA plus every
  created PR identity, base name, and head; record a no-change stage's input and output
  SHA, tree equality, and clean status instead of manufacturing a PR. Do not close the
  phase.
- [x] Give `scripts/verify_live_validation_bundle.py`, its test and
  `live-validation-evidence.md` the repo-only role: retain release-manifest hashing
  and the kit checkout's drift check while omitting them from adopter inspection,
  install baselines, and `/upgrade` offers (`#662`, PR `#670`; added 2026-09-02).
- [x] Have `pr_watch.py --record-review` post a fixed-heading disposition comment at
  the recorded head, and report a receipt without that comment and a body stamp whose
  sha is not `headRefOid` (`#603`, `#604`, PR `#667`; added 2026-09-02).
- [ ] Decide `#631` as a declaration: the Claude lane profile is task-scoping, the
  boundary is the worktree plus branch protection, and the Codex mirror is
  `--sandbox workspace-write`; the Claude prefix list and Codex sandbox syntax are not
  interchangeable and no lane-side execution guard is built without a request for one
  (re-sequenced 2026-09-02; the earlier wording asked for executable evidence first).
- [ ] Declare `#608` as a matrix row and deliver `#255`'s general mechanism as one
  test over per-runtime config keys (added 2026-09-02).
- [ ] Replay the adopter write pass and fork reconciliation from the current kit
  protected-branch head. Bind every created PR's identity, base and head and require the
  protected → upgrade → reconciliation ancestry for the PRs that exist. For a
  no-change stage, stamp its input and output SHA, tree equality, and clean status
  instead of manufacturing an empty PR. Verify the resulting adopter head against the
  condition. Movement of a bound adopter ref before the exit read-back invalidates the
  evidence. Capture one
  authoritative tuple containing the kit source and protected head, the adopter
  protected head, every created adopter PR's identity, base and head, and each no-change
  stage's input/output equality, tree-equality check, and clean status. Require the kit
  source to equal the protected head in both snapshots. Verify every ancestry edge and
  the adopter condition against those immutable SHAs, then capture the full tuple again
  and require it to be byte-identical. A mismatch requires replay. Publish both snapshots
  and the stamped verification result on the kit wrap-up PR before it merges. Later ref
  movement is a separate event; wrap-up records the observation without treating its own
  commit as the replay source.

Done when an existing Codex adopter can upgrade without retaining stale runtime
behavior or losing local policy, the remaining `#243` field exercises are complete,
`#631` and `#608` carry their declarations, and `#255`'s general mechanism is delivered.
The final adopter replay binds the kit protected-branch head to its source SHA; binds
every created adopter PR identity, base name, and head; records any no-change stage's
input and output SHA, tree equality, and clean status; proves the ancestry chain for the
PRs that exist; and verifies the resulting adopter head against the condition. Movement
or retargeting of a bound adopter ref invalidates the evidence when it occurs before the
exit read-back. Capture the full authoritative tuple of kit and adopter protected heads
plus every created adopter PR's
identity, base and head and each no-change stage's input/output equality, tree-equality
check, and clean status. Require the kit source to equal the protected head in both
snapshots; verify the ancestry edges and adopter condition against those immutable SHAs;
then capture the tuple again and require a byte-identical result. Publish both snapshots
and the stamped verification result on the kit wrap-up PR before it merges.
That stable bundle establishes the exit at the refs it names. Later work carries its
own verification obligation rather than rewriting the observation; wrap-up records the
event without treating its own commit as the replay source. Nothing else establishes
the exit; merged delivery slices are not used as a reassuring substitute for it.

### Phase 6 — Gate parity and roll it out

Re-sequenced 2026-09-02: the pilot moved to Phase 5, and the cost and hygiene work the
review found burning comes before the gate, because the gate would otherwise inherit
the cost.

- Add the proportional opening pass for record-prose pull requests (`#585`):
  deterministic checks plus one correctness lens when every changed path is a record
  surface.
- Measure the suite (`pytest --durations`, stamped), register an `evidence` marker for
  the bundle-walking and copytree fixture tests, add `make test-fast`, keep `make test`
  as the verification command.
- Distill `review-process-learnings_2026-08-24.md` into `fallback-review-panel.md`
  doctrine and archive its per-PR sections.
- Split the matrix's headless-lane cell into a per-runtime sub-table linking to the
  records; cut this plan's *Sprint status* to exits, owners and order; drop the
  *Phase 3 integration inventory* from this plan.
- Route `session-start`'s open-pull-request reads through `pr_watch.py --json
  --no-persist`; fold the REST backend's repeated fetch inside `pr_watch.py`.
- Move adapter bodies from `_CURRENT_CONTEXTS` to per-runtime templates and add the
  appended-instruction mutation for `adopt`, `upgrade` and `pr-watch`.
- Add fresh-repository fixtures for Codex-only, Claude-only, and dual-runtime
  adoption.
- Add trusted Codex smoke tests for instruction discovery, skill discovery,
  SessionStart, PostToolUse, `/review`, fallback panels, and parallel lanes, run on
  demand with a stamped record rather than in pull-request CI.
- Keep Claude integration smoke tests beside them where automation credentials permit.
- Replace the historical convergence status with the maintained parity matrix and
  move historical analysis to an archive.

Done when the parity matrix is enforced by deterministic checks and confirmed by the
Phase 5 adopter run.

## Completed review and shared-integration slices

PR `#593` delivered the review-evidence composition workstream separately from the
trusted-client validation: the shared engine now preserves a full-panel parent plus an
exact-head delta, validates ancestry, paths, heads, lenses, and pass caveats, and keeps
legacy receipts compatible. The shared fallback doctrine and prompt builder already
carry the full-versus-delta routing rules; Claude and Codex consume those same semantics.

Do not add a generic path or prose classifier as the next slice. The remaining review
gap is a deterministic artifact that can prove record-only semantics and independently
bind posted delta-draw verdicts; Git paths and author-supplied labels cannot establish
either fact. Until such an artifact exists, uncertain classification continues to take
the full-panel route and issue `#32` remains the provenance boundary.

PR `#596` then merged the shared integration contract for the lifecycle bookends. PR
`#599` completed that phase with config migration, frozen approval state, exact
external-write authority and read-back, cross-operation forge provenance, total
outcomes, thin adapters, and declaration-derived hostile mutations.

PR `#598` then moved the reusable lane-identity and forge-safety behavior exposed by
cs-toolkit `#2086` into kit-owned engines and shared workflows. It deliberately leaves
runtime launcher mechanics and downstream repo-owned engine adaptation outside the
slice. The environment-capable launcher workstream then selected the kit-owned stable
`codex exec` wrapper, added descriptor/receipt authority and synthetic live isolation
evidence, and left compute calibration plus downstream adaptation outside its boundary.

Keep the trusted-client record as an observation at its stamped client and revision; do
not turn it into a general instruction-loading guarantee.
