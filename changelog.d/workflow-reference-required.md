## kit_doctor: an installed workflow's reference files are required

CHANGED (gate semantics): a file under `docs/agentic-dev-kit/workflows/<slug>/` is now
`missing-required` when absent and `docs/agentic-dev-kit/workflows/<slug>.md` is
installed at the kit's version. That makes `kit_doctor` exit 1 where it used to report the
file as an ordinary `missing`, `declined` or `new-upstream`. Today this covers
`pr-watch/report-fields.md` and the four `triage-friction-log/*.md` files.

An entry still at an older version gets no such requirement: the first report of an
upgrade offers its reference files as ordinary `new-upstream` or `missing` files. During
`/upgrade`, refresh the entry, re-run `kit_doctor`, and install every file it then reports
`missing-required`; do not offer those as a decision. The summary note now reads `required by an installed
engine or workflow`.
