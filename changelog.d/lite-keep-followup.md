## kit_doctor: a lite baseline records which skills were kept

CHANGED: a lite `--record-install` writes `kept`, the source paths of the skills named
with `--keep` that are not the kit's copy, beside `not_installed`. Only a skill in `kept`
reads `declined` while present. A skill that was absent at record time (one skipped for
the repository's `.claude/commands/<slug>.md`, say) and has appeared since, not the
kit's copy, is now drift and fails the report, where it read `declined` with exit 0. A
lite baseline recorded with `--keep` before this change has no `kept`: re-run
`--record-install --from-kit <kit checkout> --keep <skill path>` for each kept skill,
or its kept skills read as drift.

CHANGED: `--keep` naming a skill that is not there exits 2 before anything is written.

CHANGED: a `config/dev-model.yaml` that cannot be looked up for a reason other than its
absence, such as a `config/` directory that cannot be searched, is refused with exit 2
and `error: <path> cannot be read: <reason>` in every mode. `--adapter-report` read it
as no config, judging the repository `full` with exit 0. Make the directory searchable,
or move it aside.
