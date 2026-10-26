## Lanes declare a terminal state; the launcher resumes or records a stall

ADDED (config keys): `parallel.max_resumes`, a non-negative integer, shipped as `1`.
`launch_lane.py` exits 64 before any launch attempt when it is missing or not such an
integer. Run `init.sh` (or `/upgrade`) to add it, or add `max_resumes: 1` under
`parallel:` yourself.

CHANGED (gate semantics): a lane whose runtime exits successfully is `completed` only
when the last non-blank line of its final text is `LANE-TERMINAL: pr-ready #<n>`,
`LANE-TERMINAL: no-pr <reason>` or `LANE-TERMINAL: blocked <reason>` (#514, #564). The
lane contract (`dev_session.sh print-contract`, and the descriptor's
`prompt_preamble`) now asks for that line. Without it, a Claude lane is resumed in the
same session up to `parallel.max_resumes` times. A lane that still names no terminal
state, or cannot be resumed (any Codex lane, `max_resumes: 0`, a result with no
canonical session id), is recorded with the new receipt status `stalled`. A task prompt
that tells the lane to reply with an exact text must leave room for the closing
`LANE-TERMINAL:` line; otherwise each run costs a resume round and can stall.

ADDED (engine CLI surface): `launch_lane.py` exits 75 for a `stalled` lane. A caller
that treated every nonzero exit as a failure now also sees a stall there; one that
checked for exit 70 alone does not.

CHANGED (report shape): the launch request carries `request.max_resumes`, and every
terminal receipt carries `terminal.lane_state` (`state`, `pr`, `reason`, or `null`) and
`terminal.resumes`, one entry per resume round with its own argv, digests, return code,
denials, usage, terminal state and error; a round cut short by a refusal is recorded
with the fields it never reached `null` and `error` `round did not finish`.
`terminal.usage` still covers the launch round alone; add each
`terminal.resumes[].usage` for the lane's total. `dev_session.sh list` shows `stalled`
in the RUN column.
