## kit_doctor, the reviewer eval and the triage engine run their remaining Git calls through the shared runner

CHANGED (engine CLI, gate semantics). Refresh `kit_doctor.py`, `review_eval.py` and
`lib/triage/` (`gate.py`, `recovery.py`, `storage.py`) together with a
`lib/subprocess_runner.py` that has `run_result` and `run_bytes`. They import them, so
an older runner beside them fails at import. `kit_doctor.py` now imports the runner at
start, so a partial copy that leaves it out stops the doctor too.

- `kit_doctor.py`'s Git calls behave as before: the same environment, an empty stdin,
  and exit code 1 for a Git that times out or cannot start. The stderr of those two
  cases is now the runner's message (`… timed out after Ns`, `… could not run: …`).
- `review_eval.py`'s commit check and preflight-blob copy are bounded at 30 seconds and
  drop every inherited `GIT_*` variable, so every Git call in `review_eval.py` now has a
  bound. A commit check Git cannot answer is a case-file error rather than a missing
  commit.
- The triage engine's sweep reads (`merge-base --is-ancestor`, `git show`) and its
  tracked-artifact check (`ls-files --error-unmatch`) are bounded at 30 seconds and drop
  every inherited `GIT_*` variable. A sweep read that cannot answer keeps the state
  held, as a failed read did. A tracked-artifact check that times out or cannot start
  now hard-stops the run, where a Git that could not start raised an uncaught
  `OSError`. A non-zero exit still reads as "not tracked", as before. The `ps`
  start-time fallback is bounded at 10 seconds.
