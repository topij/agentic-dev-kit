## Ticket execution environment

Refresh the shared ticket-writing, session-start and parallel workflows and install
`docs/agentic-dev-kit/ticket-execution-environment.md`. Add an execution-environment
section to new ticket payloads before approval. To index it through tracker labels,
configure `tracker.execution_environment.labels` and provision the matching labels;
existing installs can use the body section alone. Invoke `session-start cloud` in
a cloud session when the runtime does not supply that context. Legacy tickets stay
unknown until their requirements are read; no backlog rewrite is automatic.
