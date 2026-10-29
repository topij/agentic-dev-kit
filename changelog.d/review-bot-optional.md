## A third-party review bot is now opt-in

BREAKING (config keys): `review.bots` now defaults to `[]`, in `pr_watch.py`'s
built-in default, in the shipped `config/dev-model.yaml`, and in the key `init.sh`
adds to a `review:` section that lacks it. With no bot configured, every pull
request's independent review is the fallback review its `review_class` owes, run
at the converged head: one lens on a standard change, both lenses on a
safety-critical one. If your repo runs CodeRabbit or another reviewer, check that
`config/dev-model.yaml` names it explicitly, e.g. `bots: [coderabbit]`. A config
that already lists the bot is unaffected.

BREAKING (gate semantics): a config whose `review:` section has no `bots` key used
to get CodeRabbit from the engine default, and now gets no bot. For that bot:
- its pending check stops holding `mergeable`;
- the bot-named `configured review bot requested changes` blocker stops applying
  to it (the aggregate `review decision is CHANGES_REQUESTED` blocker, which reads
  every reviewer, still can);
- its review of the merging head no longer satisfies the merge gate on its own;
  the fallback review is owed instead;
- `post-merge-systemize` no longer treats its comments as review findings.

Name the bot in `review.bots` to keep the old behaviour.

BREAKING (gate semantics): `post-merge-systemize` needs a trusted review-finding
source, and a review bot was the only one the shipped config named. With
`review.bots: []` and the shipped `systemize.operator_logins: []`, the engine
refuses with
`no trusted review source: configure systemize.operator_logins or review.bots`.
Set `systemize.operator_logins` to the forge logins whose PR comments should count
as review findings; `init.sh` prompts for it.

CHANGED (report / return shape): with no bot configured, the PR follow-up hook's
reminder says the fallback review is the PR's own review instead of conditioning
it on an unavailable bot. Nothing to do.
