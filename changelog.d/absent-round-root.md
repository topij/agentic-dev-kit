## session_cleanup.py: a round whose scratch root is gone too retires as `absent`

CHANGED: `preview`, `apply` and their `--round` forms used to refuse with `review
round root unavailable: absent` when a round's path was gone and its scratch root
had been removed too, and with `allocation root identity changed` when the root was
present with another identity (for example recreated by another session). They now
report that round as `absent` (reason `round and its scratch root are both gone`, or
`round is gone and its scratch root's identity no longer matches`), and the path
outcome carries `"unverified": true`. `apply` records the round `removed` with an
`unverified` field holding that reason, so the inventory can complete. Nothing is
deleted. The root must still be an expanded `scratch.roots` entry, and for these
rounds any inspection error other than a missing path now refuses, which is
stricter than before. Only the engine's own removal of that round, after its path
returns and passes every check, clears the mark; re-running `apply` while the path
is still gone keeps it.

CHANGED: while any round of an inventory is marked `unverified`, `retire-evidence`
keeps every item of that inventory, whichever seal holds it, until its bytes are
named with `--include`. The round's data may still exist on a moved root or an
unmounted volume, so confirm that before including it. Rounds marked by `reconcile`
hold nothing.

ADDED: `evidence_summary` (on `list`, `preview` and the `retire-evidence` plan)
gains `held` with `items`, `bytes` and `reasons`: the present evidence of an
inventory with a round marked `unverified`, some of which may also be kept for
another reason. A consumer that compares the summary exactly sees the
new key.

An inventory left incomplete by #1278's wedge needs no action beyond running
`preview` and `apply` again under the usual authorization.
