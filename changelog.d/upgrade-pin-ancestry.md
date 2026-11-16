## Pin an upgrade to a kit revision

BREAKING (upgrade procedure, #1445) — Set `KIT_REF` in the shell running the upgrade kit block. Choose a tag, branch,
full commit SHA, or the empty string for the remote default. Carry the resolved
SHA into the full preflight or lite planning read with `--check-upgrade`.
Select a candidate whose doctor supports this flag. Commit the installed kit's
actual revision in the adopter's baseline before upgrading a legacy install
with unknown provenance. If the candidate needs more history, give the kit
clone access to its origin and retry.

BREAKING (report shape) — Lite JSON readers should handle a null
`apply` command on a stopped plan.
