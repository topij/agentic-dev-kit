## Preflight command paths

Refresh `panel_prompt.py` and its tests. Keep `paths.engines` relative to the
repository without parent traversal, and install `check_record_prose.py` there.
The assembler now refuses missing checker files, non-regular targets and symlink
redirects before emitting a preflight command.
