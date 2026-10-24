# Troubleshooting

Start with the observed symptom, then keep the evidence named in its row before
retrying. Commands assume the kit's `paths.engines: scripts`; adopters substitute
their configured engine directory. Run installation checks in the repository being
inspected. Workflow names are agent invocations, not shell commands.

| Symptom or report | Owning command or workflow | Evidence to keep | Next action and authority boundary |
| --- | --- | --- | --- |
| `Failed to spawn: pytest` or `No module named pytest` | `make test` | Attempted command, working directory and terminal output | Run `make test`, which supplies the test dependencies. Allow time for the terminal summary; a truncated run is not verification. See [verification](../AGENTS.md#verification). |
| `differs`, `locally-edited` or `stale-and-edited` | `uv run scripts/kit_doctor.py` | Doctor report, installed baseline and local diff | Inspect the diff through [upgrade](agentic-dev-kit/workflows/upgrade.md). A hash mismatch alone does not authorize replacement or classify an edit. |
| Adapter reports `adopter-owned` or `baseline unavailable` | `upgrade` installation inspection | Adapter bytes, baseline commit and history lookup result | Preserve authored content; inspect the historical baseline or use the workflow's explicit ownership decision. Do not overwrite an unclassified adapter. |
| Explicit reviewer model pin has a cache warning | `uv run scripts/kit_doctor.py` | Exact configured model and cache observation | Confirm availability in the invoking client before deliberately changing compute. The cache report is advisory; it does not authorize an automatic model upgrade. See [installation diagnosis](developer-guide.md#diagnose-an-installation). |
| `converged: true` but `mergeable: false` | `uv run scripts/pr_watch.py <PR> --json` | Exact repository, PR head, `merge_blockers`, `review_evidence`, read gaps | Follow each blocker in the [report reference](agentic-dev-kit/workflows/pr-watch/report-fields.md). Review completion and actor merge authority remain separate. |
| Reviewer skipped or unavailable | `pr-watch` | Full bot status body, current head, pending-review state and computed review class | Follow the [fallback contract](agentic-dev-kit/fallback-review-panel.md). Check existing head coverage before launching reviewers; an outage is not a waiver. |
| `review_rounds.spent` with findings left | `pr-watch` | Reviewed heads, unresolved findings, dispositions and proposed repair scope | Post the workflow's decision packet and hold for the operator. A spent budget does not permit an extra fix round or merging past findings. See [stop conditions](agentic-dev-kit/workflows/pr-watch.md#stop-conditions). |
| `mergeable: true` but no authority to merge | Project merge policy / lane cockpit | Exact head, current poll and request authority | Hold for the authorized actor. A lane never merges itself; use its [cockpit route](agentic-dev-kit/workflows/parallel.md). |
| Lane launch or activation refuses | `scripts/dev_session.sh` / `scripts/launch_lane.py` | Exact command, scope, descriptor/receipt if produced, and refusal output | Resume through the [parallel workflow](agentic-dev-kit/workflows/parallel.md); do not invent launch receipts or repair authority fields by hand. |
| Shared hook install is reported instead of performed | `init.sh` in a linked worktree | Checkout identity and installer output | Follow the [upgrade workflow's hook step](agentic-dev-kit/workflows/upgrade.md). Shared Git administration requires the deliberate install route, not another bare installer retry. |
| Document budget warning | `uv run scripts/check_doc_budget.py` | File and configured budget named by the report | Route the record through its owning workflow. For an instruction file such as `AGENTS.md`, consolidate as the remedy says rather than raising the budget. A warning does not authorize archival, tracker filing or deletion. |
| Cleanup says `kept`, `active` or `unavailable` | `uv run scripts/session_cleanup.py preview <session>` | Session id, retained-evidence index, exact paths and keep reasons | Preserve the inventory and follow [cleanup recovery](agentic-dev-kit/session-cleanup.md). End writers and resolve the cause; do not broaden sweep roots or remove guards. A preview token is not consent. |
| Cleanup returns `archive-with-runtime` | `session_cleanup.py apply` | Approved scope and exact app-managed worktree identity | Use native archive under the same authorization, then re-run apply from outside disposable paths. Queued archive is not completed cleanup. See [cleanup](agentic-dev-kit/session-cleanup.md). |

For an unavailable forge or tracker, retain the exact error and resume through the
owning workflow after access returns. Unavailable data is not an empty list, and an
ambiguous external write needs read-back before retrying. Avoid copying credentials
into reports. The [developer guide](developer-guide.md) supplies the normal path;
this page points back to contracts rather than overriding their refusal rules.
