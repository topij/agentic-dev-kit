# Codex environment-capable launcher — live validation 2026-08-26

## Conclusion

The selected kit-owned wrapper launched the installed stable `codex exec` surface in a
synthetic headless lane after replacing hostile inherited lane identity. The wrapper's
child independently observed one worktree, Git repository, lane branch/base, state
root, and process before Codex received the prompt. The parent then bound those
observations to the launch request and did not report success until the Codex final
message was digested into the durable terminal receipt. The runtime reported the
explicitly inherited caller descriptor closed, and the post-run lineage observer found
no nonce-bearing detached process.

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
  `baca3b8d5cf76f10509f591db767ffce56e694a5` on 2026-08-26 printed
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
  `7c987567ff56d5f58312122fd1dcb5a167465eddd59ef1ca8b961a26b64f9895` for the
  launcher.

## Launch request

The synthetic lane was issued with:

```text
DEVKIT_SESSIONS_DIR=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions \
  scripts/dev_session.sh new live --headless --runtime codex
```

The launcher then ran with deliberately foreign inherited values:

```text
PATH=/private/tmp/codex-launcher-synthetic-v9.alsbIk/hostile-bin:<normal trusted paths> \
DEVKIT_STATE_ROOT=/private/tmp/synthetic-foreign-state \
DEVKIT_ROOT=/private/tmp/synthetic-foreign-root \
DEVKIT_FOREIGN_LANE=must-not-survive \
GH_REPO=foreign/synthetic \
GIT_WORK_TREE=/private/tmp/synthetic-foreign-worktree \
GIT_CONFIG_COUNT=1 \
GIT_CONFIG_KEY_0=remote.origin.pushurl \
GIT_CONFIG_VALUE_0=/private/tmp/synthetic-foreign-origin \
GIT_OBJECT_DIRECTORY=/private/tmp/synthetic-foreign-objects \
GIT_SSH_COMMAND=/private/tmp/codex-launcher-synthetic-v9.alsbIk/hostile-bin/git \
TEST_INHERITED_FD=512 \
python3 scripts/launch_codex_lane.py \
  --descriptor /private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live/launch-descriptor.json \
  --prompt-file /private/tmp/codex-launcher-synthetic-v9.alsbIk/prompt.txt
```

The task limited Codex to local read-only identity observation and prohibited edits,
commits, pushes, pull requests, browsing, and child agents.

## Durable binding

The completed receipt carried descriptor id
`64cea492-ac2c-4554-9f46-ea9a4e03e9dd` and these request digests. The separately
persisted rewrite seal bound the same descriptor id and descriptor digest before launch:

```text
descriptor_sha256=bddceb87f69bbafd5b4c0a5a735b8ecc84cd0d77123a8ce33e0cd5bcd13af278
task_sha256=d4f2e03271ecac207aeebf549a0e0e910e24cb709aeac39df3de4e5ef22713e1
combined_prompt_sha256=36becfd298a17009d05f932ba09cb4bccec61ad9224ef5721305b72395d4b982
process_nonce_sha256=d1071facb42c6c0997dbb930d532d02ce901eae483fba3dbeb1a5248c6185753
configured_command=["/opt/homebrew/bin/codex","exec"]
```

The child constructed and durably recorded the following observations before `exec`:

```text
scope=live
worktree=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live/wt
git_top=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live/wt
session_dir=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live
state_root=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live/state
marker_state_root=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live/state
repo_root=/private/tmp/codex-launcher-synthetic-v9.alsbIk/repo
origin_url=/private/tmp/codex-launcher-synthetic-v9.alsbIk/origin.git
origin_push_url=/private/tmp/codex-launcher-synthetic-v9.alsbIk/origin.git
branch=lane/live
persisted_branch=lane/live
base=main
base_oid=baca3b8d5cf76f10509f591db767ffce56e694a5
lane_oid=baca3b8d5cf76f10509f591db767ffce56e694a5
merge_class=operator
DEVKIT_REFUSE_UNSANDBOXED_STATE=1
DEVKIT_ROOT=/private/tmp/codex-launcher-synthetic-v9.alsbIk/repo
DEVKIT_STATE_ROOT=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live/state
repository_overrides_present=[]
pwd_environment=/private/tmp/codex-launcher-synthetic-v9.alsbIk/sessions/live/wt
process_pid=76388
process_ppid=76357
process_session_id=76388
process_start_fingerprint=ps:Wed Aug 26 23:59:46 2026
```

The independently executing Codex session then reported the same physical directory,
Git top-level/common directory, origin fetch/push identity, branch, commit, marker, and
descriptor-owned environment. It reported the named Git repository overrides,
injected Git config keys, object-directory and transport overrides, and `GH_REPO`
absent; no inherited repository override survived. Codex itself added `GIT_PAGER=cat`
after the wrapper's pre-exec observation. The caller opened descriptor 512 and lowered
its soft descriptor limit below that number before launch; Codex reported
`TEST_INHERITED_FD=512` but independently found descriptor 512 closed.

The inherited path began with a fake `git` that would create a marker and fail;
`test ! -e /private/tmp/codex-launcher-synthetic-v9.alsbIk/fake-git-ran && echo
fake-git-not-run` at synthetic
revision `baca3b8d5cf76f10509f591db767ffce56e694a5` on 2026-08-26 printed
`fake-git-not-run`, while the receipt bound `/opt/homebrew/bin/codex` as the resolved
config-owned command.

The terminal receipt recorded `returncode=0`, no signal or error, and final-message
digest `cadf90a567e8aadb93e530546276773fe91923792f26fe51aefb593183f4b2bc`.

## Cleanup and containment

- `git status --short` in the synthetic lane at revision
  `baca3b8d5cf76f10509f591db767ffce56e694a5` on 2026-08-26 returned no entries.
- The receipt-bound process audit
  `python3 -c '<os.kill(pid, 0) for the exact live-probe PID tuple>'` at the same
  revision/date took the `ProcessLookupError` branch for the launcher and receipt-bound
  Codex process, printing `stopped:76357` and `stopped:76388`. The launch-nonce observer
  printed `lineage {}`.
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
