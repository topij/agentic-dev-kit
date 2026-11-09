## upgrade: a lite install has an upgrade path

CHANGED: `upgrade.md` Step 0 no longer stops on a repository whose config says
`profile: lite`. It routes to the new *Lite profile* section at the end of
`upgrade.md`, which replaces the lite docs and skills that were not edited in the
repository with the kit's copies, leaves edited ones and kept skills to the operator,
and re-records `kit-manifest.json` with `kit_doctor.py --record-install` run from the
kit clone. It stops when the config schema is behind the kit's: no lite config
migration exists. A full install's upgrade is unchanged.

CHANGED: the `AGENTS.md` section `adopt.md`'s *Lite profile* writes gains a sentence
naming that upgrade path. To take it into an existing lite install, run the upgrade:
its U2 step compares the section with the kit's and offers the change.
