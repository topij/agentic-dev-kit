## Ticket execution environment

Refresh the shared ticket-writing, session-start and parallel workflows and install
`docs/agentic-dev-kit/ticket-execution-environment.md`. Add an execution-environment
section to new ticket payloads before approval. To index it through tracker labels,
configure `tracker.execution_environment.labels` and provision the matching labels;
existing installs can use the body section alone. Invoke `session-start cloud` in
a cloud session when the runtime does not supply that context. Legacy tickets stay
unknown until their requirements are read; no backlog rewrite is automatic.

When refreshing the portability tests, copy the contract fixture
`scripts/tests/fixtures/ticket-execution-environment-contract.md` with
`scripts/tests/test_portability.py` and its matching `scripts/tests/conftest.py`.

These portability checks pin the reviewed Markdown snapshot, including whitespace
structure. They do not execute an agent selecting work. Review any contract change
before updating its snapshot; refreshing both together bypasses the equality check.
