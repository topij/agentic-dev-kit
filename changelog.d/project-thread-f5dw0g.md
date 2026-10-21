## Review panel: an optional findings verifier, cited findings and typed dispositions

ADDED (engine CLI surface): `panel_prompt.py --verifier --head <sha> --scratch <tree>
--lens-report <lens>=<path>` (one `--lens-report` per lens that ran) renders the
verifier's prompt: the lens reports quoted verbatim under the doctrine's new *The
contract the verifier gets* (#1155, #613). With `--verifier` the command exits 2 on
`--lens`, the draw flags, `--repair-boundary`, `--carry-forward` or
`--prior-dispositions`, and on a report that is missing, empty, named twice or
attributed to a lens outside `review.fallback_panel.lenses`. `--lens-report` without
`--verifier` exits 2, and `--agent-definition` refuses both new flags.

CHANGED (engine CLI surface): `--lens` is no longer argparse-required. A lens prompt or
`--agent-definition` without it still exits 2, now with this script's own message
instead of argparse's usage error.

CHANGED (report shape): the lens contract in `fallback-review-panel.md` gains **Cite
your evidence**: a lens numbers its findings `F1`, `F2` and on, and cites `path:line`
or an executed command for each. The panel doc adds *Verifying findings* (optional until
the reviewer eval measures it; a HIGH the verifier refutes goes to the operator),
*Typed dispositions* (`accept`, `dispute-evidence`, `dispute-concern`; a HIGH or a
lens-marked regression is never closed by `dispute-concern`), and *When a lens amends
its report after the receipt* (#719). If you keep a local copy of the panel doctrine or
of `pr-watch.md`, take these sections with it.
