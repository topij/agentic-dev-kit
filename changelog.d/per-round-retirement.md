## Per-round retirement in session cleanup

CHANGED: `session_cleanup.py allocate` now refuses while an earlier round in the same
inventory is unretired, and always refuses while an earlier round's retirement was
interrupted. Between review rounds, retire the finished round with
`seal`, `preview` and `apply --round <receipt-id>`. Those keep the inventory open,
as `docs/agentic-dev-kit/session-cleanup.md` (*Retire each round before the next*)
describes. To keep an earlier round on purpose, pass `--keep-previous "<reason>"` to
`allocate`; the round then retires with the inventory. A script that allocates
several rounds into one inventory without retiring them now exits `2` on the second
allocation.

A retired round's recorded status is now `removed` rather than `removing`. A
consumer that reads `session.json` and treats `removing` as finished must also
accept `removed`.

While a round's retirement is interrupted (`removing`), `track-process` refuses with
exit `2`; resume that round's `apply --round` first. An `apply --round` that stops
before removal persists no approval, so preview again for a fresh token. Each round's last apply result is recorded as
`last_result` on that round's entry.
