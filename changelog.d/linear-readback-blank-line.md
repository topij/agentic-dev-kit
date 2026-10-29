## Triage read-back: an empty line Linear adds before a list no longer holds the run

CHANGED (gate semantics): a tracker read-back that differs from the approved payload
only by one empty line between a line of text (a paragraph, heading, quote or ordered
item: any line with non-space content that is not an unordered-list item or fenced code) and the unordered-list item
under it, outside fenced code, now verifies instead of holding the operation as `ambiguous`
(#1291). Linear's editor inserts that line, so every approved payload with a
paragraph followed directly by a list was created and then held at `reconciliation`.
Two empty lines, an empty line before anything other than a list item, a
whitespace-only line and a fence delimiter on either side still leave the attempt
ambiguous; bullet-marker spelling is relaxed as before.

Refresh `scripts/lib/triage/model.py` with
`docs/agentic-dev-kit/workflows/triage-friction-log/state-schema.md` and
`scripts/tests/test_triage_providers.py`. Change nothing in `config/dev-model.yaml`
while a run is held: the run is bound to the configuration's fingerprint. A run held
for this difference alone verifies the existing issue by its marker on the next
`resume --enable-tracker`, with no second create and no new approval.
