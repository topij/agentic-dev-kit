## post-merge-systemize reads fallback-panel dispositions and tallies reviewer precision

CHANGED (report shape): the systemize digest now takes fallback-panel findings from
`pr_watch.py --record-review --disposition` comments by a trusted author (#772). Each
typed line `<lens> F<n> <SEVERITY>: <stance> — <text>` becomes a finding with id
`disposition:<comment-id>:<lens>:F<n>`, whose `source` also carries `lens` and
`review_source`. Every finding gains `stance` and `reviewed_head`, which are null for
thread and review findings. The digest gains a top-level `reviewer_tally`: per-source
counts by addressed state and stance, a refuted flag, and per-PR rounds (#1157).
`digest_merged_prs.py --verify` compares the new fields too, so an agent-built
LLM-only digest written to the old shape now fails verification. Build it to Step 1 of
the current `post-merge-systemize.md`.

ADDED (config keys): `systemize.refuted_flag_min_findings` and
`systemize.refuted_flag_percent` are optional. If omitted, they read `5` and `50`.

To get panel findings into a run, list the account that posts the disposition comments
in `systemize.operator_logins`, for example in `config/dev-model.local.yaml`. Write each
finding's disposition as the typed line, with the lens's severity. An empty operator
list still reads no disposition comment.
