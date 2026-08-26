# Codex environment-capable launcher — live validation 2026-08-26

## Conclusion

The selected kit-owned wrapper launched the installed stable `codex exec` surface in a
synthetic headless lane after replacing hostile inherited lane identity. The wrapper's
child independently observed one worktree, Git repository, lane branch/base, state
root, and process before Codex received the prompt. The parent then bound those
observations to the launch request and did not report success until the Codex final
message was digested into the durable terminal receipt.

This is a trusted-client observation at the stamped client, synthetic commit, date,
and engine bytes below. It does not establish future-client behavior, the desktop app,
native subagent dispatch, app-server, cloud tasks, or a real adopter repository.

## Data boundary

An attempted probe whose synthetic history included the repository's scripts tree was
rejected by the execution approval layer before the launcher process started. The
accepted probe instead exposed a synthetic tracked worktree under `/private/tmp`
containing only a harmless README, gitignore, and config. The minimum copied launcher
engines remained untracked outside the lane worktree. No additional workspace source,
credentials, local config overlay, MCP file, or operator note entered the fixture.

## Stamped surfaces

- `codex --version` at synthetic revision
  `463bcfbd4790d715c7c0adc1103c981bf778d914` on 2026-08-26 printed
  `codex-cli 0.149.1`; the live run banner printed `OpenAI Codex v0.149.1`.
- The official OpenAI developer-command reference on 2026-08-26 described
  `codex exec` as stable and documented `--cd, -C` as setting the workspace root for
  the non-interactive task. Product documentation supplied the candidate surface; the
  receipt below supplied the behavioral evidence.
- `shasum -a 256 scripts/dev_session.sh scripts/launch_codex_lane.py
  /Users/topi/Coding/agentic-dev-kit/scripts/dev_session.sh
  /Users/topi/Coding/agentic-dev-kit/scripts/launch_codex_lane.py` at the same synthetic
  revision/date printed matching pairs:
  `2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba` for the
  descriptor issuer and
  `ff4ad587ea1c578b9db1f18e015a4d989e4ea25ca2dd1989a3c4c3358b246349` for the
  launcher.

## Launch request

The synthetic lane was issued with:

```text
DEVKIT_SESSIONS_DIR=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions \
  scripts/dev_session.sh new live --headless --runtime codex
```

The launcher then ran with deliberately foreign inherited values:

```text
PATH=/private/tmp/codex-launcher-synthetic-v6.et6sa9/hostile-bin:<normal trusted paths> \
DEVKIT_STATE_ROOT=/private/tmp/synthetic-foreign-state \
DEVKIT_ROOT=/private/tmp/synthetic-foreign-root \
DEVKIT_FOREIGN_LANE=must-not-survive \
GH_REPO=foreign/synthetic \
GIT_WORK_TREE=/private/tmp/synthetic-foreign-worktree \
GIT_CONFIG_COUNT=1 \
GIT_CONFIG_KEY_0=remote.origin.pushurl \
GIT_CONFIG_VALUE_0=/private/tmp/synthetic-foreign-origin \
python3 scripts/launch_codex_lane.py \
  --descriptor /private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live/launch-descriptor.json \
  --prompt-file /private/tmp/codex-launcher-synthetic-v6.et6sa9/prompt.txt
```

The task limited Codex to local read-only identity observation and prohibited edits,
commits, pushes, pull requests, browsing, and child agents.

## Durable binding

The completed receipt carried descriptor id
`8be7b55b-97ea-40dd-b17b-08e76c71c290` and these request digests. The separately
persisted rewrite seal bound the same descriptor id and descriptor digest before launch:

```text
descriptor_sha256=b96291fb27c60a7e712c845050d1a582cf836c92689a31e7a78704b58a9b4397
task_sha256=db9131543711f8876549da438274ca8662374b3347de1c329b6bfae00e389d64
combined_prompt_sha256=962e9da7b8e12aa27f38ced5cc93c8ca0dfd98e9eaab7e5fabd699cb9535657c
process_nonce_sha256=74ca1f2434b28b75233b0ec601a9c4a373a9fcb18387898948d4b11f0b70326f
configured_command=["/opt/homebrew/bin/codex","exec"]
```

The child constructed and durably recorded the following observations before `exec`:

```text
scope=live
worktree=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live/wt
git_top=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live/wt
session_dir=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live
state_root=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live/state
marker_state_root=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live/state
repo_root=/private/tmp/codex-launcher-synthetic-v6.et6sa9/repo
origin_url=/private/tmp/codex-launcher-synthetic-v6.et6sa9/origin.git
origin_push_url=/private/tmp/codex-launcher-synthetic-v6.et6sa9/origin.git
branch=lane/live
persisted_branch=lane/live
base=main
base_oid=463bcfbd4790d715c7c0adc1103c981bf778d914
lane_oid=463bcfbd4790d715c7c0adc1103c981bf778d914
merge_class=operator
DEVKIT_REFUSE_UNSANDBOXED_STATE=1
DEVKIT_ROOT=/private/tmp/codex-launcher-synthetic-v6.et6sa9/repo
DEVKIT_STATE_ROOT=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live/state
repository_overrides_present=[]
pwd_environment=/private/tmp/codex-launcher-synthetic-v6.et6sa9/sessions/live/wt
process_pid=25140
process_ppid=25103
process_session_id=25140
process_start_fingerprint=ps:Wed Aug 26 22:44:23 2026
```

The independently executing Codex session then reported the same physical directory,
Git top-level/common directory, origin fetch/push identity, branch, commit, marker, and
descriptor-owned environment. It reported the named Git repository overrides,
injected Git config keys, and `GH_REPO` absent; no repository override survived.
The inherited path began with a fake `git` that would create a marker and fail;
`test ! -e /private/tmp/codex-launcher-synthetic-v6.et6sa9/fake-git-ran && echo
fake-git-not-run` at synthetic
revision `463bcfbd4790d715c7c0adc1103c981bf778d914` on 2026-08-26 printed
`fake-git-not-run`, while the receipt bound `/opt/homebrew/bin/codex` as the resolved
config-owned command.

The terminal receipt recorded `returncode=0`, no signal or error, and final-message
digest `8d1ecda1bfe40ec44e018a7ccf23f108b234e489070ff05aff03a24ad9b9c467`.

## Cleanup and containment

- `git status --short` in the synthetic lane at revision
  `463bcfbd4790d715c7c0adc1103c981bf778d914` on 2026-08-26 returned no entries.
- The receipt-bound process audit
  `python3 -c '<os.kill(pid, 0) for the exact live-probe PID tuple>'` at the same
  revision/date printed `stopped:25103` and `stopped:25140` by taking the
  `ProcessLookupError` branch for the launcher and receipt-bound Codex process.
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
