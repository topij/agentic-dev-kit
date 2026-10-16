Before computing proposal digests, classify each proposed ticket and include its
execution-environment section and configured label according to
[`ticket-execution-environment.md`](../ticket-execution-environment.md). Apply this
in engine-backed and LLM-only drafting; the author supplies the metadata, and the
engine's exact-payload binding preserves it without independently verifying the
classification. Never add it after approval or rewrite retained proposals on resume.

Build the idempotency marker without a recursive digest. First canonicalize
`{title, body_without_marker, project, labels}` and hash it as `payload_core_digest`.
The non-rendering marker binds session id, candidate id, and that core digest. Append the
marker to the body, then canonicalize the final `{title, body, project, labels}` and hash
it separately as `payload_digest`. State and report store both digests; exact-payload
approval binds the final digest, and marker read-back uses the core digest before
requiring the complete final payload to match. The marker is therefore part of the exact
payload the operator reviews without attempting to hash a digest into itself. In
engine-backed mode invoke `triage.draft_engine`; in LLM-only mode draft with the
configured analysis tier and record `agent-executed`.

