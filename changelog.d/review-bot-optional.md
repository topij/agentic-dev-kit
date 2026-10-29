## A third-party review bot is now opt-in

`review.bots` now defaults to `[]`, in `pr_watch.py`'s built-in default, in the
shipped `config/dev-model.yaml`, and in the key `init.sh` adds to a `review:`
section that lacks it. With no bot configured, every pull request's independent
review is the fallback review its `review_class` owes, run at the converged head:
one lens on a standard change, both lenses on a safety-critical one.

If your repo runs CodeRabbit or another reviewer, check that
`config/dev-model.yaml` names it explicitly, e.g. `bots: [coderabbit]`. A config
whose `review:` section has no `bots` key used to get CodeRabbit from the engine
default. It now gets no bot. That bot's pending check stops holding the merge,
the bot-named `configured review bot requested changes` blocker stops applying to
it (the aggregate `review decision is CHANGES_REQUESTED` blocker, which reads
every reviewer, still can), its review of the merging head no longer satisfies
the merge gate on its own, and `post-merge-systemize` no longer treats its
comments as review findings. The fallback review is owed instead. A config that already lists
the bot is unaffected.

`post-merge-systemize` needs a trusted review-finding source, and a review bot
was the only one the shipped config named. With `review.bots: []` and the
shipped `systemize.operator_logins: []`, the engine refuses with
`no trusted review source: configure systemize.operator_logins or review.bots`.
Set `systemize.operator_logins` to the forge logins whose PR comments should
count as review findings; `init.sh` prompts for it.
