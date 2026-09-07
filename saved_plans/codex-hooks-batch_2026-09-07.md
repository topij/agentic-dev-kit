# Codex hooks batch — 2026-09-07

This records the approved live Codex batch following the
[REG-01 application](adopt-reg01-application_2026-09-07.md) and
[installed-suite assessment](adopt-suite-assessment_2026-09-07.md).
The observations below come from interactive `/hooks`, with `/debug-config`
providing the live configuration stack. Static doctor output does not establish them.

## Inputs and continuity

The kit checkout was `/Users/topi/Coding/agentic-dev-kit` at
`0fcad7f7dab385d9ea5f296423e956f6d0ac0eea`. `codex --version` there on
2026-09-07 printed `codex-cli 0.149.1`.
The fixture was `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture` at
`08ac687f4ae14218a3861c6b8b143d8b86c4e3c2`, including its uncommitted REG-01 payloads.
The [setup record](codex-hooks-batch-evidence_2026-09-07/setup.json) binds the
comparison source, disposable copy and hashes to those inputs.

The fixture baseline is
[fixture-inventory-after-reg01.json](adopt-reg01-application-evidence_2026-09-07/fixture-inventory-after-reg01.json),
which supersedes FIX-01. The source baseline remains
[source-input-inventory.json](codex-adopt-ver02-evidence_2026-09-06/source-input-inventory.json).
The [post-session audit](codex-hooks-batch-evidence_2026-09-07/post-session-audit.json)
and [final audit](codex-hooks-batch-evidence_2026-09-07/final-audit.json) retain the
stamped inventory and Git comparisons. Neither original tree was rebuilt or changed.
The [audit program](codex-hooks-batch-evidence_2026-09-07/audit.py.txt) is preserved
as historical source; it depends on the retained temporary trees and must not be
used as an instruction to recreate them.

## (a) Fixture loading and trust

Launch on 2026-09-07 at the fixture revision above:

```sh
TERM=xterm-256color codex --cd /private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture --no-alt-screen
```

The operator-authorized session accepted project trust and selected **Review hooks**.
`/hooks` listed the fixture's PostToolUse and SessionStart definitions from its
`.codex/hooks.json`; each displayed **New hook - review required**.
`/debug-config` listed the fixture's `.codex/config.toml` as enabled.
The [terminal excerpts](codex-hooks-batch-evidence_2026-09-07/fixture-tui-excerpts.txt)
retain the complete event overview, project command details and configuration stack.
The overview also includes inherited user hooks; it is not a fixture-only tally.

Thus the project configuration was enabled and the project hook definitions were
discovered in this CLI. Project trust was accepted; the current project hook
definitions were left untrusted. No hook-trust action or model turn was submitted.
This establishes loading/discovery, not execution of those definitions.
Project trust persisted in the host user's Codex config outside the fixture.

## (b) Unset feature case

The original fixture and host user config set `features.hooks = true`, so neither
could establish the unset case. A disposable fixture copy retained the same revision
and payloads except for removal of its `.codex/config.toml`. Private temporary Codex
state omitted both hooks feature spellings and a user hooks file.

```sh
env CODEX_HOME=/private/tmp/adk-codex-batch-20260907-br1ch2u4/codex-state TERM=xterm-256color codex --cd /private/tmp/adk-codex-batch-20260907-br1ch2u4/unset-fixture --no-alt-screen
```

After project trust and **Review hooks**, `/hooks` on 2026-09-07 at the copy's fixture
revision listed SessionStart and PostToolUse from the copy's `.codex/hooks.json`,
each pending review. The [terminal excerpts](codex-hooks-batch-evidence_2026-09-07/unset-tui-excerpts.txt)
retain the table and definition details. The audit records the absent feature settings,
absent project config and user hooks file, and removal of the temporary credential copy.
`/debug-config`'s project-layer listing alone is not evidence that an absent file exists.

**Unset did not prevent discovery in this observed CLI.** This does not establish
execution after hook trust, the explicitly disabled case or other clients' defaults.
The operator approved the [exact observation](codex-hooks-batch-evidence_2026-09-07/observation-698.md),
which was [posted to #698](https://github.com/topij/agentic-dev-kit/issues/698#issuecomment-5569204436).
The [read-back receipt](codex-hooks-batch-evidence_2026-09-07/tracker-observation-698.json)
records the matching body and open issue. Installer/doctor correction remains separate work.

## (c) Reserved dispositions

The operator approved the exact linked payloads and closure as completed:

- [#608 disposition](https://github.com/topij/agentic-dev-kit/issues/608#issuecomment-5568932557)
  credits PR #680's existing live TUI observation and its scoped matrix declaration.
- [#255 disposition](https://github.com/topij/agentic-dev-kit/issues/255#issuecomment-5568933659)
  credits PR #680's runtime-submap declaration test, with its explicit coverage limits.

The [tracker receipt](codex-hooks-batch-evidence_2026-09-07/tracker-dispositions.json)
retains approval scope, exact payload hashes and the command-stamped closure read-backs.
PR #680's credited probe was not repeated. Neither were PR #699's trial, REG-01's
application or PR #701's assessment.

## Evidence and boundary

[Capture provenance](codex-hooks-batch-evidence_2026-09-07/capture-provenance.json)
identifies selections from control-sequence-stripped PTY output, with trailing whitespace
removed, and the omitted screens. These are excerpts, not complete terminal transcripts.
The raw captures remain in the ignored local reports directory; [digests](codex-hooks-batch-evidence_2026-09-07/sha256.json)
cover the promoted files.

No new initialization, adoption completion, fixture PR, Phase 5 exit or cs-toolkit
replay was authorized by this batch. Each retains its own exact decision. The repairs
on #534 remain Claude-shaped work. A later approved fixture execution must first
recheck the post-REG-01 baseline and stop if either original temporary tree is missing.
