## Document budgets: an entry may omit `archive`, for instruction files

CHANGED (config keys): a `doc_budgets` entry in `config/dev-model.yaml` may now omit
`archive`. Use that for an instruction file such as `AGENTS.md`, which has no history
file to sweep into, and write a `remedy` that names consolidation. Over budget,
`check_doc_budget.py` then prints `⚠ <path> is <n> lines (budget ~<b>): <remedy>.`
instead of an archive sweep. An `archive:` key whose value is empty or not a path
(`false`, a number, a list) now stops the engine with exit 2; omit the key instead. An
empty `remedy` stops it with exit 2 as well. Existing entries with a path `archive` and
a non-empty `remedy` need no change.

The kit's own config adds an `AGENTS.md` entry. Your config is yours, so nothing is
added to it on upgrade: copy the entry if you want the tripwire, and set its `budget`
for your file. A configured path that does not exist stops the engine with exit 2, so
add an entry only for a file every checkout has.

CHANGED (report / return shape): `post-merge-systemize` shared-rule proposals and their run report
now state each proposal's net line change and the existing text it considered folding
into, and a `triage-friction-log` ticket that changes a standing instruction asks its
implementing pull request for the same figure.
