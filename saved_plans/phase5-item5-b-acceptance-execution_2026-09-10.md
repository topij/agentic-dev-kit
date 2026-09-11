# ITEM5-B acceptance and fixture PR execution

The operator approved `ITEM5-B-ACCEPT-01 as scoped` and `ITEM5-B-PR-01 as scoped`
on 2026-09-10. The [decision packet](phase5-item5-b-acceptance-decision_2026-09-10.md#operator-disposition--2026-09-10)
retains the exact response, original packet and payload-ledger hashes, and fresh
pre-write audit binding. This record owns the subsequent execution checkpoint.
Fixture merge is excluded. Phase 5 item 5 remains incomplete.

## Bound inputs and acceptance

```sh
COCKPIT=/Users/topi/Coding/agentic-dev-kit
REPO=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture
KIT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source
OUT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910
```

The approved fixture input was `413132b01d14c735d94753231bf325904135285f`.
The retained source pin is `60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`.
The baseline SHA-256 is
`9e2196df3b7239b599819abcfc20271b0389b70f78f22837a0709575145b9126`.

The [PR #729 readback](phase5-item5-b-acceptance-execution-evidence_2026-09-10/pr729-readback.json)
binds merge `914c2e4ef06a33d88ae7c94a823d3262a9526278`, reviewed head
`119283e2d8a4add1e4a3d7f1cc944ddd07e85f99`, their equal Git tree objects and the
[final review](https://github.com/topij/agentic-dev-kit/pull/729#issuecomment-5619727368)
and [retained-tree checkpoint](https://github.com/topij/agentic-dev-kit/pull/729#issuecomment-5619798749).
It retains exact commands, directory, revision and observation time.

The current acceptance audit ran with `python3 -B` and Python optimization unset in
`$COCKPIT` at `914c2e4ef06a33d88ae7c94a823d3262a9526278` on 2026-09-10.
Its [raw output](phase5-item5-b-acceptance-execution-evidence_2026-09-10/acceptance-audit.json)
reports equality to UPDATE FINAL. It checked the original paths as absent without
reconstructing them:

- `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`
- `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`

ACCEPT-01 accepts the packet's named ownership and preservation outcomes against
that audit's hashes, modes and full typed tracked/merged configuration. The custom
`.agents/skills/wrap-up/SKILL.md` remains an ownership collision fixture whose body
is `Preserve this adapter.` This acceptance does not certify a usable wrap-up
workflow, a loaded client configuration, hook trust or a notification route.

## Applied ledger and publication

PR-01 applied the exact approved payloads at their absolute destinations after
asserting the owning directory and verifying the before archive and Git bundle:

| Destination | Applied SHA-256; mode |
|---|---|
| `$REPO/notes/friction.md` | `93dbef2c7b0af697602f4ede9b501387aba0f6a0ce841f2192c8c2f00ef91271`; `0644` |
| `$REPO/.github/workflows/item5-b-installed.yml` | `ae69eae2c8fb65e5cd8b7accdda3e376b1ad7d2fc82276c09ef06e03e105e917`; `0644` |

The workflow's missing `.github` and `.github/workflows` parents were created with
mode `0755`. The staged diff was read before a separate commit command. The resulting
fixture commit is `f770f183bf6691f1f706c676b740cf2ef5ceb766` on
`chore/item5-b-field-exit`. Historical fixture branches were retained.

After local verification, the authenticated owner inventory and exact repository
API absence check preceded creation of private `topij/adk-item5-b-field-20260909`.
The canonical private identity was read back before adding its exact HTTPS origin
and pushing. `main` was created at existing seed
`8533c334637e8776ca7a4fe3a9fd8c6c64e35707`; default-branch and remote head readbacks
preceded the ready PR. No commit was added to `main`.

[Fixture PR #1](https://github.com/topij/adk-item5-b-field-20260909/pull/1) was created
with the supplied title and body, from `chore/item5-b-field-exit` to `main`.
The initial `gh pr view --json files` result was incomplete; the check stopped there.
The complete paginated `pulls/1/files` API response then matched the local seed-to-head
file set. The existing PR was read back; creation was not retried.
`uv run "$REPO/scripts/devkit/pr_watch.py" 1 --assert-ready` in `$REPO` at
`f770f183bf6691f1f706c676b740cf2ef5ceb766` on 2026-09-10 reported already ready.

## Verification and limitations

The command/environment records and complete stdout/stderr logs are retained beside
this record and under `$OUT`. They bind the actual argv, directory, immutable revision,
start/end timestamps and status. Local cache, temporary and state paths were routed
under the approved evidence root with role-specific state/cache locations; Python
optimization was unset and bytecode writes disabled. Suite processes reached their
terminal summaries without a wall-clock kill.

The following observations are from 2026-09-10 at fixture
`f770f183bf6691f1f706c676b740cf2ef5ceb766` and source
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`:

| Command; directory | Actual result |
|---|---|
| `python3 -B "$REPO/scripts/devkit/kit_doctor.py" --root "$REPO" --manifest "$KIT/kit-manifest.json" --json`; `$REPO` | Exit `0`. |
| `python3 -B "$KIT/scripts/kit_doctor.py" --root "$REPO" --adapter-report --adapter-source "$KIT" --json`; `$REPO` | Exit `0`; custom Codex wrap-up classified `adopter-owned`. |
| `python3 -B "$REPO/scripts/devkit/check_doc_budget.py"`; `$REPO` | Exit `0`. |
| `uv run --with pytest --with pyyaml python -B "$REPO/scripts/devkit/run_installed_tests.py" --root "$REPO"`; `$REPO` | `2129 passed, 128 skipped in 466.23s (0:07:46)`, exit `0`. |
| `make test`; `$OUT/source-verification`, an independent clone detached at the source pin | `1 failed, 2497 passed, 1 skipped in 526.82s (0:08:46)`, exit `2`. |
| Separate `bash -n` calls on `scripts/dev_session.sh`, `scripts/reconcile_sessions.sh`, `scripts/lib/repo_root.sh`, `scripts/hooks/pre-push`; `sh -n init.sh`; `$OUT/source-verification` | Each exited `0`, covering the named paths omitted by #561's multi-filename recipe. |

The source traceback is
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`,
the disclosed #393 limitation. It is a failed source run, separate from the passing
installed observation. The installed skip entries match the UPDATE installed log;
kit-source-only and omitted-layout contracts remain unverified by that runner.
The fixture has no Makefile, and no fixture `make test` is claimed.

## Hosted verification and independent review

The [hosted job](https://github.com/topij/adk-item5-b-field-20260909/actions/runs/34505089997/job/102965180333)
completed successfully on 2026-09-10 at fixture head
`f770f183bf6691f1f706c676b740cf2ef5ceb766`. Its [identity and step statuses](phase5-item5-b-acceptance-execution-evidence_2026-09-10/fixture-ci-job.json)
and [complete log](phase5-item5-b-acceptance-execution-evidence_2026-09-10/fixture-ci-job.log)
retain the checkout, pinned source clone, doctor, adapter, budget, installed runner,
source `make test` and separate shell parses.

On that runner, the installed command above ran in
`/home/runner/work/adk-item5-b-field-20260909/adk-item5-b-field-20260909` and printed
`2126 passed, 131 skipped in 201.53s (0:03:21)`. Source `make test` ran in
`/home/runner/work/_temp/item5-b-kit-source` at
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac` and printed
`2496 passed, 3 skipped in 230.28s (0:03:50)`. The hosted skips additionally name
the unavailable locale classification for the nonbreaking-space initializer probes.
They do not match the local platform's coverage. The source log has no #393 failure;
that does not erase the local failure. Setup/install output identifies CPython
`3.12.14`, uv `0.12.12`, pytest `9.1.1` and PyYAML `6.0.3`; local tool/interpreter
readbacks retain their differing versions in the execution result.

The independent adversarial and correctness reviews completed at the fixture head
using `gpt-6-astra`, effort `high`, confirmed by their recorded rollout contexts.
Their complete [adversarial report](phase5-item5-b-acceptance-execution-evidence_2026-09-10/fixture-adversarial-full-report.md)
and [correctness report](phase5-item5-b-acceptance-execution-evidence_2026-09-10/fixture-correctness-full-report.md)
retain placed/reviewed revisions, remote-base checks, independent scratch paths,
terminal commands/results, mutation diffs, restoration and handed-tree attestations.
The [adversarial receipt](https://github.com/topij/adk-item5-b-field-20260909/pull/1#issuecomment-5622780057)
and [correctness receipt](https://github.com/topij/adk-item5-b-field-20260909/pull/1#issuecomment-5622712808)
were posted and read back before preparing a remedy.

The adversarial lens marked the regular-file-at-`state` detector gap P2 and inherited,
not a regression. Its unchanged-guard probe left a regular root file while pytest
exited successfully; the reviewed state-saving path then raised `NotADirectoryError`.
The correctness lens marked the newline-normalized adapter comparison's “byte-identical”
wording P3/imprecision, without a demonstrated behavioral regression. These findings
are separate from #393. The original approved payloads contain neither remedy.

**PR-01 is paused at its inherited review findings.** Its fixture files, commit, private
publication and hosted run were executed; the independent findings remain pending.
No `--record-review fallback:panel` clean-review receipt or handled-round acknowledgment
was issued. The post-review `pr_watch.py 1 --json` poll in `$REPO` at
`f770f183bf6691f1f706c676b740cf2ef5ceb766` on 2026-09-10 reports no valid independent
review receipt and `mergeable: false`. This is not a completed operator handoff.
Fixture PR #1 remains unmerged under the original exclusion.

The [kit-only repair decision](phase5-item5-b-review-repair-decision_2026-09-10.md)
presents hash-bound candidate code/test/wording payloads and a changelog template.
Its focused preparation reproduced the missing detection and exercised the proposed
remedy in a disposable clone. It authorizes no implementation by itself. Neither a
future kit repair nor this record updates the retained fixture or its baseline.

## Kit record verification

`make test` ran in `/private/tmp/item5-b-kit-verification-_lknkru1/repo` at
`914c2e4ef06a33d88ae7c94a823d3262a9526278`, with the record working-tree snapshot
hashed in the [command record](phase5-item5-b-acceptance-execution-evidence_2026-09-10/kit-verification.json),
on 2026-09-10. It printed `1 failed, 2497 passed, 1 skipped in 388.34s (0:06:28)`,
exit `2`; the [complete log](phase5-item5-b-acceptance-execution-evidence_2026-09-10/kit-make-test.stdout.log)
retains the same #393 deep-JSON traceback. Separate shell parses in that command
record each exited `0`. This was a kit verification copy, not retained `$KIT` or
an additional fixture client exercise. Later execution-disposition records have their
own file validation; this run describes the hashed snapshot it actually tested.

## Retention and remaining work

The [retained-state record](phase5-item5-b-acceptance-execution-evidence_2026-09-10/retained-state.json)
and [execution result](phase5-item5-b-acceptance-execution-evidence_2026-09-10/result.json)
bind the final checkpoint commands, revisions and observation times. The forge
[before](phase5-item5-b-acceptance-execution-evidence_2026-09-10/forge-before-exit.json)
and [after](phase5-item5-b-acceptance-execution-evidence_2026-09-10/forge-after-exit.json)
tuples compare repository privacy/identity, base/head, complete changed paths,
check conclusions and the recorded reviews. Their equality freezes the pending
review state; it does not establish a successful fixture handoff.

The verified before byte archive and Git bundle remain under `$OUT`, bound by the
[external retention ledger](phase5-item5-b-acceptance-execution-evidence_2026-09-10/external-sha256.json).
No rollback has been executed. The approved conditional local undo remains in the decision packet;
remote repository/branch deletion, PR closure and fixture merge require a fresh exact
decision. Retained `$KIT`, fixture baseline, local policy, ignored override and
historical update/replay evidence are outside the payload writes. Checkpoint inventory
comparisons establish observed equality of bytes, modes, symlink targets and recorded
Git state; they do not prove the absence of transient writes between observations.

New fixture client loading/trust, functional replacement of the custom wrap-up,
initialization, baseline refresh and user-profile changes were not executed. The
systemize live routing, engine-backed operation, notifications, restart/recovery and
remaining probe branches retain the packet's explicit gaps. Adoption handoff alone
cannot establish Phase 5 field exit.

The [maintained sprint status](codex-parity-plan_2026-08-23.md#sprint-status--reconciled-2026-09-10)
preserves completed item 6 and its replay evidence, cs-toolkit #2222/#2223/#2255,
#723's approved upstream deferral, #585's earlier placement outside Phase 6, and
#724's delivery of the #722 record batch. No repeat or new credit is claimed.
The friction-log sweep remains parked; no tracker payload or new intake was started.

**Next:** follow the [approved kit repair execution](phase5-item5-b-kit-repair-execution_2026-09-10.md)
through its REVIEW-02 execution record's verified #731 merge, then prepare the exact
retained-update decision packet. Retained execution still needs its own exact decision;
keep the systemize field-exit matrix and fixture merge separate.

## Kit record review amendment

The kit record at `d2d32d56e3bdedcd0b32b1210a459f6429e3d6fd` received independent
adversarial and correctness review on 2026-09-10. The complete
[adversarial receipt](https://github.com/topij/agentic-dev-kit/pull/730#issuecomment-5623418113)
and [correctness receipt](https://github.com/topij/agentic-dev-kit/pull/730#issuecomment-5623385214)
were posted and read back before fixes. Their terminal reports retain actual compute,
full `make test` summaries, the disclosed #393 failure, separate shell parses,
behavioral mutation results and restoration/handed-tree evidence.

The adversarial lens reproduced a P2 omission in the new repair plan: its initial
ledger left out the kit release manifest required after changing covered files.
The correctness lens reported no actionable finding. The then-unapproved repair packet
was amended to include the exact release-manifest payload, before/after hashes,
deterministic generation and a failing-before/passing-after self-check. This amended
future kit scope does not authorize any retained fixture/source or baseline write.
The proposal evidence binds the focused preparation; full candidate `make test`
is recorded by the subsequent approved kit repair execution. The fixture's inherited review findings remain
pending under their separate decision boundary.
