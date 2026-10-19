## Scratch retirement with empty Git markers

Refresh `scripts/sweep_scratch.py` and its tests. Empty regular `.git` files no
longer classify an entry as `live-worktree`; stale sweeps and finished-round
retirement can remove entries containing them when the other protections allow it.
Nonempty malformed Git files and Git dependencies remain protected.
