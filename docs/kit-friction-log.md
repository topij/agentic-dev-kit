# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **This repo's tracker is GitHub Issues on itself**, so most friction is filed directly as
> issues rather than parked here — which is the routing Principle #2 prescribes, not a
> neglected inbox. Anything that appears below a graduation marker is un-graduated: not yet
> issue-shaped, or waiting for the next `triage-friction-log` sweep.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-08-08 — Backlog migrated to GitHub Issues (#370–#374)

Tenth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Seven entries in, seven accounted for:** five new issues
([#370](https://github.com/topij/agentic-dev-kit/issues/370)–[#374](https://github.com/topij/agentic-dev-kit/issues/374)),
two occurrence comments (`#305`, `#115`), and one entry that routed nowhere new — the cockpit
mutation-harness post-mortem, whose occurrence *and* its "do not mutate the live tree" reframe
were already on `#326` before this sweep began. All seven writes were re-read from the tracker
after landing per `#138` — compared **by body**, with both commented issues confirmed still
open afterwards.

**Approval.** The operator replied `Lgtm` in the Slack DM thread (channel `D083840DP7B`, parent
ts `1786168490.379319`) — a bulk approve of all seven, with nothing declined.

**Frozen inbox:** 16,602 bytes, `sha256 d8952f1c…`, reproducing from
`tail -n +14 docs/kit-friction-log.md | shasum -a 256` — run at draft time and again at
finalize, digest matched both times. The current inbox was byte-identical to the snapshot at
finalize, so every block swept and nothing was held back.

**Reading the tracker before drafting changed two routings.** The `panel_prompt.py` entry reads
as already handled — `#214` has landed, the engine ships, and `git grep panel_prompt` now hits
`fallback-review-panel.md` — but that hit is a `lens_compute` config aside, and "Running it"
step 2 still tells you to hand-author every lens prompt. The entry's wording had gone stale
while its substance stood, which is `#373`. The cockpit mutation-harness entry went the other
way: already fully represented on `#326`, so filing anything would have duplicated it. Swept
entries are verbatim in the archive under `Graduated 2026-08-08`.
