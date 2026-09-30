# Phase 5 D — PHASE5-D-SYSTEMIZE-ENGINE-01 approval packet

**Prepared for approval; nothing below is approved or executed.** This binds the
D-SYSTEMIZE-ENGINE row of the [D proposal](phase5-d-proposal_2026-09-21.md)
("Subsequent D packages and evidence gates") into an executable scope, in the same
form as PHASE5-D-TRIAGE-ENGINE-01. Topi owns scope changes and the merge decision.

## Grounding reads

All reads below were taken in `/Users/topi/Coding/agentic-dev-kit` on 2026-09-23 at
`92926ca62ea1b31cba81e7f9be4b33274513a034` (`origin/main`, which is #768's merge).

- `ls scripts/fetch_merged_prs.py scripts/digest_merged_prs.py scripts/heartbeat_cli.py`
  → all three `No such file or directory`. The configured set is wholly absent, so
  `post-merge-systemize` runs LLM-only today.
- `config/dev-model.yaml` `systemize:` declares `fetch_engine`, `digest_engine` and
  `heartbeat_engine` by filename only. No key names the heartbeat's state path, its job
  name or its invocation. `init.sh` carries its own copy of that block.
- The shared workflow `docs/agentic-dev-kit/workflows/post-merge-systemize.md`
  says to invoke the engines, but it defines no CLI for them. It also says how the
  heartbeat is used (start before the fetch, a tick after the digest and after each
  slice, complete as the final write), without a state contract. And it asks for an
  "addressed state when evidenced" without saying what counts as evidence. #748
  (adopter-filed, open) measured what that gap does to an LLM-only run: 15 of 16
  "unaddressed" findings were already addressed, 10 of them with
  `reviewThreads.isResolved == true`.
- `scripts/tests/test_portability.py` pins text from that workflow, so any workflow
  edit also edits that file.
- Donor `/Users/topi/Coding/in-parallel/cs-toolkit` read at
  `f76b319707628065c3bfea976732f2654d1dcef2`. `git log 53f2f17..HEAD` over the three
  scripts plus `libs/pipeline-engine/src/pipeline_engine/heartbeat.py` printed
  nothing, so they are unchanged since the proposal's read. The repository root has no
  `LICENSE*` file. The donor derives addressed state from reply-text regexes, which is
  the heuristic #748 measured, and its heartbeat is customer-fan-out shaped.

## Proposed approval: PHASE5-D-SYSTEMIZE-ENGINE-01

**Purpose:** ship the configured fetch, digest and heartbeat engine set against the
shared systemize declaration, so that the presence of all three files selects
engine-backed mode honestly. This is an implementation slice. It is not a live
systemize run, and it includes no scheduler installation, rule PR, friction append,
tracker write or notification.

**Runtime and compute.** Implementation runs inline in this Claude Code session.
`systemize.analysis_tier` and this work are `expensive`, which
`models.runtime_mappings.claude` maps to `fable`. This session cannot switch its own
model, so the tier is guidance here and no switch is claimed. Review lenses use the
configured `review.fallback_panel.lens_compute.claude` values through
`scripts/panel_prompt.py`.

**Workspace.** Use branch `feat/phase5-d-systemize-engine`, created from `92926ca` in
the control checkout. Keep synthetic state, fake-forge fixtures and temporary homes
under `DEVKIT_STATE_ROOT` directories inside the scratchpad or pytest `tmp_path`, never
the production `state/` root. Retain reviewable evidence (the requirement ledger,
verification logs and review disposition) under
`state/review-evidence/phase5-d-systemize-engine-01/`. Use absolute write paths.
Do not touch the retained B/C fixture or the triage evidence namespace.

**Donor decision.** Write an independent implementation of the kit contract. The donor
has no licence file, so reuse authority is not established. Its addressed-state
heuristic is the defect #748 documents, and its heartbeat shape belongs to another
pipeline. It stays a read-only reference, for the source-severity badge vocabulary
only. No donor bytes are copied.

### Design decisions bound by this approval

1. **Heartbeat configuration: two new keys, required only in engine-backed mode.**
   - `systemize.heartbeat_job`, default `post-merge-systemize`: the job name written
     into the state file.
   - `systemize.heartbeat_pattern`, default
     `state/automation-progress/post-merge-systemize_{window}_{mode}_{date}.json`:
     a logical state path under the same `{window}`/`{mode}`/`{date}` placeholder
     rule, resolver and target-safety checks as the cache and digest.

   Both are validated only when the complete engine set is present. An adopter whose
   config lacks them keeps a working LLM-only run, so the change is `ADDED`/`CHANGED`
   rather than `BREAKING`. A partial engine set still stops, as today.
2. **Addressed-state evidence is named in the shared workflow, not only in the engine.**
   - `addressed` means the forge reports the finding's review thread
     `isResolved == true`.
   - `outdated` means an unresolved thread with `isOutdated == true`, which is
     inconclusive and kept distinct.
   - `unaddressed` means an unresolved, current thread.
   - `unevidenced` means a finding with no thread, such as a review body or an issue
     comment.

   Ranking counts every value except `addressed` as unaddressed, which keeps it
   conservative. The report states the tri-state honestly. This is the smallest
   workflow edit that keeps LLM-only and engine-backed digests the same. #748 is
   referenced, and whether the PR discharges it is left to review (no closing
   keyword).
3. **RFC 8785 canonicalisation:** import `scripts/lib/triage/canonical.py` unchanged,
   rather than writing a second implementation, because the config fingerprint and run
   identity must be byte-identical across engines and runtimes. The manifest declares
   the dependency. Promoting it to a neutral `scripts/lib/` module is out of scope,
   since it would touch the triage engines.
4. **Guideline-citation state** is detected deterministically. A finding counts as
   `cited` when it names a path in the repository's active instruction or
   shared-workflow set, or when it carries a reviewer's own guideline marker ("as per
   coding guidelines", "based on learnings"). The matched evidence is recorded.
   Otherwise it is `none`.

### Implementation footprint (frozen allowlist)

- Entry points: `scripts/fetch_merged_prs.py`, `scripts/digest_merged_prs.py`,
  `scripts/heartbeat_cli.py`. All three are PEP 723 scripts, stdlib plus PyYAML (via
  `kitconfig`), and all three must be installed together.
- Helpers: `scripts/lib/systemize/`, covering config validation and fingerprint, run
  identity, artifact target safety and identity reuse, the forge provider behind an
  injectable runner, severity/addressed/citation normalisation, ranking and cap, digest
  validation and heartbeat state.
- Tests: `scripts/tests/test_systemize_*.py`.
- Shipping wiring, edited only as far as needed:
  - `config/dev-model.yaml` and `init.sh`'s embedded block, for the two keys;
  - `kit-manifest.json`;
  - `CHANGELOG.md`, in this PR's numbered entry;
  - the shared `post-merge-systemize.md`, for the CLI contract, the heartbeat keys and
    the addressed-evidence definition;
  - `scripts/tests/test_portability.py` and `scripts/tests/fixtures/init-config.json`,
    only for the pins those edits move.
- Excluded: `pr_watch.py`, `dev_session.sh`, `launch_lane.py`, lane settings, the
  runtime adapters under `.claude/commands/` and `.agents/skills/`, the triage engines
  and unrelated cleanup. Any need to touch a path outside this list stops for an
  amendment naming the path and the reason.

### Engine contract to implement

Every engine resolves the merged config through `kitconfig.load_config()`. Every engine
takes `--mode {live,test} --window-days N --date YYYY-MM-DD`, re-derives the run
identity rather than trusting a caller-supplied one, and refuses on a partial configured
engine set. Each exits `0` on success, `1` on a hard stop (one stderr line naming the
failed check and its remedy) and `2` on a usage error. On success each writes one JSON
envelope to stdout, holding the resolved artifact paths and `run_identity_digest`.

- **Fetch**
  - Preflight covers everything the workflow's "Resolve configuration" section
    validates: the keys, values and relationships, the trusted-source union being
    non-empty, the `state_paths` resolver and `STATE_DIRNAME` match, and non-creating
    path resolution.
  - It then runs the authenticated forge read: repository identity, protected-branch
    head, and a merged-PR search over the exact UTC window with complete pagination.
    Truncation or a failed page is a hard stop.
  - Per PR it collects review objects, `reviewThreads` (with `isResolved`,
    `isOutdated`, path and every comment's author), issue comments, file paths, merge
    revision and tracker references (closing references plus `#N` or URL mentions).
    Every node collection is paged to completion.
  - It writes the full raw bundle atomically, under an identity-checked target.
- **Digest**
  - Reads the raw bundle through `resolve_read_path` and requires an exact identity
    match.
  - Keeps findings only from trusted sources: exact normalised operator logins, and
    configured bots plus their listed aliases only.
  - Normalises severity by the canonical table, preserving the source label. Unmapped
    labels and scales are recorded as the report's limitation input.
  - Applies addressed and citation state, ranks, applies
    `max_findings_prs_per_run`, records the omitted identities and the uncapped
    count, and derives `findings_pr_count`, `single_pass_recommended` and `n_batches`.
  - Writes the digest atomically.
  - A `--verify <digest>` form recomputes all of that independently from the raw
    bundle and exits `1` on any disagreement. It works on an LLM-only digest too.
- **Heartbeat**
  - `start`, `tick --step <name> [--slice i/n]` and
    `complete --reason {complete,error}`. The state file lives at the resolved
    `heartbeat_pattern` and is bound to the run identity digest.
  - `tick` or `complete` without a matching `start` exits `1`, as do a foreign
    identity, a regressing slice counter and any write after `complete`.
  - A failed `complete` exits non-zero, so the workflow can mark the run incomplete.
  - Single writer: a lock file refuses a concurrent invocation rather than losing an
    update.

### Acceptance evidence

Before any implementation write, a requirement-to-file/test ledger in the evidence
namespace maps each of the following to code and a test, including its refusal branch:

- every config-validation invariant;
- every target-safety refusal (absolute path, `..`, symlink escape, hardlink alias,
  non-regular target, tracked target, control input, collision, foreign or unreadable
  identity);
- each identity field;
- each severity mapping row;
- the ranking tie-breakers;
- the cap and batching formulas;
- the addressed tri-state;
- every heartbeat transition.

The tests must show:

- real subprocess invocation of all three entry points, with exit status asserted,
  against a fake `gh` on `PATH`, in a temporary repository with `DEVKIT_STATE_ROOT`
  set;
- partial-set refusal from each entry point;
- fetch pagination to completion, and refusal on a truncated or failed page;
- `--verify` rejecting a tampered digest `prs[]`, cap disclosure and each derived
  field;
- sandbox-versus-production read selection in both directions;
- a heartbeat start → tick → complete sequence, plus each refusal.

Synthetic fixtures prove engine behaviour only. They are not a live-window route, and
D-SYSTEMIZE-LIVE stays a separate package.

### Verification and delivery

- Run `make test` on the branch with an extended timeout. Stamp the result with the
  command, the directory it ran in, the candidate sha and the date. Keep failures, skips
  and the #561 syntax-check limitation explicit.
- Run a disposable installed-engine check through `init.sh` or the manifest install path
  in a scratch clone, because the install surface changes.
- Open a ready PR, run `pr-watch --assert-ready`, then follow it to green and review-clean
  with the configured bot plus the fallback lenses (adversarial and correctness) on the
  exact candidate.
- The outcome is a reviewed candidate. Merge, installation into a field checkout, a
  live or test systemize run, scheduler wiring and every external write each need
  their own approval.

**Stops:** unexplained source, config or ref drift; a necessary edit outside the
allowlist; a contract ambiguity that would weaken the shared declaration; a failed
required verification; or a new actionable finding outside scope. On any of these, keep
the checkpoint and propose a bounded amendment.

**Approval wording:** "I approve PHASE5-D-SYSTEMIZE-ENGINE-01 as scoped, through a
ready, verified and reviewed kit PR, without merge or live systemize writes."
