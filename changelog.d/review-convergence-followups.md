## Review convergence follow-ups: a delta channel for later rounds

ADDED (engine CLI surface): `panel_prompt.py --last-reviewed <sha>` names the fix round
since `<sha>` (`git diff <sha>...<head>` and `git log <sha>..<head>`) as what a re-run
reads first, with the full diff and every severity still in scope (#1163). Use it for a
standard pull request's later-round delta pass, beside both draws, and to aim any
re-run. It exits 2 with `--repair-boundary`, with `--verifier`, with
`--agent-definition`, when empty, and when `<sha>` is not a strict ancestor of `--head`.

CHANGED (report shape): a delta prompt renders the LOW delta-or-ticket dispute route
("calls for a ticket", withdraw disputed code) only when `--repair-boundary` is given.
A record-prose delta's prompt no longer carries it. The panel doc declares the
two-full-pass switch as a constant beside the rule.
