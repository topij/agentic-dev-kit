## Workflows: triage-friction-log is split into an entry plus reference files

CHANGED (report / return shape): `docs/agentic-dev-kit/workflows/triage-friction-log.md`
keeps part of its text in a directory of the same name beside it, so that each file fits
in a single read. The entry and each reference file say to read all of them before the
first action of any run. The new files are `KIT_OWNED`, so `kit_doctor` lists
any you lack:

- `docs/agentic-dev-kit/workflows/triage-friction-log/recovery.md`
- `docs/agentic-dev-kit/workflows/triage-friction-log/state-schema.md`
- `docs/agentic-dev-kit/workflows/triage-friction-log/finalize.md`
- `docs/agentic-dev-kit/workflows/triage-friction-log/engine-cli.md`

During `/upgrade`, take every one of them together with the entry file. An entry
without its reference files sends the agent to a file that is not there.

If you vendor the kit's tests, take `scripts/tests/conftest.py` together with
`scripts/tests/test_portability.py`. It imports `read_workflow` from `conftest`, and a
refreshed module beside an older `conftest.py` fails at collection.
