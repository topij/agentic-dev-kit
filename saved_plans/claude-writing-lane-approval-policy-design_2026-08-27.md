# Writing-lane approval policy design — 2026-08-27

## Slice boundary

This design adds a config-owned approval/sandbox policy per runtime beside
`parallel.<runtime>_headless_command`, passed mechanically by `scripts/launch_lane.py`,
and on Claude the trust-establishment step the `#611` live record exposed. It then
takes a Claude-authored writing-lane live record whose evidentiary boundary extends the
`#611` record from read-only observation to a scoped write, commit, push, pull request,
and cockpit-side review through `dev_session.sh pr-watch` on a synthetic repository.

It does not calibrate model or reasoning effort (`#605`, `#255`), run a first real
headless task (`#602`), decide Claude's shipped permissions as repository policy beyond
what the lane trust route needs (`#606`), produce the Codex writing-lane record or
claim Codex approval behaviour (the follow-on Codex session), adapt a downstream
repository (`#607`), generate adapters, or write to the tracker without a
payload-specific approval.

Everything `#609` and `#611` established stays in force unchanged: descriptor seal and
authority binding; complete environment replacement; every inherited `GIT_*` key,
`GH_REPO`, `PWD`, `OLDPWD`, and caller `PATH` removed; trusted executable lookup;
independent child observation of worktree, repository, origin fetch/push identity,
lane branch/base, state root, environment, and process; live descriptor enumeration
and fail-closed unavailability; launch-nonce lineage containment; act-time
revalidation before every signal; one-shot attempts; terminal receipts; the
config-declared transports; and the pinned Codex argv shape. The policy is a new argv
contribution the engine validates per runtime in the same shape as the transports.

## Product surface inventory

`claude --version` on 2026-08-27 printed `2.1.247 (Claude Code)`; `codex --version`
printed `codex-cli 0.149.1`. The flags below are quoted from each client's `--help`
output on that date; they supply the candidate surface, and only the probes and the
live record supply behaviour.

- `claude --help`: `--permission-mode <mode>` with choices `acceptEdits`, `auto`,
  `bypassPermissions`, `manual`, `dontAsk`, `plan`; `--settings <file-or-json>` ("load
  additional settings from"); `--setting-sources <sources>` ("Comma-separated list of
  setting sources to load (user, project, local)"); `--allowedTools` /
  `--disallowedTools`; `--bare` ("skip hooks, LSP, plugin sync, attribution,
  auto-memory, background prefetches, keychain reads, and CLAUDE.md auto-discovery
  … Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper via --settings (OAuth
  and keychain are never read)"); `--dangerously-skip-permissions` and
  `--allow-dangerously-skip-permissions`. The `-p` entry itself states: "The workspace
  trust dialog is skipped when Claude is run in non-interactive mode … Only use this in
  directories you trust."
- `codex exec --help`: `-s, --sandbox <SANDBOX_MODE>` with possible values
  `read-only`, `workspace-write`, `danger-full-access`; `--approve-for-me`;
  `--dangerously-bypass-approvals-and-sandbox`; `--dangerously-bypass-hook-trust`;
  `-c <key=value>` config overrides. No `--ask-for-approval` or `--full-auto` flag is
  listed for `exec` at this version.

### Trust probes (Claude)

Run on 2026-08-27 against `claude` 2.1.247 in a fresh Git directory under
`/private/tmp` that no entry in `~/.claude.json` trusts, with `ANTHROPIC_API_KEY`
unset (OAuth), a committed `.claude/settings.json` carrying
`permissions.allow: ["Bash(touch:*)"]` and a `SessionStart` hook that creates
`hook-project-ran`, and a separate profile file carrying the same allow entry and a
`SessionStart` hook that creates `hook-profile-ran`. Every invocation was
`claude -p --output-format json` plus the flags in the row; each prompt asked for
exactly one `touch` through Bash or one file through Write and nothing else.

| Probe | Flags | Observed |
| --- | --- | --- |
| P1 | none | stderr: "Ignoring 1 permissions.allow entry from .claude/settings.json: this workspace has not been trusted … or set projects[…].hasTrustDialogAccepted: true in /Users/topi/.claude.json". The `touch` ran, `permission_denials` was empty, and **the project `SessionStart` hook executed** (`hook-project-ran` present). The command ran because the operator's user settings reached the session: `~/.claude/settings.json` declares `permissions.defaultMode: auto`. |
| P2 | `--setting-sources project` | Same stderr. `touch` **denied**: `permission_denials` held one Bash entry while the envelope still read `subtype=success`, `is_error=false`. |
| P3 | `--setting-sources project --permission-mode dontAsk --settings <profile>` | Same stderr for the project file; the **profile's allow entry was honoured**: `touch` ran, exit code 0, no denial. |
| P4 | `--setting-sources "" --permission-mode dontAsk` | No stderr. `touch` **denied** in `permission_denials`; envelope `success`. Neither hook file was created. |
| P5 | `--setting-sources project --permission-mode acceptEdits --settings <profile>` | Write **accepted**; both `hook-project-ran` and `hook-profile-ran` created. |
| P6 | `--setting-sources project --permission-mode dontAsk --settings <profile>` | Write **denied** in `permission_denials` (the profile allows only `touch`); envelope `success`. |
| P7 | `--setting-sources "" --permission-mode dontAsk --settings <profile>` | No stderr. `touch` ran, exit code 0, no denial; `hook-profile-ran` created, `hook-project-ran` **absent**. |
| P8 | `--setting-sources "" --permission-mode dontAsk` (repeat of P4 checking hook files) | `touch` denied; neither hook file created. |

### Instruction-visibility probes (Claude)

Same directory and client, later the same day, after the lane runs below had shown
`claude_md_marker=not-seen`. A `CLAUDE.md` holding `SYNTHETIC-CONTRACT-MARKER` was
added and each invocation asked, with no tool use, whether that text was in context.

| Probe | Flags | Observed |
| --- | --- | --- |
| C1 | none | `seen`; stderr carried the same "Ignoring … permissions.allow" line as P1 |
| C2 | `--setting-sources ""` | `not-seen`; no stderr |
| C3 | `--setting-sources project` | `seen`; same stderr as C1 |
| C4 | `--setting-sources user` | `not-seen`; no stderr |

`CLAUDE.md` discovery follows the `project` setting source. The selected route
therefore drops the branch's project instructions along with its settings, and the
lane contract preamble the wrapper prepends is the only project-level text that
binds a Claude lane. That is a limit of this slice, recorded in
`parallel-headless.md`; re-injecting a cockpit-owned instruction file is a separate
decision.

Three facts the design rests on:

1. **A denied action is not an error result.** The envelope stays
   `type=result`, `subtype=success`, `is_error=false`; the denial is only visible in
   `permission_denials`. An engine that accepts the envelope alone would mark a lane
   whose write was refused as `completed`.
2. **Settings from two inherited sources reach an unattended lane by default**: the
   operator's user settings (here `defaultMode: auto` and its allow list) and the
   untrusted checked-out branch's project settings, whose `permissions.allow` is ignored
   but whose **hooks execute**. Only `--setting-sources ""` excluded both.
3. **`--settings <file>` is honoured in an untrusted workspace**, including its
   permission rules and hooks, with or without the project source loaded.

## Trust-route selection matrix (Claude)

| Route | Mechanism | Persistent state written | What it makes authoritative in the lane | Observable by the child observer | Available under OAuth auth | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Pre-trust the lane worktree path | Write `projects["<worktree>"].hasTrustDialogAccepted: true` into `~/.claude.json` before launch | Yes — operator-owned runtime state outside the lane sandbox, keyed by a path that `sessions/<scope>/wt` reuses after `rm` and a later `new` | The checked-out branch's `.claude/settings.json` in full: its allow list and its hooks, with no operator watching | Only by reading operator state; nothing in argv or the receipt | Yes | **Rejected**: standing trust outlives the lane and grants branch content the very authority the record found withheld |
| Kit-owned settings profile via `--settings`, with `--setting-sources ""` and `--permission-mode` | Argv contribution built from config; profile read from the cockpit tree, not the lane worktree | None | Exactly the config-declared mode and the cockpit-owned profile; neither user nor branch settings load (P7/P8), and neither does the branch's `CLAUDE.md` (C2) — the lane contract preamble is what binds | Yes: argv is recorded in the observation receipt; the profile path and digest are in the request binding both sides compute | Yes (P3, P5, P7) | **Selected** |
| `--bare` with the project contract re-injected | `--bare` plus `--append-system-prompt`/`--add-dir` | None | Nothing from the workspace; contract must be re-supplied by the wrapper | Yes | **No** — `--help` states OAuth and keychain are never read; this environment carries no API key, so the route cannot produce the record | **Rejected for this slice**; viable only for API-key deployments and unobserved |

## Supported contract

Two flat keys join `parallel` per runtime, validated by the engine before any attempt
record exists, in the same shape as the transports:

- `parallel.<runtime>_approval_policy` — a declaration from an engine-owned vocabulary:
  - Claude: `dont-ask` → `--permission-mode dontAsk`; `accept-edits` →
    `--permission-mode acceptEdits`. Shipped default `dont-ask`, with the profile
    granting `Edit(**)`, `Write(**)`, `MultiEdit(**)`, and `NotebookEdit(**)` — a
    path pattern the runtime resolves relative to the worktree root and never
    outside it; a bare `Write` under `dont-ask` wrote `../outside-probe.txt` live,
    so the validator refuses a bare or root-escaping edit-tool allow: under this
    default the allow list is the whole boundary.
    The first draft shipped `accept-edits`; panel round 5 observed live that the
    runtime then auto-accepts its own class of file-system Bash commands inside the
    worktree (`rm -rf`, `mv`, redirection writes, `cat`) with none of them in the
    allow list and an empty denial list, while a write outside the worktree was
    still denied. `accept-edits` stays declarable with that behaviour stated.
  - Codex: `read-only` → `--sandbox read-only`; `workspace-write` →
    `--sandbox workspace-write`. Shipped default `read-only`, the conservative pin
    until the Codex record observes the alternative.
  - Every unrestricted spelling is a declared **non-member** on both runtimes:
    `bypassPermissions`, `auto`, `manual`, `plan`, `dangerously-skip-permissions`,
    `danger-full-access`, `approve-for-me`, and any value not in the table refuse
    before the attempt record. A missing key refuses the same way. No config value
    makes the engine emit `--dangerously-skip-permissions`,
    `--allow-dangerously-skip-permissions`, `--sandbox danger-full-access`,
    `--dangerously-bypass-approvals-and-sandbox`, or `--dangerously-bypass-hook-trust`.
- `parallel.claude_settings_profile` — the path of the lane settings profile, relative
  to the repository root or absolute. Shipped default `config/claude-lane-settings.json`,
  seeded by `init.sh` when absent and adopter-owned afterwards. The engine refuses a
  profile that is missing, a symlink, not a regular file, not one JSON object, without
  a `permissions` object, with `permissions.defaultMode` (the mode is config-declared,
  one authority), or whose `permissions.allow` carries a `Bash` entry with no literal command
  prefix — the pattern, read literally (only the entry's outer whitespace is
  ignored; inside the parentheses a space is a character, as the runtime's matcher
  reads it), must start with a letter, digit, or path character and its head
  (everything before the first wildcard, `:`, or space) must hold a letter or
  digit; `Bash`, `Bash(*)`,
  `Bash(**)`, `Bash(?*)`, `Bash(:*)`, and `Bash(/*)` all fail that — or grants an edit tool (`Edit`, `Write`, `MultiEdit`,
  `NotebookEdit`) without a path pattern relative to the worktree root, or with one
  rooted outside it (`//`, `~`, `..`). The rule is
  structural because the panel's round 2 found `Bash(**)` unrestricted live at
  2.1.247 while an enumerated blocklist missed it, and found `Bash(:*)` *not*
  unrestricted (it matches commands starting with `:`), so an enumeration built
  from assumption was wrong in both directions; round 3 then found a lone path
  character before a wildcard (`Bash(/*)`, every absolute-path command) passing a
  first-character rule, which is why the head token is inspected. The guard judges
  the shape of a prefix, never the command it names — `Bash(sh:*)` is an adopter's
  declaration. Codex has no profile key in this slice.

The argv is assembled in one fixed order — command prefix, **approval contribution**,
worktree arguments, final-text arguments, prompt arguments:

- Codex: `codex exec --sandbox <policy> --cd <worktree> --output-last-message <file> -`
- Claude: `claude -p --setting-sources "" --permission-mode <mode> --settings <absolute profile> --output-format json`

The Claude contribution always carries all three flags; the route is the engine's, not
a per-launch choice. The Codex contribution is validated and passed; its behaviour is
not claimed until the Codex writing-lane record exists.

## Design matrix

Launch surface × runtime × approval-establishment route × write class × observed
approval transition × durable evidence × authoritative observer × failure outcome.
"Observed" cells are filled by the live record; this table declares what each cell
must contain and how it fails.

| Launch surface | Runtime | Approval establishment | Write class | Approval transition expected | Durable evidence | Authoritative observer | Failure outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kit wrapper → `claude -p` | Claude | `--setting-sources ""` + `--permission-mode dontAsk` + `--settings <profile>` | read-only | none | receipt `request.approval_policy`, `observed.argv`, `terminal.permission_denials == []` | wrapper child (argv) + parent (denials from the envelope) | a denial → `failed` |
| same | Claude | same | worktree write (Edit/Write in cwd) | accepted by the profile's edit-tool allow, no prompt; the runtime keeps the tools inside the worktree | same, plus the lane commit's tree | same | denial → `failed`; a write outside cwd is denied, not prompted |
| same | Claude | `--permission-mode acceptEdits` (declarable, not default) | worktree write and the runtime's own file-system Bash class | accepted by the mode regardless of the allow list (round 5, live: `rm -rf`, `mv`, redirection, `cat`) | same | same | a write outside cwd denied; an untracked file deleted inside cwd leaves no trace in the receipt or `git status` |
| same | Claude | same | commit (`git add`, `git commit`) | accepted by profile allow rule | commit sha read back in the cockpit | profile rule + cockpit `git` | denial → `failed` |
| same | Claude | same | push (`git push -u origin <lane>`) | accepted by profile allow rule | remote-tracking head read back in the cockpit | same | denial → `failed`; the flag spellings of a force push are profile deny rules, the `+refspec` form is not deniable by a prefix rule (panel round 4, live) — history protection is the forge's and the lane contract's |
| same | Claude | same | PR (`gh pr create`, `gh pr ready`) | accepted by profile allow rule | PR number and head read back by `dev_session.sh pr-watch` `_resolve_lane_pr` | forge read-back | denial → `failed`; a cross-repository or wrong-base PR refuses in `_resolve_lane_pr` |
| same | Claude | same | merge | **never in the lane** — `gh pr merge` is a profile deny rule and the contract says do not merge | `dev_session.sh merge` refuses an operator-class lane; a self-class lane merges only from the cockpit after `mergeable` | cockpit wrapper | lane attempt → denial → `failed` |
| Kit wrapper → `codex exec` | Codex | `--sandbox read-only` | read-only | unobserved in this slice | receipt `request.approval_policy`, `observed.argv`, `terminal.permission_denials == null` | wrapper child (argv) | sandbox refusal is not visible through `last-message-file`; behaviour owed to the Codex record |
| same | Codex | `--sandbox workspace-write` (declarable, not default) | worktree write / commit / push / PR | unobserved | same | same | same |
| Pre-trusted worktree | Claude | `~/.claude.json` write | any | branch `.claude/` authoritative | none in the receipt | none | rejected route |
| `--bare` | Claude | contract re-injection | any | unobserved | — | — | rejected route for this environment |
| Native agent dispatch, remote/cloud sessions, direct `codex exec` / `claude -p` | either | none | any | — | — | — | unsupported, unchanged from `#611` |

## Terminal outcomes (total)

| Situation | Where it is decided | Declared outcome | Receipt status | Attempt record |
| --- | --- | --- | --- | --- |
| Policy key absent, outside the vocabulary, or an unrestricted spelling | `_config_for_launcher`, before the attempt | `refused-declaration` (exit 64) | none | not created |
| Profile missing, symlinked, malformed, without `permissions`, with `defaultMode`, or widening a whole tool | same | `refused-trust-step` (exit 64) | none | not created |
| Profile bytes differ between the parent's and the child's read | child authority check | `refused-trust-step` | `rejected` → parent terminalizes `failed` | remains |
| Child argv would omit or alter the policy contribution | parent binding validation (`observed.argv` ≠ expected) | `refused-observation` | `failed` | remains |
| Runtime returns a `success` envelope with non-empty `permission_denials` (a denied write, or an action that would have prompted with no operator) | parent, after exit | `denied` | `failed`, error names the declared policy, `terminal.permission_denials` carries the list | remains |
| Runtime returns `success` with empty `permission_denials` | parent | `completed` | `completed`, `terminal.permission_denials == []` | remains (one-shot) |
| Envelope lacks a list-valued `permission_denials` | parent | `refused-evidence` | `failed` | remains |
| Codex `last-message-file` transport | parent | denials unobservable | `completed` or `failed` by the existing rules, `terminal.permission_denials == null` | remains |
| Everything `#609`/`#611` refuse (interruption, nonzero exit, lineage, malformed JSON …) | unchanged | unchanged | unchanged | unchanged |

A `null` denial list means the transport cannot observe the policy outcome; it is never
written as `[]`.

**A `failed` receipt is not evidence that the lane made no writes.** The runtime
continues after a denied call, so a lane can commit, push, and open a pull request and
still terminalize `failed` because one diagnostic it tried was refused (the live record
observed exactly this). The receipt status is the policy verdict; the lane's side
effects are reconciled from the worktree and the forge as they always were.

## Receipt shape additions

- `request.approval_policy`: `{"declared": <value>, "argv": [<contribution>],
  "settings_profile_path": <absolute path or null>, "settings_profile_sha256": <hex or null>}`,
  computed identically by parent and child.
- `observed.argv`: the exact argv the child observer `exec`s, recorded before the
  ready signal and compared by the parent against its own expectation.
- `terminal.permission_denials`: list (Claude `json-stdout`) or `null`
  (`last-message-file`).

## Semantic rows and hostile mutations

Positive constructions (each is a test):

1. Claude argv carries the full contribution in the fixed order; the receipt's
   `request.approval_policy` names the profile path and digest and `observed.argv`
   equals the argv the fake runtime saw; `terminal.permission_denials == []`.
2. The Codex argv is pinned byte for byte with `--sandbox read-only` in the fixed
   position and every other element unchanged; `terminal.permission_denials is None`.
3. A `success` envelope with a non-empty `permission_denials` terminalizes `failed`
   with the list preserved and the attempt intact.
4. Each declaration outside the vocabulary, each unrestricted spelling, and an absent
   key refuse before the attempt on both runtimes.
5. Each refused profile shape refuses before the attempt; a valid profile is accepted.
6. A profile rewritten after the parent's read is refused by the child.
7. A receipt whose `observed.argv` omits `--settings`, `--setting-sources`,
   `--permission-mode`, or `--sandbox` fails parent validation even when the rest of
   the receipt is bound.
8. Both runtime adapters name no permission flag, mode, sandbox, or profile; the shared
   workflow does.

Hostile mutations recomputed locally (each must be killed by a behavioural assertion):

- the declared policy present in config but omitted from the child argv (kills 1, 2, 7);
- the trust step skipped while the receipt claims it (`--settings` dropped, digest
  still written) (kills 1, 7);
- a lane write accepted before the approval transition is read (the denial check
  removed) (kills 3);
- a policy value widening to unrestricted without being declared (vocabulary grows
  `bypass`/`danger-full-access`, or the engine emits a dangerous flag) (kills 4);
- the Codex argv regressing while the policy is added (`--cd` dropped or reordered)
  (kills 2);
- a runtime adapter contradicting shared policy (an adapter line naming
  `--permission-mode`, `--dangerously-skip-permissions`, or `--sandbox`) (kills 8);
- a profile with `defaultMode: bypassPermissions` or `allow: ["Bash"]` accepted (kills 5).

## Ownership boundary

Unchanged from `#611`: the descriptor issuer, the launcher, the receipt validator, and
the behavioural tests are kit-owned; the policy vocabulary and argv are engine-owned;
the declared values and the profile are adopter-owned config seeded by `init.sh`; the
launch and failure policy lives in `parallel-headless.md` and the runtime-parity
capability row; both runtime adapters stay thin. The seal remains corruption and
descriptor-only rewrite evidence, not a privilege boundary against the same OS account.
The settings profile shares that boundary: parent and child each read and digest it
and must agree, but the runtime loads the path itself at `exec`, so a same-account
writer replacing the file inside the child's observe-to-exec window is not caught
(panel round 2, adversarial lens, reported as structural and not reproduced).
Passing the validated bytes inline instead of the path would close it and is a
separate change. The shipped profile's deny entries name the flag spellings of a
force push and nothing more: a prefix rule cannot say "contains a forced update",
so `git push origin +HEAD:main` passes the profile (panel round 4, live-reproduced
against a throwaway remote). History protection of a remote branch is the forge's
branch protection and the lane contract's own-branch rule; a deterministic
lane-side push gate (a pre-push hook installed in the lane worktree that refuses
forced updates and any ref but the lane branch) is the rule-1 mechanism and is
follow-up work, not part of this slice.
