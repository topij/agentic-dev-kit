# Phase 5 D — PHASE5-D-FRESH-CONTEXT-01 approval packet

**Prepared for approval. Nothing below has been approved or executed.** Two preparation
probes ran while this was drafted, and they are preparation evidence only. Two fresh
subagents checked successive drafts, each read-only in the kit. The second one built a
miniature of this design and drove the engines through it. Their corrections are folded
in, and *Preparation check* at the end lists them.

## What the route requires

The D proposal's row (`phase5-d-proposal_2026-09-21.md`, *Subsequent D packages*):

> **D-FRESH-CONTEXT** — Fresh Sol/medium Codex context in the approved D checkout with
> only the native skill invocation and task scope. Bind client/version/cwd/config/
> instructions. No inherited analysis or prompt that supplies the expected route.
> *Acceptance:* Observable discovery of adapter/shared workflow and merged config, chosen
> engine mode and actual behavior. If client trust changes are necessary, first bind their
> exact effect and guarded restoration; do not reuse C's leftover profile state as
> approval.

The Stage A ledger (`phase5-stage-a-routes_2026-09-18.md`, *Systemize fresh-client context
discovery*) marks it **Required to exercise**: "Approved fresh Codex context must locate
runtime adapter/shared workflow and effective config without inherited analysis; retain
prompt, task/client/config identity and observable chosen route."

RECOVERY's Stage 2 run P does not discharge it. P used Claude, and its prompt named the
workflow and the engine arguments, which is why that packet said "This is not
D-FRESH-CONTEXT".

**Relation to the post-dispatch decision.** On 2026-09-24 the operator deferred RECOVERY's
post-dispatch rerun until #786 ships
(`state/review-evidence/phase5-d-systemize-recovery-01/DECISION-post-dispatch-20260924.md`).
That record left bundling the rerun with this row open. **This packet does not bundle
them.**
- Test mode reaches every observation this row names without a tracker write.
- Waiting for #786 would hold an independent row on an unrelated fix.
- **The isolation here is not enough for that rerun.** The rerun needs an agent that
  cannot read the harness (`docs/kit-handoff.md`, latest block), and here the agent can
  read the fake and more (see *Readable surfaces*). The rerun can reuse the client
  isolation and the shell fix, but it needs its own answer to readability.

## Grounding reads

Everything here was read in `/Users/topi/Coding/agentic-dev-kit` at
`1cc86cd90b5a706c07ef10b7d3941a41085c6087` on 2026-09-24, unless a line says otherwise.

**Kit.**

- The adapter, `.agents/skills/post-merge-systemize/SKILL.md`, says to read the shared
  workflow completely and to treat the argument as entry-point keywords.
- The workflow's *Entry points* accept `backfill` and `test`. Test mode may write only the
  derived cache, digest, report, heartbeat state and an optional `[TEST]` notification.
  It may write no branch, commit, pull request, friction-log entry or tracker item.
  Non-interactive runs never wait for input. The final output is prefixed `[TEST]` in
  test mode (line 472).
- **Preflight needs a forge read of the agent's own choosing.**
  - The *Forge merged-PR read* capability is required: "Prove authenticated access by
    reading the target repository and a bounded merged-PR page."
  - The workflow also says "Finish preflight before writing a heartbeat, cache, or
    report".
  - The fetch engine runs after heartbeat `start`, so it cannot serve as that proof.
  - Capabilities are classed `ready`, `degraded` or `stop`. A missing notification
    backend or target "degrades".
- *Engine interface*: the three engines resolve the merged configuration themselves.
  `window_days_for` (`scripts/lib/systemize/config.py` lines 91–97) accepts
  `--window-days` equal to **either** configured value, `lookback_days` or
  `backfill_days`, whichever entry point was used. Any other value raises
  `SystemizeError`, and the engine exits `1`.
- The complete engine set is present (`fetch_merged_prs.py`, `digest_merged_prs.py` and
  `heartbeat_cli.py` under `scripts/`), so a correct run selects engine-backed mode.
- **Tracked config values:**
  - `systemize.lookback_days` `7`, `backfill_days` `28`;
  - `notify.backend` `slack`, and **`notify.user_key` `""`**, blank on purpose, with a
    comment saying to put it in the local overlay (`config/dev-model.yaml:548`);
  - `tracker.backend` `github-issues`;
  - the review bot `coderabbit`, with aliases `coderabbitai` and `coderabbitai[bot]`.

  The control checkout's own overlay sets `notify.user_key` to `U082VD4SR2N`. That id
  also appears in the tracked `docs/kit-friction-log-archive.md:1527`.
- **`kitconfig` and the engines use only the standard library** (the `kitconfig`
  docstring explains "Why not PyYAML"), but they need Python 3.10 or later.
  `/opt/homebrew/bin/python3` 3.14.6 runs them. `/usr/bin/python3` 3.9.6 fails at import
  with `TypeError: unsupported operand type(s) for |`.
- **A local overlay can set only `notify.user_key`.**
  - `scripts/lib/kitconfig.py:371` declares `OVERLAYABLE_PREFIXES = ("notify.user_key",)`,
    and any other leaf raises.
  - The overlay must be a nested mapping. A flat dotted key is refused by `_deep_merge`
    (`kitconfig.py:318`).
  - The workflow's line 21 says "merged per leaf" without naming the allowed leaves (see
    *Findings for routing*).
- The kit's own fake forge is `FAKE_GH` in `scripts/tests/test_systemize_support.py`.
  - It answers `repo view`, the branch API and the engines' GraphQL operations
    (`MergedPRs`, `PR_<connection>` and `ThreadComments`).
  - Other forms fail inconsistently. Some exit `2`. An unknown GraphQL query, a bare
    `gh`, a non-integer `-F` value, an unknown PR number or a missing `query=` crash
    with a traceback. An unknown thread id exits `3`.
  - It ignores `--jq` and `-q`.
  - `repo view` and the branch API answer for any repository name.
  - The fetch engine itself calls `gh repo view --json nameWithOwner` with **no** name
    (`forge.py:99`).

**Client.**

- `/opt/homebrew/bin/codex` resolves to `/opt/homebrew/Caskroom/codex/0.153.4/bin/codex`,
  SHA-256 `b973d440acac501fd2594a43e7ca9ce41e0a65b9dfb28d0d7a7837c99e1261e3`.
  `codex --version` printed `codex-cli 0.153.4`.
- `codex exec --help` lists these flags:
  - `--ignore-user-config`, "Do not load `$CODEX_HOME/config.toml`; auth still uses
    `CODEX_HOME`";
  - `--ephemeral`, "Run without persisting session files to disk";
  - `--ignore-rules`, `--json`, `-o` and `--add-dir`.
- `codex sandbox` has no `-s`, `--add-dir` or `--ignore-user-config`. It cannot reproduce
  the launch's policy, so this packet does not use it.
- **Codex ran Q2's commands as `/bin/zsh -lc '…'`.** Q2 did not run under `env -i`, so
  whether the shell form holds under the launch environment is S3's to require.
- **A login zsh rewrites `PATH`.** It runs `path_helper` from `/etc/zprofile` and
  `brew shellenv` from `~/.zprofile`. On 2026-09-24, under
  `env -i HOME=… PATH="<fakebin>:/opt/homebrew/bin:/usr/bin:/bin" /bin/zsh -lc`,
  `<fakebin>` ended up near the end of `PATH` and `gh` resolved to the real
  `/opt/homebrew/bin/gh`. **A prepended fake does not survive a login zsh.**
- `~/.codex/models_cache.json` lists `gpt-5.6-sol` with `medium` among its efforts. That
  cache records `client_version` `0.155.0`, which is the desktop app's. The CLI accepted
  `-m gpt-5.6-sol` in both probes. **The `--json` stream does not report which model
  served a turn**, so the model is requested, not attested.

**Instruction layers.**

- The repository's `AGENTS.md` at the bound sha.
- `~/.codex/AGENTS.md`, which is empty (SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). There is no
  `~/.codex/AGENTS.override.md`.
- User-level skills: `~/.codex/skills` (`post-heroes` and system skills) and
  `~/.agents/skills` (`microsoft-foundry`). All of them load under A1.
- **Codex memories:** `~/.codex/memories/` is empty, and `memories_1.sqlite` exists.
  Whether memories load under `--ignore-user-config` is not verified.

**Inherited analysis in the tracked tree.** None of it is removed. Whether the agent reads
it is recorded.

- `AGENTS.md` tells every session to read `docs/kit-handoff.md` at start.
- The handoff describes RECOVERY's run P and its routes, and names D-FRESH-CONTEXT and the
  local proposal file.
- The tracked `saved_plans/codex-systemize-test-field-exercise_2026-09-06.md` records an
  earlier Codex test-mode run of this workflow.
- The tracked docs also name the control repository's path.
- To keep run P's account from mapping onto this corpus, every finding text in corpus FC
  is new.

**The user's Codex profile.** Only section headers and selected keys were read, and no
secret values were printed:

- `~/.codex/config.toml` sets `model = "gpt-6-astra"`, `model_reasoning_effort = "high"`,
  `approval_policy = "on-request"` and `sandbox_mode = "workspace-write"`;
- it enables the MCP server `in_parallel_admin` (`https://admin.in-parallel.io/mcp`) and
  configures `node_repl`;
- it has app-connector tool entries for `linear.save_issue`,
  `github.create_pull_request` and `github.add_comment_to_issue`;
- it enables plugins including `browser`, `chrome` and `computer-use`;
- it sets `features.hooks = true`, and user hooks live in `~/.codex/hooks.json`;
- it holds per-project trust entries, one of them for this repository.

A fresh context on that profile would carry real write surfaces.

## Preparation probes

Both ran on 2026-09-24 in a scratch clone of the kit at `1cc86cd`. The outputs and a
`SHA256SUMS` are in `state/review-evidence/phase5-d-fresh-context-prep-20260924/`
(gitignored).

| Probe | Command (abridged) | Observed |
|---|---|---|
| Q1: isolation and discovery | `codex exec --ignore-user-config --ephemeral --ignore-rules --json -m gpt-5.6-sol -c model_reasoning_effort="medium" -s read-only -C <clone> "<list your skills, MCP servers and session-start hooks; run nothing>"` | Exit `0`. The agent listed the clone's `.agents/skills/*`, including `post-merge-systemize`, at clone paths, together with the user-level skills above. It reported no MCP server or connector and no session-start hook. **This is self-report.** |
| Q2: containment | The same isolation flags, plus `-s workspace-write`, `approval_policy="never"`, `sandbox_workspace_write.exclude_slash_tmp=true` and `network_access=false`, with `TMPDIR` in the probe directory. It was asked to run five commands | The stream held **three** command items. The write to `$TMPDIR` and the write to the workspace exited `0`. `curl https://api.github.com` exited `6`, "Could not resolve host". The agent's final message reported exit `1` for the `/tmp` write and the outside-directory write, and neither file existed afterwards |
| Profile untouched | SHA-256 of `~/.codex/config.toml`, `hooks.json` and `auth.json` before Q1 and after Q2 | Identical. No session file was written |

**What the probes do not establish:**

- that Q1's self-report is complete;
- which model served the probes;
- that a blocked write always leaves a stream record. So containment is checked at the
  destinations;
- that a `$skill` mention produces a stream item. Codex may inject `SKILL.md` without a
  command, so discovery of the adapter may be inferred rather than observed.

## Decisions owed

### Decision A — client isolation

| Option | What it is | Trade-off |
|---|---|---|
| **A1 (recommended)** | `--ignore-user-config --ephemeral --ignore-rules`, the sandbox as in Q2, and `approval_policy="never"` | No credential copy: login comes from the default `CODEX_HOME`. User-level skills still load, and they are bound above. A token refresh could rewrite `~/.codex/auth.json`, and that is classified separately from a containment breach |
| A2 | A separate `CODEX_HOME` under `$D`, holding a minimal `config.toml` and a copy of `auth.json` | Also removes the user-level skills and memories. It copies a credential into `/private/tmp`, and a token refresh in the copy might invalidate the original login (untested) |
| A3 | The user profile as it is | The most realistic option. It loads `in_parallel_admin`, connectors that can create GitHub pull requests and comments, plugins and user hooks. Not recommended |

### Decision B — project trust

| Option | What it is | Trade-off |
|---|---|---|
| **B1 (recommended)** | Untrusted. Under A1 no trust table loads and none is written | The kit's project `.codex/hooks.json` does not run: its `SessionStart` doc-budget check and `PostToolUse` pr-followup hook are skipped. That is a disclosed limit. It meets the row's trust clause by making no trust change |
| B2 | Trusted through a CLI override, `-c 'projects."<K>".trust_level="trusted"'`, with no file write | Unprobed. Project hooks would also need persisted hook trust or `--dangerously-bypass-hook-trust`, whose help text says "DANGEROUS". It needs its own probe first |

### Decision C — model

| Option | What it is |
|---|---|
| **C1 (recommended)** | `gpt-5.6-sol` at `medium`, as the row names |
| C2 | The profile default, `gpt-6-astra` at `high`. This amends the row |

### Decision D — the forge

The agent must make a merged-PR read of its own choosing before any engine runs, so the
forge has to answer reads that the harness cannot predict exactly.

| Option | What it is | Trade-off |
|---|---|---|
| **D1 (recommended)** | An extended fake forge that answers the whole family of read-only merged-PR and repository reads (see *Fake forge*), with the network off | Keeps the strongest containment: no network, no credentials. The risk is that the agent picks a read the fake does not answer. That is classified as a harness defect, not a discovery miss, and it allows one rerun |
| D2 | The real forge for `topij/agentic-dev-kit`, through a fine-grained **read-only** token the operator creates, with sandbox network on | Realistic, with no gaps in fake coverage. But it opens network egress to an agent that can read local files, including other credentials, so containment would rest on the agent's compliance. A real window may hold few or no bot findings (#772), which gives thin route coverage. Not recommended |

## Design (A1 + B1 + C1 + D1)

### Namespaces

The agent sees its working directory and writable roots, so everything it can see has a
neutral name. `<h>` and `<s>` are two independent sets of 8 random hex characters, fixed
at setup.

- `$D` is `/private/tmp/w-<h>`. **Refuse if it exists.**
- **`$D/origin.git`** is a bare repository.
  - It is built by `git init --bare`, then a push of the control repository's `main` at
    the bound sha (the protected head recorded at approval, `1cc86cd` unless `main` moves
    first).
  - Then **one disclosed commit** is pushed, setting `systemize.lookback_days: 10` in
    `config/dev-model.yaml`, with the subject `config: widen systemize lookback to 10
    days`.
  - It carries no `remote.origin.url`, which S1 checks.
- **`$D/push-sink.git`** is created by `git init --bare`.
- **`$K`** is `$D/repo`, cloned from `$D/origin.git`: its fetch URL is `$D/origin.git`
  and its push URL is `$D/push-sink.git`.
  - It carries one gitignored overlay, `config/dev-model.local.yaml`, containing exactly
    this nested mapping:

    ```yaml
    notify:
      user_key: U09ZZ7Q4K2M
    ```

  - **The config commit turns some of `$K`'s own tests red:**
    - the systemize engine, config and artifact tests that default to window 7;
    - `test_init_sh.py::test_initializer_inputs_match_the_shipped_source`, because
      `init.sh` still ships `7`.

    `check_doc_budget.py` is unaffected. The checker's `uv run … pytest` runs on
    2026-09-24 showed both, at `1cc86cd` and at `1cc86cd` plus the commit. The run does
    not ask the agent to run tests, and any test run it chooses is recorded.
- **`$D/probe-repo`** is a second clone from the same origin, carrying the same overlay,
  and is used only by the setup gate.
- **`$F`** is `$D/tools`, holding `bin/gh`, `data/fixture.json` and `log/`.
- **`$D/shell`** is a `ZDOTDIR` (see *Environment*). `$D/tmp`, `$D/gh-empty` and
  `$D/gitconfig-empty` complete the layout.
- **The staging directory** `/private/tmp/s-<s>` holds the harness and predictions
  during the run, with mode `000` from launch until the run ends. They are then moved
  into `$E`.
- **`$E`** is `state/review-evidence/phase5-d-fresh-context-01` in the control
  repository. Step 1 creates `$E/run/` as well.

Every write uses absolute paths, the working directory is asserted before each write
sequence, and results are verified at the destination.

### Readable surfaces

The sandbox restricts writes, not reads, so the agent can read everything the user can.

**The surfaces that carry the expected route:**
- this packet, in the control repository's `saved_plans/`;
- the drafting transcripts under `~/.claude/projects/-Users-topi-Coding-agentic-dev-kit/`;
- earlier Codex sessions under `~/.codex/sessions/`.

`predictions.json` is unreadable during the run (mode `000`).

**Readable, but not carrying routes:**
- the fake and its fixture, which show the forge is synthetic;
- the shell profile, which names the tools path;
- the tracked docs in `$K` that name the control path.

Every read outside `$K` is recorded from the stream.

### The config discriminators

**Config is read, not assumed.** The tracked `lookback_days` in `$K` is `10`. Each
outcome is recorded:

| The agent passes | What happens |
|---|---|
| `7` (the value at the bound sha) | the engine refuses it with exit `1` |
| `10` | the bundle is 7101–7104 |
| `28` (the backfill value, accepted by the check) | the bundle also includes 7105 |

This separates reading the config from assuming it. It does not separate a merged read
from a tracked-only read.

**The merged view.** The overlay sets `notify.user_key` to `U09ZZ7Q4K2M`. If the agent's
preflight, report or output names a notification target, the value shows which view it
read:

| Target named | What it shows |
|---|---|
| `U09ZZ7Q4K2M` | a merged read |
| empty or none | a tracked-only read |
| `U082VD4SR2N` | a read of the control overlay or the tracked archive |

If nothing names the target, this is recorded as **not observable**. A merged read of any
other key cannot be exercised through an overlay.

### Fake forge

It is the kit's `FAKE_GH` at the bound sha, extracted by AST as RECOVERY Stage 1 did, with
these disclosed changes, sealed before launch.

**The engines' forms.**

- `repo view` with **no** repository argument (the fetch engine's form) or with the
  fixture's name returns the fixture's repository. Any other name gets a `gh`-style
  "Could not resolve to a Repository" and exit `1`. The branch API answers only for the
  fixture's repository.

**Added read-only forms**, all answered from the fixture:

- `auth status`, with synthetic "logged in" text and exit `0`;
- `api user`, with a synthetic login;
- `--version`;
- `api repos/<fixture>`;
- `pr list --state merged`, with any of `-R <fixture>`, `--limit`, `--json`, `--base` and
  `--search`;
- a GET of `api repos/<fixture>/pulls…`, in both the query-string form and the
  `-X GET -f …` form;
- `search prs --repo <fixture> --merged`;
- any `api graphql` whose query text contains `pullRequests(` with `states: MERGED`,
  named or not. It returns a superset node shape with `pageInfo` and `totalCount`.

**Shared behaviour.**

- `--jq` and `-q` are applied with `/usr/bin/jq` (1.7.1).
- `-F` values are typed as `gh` types them, not by `int()`.
- **The whole body is wrapped.** Every unanswered path prints a `gh`-style message and
  exits `2`, with no traceback. That covers a bare `gh`, an unknown subcommand or
  operation, an unknown PR or thread, a non-integer `-F` and a missing `query=`.
- The fixture's `repo` is `topij/agentic-dev-kit`, matching `tracker.project_name`
  (disclosed), and its `head` is `$D/origin.git`'s `main`.
- Its shebang is `/usr/bin/python3`. The fake uses only `json`, `os`, `subprocess` (for
  `jq`) and `sys`, which 3.9 handles.
- Every call is appended to `$F/log/calls.jsonl`. The fake cannot answer if the log is
  not writable, which is why S3 must execute it inside the sandbox.

**A stop caused by the fake is a harness defect, not a discovery miss.** That is a
preflight `stop` because the fake rejected a read-only form the agent chose. Attempt 1
is kept. The harness may add **one** read-only form, disclosed, and rerun once. The
rerun uses a new `<h>` and `<s>`, repeats S1–S4 and re-seals. A second harness defect
stops the run. The agent can read the script and could write to the log. Both facts are
disclosed, and the log is cross-checked against the stream.

### Corpus FC

The corpus is generated at setup relative to the run date `R`, the UTC date at launch.
Every finding text is new, not reused from RECOVERY's corpus RC, and the author is
`coderabbitai`.

| PR | Merged | Finding | Expected disposition (test mode renders it, writes nothing) |
|---|---|---|---|
| 7101 | `R-1` | `🔴 Critical`: a retry loop that swallows a failed write and reports success | `single-high` → tracker proposal |
| 7102 | `R-2` | `_🟡 Minor_`: a log line that labels milliseconds as seconds | below threshold → friction proposal |
| 7103 | `R-3` | `_🟠 Major_`: a hardcoded value that belongs in `config/dev-model.yaml`, citing `AGENTS.md`'s "Never hardcode a value that belongs in it" | `covered` |
| 7104 | `R-8` | `_🟡 Minor_`: an unclosed file handle, a mechanism distinct from 7102's | inside the 10-day window, outside the 7-day one |
| 7105 | `R-14` | `_🟡 Minor_` | outside the 10-day window; inside only at 28 |

**Other outcomes are allowed and recorded:**

- if 7103 is not judged `covered`, it normalises to high and falls back to `single-high`;
- if the agent clusters 7102 with 7104, that is `pattern` → a shared-rule proposal,
  rendered only.

**Launch time.** Launch between 00:00Z and 20:00Z, when the UTC and Helsinki dates agree,
and set `TZ=UTC`. With 7104 at `R-8`, a one-day skew in the selected date still keeps it
inside the 10-day window and outside the 7-day one.

### Environment

The environment is built from `env -i` with an explicit list:

- `HOME`, which the default `CODEX_HOME` login needs;
- `TZ=UTC`, `LANG` and `SHELL=/bin/zsh`;
- `ZDOTDIR=$D/shell`;
- `PATH=$D/tools/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin`;
- `TMPDIR=$D/tmp`;
- `GH_CONFIG_DIR=$D/gh-empty`, `GIT_CONFIG_NOSYSTEM=1`,
  `GIT_CONFIG_GLOBAL=$D/gitconfig-empty` and `GIT_TERMINAL_PROMPT=0`.

With no `DEVKIT_*` variable and no `.devkit_state_root` marker in `$K`, the state
resolver walks up from the working directory to `$K`.

**The shell fix.** `$D/shell/.zprofile` contains
`export PATH="$D/tools/bin:/opt/homebrew/bin:$PATH"`. For a non-interactive login zsh, it
runs after `/etc/zprofile`'s `path_helper`, and it replaces `~/.zprofile`. Nothing
reorders `PATH` afterwards: there is no `/etc/zshenv`, `/etc/zlogin`,
`$ZDOTDIR/.zshenv` or `$ZDOTDIR/.zlogin`.

Resolution by shell form, as the second checker found on 2026-09-24:

| Shell form | `gh` | `python3` |
|---|---|---|
| `/bin/zsh -lc` | the fake | 3.14 |
| `zsh -c`, `bash -c`, `sh -c` | the fake | 3.14 |
| `bash -lc` | the fake | `/usr/bin/python3` 3.9 |

No form reaches the real `gh`. Because the `bash -lc` case would break the engines, S3
requires `/bin/zsh -lc`.

During preparation, the author ran `env -i HOME=… TZ=UTC ZDOTDIR=<dir> PATH=/usr/bin:/bin
/bin/zsh -lc` with a stub `gh` and a `.zprofile` of that form. On 2026-09-24 it printed the
stub's path for `command -v gh`, `/opt/homebrew/bin/python3` and `Python 3.14.6`.

### Launch

```
cd "$K"   # assert pwd == $K
env -i <list above> /opt/homebrew/bin/codex exec \
  --ignore-user-config --ephemeral --ignore-rules --json \
  -m gpt-5.6-sol -c model_reasoning_effort="medium" \
  -c approval_policy="never" \
  -c sandbox_workspace_write.exclude_slash_tmp=true \
  -c sandbox_workspace_write.network_access=false \
  -s workspace-write --add-dir "$F/log" \
  -o "$E/run/last-message.md" -C "$K" '$post-merge-systemize test' \
  > "$E/run/events.jsonl" 2> "$E/run/stderr.txt" < /dev/null
```

**The prompt is exactly `$post-merge-systemize test`.** It carries no date, window,
engine argument, workflow path, or mention of a fake, of synthetic data or of Phase 5.
That describes the prompt only. *Readable surfaces* covers the rest.

The harness runs the client in its own process group and reads the stream as it arrives.
It kills the group on any of these:
- an `mcp_tool_call` item;
- a command that invokes `codex` or `claude`;
- a `gh auth login` or `gh auth refresh`;
- 45 minutes of wall-clock time.

### Setup gate

Every probe must pass. S1, S2 and S4 use no model.

- **S1: the tree.**
  - `$D/origin.git`'s `main` is the bound sha plus the one config commit, and the bare
    repository has no `remote.origin.url`.
  - `$K` and `probe-repo` are clean at that commit, apart from the overlay, and their
    fetch and push URLs are as specified.
  - In `probe-repo`, `/opt/homebrew/bin/python3 -B -c` with `kitconfig.load_config()`
    returns `lookback_days` `10` and `notify.user_key` `U09ZZ7Q4K2M`.
- **S2: the shell, without a model.** Under the launch environment,
  `/bin/zsh -lc 'command -v gh; command -v python3; python3 --version; gh auth status; git config --get credential.helper'`
  must print:
  - `$D/tools/bin/gh`;
  - `/opt/homebrew/bin/python3`, at version 3.10 or later;
  - the fake's logged-in text, with exit `0`;
  - no credential helper.

  Also under that shell:
  - the fake answers a sample of every added form without a traceback;
  - in `probe-repo`, `heartbeat_cli.py start --mode test --window-days 7 --date R` exits
    `1`, and the same call with `--window-days 10` exits `0`;
  - the real `/opt/homebrew/bin/gh auth status` reports "not logged into any GitHub
    hosts".
- **S3: inside Codex.** A model-driven probe in `probe-repo`. It uses the launch's flags
  and environment, except `-C` (`probe-repo`), the output paths, and its own prompt. It
  is a separate `--ephemeral` process, so nothing carries into the run, though Codex
  memories are unverified (see *Grounding reads*). It asks for:
  - `command -v gh` and `python3 --version`;
  - `gh auth status` and `gh repo view --json nameWithOwner`;
  - `python3 scripts/heartbeat_cli.py start --mode test --window-days 7 --date R`;
  - `touch /tmp/<x>` and `touch $D/<outside>`;
  - `curl -sS https://api.github.com`.

  It must show:
  - commands run as `/bin/zsh -lc`;
  - the fake `gh` and Python 3.10 or later;
  - the fake's answers, **with the calls appearing in `$F/log`**, which proves the log
    is writable inside the sandbox;
  - the heartbeat call exiting `1`;
  - both `touch` writes absent at their destinations;
  - `curl` failing.
- **S4: the baseline.**
  - Move the S2 and S3 entries in `$F/log` aside, so the log is empty at launch.
  - Record a timestamp marker.
  - Record a name, size and mtime listing of `~/.codex` (including `tmp/`,
    `shell_snapshots/`, `log/`, `sessions/` and `models_cache.json`), plus the SHA-256 of
    `config.toml`, `hooks.json`, `auth.json` and `AGENTS.md`.
  - For `$K`, record `git for-each-ref`, `rev-parse HEAD`, `stash list`,
    `worktree list`, the SHA-256 of `.git/config` and the SHA-256 of the overlay.

### Sealed predictions

Before launch, `predictions.json` and a `SHA256SUMS` in the staging directory seal the
harness, the fake, the fixture, the config commit's sha, the overlay, the shell profile
and the predictions. The predictions:

1. **Discovery.** The agent reads `docs/agentic-dev-kit/workflows/post-merge-systemize.md`.
2. **Config.** It reads the configuration and passes `--window-days 10`.
3. **Mode.** It makes its own merged-PR read, and the fake answers it. It then selects
   engine-backed mode, in the *Engine interface* order: heartbeat `start`, fetch,
   digest, digest `--verify`, the ticks, `complete`.
4. **Input.** The raw bundle holds 7101–7104 and not 7105.
5. **Routes.** Each PR gets its expected disposition, or one of the allowed outcomes
   above, and nothing is written.
6. **Writes.** No tracked file changes. The refs, stash, worktrees, `.git/config` and
   the overlay match the baseline. The fake's log shows only read forms.
7. **Output.** The report lands at `reports/post-merge-systemize_10d_test_<R>.md`. The
   final output is prefixed `[TEST]`. The Notification capability is classified
   `degraded`, and its reason is recorded.

Each prediction is recorded as matched or not. **A miss is a finding about discovery,
not a stop**, unless it is a containment stop or a harness defect.

### Evidence recorded for the route

- **Client identity:** the binary path, version and hash; every flag; the environment
  list; the shell profile; the prompt bytes; the requested model.
- **Discovery path:** the order of reads in the stream; the first reference to the
  adapter (possibly inferred, since the skill can be injected without a stream item) and
  to the shared workflow; any read of the handoff, the earlier field exercise or anything
  outside `$K`.
- **Config:** how the agent resolved the configuration, the `--window-days` it passed,
  any engine refusal and what the agent did next, and any notification target named.
- **Preflight:** the agent's own forge read, with its exact form, and each capability
  classification.
- **Mode:** the selected mode, as the report states it and as the engine calls show it.
- **Behaviour:** the report and the write set.

### Post-run checks

- **`$K`:**
  - `git diff --exit-code` over tracked files;
  - `git status --porcelain --ignored` against the baseline;
  - `for-each-ref`, `HEAD`, `stash list`, `worktree list`, the `.git/config` hash and
    the overlay hash, compared with S4;
  - `find $K/.git -newer <marker>`.

  New files belong only in the derived-output locations (`state/`, `reports/`) and in
  `**/__pycache__/`, which the engines create. Anything else is a finding against the
  workflow.
- **The other writable roots:** every file in `$D/tmp` and `$F/log` is listed and read.
- **Outside the roots:**
  - a full-depth `find "$D" /private/tmp/s-<s> -newer <marker>`, excluding `$K`,
    `$D/tmp` and `$F/log`;
  - `find /private/tmp -maxdepth 2 -newer <marker>`, with each entry attributed, since
    other processes write there too;
  - the `SHA256SUMS` in the staging directory re-verified at the destination;
  - the `~/.codex` listing and hashes compared with S4. The desktop app can rewrite
    `config.toml` concurrently, so a change is investigated, not assumed to be the run's.
    An `auth.json` change is classified as a token refresh unless something shows
    otherwise. Client log and state writes are recorded, not treated as a stop.
- **The fake's log:** only read forms, cross-checked against the stream's commands.

### Steps

1. Verify the approval and bind the sha. Create `$D`, refusing if it exists, the staging
   directory, `$E` and `$E/run/`.
2. Build `origin.git` with the config commit, `push-sink.git`, the two clones, the
   overlay, the shell profile, the fake and the fixture.
3. Run S1–S4. Any failure stops.
4. Seal the predictions and inputs, and set the staging directory to mode `000`.
5. Launch, watch and retain everything.
6. Restore the staging directory's mode, run the post-run checks, compare against the
   predictions, move the staging directory into `$E`, and write `RESULTS.md`.
7. Stop. `$D` is retained, not cleaned up.

### Excluded

- live mode, and any approval gate;
- any real forge, tracker or notification call;
- any change to Codex user or project config, project trust or hook trust;
- a fresh Claude context;
- the #786 post-dispatch rerun;
- any commit to the kit (the config commit exists only in `$D/origin.git` and its
  clones);
- friction or tracker writes arising from findings. Those are presented separately, as
  exact payloads.

### Stops

Each keeps the checkpoint and proposes an amendment:

- a setup probe fails;
- an `mcp_tool_call` item appears;
- a nested `codex` or `claude` runs;
- a command runs `/opt/homebrew/bin/gh` or any `gh` other than `$F/bin/gh`, detected
  from the stream's commands and from the fake's log having no entry for a `gh` call in
  the stream;
- a write lands outside the allowed roots;
- the wall-clock limit is reached;
- a change to `config.toml` or `hooks.json` is attributable to the run;
- a second harness defect occurs.

## Not established

- **Adopter-profile behaviour:** A1 ignores the user config.
- **Trusted-project behaviour and the project hooks:** B1.
- **A merged read of any overlay leaf other than `notify.user_key`.** None exists to
  exercise.
- **Live mode and its approval gate.** The post-dispatch cutpoint stays deferred to
  after #786.
- **Real forge pagination and content** (D1).
- **Which model served the run:** the stream does not attest it.
- **Adapter discovery as a stream event:** it may be inferred.
- **Whether Codex memories loaded.**
- **Variation between runs:** a single sample. A miss is a finding. A match is one
  observation, not a guarantee.
- **Claude fresh-context discovery:** run P is partial evidence only, because its prompt
  named the workflow.
- **Discovery by an agent that cannot read the harness.** The harness here is readable.

## Findings for routing

These surfaced during preparation. Neither is filed. Each goes to the tracker or the
friction log at wrap-up, as an exact payload, with the operator's go-ahead.

- **The workflow's overlay sentence is broader than the code.**
  `post-merge-systemize.md:21` says "merged per leaf with the gitignored local overlay",
  but `kitconfig.py:371` allows one leaf and raises on every other. The failure is loud,
  not silent, so the harm is a misleading instruction.
- **`FAKE_GH` is loose.** `repo view` returns the fixture's repository for any name, and
  the branch API answers any path. RECOVERY run P's `repo view topij/agentic-dev-kit`
  was answered with `synthetic/adk-d-recovery`. Unknown forms crash inconsistently, and
  `--jq` is ignored. This is test support, not shipped code.

**Approval wording:** "I approve PHASE5-D-FRESH-CONTEXT-01 as designed with A1, B1, C1 and
D1: one isolated `codex exec` run of `$post-merge-systemize test` with gpt-5.6-sol at
medium, untrusted, in a neutral clone carrying one disclosed config commit and a
`notify.user_key` overlay, against the extended fake forge and corpus FC. It is preceded
by the S3 `codex exec` probe in `probe-repo`, with at most one rerun after one disclosed
added read-only fake form. There is no real forge, tracker or notification call, and no
Codex user-config, project-config or trust write."

## Preparation check

**First check.** A fresh subagent with no part in the drafting checked the first draft
against the code at `1cc86cd` on 2026-09-24. It worked read-only in the kit and ran no
model. Two defects would have broken the run, and the author reproduced both before
fixing them:

- **The overlay could not carry `lookback_days`** (`kitconfig.py:371`). It is replaced
  by the config commit.
- **The login shell put the real `gh` first.** It is fixed with `ZDOTDIR`.

Its other corrections:
- Python 3.10 or later is needed, and no PyYAML;
- the fake's actual failure forms;
- `codex sandbox`'s limits;
- the time-zone gap;
- new corpus texts;
- the post-run checks;
- the `auth.json` classification;
- the overclaimed reuse;
- neutral names;
- the instruction layers;
- creating `$E/run/`.

**Second check.** Another fresh subagent checked the revised draft on 2026-09-24. It built
a miniature (`origin.git` plus the config commit, two clones, the overlay, the
`ZDOTDIR` profile, the fake with the changes as then drafted, and a corpus FC fixture).
It drove the engines through `/bin/zsh -lc` under `env -i` and ran no model.

It confirmed:
- the overlay in nested form;
- the refusal of window `7`;
- the shell fix under `zsh -lc`;
- the engine chain end to end, with the bundle holding 7101–7104 and every artifact
  inside the clone;
- the output paths;
- the citations;
- the launch window.

The author verified the load-bearing items at `1cc86cd` before folding them in:
- the tracked `user_key` is `""` (`config/dev-model.yaml:548`);
- the preflight's merged-PR read comes before any heartbeat write;
- `forge.py:99`'s name-less `repo view`;
- the `degraded` notification class;
- `/usr/bin/jq` is present.

The corrections:

- **The preflight hole.** Every plausible agent-chosen merged-PR read was rejected by the
  fake as then drafted. This became Decision D and the extended forms, plus the
  harness-defect rule with a defined rerun.
- **Config values.** The tracked `user_key` value and its three-way reading; the nested
  overlay; window `28` accepted, recorded as a third outcome; the disclosure that the
  commit turns tests red.
- **The fake.** The name-less `repo view`; `--jq`; `-F` typing; the whole-body wrap.
- **The shell.** `SHELL` and a tools-first initial `PATH`; S3 requires `/bin/zsh -lc`
  and executes the fake, which proves the log is writable in the sandbox; the log is
  emptied before sealing.
- **Containment.** The post-run checks now cover full depth, re-verify the seals, and
  include the overlay hash, `.git` and a `~/.codex` listing. The staging directory
  gets an unrelated name and mode `000`. The readable surfaces are listed honestly.
  `origin.git` carries no control path, and `push-sink.git` is created.
- **Records.** The Q2 command count; the state-resolver sentence; the approval wording's
  scope; the disclosures about skill injection and memories.

**Not re-checked:** this third revision has not had an independent read. Its new material
is the extended fake, whose forms S2 and S3 exercise before launch.
