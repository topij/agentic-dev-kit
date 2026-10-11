## Workflows: pr-watch is split into an entry plus a reference file

CHANGED (report / return shape): `docs/agentic-dev-kit/workflows/pr-watch.md` no longer
has a *Notes* section. Its instructions moved into the loop steps and the paragraphs
before the loop, and its description of report fields, the REST backend and the review
configuration keys moved to `docs/agentic-dev-kit/workflows/pr-watch/report-fields.md`.
The entry and the reference file say to read both before the first action of any run.
The new file is `KIT_OWNED`, so `kit_doctor` lists it if you lack it.

During `/upgrade`, take `pr-watch/report-fields.md` together with `pr-watch.md`. An entry
without its reference file sends the agent to a file that is not there.

If you vendor the kit's tests, take `scripts/tests/conftest.py` together with
`scripts/tests/test_pr_watch.py`. It now imports `read_workflow` from `conftest`, and a
refreshed module beside a `conftest.py` older than that function fails at collection.
