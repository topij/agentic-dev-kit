## Pass a ref when you install or upgrade the kit

`adopt.md` and `upgrade.md` Step 0 now clone the kit at a ref you name: set `KIT_REF` to a release tag or a commit sha before running the kit block, and the block prints the resolved commit (`kit commit: <sha>`) before the first copy. Put that sha in the adoption's or upgrade's pull request. With no `KIT_REF` the block uses `main`, as it stands when it runs. A lite upgrade that named a ref adds `--kit-commit <sha>` to U2's `kit_doctor.py --upgrade-lite` read; with no ref it runs as before. No engine changed.
