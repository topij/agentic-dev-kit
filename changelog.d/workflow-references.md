## Workflows: triage-friction-log and pr-watch read their reference files on a trigger

CHANGED (report / return shape): `docs/agentic-dev-kit/workflows/triage-friction-log.md`
and `docs/agentic-dev-kit/workflows/pr-watch.md` each keep part of their text in a
directory of the same name beside them, and link each file with the condition for
reading it. The new files are `KIT_OWNED`, so `kit_doctor` lists any you lack:

- `docs/agentic-dev-kit/workflows/triage-friction-log/recovery.md`
- `docs/agentic-dev-kit/workflows/triage-friction-log/state-schema.md`
- `docs/agentic-dev-kit/workflows/triage-friction-log/finalize.md`
- `docs/agentic-dev-kit/workflows/triage-friction-log/engine-cli.md`
- `docs/agentic-dev-kit/workflows/pr-watch/engine-reference.md`

During `/upgrade`, take every one of them together with the two entry files. An entry
without its reference files sends the agent to a file that is not there.

If you vendor the kit's tests, take `scripts/tests/conftest.py` together with
`scripts/tests/test_portability.py` and `scripts/tests/test_pr_watch.py`. Both import
`read_workflow` from `conftest`, and a refreshed module beside an older `conftest.py`
fails at collection.
