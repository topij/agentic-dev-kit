## Lanes use file-based messages and a launcher-read ticket; the profile grants restore and comment

ADDED (engine CLI surface): `launch_lane.py --ticket <n>` reads GitHub issue `n` with
`gh` from the trusted executable path before launch. It appends the issue to the lane's
prompt between `<<<TICKET` and `TICKET>>>` lines (#1081, #271). It exits 64 before any
launch attempt when:

- the read fails;
- the answer is not that issue;
- the ticket contains `TICKET>>>`;
- `tracker.backend` is not `github-issues`.

Without `--ticket` nothing changes. To use it, have `gh` authenticated and on the
trusted path.

CHANGED (report shape): the launch request carries `request.ticket` (`number`, `url`,
`block_sha256`, or `null`). A reader that compares a request binding field by field
must include it.

CHANGED (gate semantics): the lane contract (`dev_session.sh print-contract`, and the
descriptor's `prompt_preamble`) gains three instructions (#1011, #628):

- keep each shell call to one simple command;
- write commit messages and pull-request text under `<state.dirname>/lane/` in the
  worktree, and pass them with `git commit -F` and `gh pr create --body-file`, with the
  verification result in the body before opening and later additions as
  `gh pr comment --body-file`;
- undo worktree changes with `git restore`.

The "wait on anything" rule now says to poll with one simple check per call, not with
an until-loop. A launcher that compares the preamble with `print-contract` needs both
from the same kit revision.

CHANGED (config keys): the shipped `config/claude-lane-settings.json`, and the copy
`init.sh` seeds when none exists, now also allow `Bash(git restore:*)` and
`Bash(gh pr comment:*)`. `init.sh` never rewrites an existing profile. Add both entries
to yours, or a lane that follows the new contract has those calls denied and ends
`failed`.
