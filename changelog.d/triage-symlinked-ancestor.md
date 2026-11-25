## Triage engine: a symlinked artifact ancestor is refused by name, and a gate under one is not reported as a held gate

CHANGED (engine CLI surface): when the engine's own walk of an artifact path meets a
symlinked directory, it still refuses it, but the refusal now names that directory by
its full path (`symlinked parent is refused: <directory>`) instead of a bare OS error
such as macOS's `[Errno 20] Not a directory: 'tmp'`. The walk runs for `--request` and
`--approval-context` files and for every state, gate, recovery and quarantine artifact
it opens, both the first time and on each re-walk before a write. A directory swapped
for a symlink in between now ends the run `operator-held` with a canonical result,
where it used to escape as an unhandled `OSError`. A directory under the state root
that is already a symlink when a run starts is unchanged: the state resolver refuses it
before any walk, as before.

What to do: pass `--request` and `--approval-context` paths with no symlinked
directory above them. Resolve them yourself first, as `engine-cli.md` already asks for
the outcome-receipt and caller-run paths; an unresolved system temporary-directory
alias such as macOS's `/tmp` is the usual cause.

A directory above the triage gate that becomes a symlink after the engine resolved the
state root keeps `refusal_code: single-writer-gate`, but its `resume_action` now says
to put the real directory back and rerun, not to use interactive `recover` for a
proven-dead owner. An interactive `recover` or `test` returns the same refusal, since
no gate can be read through the symlink; if the run had published its gate before the
swap, the rerun reports that gate as held. A caller that matches on the old
`resume_action` text for this case must match the new one.
