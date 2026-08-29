# Claude `SessionStart` matcher — live validation

Produced from a Claude Code session on 2026-08-29 to settle `#606`'s middle question:
whether `.claude/settings.json`'s `SessionStart` matcher `"startup"` is a deliberate
narrowing or an ad hoc one, and what the client accepts in its place.

`init.sh`'s Codex advisory already omits the matcher deliberately, "for open-ended
coverage as new start sources are added". Nothing had established whether the Claude
side *could* do the same, so the asymmetry stood as an assumption. This record replaces
the assumption with a measurement.

## Client and fixture

- Client: `claude --version` → `2.1.251 (Claude Code)`.
- Fixture: a throwaway git repository under the session scratchpad, containing only
  `.claude/settings.json`. Its bytes are
  `sha256 9b8e0f0461f4294ad80d412ef8b3d9494e6df7675ba8170869674b8ba175e32f`.
- The fixture registers **four** `SessionStart` groups over the same event, each
  appending the hook's stdin to a differently-named file, so one run reports every
  group's decision at once:

  | group | matcher |
  |---|---|
  | `startup` | `"startup"` |
  | `nomatcher` | key absent |
  | `alternation` | `"startup\|resume\|clear\|compact"` |
  | `star` | `"*"` |

  Reading the *hook's own stdin* rather than a marker string is what makes the
  `source` field below evidence rather than inference: each file carries the client's
  own `hook_event_name` and `source` for the run that wrote it.

## Runs

Both runs were `claude -p --output-format json --permission-mode plan`, invoked with
the fixture as the working directory, and both exited 0 with empty stderr.

**Run 1 — a fresh session.** Session id `40c7742d-c95c-4aef-9703-6d566b180255`. All
four groups fired. The `startup` group's stdin carried
`{"hook_event_name": "SessionStart", "source": "startup"}`.

**Run 2 — `--resume 40c7742d-c95c-4aef-9703-6d566b180255`**, the same fixture, the four
output files from run 1 moved aside first so an absence could be read as an absence.
Three groups fired — `nomatcher`, `alternation`, `star` — each carrying
`{"hook_event_name": "SessionStart", "source": "resume"}`. **The `startup` group wrote
no file.**

## What that establishes, and what it does not

- At this client, `SessionStart` has at least two sources, and `matcher: "startup"`
  fires on one of them. The narrowing is real and it is observable, not theoretical:
  a resumed session skipped the tripwire.
- An **omitted** `matcher` fires on both sources, `"*"` fires on both, and the
  four-way alternation fires on both. The client rejected none of the three and warned
  about none of them — stderr was empty on both runs.
- So omitting the matcher is available on Claude, and the shipped `"startup"` was a
  narrowing the kit chose rather than one the runtime imposed. That is the answer
  `#606` asked for.

Two limits, stated because the runs do not cover them:

- **`clear` and `compact` were not exercised.** Both are interactive session
  transitions with no headless invocation that produces them, so this record covers
  `startup` and `resume` only. That is sufficient for the decision — one non-`startup`
  source that the narrow matcher skipped and the open form caught is what settles it —
  but it is not a claim that every source behaves as `resume` did.
- **The alternation and `"*"` forms are recorded, not adopted.** Both fired. The
  alternation is rejected on a different ground than support: it enumerates the sources
  known on 2026-08-29, so a source added later is skipped silently, which is the same
  failure as `"startup"` in slower motion. Omission has no list to go stale, and it is
  the form the Codex advisory already prescribes for the same reason.
