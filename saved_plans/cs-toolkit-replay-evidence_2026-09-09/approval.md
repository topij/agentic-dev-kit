# REPLAY-01 — cs-toolkit replay decision

Status: proposed; adopter writes are not authorized yet.

## Bound inputs

Read on 2026-09-09 using `gh api repos/<owner>/<repo>/branches/main`, `git rev-parse HEAD`, `git symbolic-ref --short -q HEAD`, `git status --short`, `git remote get-url origin`, and a JSON read of the adopter manifest.

- REPO: `/Users/topi/Coding/in-parallel/cs-toolkit`
- KIT: `/private/tmp/agentic-dev-kit` (fresh kit clone; the existing fixture trees were not recreated).
- Approved origin to require: `https://github.com/in-parallel-oy/cs-toolkit.git`
- Adopter main / input: `bdeaf04f1ceed92570ddcd22281b659d5eb5cc80`
- Installed kit baseline: `bde4c234eaa9005e90b987007101aba98281ce88`
- Kit source / protected main: `e698ec47d6284ccd31af5ba9d8bc5657fe992310`

The status commands printed no changes at those revisions on that date. The source workflow's destination hash matched the workflow read in the cockpit. Before writing, recheck the origin, source, input revision, branch, status and file hashes; changed inputs require a revised decision.

## Proposed upgrade writes

Branch from the bound adopter input as `chore/kit-upgrade-replay-20260909`. Follow the source clone's shared Upgrade workflow. Assert the physical working directory before each write sequence, use absolute REPO/KIT paths, and hash at the destination after copies.

Refresh these untouched installed files from the source clone, identified as `stale` by the command retained in `source-doctor.txt`:

- `init.sh`
- `scripts/devkit/kit_doctor.py`
- `scripts/devkit/tests/conftest.py`
- `docs/agentic-dev-kit/workflows/parallel-headless.md`
- `docs/agentic-dev-kit/workflows/adopt.md`
- `docs/agentic-dev-kit/runtime-parity.md`
- `docs/agentic-dev-kit/fallback-review-panel.md`

Run the refreshed `"$REPO/init.sh" --no-clobber` from REPO, accepting existing prompt values and inspecting its config, ignore-file and hook effects. Preserve the recorded template and hook declines. Re-run the source doctor after refreshes; install a newly proven required dependency if the workflow requires it. Stop and present any unexpected authored-file change or policy decision.

Proposed explicit decisions for newly offered paths: **decline**:

- `scripts/devkit/tests/test_pre_push_hook.py` — its kit pre-push hook is already declined.
- `scripts/devkit/tests/fixtures/shipped-registrations/codex-hooks.json` — its consuming test modules are declined; CHANGELOG #705 explicitly supports declining the fixture.
- `scripts/devkit/tests/fixtures/shipped-registrations/claude-settings.json` — same declared test-surface boundary.

Record the resulting install and these decisions in `kit-manifest.json` using `--record-install --from-kit "$KIT"`. Existing adopter-owned policy, root lane forks, registrations, generated bindings and lens definitions are preserved by the upgrade scope. The initial adapter read-back is retained in `adapter-and-range.txt`.

## Separate fork reconciliation

Compare the kit baseline-to-source changes for `scripts/dev_session.sh` and `scripts/reconcile_sessions.sh`, and review the adopter forks plus `docs/developer/devkit-workflows-local.md`, `docs/developer/parallel-local.md`, and their Claude/Codex bindings against the refreshed shared doctrine.

The initial `git diff --stat bde4c234eaa9005e90b987007101aba98281ce88 e698ec47d6284ccd31af5ba9d8bc5657fe992310 -- scripts/dev_session.sh scripts/reconcile_sessions.sh` printed nothing from KIT on 2026-09-09. That is a preflight observation, not a completed no-change stage.

If reconciliation needs no change, retain its exact invocation and successful output, input/output SHA equality, tree equality, empty status and linkage to the upgrade output. Do not create an empty PR. If it needs a diff, prepare the focused reconciliation preserving operator-only merge policy and both state-root namespaces; obey the adopter's sequential PR rule and present any new policy choice before applying it.

## Verification and publication

After approved writes, run Upgrade Step 5 against the resulting adopter, its installed-test runner with an isolated state root, its document-budget command, and adopter `make test`. Run required adopter root checks and relevant pre-commit checks. Retain terminal outputs and actual exit statuses; no tests were run during this read-only adopter preflight.

Build the plan's evidence matrix from the upstream fork diff and actual reconciliation diff, mapping hunks to exact passing test nodes or independently reviewed not-applicable dispositions. Include the adapter report and binding assessment.

Bind every created PR's identity, base name and head. Prove protected → upgrade → reconciliation ancestry as applicable. Capture the complete authoritative tuple, verify the immutable revisions and adopter condition, capture again, and require byte-identical snapshots. Movement of a bound ref before the final read-back invalidates the evidence.

Open completed work ready for review, run `pr-watch --assert-ready`, finish review follow-through, and record each round's review receipt before that round's fixes. Merge authority remains with the operator. Publish both snapshots and the stamped verification result on the ordinary kit wrap-up PR before merge; fold the full #722 batch into that wrap-up.

Item 5 remains blocked by the missing original fixture/source trees. This proposal does not rebuild them, repeat credited field exercises, implement #585, authorize tracker writes, or by itself establish the entire Phase 5 exit.

## Exact requested decision

Approve REPLAY-01: the upgrade writes and explicit declines above, the separately evaluated fork reconciliation, required validation, ready PR creation and review follow-through, and retained replay evidence. Adopter merges retain separate exact authority.


## Subsequent exact decision — 2026-09-09

Operator decision in this Codex session, 2026-09-09:
Approve REPLAY-01 as written, including its explicit declines and ready-PR review follow-through, with merges remaining operator-held

The approved packet is decision.md, SHA-256 f58a3044195d21ffa4704943b89859de893f59ad7da9a3531b223eabea3f8fe1.
Its pre-approval status text is retained as the proposal that received this decision.


## Accepted review limitation — 2026-09-09

2026-09-09 — exact issue payload and unchanged-byte deferral approved in the current session.
Operator answer: Approve filing and deferral
Title: is_install_baseline must reject non-object manifest JSON
Repository: topij/agentic-dev-kit
Labels: bug, P3, test
Body SHA256: bbd40d80eb3b66f142c21c21eb3a55c963737532ee5d6830525859f10339622b


At kit source e698ec47d6284ccd31af5ba9d8bc5657fe992310, scripts/tests/conftest.py uses membership directly on json.loads output. The replay probe imported the corresponding cs-toolkit helper at 21fe33bb040e7fdcc8f7d3d7c4402e768b1ff351 on 2026-09-09: null and numeric JSON raised TypeError; a matching string or list returned True. Require a dict before testing kit_commit, and cover these forms in the helper tests. The approved adopter installation has no test-module callers of this helper. Finding: https://github.com/in-parallel-oy/cs-toolkit/pull/2255#discussion_r3971657369. Preserve the replay’s pinned source and record this accepted limitation; implementation remains separate.

Filed and authoritatively read back as https://github.com/topij/agentic-dev-kit/issues/723.
