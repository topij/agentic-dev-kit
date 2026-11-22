## The reviewer eval and the triage engine run Git through the shared subprocess runner

CHANGED (engine CLI). Refresh `review_eval.py`, `lib/triage/model.py` and
`lib/triage/recovery.py` together with a `lib/subprocess_runner.py` at or after the
one that added `without_git_environment` and the `CommandError` family. All three now
import it, so an older runner beside them fails at import.

`review_eval.py` kills a Git call after 30 seconds, the fetch into a case's isolated
tree after 300, and a `panel_prompt.py` render after 120. Before, none had a bound. A
timeout is a run error like any other failure there. The messages for a Git or engine
call that fails are unchanged.

Every Git call in `review_eval.py`, the triage engine's protected-ref read
(`git_output`), and the reads that look for a recovered run's sweep commit no longer
inherit any `GIT_*` variable. An inherited `GIT_DIR` from a hook used to send them to
another repository. In recovery, the sweep was then never found and the state stayed
held. Because every `GIT_*` name is dropped, configuration passed through the
environment (`GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`, `GIT_CONFIG_GLOBAL`,
`GIT_SSH_COMMAND` and the like) no longer reaches these calls either; set it in a Git
config file instead. The triage engine's repository-identity reads keep their own
narrower filter, which keeps `GIT_CONFIG_*`, and are unchanged.
