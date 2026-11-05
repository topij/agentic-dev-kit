## kit_doctor and the adapter report: install profiles, and a lite profile `adopt` can install

ADDED: `config/dev-model.yaml` key `profile`, `full` or `lite`; absent means `full`.
`kit_doctor.py` refuses any other value with exit 2, in every mode, including a key
that is present but blank or null. A full install needs no change.

ADDED: the lite profile (#1320). `adopt.md` gains *Choose the profile* after Step 0
and a *Lite profile* section, which installs `docs/agentic-dev-kit/lite/` and
`session-start`, `wrap-up` and `review` skills for both runtimes, with no engines,
hooks or Python files. Its config keys are `profile`, `kit.version`,
`paths.handoff`, `paths.friction_log`, and the optional `friction.down_route` and
`review.safety_critical_paths`. `upgrade.md` Step 0 stops on a lite repository: its
upgrade path is not written yet.

CHANGED: the three `docs/agentic-dev-kit/lite/lite-*.md` docs are now kit-owned with
role `lite`, no longer `repo-only`. On a full install, an absent one reports the new
file state `outside-profile`, never `new-upstream` or `missing`, and `/upgrade`
leaves it out. It is not a finding, and the exit code is unchanged. A consumer of
`kit_doctor.py --json` that enumerates `files[].state` sees the new value, and the
three lite docs now appear in `files`.

CHANGED: when the install baseline's profile differs from the config's, `kit_doctor.py`
prints `✗ NOT intact` and exits 1. Re-run `--record-install` after moving between
profiles.

CHANGED: `kit_doctor.py --json` gains `profile` and `baseline_profile_mismatch`, and
`hooks_state` gains `outside-profile` (a lite repository). `--record-install` writes
`"profile": "lite"` into the baseline of a lite repository only; a full baseline is
unchanged. `--generate-manifest` writes a top-level `profiles` map
(`{"lite": [<paths>]}`). A consumer that compares the release manifest's keys or a
lite baseline's keys exactly sees the new key.

CHANGED: `--adapter-report` reads `profile` from the adopter's config. Two new row
states: `outside-profile` (a lite repository, a full-only skill it does not have)
and `profile-mismatch` (a binding that is the other profile's render). On a lite
repository the expected `session-start`, `wrap-up` and `review` skills are the lite
ones. `lib/runtime_adapters.py` takes six new `lib/adapter_templates/<runtime>/lite-*.md`
files: refresh that directory together with it.
