## Triage engine: a symlinked artifact ancestor is refused by name, and a gate under one is not reported as a held gate

CHANGED (engine CLI surface): when the engine's own walk of an artifact path meets a
symlinked directory, it still refuses it, but the refusal now names that directory by
its full path (`symlinked parent is refused: <directory>`) instead of a bare OS error
such as macOS's `[Errno 20] Not a directory: 'tmp'`. The walk runs for `--request` and
`--approval-context` files and for every state, gate, recovery and quarantine artifact
it opens, both the first time and on each re-walk before a write. A directory swapped
for a symlink between one storage call's first walk and its re-walk now ends the run
`operator-held` with a canonical result, where it used to escape as an unhandled
`OSError`. A directory under the state root that is a symlink when the engine resolves
a state path, whether it was one when the run started or was swapped in between two
storage calls, is unchanged: the state resolver refuses it with an unhandled
`PathTraversalError`, as before.

What to do: pass `--request` and `--approval-context` paths with no symlinked
directory above them. Resolve them yourself first, as `engine-cli.md` already asks for
the outcome-receipt and caller-run paths; an unresolved system temporary-directory
alias such as macOS's `/tmp` is the usual cause.

A directory above the triage gate that becomes a symlink after the engine resolved the
state root keeps `refusal_code: single-writer-gate`, but its `resume_action` now says
to put the real directory back and rerun, not to use interactive `recover` for a
proven-dead owner. An interactive `recover` or `test` whose own gate acquisition meets
the swap returns the same refusal. Once the directory is back, a rerun reports a gate
the refused run published before the swap as held; while the symlink is still in place,
a rerun fails in the state resolver as above. A caller that matches on the old
`resume_action` text for this case must match the new one.
