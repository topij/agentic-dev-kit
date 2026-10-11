## Workflows: pr-watch's explanations move to its reference file

CHANGED (report / return shape): `docs/agentic-dev-kit/workflows/pr-watch.md` keeps the
rules its loop acts on. The reasoning behind loop step 1's merge blockers, the
*Converged* stop condition's review request, the round count and `--all-comments` moved
to new sections of `docs/agentic-dev-kit/workflows/pr-watch/report-fields.md`: *Review
evidence and merge blockers*, *The review request at convergence*, *Round counting* and
*The all-comments view*. The entry names each of them where its text used to be. The
split test fails when a section the entry cites by name is missing from the reference
file, and `test_pr_watch.py` fails when the entry drops one of these citations or one
of the loop rules that test lists.

During `/upgrade`, take `pr-watch.md` and `pr-watch/report-fields.md` together, as before.
An entry from this change beside an older reference file cites sections that file does
not have.
