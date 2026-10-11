## Record preflight commit object identity

Refresh `check_record_prose.py` and its tests. Base, head, and stamp revisions must
identify a unique commit object directly. Hex-named branches and tags cannot supply
missing object IDs or disambiguate object prefixes; annotated tag object IDs are not
peeled into commits. Use the commit's full SHA or an unambiguous abbreviation.

The no-write regression checks now observe directories, symlink targets, permissions,
and modification metadata as well as regular-file bytes.
