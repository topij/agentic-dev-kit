## Narrative preflight on mixed changes

- CHANGED (gate semantics, #1197): `check_record_prose.py` now checks the
  configured narrative paths of any change that touches at least one of them,
  instead of returning `not-applicable` whenever another file changed too. It
  returns `not-applicable` only when no narrative path changed. A mixed change
  that used to exit 0 as `not-applicable` can now exit 1 on a finding in its
  handoff or friction-log lines: resolve it, or declare an intended closing
  reference with `--allow-close`.
- ADDED (report shape, #1197): the JSON report carries `unchecked_paths`, the
  changed files outside the narrative paths, which got no preflight check. Read
  it with `paths` rather than assuming the whole diff was scanned. The `limits`
  list gains one entry saying so.

Take `scripts/check_record_prose.py` together with
`docs/agentic-dev-kit/fallback-review-panel.md` and
`docs/agentic-dev-kit/workflows/wrap-up.md`: run the preflight before the opening
review of any change that touches a narrative path. If you vendor the kit's tests,
take `scripts/tests/test_record_prose.py` as well.
