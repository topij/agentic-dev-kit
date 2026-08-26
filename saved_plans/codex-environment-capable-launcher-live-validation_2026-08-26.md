# Codex environment-capable launcher — live validation 2026-08-26

## Conclusion

The selected kit-owned wrapper launched the installed stable `codex exec` surface in a
synthetic headless lane after replacing hostile inherited lane identity. The wrapper's
child independently observed one worktree, Git repository, lane branch/base, state
root, and process before Codex received the prompt. The parent then bound those
observations to the launch request and did not report success until the Codex final
message was digested into the durable terminal receipt.

This is one trusted-client observation at the stamped client, synthetic commit, date,
and engine bytes below. It does not establish future-client behavior, the desktop app,
native subagent dispatch, app-server, cloud tasks, or a real adopter repository.

## Data boundary

An attempted real-workspace probe was rejected by the execution approval layer before
the launcher process started because it would have sent repository and environment
metadata to an external service. The accepted probe instead used a synthetic repository
under `/private/tmp` containing only a harmless README, config, and the launcher
engines. No workspace source, credentials, local config overlay, MCP file, or operator
note entered that fixture.

## Stamped surfaces

- `codex --version` and the live run banner at synthetic revision
  `afcdd71e2e427bba348a5697e31351ecf08f1f9d` on 2026-08-26 reported
  `OpenAI Codex v0.149.1`.
- The official OpenAI developer-command reference on 2026-08-26 described
  `codex exec` as stable and documented `--cd, -C` as setting the workspace root for
  the non-interactive task. Product documentation supplied the candidate surface; the
  receipt below supplied the behavioral evidence.
- `shasum -a 256 scripts/dev_session.sh scripts/launch_codex_lane.py
  /Users/topi/Coding/agentic-dev-kit/scripts/dev_session.sh
  /Users/topi/Coding/agentic-dev-kit/scripts/launch_codex_lane.py` at the same synthetic
  revision/date printed matching pairs:
  `9ce3a64047f4b5f5377624686ef43abf1b1d7f6b5e8e70a537caab79a1d6f815` for the
  descriptor issuer and
  `6087fb00f4eec9a443fca41bf8a4f5e0fd32084148e786b6d9bd9cc6836f3a03` for the
  launcher.

## Launch request

The synthetic lane was issued with:

```text
DEVKIT_SESSIONS_DIR=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions \
  scripts/dev_session.sh new live --headless --runtime codex
```

The launcher then ran with deliberately foreign inherited values:

```text
DEVKIT_STATE_ROOT=/private/tmp/synthetic-foreign-state \
DEVKIT_ROOT=/private/tmp/synthetic-foreign-root \
DEVKIT_FOREIGN_LANE=must-not-survive \
GH_REPO=foreign/synthetic \
GIT_WORK_TREE=/private/tmp/synthetic-foreign-worktree \
python3 scripts/launch_codex_lane.py \
  --descriptor /private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live/launch-descriptor.json \
  --prompt-file /private/tmp/codex-launcher-synthetic-v2.Y9JBVY/prompt.txt
```

The task limited Codex to local read-only identity observation and prohibited edits,
commits, pushes, pull requests, browsing, and child agents.

## Durable binding

The completed receipt carried descriptor id
`8425aaf3-8f59-44c4-9cc7-f9874e27d39b` and these request digests:

```text
descriptor_sha256=eaf7a8d2d927d2009ae2c706a6ac1c06e721cd7282da906dac25c83d42d48a25
task_sha256=5c31a153281de5c6ac628000c7545e32b998765bdd11aeeb5f800b79410ce832
combined_prompt_sha256=408f8ec961647675b48577de0d8aa47f449515442ca66adf9a89f76483ba9d91
process_nonce_sha256=9c453d18e4a8179cb75e0bd2b8ab519de4e7b52e43477667bd8dd9c8bf6f954e
configured_command=["codex","exec"]
```

The child constructed and durably recorded the following observations before `exec`:

```text
scope=live
worktree=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live/wt
git_top=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live/wt
session_dir=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live
state_root=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live/state
marker_state_root=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live/state
repo_root=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/repo
origin_url=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/origin.git
branch=lane/live
persisted_branch=lane/live
base=main
base_oid=afcdd71e2e427bba348a5697e31351ecf08f1f9d
lane_oid=afcdd71e2e427bba348a5697e31351ecf08f1f9d
merge_class=operator
DEVKIT_REFUSE_UNSANDBOXED_STATE=1
DEVKIT_ROOT=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/repo
DEVKIT_STATE_ROOT=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live/state
repository_overrides_present=[]
pwd_environment=/private/tmp/codex-launcher-synthetic-v2.Y9JBVY/sessions/live/wt
process_pid=60441
process_ppid=60423
process_session_id=60441
process_start_fingerprint=ps:Wed Aug 26 21:36:46 2026
```

The independently executing Codex session then reported the same physical directory,
Git top-level/common directory, origin, branch, commit, marker, and descriptor-owned
environment. It reported the named Git repository overrides and `GH_REPO` absent; no
repository override survived.

The terminal receipt recorded `returncode=0`, no signal or error, and final-message
digest `475e433134cfa18f900960d95cc2cfeb8ffcb3b70ce623fc4febb93b406abe53`.

## Cleanup and containment

- `git status --short` in the synthetic lane at revision
  `afcdd71e2e427bba348a5697e31351ecf08f1f9d` on 2026-08-26 returned no entries.
- The receipt-bound process audit
  `python3 -c '<os.kill(pid, 0) for the exact live-probe PID tuple>'` at the same
  revision/date printed `stopped:60423`, `stopped:60441`, `stopped:60507`, and
  `stopped:61152` by taking the `ProcessLookupError` branch for the launcher, Codex,
  and its observed helper processes.
- The synthetic lane is removed after this record is written. Its temporary fixture is
  not an adopter artifact and supplies no authority after teardown.

## Limits carried forward

The supported claim is limited to the kit wrapper driving stable local `codex exec`.
The wrapper, rather than Codex itself, owns environment replacement, inherited-variable
removal, independent identity observation, one-shot authority, interruption handling,
and the descriptor/receipt chain. Model, reasoning effort, and Codex project permission
calibration remain outside this slice. The read-only task did not observe a write or an
approval transition, so it establishes no behavior for write permission, approval
prompts, refusal, or unattended write completion.
