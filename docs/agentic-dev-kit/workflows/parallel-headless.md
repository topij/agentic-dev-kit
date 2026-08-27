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
the wrapper redirects onto the reserved final-message file before `exec`.
`parallel.<runtime>_approval_policy` declares the approval/sandbox policy from the
same kind of engine-owned vocabulary and is passed as argv in the fixed slot after the
command prefix: Codex `read-only` / `workspace-write` (`--sandbox <value>`), Claude
`dont-ask` / `accept-edits` (`--permission-mode dontAsk|acceptEdits`). The shipped
Claude default is `dont-ask`, under which the profile's allow list is the whole
boundary: the profile grants file editing through `Edit(**)`, the one rule that
governs every file-editing tool at 2.1.247, which the runtime resolves relative to the
worktree root and never outside it (a bare `Edit` edits anywhere — observed live —
and the wrapper refuses it; a `Write(...)` entry is inert on that client, so scope
editing with `Edit(<pattern>)` and nothing else), and every Bash call outside the
declared prefixes is a denial.
`accept-edits` is declarable and is not the default because the runtime then also
auto-accepts its own class of file-system Bash commands inside the worktree — `rm`,
`mv`, redirection writes, and `cat` were observed accepted live at 2.1.247 with none
of them in the allow list — so under that value the allow list bounds only what the
runtime's own classifier does not already accept. Every
unrestricted spelling — `bypassPermissions`, `auto`, `manual`, `plan`,
`danger-full-access`, the `--dangerously-*` flags — is a non-member the wrapper
refuses before any attempt record exists, and a missing key refuses the same way; no
config value widens a lane to unrestricted. Shared
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
Model and reasoning-effort calibration remain separate from launcher identity. The
approval policy is not: it is the declared `parallel.<runtime>_approval_policy` above,
and the wrapper reads its outcome back. Do not read the checked-out project's rules as
standing in for it. A freshly issued lane worktree is an untrusted workspace to Claude:
the branch's committed `permissions.allow` entries are ignored there while its hooks
still execute, and the operator's own user settings (their default mode and allow
list) reach the lane by default. So the Claude trust route is the one the wrapper
builds and no other: `--setting-sources ""` loads neither the user's nor the branch's
settings, and the cockpit-owned profile named by `parallel.claude_settings_profile`
(shipped `config/claude-lane-settings.json`, seeded by `init.sh` when absent and
adopter-owned afterwards) is passed with `--settings` as the one settings source the
lane loads — its permission rules and its hooks apply, the branch's do not. The
wrapper refuses a profile that is missing, symlinked, not one JSON object, without a
`permissions` object, carrying `permissions.defaultMode` (the mode is declared once,
in config), or carrying a `Bash` allow entry with no literal command prefix — `Bash`,
`Bash(*)`, `Bash(**)`, `Bash(:*)`, `Bash(/*)`, anything whose pattern head (the
pattern read literally, up to the first wildcard, `:`, or space) holds no letter or
digit — decided by that structure, not by a list of spellings — or granting an edit
tool without a path pattern relative to the worktree root (`Write`, `Write(//…)`,
`Edit(../**)`). The guard judges the
shape of a prefix and never the command it names: `Bash(sh:*)` is a prefix an
adopter declared. The
profile is read and digested by the parent and again by the child, and the two
digests must agree; the bytes the runtime itself loads from the path at `exec` are
not re-read, so a writer on the same OS account who replaces the file inside the
child's observe-to-exec window is outside this check, the same boundary the
descriptor seal declares. Pre-trusting the worktree
path in the operator's Claude configuration is not a supported route: that trust is
keyed by a path `sessions/<scope>/wt` reuses, outlives the lane, and makes branch
content authoritative; neither is `--bare`, which never reads OAuth credentials and
drops the project contract. Do not edit the lane worktree's `.claude/` to change lane
policy — it is not read.

The approval transition is read, not assumed. Claude reports a refused tool call as a
`success` envelope whose only trace is a non-empty `permission_denials` list, so a
lane whose write was denied (or whose action would have prompted, which an unattended
`-p` session cannot do) terminalizes `failed` with the list preserved in
`terminal.permission_denials` and the declared policy named in the error; a result
with no list-valued `permission_denials` is refused rather than read as nothing
denied; `completed` carries `[]`. Through `last-message-file` the outcome is not
observable and the receipt carries `null`, never `[]`. The receipt also binds the
declared policy, its argv, and the profile path and digest in `request.approval_policy`,
and the exact argv the observer exec'd in `observed.argv`; the parent refuses an
observation whose argv omits the policy or the trust step. The Codex value is
validated and passed the same way, and its behaviour is not claimed until a Codex
writing-lane record exists; the shipped Codex default is `read-only` for that reason.
The shipped profile's allow-list is the minimum a writing lane needs to edit inside
its worktree (`Edit(**)`), commit, push its own branch, open and ready a PR, and poll
it; `git remote` is granted read-only (`get-url`, `-v`), because a broad
`git remote:*` let a lane retarget `origin` and push elsewhere through the
already-granted push form (panel round 11, live against a throwaway remote). The
push allow is `Bash(git push -u origin:*)`, the form the lane contract names
and the narrowest a rule can express: the runtime matches Bash rules on token
boundaries, so a branch-prefix allow (`git push -u origin lane/:*`) matched nothing
live — not even the lane's own push. The narrowed allow bounds only the verb and the remote name: it refuses the
flag-first and no-`-u` spellings the panel reproduced passing a broad
`Bash(git push:*)` (`git push origin :x`, `git push -uf …`, `git push --force …`,
`git push origin +HEAD:main`), and it bounds **nothing after `origin`** — a flag
(`git push -u origin --force x`, `git push -u origin -f x`), a deletion (`git push -u
origin :x`), and a forced refspec (`git push -u origin +HEAD:x`) all match it, every
one observed live against a throwaway remote. The deny entries for the flag
spellings catch only the flag-first placement. So the profile does not protect a
remote branch's history; that remains the forge's branch protection and the lane
contract's own-branch rule, and a deterministic lane-side push gate is follow-up
work, not a claim this contract makes. What else belongs in that profile as repository policy is `#606`, not this
contract.

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
