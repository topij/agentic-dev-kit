# Claude writing lane — live validation 2026-08-27

## Conclusion

The per-runtime kit-owned wrapper launched the installed Claude Code client in a
synthetic headless lane under the config-declared approval policy and the wrapper's
trust route, and the lane performed a scoped write, committed, pushed, and opened a
ready pull request on a private synthetic GitHub repository. The wrapper's child
observed the exact argv it exec'd — including `--setting-sources ""`,
`--permission-mode acceptEdits`, and `--settings <cockpit-owned profile>` — before
the ready signal; the parent bound the declared policy, the profile path and digest,
and that argv into the request; and success was reported only after the runtime's own
`permission_denials` list was read back empty. The cockpit then resolved the lane's
pull request through `dev_session.sh pr-watch`, recorded a review receipt at the exact
head, was refused by `dev_session.sh merge` until the settle window had passed, and
merged through the same wrapper.

Two further lanes in the same fixture observed the denied transition live. A first
lane under `accept-edits` whose task asked for diagnostics the profile does not allow
completed every write class and still terminalized `failed`, with the refused Bash
calls preserved on the receipt. A control lane under `dont-ask` had its `Write`
refused, terminalized `failed`, and left a clean worktree.

This is a trusted-client observation at the stamped client, synthetic commits, date,
and engine bytes below, produced from a Claude Code session so that the runtime under
test is the one observed. It establishes nothing about Codex approval behaviour, a
future client, native subagent dispatch, a Claude remote session, a real adopter
repository, or any policy value other than the two declared here.

## Data boundary

The synthetic tracked repository held only a README, a gitignore, a `CLAUDE.md`
carrying one marker line, `config/dev-model.yaml` naming the absolute Claude binary
and the declared policy, a `config/claude-lane-settings.json` byte-identical to the
kit's shipped profile, and a hostile `.claude/settings.json` (an allow rule and a
`SessionStart` hook that would create `hook-branch-ran` in the worktree if the
branch's settings loaded). The copied engines (`dev_session.sh`, `launch_lane.py`,
`pr_watch.py`, `scripts/lib/`) sat gitignored under the fixture repository root,
outside every lane worktree, and were never pushed. The fixture git identity was
synthetic (`lane-fixture@example.invalid`). The launcher ran with `ANTHROPIC_API_KEY`
unset (OAuth); the prompts sent to the service were the lane contract plus the task
texts digested below; the files a lane could read were the tracked five above plus its
own note. The synthetic repository is private and remains so after this record: the
`gh` token in this session carries no `delete_repo` scope, so removing it is an
operator action, named under *Cleanup and containment*.

## Stamped surfaces

- `claude --version` at synthetic base `9ce532759c562081b02705927c1738a364b4654b` on
  2026-08-27 printed `2.1.247 (Claude Code)`.
- `sha256` over the fixture's copied engines and the kit checkout's engines on
  2026-08-27 printed matching pairs:
  `2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba` for
  `dev_session.sh` (the descriptor issuer, unchanged since the `#609` record) and
  `766b87e0ad95372575ff8138714fb67c76955177d161cc61612575708296c5a2` for
  `launch_lane.py` (this slice's engine bytes at the time of the runs).
- `sha256` over `config/claude-lane-settings.json` in the fixture and in the kit
  checkout on 2026-08-27 both printed
  `c7d6bb24209e7312e41f59b5c7a731c65d1a9554de2558140d036244f7eda2ea`; every receipt
  below binds that digest as `request.approval_policy.settings_profile_sha256`.
- The route-selection probes and their flags are in
  [`claude-writing-lane-approval-policy-design_2026-08-27.md`](claude-writing-lane-approval-policy-design_2026-08-27.md);
  documentation and those probes supplied the candidate surface, the receipts below
  supplied the behavioural evidence.

## Launch requests

Each lane was issued from the fixture repository root with
`DEVKIT_SESSIONS_DIR=/private/tmp/claude-writing-lane.DRcP8l/sessions
scripts/dev_session.sh new <scope> --headless --runtime claude` (`--merge-class self`
for `live` and `write`; the default operator class for `control`). The fixture config
declared `claude_headless_command: ["/Users/topi/.local/bin/claude", -p]`,
`claude_worktree_transport: process-cwd`, `claude_prompt_transport: stdin`,
`claude_final_text_transport: json-stdout`,
`claude_settings_profile: config/claude-lane-settings.json`, and
`claude_approval_policy: accept-edits` — rewritten to `dont-ask` for the control lane
only and restored afterwards. `codex_approval_policy: read-only` was declared and
never exercised.

Every launch ran with the same deliberately foreign inherited values:

```text
PATH=/private/tmp/claude-writing-lane.DRcP8l/hostile-bin:<normal caller path> \
DEVKIT_STATE_ROOT=/private/tmp/synthetic-foreign-state \
DEVKIT_ROOT=/private/tmp/synthetic-foreign-root \
DEVKIT_FOREIGN_LANE=must-not-survive \
GH_REPO=foreign/synthetic \
GIT_WORK_TREE=/private/tmp/synthetic-foreign-worktree \
GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.origin.pushurl \
GIT_CONFIG_VALUE_0=/private/tmp/synthetic-foreign-origin \
GIT_OBJECT_DIRECTORY=/private/tmp/synthetic-foreign-objects \
python3 scripts/launch_lane.py --descriptor <session>/launch-descriptor.json --prompt-file <task>
```

The `#611` fake-`git` shim was not repeated: the trusted-path replacement it evidenced
is unchanged engine code, and every receipt below binds the resolved
`configured_command` `["/Users/topi/.local/share/claude/versions/2.1.247", "-p"]`
while the child recorded `repository_overrides_present=[]` and exactly the three
descriptor-owned `DEVKIT_*` values.

## Lane `write` — the writing-lane record (completed)

Task digest `58cb5990514eba584db76fef9f53d6968dda7d67a5a596f4305b81ad18e90643`. The
task confined the lane to single `git` and `gh pr` commands, one `Write`, no merge,
no sub-agents, and told it that `gh pr checks` reporting no checks is terminal and that
`pr_watch.py` is absent from the worktree by design.

Durable binding, descriptor `6ced1839-a1da-45e4-b28c-8f699ada09ea`; the separately
persisted rewrite seal bound the same id and descriptor digest before launch:

```text
descriptor_sha256=bd98c6601f95f51f01d5c64573c63673cb6f9fa6b5f4ee8a2d5b24922d1bd2c9
task_sha256=58cb5990514eba584db76fef9f53d6968dda7d67a5a596f4305b81ad18e90643
combined_prompt_sha256=d9a9de30af4835d89ed8d4c84294e25dde1099db556d4ba7e8107d3779953c7a
process_nonce_sha256=4245f6c9c9e8a224e2b9541d37ec942192bcb173c1a28e5fdee5b4a8f7013582
configured_command=["/Users/topi/.local/share/claude/versions/2.1.247","-p"]
runtime=claude
transports={"final_text":"json-stdout","prompt":"stdin","worktree":"process-cwd"}
approval_policy.declared=accept-edits
approval_policy.argv=["--setting-sources","","--permission-mode","acceptEdits","--settings","/private/tmp/claude-writing-lane.DRcP8l/repo/config/claude-lane-settings.json"]
approval_policy.settings_profile_sha256=c7d6bb24209e7312e41f59b5c7a731c65d1a9554de2558140d036244f7eda2ea
```

The child constructed and durably recorded, before `exec` at `2026-08-27T08:40:29Z`:

```text
scope=write
worktree=/private/tmp/claude-writing-lane.DRcP8l/sessions/write/wt
git_top=/private/tmp/claude-writing-lane.DRcP8l/sessions/write/wt
state_root=/private/tmp/claude-writing-lane.DRcP8l/sessions/write/state
marker_state_root=/private/tmp/claude-writing-lane.DRcP8l/sessions/write/state
repo_root=/private/tmp/claude-writing-lane.DRcP8l/repo
origin_url=https://github.com/topij/adk-writing-lane-synthetic-20260827.git
origin_push_url=https://github.com/topij/adk-writing-lane-synthetic-20260827.git
branch=lane/write  persisted_branch=lane/write  base=main
base_oid=9ce532759c562081b02705927c1738a364b4654b
lane_oid=9ce532759c562081b02705927c1738a364b4654b
merge_class=self
DEVKIT_REFUSE_UNSANDBOXED_STATE=1
DEVKIT_ROOT=/private/tmp/claude-writing-lane.DRcP8l/repo
DEVKIT_STATE_ROOT=/private/tmp/claude-writing-lane.DRcP8l/sessions/write/state
repository_overrides_present=[]
argv=["/Users/topi/.local/share/claude/versions/2.1.247","-p","--setting-sources","","--permission-mode","acceptEdits","--settings","/private/tmp/claude-writing-lane.DRcP8l/repo/config/claude-lane-settings.json","--output-format","json"]
process_pid=73437  process_ppid=73396  process_session_id=73437
process_start_fingerprint=ps:Thu Aug 27 11:40:29 2026
```

The independently executing Claude session answered with one JSON object,
`type=result`, `subtype=success`, `is_error=false`, `permission_denials=[]`, whose
`result` reported: `git_top` and `branch` equal to the observation above;
`status_before_write=clean` (so no `hook-branch-ran` file existed — the branch's
`SessionStart` hook did not execute); `head=b10f159d5bfb7f7a4d929c48f5cbd4be16767cbb`
after `feat: add the lane note`; `pr_number=2`,
`pr_url=https://github.com/topij/adk-writing-lane-synthetic-20260827/pull/2`,
`pr_head=b10f159d5bfb7f7a4d929c48f5cbd4be16767cbb`, `pr_is_draft=false`;
`pr_checks` as `gh pr checks` exiting non-zero with no checks reported on the branch;
`claude_md_marker=not-seen` (the branch's `CLAUDE.md` did not reach the lane — the
route's declared trade-off, see the design record's C-probes);
`permission_denials=none`; `contract_first=yes`.

The terminal receipt recorded `status=completed`, `returncode=0`, no signal or error,
`final_text_transport=json-stdout`, `permission_denials=[]`, final-message (raw
envelope) digest `4d56c650822fdccd08fadf8cb084e7e7fc1732da98dde91938461866bbf0731f`
and final-text digest `b0be9ee36a35e03e458c4c2ce483c611ad9bb4d88d52286c9532d1d4902dc82c`;
recomputing `sha256` over the envelope bytes and over its `result` string on
2026-08-27 reproduced both.

Cockpit read-back on 2026-08-27, independent of the lane's report: `git ls-remote
--heads origin` listed `lane/write` at `b10f159d5bfb7f7a4d929c48f5cbd4be16767cbb`;
`gh pr view 2 --json …` returned `state=OPEN`, `isDraft=false`, `baseRefName=main`,
`headRefName=lane/write`, `headRefOid=b10f159d…`, `isCrossRepository=false`; the lane
worktree's `git status --short` was empty and `notes/lane-note.md` held exactly the two
requested lines.

### Cockpit review and merge through the lane wrappers

- `dev_session.sh pr-watch write --json` at head `b10f159d…` on 2026-08-27 first
  reported `converged=true`, `mergeable=false`, `review_evidence.valid=false`,
  `merge_blockers=["check rollup has not settled for current head (stable 1.1m of 3m)"]`.
- `dev_session.sh pr-watch write --record-review fallback:claude --lenses correctness
  --head b10f159d5bfb7f7a4d929c48f5cbd4be16767cbb`, after the cockpit read the one-file
  diff, printed the receipt acknowledgement and the one-lens caveat the engine attaches.
- The next poll reported `review_evidence.valid=true`, `route=receipt`,
  `source=fallback:claude`, `head=b10f159d…`, `lenses=[correctness]`, still
  `mergeable=false` with the settle blocker at `stable 2.0m of 3m`;
  `dev_session.sh merge write` refused with "PR #2 is not green, review-clean, and
  merge-ready; run pr-watch to convergence first".
- The poll after the window reported `rollup_settled=true`, `merge_blockers=[]`,
  `mergeable=true`; `dev_session.sh merge write` then exited 0, and `gh pr view 2`
  returned `state=MERGED`, `mergedAt=2026-08-27T08:45:10Z`,
  `mergeCommit=ee345ed9d51db242e62b24e266a04d0cb15cfed9`; `git ls-remote --heads
  origin` no longer listed `lane/write`, and `origin/main` was `ee345ed feat: add the
  lane note (#2)`.

The merge is a cockpit action under the lane's persisted self-merge class, gated on
the engine's `mergeable`; the lane itself never attempted it.

## Lane `live` — every write class, then `failed` on denied diagnostics

Task digest `0c749218cb472f3f032cd80976a984295d125c14e7fb7b6b2fa80b4c58eb07bc`. This
earlier task also asked the lane for `pwd -P`, `printf … | cut`, `env | grep
^DEVKIT_`, and `printenv`, and combined its first three commands with `;` — none of
which the shipped profile allows.

Descriptor `3740b59a-1c78-4e82-9559-cb3b583fc151`;
`descriptor_sha256=5c98d9e0eb6be4d04ae77f326c818e9a3fdc685ae6689201828c0685201e4811`,
`combined_prompt_sha256=cab18340bc0fdc943be08bc7516ecdfff8af8a72673b89364e76e450d3f7c8ee`,
`process_nonce_sha256=860e132c8ce58ba9d3e9d7f06dc9e3af33d511add8a82f26869efe033b47b0a4`,
the same `approval_policy` block as `write`, child `pid=58543 ppid=58516`
`start_fingerprint=ps:Thu Aug 27 11:37:23 2026`, observed at `2026-08-27T08:37:24Z`.

The runtime's envelope was `subtype=success`, `is_error=false`, and its
`permission_denials` list named, in order, the `Bash` calls
`git branch --show-current; git rev-parse --show-toplevel; pwd -P`, `pwd -P`,
`printf %s "$PATH" | cut -d: -f1`, `env | grep ^DEVKIT_`, `printenv PATH`, and
`printenv GH_REPO`. The lane continued past each refusal and its `result` reported
`head=5ae642af091ed018fb3251b50056a9c6e11f342c`, `pr_number=1`,
`pr_is_draft=false`, `hook_branch_marker=absent`, `claude_md_marker=not-seen`,
`contract_first=yes`, and `unavailable-denied` for the path and environment fields.
Cockpit read-back listed `lane/live` at `5ae642af…` and pull request #1 open on that
head.

The terminal receipt recorded `status=failed`, `returncode=0`, `error="runtime
reported permission denials under declared policy accept-edits"`,
`final_text_sha256=null`, final-message digest
`c3821bc8d230be9e83b72bc24e20f8b44f56bc87c8eb22216dd4a74e6df59a6e` (recomputed on
2026-08-27), and the denial list above verbatim under `terminal.permission_denials`.

What this run establishes: the compound and the diagnostic commands were refused with
no prompt and no operator, exactly as `-p` mode denies; the wrapper read the refusal
out of a `success` envelope and refused to call the lane `completed`; and the lane's
writes — commit, push, pull request — exist on the forge regardless. A `failed` receipt
is the policy verdict, not a claim that nothing was written.

## Lane `control` — `dont-ask`, one refused `Write`

Task digest `088309a89ac923867a46d56cfc694eaa8e40d924064ee49ebdf2e57c7e55cf26`: create
`notes/control.md` with `Write`, then `git status --short`, nothing else.

Descriptor `e2271851-0687-471e-94f6-b39ce45a2f74`;
`descriptor_sha256=0133721cfa3ae021c9de9fb88a0368b2efa55ab3e6933edd32ad8da4761802ce`,
`combined_prompt_sha256=565f6b8f1d5c5cd280afceca8e1c13ab785b3eb425dbe41946afe2a6b607ab5a`,
`process_nonce_sha256=0f217f77352de961892d44c77a3fdc18c2331fc712e38ebda4c9e636264dcc7a`;
`approval_policy.declared=dont-ask` with argv
`["--setting-sources","","--permission-mode","dontAsk","--settings","…/config/claude-lane-settings.json"]`
and the same profile digest; child `pid=78492 ppid=78454`
`start_fingerprint=ps:Thu Aug 27 11:41:30 2026`, observed at `2026-08-27T08:41:30Z`.

The envelope was `subtype=success`, `is_error=false`, with one `permission_denials`
entry: `tool_name=Write`,
`file_path=/private/tmp/claude-writing-lane.DRcP8l/sessions/control/wt/notes/control.md`.
The `result` reported `write_result=denied`, `git_status=clean`, `contract_first=yes`.
The terminal receipt recorded `status=failed`, `returncode=0`, `error="runtime
reported permission denials under declared policy dont-ask"`,
`final_text_sha256=null`, final-message digest
`db84273eb587e871506600a622fdce22c346aa4e9a1abb02ce531b1066091a4e`. The cockpit's
`git status --short` in the control worktree on 2026-08-27 returned no entries.

## Cleanup and containment

- The receipt-bound process audit `python3 -c '<os.kill(pid, 0) for each receipt's
  pid and ppid>'` on 2026-08-27 took the `ProcessLookupError` branch for every pair,
  printing `stopped` for `58543`, `58516`, `73437`, `73396`, `78492`, and `78454`.
- `ps eww -axo pid=,command= | grep -v grep | grep -c "ADK_LAUNCH_PROCESS_NONCE="` on
  2026-08-27 printed `0`.
- `git status --short` in the `write` and `control` lane worktrees on 2026-08-27
  returned no entries; the `live` worktree was clean at its committed head.
- After this record was written, pull request #1 was closed from the cockpit, the
  three lane sessions were removed with `dev_session.sh rm`, and the fixture directory
  was deleted. The private synthetic repository
  `topij/adk-writing-lane-synthetic-20260827` remains until the operator deletes it;
  it holds the seed commit, the squash-merged lane note, and the two pull requests, and
  supplies no authority.

## Limits carried forward

The supported claim is limited to the kit wrapper driving stable local `claude -p` at
the stamped client with the two declared Claude policy values and the shipped profile.
The wrapper, not Claude, owns the trust route, the argv, the request binding, the
denial read-back, and the receipt.

- **Codex is unobserved.** `codex_approval_policy` is validated and passed as
  `--sandbox <value>`; whether Codex refuses, prompts, or proceeds under either value,
  and whether `last-message-file` can surface a refusal at all, is the Codex record's
  to establish. The shipped Codex default stays `read-only` until then.
- **Project instructions do not reach a Claude lane on this route.** `CLAUDE.md`
  discovery follows the `project` setting source; with `--setting-sources ""` the lane
  saw neither the branch's settings nor its `CLAUDE.md`. The lane contract preamble the
  wrapper prepends is the binding project-level text. Re-injecting a cockpit-owned
  instruction file is a separate decision.
- **Project hooks did not execute** in the untrusted worktree under this route
  (`hook-branch-ran` absent in every lane; `status_before_write=clean`). Under the
  default sources the design record's P1 probe observed the opposite; the difference
  is the route, not the trust state.
- **The profile's allow-list is the minimum for the write classes observed**, and
  the `live` lane shows what it excludes: compound commands and shell diagnostics.
  Widening it is repository policy (`#606`), not launcher behaviour.
- **Model and effort calibration** (`#605`) remain outside this slice; the envelopes
  named the models the client selected without any lane-side choice.
