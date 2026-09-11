# ITEM5-B-UPDATE-03 — approved retained execution

The operator answered the [packet](phase5-item5-b-update03-decision_2026-09-11.md)
in the current Codex task: **“Approve ITEM5-B-UPDATE-03 as scoped above”**.
The embedded `authority.json` retains that exact response, the exact question and
the packet digest, ledger SHA-256
`141408cc180def2dd1bb3c1dc448f16b2b45a486dc083afeb184b7e2e71937f1`, and binding
SHA-256 `51283931d2a48285d37e8de18236f0c15420a6fe1c02ef58172f7657809a9421`.
That approval was consumed by this attempt. The prepared packet and its unapproved
binding are preserved historical inputs; they were not rewritten as execution evidence.
UPDATE-01 remains consumed and UPDATE-02 remains historical and unanswered.

The [embedded records](phase5-item5-b-update03-execution-evidence_2026-09-12/records.json.gz)
retain original bytes as base64 with per-file SHA-256, including the approval,
act-time validation, forge readbacks, execution driver, before/final inventories,
baseline, command arguments, environments, timings and complete output. The
[assessment](phase5-item5-b-update03-execution-evidence_2026-09-12/execution-assessment.json)
and [retention index](phase5-item5-b-update03-execution-evidence_2026-09-12/retention.json)
identify the result and external backups. These programs record this completed attempt;
they are not a reusable update authorization or a current-state proposal validator.
The historical assessment field `installed_skip_scope_unchanged` records equality
of normalized grouped pytest summaries. It cannot establish which individual
test nodes skipped.

## Applied scope

The r5 validator invoked the committed r4 audit with Python optimization disabled
before execution, from `/Users/topi/Coding/agentic-dev-kit` at
`955c6b4be4c869f1f16d43b29457ce4140cb492b` on 2026-09-11. It returned
`prepared-inputs-and-program-binding-verified; proposal-only`. The separate
`gh api` / `gh pr view` readback in `forge-before.json` matched the post-acceptance
fixture identity, PR tuple, file list and original complete review-receipt body hashes.
The original temporary paths remained absent; neither was reconstructed.

Verified non-Git byte archives and Git bundles were created before retained changes.
The detached source at `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source` advanced from
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac` to `7e0232ed871b37a315c5509c97b83d3b00b1a3fd`.
The execution driver's `source` and `final` stages compared its complete checkout
delta with the approved ledger, every tracked destination with its Git blob, and
release-manifest entries with their hashes. Their full reports retain the observed
directories, revisions, dates and commands.

The fixture at `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture`
received only the ledger's workflow, conftest, initializer/portability/state-guard
test payloads and generated install baseline. The baseline recorder's actual bytes
matched the predicted payload. The local branch `chore/item5-b-update-7e0232e`
was committed as `4ad91c875377d8607082cd0a125ba801218187ed` before suites ran. Existing fixture refs,
including `chore/item5-b-field-exit`, were preserved. No fixture push occurred.

## Verification observations — 2026-09-11 (UTC)

Every command below ran through the committed r4 command runner, with the packet's
Git configuration isolation. Role-specific state, tool caches, virtual environments,
pytest caches and temporary paths were under `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/update-7e0232e-20260911`.
Python optimization was disabled and bytecode writes were disabled. Suites ran
serially to terminal summaries, without changing their selection after results.

| Command and working directory | Revision | Actual result |
|---|---|---|
| Installed `kit_doctor.py --root "$REPO" --manifest "$KIT/kit-manifest.json" --json`; `$REPO` above | `4ad91c875377d8607082cd0a125ba801218187ed` | Exit `0`; installed bytes matched and baseline was trusted. Full report retained. |
| Source `kit_doctor.py --root "$REPO" --adapter-report --adapter-source "$KIT" --json`; `$REPO` | `4ad91c875377d8607082cd0a125ba801218187ed`, source `7e0232ed871b37a315c5509c97b83d3b00b1a3fd` | Exit `0`; custom Codex wrap-up remained `adopter-owned`. Rendered-form comparison normalizes newlines; this is not client execution. |
| Installed `check_doc_budget.py`; `$REPO` | `4ad91c875377d8607082cd0a125ba801218187ed` | Exit `0`; full configured-path report retained. No archival workflow ran in the fixture. |
| `uv run --with pytest --with pyyaml python -B "$REPO/scripts/devkit/run_installed_tests.py" --root "$REPO"`; `$REPO` | `4ad91c875377d8607082cd0a125ba801218187ed` | `2161 passed, 128 skipped in 539.42s (0:08:59)`; runner exit `0`. Grouped skip summaries matched the earlier installed log. |
| `make test`; `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/update-7e0232e-20260911/source-verification` | `7e0232ed871b37a315c5509c97b83d3b00b1a3fd` | `1 failed, 2529 passed, 1 skipped in 540.33s (0:09:00)`. Make exited `2`; the command runner returned `1`. |
| Separate `bash -n` for `scripts/dev_session.sh`, `scripts/reconcile_sessions.sh`, `scripts/lib/repo_root.sh`, `scripts/hooks/pre-push`, and `sh -n init.sh`; the same source clone | `7e0232ed871b37a315c5509c97b83d3b00b1a3fd` | Each exited `0`. These parse observations cover #561's recipe gap; they do not repair it or execute shell behavior. |

The source failure was the disclosed #393 deep-JSON hook-output assertion; its actual
traceback and failed node remain in the unmodified output. The installed result does
not turn that source run into a passing suite. The fixture has no project Makefile,
and no fixture `make test` result is claimed.

The final checks compared all preserved fixture paths, complete tracked/merged typed
configuration, the recorded baseline, retained source bytes, Git identity, existing
refs, hooks/config and item 6 replay hashes. Administrative deltas are enumerated in
the assessment. Rollback was not performed; verified backups and the local attempt
remain available under the retention index. The final forge readback is retained
alongside the pre-execution readback.

## Limits and next decision

The accepted inherited **special-file-root limitation remains**: a FIFO state root
can escape the inherited snapshot and obstruct state persistence. No detection or
recovery for it is supplied or claimed. The inherited inventories omit supplied
root and `.git` root modes and timestamps; checkpoint equality does not exclude
transient intervening writes.

ACCEPT-01 is ownership acceptance only. Preserving the custom wrap-up does not make
its `Preserve this adapter.` body functional. Installed verification, client
functionality and field-exit completion remain separate. Generic-upgrade bootstrap
follow-ups preserved in the packet remain outside this execution; no source repair
or new approved deferral is claimed.

Fixture publication, PR continuation/closure/merge, generic upgrade, initialization,
client/trust/profile exercises, settings changes and tracker payloads were excluded.
The existing fixture PR's body and CI still name the earlier source, so its historical
hosted result is not verification of this local attempt. Fixture merge remains excluded.

Phase 5 item 5 remains incomplete. Item 6 and its replay evidence are preserved,
without repeat or new credit for cs-toolkit #2222/#2223/#2255. #723 remains the approved
upstream deferral; #585 stays earlier outside Phase 6; #724 delivered #722.
The friction sweep remains parked.

**Next:** revalidate against this attempt's final checkpoints and prepare the separate
exact fixture PR continuation decision, including CI/body/publication/review scope.
Do not run the consumed proposal validator as a current-state equality check.
Any remaining field-exit work retains its own scope decision.
