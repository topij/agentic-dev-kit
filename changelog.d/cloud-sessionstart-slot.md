## Installer: a stated slot for your own cloud-only SessionStart hook

ADDED (installer output): `init.sh`'s Claude `SessionStart` advisory now ends with a
note on where your own cloud-only setup hook goes: a further entry in the same
`hooks.SessionStart` array of `.claude/settings.json`, after the kit's entry, gated on
`[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0`. `docs/agentic-dev-kit/runtime-parity.md`
has a new *Adopter-owned cloud setup hook* section with an example entry and a
best-effort script skeleton. Claude Code only; nothing goes into `.codex/hooks.json`.

If you install tools for Claude Code cloud sessions by appending commands to the kit's
`SessionStart` entry, move them into an entry of their own. `kit_doctor` gives that
entry no finding as long as the script it runs does not share a basename with a kit
engine.

If you vendor the kit's tests, take `scripts/tests/test_init_sh.py` together with
`init.sh`. Its new test reads the note above from `init.sh`'s output, and fails against
an older `init.sh`.
