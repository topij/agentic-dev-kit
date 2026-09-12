# ITEM5-B-PR-02 execution — 2026-09-13

The operator replied `Approve ITEM5-B-PR-02 as scoped` to the
[r2 packet](phase5-item5-b-pr02-decision_2026-09-12.md). Its ledger
`35bcfee00567831223c37c10d3f6ebec86cd826ea4572009cc20a816193aaf4c`
and binding `6dde63401a2d4dd451ee94f07a962e63caebdd54b0115fb9e477fab84896fa27`
remain unchanged historical preparation artifacts. The approval was consumed by
the attempt below. Kit [#737](https://github.com/topij/agentic-dev-kit/pull/737)
delivered the packet as `083bccbfa4c4b066d82e7625ddf1efe70716dd2d`, from reviewed
head `ebf03f8c9598d38d00c1a55bb49c07d0bf179238`; its
[delivery checkpoint](https://github.com/topij/agentic-dev-kit/pull/737#issuecomment-5645343460)
was read back before execution. No earlier packet or closeout was reopened.

## Applied scope

The supplied CI workflow was committed on local branch `chore/item5-b-pr02-7e0232e`
as `12d7d4b41abe75451ed74d7cbc068bc6b8be2db7`. Its content hash is
`0b2e8bdda56a34856518d12d65d27ca9ac6fb7be3e48e798dcf83940d5c337dc`.
The ordinary non-forced push advanced the existing private
[fixture PR #1](https://github.com/topij/adk-item5-b-field-20260909/pull/1)
head `chore/item5-b-field-exit`; the original local branch was preserved.
The exact approved title and body were published after the push readback.

The immediate PR read after the successful push returned the earlier head.
Execution stopped before the title/body edit; fresh PR and remote-ref reads
confirmed the candidate before continuation. The push was not repeated.
No baseline refresh, retained-source change, configuration change or initialization
was performed. The baseline remains
`e02fda03c4119b0deb9cba6fbf37818831f3244c9f3fc1e8b37fd79e9768291b`.

## Verification

The execution root is
`/Users/topi/Coding/adk-field-exercises/item5-b-20260909/pr02-7e0232e-20260912`
(`OUT`). The retained fixture is its sibling `fixture` (`REPO`), and retained
source is sibling `kit-source` (`KIT`), detached at
`7e0232ed871b37a315c5509c97b83d3b00b1a3fd`. The committed PR-02 command runner
provided Git configuration isolation and administrative checks. Commands used
unoptimized Python with bytecode disabled and generated state/caches outside
the retained trees. Full local commands, outputs, environments and timestamps stay
under `OUT`; the evidence index below binds the retained files.

On 2026-09-12 UTC, at fixture `12d7d4b41abe75451ed74d7cbc068bc6b8be2db7`, from
`/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture`:

- `uv run --with pytest --with pyyaml python -B scripts/devkit/run_installed_tests.py --root "$REPO"`
  printed `2161 passed, 128 skipped in 402.23s (0:06:42)` and exited successfully.
- The installed doctor, pinned-source adapter report and document-budget commands
  exited successfully; command metadata and full reports remain in `OUT`.

From `OUT/source-verification`, independently cloned at source
`7e0232ed871b37a315c5509c97b83d3b00b1a3fd`, on 2026-09-12 UTC, `make test`
printed `1 failed, 2529 passed, 1 skipped in 421.76s (0:07:01)`.
The failure was `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`,
the disclosed #393 limitation. This was not a passing source suite.
Separate `bash -n` invocations for `scripts/dev_session.sh`,
`scripts/reconcile_sessions.sh`, `scripts/lib/repo_root.sh`, `scripts/hooks/pre-push`,
and `sh -n init.sh` exited successfully in that directory/revision/date, accounting
for #561's grouped syntax-check gap without claiming to repair it.

`gh run view 34717806769` from the retained fixture at the fixture SHA above on
2026-09-12 UTC confirmed the
[hosted run](https://github.com/topij/adk-item5-b-field-20260909/actions/runs/34717806769)
succeeded. Its complete log records installed `2158 passed, 131 skipped in 213.61s`
and source `2528 passed, 3 skipped in 244.80s`. The hosted Python 3.12 environment
and local Python 3.14 environment have different skip coverage. Grouped historical
skip equality does not establish identical skipped nodes; skipped assertions are
not passing assertions.

## Review and handoff

The correctness review completed at fixture `12d7d4b41abe75451ed74d7cbc068bc6b8be2db7`.
It reported P3/Low coverage-claim imprecision in `scripts/devkit/tests/test_panel_prompt.py`:
the path-equality assertion does not observe the dependency declaration it claims
to protect. Its scoped mutation survived while dependent tests skipped. The lens
did not establish a production-behavior regression or complete-mutant-suite survival.
The complete report and mutation/restoration evidence stay local; no fix or tracker
write was made. Its exact scope decision remains pending. The
[review handoff](https://github.com/topij/adk-item5-b-field-20260909/pull/1#issuecomment-5649128514)
preserves the finding and reconciles the earlier delivered detector and wording
repairs. The installed comment-posting function published that summary without
recording a clean-review gate receipt or acknowledging the pending finding.

Automatic approval review initially refused the adversarial launch because the
private source/diff and review context would reach an external model service.
The operator subsequently answered `Yes, please send it` to the explicit question
authorizing that payload to OpenAI's Codex service for the remaining adversarial
review. This permission does not authorize public raw-report publication or fixture
merge. `codex exec -c model_reasoning_effort=high` for each independent lens
was read back from its actual rollout as OpenAI `gpt-6-astra` with effort `high`;
the [scoped evidence index](phase5-item5-b-pr02-execution-evidence_2026-09-13/index.json)
retains the launch argv, actual runtime fields and report hashes.

The adversarial report completed on 2026-09-13 local date at fixture
`12d7d4b41abe75451ed74d7cbc068bc6b8be2db7` with no new actionable findings.
Its full report records the complete installed runner, behavioral mutation failures
and byte-equal restorations. Its probes reproduced the documented shutdown-time
observation limit, without establishing a shipped late write or bypass of the
workflow's separate Git-status check. The initial host-executable assumption failed
before doctor launch; the reviewer retained it, used `python3` and reacquired the
verification lock. Complete reports were read before this disposition.

The resume audit `env -u PYTHONOPTIMIZE python3 -B /private/tmp/item5b-pr02-execution-20260912/resume-disclosure.py`
from `/Users/topi/Coding/agentic-dev-kit` at
`083bccbfa4c4b066d82e7625ddf1efe70716dd2d` on 2026-09-13 local date matched the
saved paused inventories and administration before dependent Git/config reads.
Fresh `forge-r2.py resume-disclosure-forge published` readbacks matched the paused
complete forge tuple. The consumed pre-attempt equality entry point was not reused.

The accepted inherited special-file-root limitation remains: a FIFO state root can
escape the inherited snapshot and obstruct persistence. Root and `.git` root modes
and timestamps are omitted; endpoint equality does not exclude transient writes.
Ownership acceptance of the preserved custom wrap-up is not functionality, client
loading/trust/hook verification, adoption completion or field exit.

Phase 5 item 5 remains incomplete. Item 6/replay and cs-toolkit #2222/#2223/#2255
retain their existing credit. #723 stays the approved upstream deferral; #585 stays
earlier and outside Phase 6; #724 delivered #722. UPDATE-01 and UPDATE-03 are consumed;
UPDATE-02 remains historical and unanswered. The original missing paths were not
reconstructed. The friction sweep stays parked. Additional fixture fixes, remaining
field routes, tracker payloads, fixture closure and fixture merge require separate
scope; this record grants none of them.


## Retained final checkpoint

`env -u PYTHONOPTIMIZE python3 -B /private/tmp/item5b-pr02-execution-20260912/finish-fixture.py`
from `/Users/topi/Coding/agentic-dev-kit` at
`083bccbfa4c4b066d82e7625ddf1efe70716dd2d` with these scoped record edits,
on 2026-09-13 local date, verified equal complete forge tuples and retained
inventories matching the paused checkpoint. Its installed
`pr_watch.py 1 --json --no-persist` reads left local watch state unchanged and
reported the fixture head with hosted checks green, `converged: false`,
`mergeable: false`, and no valid independent-review gate receipt. The full review
reports are complete; the correctness finding is unresolved.

Final retained checkpoint: `OUT/retained-review-final.json`, SHA-256
`98250efb1ac3ff08a8e64153cae048120cf34607ed4fe3a02fad0e864bb7d827`.
The complete local archive is
`/Users/topi/Coding/agentic-dev-kit/state/review-evidence/item5-b-pr02-execution-20260912/completed-execution.json.gz`,
SHA-256 `d5ad0f284134157eb66005a3a93034d866f9eafceabe0be993394c4b72852d0a`.
The index binds commands, checkpoints, actual compute, reports and the posted
summary. Full new private logs/reports are retained locally, not published in this
record; the index does not promote them as a public reproducible capability bundle.
The original local evidence roots and earlier pause archives remain preserved.

**Next:** read this checkpoint and the pending correctness report, revalidate the
retained trees read-only with the committed inventory/configuration-isolation
helpers, then prepare the exact scope decision for that finding. Do not replay a
consumed pre-attempt equality entry point, repeat the completed panel, or execute
an additional retained update without its separate decision.
