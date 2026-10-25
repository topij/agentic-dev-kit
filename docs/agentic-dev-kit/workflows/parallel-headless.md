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

Interactive `new` is operator-launched by design (it prints launch or activation
guidance, and the shared workflow says *don't start the session yourself*). That's
the wrong shape for an **unattended** batch — a background sub-agent or cloud
session that should drive a *sandboxed* lane without a human in the loop.
`--headless` is for exactly that:

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
  --prompt-file <task-prompt> \
  [--tier <cheap|default|expensive>] \
  [--ticket <issue-number>]
```

`--ticket` has the launcher read that GitHub issue with the trusted `gh` before launch
and append it after the task prompt, between `<<<TICKET` and `TICKET>>>` lines. The
request records `ticket` (`number`, `url`, `block_sha256`). The launch is refused (exit
64) before any attempt record when the number is not a positive integer,
`tracker.backend` is not `github-issues`, `tracker.url` is not an `https://` url, `gh`
is not on the trusted path, the read fails or times out, the answer's number, title or
body is missing or malformed, its url is not exactly `<tracker.url>/<n>`, with any
trailing slash on `tracker.url` dropped (which refuses a pull request with that number
and an issue of another repository or host), or its title or body contains `TICKET>>>`.

`--tier` applies the plan step's effort tier through `models.runtime_mappings`; without
it the lane inherits the client's compute. [`parallel.md`](parallel.md#per-lane-effort-tier-risk--reasoning-effort--model)
says what the wrapper passes and what the receipt records.

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
Claude default is `dont-ask`, under which the profile's allow list bounds every call
the runtime does not accept on its own: the profile grants file editing through
`Edit(**)`, the one rule that governs every file-editing tool at 2.1.247, which the
runtime resolves relative to the worktree root and never outside it (a bare `Edit`
edits anywhere — observed live — and the wrapper refuses it; a `Write(...)` entry is
inert on that client, so scope editing with `Edit(<pattern>)` and nothing else), and
a Bash call outside the declared prefixes is a denial — except for the read-only
class the runtime accepts regardless at 2.1.247 (`pwd`, `whoami`, `cat`, `grep`,
`find`, bare `git remote -v` ran with nothing in `permission_denials`, while `touch`,
`curl`, `env` and `git remote show` were denied). That acceptance is a property of
command **shape** and not of command name: a `for … do cat … done` loop and a
`;`-chained `grep`/`echo` compound were both denied at 2.1.250 in a session that
accepted plain `grep` and `cat` (`#628`), and under `dont-ask` such a denial is
terminal for the whole lane rather than a round trip. So a lane can read whatever its
process can read, and the receipt cannot show a read the runtime never asked about.

**Routine lane steps go through forms the profile accepts** (`#1011`, `#1081`, `#628`).
The record of compound commands is mixed: at 2.1.250 a `for` loop and a `;` chain of
accepted reads were denied (above), while `make test; echo …` ran (below). Probed at
Claude Code 2.1.310 on 2026-10-25 with the shipped profile under `dontAsk`: an `&&`
chain, a pipe, a `for` loop and a `;` chain of allowed `git` commands all ran, and
`git status --short && touch probe-denied.txt` was denied whole. The lane contract
therefore states the rule both records agree on: every part of a command must be
allowed, one refused part ends the run, and one simple command per call is the safe
default. It also tells every lane to write commit messages and pull-request text to
files under the worktree's `<state.dirname>/lane/`, never to stage that directory
(`init.sh` adds `state/` to `.gitignore` only when it can), to pass them with `git
commit -F` and `gh pr create --body-file`, and to undo a worktree change with `git
restore`. A headless lane is also told to put its verification result in the body before
opening and to report anything later, including a draft-exception lane's remote result,
in its final text instead of editing the body; an interactive lane keeps the ordinary
`gh pr comment` replies of `pr-watch.md`. The shipped profile grants `Bash(git restore:*)` for the
last and grants neither `gh pr edit`, which could retarget a pull request's base, nor
`gh pr comment`, whose `--delete-last`, `--edit-last` and `--repo` reach other comments
and repositories. A lane's ticket arrives through `launch_lane.py --ticket`, so the
profile grants no tracker read either; probed at 2.1.310 on 2026-10-25 under the lane's
own flags, `gh issue view` was denied. A probe that drops `--setting-sources ""` loads
the operator's own settings and can show it allowed, which says nothing about a lane.

**What the allow list bounds is the lane's task, not its reach** — see the profile
discussion below, where `#606` states the two directions in which "bounds what a lane
can do" is wrong: a class of write it cannot authorize, and a class of execution it
authorizes with no rule in any list. `accept-edits` is declarable and is not the default
because the runtime then also auto-accepts its own class of file-system Bash commands
inside the worktree — `rm`, `mv`, and redirection writes were observed accepted live at
2.1.247 with none of them in the allow list (`cat` ran too, and belongs to the read-only
class above that either value accepts) — so under that value the allow list bounds only
what the runtime's own classifier does not already accept. Every unrestricted spelling —
`bypassPermissions`, `auto`, `manual`, `plan`, `danger-full-access`, the
`--dangerously-*` flags — is a non-member the wrapper refuses before any attempt record
exists, and a missing key refuses the same way; no config value widens a lane to
unrestricted. Shared across runtimes, `parallel.descriptor_ttl_seconds` supplies
descriptor lifetime, `parallel.observation_timeout_seconds` bounds the child observation
handshake, and `parallel.termination_grace_seconds` bounds graceful cleanup before
forced process-group termination, and `parallel.max_resumes` bounds how many times one
launch resumes a lane that stopped without a terminal state (below). Resolve all through
the merged config; never restate them in an adapter or fixture. A user-local runtime
install, such as `~/.local/bin/claude`, is outside the wrapper's trusted executable
path by design. The supported route is host placement: link the binary into one of the
trusted directories (the system defaults plus `/opt/homebrew/bin`, `/usr/local/bin` and
`/opt/local/bin`) and keep the bare command name in the config. On macOS with Homebrew,
for example, `ln -s ~/.local/bin/claude /opt/homebrew/bin/claude`. A bare name the
wrapper cannot find is refused with those directories named; an absolute command is
used as written and never looked up, so its refusal names the file. Do not name the
absolute binary in the tracked config, which would hand one host's layout to every
checkout, and the gitignored local overlay does not accept these keys: a file nobody
reviews would then choose the binary the wrapper runs.

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

**Terminal state and bounded resume.** A lane given the contract verbatim still stopped
to wait for a watcher or for its own subagents (`#514`, `#564`), so the launcher checks
for the end instead of trusting the instruction. The contract asks the lane to end its
final text with one plain-text line: `LANE-TERMINAL: pr-ready #<n>`, `LANE-TERMINAL:
no-pr <reason>` or `LANE-TERMINAL: blocked <reason>`. The wrapper splits the final text
as Python's `str.splitlines` does, so a vertical tab, form feed, file, group or record
separator, U+0085, U+2028 or U+2029 also ends a line. It reads only the last non-blank
line, with surrounding whitespace stripped, and needs the whole line to match: a line
quoted earlier, wrapped in backticks or followed by more lines is no terminal state. For
`no-pr` and `blocked` the rest of the line is the reason: up to 200 characters of
printable text in Python's `str.isprintable` sense, so no control characters (C0, DEL or
C1), no format characters such as bidi overrides or zero-width spaces, and no separator
other than the ordinary space. The receipt records what it declared as
`terminal.lane_state`.

A successful run without that line is a nonterminal stop. For a Claude lane the wrapper
resumes the same runtime session (`--resume <session_id>`) with one fixed nudge that
restates the terminal rule and names nothing new to do, at most `parallel.max_resumes`
times. A resume continues the launch the wrapper already bound and needs no new
descriptor: it runs from the same wrapper process, in the worktree, with the scrubbed
environment and the launch's lineage nonce, and with the launch argv's command, trust
step, approval policy, settings profile and compute plus only `--resume <session_id>`.
The session id must be a canonical UUID. Each round reserves its own
`launch-final-<id>-resume-<n>.txt`, gets the same process-group and lineage cleanup as
the launch, and is recorded in `terminal.resumes` with its argv, digests, return code,
denials, usage and terminal state. A round that a refusal cuts short (a termination or
evidence read the wrapper refuses) is still recorded, with the fields it never reached
`null` and `error` set to `round did not finish`; an interrupted round's `error` is
`launcher interrupted`, unless a refusal also cut it short, which leaves
`round did not finish`. A signal that lands before a round starts stops the loop without
starting one. A signal the wrapper records after it has read a declared terminal state
leaves the receipt `completed`; one recorded before that read, at launch or while a
resume round runs, records the lane `interrupted`. A failed, denied or interrupted
round, at launch or on resume, is never resumed. While a round runs, the receipt stays
`observed`, so the board shows `running`.

Observed live with Claude Code 2.1.310 on 2026-10-25, from a clone whose primary
checkout was a commit since rebased, with the same tree, as `c60680a4`: a `--tier cheap`
lane told to answer only `READY` ended its launch round without the line, was resumed in
the same session under `dontAsk` and the lane profile, ended with a `no-pr` line, and
was recorded `completed` with one entry in `terminal.resumes`.

A lane that still names no terminal state is recorded `stalled` and the wrapper exits
75; one that cannot be resumed is recorded `stalled` at once. That covers a Codex lane,
whose final-message file carries no session id, `max_resumes: 0`, and a result with no
canonical session id. Exit statuses: 0 `completed`, 75 `stalled`, 70 `failed`, 64
refused before launch, 128+N interrupted by signal N.

`completed` and exit 0 cover every declared terminal state, `blocked` included: a
caller that must tell a blocked lane from a finished one reads `terminal.lane_state`.

Before each resume round the wrapper re-reads the settings profile and refuses, failing
the lane, unless its digest still equals the request's `settings_profile_sha256`: the
launch round can write files, and the profile is one. The executable path and the
worktree, the other launch-time values a resume reuses, are not re-checked; the launch
round execs by path in the same way. The wrapper checks that the lane *declared* an end,
not that a `pr-ready #<n>` names a real, ready pull request.

The nudge does not restate the lane's PR or CI state; the lane reads that itself.
`terminal.usage` covers the launch round only, so a lane's total is it plus every
`terminal.resumes[].usage`.

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

The repository a lane must belong to is named by its Git common directory, not a
checkout path. The descriptor's repository root is the checkout whose config and engine
issue and authorize the launch, and the wrapper holds it to its own config root; the
child then holds its worktree's common directory to that checkout's. The primary
checkout and every linked worktree of a repository share one common directory, so a
descriptor issued from a linked cockpit worktree launches as one issued from the primary
does, and a checkout of any other repository is refused even when its path, branch,
commits and origin URLs all match. The receipt records the comparison as
`expected.git_common_dir` and `observed.git_common_dir`.

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
Model and reasoning-effort remain separate from launcher identity: the wrapper carries
neither, and a lane inherits what its trust route resolves to (`parallel.md`, *How the
tier reaches the lane*). The approval policy is not: it is the declared `parallel.<runtime>_approval_policy` above,
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
`permissions` object, carrying any `permissions` key other than the three rule lists
`allow`, `deny`, `ask` — `defaultMode` (the mode is declared once, in config),
`additionalDirectories` (the settings form of `--add-dir`, tool access beyond the
worktree with no rule in any list), or a key the wrapper does not recognise, refused
rather than passed through because an entry this client ignores may be honoured by
another — or carrying a `Bash` allow entry with no literal command prefix — `Bash`,
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
it; `git remote` is granted as `get-url` only, because a broad `git remote:*` let a
lane retarget `origin` and push elsewhere through the already-granted push form
(panel round 11, live against a throwaway remote), and `git remote -v:*` admitted
`git remote -v set-url` the same way, `-v` being a modifier (round 12, live) —
`get-url` is the subcommand token itself, and git accepts nothing after it but its
own `--push`/`--all` flags and a remote name. The
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
work, not a claim this contract makes.

**The profile scopes a lane's task; it is not a security boundary, and the difference
is measured rather than conceded.** `Edit(**)` bounds file *edits* to the worktree; it
does not bound a *process*. So a `Bash(<interpreter> <worktree-path>)` entry names a
file the lane is separately allowed to rewrite, and the two grants compose into
something neither one says. Under the shipped profile with **nothing added**, a lane
asked to rewrite `scripts/pr_watch.py` — already granted
`Bash(uv run scripts/pr_watch.py:*)` — so that it writes an absolute path outside the
worktree, and then to run it, did exactly that and returned an empty
`permission_denials` (`#606`, Claude Code 2.1.250, 2026-08-28, evidence bundle in
`saved_plans/lane-permission-policy-evidence_2026-08-28/`). The escaped file is read
back from the host filesystem in that bundle's `escape-readback.txt` rather than taken
from the probe's own account of itself, because a probe narrating success and a probe
that actually escaped are otherwise the same evidence — a delta-pass lens named that
gap. No spelling of that entry
closes it while the lane can write the file it names: a command-prefix allow list
cannot constrain the *contents* of a file its prefix names. Closing it would need a
different mechanism — an OS sandbox around the child, or granting only scripts
resolved from outside the lane-writable worktree — which is `#631`, not an edit to
this profile.

**`#631` is decided as a declaration rather than a mechanism (2026-09-05).** Neither
route above is adopted. **What bounds a lane is the worktree and the forge's branch
protection** — and it always was. Read that as naming what each one bounds, not as a
containment guarantee: `Edit(**)` scopes the lane's tool-mediated file edits to the
worktree, and branch protection scopes what can reach the protected branch's history.
**Neither of them bounds the lane's process**, and the escape measured just above is
exactly a process leaving the worktree — so a lane that rewrites a granted engine and
runs it is outside both, and this declaration claims nothing the *confused lane*
paragraph below withdraws. The profile was never a third thing standing beside them, so
naming the pair concedes nothing that was previously true. **The Codex mirror of
that boundary is `--sandbox workspace-write`**, the value already beside the shipped
`read-only` in `launch_lane.py`'s engine-owned vocabulary. It mirrors because it
bounds the same territory, not because it renders the allow list into another syntax:
**the Claude prefix list and the Codex sandbox value are not interchangeable** and do
not map entry-for-entry, which is `runtime-parity.md`'s "the mirror to Codex is the
doctrine, not the grants" stated from this side. A Codex writing lane inherits the
boundary and not the entries.

**No lane-side execution guard is built without a request for one.** That is the
operative half of the declaration, and the reason it is written here rather than left
implicit: a session that reads the composition above is invited to close it, and
closing it is an *addition* — `safety-critical-changes.md` rule 3's trap, on a file
that gates launch authority, where three unrequested mechanisms each became a later
HIGH. The composition is a documented limitation that fails **closed** for the
confused lane this profile is for; a guard invented against it trades that for a
fail-open surface nobody asked for and nobody scoped. A process-level boundary is
available to an adopter who needs one, as a request: it gets its own issue, its own
executable positive construction, and its own locally recomputed hostile mutation,
not a fix round on this file.

What the profile does deliver, and what the allow list should be read as bounding, is
**fail-closed behaviour for a confused lane**: one that wanders off-task reaches for
something no rule covers, is denied, and the wrapper terminalizes the run `failed`
with a legible record of what it reached for. That property is untouched by the
composition above, because a confused lane does not rewrite an engine to escape.
Against a lane that is actively hostile, or prompt-injected into acting like one, this
profile has never been the thing standing in the way — the descriptor seal already
disclaims that boundary above, and the allow list does not reinstate it.

So the shipped grants are decided on what each one **buys** a lane. `#606` settled the
grantable questions — these two — and then the `.claude/` question below, which no
grant reaches:

- **`Bash(make test:*)`** — `AGENTS.md` makes `make test` the repository's verification
  command and forbids deferring verification to CI without running it; a lane could not
  comply, structurally. Probed at Claude Code 2.1.250 on 2026-08-28 under the shipped
  profile before the grant: `make test` and a bare `uv run pytest` were refused, with a
  `cat` in the same session accepted as the live control. It needs no companion
  `uv`/`uvx` entry, because the permission check is on the Bash tool call and not on
  what the recipe spawns.
  **Read the entry as admitting a command whose argv begins with `make test`, which is
  not "the `test` target":** at that same client and date, standalone
  `make mutation-test` was refused while `make test mutation-test` ran both goals. The
  match is on argv tokens rather than raw text, so `make test-exfil` and
  `make testing-foo` were refused as well — "begins with" bounds the leading tokens,
  not a string prefix. A panel lens falsified the stronger "bounded to the one target"
  claim by running the two-goal form, and a delta-pass lens established the token
  boundary; both were corrected here rather than hedged.
- **`Bash(uv run scripts/kit_doctor.py:*)`**, and the `scripts/devkit/` spelling beside
  it as `pr_watch.py` already has — because a lane editing any kit-owned file must
  refresh the manifest or its PR is deterministically red, which costs the lane its
  whole result rather than one check. Granted bare rather than scoped to
  `--generate-manifest`, so that checking the manifest before regenerating it does not
  end the run. It admits `#464`'s broken redirect exactly as it admits the correct
  invocation; a prefix rule cannot see a redirect, so that belongs in the lane contract.
  **A task prompt for a lane that may edit a hashed file names the allowed form
  verbatim:** `uv run scripts/kit_doctor.py --generate-manifest`, which writes the
  manifest itself and must not be redirected. The pre-push hook's refusal message
  names only `kit_doctor.py --generate-manifest`, and a `python3 scripts/kit_doctor.py`
  call matches no entry here and is denied; lanes that reached for that spelling
  stopped without a PR (`#1102`).

**A lane doing kit-owned Claude-adapter work is not a supported case** (`#606`
deciding `#627`). A lane cannot write under `.claude/` — measured across `commands/`,
`rules/`, `agents/`, `settings.json` and the bare directory, in two repositories and
under two file-editing tools, in a session that wrote `.agents/`, `docs/` and
`.github/workflows/`. Neither the `Edit(**)` glob nor dot-directories is the mechanism,
and **no allow-list entry reaches it**: it is the client's own guard, so the profile
cannot authorize it and no future entry here will. The supported route for a
runtime-parity change is to split it — the lane takes the runtime-neutral half and the
Codex adapter, the cockpit takes the `.claude/` half — which is what `#625` did by
necessity. Do not send a lane at `.claude/` and read the resulting `failed` as a lane
defect.

Both findings correct the same sentence, in opposite directions: this profile does not
bound "what a lane can do". There is a class of write it **cannot authorize**
(`.claude/`), and a class of execution it **authorizes with no rule in any list** (the
composition above).

**A behavioral change to this profile is safety-critical.** A profile-only edit changes
what the unattended client is authorized to run even when `launch_lane.py` is
byte-identical. The Codex binding in `AGENTS.md` names the profile configured by
`parallel.claude_settings_profile`; Claude's path-scoped rule names the shipped
`config/claude-lane-settings.json` and requires that entry to follow the config when
an adopter relocates it. Both bindings route to the same
`safety-critical-changes.md`; neither carries a runtime-specific copy of its doctrine.
This decision is specific to the dedicated policy file. It does not put all of
`config/dev-model.yaml` under the path trigger, which cannot distinguish
`parallel.*` keys from unrelated configuration.

**What a matched prefix does not do is swallow the rest of a compound command**, and
the distinction is worth stating because it is easy to measure wrongly. Each segment of
a compound is permission-checked on its own. Probed at Claude Code 2.1.250 on
2026-08-28: `make test; curl …` and `git status; curl …` were both refused against a
bare `curl` control that was refused too, while `make test; echo …` ran — `echo` being
accepted on its own, not carried in by the prefix. A delta-pass lens extended this
across every operator it could reach — `&&`, `||`, `|`, backtick substitution, `$()`,
`<()`, and an env-assignment prefix, plus `eval` and `bash -c` — and found none that
carried a denied segment through a granted one.

That distinction had to be measured, not reasoned: a panel lens ran only the `echo`
form, read it as the prefix widening to arbitrary shell, and reported a HIGH. The
accept-form evidence cannot separate "the prefix carried the rest" from "both parts
were acceptable anyway"; only the denied-segment case does. So chaining is not a route
around the allow list, and `#631`'s composition — rewrite a granted engine, then run
it — remains the one that is.

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
