# Unattended / headless parallel lanes

Companion to [`parallel.md`](parallel.md), split out so an agent only pays for this
content when it's actually launching an **unattended** lane — a background sub-agent
fan-out, a cloud session, or any launcher driving a lane with no human at a terminal.
The board (`list` / `list --watch`), `plan`, interactive `new`, the per-lane
effort-tier and merge-class tables, finishing a session, and the joint wrap-up all stay
in [`parallel.md`](parallel.md); this file is only the headless launch mechanics:
the `--headless` flag, its JSON descriptor, the lane-contract preamble every headless
launch must inject verbatim, and the fan-out recipe.

### Unattended / headless launch — `new --headless`

Interactive `new` is operator-launched by design (it prints a copy-paste line and the
rule above says *don't start the session yourself*). That's the wrong shape for an
**unattended** batch — a background sub-agent or a cloud session that should drive a
*sandboxed* lane without a human in the loop. `--headless` is for exactly that:

```bash
<engine-dir>/dev_session.sh new --headless <scope> --merge-class <self|operator> --runtime <codex|claude>
```

It creates the worktree + sandbox exactly as `new` does, but instead of the human
block it:

1. **Writes a sticky `<worktree>/.devkit_state_root` marker** holding the absolute
   sandbox path. This is the mechanism that makes a headless lane safe: a background
   sub-agent's shell calls don't share a shell, so an exported `DEVKIT_STATE_ROOT`
   doesn't survive call-to-call. Your state-sandbox resolver reads the marker
   (walking up from cwd) when the env var is unset, so the lane's `state/` writes
   isolate into the sandbox **automatically** — no env gymnastics in the prompt.
   (Precedence: env var → marker → repo-root default. Cron/CI writes no marker, so
   it's unaffected.)
1. **Persists a canonical JSON descriptor beside the lane metadata and prints those
   same bytes to stdout** (diagnostics go to stderr, so stdout is clean JSON). The
   descriptor binds its schema and one-shot id; issue/expiry window; descriptor,
   session, worktree, state, and repository roots; origin, scope, branch, base,
   merge class, base and lane commits; prompt preamble; environment; and runtime.
   `prompt_preamble` is the canonical lane-contract text
   below — the launcher **MUST** prepend it verbatim to the lane's task prompt. `env`
   carries lane-specific `DEVKIT_STATE_ROOT`, `DEVKIT_ROOT`, and
   `DEVKIT_REFUSE_UNSANDBOXED_STATE=1`. A separately persisted rewrite seal binds the
   exact descriptor digest and id, and the launcher cross-binds this environment map to
   the descriptor repository, state root, and refusal identity. The launcher **MUST replace inherited values
   with this map**: the resolver gives an explicit env root precedence over the marker,
   so inheriting the cockpit's root would collapse every child lane into one sandbox.
   The refusal flag flips the unsandboxed-write guard from *warn* to *refuse* — so a lane
   whose marker resolution somehow fails (deleted marker, cwd escaped the worktree)
   hard-errors on a `state/` write instead of silently landing in prod. Interactive
   `new` and cron/CI never set either field.

   The supported wrapper removes every inherited `DEVKIT_*` and `GIT_*` key, plus
   `GH_REPO`, caller `PATH`, `PWD`, and `OLDPWD`; then it installs the engine-owned
   trusted executable path and assigns every key from
   `env` unconditionally and seeds `PWD` from the descriptor worktree. The child then
   resolves its physical cwd independently and rejects disagreement with that seeded
   value. Do not use `setdefault`, skip a key because it is already present, or rely
   on the marker to beat an inherited root. Unrelated permitted variables remain
   available; the descriptor map is complete for lane-root identity, not a complete
   process environment. Before runtime exec, the observer closes every non-standard
   inherited file descriptor. An internal launch-lineage nonce is added only after the
   child has observed the exact descriptor environment; it lets the parent detect and
   terminate descendants that detach from the original process group.

### The lane-contract preamble (inject this verbatim)

Every mechanism that hands a task prompt to a headless lane — a multi-agent
workflow fan-out, a single-background-sub-agent fallback, or any future launcher —
**MUST prepend the same fixed contract text** ahead of the task-specific
instructions. This is the fix for an idle-stall failure mode: a rule that lives only
in a memory or in this doc's prose can't bind a freshly spawned lane, because a fresh
agent has no memory and doesn't read `parallel.md` unless told to. The contract must
be *in the prompt itself*, every time.

Fetch the current text with `<engine-dir>/dev_session.sh print-contract` (plain text, no
JSON) or read it straight off the `prompt_preamble` field of any `new --headless`
descriptor — **do not hand-copy or paraphrase it into this workflow or a launcher**.
Always read it fresh from one of those two engine surfaces so a future edit propagates
without maintaining a second copy.

**Supported unattended launch contract — Codex and Claude.** Run `new --headless
--runtime <codex|claude>` once (or set `DEVKIT_RUNTIME` for descriptor issuance), write
the task-specific prompt to a regular file, and invoke the one config-owned kit engine
with the persisted descriptor path. The descriptor's `runtime` selects the template;
the wrapper refuses a descriptor whose runtime has no configured command.

```bash
python3 <engine-dir>/launch_lane.py \
  --descriptor <session>/launch-descriptor.json \
  --prompt-file <task-prompt>
```

Per runtime, `parallel.<runtime>_headless_command` supplies the argv prefix (the
shipped values select stable `codex exec` and `claude -p`), and
`parallel.<runtime>_worktree_transport`, `parallel.<runtime>_prompt_transport`, and
`parallel.<runtime>_final_text_transport` declare how the runtime is told its
worktree, receives its prompt, and returns its final text. Those declarations are
checked, not chosen: the engine owns the vocabulary and the argv each transport
produces, and refuses a declaration the named runtime does not implement. Codex
declares `cd-flag` / `stdin-dash` / `last-message-file` — `--cd <worktree>`, the
prompt on stdin behind a `-` argument, final text through `--output-last-message`.
Claude declares `process-cwd` / `stdin` / `json-stdout` — the working directory is the
child process's own, the prompt arrives on stdin with no argument, and the final text
is the `result` of the one JSON object `--output-format json` prints on stdout, which
the wrapper redirects onto the reserved final-message file before `exec`. Shared
across runtimes, `parallel.descriptor_ttl_seconds` supplies descriptor lifetime,
`parallel.observation_timeout_seconds` bounds the child observation handshake, and
`parallel.termination_grace_seconds` bounds graceful cleanup before forced process-
group termination. Resolve all through the merged config; never restate them in an
adapter or fixture. A user-local runtime install is outside the wrapper's trusted
executable path by design: name the absolute binary in the command.

The wrapper is the supported mechanism because it owns the guarantees a native agent
dispatch or direct `codex exec` / `claude -p` call does not: worktree `cwd`,
inherited-identity removal, trusted executable lookup, descriptor environment
replacement and rewrite seal, session-scoped one-shot attempt and final-path
authority, and a fork-only child observer with no public direct entry that reads Git
fetch/push origin identity, the marker, persisted lane metadata, filesystem
relationships, a freshly derived canonical prompt contract, and its own process before
`exec`. It writes a receipt in the session directory, binds the exact
descriptor/task/combined-prompt bytes plus the runtime and its declared transports,
and returns success only after the runtime command exits successfully and a durable
terminal receipt binds the final-message evidence bytes and the extracted final text
by digest. For Claude, an empty stdout, malformed or partial JSON, more than one JSON
value, a non-`result` object, an error result, or an empty `result` is a failed
terminal receipt, never success.

The descriptor, rewrite seal, and receipt fail closed on expiry, descriptor-only byte
rewrite, or reuse; a moved descriptor; a descriptor environment that disagrees with its repository,
state root, or refusal identity; a substituted id or issue window; a
foreign repository, worktree, origin fetch/push identity, scope, state root, branch,
base, commit, prompt contract, or merge class; an occupied attempt or final-message
path; a child
process that does not hold the current launch capability; a child leader that exits
while its process group or detached launch lineage remains; interruption; an inherited
non-standard file descriptor reaching runtime exec; missing observation; nonzero child exit;
or missing final text. A parent killed before
it can finalize leaves the exclusive attempt record, so retry cannot silently reuse
the descriptor. Issue a fresh lane descriptor only after accounting for the partial
lane and attempt.

The rewrite seal detects corruption or replacement of the supplied descriptor while
kit-owned session evidence remains intact. It is not a security boundary against a
process already controlling the same OS account and able to replace the seal, metadata,
engine, worktree, or receipt together; that stronger signer/broker problem is outside
this local mechanism.

Do not hand this descriptor to native in-session agent dispatch on either runtime, a
desktop task, Codex cloud, a Claude remote session, or direct `codex exec` /
`claude -p`: those surfaces do not apply this complete local
worktree/environment/receipt contract. App-server is experimental and is not selected
for this bounded mechanism. Keep the lane attended when the wrapper is unavailable.
Model and reasoning-effort calibration, and the approval or permission policy a
writing lane needs, remain separate from launcher identity; a lane runs under the
checked-out project's own hooks and permission rules, which `claude -p` loads from its
cwd.

Every supported launcher must still prepend `prompt_preamble` verbatim and must not
open a second worktree on top of `new --headless`. The wrapper does both by consuming
the existing descriptor and constructing the combined prompt itself.

**When to use which.** Attended work (operator at a terminal) → plain `new`.
Unattended pipeline-touching work (any lane that writes `state/cache/`) → `new
--headless` so the sandbox is active without a surviving shell export. This is the
`parallel` vs bare-background-agent decision rule: *does the lane write `state/`? →
it needs a sandbox → `new --headless`, not a bare background worktree.* This should be
**guarded, not just documented**: your state-sandbox write path should warn when an
unsandboxed lane (no `DEVKIT_STATE_ROOT`, no marker, job-name env unset, in a linked
worktree) writes repo-root `state/` — and `new --headless` sets
`DEVKIT_REFUSE_UNSANDBOXED_STATE=1` by default (the `env` descriptor field + activate
snippet above) to make that a hard error rather than a warning. Cron/CI and normal-
interactive paths are unaffected.
