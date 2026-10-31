## session_cleanup.py: a round whose scratch root is gone too retires as `absent`

CHANGED: `preview`, `apply` and their `--round` forms used to refuse with `review
round root unavailable: absent` when a round's path was gone and its scratch root
had been removed too. They now report that round as `absent`, with the reason
`round and its scratch root are both gone`, and `apply` records it `removed`, so the
inventory can complete. Nothing is deleted. The root must still be an expanded
`scratch.roots` entry, any inspection error other than a missing path still
refuses, and a recreated root still refuses with `allocation root identity changed`.
An inventory left incomplete this way needs no action beyond running `preview`
and `apply` again under the usual authorization.
