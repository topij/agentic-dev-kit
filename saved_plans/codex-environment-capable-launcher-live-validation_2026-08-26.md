# Codex environment-capable launcher — live validation 2026-08-26

## Conclusion

The selected kit-owned wrapper launched the installed stable `codex exec` surface in a
synthetic headless lane after replacing hostile inherited lane identity. The wrapper's
child independently observed one worktree, Git repository, lane branch/base, state
root, and process before Codex received the prompt. The parent then bound those
observations to the launch request and did not report success until the Codex final
message and terminal receipt were durable.

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
  `250bd6f1515f7048b8d42a04b82d7a694d70e9e9` on 2026-08-26 reported
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
  `9cbf3c35c838ef7c9d2e3c793491170ea48d89834b4a4bad26b2f60733594399` for the
  launcher.

## Launch request

The synthetic lane was issued with:

```text
DEVKIT_SESSIONS_DIR=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions \
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
  --descriptor /private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live/launch-descriptor.json \
  --prompt-file /private/tmp/codex-launcher-synthetic.KKJ7QT/prompt.txt
```

The task limited Codex to local read-only identity observation and prohibited edits,
commits, pushes, pull requests, browsing, and child agents.

## Durable binding

The completed receipt carried descriptor id
`ab3afdc0-d523-4c22-9af7-ab91770d352c` and these request digests:

```text
descriptor_sha256=d875836ab17edb1fc2d48872890d4c6853fd03d18d96f6eca960e76be4fc5e7a
task_sha256=347e9bdb6e8a2d3ebd399e6f13df6c284d8f7a79f84a5f955031a51bf8bc61be
combined_prompt_sha256=0fbc676753ad3b16ad05fb37492f4c4af18d6821a0d842ce309e2c94a241a5a9
process_nonce_sha256=cad79cd050315e6f2ff5d87a3132e9b96ac7856ee842b9e168a78b75a61232b3
configured_command=["codex","exec"]
```

The child constructed and durably recorded the following observations before `exec`:

```text
scope=live
worktree=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live/wt
git_top=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live/wt
session_dir=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live
state_root=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live/state
marker_state_root=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live/state
repo_root=/private/tmp/codex-launcher-synthetic.KKJ7QT/repo
origin_url=/private/tmp/codex-launcher-synthetic.KKJ7QT/origin.git
branch=lane/live
persisted_branch=lane/live
base=main
base_oid=250bd6f1515f7048b8d42a04b82d7a694d70e9e9
lane_oid=250bd6f1515f7048b8d42a04b82d7a694d70e9e9
merge_class=operator
DEVKIT_REFUSE_UNSANDBOXED_STATE=1
DEVKIT_ROOT=/private/tmp/codex-launcher-synthetic.KKJ7QT/repo
DEVKIT_STATE_ROOT=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live/state
repository_overrides_present=[]
pwd_environment=/private/tmp/codex-launcher-synthetic.KKJ7QT/sessions/live/wt
process_pid=93788
process_ppid=93772
process_session_id=93788
process_start_fingerprint=ps:Wed Aug 26 20:56:26 2026
```

The independently executing Codex session then reported the same physical directory,
Git top-level/common directory, origin, branch, commit, marker, and descriptor-owned
environment. It observed `GH_REPO` absent and only `GIT_PAGER=cat` in the broader
`GIT_*` namespace; no Git repository override survived.

The terminal receipt recorded `returncode=0`, no signal or error, and final-message
digest `ab903f17398c0a737f986ea7f2393e2390229ab6ef167e21bc69057f952ab87d`.

## Cleanup and containment

- `git status --short` in the synthetic lane at revision
  `250bd6f1515f7048b8d42a04b82d7a694d70e9e9` on 2026-08-26 returned no entries.
- The receipt-bound process audit
  `python3 -c '<load receipt; os.kill(observed pid, 0)>' <receipt>` at the same
  revision/date printed `stopped:93788` by taking the `ProcessLookupError` branch.
- The synthetic lane is removed after this record is written. Its temporary fixture is
  not an adopter artifact and supplies no authority after teardown.

## Limits carried forward

The supported claim is limited to the kit wrapper driving stable local `codex exec`.
The wrapper, rather than Codex itself, owns environment replacement, inherited-variable
removal, independent identity observation, one-shot authority, interruption handling,
and the descriptor/receipt chain. Model, reasoning effort, and Codex project permission
calibration remain outside this slice.
