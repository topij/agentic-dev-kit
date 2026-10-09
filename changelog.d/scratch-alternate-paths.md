## Scratch alternate path preservation

- **Gate semantics:** Refresh `scripts/sweep_scratch.py` and its tests. Unquoted
  `objects/info/alternates` paths retain whitespace and filesystem bytes, so the
  survey and removal re-check protect the actual borrowed object store.
