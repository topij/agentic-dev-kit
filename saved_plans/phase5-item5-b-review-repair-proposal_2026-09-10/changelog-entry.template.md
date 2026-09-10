## #{{REPAIR_PR_NUMBER}} — {{EXECUTION_DATE}}

- **CHANGED — state-write detection:** refresh the installed engine-root
  `conftest.py` and `tests/test_state_guard.py`, then run the installed suite from
  the repository root. Creating or changing a regular file at the repository's
  `state` path now makes verification fail; inspect the reported path before
  restoring it from the verified pre-run state.

