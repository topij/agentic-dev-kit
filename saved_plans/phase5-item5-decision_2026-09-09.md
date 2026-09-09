# Phase 5 item 5 — operator decision packet

**ITEM5-B approved on 2026-09-09.** The operator replied `Approve ITEM5-B as scoped`
to the packet at `edc199f42bc65b1850172ea79b791ef358577ae1`, then requested autonomous
continuation. The [execution record](phase5-item5-b-execution_2026-09-09.md) owns its
result and next action. ITEM5-A was not selected. Neither option restores the original
exercise's continuity or completes item 5 by itself.

## Delivery and evidence read-back

`gh pr view 724 --repo topij/agentic-dev-kit`
read back kit #724 as merged at `8418118e40728c667c32a28a182697139bc7a5ef` on
2026-09-09. The checkout was at that SHA. Its diff contains the #722 batch; there is
no outstanding record batch to repeat. `gh pr view 2255 --repo in-parallel-oy/cs-toolkit`
read back the adopter merge as
`c4119f85e07f2a089ab8d5decc94cf2cd1635d14`, with reviewed head
`21fe33bb040e7fdcc8f7d3d7c4402e768b1ff351`, on the same date.

The [completed replay](cs-toolkit-replay_2026-09-09.md) remains Phase 5 item 6's
evidence. Its source is `e698ec47d6284ccd31af5ba9d8bc5657fe992310`, not the later
kit record merge. The accepted #723 upstream deferral and original-checkout versus
fresh-clone test limits remain attached to that replay. Initial #2222/#2223 and
replay #2255 receive no new credit here. #585's earlier placement outside Phase 6 is settled.

## Retained baselines and what they support

The [read-only audit](phase5-item5-baseline-audit_2026-09-09.py.txt), invoked with
`python3 -B saved_plans/phase5-item5-baseline-audit_2026-09-09.py.txt` in
`/Users/topi/Coding/agentic-dev-kit` at `8418118e40728c667c32a28a182697139bc7a5ef`
on 2026-09-09, produced the [retained result](phase5-item5-baseline-audit_2026-09-09.json).
It found the original paths absent, including a check for dangling symlinks:

- `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`
- `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`

No tree was reconstructed during that audit. The same audit compared the named bundle ledgers and
the replay snapshots; its mismatch fields are empty and the snapshots remain
byte-identical. This checks retained bytes, not a rerun of the replay.

| Retained material | What it can establish or supply | Limit |
|---|---|---|
| [Original fixture inputs](codex-adopt-field-evidence_2026-09-05/fixture-inputs.json), [copy ledger](codex-adopt-field-evidence_2026-09-05/copy-ledger.json), [install baseline](codex-adopt-field-evidence_2026-09-05/install-baseline.json) | Synthetic input text, source-to-destination mapping, preserved wrap-up adapter, source pin and installed scope. | Pre-initialization baseline; not the final fixture state. |
| [Post-init config](codex-adopt-initialization-evidence_2026-09-06/config-after-init.yaml), expected mappings, terminal transcript and verification log in that evidence directory | Initialized config bytes and the recorded execution/failures. | The failed suite is an observation, not successful adoption verification. |
| [VER-02 source inventory](codex-adopt-ver02-evidence_2026-09-06/source-input-inventory.json) at `ab0a6d62308b298478b2f85fc961f14348f35365` | Each inventoried source file has its matching blob at the same path in the available kit Git object. | File bytes do not restore a deleted clone's Git metadata. |
| [FIX-01 patch](adopt-fix01-evidence_2026-09-06/ownership-and-lenses.patch.txt), [lens render outputs](codex-adopt-completion-review-evidence_2026-09-06/inspection.json), [REG-01 payloads](adopt-reg01-runtime-registration_2026-09-06.md#the-payloads) | Ownership-marker removal, nested-path lens bytes and registration/config payloads. | Their earlier execution approvals were consumed; copying into a new tree needs this new decision. |
| [Post-REG-01 fixture inventory](adopt-reg01-application-evidence_2026-09-07/fixture-inventory-after-reg01.json) | Superseding comparison baseline for paths, kinds, modes and hashes. The audit locates non-cache file bytes in retained files, JSON string fields or source blobs. It derives `.gitignore`, marker removal and rendered `notes/friction.md` in memory and matches their hashes. | A digest inventory is not a complete backup. Actual destination modes and bytes would still need verification after an approved write. |
| [Suite assessment](adopt-suite-assessment_2026-09-07.md), [hooks batch](codex-hooks-batch_2026-09-07.md), [continuation](codex-hooks-continuation_2026-09-09.md) | Bounded failure classification and already-credited client observations with their limits. | They neither repair the old installed tests nor transfer trust to a new path/client. Later kit repairs must be tested at their own source pin. |

The audit could not locate the retained bytes for `.pytest_cache/.gitignore`,
`.pytest_cache/CACHEDIR.TAG`, `.pytest_cache/README.md`,
`.pytest_cache/v/cache/lastfailed`, `.pytest_cache/v/cache/nodeids`, or
`scripts/devkit/lib/__pycache__/kitconfig.cpython-314.pyc` in its examined sources.
The inventories exclude `.git`; the original fixture commit
`08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` is unavailable in the kit object database.
No retained Git-object backup, original hook-installation state or runtime trust store
is established by this audit. Neither proposal fabricates those artifacts or that SHA.

## The options and proposed writes

The paths below are proposed new roots, never substitutes at the missing original
names. An approved execution must refuse existing destinations. Bind absolute `REPO`
and `KIT` once to the selected fixture/source below; assert `pwd -P` immediately before
each write sequence and hash the actual destination files afterward. Use independent
Git metadata, not a copied linked-worktree pointer. The source clone must have no
push-capable origin pointing back to the cockpit.

| | ITEM5-A — historical payload rebuild | ITEM5-B — fresh current-kit verification (recommended) |
|---|---|---|
| `REPO` | `/Users/topi/Coding/adk-field-exercises/item5-a-20260909/fixture` | `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture` |
| `KIT` | `/Users/topi/Coding/adk-field-exercises/item5-a-20260909/kit-source` | `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source` |
| Kit pin | `ab0a6d62308b298478b2f85fc961f14348f35365` | `8418118e40728c667c32a28a182697139bc7a5ef`; later movement does not silently change this proposal. |
| Fixture construction | Materialize post-REG-01 non-cache payloads from the audit's sources, with the recorded modes. Use a new Git identity and baseline. Explicitly omit the listed cache artifacts and record that normalization. | Create a new synthetic input repository using retained adopter-owned text/config and settled ownership choices; stage non-repo-only manifest paths from the pinned current kit. Remap only `scripts/` to `scripts/devkit/`; keep other paths root-relative. Install the missing runtime adapters and retained reference-file scope at their root-relative paths, preserving the custom wrap-up adapter. Record a new installation baseline. |
| Additional writes | New local Git metadata/commit on `chore/adopt-agentic-dev-kit`; external test-state/log directories under the selected exercise parent. No initializer or historical `.git/hooks` reconstruction. | New local Git metadata/commits on `chore/adopt-agentic-dev-kit`; `init.sh --no-clobber` with the exact prompt answers below; generated narrative/profile/hook files and ignore entries; retained REG-01 registrations and current renderer's nested-path lens definitions; new baseline, test-state/log directories under the selected parent. |
| Evidence gained if checks succeed | Reproduction of the normalized historical file payload and behavior of the historical installed source under a newly recorded environment. | Successful installation verification at the current pin while preserving custom paths, policy, wrap-up adapter and local overlay; tests can assess the later installed-suite repairs without the lost-tree precondition. Setup steps are not newly credited field exercises. |
| Cannot establish | Original filesystem/Git/trust continuity; current-kit correctness; newly successful original adoption; fixture PR lifecycle; any systemize route. | Original continuity or historical-cache behavior; fresh runtime discovery/trust/execution; fixture PR lifecycle; any systemize route. It does not rewrite the existing hook observations. |

For either option, the approved execution records destination inventory and modes,
source pin, new Git identity, exact commands and terminal outputs. Run the destination
installed-test runner, destination document-budget check, installed doctor against the
independent pinned source manifest, and the source doctor's adapter report. Keep actual
warnings, declared declines and preserved custom files visible. Run kit `make test`
separately, to completion, without concurrent state writers; keep the known #393
deep-JSON failure separate from new failures and from the adopter's artifact-inventory
failure. A passing subset cannot replace the required installed-suite result. Unexpected
failures produce a report and a proposed repair, not an unapproved source or fixture fix.

ITEM5-B's initialization answers are: project `adopt-context-fixture`; runtime `codex`;
operator logins `none`; tracker backend `none`; empty tracker project and URL; protected
branch `main`; notify user `tracked-fixture-recipient`; review bots `none`. Preserve
`notify.backend: none` and the gitignored override `local-fixture-recipient`.
Preserve `ROADMAP.md`, `notes/history.md`, `notes/friction.md`,
`notes/friction-archive.md`, `scripts/devkit`, the fixture policy without its old
ownership marker, and the fixture-owned wrap-up adapter. Use the retained complete
post-init tracked config as the value baseline; refuse unexplained mapping changes.

The proposed REG-01 writes are `.codex/hooks.json`, `.codex/config.toml` and
`.claude/settings.json` at the retained payload hashes. The Claude file carries actual
cockpit permission grants. The decision authorizes placing those files in the new
fixture, not launching a runtime there, changing the user's configuration, or transferring
trust. ITEM5-B explicitly authorizes Codex to run the specified fixture-only initializer
proposal; otherwise adopt Step 3c leaves execution to the operator.

## Remaining item 5 work under either decision

- **Adoption:** the selected run must establish its own successful verification. Final
  preserved-file acceptance, adoption completion, a fixture remote/ready PR and its
  review lifecycle remain separate exact decisions. No remote repository is selected
  here, and none is needed for local verification.
- **Systemize:** [the retained test exercise](codex-systemize-test-field-exercise_2026-09-06.md)
  credits LLM-only test analysis and artifact checkpoints. Live rule/friction/tracker
  routes, notifications, engine-backed operation and full restart/crash recovery remain
  untested. The capsule cannot reconstruct the full raw fetch or prove pagination anew.
  Cap-triggered omission, batched analysis, competing-mtime selection, hostile artifact
  targets and fresh-client discovery also remain outside that record. A separate
  route/payload decision must select what is required for the remaining field exit;
  neither fixture option silently waives these limits or authorizes live writes.
- **Triage:** the interactive LLM-only graduation stays credited. Engine-backed and
  notification-service routes are not established. Preserve the parked source entries
  identified as TRI-03/TRI-04/TRI-05 in the maintained reconciliation; later triage runs
  may use different candidate IDs. The inbox budget reminder supplies no payload or
  archive decision.
- **Sprint:** Phase 5 stays incomplete until the remaining field coverage is resolved;
  Phase 6 stays unstarted. Item 6's completed replay and #723 deferral are unchanged.

## Approval boundary

The operator's **`Approve ITEM5-B as scoped`** authorized only the new fixture/source,
specified initialization, registration, local verification and evidence writes above.
The scope includes a compact result record under `saved_plans/` and the ordinary
kit wrap-up/ready-PR review path. The separate `merge when clean` instruction and
autonomous-continuation request govern this session's kit PR. Neither permits cs-toolkit
writes, a fixture remote/PR, live systemize/triage routing, user-profile changes, or a
Phase 5 completion declaration. Unexpected failures still require a proposed repair,
not an unapproved source or fixture fix. An amended choice needs a revised exact scope.

The [execution record](phase5-item5-b-execution_2026-09-09.md) supersedes this packet's
former request for an item 5 choice. Do not repeat the consumed setup approval.
