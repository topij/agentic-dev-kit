# Runtime smoke — live record — 2026-10-02

The stamped run of the on-demand runtime smoke runner (#879, Phase 6 items 7 and 8),
and what the runs before it taught the runner. Every claim here is an observation at
the clients, revisions and date it names, not a guarantee for another client, account or
machine. None promotes a parity-matrix capability: a smoke record is an observation, not
a promotion bundle (`docs/agentic-dev-kit/live-validation-evidence.md`, *On-demand smoke
records*).

## The stamped run

The runner wrote [`record.md`](runtime-smoke-evidence_2026-10-02/record.md) and
[`record.json`](runtime-smoke-evidence_2026-10-02/record.json) at kit revision
`c3f98666fe82e117ca602fdf92d6a5bc53ee1258`, started 2026-10-02T11:32:40Z and finished
11:37:33Z UTC. It was started as `uv run scripts/runtime_smoke.py` with these arguments,
which the record keeps as given beside its interpreter, operator paths replaced by the
runner's placeholders:

```text
--work-root <work-root> --out <out> \
  --codex-bin /opt/homebrew/bin/codex --codex-version 0.153.4 --codex-home <codex-home> \
  --claude-bin ~/.local/bin/claude --claude-version 2.1.287 \
  --claude-config-dir <claude-config> \
  --allow-codex-project-trust --allow-codex-hook-trust-bypass
```

It exited 0, and every row passed: `codex.instructions`, `codex.skills`,
`codex.session_start`, `codex.post_tool_use`, `codex.review`, `codex.panel`,
`codex.lane`, `claude.instructions`, `claude.commands`, `claude.session_start`,
`claude.post_tool_use`, `claude.review`, `claude.panel` and `claude.lane`. Each row's
evidence and the session fields read from the runtime's own artifacts are in
`record.json`.

The clients, as the pinned binary reports itself and as each row's own artifacts report
the runtime that executed:

- **Codex:** `/opt/homebrew/bin/codex`, a link into the Homebrew cask, printed
  `codex-cli 0.153.4`; every Codex row's rollout `session_meta.cli_version` read
  `0.153.4`.
- **Claude Code:** `~/.local/bin/claude` printed `2.1.287 (Claude Code)`; every Claude
  row's transcript `version` read `2.1.287`.
- **The lanes** ran the command the launcher resolves on its own trusted path:
  `/opt/homebrew/bin/codex` and `/opt/homebrew/bin/claude`. Each lane row's
  `configured_command_realpath` names the file that ran, the same file the pinned path
  resolves to: the cask's `codex`, and `~/.local/share/claude/versions/2.1.287`, which
  `/opt/homebrew/bin/claude` reaches through `~/.local/bin/claude`.
- **Not exercised:** the ChatGPT app bundles its own Codex, which printed
  `codex-cli 0.159.2` (`/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex
  --version` on 2026-10-02). The lane launcher resolves `codex` on its fixed trusted
  path to the Homebrew binary, so a run pinned to the app's binary would fail its lane
  row on the executing version, by design.

## Isolation, credentials and trust

- Each runtime ran under an isolated home the operator created and logged in to on
  2026-10-02: Codex with a ChatGPT login (`codex login status`: `Logged in using
  ChatGPT`), Claude with a claude.ai login (`claude auth status`: `authMethod`
  `claude.ai`). The runner refuses the operator's own homes.
- For the Codex hook probe alone, and per invocation, the operator authorized
  `--dangerously-bypass-hook-trust` and a `-c` override trusting the fixture path
  (`--allow-codex-hook-trust-bypass`, `--allow-codex-project-trust`). No other session
  ran with either.
- The runs left the operator's own settings as they were. For runs 1 to 5,
  `shasum -a 256 ~/.codex/config.toml` at 2026-10-02T10:27:25Z, after run 5 ended,
  printed a value beginning `0227cc926633727a`, as did the session's first reading that
  day, taken before it ran any client command. That file was rewritten between runs 5
  and 6, while no smoke run was running, so a hash cannot speak for run 6; instead
  `grep -c adk-smoke` over `~/.codex/config.toml` and over `~/.claude.json` printed 0
  for each at 2026-10-02T11:32:35Z, before run 6, and again at 11:37:51Z, after it.

## Observations

1. **#802, in an isolated home.** No `codex exec` here wrote a `config.toml` into the
   isolated home, so none wrote a trusted-project entry there. `ls
   <codex-home>/config.toml` found no file at 2026-10-02T10:14:53Z, after every `codex
   exec` session of runs 1 to 3 had ended (run 3's Claude rows were still running), at
   10:27:25Z, after run 5, and at 11:37:51Z, after run 6. Runs 2 to 6 each passed a
   per-invocation project-trust override. Each record's own observation, which the runner
   reads from that file, lists no added project or hook-state entry. #802 saw the
   entries under the operator's own home, from `codex exec --ignore-user-config
   --ephemeral`, and leaves open whether the CLI or the desktop app's service writes
   them. Under an isolated home, with the flags these records show, the CLI wrote no
   `config.toml` at all: that narrows the question without settling it, and says nothing
   of trust Codex might keep anywhere else.
2. **Codex trusts a project's hooks at two layers.** With the fixture not a trusted
   project, `--dangerously-bypass-hook-trust` alone produced output from neither hook
   (run 1). With a per-invocation project-trust override as well, both ran and their
   output reached the session (runs 2 to 6). #802's description of a trusted path
   loading a project's config and hooks is consistent with that; these runs did not
   exercise persisted trust.
3. **Where Codex 0.153.4 puts injected context.** Under the isolated home, AGENTS.md
   arrived as `state.agents_md` in a `world_state` snapshot, byte-identical to the
   fixture's file. A `codex exec` rollout from the same client version started from the
   desktop app under the operator's own home, read on 2026-10-02 and not retained,
   carried it as a `# AGENTS.md instructions for` user message instead. The PostToolUse
   warning was written between the shell call and its output. `codex exec review` wrote a
   parent session carrying `EnteredReviewMode` and `ExitedReviewMode` items, and a child
   session whose `session_meta.source` is `{"subagent": "review"}`; the reviewer's compute
   is in that child's `turn_context`, which in run 6 read `gpt-6-astra`, the isolated
   home's default model, at `low`, the configured cheap tier the runner passes as
   `-c model_reasoning_effort`.
4. **Claude applies a lens's effort only on the documented route.** Launched as
   `claude -p --agent <lens>` (run 1), each lens ran the definition's model,
   `claude-sonnet-5-5`, at effort `medium` rather than the definition's `high`. Delegated
   from a parent session to the agent named after the lens, the route
   `fallback-review-panel.md` documents, each ran `claude-sonnet-5-5` at `high` (runs 2
   to 6). The parent transcribed the rendered lens prompt into its Agent call; the
   runner compared the subagent's first prompt with it, both trimmed of surrounding
   whitespace, and found them equal. That transcription is the inline hand-off #643 is
   about.
5. **Claude in an untrusted workspace.** Under `-p`, Claude ignored the project's
   `permissions.allow` entries with a stderr notice that the workspace was not trusted,
   and still ran the project's hooks.
6. **The configured Claude review command** ran as a local command: the transcript
   records the literal `/code-review` and a `local_command` entry, and in run 6 the
   review ran in a `general-purpose` subagent on `claude-opus-5-5` at `medium`.

## The runs before the stamped one

The stamped run is run 6. The runs before it were full live runs at earlier revisions of
the runner, against the same clients and isolated homes.

- **Run 1,** at `7b209d7`, 2026-10-02T09:50:51Z to 09:54:48Z, with the hook-trust bypass
  only. Its record is retained as historical evidence in
  [`run1-7b209d7/`](runtime-smoke-evidence_2026-10-02/run1-7b209d7/record.md). It failed
  `codex.instructions`, `codex.review`, `claude.review` and `claude.panel` for the
  runner's reasons, which `5505edd` fixed: the `world_state` shape, review mode as
  completed items, the `local_command` shape, and the `--agent` route (observation 4).
  Its two Codex hook rows recorded no hook output (observation 2); their reason text
  said the hooks ran, which nothing showed, and `5505edd` corrected it.
- **Run 2,** at `5505edd`, 10:05:39Z to 10:09:58Z, with both trust layers. Every row
  passed except `codex.post_tool_use`, whose check wanted the warning after the tool
  output (observation 3); `67b96dd` anchors it on the call instead.
- **Run 3,** at `67b96dd`, 10:10:27Z to 10:15:22Z, with both trust layers. Every row
  passed.
- **Run 4,** at `155e2b5`, 10:15:26Z to 10:19:48Z, with both trust layers. Every row
  passed. Its record left the native Codex reviewer's model and effort null: they live in
  the review's child session, which `64526e1` reads. It is not retained; run 5 supersedes
  it.
- **Run 5,** at `64526e1`, 10:21:56Z to 10:27:12Z, with both trust layers. Every row
  passed, and it was the stamped run until review tightened the runner (`b22354c`,
  `24570a8`): `claude.instructions` now requires AGENTS.md to load as CLAUDE.md's import,
  and `claude.post_tool_use` requires the hook's warning after the call whose result
  carries the nonce URL. Its record's invocation line begins `uv run`, which that runner
  wrote without being able to observe how it was started; run 6's record keeps the
  arguments as given and the interpreter. Run 5's record is retained in
  [`run5-64526e1/`](runtime-smoke-evidence_2026-10-02/run5-64526e1/record.md).

Runs 2 and 3 are not retained. Their records kept a Claude stderr excerpt cut before
redaction, so part of the operator's scratchpad path survived, account name included;
`155e2b5` bounds strings only after redaction. Run 1's record predates that field.
`grep -c` for `/Users/`, `-Users-`, `/private/tmp/claude-502` and the account name over
the `record.json` and `record.md` of runs 1, 5 and 6 printed 0 for each at
2026-10-02T11:38:45Z.

## Not established

- Effort's effect. These rows read the applied model and effort, not what effort changed.
- Interactive surfaces: the Codex TUI and desktop hook views, and Claude's trust dialog.
- Persisted trust. Every trust here was per invocation, in an isolated home.
- A lane's compute. The launcher carries no model or effort; each lane ran its home's
  defaults, which the record's lane rows show.
- The runner's interrupt and abort paths against live clients. Exit 4, and the stop of
  every client it started, were exercised with the fake clients of
  `scripts/tests/test_runtime_smoke.py` only.
- Another client version, account or machine.
