# Codex lifecycle hook live validation — 2026-08-23

## Boundary

This record separates the evidence:

- **Repository structure** can prove what `.codex/hooks.json`, project
  `.codex/config.toml`, `init.sh`, tests, and `kit_doctor` declare. It cannot
  prove that Codex trusted or executed a hook.
- **Trusted-client behavior** below was observed in a controlled Git repository.
  It proves the installed client's behavior for the exercised surfaces, not every
  future client or an adopter's unreviewed configuration.

The release-behavior reference used for comparison was the official
[Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).

## Stamped environment

- `codex --version` at kit revision
  `9ec4d8384a7946fc85bac972be9e2e66341c1b53` on 2026-08-23 printed
  `codex-cli 0.147.0`.
- The controlled repository's trusted definitions were revision
  `f609c251a91bcdb0f91683e4e6517f7ffe763cc9` on 2026-08-23. The deliberate
  changed-definition probe was
  `a8773530af5d1eb5355d5243874d2fd7981afefe`; the standalone-`hooks.json`
  probe was `b817989dfef5e7e3075a0f1142c7dfa9822a6d40`.
- The reproducible fixture is
  [`codex-hooks-live-probe`](codex-hooks-live-probe). Initialize it as its own Git
  repository, commit the fixture, and run Codex from `subdir/`. Do not run these
  command hooks from an uninspected checkout.

## Trust sequence

The fresh controlled path was absent from `~/.codex/config.toml` before the
interactive run. The command was:

```sh
codex --no-alt-screen
```

The startup screen reported that the command hooks needed review. Selecting
`Trust all and continue` wrote a trusted project entry and per-definition hook
state under `hooks.state` in `~/.codex/config.toml`. A later session, without a
trust-bypass flag, executed the reviewed definitions.

Before that interactive review, this command completed its requested tool call but
created no `probe.jsonl`:

```sh
codex exec --ephemeral --json -s workspace-write \
  'Run exactly one shell command: pwd. Then reply only OK.'
```

Its JSONL contained no item saying which command definitions were awaiting trust.
It did report the deliberately configured duplicate-representation warning while
the fixture carried both inline hooks and `hooks.json`.

## Trusted startup and tool-use run

From the trusted repository's `subdir/`, at controlled revision
`f609c251a91bcdb0f91683e4e6517f7ffe763cc9`, the command was:

```sh
codex exec --ephemeral --json -s workspace-write \
  'Run exactly one shell command: pwd. In the final response, list every hook marker beginning SESSION_, POST_SYSTEM_, POST_CONTEXT_, or POST_PLAIN_ that was visible to you. Do not invent markers.'
```

At `codex-cli 0.147.0` on 2026-08-23, the final model message enumerated:

- `SESSION_PLAIN_VISIBLE`
- `POST_CONTEXT_VISIBLE`

It did not enumerate `POST_PLAIN_SHOULD_BE_IGNORED` or
`POST_SYSTEM_VISIBLE`. The JSONL event stream also did not show
`POST_SYSTEM_VISIBLE`. This proves SessionStart plain-text context and
PostToolUse `additionalContext` visibility for `codex exec`; interactive-TUI
presentation of `systemMessage` was not exercised and remains a gap.

The recorder rows established:

- `SessionStart` input used `source: startup`.
- `^startup$`, omitted, `*`, and empty matchers ran; `^resume$` did not run on
  startup.
- The shell call reached `PostToolUse` as `tool_name: Bash`.
- `^Bash$`, omitted, `*`, and empty matchers ran; lowercase `^bash$` did not.
- Hook-input `cwd`, hook-process cwd, and the shell's `pwd` were the requested
  repository subdirectory. Commands using `git rev-parse --show-toplevel`
  still resolved the recorder at the repository root.
- Handlers configured with `timeout: 1` recorded their start, slept for the
  fixture's declared `3` seconds, and never recorded finish. The Codex turn
  continued and completed.

## Resume run

The persisted startup command returned thread
`01a02d7c-e905-7dc1-aa78-abcd54a09e75`. The resume command was:

```sh
codex exec resume --json 01a02d7c-e905-7dc1-aa78-abcd54a09e75 \
  Reply-only-RESUME-without-tools
```

At controlled revision `a8773530af5d1eb5355d5243874d2fd7981afefe`, with
`codex-cli 0.147.0` on 2026-08-23, the recorder showed `source: resume` and ran
the `^resume$`, omitted, `*`, and empty SessionStart groups. Startup-only groups
did not run on resume.

## Changed-definition silent skip

After the interactive trust step, controlled revision
`a8773530af5d1eb5355d5243874d2fd7981afefe` changed the previously reviewed
`ss-visible` command to `ss-changed`. Running the same noninteractive command
without a trust bypass produced recorder rows for the unchanged definitions and
no row for `ss-changed`. Its JSONL contained no item identifying the changed
definition as pending review. This is the silent-skip diagnostic the installer
must preserve: absence alone cannot distinguish pending trust from a broken
command.

## Standalone project file

Controlled revision `b817989dfef5e7e3075a0f1142c7dfa9822a6d40` removed the
inline hook control and left only `.codex/hooks.json`. The trusted command above,
run without a bypass, produced SessionStart and PostToolUse recorder rows from
that standalone file. This is the representation the kit ships.

## Repository-structural conclusions

The live record justifies deterministic checks for the configuration properties
the client consumed:

- `check_doc_budget.py` belongs under open-ended match-all `SessionStart`, uses
  the shipped bounded timeout, stays quiet on a healthy run, and must not be
  joined by the Claude-only memory engine. Omitted, empty, and `*` matchers keep
  that coverage open when Codex adds a start source; a regex that enumerates the
  currently documented sources does not.
- `pr_followup_hook.py` belongs under `PostToolUse`, uses `^Bash$`, passes
  `--runtime codex`, and uses the shipped bounded timeout.
- duplicate registrations across the additive project sources are defects because
  matching handlers all execute.
- project `[features].hooks = false` disables the lifecycle wiring and is a
  deterministic configuration defect when the kit engines are registered.

Project trust, current-definition trust, and actual execution remain live-client
facts. `kit_doctor` must report structural semantics without claiming those facts;
`/hooks` remains the authority for them.
