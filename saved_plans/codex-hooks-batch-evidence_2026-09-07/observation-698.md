Live Codex observation — 2026-09-07. Severity M, continuing this issue's diagnostic scope.

`codex --version` in /Users/topi/Coding/agentic-dev-kit at 0fcad7f7dab385d9ea5f296423e956f6d0ac0eea on 2026-09-07 printed `codex-cli 0.149.1`.

The original post-REG-01 fixture sets `features.hooks = true`, as does the user's Codex config. I therefore used a disposable copy at 08ac687f4ae14218a3861c6b8b143d8b86c4e3c2 with its uncommitted registration payloads, removed only its .codex/config.toml, and supplied private temporary Codex state with no hooks feature setting or user hooks file. The copied .codex/hooks.json retained SHA-256 dbea8d8084adcc50e786af584c7e407fc5d7040bf26bd614c9966e9ba2797cfb.

The interactive launch was:

    env CODEX_HOME=/private/tmp/adk-codex-batch-20260907-br1ch2u4/codex-state TERM=xterm-256color codex --cd /private/tmp/adk-codex-batch-20260907-br1ch2u4/unset-fixture --no-alt-screen

After accepting project trust and choosing Review hooks, `/hooks` on 2026-09-07 at that copy revision listed SessionStart and PostToolUse from the copy's .codex/hooks.json. Each displayed Installed 1, Active 0, Review 1, with `New hook - review required`. `/debug-config` identified the private user config layer. The private config contained only the update-check setting and Codex's added project-trust entry; neither hooks feature spelling was set.

An unset feature switch therefore did not prevent reading/discovering these registrations in this observed CLI. This does not establish execution after hook trust, the explicitly disabled case, or defaults in other clients. The original fixture and comparison source retained their inventories and Git states in the stamped post-session audit.

Use this observation to scope the installer/doctor correction without treating discovery as execution. #698 stays open for that correction; no installer or doctor change is made by this comment.
