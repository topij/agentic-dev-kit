# Claude environment-capable launcher — live validation 2026-08-27

## Conclusion

The per-runtime kit-owned wrapper launched the installed Claude Code client through
`claude -p --output-format json` in a synthetic headless lane after replacing hostile
inherited lane identity. The wrapper's fork-only child independently observed one
worktree, Git repository, origin fetch/push identity, lane branch/base, state root,
and process before Claude received the prompt on stdin. The parent bound those
observations to the launch request — including the runtime and its three declared
transports — and did not report success until Claude's single JSON result object was
durable on the reserved final-message file and its extracted `result` text was
digested into the terminal receipt. Claude, executing as the exec'd observer process,
then reported the same identity from inside the lane, and the post-run lineage
observer found no nonce-bearing process.

This is a trusted-client observation at the stamped client, synthetic commit, date,
and engine bytes below, produced from a Claude Code session so that the runtime under
test is the one observed. It does not establish future-client behavior, native
subagent dispatch, a Claude remote session, a real adopter repository, or any writing
or approval behavior.

## Data boundary

The synthetic tracked worktree under `/private/tmp` held only a README, a gitignore, a
`config/dev-model.yaml` naming the absolute Claude binary, and a `.claude/settings.json`
carrying a read-only Bash allow-list. The minimum copied launcher engines
(`launch_lane.py`, `dev_session.sh`, `scripts/lib/`) sat untracked and gitignored
outside the lane worktree. No workspace source, credentials, local config overlay, MCP
file, or operator note entered the fixture. The launcher ran from an environment with
`ANTHROPIC_API_KEY` unset; the prompt sent to the service was the lane contract plus
the read-only observation task below, and the files Claude could read were the four
above.

## Stamped surfaces

- `claude --version` at synthetic revision
  `be8e1c5b43e92b53e0fc06ec1626e292167d82df` on 2026-08-27 printed
  `2.1.247 (Claude Code)`.
- Claude Code's published CLI reference on 2026-08-27 documents `-p`/`--print` for
  non-interactive use, `--output-format json`, the prompt read from stdin, and no
  working-directory flag; the earlier no-repository probe recorded in
  [`claude-environment-capable-launcher-design_2026-08-27.md`](claude-environment-capable-launcher-design_2026-08-27.md)
  showed the one-object `type=result` envelope. Documentation and that probe supplied
  the candidate surface; the receipt below supplied the behavioral evidence.
- `sha256` over the fixture's copied engines and the kit checkout's engines at the
  same synthetic revision/date printed matching pairs:
  `2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba` for
  `dev_session.sh` (the descriptor issuer, unchanged since the `#609` record) and
  `23afab475f51a9e827c810949bb78bd2d0589f3bed06041d92ba890ebca0501b` for
  `launch_lane.py`.

## Launch request

The synthetic lane was issued with:

```text
DEVKIT_SESSIONS_DIR=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions \
  scripts/dev_session.sh new live --headless --runtime claude
```

The fixture config declared
`claude_headless_command: ["/Users/topi/.local/bin/claude", -p]` — the user-local
install is outside the wrapper's trusted executable path, so the absolute binary is
named — with `claude_worktree_transport: process-cwd`, `claude_prompt_transport:
stdin`, and `claude_final_text_transport: json-stdout`.

The launcher then ran with deliberately foreign inherited values, the same set the
`#609` Codex record used:

```text
PATH=/private/tmp/claude-launcher-synthetic.n7zq3nen/hostile-bin:<normal caller path> \
DEVKIT_STATE_ROOT=/private/tmp/synthetic-foreign-state \
DEVKIT_ROOT=/private/tmp/synthetic-foreign-root \
DEVKIT_FOREIGN_LANE=must-not-survive \
GH_REPO=foreign/synthetic \
GIT_WORK_TREE=/private/tmp/synthetic-foreign-worktree \
GIT_CONFIG_COUNT=1 \
GIT_CONFIG_KEY_0=remote.origin.pushurl \
GIT_CONFIG_VALUE_0=/private/tmp/synthetic-foreign-origin \
GIT_OBJECT_DIRECTORY=/private/tmp/synthetic-foreign-objects \
GIT_SSH_COMMAND=/private/tmp/claude-launcher-synthetic.n7zq3nen/hostile-bin/git \
TEST_INHERITED_FD=512 \
python3 scripts/launch_lane.py \
  --descriptor /private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live/launch-descriptor.json \
  --prompt-file /private/tmp/claude-launcher-synthetic.n7zq3nen/prompt.txt
```

The caller opened descriptor 512 and lowered its soft descriptor limit below that
number before launch. The task limited Claude to local read-only identity observation
through the Bash and Read tools, told it the lane contract's pull-request clauses had
nothing to act on, and prohibited edits, commits, pushes, fetches, pull requests,
browsing, and sub-agents.

## Durable binding

The completed receipt carried descriptor id
`443f87b8-9a29-4dd9-83eb-76dd75c350fb` and these request digests. The separately
persisted rewrite seal bound the same descriptor id and descriptor digest before
launch:

```text
descriptor_sha256=3b7b868f7f06ba56b7bede26eff6f30a59149aac5073e4ed7ff99fe63e699c58
task_sha256=168217e8732b4956ecba0b9b4be66d255f95793430f825e3e0c2b9e651ce3559
combined_prompt_sha256=40843686591e37a72cf24c5c20a9acdc349bda575384bc523ec5c5dacb9a6c1e
process_nonce_sha256=702064985b7600188334297ed47eb6138e336827f5bf6d1aff60570f002378f3
configured_command=["/Users/topi/.local/share/claude/versions/2.1.247","-p"]
runtime=claude
transports={"final_text":"json-stdout","prompt":"stdin","worktree":"process-cwd"}
```

The child constructed and durably recorded the following observations before `exec`:

```text
scope=live
worktree=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live/wt
git_top=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live/wt
session_dir=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live
state_root=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live/state
marker_state_root=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live/state
repo_root=/private/tmp/claude-launcher-synthetic.n7zq3nen/repo
origin_url=/private/tmp/claude-launcher-synthetic.n7zq3nen/origin.git
origin_push_url=/private/tmp/claude-launcher-synthetic.n7zq3nen/origin.git
branch=lane/live
persisted_branch=lane/live
base=main
base_oid=be8e1c5b43e92b53e0fc06ec1626e292167d82df
lane_oid=be8e1c5b43e92b53e0fc06ec1626e292167d82df
merge_class=operator
DEVKIT_REFUSE_UNSANDBOXED_STATE=1
DEVKIT_ROOT=/private/tmp/claude-launcher-synthetic.n7zq3nen/repo
DEVKIT_STATE_ROOT=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live/state
repository_overrides_present=[]
pwd_environment=/private/tmp/claude-launcher-synthetic.n7zq3nen/sessions/live/wt
process_pid=96690
process_ppid=96657
process_session_id=96690
process_start_fingerprint=ps:Thu Aug 27 07:47:02 2026
```

The independently executing Claude session then answered with one JSON object whose
`result` reported the same physical directory and Git top-level, the common directory
`/private/tmp/claude-launcher-synthetic.n7zq3nen/repo/.git`, the same origin
fetch/push identity, branch `lane/live`, head
`be8e1c5b43e92b53e0fc06ec1626e292167d82df`, the marker's state root, and exactly the
three descriptor-owned `DEVKIT_*` values. It reported `GH_REPO` absent; in the `GIT_*`
namespace only `GIT_EDITOR=true`, which Claude Code sets for itself after the
wrapper's pre-exec observation (the Codex counterpart is `GIT_PAGER=cat`); the first
`PATH` entry `/bin`, the head of the trusted path rather than the hostile directory;
descriptor 512 absent from `ls /dev/fd`; its Bash shell's parent pid `96690`, the same
pid the child observer recorded for itself, so the runtime ran as the exec'd observer
without a PID change; an empty `git status --short`; and that the prompt it received
began with `LANE CONTRACT (binding):`.

The inherited path began with a fake `git` that would create a marker and fail;
`test ! -e /private/tmp/claude-launcher-synthetic.n7zq3nen/fake-git-ran` at the
synthetic revision on 2026-08-27 held, while the receipt bound
`/Users/topi/.local/share/claude/versions/2.1.247` as the resolved config-owned
command.

The reserved final-message file held one line, one JSON object, with `type=result`,
`subtype=success`, `is_error=false`, `num_turns=4`, `stop_reason=end_turn`, an empty
`permission_denials` list, and `modelUsage` naming `claude-opus-5`. The terminal
receipt recorded `returncode=0`, no signal or error,
`final_text_transport=json-stdout`, final-message (raw envelope) digest
`4e7ca5422b075d720f6bb90adccfae1706051add570adb07e47ac464844a03c7`, and
final-text (extracted `result`) digest
`76b5d0379a28b5e542fe68c438f23ef759fe58815e19abb949d264da01ada5fb`; recomputing
`sha256` over the envelope's `result` string reproduced the latter.

## Cleanup and containment

- `git status --short` in the synthetic lane at revision
  `be8e1c5b43e92b53e0fc06ec1626e292167d82df` on 2026-08-27 returned no entries.
- The receipt-bound process audit `python3 -c '<os.kill(pid, 0) for the receipt's
  pid and ppid>'` at the same revision/date took the `ProcessLookupError` branch for
  both, printing `stopped:96690` and `stopped:96657`.
- `ps eww -axo pid=,command=` filtered for `ADK_LAUNCH_PROCESS_NONCE=` at the same
  revision/date matched no line.
- The synthetic lane is removed after this record is written. Its temporary fixture is
  not an adopter artifact and supplies no authority after teardown.

## Limits carried forward

The supported claim is limited to the kit wrapper driving the stable local `claude -p`
surface with the three declared transports. The wrapper, rather than Claude itself,
owns environment replacement, inherited-variable removal, trusted executable lookup,
independent identity observation, one-shot authority, interruption handling, and the
descriptor/receipt chain.

Write and approval behavior was not observed: the read-only task performed no write
and reached no approval transition, so this record establishes nothing about write
permission, approval prompts, refusal, or unattended write completion (`#601`).

One Claude-specific observation is recorded here because it bears directly on that
next slice. Claude printed to stderr that it was ignoring the fixture's
`.claude/settings.json` `permissions.allow` entries because the workspace had not been
trusted, naming the interactive trust dialog or a `hasTrustDialogAccepted` entry for
the repository path in the user's Claude configuration as the remedies. A freshly
issued lane worktree is therefore an untrusted workspace to an unattended Claude
lane, and project-level permission rules do not reach it. The read-only commands ran
regardless and `permission_denials` was empty, so this run did not need the
allow-list; a writing lane will. Model and effort calibration (`#605`) and permission
policy (`#606`) remain outside this slice.
