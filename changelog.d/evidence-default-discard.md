## session_cleanup.py: discard by default; retained evidence needs an exception and retires through `retire-evidence`

BREAKING: `session_cleanup.py seal` (and `seal --round`) now refuses a `retain` item
without an `exception` object naming `task`, `next_action` and `delete_when`, all
non-empty. An adopter adapter or script that writes seal manifests must either add
that object to each item it truly needs to keep, or stop retaining it and list it
under the new `discard` key instead, as `{"source": <absolute path>, "reason":
<where the result is recorded>}`.

CHANGED: `retain` may now be empty when `discard` has at least one entry. This is
the normal completion path: a round or session whose results are on the pull request
seals without copying anything. A source cannot be both retained and discarded.

ADDED: `session_cleanup.py retire-evidence <session> [--include <sha256>]` previews
deleting retained evidence that no unfinished task needs, and `--approve <token>`
applies it under operator authorization naming that inventory; a standing cleanup
grant does not cover it. Items keep a tombstone (`retired`) with their hash, size, kind, source
and exception. Items with an exception, and `source` items sealed before this
change, stay kept unless named with `--include`.

ADDED: the seal reports `bytes.retained` and `bytes.copied`. `preview`,
`preview --round` (whole inventory), each `list` entry and the `retire-evidence` plan
report `evidence_summary`: `present`, `retiring`, `retired` and `missing`, each with
`items` (index entries) and `bytes` (each stored file once), plus an `exceptions`
count. A consumer that compares these outputs exactly will see the new keys.

CHANGED: a seal stores only `source`, `kind`, `requires` and `exception` from each
retained manifest item, with paths normalised, and validates every item before it
copies any bytes. A preview of a seal whose retained bytes are absent without a
tombstone now refuses with a named error rather than a raw file-not-found.

To reclaim space held by inventories sealed before this change, run
`retire-evidence` on each complete inventory under the operator's authorization;
see *Retire retained evidence* in `docs/agentic-dev-kit/session-cleanup.md`.
