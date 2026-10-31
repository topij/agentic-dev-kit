## session_cleanup.py: a round whose scratch root is gone too retires as `absent`

CHANGED: `preview`, `apply` and their `--round` forms used to refuse with `review
round root unavailable: absent` when a round's path was gone and its scratch root
had been removed too, and with `allocation root identity changed` when the root was
present with another identity (for example recreated by another session). They now
report that round as `absent` (reason `round and its scratch root are both gone`, or
`round is gone and its scratch root's identity no longer matches`), and `apply`
records it `removed` with an `unverified` mark, so the inventory can complete.
Nothing is deleted. The root must still be an expanded `scratch.roots` entry, and for
these rounds any inspection error other than a missing path now refuses, which is
stricter than before.

CHANGED: `retire-evidence` keeps the evidence of a round marked `unverified`, and of a
round marked by `reconcile`, with the reason `its round was recorded removed without
a verified removal`, until its bytes are named with `--include`. Its data may still
exist on a moved root or an unmounted volume, so confirm that before including it.

An inventory left incomplete this way needs no action beyond running `preview` and
`apply` again under the usual authorization.
