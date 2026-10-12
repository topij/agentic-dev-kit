## kit_doctor: an installed workflow's reference files are required

CHANGED (gate semantics): a file under `docs/agentic-dev-kit/workflows/<slug>/` is now
`missing-required` when absent and `docs/agentic-dev-kit/workflows/<slug>.md` is
installed at the kit's version. That makes `kit_doctor` exit 1 where it used to report the
file as an ordinary `missing`, `declined` or `new-upstream`. Today this covers
`pr-watch/report-fields.md` and the four `triage-friction-log/*.md` files.

During `/upgrade`, install every such file; do not offer it as a decision. An entry left
at an older version gets no such requirement until you refresh it, so re-run `kit_doctor`
after refreshing a workflow entry. The summary note now reads `required by an installed
engine or workflow`.
