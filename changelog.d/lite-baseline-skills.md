## kit_doctor: a lite install's baseline and main report cover its six skills

CHANGED: the six lite skill sources, `docs/agentic-dev-kit/lite/adapters/{claude,codex}/{session-start,wrap-up,review}/SKILL.md`,
are now kit-owned with role `lite`, where they were `repo-only` (#1365). On a lite
repository `kit_doctor.py` reads each at the skill path `adopt.md`'s *Lite profile*
installs it to (`.claude/skills/<slug>/SKILL.md`, `.agents/skills/<slug>/SKILL.md`), and
`--record-install` records it there, keyed by its source path. The main report now
fails a lite skill deleted after install (`removed`) or edited (`locally-edited`), where
it reported intact. A lite repository recorded before this change has only the three
docs in its baseline: re-run `--record-install --from-kit <kit checkout>` so the skills
are recorded.

CHANGED: on a lite repository, `--record-install` records a skill that is not the kit's
lite binding as the repository's own: listed in `not_installed`, named in a stderr note,
exit 0. The report reads it `declined`, and the verdict line reads
`intact for this adoption — lite install, <n> file(s) declined`. A skill absent beside
the repository's own `.claude/commands/<slug>.md` reads `declined` too.

CHANGED: `kit_doctor.py --json` lists the six skills in `files` (at the skill path on a
lite repository, at the source path elsewhere, where a full install reads them
`outside-profile`). The release manifest's `profiles.lite` lists them beside the three
docs, and a full install's re-recorded baseline lists them in `not_installed`.

CHANGED: a `config/dev-model.yaml` that exists but is not a regular file (a directory, or
a symlink that dangles or loops) is refused with exit 2 and
`error: <path> exists but is not a regular file` in every mode (#1360). `--adapter-report`
read it as no config, judging the repository `full` with exit 0. The main report already
exited 2, with a hint meant for an absent config. `lite-profile-install.md`'s "in every
mode" covered only a regular file that cannot be read, such as a permission failure.

ADDED: on a lite repository with no trusted baseline (none, or a copy of the release
manifest), the report prints
`⚠ profile: lite rests on the config alone — no trusted baseline records a lite install, so the files outside the lite profile go unchecked`.
The exit code is unchanged.
