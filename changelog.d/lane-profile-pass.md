## Lanes use file-based messages and a launcher-read ticket; the profile grants restore

ADDED (engine CLI surface): `launch_lane.py --ticket <n>` reads GitHub issue `n` with
`gh` from the trusted executable path before launch. It appends the issue to the lane's
prompt between `<<<TICKET` and `TICKET>>>` lines (#1081, #271). It exits 64 before any
launch attempt when any of these holds:

- `n` is not a positive integer;
- `tracker.backend` is not `github-issues`;
- `tracker.url` is not an `https://` url;
- `gh` is not on the trusted path;
- the read fails or times out;
- the answer's number, title or body is missing or malformed;
- its url is not exactly `<tracker.url>/<n>`;
- its title or body contains `TICKET>>>`.

Without `--ticket` nothing changes. To use it, have `gh` authenticated and on the
trusted path, and set `tracker.url` to the tracker's issues url
(`https://github.com/<owner>/<repo>/issues`).

CHANGED (report shape): the launch request carries `request.ticket` (`number`, `url`,
`block_sha256`, or `null`). A reader that compares a request binding field by field
must include it.

CHANGED (gate semantics): the lane contract (`dev_session.sh print-contract`, and the
descriptor's `prompt_preamble`) gains three instructions (#1011, #628):

- every part of a shell command must be allowed, one refused part ends the run, and one
  simple command per call is the safe default;
- write commit messages and pull-request text under `<state.dirname>/lane/` in the
  worktree, never stage that directory, and pass the files with `git commit -F` and
  `gh pr create --body-file`; put the verification result in the body before opening
  and report anything later in the final text, without editing or commenting on the
  pull request;
- undo worktree changes with `git restore`.

The "wait on anything" rule now says to poll with one simple check per call, not with
an until-loop. A launcher that compares the preamble with `print-contract` needs both
from the same kit revision.

CHANGED (config keys): the shipped `config/claude-lane-settings.json`, and the copy
`init.sh` seeds when none exists, now also allow `Bash(git restore:*)`. `init.sh` never
rewrites an existing profile. Add that entry to yours, or a lane that follows the new
contract has its restore denied and ends `failed`. The profile still grants no
`gh pr edit` and no `gh pr comment`.
