### Tracker route

Construct the proposed title, description, project, and labels from `<tracker>` and the
cluster evidence. Include the execution-environment section and configured label under
[`ticket-execution-environment.md`](../ticket-execution-environment.md) before
computing payload digests; retained approved proposals are not rewritten on resume.
Then append the idempotency marker under *External dispatch records*, and
record the proposal before presenting it. Show that exact payload to the operator,
marker included. Create or modify nothing
unless the operator explicitly confirms that payload. Configuration, a scheduler launch,
a prior approval for another payload, and tracker availability are not confirmation.

In a non-interactive run with no prior payload-specific approval, take the flagged
friction-log route and report `approval unavailable`; never pause. In an interactive run,
decline or silence takes the same route. An approved write follows the dispatch order
under *External dispatch records*. If it fails, preserve the payload and failure in the
report and do not claim an identifier.

