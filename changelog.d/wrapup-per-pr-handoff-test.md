## wrap-up: the handoff test runs before every pull request; friction is routed when found

CHANGED (gate semantics): `wrap-up`'s handoff test now runs before every pull request
goes to review, not only before a session's last one. A pull request whose body,
commits, changelog fragment and tickets already record its work, which is the usual
case, commits nothing to the handoff; one that made a decision, abandoned an approach
or moved a workstream's `▶ Next:` carries that record and is reviewed with it. A lane's
`dev/*` pull request still never carries it. If you check that only a session's last
pull request touches the handoff, drop that check.

CHANGED (gate semantics): friction is routed when it is found, through the same
friction-routing step, rather than at session end; a closing `wrap-up` routes only
what is still unrouted. The full `wrap-up` runs on the operator's request, and the
agent offers it in one line when a session ends with half-finished state, a decision
that exists only in the conversation, or unrouted friction. A parked friction-log entry
is committed only on a pull request that has not gone to review yet. Update the wrap-up
skill descriptions, the handoff sentence in your `AGENTS.md`, and the headers of your
`docs/handoff.md` and `docs/friction-log.md` (all rendered from `docs/templates/`), to
pick up the new timing.
