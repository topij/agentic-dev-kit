# Architecture

This page explains how the kit's parts fit together. Start with the
[Developer guide](developer-guide.md) for task-oriented instructions. The
[shared workflow definitions](agentic-dev-kit/workflows/) and
[`config/dev-model.yaml`](../config/dev-model.yaml) define behavior; the diagrams
here explain their relationships and do not replace their gates.

## Component map

```mermaid
flowchart LR
    Config["config/dev-model.yaml<br/>plus allowed local overlay"] --> Workflows["shared workflows<br/>docs/agentic-dev-kit/workflows/"]
    Config --> Engines["kit engines<br/>paths.engines"]
    Workflows --> Claude["Claude skills<br/>.claude/skills/"]
    Workflows --> Codex["Codex skills<br/>.agents/skills/"]
    Claude --> Agent["agent session"]
    Codex --> Agent
    Agent --> Engines
    Engines --> State["state resolver<br/>lane or production state"]
    Engines --> Registry["cleanup registry<br/>shared Git metadata + retained evidence"]
    Agent --> Forge["forge, tracker, CI,<br/>notification clients"]
    Engines --> Forge
    Templates["docs/templates/"] --> Init["init.sh"]
    Init --> Config
    Init --> Rendered["rendered agent guides<br/>and narrative docs"]
    Manifest["kit-manifest.json"] --> Doctor["kit_doctor.py"]
    Config --> Doctor
    Baseline["installed baseline<br/>and adapter provenance"] --> Doctor
    Cache["local Codex model cache<br/>advisory snapshot"] --> Doctor
```

`config/dev-model.yaml` holds project choices: document paths, runtime launchers,
model mappings, review policy, state patterns, and integration settings. The
gitignored `config/dev-model.local.yaml` can supply the allowed local override;
the merged view is the input to workflows and engines that require it. The
[config reader](../scripts/lib/kitconfig.py) documents the supported syntax and
overlay rules. A value in `models.runtime_mappings` is advisory unless a runtime
control applies it and the result is observed.

The shared workflows own behavior and authority. The Claude skill and Codex
skill files are thin entry points that load them; a runtime adapter may translate
invocation and available mechanisms but cannot relax a shared failure or approval
boundary. The [runtime parity contract](agentic-dev-kit/runtime-parity.md) lists
the adapters and documented differences. Keep a workflow change in the shared
definition so Claude and Codex receive it.

The root [AGENTS.md](../AGENTS.md) binds repository-wide instructions for Codex;
[CLAUDE.md](../CLAUDE.md) imports it for Claude Code. Policy that must reach
Claude Code and Codex belongs in that common route or a shared workflow, not
solely in `.claude/rules/`.

`init.sh` migrates supported config and renders unclaimed templates. An adopted
repository owns its rendered narrative docs and root agent guides. The
[upgrade workflow](agentic-dev-kit/workflows/upgrade.md) distinguishes those
adopter-owned files from kit-owned engines and templates; `kit_doctor.py` compares
installed kit-owned files with the manifest and checks installation properties.
Upgrades run in an assigned task worktree. Adapter inspection can use the recorded
kit baseline's history to recognize an older generated description; unavailable
history does not establish ownership. Claude lens definitions are previewed from
the adopter's merged configuration before replacement. Shared hook installation
has a separate explicit step because linked worktrees share Git administration.

See the [ownership reference](ownership.md) for edit and replacement boundaries,
including generated bindings, lane state and retained evidence.

### Source map

| Component | Code or contract | Responsibility |
| --- | --- | --- |
| Installer | [`init.sh`](../init.sh), [`docs/templates/`](templates/) | Migrate supported config, seed unclaimed docs and agent guides, install the hook shim. |
| Config reader | [`scripts/lib/kitconfig.py`](../scripts/lib/kitconfig.py) | Read the supported config subset and allowed local overlay. |
| Workflow contracts | [`docs/agentic-dev-kit/workflows/`](agentic-dev-kit/workflows/) | Define preflight, authority, outcomes, and resume behavior. |
| Runtime bindings | [Claude skills](../.claude/skills/), [Codex skills](../.agents/skills/) | Enter the shared workflows from each client. |
| Review and lanes | [`pr_watch.py`](../scripts/pr_watch.py), [`dev_session.sh`](../scripts/dev_session.sh), [`launch_lane.py`](../scripts/launch_lane.py) | Poll and record review state, issue worktrees and show the lane board, and launch bounded headless sessions with their compute, ticket and terminal state recorded. |
| State paths | [`scripts/lib/state_paths/`](../scripts/lib/state_paths/) | Resolve workflow artifacts into the declared state root or lane sandbox. |
| Review panel | [Fallback contract](agentic-dev-kit/fallback-review-panel.md), [`panel_prompt.py`](../scripts/panel_prompt.py) | Select lenses by review class, assemble isolated lens prompts, verify findings and record a head-bound receipt. |
| Review measurement | [`review_eval.py`](../scripts/review_eval.py), [evaluation guide](agentic-dev-kit/review-eval/reviewer-eval.md) | Compare lens and optional verifier reports against cases from kit history; scores require interpretation. |
| Session cleanup | [`session_cleanup.py`](../scripts/session_cleanup.py), [`sweep_scratch.py`](../scripts/sweep_scratch.py) | Retain declared evidence and retire authorized inventory paths while preserving dependency guards. |
| Installation inspection | [`kit_doctor.py`](../scripts/kit_doctor.py), [`kit-manifest.json`](../kit-manifest.json) | Report kit-owned drift, adapter and lens-definition state, and advisory Codex reviewer model observations. |

Engines beneath `paths.engines` can be vendored under another directory in an
adopter repository. The links above show this kit repository's default layout.

## Session and pull-request lifecycle

```mermaid
sequenceDiagram
    participant Developer
    participant Agent
    participant Records as Handoff and friction log
    participant Forge as Forge and CI
    Developer->>Agent: session-start
    Agent->>Records: read configured records
    Agent->>Forge: read PR and CI state
    Agent-->>Developer: briefing with gaps and recommendation
    Developer->>Agent: choose work
    Agent->>Agent: edit in assigned task worktree
    Agent->>Records: wrap-up handoff test
    opt Something no PR, commit or tracker issue records
        Agent->>Agent: commit handoff edit with the change
    end
    Agent->>Agent: delete recorded paths it created and no longer needs
    Agent->>Agent: verify completed branch
    Agent->>Forge: push, open ready PR and assert ready
    loop Until review and CI settle
        Agent->>Forge: pr-watch poll
        Forge-->>Agent: checks and findings
        opt No bot configured (the default), or a configured bot unavailable
            Agent->>Agent: lens panel round, then retire its scratch
        end
        Agent->>Forge: push repair or answer finding
    end
    Agent->>Agent: inspect merge gates and project authority
    opt Operator decision required
        Agent->>Developer: exact-head merge decision
        Developer-->>Agent: authorize or hold
    end
```

`session-start` makes no content edits or acknowledgements; its pr-watch read may
record the settle baseline. `pr-watch` checks the exact PR head and review
evidence; opening a PR is not completion. `wrap-up`'s handoff test runs before
every PR goes to review. It writes the configured handoff only for what that PR, its
commits and the tracker do not already record, and commits it on that PR so one review
covers both; when nothing is left, which is the usual result, it commits nothing.
Friction is routed when it is found. The full `wrap-up` closes a session on the
operator's request, and a separate wrap-up PR is only for a record no unreviewed PR
can carry.
Merge authority is separate from review readiness. For a non-lane PR without a
project merge policy, the [wrap-up contract](agentic-dev-kit/workflows/wrap-up.md#authority-contract)
holds the merge for an exact operator decision.

## Review evidence and merge authority

```mermaid
flowchart TB
    Poll["pr-watch at exact PR head"] --> Loop{"CI and findings<br/>handled?"}
    Loop -->|no| Repair["fix or disposition<br/>then poll again"]
    Repair --> Poll
    Loop -->|yes| Converged["converged<br/>settle any owed review request"]
    Bot["opt-in: qualifying<br/>configured-bot review<br/>of this head"] --> Evidence["independent review evidence"]
    Class["computed review class"] --> Lenses["isolated lens panel<br/>fresh-context reviewers"]
    Lenses --> Verifier["optional verifier<br/>checks each finding"]
    Verifier --> Receipt["head-bound receipt<br/>plus typed dispositions<br/>posted on the PR"]
    Lenses -.->|no verifier configured| Receipt
    Receipt --> Evidence
    Converged --> Gate{"mergeable?<br/>evidence + no merge blockers"}
    Evidence --> Gate
    Gate -->|no| Block["resolve blocker / poll / review"]
    Block --> Poll
    Gate -->|yes| Authority{"project and request<br/>authorize this actor?"}
    Authority -->|yes| Merge["merge and read back"]
    Authority -->|no| Hold["operator hold"]
```

`converged` ends the repair loop in the poll's observed scope. `mergeable` also
requires current-head independent-review evidence and satisfied merge guards;
`done` is its legacy alias. Neither ready status nor convergence grants the actor
merge authority. The REST backend can poll but cannot authorize a merge. Read
`truncated_reads` and `unavailable_reads` before treating its result as complete.

The [PR-watch contract](agentic-dev-kit/workflows/pr-watch.md) owns the request,
receipt and round-budget rules. The [fallback contract](agentic-dev-kit/fallback-review-panel.md)
selects lenses from the computed review class, isolates reviewers, and defines
optional verification and typed dispositions. `panel_prompt.py` assembles each
lens's prompt from that contract. The verifier's compute is declared per runtime in
`review.fallback_panel.verifier_compute`, as the lenses' is in `lens_compute`. A
later round can be a `fallback:delta` pass over the changes since the reviewed head,
composed with its full-review parent. With a cleanup registry configured, each
round's scratch retires before the next is allocated
([cleanup](#evidence-retention-and-cleanup)). Receipt source and lens
names are self-reported; storing them does not independently prove a review occurred.

The [evaluation runner](agentic-dev-kit/review-eval/reviewer-eval.md) measures
reviewer changes separately from this delivery gate. It gives case reports and
optional verifier comparisons, not merge clearance. Likewise, `kit_doctor`'s
Codex model-cache report is an advisory observation about explicit configured
pins, not a live availability check or an automatic model upgrade.

## Isolation and state

```mermaid
flowchart TB
    Cockpit["cockpit<br/>shared records and merge decision"] --> Issuer["dev_session.sh new"]
    Issuer --> Worktree["lane worktree<br/>source branch"]
    Issuer --> Sandbox["DEVKIT_STATE_ROOT<br/>lane state sandbox"]
    Worktree --> Launcher["launch_lane.py<br/>headless path<br/>optional --tier<br/>and --ticket"]
    Sandbox --> Launcher
    Launcher --> Terminal{"runtime exited cleanly;<br/>lane names its<br/>terminal state?"}
    Terminal -->|"pr-ready, no-pr or blocked"| Receipt["terminal receipt<br/>compute, usage, lane state"]
    Terminal -->|"no terminal state:<br/>Claude resume<br/>within max_resumes"| Launcher
    Terminal -->|"no terminal state;<br/>no resume left, or Codex"| Stalled["receipt status stalled"]
    Worktree --> PR["lane PR"]
    Receipt --> Board["cockpit board<br/>list --watch: RUN, OVERLAP"]
    Stalled --> Board
    PR --> Board
    Board --> Watch["cockpit scope pr-watch"]
    Watch --> Merge["cockpit merge wrapper<br/>or operator hold"]
```

The worktree separates source edits; `DEVKIT_STATE_ROOT` and the
[state-path resolver](../scripts/lib/state_paths/) separate workflow artifacts.
Neither mechanism removes source-file conflicts between lanes, so the cockpit
plans disjoint footprints, and the board's `OVERLAP` column names lanes whose
changes touch the same files. Interactive `new` prepares a worktree and activation
instructions. The headless path adds a one-shot descriptor, child-observed
identity, and terminal receipt through `launch_lane.py`. The launcher holds a lane to
its repository by Git common directory, so a cockpit in a linked worktree can issue
one. `--tier` applies `models.runtime_mappings` to the lane's argv; `--ticket` reads
the GitHub issue and appends it to the prompt. A lane ends by naming its terminal
state on its last line (`LANE-TERMINAL: pr-ready #<n>`, `no-pr <reason>` or
`blocked <reason>`); a Claude lane whose runtime exits successfully without it is resumed up to
`parallel.max_resumes` times when its session can be resumed, and a lane that still
names none, or cannot be resumed, is recorded `stalled`. A failed, denied or
interrupted round is recorded as such, not resumed. By default lane sessions live
beside the primary checkout (`DEVKIT_SESSIONS_DIR` overrides it), so the board
and `pr-watch <scope>` work from any of its worktrees. Review and merge use
the cockpit's scope-aware `dev_session.sh` commands so their evidence stays in
the lane's state sandbox. The [parallel workflow](agentic-dev-kit/workflows/parallel.md)
and its [headless companion](agentic-dev-kit/workflows/parallel-headless.md)
define the identity chain, terminal states and refusal paths.

State reads and writes are workflow-specific. The resolver can select a newer
sandbox or production artifact for a declared cache read; own-session triage
state must instead resolve through its write path so it cannot import another
session's approval evidence. Follow each workflow's path rules before adding an
artifact rather than constructing a `state/` path in a caller.

## Evidence retention and cleanup

```mermaid
flowchart TB
    Start["start session inventory"] --> Allocate["allocate owned review rounds"]
    Allocate --> Round["retire each round before the next<br/>seal, preview, apply --round"]
    Round --> Allocate
    Allocate --> Work["track writers<br/>register final worktree heads"]
    Work --> Stop["writers and descendants ended"]
    Stop --> Seal["seal complete evidence manifest"]
    Seal --> Evidence["content-addressed evidence<br/>shared Git registry"]
    Seal --> Preview["preview exact paths and keep reasons"]
    Preview --> Consent{"standing grant in AGENTS.md<br/>or operator authorization<br/>covers concrete scope?"}
    Consent -->|no| Hold["retain inventory; await decision"]
    Registry["inventory unavailable:<br/>device renumbered by reboot"] --> Reconcile["reconcile preview,<br/>then approved apply"]
    Reconcile --> Rebound["rebound to boot-stable identity<br/>deletes nothing"]
    Consent -->|yes| Apply["apply with renewed process attestation<br/>and fresh dependency guards"]
    Apply --> Kept["kept / active / unavailable<br/>incomplete; preserve reason"]
    Apply --> Native["archive-with-runtime<br/>Codex native archive"]
    Native --> Apply
    Apply --> Complete["completed<br/>retained hashes checked; paths absent"]
```

With `scratch.session_registry` configured, inventories and sealed evidence live
under `<git-common-dir>/devkit/<scratch.session_registry>/`, shared by linked
checkouts. This durable local record survives task-worktree removal; a fresh clone
does not contain it. The caller declares evidence completeness, including required
assets and dependencies, and the engine checks retained bytes. It cannot discover
all evidence dependencies from arbitrary report prose.

Inventories and receipts bind each directory by a filesystem identity that survives
a reboot where the platform offers one: the volume UUID on macOS, the device number
elsewhere. An inventory bound to a device number that a reboot renumbered, with
every recorded round gone and every recorded worktree absent and no longer
registered with Git, is rebound through
`session_cleanup.py reconcile`, which deletes nothing; any other identity change
keeps the inventory unavailable.

The [cleanup contract](agentic-dev-kit/session-cleanup.md) separates ownership,
retention and deletion authority. A session deletes the paths it created and recorded
once nothing needs them. A standing grant written into the repository's `AGENTS.md`
can replace asking for those paths only; it never covers an age sweep. A preview token
binds an inventory and seal; it does not supply operator consent. Fresh process and dependency observations
can keep an approved path. A native archive request still needs terminal
confirmation and another apply; queued work is not completed cleanup. Policy
changes or unavailable inventories require explicit recovery rather than broader
sweep roots. Ordinary age-based scratch reports remain a separate operation.

## Friction flywheel

```mermaid
flowchart LR
    Session["work and wrap-up"] --> Finding{"finding route"}
    Finding -->|issue-shaped and approved| Tracker["tracker item"]
    Finding -->|incomplete or accumulating| Inbox["friction inbox"]
    Inbox --> Triage["triage<br/>freeze and propose"]
    Triage --> Decision{"exact operator decision"}
    Decision -->|file and verify| Tracker
    Decision -->|archive| Archive["friction archive"]
    Decision -->|park| Inbox
    Merged["merged PR reviews"] --> Systemize["post-merge-systemize<br/>cluster root causes"]
    Systemize -->|qualifying pattern| Ladder{"fix level"}
    Ladder -->|first| Structure["structural change"]
    Ladder -->|then| Check["check shown failing<br/>on a past PR"]
    Ladder -->|judgement call only| Rule["prose rule"]
    Table[("enforcement table")] -.->|unenforced rule repeats| Ladder
    Structure --> Proposal["shared-rule PR<br/>names level and proof,<br/>updates the table row"]
    Check --> Proposal
    Rule --> Proposal
    Systemize -->|other below-threshold cluster| Inbox
    Systemize -->|below-threshold single| Severity{"tracker severity?"}
    Severity -->|below| Inbox
    Severity -->|at or above| Approval{"exact operator approval"}
    Approval -->|approved and verified| Tracker
    Approval -->|unavailable or declined| Inbox
```

The routes have different inputs. Triage works from frozen inbox blocks and
requires exact decisions and read-back before it accounts for a tracker write or
sweeps a block. Systemize works from merged PR review evidence and proposes a
shared-rule change only for a qualifying cross-PR pattern. It takes the first fix
level that works: a structural change so the mistake cannot be made, then a check
whose failure names the fix and which fails on the code of a pull request in the
cluster, and a prose rule only for a judgement call a check cannot make. When
`systemize.enforcement_table` is configured, it reads that table before proposing a prose rule: a pattern
that repeats a rule marked `judgement, unenforced` is a reason to reconsider a
check, and the proposal updates the rule's row in the same patch. Its tracker route
also needs payload-specific approval. The [triage](agentic-dev-kit/workflows/triage-friction-log.md)
and [systemize](agentic-dev-kit/workflows/post-merge-systemize.md) contracts own
the details of artifacts, retries, and recovery.

## Where to change behavior

| Change | Owning surface |
| --- | --- |
| Project path, reviewer, model guidance, or integration setting | `config/dev-model.yaml`; migrate a new key through `init.sh` |
| Workflow decision, failure, or approval rule | Shared file under `docs/agentic-dev-kit/workflows/` |
| Runtime invocation or registration | Thin `.claude/skills/` or `.agents/skills/` binding, plus the [parity contract](agentic-dev-kit/runtime-parity.md) |
| Deterministic command or state behavior | Engine under `paths.engines`, with the corresponding behavioral verification |
| Adopter-facing starting content | Template under `docs/templates/`; preserve adopter-owned rendered files |

This source repository keeps its live work in [the kit handoff](kit-handoff.md).
Its dated plans and retained evidence describe the revisions they name; use the
handoff and current contracts when making a new change.

For changes in this repository, `make test` is the verification entry point.
Changes to gate, launch-authority, or merge-authority behavior in the engines
named by [AGENTS.md](../AGENTS.md) also require the
[safety-critical review doctrine](agentic-dev-kit/safety-critical-changes.md).
