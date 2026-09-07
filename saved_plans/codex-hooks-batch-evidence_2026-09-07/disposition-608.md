Disposition — 2026-09-07, from the Codex batch. This issue's agreed scope was delivered by PR #680 (merge 3898204a00948ac5c73745dbb4bc551967b16e62).

The live observation is already credited in that PR and was not repeated for this disposition. Its recorded interactive invocation on 2026-09-05 in /private/tmp/codex-608-tui-6_emmq65 at 3b34c8dffdd72bee7d5249148bd81bc957f521eb was:

    TERM=xterm-256color codex --no-alt-screen -s read-only -a never -m gpt-5.5 -c model_reasoning_effort=high

The retained PR account reports the requested pwd and the TUI display `PostToolUse (completed) says: POST_SYSTEM_608_VISIBLE`, with `hook context: POST_CONTEXT_608_VISIBLE`. The model's final reply was `POST_CONTEXT_608_VISIBLE`.

The matrix delivered by that PR makes interactive hook-message presentation non-load-bearing. This scoped observation supports neither a general client guarantee nor a sandbox guarantee; no required parity outcome depends on the display. Those limits satisfy the agreed disposition rather than leave another presentation probe outstanding.

Evidence: https://github.com/topij/agentic-dev-kit/pull/680 and its review disposition https://github.com/topij/agentic-dev-kit/pull/680#issuecomment-5553981033.

This disposition does not decide Phase 5 exit, adoption completion, a fixture PR, initialization, or cs-toolkit replay.
