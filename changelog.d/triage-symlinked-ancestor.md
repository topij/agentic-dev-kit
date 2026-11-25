## Triage engine: a symlinked artifact ancestor is refused by name, and a gate under one is not reported as a held gate

CHANGED (engine CLI surface): an artifact path with a symlinked directory above it is
still refused, but the refusal now names that directory by its full path
(`symlinked parent is refused: <directory>`) instead of a bare OS error such as
macOS's `[Errno 20] Not a directory: 'tmp'`. This covers `--request` and
`--approval-context` files and every state, gate, recovery and quarantine artifact.
It holds on the engine's first walk of the path and on each re-walk it makes before a
write, so a directory swapped for a symlink in between ends the run `operator-held`
with a canonical result, where it used to escape as an unhandled `OSError`.

What to do: pass `--request` and `--approval-context` paths with no symlinked
directory above them. Resolve them yourself first, as `engine-cli.md` already asks for
the outcome-receipt and caller-run paths; an unresolved system temporary-directory
alias such as macOS's `/tmp` is the usual cause.

A directory above the triage gate that becomes a symlink after the engine resolved the
state root keeps `refusal_code: single-writer-gate`, but its `resume_action` now says
to put the real directory back, not to use interactive `recover` for a proven-dead
owner, and an interactive `recover` or `test` returns that refusal without inspecting a
gate. A caller that matches on the old `resume_action` text for this case must match
the new one.
