## Bind scheduled triage outcomes to individual engine calls

Refresh the triage CLI, finalize entry, `lib/triage/outcome.py`, and the shared
triage engine CLI reference together. Scheduled callers can request a durable
receipt with `--outcome-receipt` and `--invocation-id`, then classify it with
`--check-outcome-receipt` and explicit expected entry, context and mode.

Allocate a fresh id and private destination before every engine CLI call, including
retries. Receipts are published once; existing files are never cleared or replaced.
Require the process exit and the checked outcome, and distinguish waiting from
completion. If an agent makes repeated calls, instrument each call in the scheduler;
exporting a shared id around the whole agent run does not satisfy this contract.
Existing CLI exit semantics and triage approval bindings are unchanged.
