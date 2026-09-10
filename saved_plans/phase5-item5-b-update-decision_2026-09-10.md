# ITEM5-B-UPDATE-01 — operator decision packet

**Decision pending.** Approving this packet would authorize the bounded source advance,
fixture update, baseline recording, local verification and evidence below. This session
prepared the proposal read-only against the retained trees. Setup approval and the
kit-only repair approval are consumed; neither authorizes these writes.

## Inputs and delivery

Bind these absolute roots for an approved execution:

```sh
REPO=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture
KIT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source
OUT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/update-60fe0dc-20260910
```

The fixture input is `07bacf5bda3b1e7a6718c7d4528336ef81dc2143`, on
`chore/adopt-agentic-dev-kit`. The source input is detached at
`8418118e40728c667c32a28a182697139bc7a5ef`. The proposed source is exactly
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`; later protected-branch movement does not
change the decision. Neither retained tree has a remote in the audit below.

`gh pr view 726 --repo topij/agentic-dev-kit --json state,headRefOid,mergeCommit,mergedAt,statusCheckRollup`
in `/Users/topi/Coding/agentic-dev-kit` at that repair merge on 2026-09-10 read back
[PR #726](https://github.com/topij/agentic-dev-kit/pull/726) as merged with reviewed
head `186cd68010d04b3a6f334b0df10117835ed683dc`. The
[final disposition](https://github.com/topij/agentic-dev-kit/pull/726#issuecomment-5614835079)
was read through the fully paginated issue-comment API, independently of seen state.
It records the completed adversarial/correctness panel, addressed findings, source/base
suite failures attributable to the known #393 node, focused installed probes, and the
review-tree cache exception. It does not claim perfect supplied-tree no-write compliance.
The audit compares Git tree objects and binds the merge's source bytes to that reviewed head.

The [repair record](phase5-item5-kit534-repair_2026-09-10.md) and
[verification ledger](phase5-item5-kit534-repair-evidence_2026-09-10/verification.json)
retain the earlier complete synthetic installed run and later focused refinements at
their own pins. The final receipt's focused installed probes are not a full installed
run at the final merge. No delivery reading establishes retained ITEM5-B success.

## Read-only inventory and evidence comparison

The [audit program](phase5-item5-b-update-audit_2026-09-10.py.txt), run as
`python3 -B /Users/topi/Coding/agentic-dev-kit/saved_plans/phase5-item5-b-update-audit_2026-09-10.py.txt`
in `/Users/topi/Coding/agentic-dev-kit` at
`02c991770181e720ba2bb2491dcc688439004a69` with the review corrections below
in the working tree on 2026-09-10, produced the
[audit result and exact write ledger](phase5-item5-b-update-audit_2026-09-10.json).
Its reads established:

- Fixture equality with `fixture-inventory-after-checks.json`, and source equality
  with `source-inventory-after-checks.json`, from the retained ITEM5-B evidence.
  The comparison covers path presence, file bytes, symlink targets and permission
  modes, including the retained cache entries. It excludes `.git`. The current
  audit uses `stat.S_IMODE`, including special permission bits; the historical
  inventory masked those bits out. Exact equality requires their absence now,
  but cannot establish whether they were absent when the historical inventory
  was captured. Retain full permission bits in the execution before/after snapshots.
- The named fixture/source revisions, fixture branch and detached source, independent
  `.git` directories, empty Git status and absent remotes. This is a snapshot, not an
  attestation about everything another process may have done between observations.
- Matching ITEM5-B and repair evidence ledgers, the fixture's original install-baseline
  bytes, and the complete tracked/merged configuration mappings through the installed
  reader, including scalar types. The new proposal does not normalize terminal logs.
- Byte-identical replay evidence between the old source and repair pin. The source
  checkout's replay narrative receives the already-delivered record version from that
  pin; no new replay is performed or credited, and its evidence files do not change.

The audit checked these original paths for both existence and dangling symlinks and
found them absent. Do not create either path:

- `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`
- `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`

## Exact proposed writes and ownership

The JSON ledger is part of this decision, not illustrative. `source_checkout_writes`
enumerates every changed tracked source destination, its Git mode/blob and before/after
SHA-256. `fixture_payload_writes` enumerates the fixture copies and modes.
`baseline_write` contains the complete predicted baseline. Recompute the proposal and
compare these fields before execution; a mismatch requires an amended decision.

| Destination | Proposed action and ownership decision |
|---|---|
| `$KIT`, only the tracked paths enumerated in `source_checkout_writes` | Fetch the exact repair object from `/Users/topi/Coding/agentic-dev-kit` without adding a remote, tags or a fetch-head file; then advance the detached checkout to the repair pin. The entire pinned source is upstream-owned. Source record files remain in the source tree, not copied into the fixture. Retain pre-existing ignored files. |
| `$REPO/scripts/devkit/kit_doctor.py` | Replace from `$KIT/scripts/kit_doctor.py`; kit-owned engine. Its repair adds the controlled inputs to the installable inventory. |
| `$REPO/scripts/devkit/tests/conftest.py` | Replace from `$KIT/scripts/tests/conftest.py`; kit-owned test support. |
| `$REPO/scripts/devkit/tests/test_init_sh.py` | Replace from `$KIT/scripts/tests/test_init_sh.py`; kit-owned test module. |
| `$REPO/scripts/devkit/tests/test_kit_doctor.py` | Replace from `$KIT/scripts/tests/test_kit_doctor.py`; kit-owned test module. |
| `$REPO/scripts/devkit/tests/test_kit_repo_only.py` | Replace from `$KIT/scripts/tests/test_kit_repo_only.py`; kit-owned test module. |
| `$REPO/scripts/devkit/tests/test_mutation_gate.py` | Replace from `$KIT/scripts/tests/test_mutation_gate.py`; kit-owned test module. |
| `$REPO/scripts/devkit/tests/test_portability.py` | Replace from `$KIT/scripts/tests/test_portability.py`; kit-owned test module. |
| `$REPO/scripts/devkit/tests/fixtures/init-config.json` | Add from `$KIT/scripts/tests/fixtures/init-config.json`; kit-owned controlled test input, not adopter configuration. |
| `$REPO/scripts/devkit/tests/fixtures/entry-point-markers.json` | Add from `$KIT/scripts/tests/fixtures/entry-point-markers.json`; kit-owned controlled test input, not adopter policy. |
| `$REPO/kit-manifest.json` | Re-record the adopter baseline from actual destination bytes against the independent repair source, after the copy/config/preservation checks. Never copy the source release manifest into this path. |
| `$REPO/.git/` | Create `chore/item5-b-update-60fe0dc` from the exact input commit; stage only the listed payloads and baseline, and commit the attempt. This writes the new branch/ref log, HEAD/log, index, commit-message file, Git objects and their transient locks. Keep `chore/adopt-agentic-dev-kit` at the historical input. No remote or fixture PR is included. |
| `$KIT/.git/` | Fetch writes Git objects; detached checkout writes HEAD/log, index and transient locks. Use `--no-tags --no-write-fetch-head --no-auto-maintenance --no-recurse-submodules` on fetch. Do not change remote/config policy or create a push destination. Record metadata observations; Git-generated administrative bytes are not predictable payload hashes. |
| `$OUT/` | Create only if absent: `authority.json`, before/after inventory and Git read-backs, `fixture-before.tar`, `source-before.tar`, `fixture-before.bundle`, `source-before.bundle`, copy/baseline/config/ownership reports, command/output logs, `result.json`, hash ledger, and isolated `fixture-state/`, `source-state/`, `fixture-pytest-cache/`, `source-pytest-cache/`, `uv-cache/`, `uv-tools/`, `ruff-cache/`, `tmp/`. Backups contain actual bytes/modes, not only digests; archives exclude `.git`, bundles preserve Git objects. All are new execution evidence, never replacements for the retained evidence directories. |

Create directories only when required by an added destination in the source ledger or
the declared new evidence root. The fixture payload parents already exist in the
audited inventory. The proposed source fetch is a local object transfer, not a fresh
adoption clone or a rerun of the retained setup drivers.

Everything outside those destinations is a preservation decision. In particular retain
the audit's `preserve_hashes` at their exact modes and hashes: `config/dev-model.yaml`,
the ignored `config/dev-model.local.yaml`, `config/claude-lane-settings.json`,
`ROADMAP.md`, `notes/history.md`, `notes/friction.md`, `notes/friction-archive.md`,
`AGENTS.md`, `CLAUDE.md`, `.agents/skills/wrap-up/SKILL.md`, `.codex/hooks.json`,
`.codex/config.toml`, `.claude/settings.json`, `.claude/agents/adversarial.md`,
`.claude/agents/correctness.md`, `.gitignore`, `init.sh` and `.git/hooks/pre-push`.
The policy stays without the former ownership marker; the custom wrap-up stays
adopter-owned. Keep the other adapters, engine/helper files, reference registrations,
and the declared repo-only omissions unchanged. No ownership takeover, config migration,
adapter refresh, lens regeneration, hook installation or initializer run is proposed.

## Baseline change

`kit_commit` would advance from `8418118e40728c667c32a28a182697139bc7a5ef` to
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`. Replace only the file hashes named in
`fixture_payload_writes` and add its new controlled-input keys, using kit-layout
`scripts/…` keys even though the destinations are under `scripts/devkit/`.
Retain `kit_version`, `adopter_owned`, the existing installed scope and `not_installed`.
Do not copy release-only `required_by` metadata into the install baseline.

The audit predicts SHA-256
`9e2196df3b7239b599819abcfc20271b0389b70f78f22837a0709575145b9126` for the resulting
baseline using the recorder's sorted, indented JSON serialization. This is an in-memory
prediction from the stamped audit, not a completed baseline refresh. An approved run
must compare the actual recorded bytes with that prediction and require no unverified
source mismatch, unexpected decline, missing dependency or undeclared new file.
A recorded baseline describes installed bytes; it does not certify that tests passed.

## Execution order and verification

Before writes, recheck exact revisions, branch/detached identity, remote absence,
inventory equality and the unused update branch/evidence-root names. Refuse symlink,
nonregular or unexpectedly linked copy destinations. Bind the absolute roots once;
immediately before each write sequence change to its owning root and assert `pwd -P`
equals that root. Use absolute source and destination paths, then hash each actual
destination and verify its mode. Do not rely on the shell's previous directory.

After backing up, advance the source, prove its tracked bytes match the repair Git
objects and source manifest, and apply only the fixture ledger. Before recording the
baseline, re-read complete tracked/merged mappings through the destination reader and
compare with the retained intended mappings. Compare preservation hashes and the whole
non-Git inventory, allowing only the proposed payload differences. Then run:

```sh
python3 -B "$REPO/scripts/devkit/kit_doctor.py" --root "$REPO" \
  --record-install --from-kit "$KIT"
```

Run from `$REPO`; capture stdout and stderr into separate files under `$OUT`, never
redirect either to the baseline. Compare the actual baseline with the proposal, stage
only the named files and commit the attempt before the suites, so results can name an
immutable fixture revision. Read validation results before a later commit invocation.

| Command; working directory | What it establishes and what to retain |
|---|---|
| `python3 -B "$REPO/scripts/devkit/kit_doctor.py" --root "$REPO" --manifest "$KIT/kit-manifest.json" --json`; `$REPO` | Installed-byte/dependency/baseline comparison to the independent pin. Retain the full report and status, including warnings and ownership states. This does not establish client loading or trust. |
| `python3 -B "$KIT/scripts/kit_doctor.py" --root "$REPO" --adapter-report --adapter-source "$KIT" --json`; `$REPO` | Current source renderer comparison. Expect the preserved custom wrap-up as `adopter-owned`; require the generated bindings and lenses to retain their expected classifications. Reporting a custom adapter does not accept it on the operator's behalf. |
| `python3 -B "$REPO/scripts/devkit/check_doc_budget.py"`; `$REPO` | Configured fixture document budgets. It does not assess prose truth or exercise archival workflows. |
| `uv run --with pytest --with pyyaml python -B "$REPO/scripts/devkit/run_installed_tests.py" --root "$REPO"`; `$REPO` | Complete manifest-selected installed modules at the updated fixture revision. Retain printed selection, full terminal log, actual pytest summary, skip/failure reasons and exit status. No exclusion rerun substitutes for this result. |
| `make test`; `$KIT` | Source lint, current shell-syntax recipe and source pytest suite at the repair pin. Let it finish and read pytest's actual summary. The known #393 deep-JSON failure remains separate; another failure requires its own traceback assessment. #561 means this recipe does not parse every shell file it names. |
| `bash -n "$KIT/scripts/dev_session.sh"`, `bash -n "$KIT/scripts/reconcile_sessions.sh"`, `bash -n "$KIT/scripts/lib/repo_root.sh"`, `bash -n "$KIT/scripts/hooks/pre-push"`, and `sh -n "$KIT/init.sh"`, separately; `$KIT` | Parse each named shell source individually to cover the documented recipe gap. Syntax success does not execute those paths. |
| Full after-inventories, Git identity/status reads, destination hashes and replay-evidence comparison; cockpit with absolute roots | Detect unexpected payload/config/cache/ref changes and bind the reports to the intended destinations. Hash equality is byte evidence, not runtime behavior. |

Run the suites serially, without concurrent checkout, stage, commit, baseline or
other checkout-state writers. Use separate absolute `DEVKIT_STATE_ROOT` values under
`$OUT/fixture-state` and `$OUT/source-state`; set `PYTHONDONTWRITEBYTECODE=1`, route
uv caches/tools under `$OUT`, set `RUFF_CACHE_DIR="$OUT/ruff-cache"` before any
source lint invocation, and direct pytest caches and temporary files there. Ruff
otherwise writes the preserved `$KIT/.ruff_cache`; that default destination is
not authorized by this packet.
Capture the actual environment, argv, cwd, source/fixture SHAs, start/end times,
exit codes, full output hashes and pre/post inventories. Tests can still expose
unexpected writes; stop and report them instead of silently treating them as approved.

The fixture has no project Makefile in its retained input. Do not import the kit's
Makefile or claim an adopter `make test` result; the installed runner is this local
fixture's declared suite. The source `make test` remains required. Successful local
checks would establish updated-fixture verification at the recorded refs, with visible
skips and limitations. They do not complete the remaining field exit.

## Rollback and stop conditions

Keep the retained inventories, baseline and historical Git refs immutable. Verify the
new byte archives and Git bundles before the first source/fixture change. On an input
mismatch, stop before mutation. On a command failure, preserve logs and the attempted
state; do not silently broaden the file set, repair tests, rerun initialization, weaken
selection or refresh another baseline.

Rollback is included only for this attempt's enumerated changes. If the attempt has
committed and no later tracked work exists, switch the fixture back to the unchanged
`chore/adopt-agentic-dev-kit` input and the source back to its original detached pin;
keep the attempt branch and evidence for diagnosis. Before a commit, restore only the
replaced payloads/baseline from verified before-bytes and remove only newly added files
whose current hashes still equal this attempt's proposed bytes. Stop for a new decision
if another writer has changed any target. No broad reset or clean is authorized.

Preserve pre-existing ignored/cache bytes from the before-archives. Any rollback cache
restoration/removal is limited to proven attempt-owned differences after comparison;
never delete an unrelated cache or metadata path. Hash restored files at their actual
destinations and compare the restored non-Git inventories with the before-snapshots.
Git administrative history may retain the attempted fetch/checkout/commit: rollback
restores the named content and refs, not an invented claim of unchanged Git history.

## Packet review corrections

The [review receipt before fixes](https://github.com/topij/agentic-dev-kit/pull/727#issuecomment-5615355490)
records the adversarial and correctness findings at
`02c991770181e720ba2bb2491dcc688439004a69` on 2026-09-10. The audit now includes
special permission bits and states the historical limitation; the procedure declares
and redirects Ruff's cache. The receipt's private baseline simulations reproduced
the predicted baseline at the repair pin. They were disposable-clone probes, not an
execution of this decision or a full installed-suite result.

## Operator choice and remaining scope

Recommended decision: **`Approve ITEM5-B-UPDATE-01 as scoped`**. This authorizes only
the source/fixture/evidence writes above, the local verification, bounded rollback,
and an execution result plus ordinary kit wrap-up/ready-PR review path. The standing
merge-when-clean authority applies to that kit record work; it grants no fixture remote,
fixture PR, client exercise, tracker payload or user-profile change. **`Hold
ITEM5-B-UPDATE-01`** preserves the inputs and leaves this proposal pending. A changed
file set, pin, path, ownership or test strategy needs a revised packet before approval.

Phase 5 item 5 remains incomplete: final preserved-file acceptance, fixture PR lifecycle,
adoption completion and untested systemize routes retain separate exact decisions.
No live systemize/triage routing, notifications, engine-backed route, full restart
recovery or fresh-client discovery is credited here. Item 6 and its replay evidence
stay complete at their recorded refs; do not repeat or re-credit cs-toolkit
#2222/#2223/#2255. Kit #723 remains the approved upstream deferral. #585 stays earlier,
outside Phase 6. Kit #724 already carries the #722 record batch; this packet creates
no replacement batch and restores no deleted explanation.

**Next action:** the operator decides ITEM5-B-UPDATE-01; an approved execution begins
with the retained-input checks, not with copying or repeating setup. The
[maintained sprint status](codex-parity-plan_2026-08-23.md#sprint-status--reconciled-2026-09-10)
continues to own delivery order and completion.
