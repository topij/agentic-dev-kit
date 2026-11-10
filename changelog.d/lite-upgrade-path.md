## upgrade: a lite install has an upgrade path

CHANGED: `upgrade.md` Step 0 no longer stops on a repository whose config says
`profile: lite`. It routes to the new *Lite profile* section at the end of
`upgrade.md`, which replaces the lite docs and skills that were not edited in the
repository with the kit's copies, leaves edited ones and kept skills to the operator,
and re-records `kit-manifest.json` with `kit_doctor.py --record-install` run from the
kit clone. It stops when the config schema is behind the kit's: no lite config
migration exists, and when the install has no recorded baseline. Its copy and
record blocks refuse to write unless `REPO` is the top of a checkout on the branch
bound as `LITE_BRANCH`, and that branch is not the one bound as `LITE_PROTECTED`
(empty when the repository names none); U1 says how to bind both. The copy block
stops with `unknown:` and copies nothing when `LITE_TAKE` names a path that is not a
lite file. The upgrade is done only when the committed baseline names the kit clone's
commit; U2 says how to check. A full install's upgrade is unchanged.

CHANGED: the `AGENTS.md` section `adopt.md`'s *Lite profile* writes gains a sentence
naming that upgrade path. To take it into an existing lite install, run the upgrade:
its U2 step compares the section with the kit's and offers the change.
