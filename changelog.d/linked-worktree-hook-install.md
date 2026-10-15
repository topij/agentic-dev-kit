## init.sh: a linked worktree no longer rewrites the hooks every checkout shares

CHANGED (engine CLI surface): run from a linked worktree, `init.sh` (and `make
install-hooks`, which runs its `install_hooks`) no longer writes the pre-push shim into
a hooks directory other checkouts share (#990). That covers the common dir's `hooks/`
and an absolute `core.hooksPath` outside the worktree. A byte-identical, executable shim is
reported `already current`. Anything else (absent, or a shim for another engines dir) is reported
`deferred` on stderr and left unwritten, so the primary checkout and other worktrees keep
their hook until the upgrade merges. A relative `core.hooksPath` below the worktree, and
every run from the primary checkout, behave as before; one that climbs out with `..` is
judged by where it lands.

What an adopter must do: after an upgrade that ran in a linked worktree and printed
`deferred`, install the hook once it has merged. In the primary checkout on the merged
revision, run `make install-hooks` where that target exists, or else re-run
`./init.sh --no-clobber`. Alternatively run
`DEVKIT_INSTALL_SHARED_HOOKS=1 ./init.sh --no-clobber` from a linked worktree of it.
Automation that ran `init.sh` in a linked worktree to install hooks must set that
variable.
