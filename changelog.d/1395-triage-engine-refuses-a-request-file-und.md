## Triage engine: a symlinked artifact ancestor is named, and a state-path race ends `operator-held` instead of crashing

CHANGED (engine CLI surface): any artifact path whose parent directory is a symlink
(`observe`, `atomic_replace`, `exclusive_create`, `quarantine_inode`, `unlink_inode`)
is now refused with a message naming the symlinked directory, not a bare OS error
(`[Errno 20] Not a directory: 'tmp'` on macOS, `[Errno 40] Too many levels of symbolic
links` on Linux). A `--request` or `--approval-context` file placed under an
unresolved system temporary-directory alias, such as macOS's symlinked `/tmp`, used to
hard-stop naming no cause; the detail now names the symlinked directory. Resolve the
path yourself before passing it, as for the outcome-receipt and caller-run paths
(`docs/agentic-dev-kit/workflows/triage-friction-log/engine-cli.md`); the engine still
refuses a symlinked ancestor by design.

A symlinked ancestor met while an active session holds a state or gate artifact (for
instance, one introduced after the engine's own resolution) used to propagate an
unhandled `OSError` out of the CLI, exiting non-zero with a Python traceback instead of
a canonical result. It now ends the run `operator-held`, as `recovery.md` already
documents for a renamed, replaced, or symlinked parent, with exit `0` and a canonical
result naming the symlinked directory. Nothing to do: no caller depended on the crash.
