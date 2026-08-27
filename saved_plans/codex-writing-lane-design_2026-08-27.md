# Codex writing lane — live-validation design 2026-08-27

## Slice boundary

This slice produces the Codex-authored writing-lane record owed by Phase 4, sprint
item 3. It exercises the existing per-runtime wrapper at the bytes fetched and
directly verified from `origin/main`: one fresh private synthetic repository, one
Codex lane that writes inside its worktree, commits, pushes, opens a ready pull
request, and is reviewed from the cockpit through `dev_session.sh pr-watch`.

The shipped `parallel.codex_approval_policy: read-only` remains untouched. The
synthetic cockpit's `config/dev-model.yaml` declares
`parallel.codex_approval_policy: workspace-write` for this fixture only. The wrapper
must bind that declaration as `--sandbox workspace-write`; no prompt, project file,
user file, or lane action may replace it with `danger-full-access` or add a dangerous
bypass flag.

The record observes, rather than infers, the boundary of `workspace-write`: an
inside-worktree write, a write outside the worktree, a write to the descriptor-owned
state root, and a networked push. A controlled user Codex configuration separates the
default writable `/tmp` class from the state-root claim: it excludes `/tmp` and
`$TMPDIR`, names only the descriptor's state root as an additional writable root, and
first disables and then enables workspace-write network access. The denial lane sets
user `approval_policy = "never"`; the writing lane sets `approval_policy =
"on-request"` with `approvals_reviewer = "auto_review"` so any request to leave the
sandbox has an observable automatic approval verdict rather than a human prompt. A tracked project
`.codex/config.toml` declares conflicting network and marker values while the
controlled user config marks the fresh worktree untrusted. This makes user-config and
project-config reach observable as behavior, not filename inspection.

The controlled Codex home contains no copied credential bytes. Its `auth.json` is a
local symlink to the operator's existing authentication file and is never tracked,
printed, included in a prompt, or pushed. The synthetic repository holds no workspace
source or operator note.

Everything established by `#609`, `#611`, and `#614` remains unchanged: descriptor
and rewrite-seal authority; environment replacement; repository-override removal;
trusted executable lookup; child observation; nonce lineage containment; one-shot
attempts; terminal receipts; config-declared transports; the Codex argv order; the
approval-policy vocabulary; and the Claude profile validator and denial route. Model
and effort calibration (`#605`, `#255`), the first real launcher task, `#606`, `#607`,
the adapter-generation work, and the mechanisms filed as `#615` through `#618` remain
outside this slice.

The launcher changes only if the live record proves the existing Codex path is
incorrect and the correction is a bounded fix rather than a new evidence mechanism.
A denial that Codex does not serialize through `last-message-file` is a matrix finding,
not authority to invent a second transport in this slice.

## Product surface selected before execution

`codex --version` on 2026-08-27 at kit revision
`da5d31ec18875464bf0622e755d4988920209316` printed `codex-cli 0.149.1`.
`codex exec --help` at that revision and date listed `--sandbox`,
`--output-last-message`, `--ignore-user-config`, and `--ignore-rules`; the configured
wrapper argv includes the first two and neither ignore flag. The
[official configuration reference](https://developers.openai.com/codex/config-reference)
states that user configuration lives in `~/.codex/config.toml`, project overrides live
in `.codex/config.toml`, untrusted projects skip project-local config, hooks, and rules,
and workspace-write network access and additional writable roots are separate
`sandbox_workspace_write` keys. The
[official approvals and sandbox security page](https://learn.chatgpt.com/codex/agent-approvals-security)
states that the worktree's `.git` pointer and resolved Git directory remain protected
read-only under workspace-write, so a lane commit necessarily supplies an
approval-transition observation. Those are candidate surfaces only; the lanes below
supply the behavioral evidence.

## Design matrix

Sandbox state × durable evidence × authoritative observer × terminal outcome. Every
row has one declared observation and one receipt status; an empty observation is not
an all-clear.

| Row | Sandbox state / action | Positive construction | Durable evidence | Authoritative observer | Declared terminal outcome | Receipt status |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | fixture-only `workspace-write` declaration | synthetic merged config resolves `workspace-write`; child argv is exactly `codex exec --sandbox workspace-write --cd <worktree> --output-last-message <file> -` | request approval block plus `observed.argv`; kit tracked config diff remains empty | wrapper parent and child | declaration accepted | `completed` or an existing launcher failure; never widened |
| D2 | worktree write | create the requested note below the lane worktree | committed tree, clean lane status, final text | lane Git plus cockpit read-back | permitted | `completed`, `terminal.permission_denials == null` |
| D3 | write outside the worktree | with `/tmp` and `$TMPDIR` excluded, attempt one sibling-fixture write | target absence plus Codex's final text and captured event/stderr | host filesystem plus Codex | denied by sandbox | `completed` when Codex exits zero with final text; `failed` only on an existing launcher failure, always denial field `null` |
| D4 | descriptor state root | add only the exact state root to `sandbox_workspace_write.writable_roots`, then write one probe there | state-root file at the descriptor path and sibling target absence | host filesystem cross-checked against descriptor | permitted by controlled user config | `completed`, denial field `null` |
| D5 | network-disabled push | commit a probe branch and run `git push -u origin <lane>` with `network_access = false` | absent remote ref plus Codex's final text and captured event/stderr | forge/remote read-back plus Codex | denied by sandbox | `completed` on a zero-exit final response; denial field `null` |
| D6 | protected Git metadata and undeclared sandbox widening | denial lane: `approval_policy = "never"`; writing lane: `on-request` with `auto_review`; capture every escalation request and verdict for commit/push | raw event/stderr capture, final text, bound argv, resulting commit/remote state | Codex event stream, auto reviewer, wrapper observation, Git read-back | denial, approval, or no request recorded per action; wrapper never silently relabels the declared sandbox | one receipt status matching the client exit, denial field `null` |
| D7 | project Codex config | tracked project config conflicts with the controlled user values and carries a marker; user config marks the worktree untrusted | marker absence and behavior matching the user values, not the project values | Codex final text plus host/remote read-back | project layer not loaded | receipt follows the attempted actions; denial field `null` |
| D8 | user Codex config | controlled user config excludes temp roots, grants the exact state root, selects network off/on, and selects `never` versus `on-request`/`auto_review` per lane | D3–D6 behavior and user marker if the client exposes it | Codex plus auto reviewer and host/remote read-back | user layer loaded; every user-owned widening is disclosed | receipt follows the attempted actions; denial field `null` |
| D9 | network-enabled writing lane and review | enable network and auto-reviewed approvals in the controlled user config; scoped write, commit, push, ready PR; cockpit `dev_session.sh pr-watch` binds review to the exact head | receipt, approval events, commit, remote ref, PR metadata/diff, pr-watch receipt | wrapper child/parent, auto reviewer, GitHub, cockpit pr-watch | lane completed and reviewed if every required widening is approved; otherwise the exact gap remains | launcher status follows the client; denial field `null`; pr-watch records only an exact reviewed head |

## Terminal outcomes are total

| Situation | Declared outcome | Durable evidence | Receipt status |
| --- | --- | --- | --- |
| shipped kit config | remains `read-only`; not used for a writing launch | tracked config and final diff | no fixture receipt |
| fixture policy missing, outside the engine vocabulary, or `danger-full-access` | refused declaration before an attempt | launcher error and absent attempt | no receipt |
| observed argv omits or changes `--sandbox workspace-write` | refused observation | rejected/failed receipt and preserved attempt | `failed` |
| inside write or exact state-root write succeeds and Codex supplies final text | permitted | filesystem/Git read-back plus final-message digest | `completed`, denial field `null` |
| outside write is denied but Codex supplies final text and exits zero | denial observed only in Codex output | absent target plus raw output and final-message digest | `completed`, denial field `null` |
| network push is blocked but Codex supplies final text and exits zero | denial observed only in Codex output | absent remote ref plus raw output and final-message digest | `completed`, denial field `null` |
| protected Git metadata or another escape requests approval under `never` | widening refused | raw event/stderr capture plus bound argv and unchanged Git state | client exit determines `completed`/`failed`; denial field `null` |
| protected Git metadata or another escape is approved by the controlled auto reviewer | action runs outside the declared sandbox for that call; wrapper declaration remains `workspace-write` | approval event plus resulting Git/remote state and bound argv | client exit determines `completed`/`failed`; denial field `null` |
| no escalation is attempted | no widening observed | raw event/stderr capture plus bound argv | client exit determines `completed`/`failed`; denial field `null` |
| Codex exits nonzero, final text is absent, observation fails, or lineage survives | existing launcher failure | attempt and terminal receipt | `failed` or `interrupted`, denial field `null` |
| network-enabled write/commit/push/PR completes | permitted at the declared sandbox plus controlled network value | commit, remote ref, PR read-back, receipt | `completed`, denial field `null` |
| pr-watch evidence is missing, stale, or for another head | review incomplete | pr-watch JSON and state receipt | not mergeable; launcher receipt remains unchanged |

`terminal.permission_denials == null` is an unobservable structured denial outcome,
not evidence that nothing was denied. The final text and event/stderr capture are
Codex-authored observations; the receipt can bind the final text but cannot promote it
to a structured denial list.

## Executable positive constructions and hostile mutations

Each mutation is recomputed from its independently constructed positive. If this
record remains prose-only, the live probes and cockpit read-backs execute these pairs;
if launcher code changes, each pair becomes a behavioral assertion before the change
is accepted.

| Row | Executable positive | Locally recomputed hostile mutation | Kill condition |
| --- | --- | --- | --- |
| D1 | resolve fixture config, launch, compare request policy and exact observed argv | change the fixture declaration to `danger-full-access`, or remove `--sandbox` from a recomputed observed receipt while leaving the request self-consistent | declaration refuses before attempt; altered observation never terminalizes `completed` |
| D2 | create and commit only the requested in-worktree note | recompute the expected tree with the note absent while preserving the reported commit text | cockpit tree read-back disagrees |
| D3 | exclude temp roots and observe the sibling write denied | pre-create or allow the sibling target while retaining final text that says denied | target-existence read-back disagrees |
| D4 | explicitly grant the descriptor state root and write the probe | substitute a sibling state path in the user config while retaining the descriptor's path in the record | exact-path read-back disagrees |
| D5 | disable network and observe the push blocked with no remote ref | seed the remote ref while retaining Codex's blocked-push text | `git ls-remote` disagrees |
| D6 | preserve `workspace-write` and capture each refusal/approval/no-request verdict for widening | replace the observed argv with `--sandbox danger-full-access`, add a dangerous bypass flag, or claim an approval without the action's resulting Git state | exact argv binding disagrees, declaration refuses, or Git read-back disagrees |
| D7 | mark the worktree untrusted and observe the project marker/config absent | mark it trusted or inject the project marker while retaining the record's “not loaded” claim | marker/behavior read-back disagrees |
| D8 | apply the controlled user writable-root, network, and approval-review values | launch with `--ignore-user-config` while retaining the user-config claim | state-root/network/approval behavior disagrees |
| D9 | read back every required approval verdict plus the exact commit, remote ref, ready PR, and pr-watch receipt head | omit a widening, substitute a foreign PR/head, remove the remote ref, or record review at the previous head | event, forge, or pr-watch binding refuses/disagrees |

The particularly dangerous false-success shapes are explicit: a denied action whose
Codex process still yields a `completed` receipt with `permission_denials == null`;
`workspace-write` silently widened to undeclared `danger-full-access`; and a Codex argv
without `--sandbox` terminalized as completed. The record must preserve the first as a
transport limitation and kill the latter two through the existing declaration and
argv bindings.

## Evidence capture and containment

- Persist launcher stdout and stderr beside each synthetic session before any retry.
- Recompute every descriptor, task, combined-prompt, final-message, and copied-engine
  digest from the bytes at the destination.
- Read back the remote head and pull request independently of the lane's prose.
- Poll the synthetic PR through `dev_session.sh pr-watch` from the cockpit-owned
  fixture engines. Use `--no-persist` for any read-only cockpit poll concurrent with a
  test run; no poll runs during `make test`.
- Audit the receipt-bound process lineage, lane worktree status, fixture contents,
  state-root containment, and synthetic repository visibility before cleanup.
- Remove lane sessions and the temporary fixture after the record is written. Delete
  the private synthetic GitHub repository after the task PR merges; if the token lacks
  `delete_repo`, ask the operator to delete it in the UI and verify absence with
  `gh repo view`.

## Exit boundary

The runtime-parity Codex cell moves only to the behavior the live record and
independent read-backs establish. It must name structured denial read-back as absent
under `last-message-file`; it must not claim that `workspace-write` alone grants
network, that project/user configuration is isolated, that every denied action is
visible to the wrapper, or that a future client behaves the same way. A prose-only
record creates no adopter-observable change and therefore no `CHANGELOG.md` entry.
