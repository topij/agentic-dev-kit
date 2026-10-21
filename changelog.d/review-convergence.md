## Review convergence: prior dispositions, bug classes and pre-existing findings

ADDED (engine CLI surface): `panel_prompt.py --prior-dispositions <link>` renders a
pointer to where earlier rounds' findings and dispositions are posted, under its own
heading; the lens reads it after its own pass (#1153, #463). The value must be one
`https://` link with no whitespace, or the command exits 2, and `--agent-definition`
refuses the flag like every other prompt flag. Pass it on every re-run's prompt; a first pass needs nothing.

CHANGED (gate semantics): the lens contract in `fallback-review-panel.md` gains
**Name the bug class**, **Classify against the base**, **Expect the remediation to
carry the next defect** and **No repeats**. A finding classed *pre-existing*, with the
base revision cited, takes the ticket route at any severity, and is put to the
operator when it sits on a `review.safety_critical_paths` file or is rated HIGH
(#1154). Under #1153,
after its second full pass a standard pull request's later rounds take the
`fallback:delta` pass at any severity; safety-critical pull requests keep full
re-runs. If you keep
a local copy of the panel doctrine or of `pr-watch.md`, take these sections with it.
