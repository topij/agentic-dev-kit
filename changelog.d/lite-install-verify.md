## adopt: the lite install carries no shell variable between commands, and L5 is one engine command

ADDED (engine CLI): `kit_doctor.py --verify-lite --from-kit <kit> --root <root>` (#1420).
It runs `adopt.md`'s *Lite profile* L5 against the record L4 wrote in the working tree
from that kit, and judges it. It prints two `verify (L5):` lines, one for the install
and one for the skill bindings, and exits 0. A lite doc or skill that is missing,
edited or otherwise not intact, and a binding that is neither the kit's render nor a
kept one, each give a `stop: verify (L5):` line and exit 1. So does a config whose
`kit.version` is not the kit's. With no record L4 wrote from that kit's commit it
prints `refused:` and exits 1. Both paths must be absolute, and the flag combines with
no other mode (exit 2). It writes nothing. A lite file left absent counts as missing
here, except the Claude skill L3 skipped for a kept `.claude/commands/<slug>.md`: the
upgrade's `--leave-absent` choice does not exist at install.

CHANGED: `adopt.md`'s *Lite profile* no longer uses the Step 0 block that binds `REPO`
and `KIT`. L1 runs only the kit block, and writes down the kit path it prints and the
checkout's root. L3's copy block starts with `REPO='<root>'` and `KIT='<kit>'`, filled
in by hand. It refuses a placeholder left in, a root that is not the top of a checkout,
and a kit path with no `kit-manifest.json`. L4 is `--record-install --from-kit <kit>
--root <root>`. L5 is the `--verify-lite` command above, in place of the main report
and the adapter report read by eye.

What to do: nothing, unless your own notes or scripts for a lite install run L5's two
old commands, or rely on `KIT` and `REPO` carrying from Step 0. Run `--verify-lite`
with both paths written out instead. A full install is unchanged.
