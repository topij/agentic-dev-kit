## `panel_prompt.py --preflight-rev`; the kit's own reviewer eval

ADDED (engine CLI surface): `panel_prompt.py` gains `--preflight-rev <sha>`, which takes
the narrative preflight's checker and config from that commit instead of `--head`, and
says so in the prompt under the preflight invocation. The verifier and
`--agent-definition` refuse it. Nothing changes for a call without it.

The reviewer eval itself (`scripts/review_eval.py` and
`docs/agentic-dev-kit/review-eval/`, #1156) is kept in the kit's own repository and is
not installed. `fallback-review-panel.md` now asks for an eval score on a
`lens_compute` or `focus` change only where an eval exists, so an adopter has nothing to
do for it.
