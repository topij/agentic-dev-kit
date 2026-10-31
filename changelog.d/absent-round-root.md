## session_cleanup.py: a round whose scratch root is gone too retires as `absent`

CHANGED: `preview`, `apply` and their `--round` forms used to refuse with `review
round root unavailable: absent` when a round's path was gone and its scratch root
had been removed too, and with `allocation root identity changed` when the root had
been recreated. They now report that round as `absent` (reason `round and its scratch
root are both gone`, or `round is gone and its scratch root was recreated`), and
`apply` records it `removed`, so the inventory can complete. Nothing is deleted. The
root must still be an expanded `scratch.roots` entry that is not otherwise refused,
and any inspection error other than a missing path still refuses.
An inventory left incomplete this way needs no action beyond running `preview`
and `apply` again under the usual authorization.
