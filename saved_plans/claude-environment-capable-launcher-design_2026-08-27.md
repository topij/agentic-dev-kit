# Claude environment-capable launcher design — 2026-08-27

## Slice boundary

This design generalises the supported Codex lane wrapper delivered by PR `#609` into a
per-runtime wrapper whose second supported runtime is Claude Code through `claude -p`.
It does not calibrate models or reasoning effort (`#605`, `#255`), add approval or
sandbox policy or writing-lane evidence (`#601`), select permission mode (`#606`), run
a first real headless task (`#602`), adapt a downstream repository (`#607`), or define
a launcher framework beyond the two selected mechanisms.

The product inventory is grounded in the installed client and Claude Code's published
CLI reference. `claude --version` on 2026-08-27 printed `2.1.247 (Claude Code)`; the
binary resolved through `command -v claude` to `/Users/topi/.local/bin/claude`, a
symlink into `/Users/topi/.local/share/claude/versions/2.1.247`. A probe on 2026-08-27
of `printf '<prompt>' | claude -p --output-format json` run outside any repository
printed one line holding one JSON object whose keys include `type` (`result`),
`subtype` (`success`), `is_error` (`false`), `result` (the reply text),
`permission_denials`, and `session_id`. Documentation and the probe supply the
candidate surface; only the live isolation record for this slice can establish that
the selected client ran with the intended worktree and lane environment.

Everything PR `#609` established stays in force unchanged: absolute descriptor and
authority binding; complete replacement of inherited lane/state identity; removal of
inherited repository authority including every `GIT_*` key; trusted executable lookup
rather than caller `PATH`; independent child observation of worktree, repository, lane,
state root, branch/base, forge, environment, and process identity; live inherited-
descriptor enumeration with fail-closed unavailability; the private launch nonce and
detached-descendant containment; act-time nonce/fingerprint revalidation before
signalling; one-shot attempt semantics; durable observation, final-message, and
terminal-receipt binding; and the local descriptor seal's documented same-user trust
boundary. The generalisation touches only the runtime selection, the child argv, and
the final-text evidence route.

## Design matrix

| Launch surface | Runtime authority | Worktree authority | Environment replacement | Inherited-variable removal | Prompt transport | Final-text transport | State-root isolation | Process identity | Durable evidence | Authoritative observer | Unavailable / failure outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Native in-session Claude agent dispatch (Agent tool, subagent definitions, workflow agents) | Runtime-owned; selects `model`/`effort` but no lane | Prompted path or a runtime-created worktree that conflicts with `new --headless`; no child `cwd` field | No child environment field; cockpit environment inherited | None | Tool prompt | Agent final text only | Marker only; an inherited explicit root wins over it | Runtime agent id; no OS child binding | Agent self-report | Agent self-report | Unsupported for unattended state-writing lanes; remain attended |
| Interactive `claude` started in the worktree by the operator | Operator shell | Operator `cd`; the activation snippet exports the lane roots | Operator shell assigns values | Depends on the operator command | Operator typing | Interactive transcript | Valid for attended activation | Foreground CLI process | Transcript; no one-shot launch receipt | Operator plus session | Attended path only; a missing export is an operator-visible activation failure. Stays supported |
| Direct `claude -p` invoked by a caller in the worktree | Caller | Process cwd chosen by the caller | Inherits the caller environment | None supplied by Claude itself | Stdin or positional argument | `--output-format json` on stdout, or plain text | Unsafe when an inherited explicit lane root outranks the marker | Foreground CLI process, not descriptor-bound | Optional JSON on stdout | Claude process self-report | Unsupported directly; supported only behind the kit-owned wrapper |
| **Selected: kit-owned wrapper → `claude -p` (`process-cwd` / `stdin` / `json-stdout`)** | Descriptor `runtime` selects the config-owned template `parallel.claude_*`; the engine validates each declared transport against what Claude implements | Wrapper `chdir`s the fork-only observer into the descriptor worktree and seeds `PWD`; the child independently resolves physical cwd and Git top-level before `exec`; no worktree flag is passed because Claude Code takes cwd from the process | Unchanged from `#609`: permitted caller environment minus lane/repository overrides, trusted `PATH`, every descriptor key assigned unconditionally | Unchanged from `#609`: every `DEVKIT_*`, every `GIT_*`, `GH_REPO`, caller `PATH`, `PWD`, `OLDPWD`; non-standard descriptors closed | Combined prompt bytes written to the child's stdin after the observation handshake; no prompt argument, so the prompt never appears in argv or process listings | Child stdout is redirected onto the exclusively reserved empty final-message file before `exec`; after exit the parent accepts exactly one JSON object with `type=result`, `subtype=success`, `is_error=false`, and a non-empty string `result`; the receipt digests both the raw evidence bytes and the extracted text | Unchanged from `#609`: descriptor environment cross-bound to repository, state, and refusal identity; root must equal the marker and session state directory | Unchanged from `#609` | Unchanged from `#609`, plus `request.runtime`, `request.transports`, `terminal.final_text_transport`, and `terminal.final_text_sha256` | Unchanged from `#609` | Everything `#609` refuses, plus: a runtime the config does not template, a declared transport the runtime does not implement, empty or absent stdout, malformed or partial JSON, more than one JSON value, a non-`result` object, an error result, or an empty `result` string — each is a non-success terminal receipt that blocks descriptor reuse |
| **Retained: kit-owned wrapper → `codex exec` (`cd-flag` / `stdin-dash` / `last-message-file`)** | Descriptor `runtime` selects `parallel.codex_*` | `--cd <worktree>` plus the same observer `chdir` | Unchanged | Unchanged | Stdin with the `-` argument, as before | `--output-last-message <reserved file>`, as before; the extracted text is the file's bytes | Unchanged | Unchanged | Unchanged, plus the same new request/terminal fields | Unchanged | Unchanged; the child argv is byte-identical to `#609` |
| Claude Code remote or cloud session | Service environment | Service-selected checkout | Service configuration, not the local descriptor map | Not observable from the local lane engine | Service | Service transcript | Does not bind the local worktree marker and state sandbox | Remote session id | Service record | Remote service | Unsupported for a local `new --headless` descriptor |

## Supported contract

The supported unattended mechanism for either runtime is the one kit-owned Python
engine, `scripts/launch_lane.py` (renamed from `launch_codex_lane.py`; the old name is
retired rather than aliased). It consumes the descriptor issued by
`dev_session.sh new --headless --runtime <codex|claude>`, consumes the task prompt as
bytes, and starts the runtime's config-owned headless command inside the descriptor
worktree. The runtime adapter only invokes the shared workflow and names the
runtime-native mechanism; it selects no transport, environment, identity, retry, or
evidence policy.

The tracked configuration owns, per runtime, a flat set of keys under `parallel`:

- `<runtime>_headless_command` — the argv prefix; never a shell string.
- `<runtime>_worktree_transport` — `cd-flag` (Codex) or `process-cwd` (Claude).
- `<runtime>_prompt_transport` — `stdin-dash` (Codex) or `stdin` (Claude).
- `<runtime>_final_text_transport` — `last-message-file` (Codex) or `json-stdout`
  (Claude).

The keys are declarations, not free choices. The engine owns the vocabulary and the
argv each transport produces, and it refuses a declared transport the named runtime
does not implement, so a config edit cannot make Claude read its prompt from an
argument or make Codex report through stdout. A runtime whose command key is absent is
not supported, whatever the descriptor says. The shipped default for Claude is
`[claude, -p]`; a user-local installation such as `~/.local/bin/claude` is outside the
trusted executable path by design, so an adopter names the absolute binary in config.

The argv is assembled in one fixed order — command prefix, worktree arguments,
final-text arguments, prompt arguments — which reproduces the Codex argv of `#609`
exactly and yields `claude -p --output-format json` for Claude.

Claude receives `PATH` replaced by the trusted path, the descriptor environment, and
every other permitted caller variable. That includes runtime credentials and
configuration variables the operator's shell may carry; an alias such as
`env -u ANTHROPIC_API_KEY claude` is shell hygiene the wrapper does not replicate. The
live record for this slice runs from an environment that carries no API key. Claude
also writes its own session transcript under the user's Claude configuration
directory, keyed by the worktree path — runtime-owned state outside the lane sandbox,
the same class as Codex's session store.

This slice passes no permission flag. `claude -p` loads `CLAUDE.md` and project
settings from its cwd, but the live record then found that a freshly issued lane
worktree is an untrusted workspace whose committed `permissions.allow` entries Claude
ignores, so no project permission rule reached the lane. What a writing lane needs is
`#601`.

## Independent observation and evidence chain

Unchanged from `#609` except for the two additions below.

The request binding, computed identically by parent and child and compared before the
child may proceed, now also carries `runtime` and the three declared transports. A
child whose configuration resolves to a different runtime or transport than the parent
observed refuses at the authority check.

For `json-stdout`, the child verifies the reserved final-message path is still an
empty regular non-symlink file and duplicates it onto its stdout after the observation
handshake and immediately before `exec`, so no wrapper output can precede the
runtime's. The parent extracts the final text only after the child has exited and the
process group and launch lineage are gone; the terminal receipt binds
`final_message_sha256` (raw evidence bytes, as before) and `final_text_sha256`
(extracted text). For `last-message-file` the two digests are equal.

## Fail-closed outcomes

Everything in `#609`, plus:

- A descriptor whose `runtime` names a runtime without a configured command refuses
  before the attempt record is created.
- A declared transport outside the runtime's implemented vocabulary refuses before the
  attempt record is created.
- A child stdout that holds nothing, holds bytes that are not one complete JSON
  object, holds more than one JSON value, holds an object whose `type` is not
  `result` or whose `is_error` is not `false` or whose `subtype` is not `success`, or
  whose `result` is missing, non-string, or empty, terminalizes as `failed` with the
  reason named and leaves the exclusive attempt in place.
- The Codex argv and its evidence route are pinned by test; a change to either is a
  regression the suite reports, not a silent drift.

## Ownership boundary

Unchanged from `#609`. The descriptor issuer, the launcher, the receipt validator, and
the behavioral tests are kit-owned; the launch and failure policy lives in
`parallel-headless.md` and the runtime-parity capability row; both runtime adapters
stay thin. The seal remains corruption and descriptor-only rewrite evidence, not a
privilege boundary against the same OS account.
