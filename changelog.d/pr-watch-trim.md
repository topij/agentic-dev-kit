## Workflows: pr-watch's explanations move to its reference file

CHANGED (report / return shape): `docs/agentic-dev-kit/workflows/pr-watch.md` keeps the
rules its loop acts on, and the reasoning behind loop step 1's merge blockers, the
*Converged* stop condition's review request, the round count and `--all-comments` moved
to four new sections of `docs/agentic-dev-kit/workflows/pr-watch/report-fields.md`. The
entry cites them by name, and the split test checks each cited section exists.

During `/upgrade`, take `pr-watch.md` and `pr-watch/report-fields.md` together, as before.
An entry from this change beside an older reference file cites sections that file does
not have.
