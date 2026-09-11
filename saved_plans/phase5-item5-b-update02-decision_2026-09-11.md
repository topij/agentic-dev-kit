# ITEM5-B-UPDATE-02 — retained repair update decision

**Prepared; execution not approved.** This packet proposes a local retained update
for the repair delivered in kit #731. Preparation and the kit record PR lifecycle
are authorized. ITEM5-B-UPDATE-01 is consumed; neither that decision, ownership
acceptance nor the kit merges authorizes this attempt. No retained update was run
to prepare this packet.

## Delivery and current input

The [forge readback](phase5-item5-b-update02-evidence_2026-09-11/forge-readback.json.gz)
retains exact `gh pr view` and paginated review-submission, inline-comment and
issue-comment reads from `/Users/topi/Coding/agentic-dev-kit` at
`bc0c33a3af93d78545050612649f49fa72107a40` on 2026-09-11. It read back:

- [Kit #732](https://github.com/topij/agentic-dev-kit/pull/732), merge
  `bc0c33a3af93d78545050612649f49fa72107a40`, reviewed head
  `3927f40befb75694b1efaa7b994c2bacf0a41ece`, and its complete
  [completion checkpoint](https://github.com/topij/agentic-dev-kit/pull/732#issuecomment-5631092756).
- [Kit #731](https://github.com/topij/agentic-dev-kit/pull/731), merge
  `e6d6e77d118454349f8e8bb046e99ef3009c5f5c`, reviewed head
  `1bd4e10b423b0b4b230fb1a481bbc477de784a61`, and its complete
  [delivery checkpoint](https://github.com/topij/agentic-dev-kit/pull/731#issuecomment-5629015678).

The [repair execution](phase5-item5-b-review-followup-execution_2026-09-11.md)
owns its applied scope, independent review receipts and verification limits.
The proposed source is exactly the #731 merge above, not a moving branch. The
audit compares its Git tree to the reviewed head and requires equality. #732
delivered the later handoff; it does not change the selected repair source.

For any later approved execution, bind:

```sh
COCKPIT=/Users/topi/Coding/agentic-dev-kit
REPO=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture
KIT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source
OUT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/update-e6d6e77-20260911
```

Fixture input: `f770f183bf6691f1f706c676b740cf2ef5ceb766`, branch
`chore/item5-b-field-exit`. Source input: detached
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`. Required input baseline SHA-256:
`9e2196df3b7239b599819abcfc20271b0389b70f78f22837a0709575145b9126`.
The fixture origin is `https://github.com/topij/adk-item5-b-field-20260909.git`;
the source has no remote. Preserve these identities.

`env -u PYTHONOPTIMIZE python3 -B /Users/topi/Coding/agentic-dev-kit/saved_plans/phase5-item5-b-update02-audit_2026-09-11.py.txt`
ran from the cockpit at `bc0c33a3af93d78545050612649f49fa72107a40`, with the
new audit program in the working tree, on 2026-09-11. The
[result](phase5-item5-b-update02-evidence_2026-09-11/audit.json.gz) reports
`matches-post-acceptance-checkpoints; proposal-only`. It imports only the committed
acceptance audit's read-only inventory/identity helpers; it never invokes that
audit's historical UPDATE FINAL entry point. Optimized Python is refused before
loading the helpers. The comparison covers descendant file and Git administration
inventories, their permission bits, symlink targets, ignored/cache bytes, refs, index,
config, remotes, branch/detached identity and the baseline. It rechecks the trees
after reading. The complete typed tracked/merged mappings and unchanged item 6
replay evidence are retained in the result.
The inherited inventories omit the supplied roots' own permission modes; checkpoint
equality does not verify the fixture/source root or `.git` root modes.

The comparison uses the post-acceptance
[retained-final checkpoint](phase5-item5-b-review-followup-evidence_2026-09-10/retained-final.json.gz).
The forge readback separately matches the
[forge-after-exit tuple](phase5-item5-b-acceptance-execution-evidence_2026-09-10/forge-after-exit.json),
including private repository identity, PR #1's base/head/body/file set/checks and
the complete original review receipt body hashes. This records checkpoint
equality; it cannot prove absence of transient writes between observations.

The audit checks these exact original paths for existence, including dangling
symlinks. They were absent in that observation. Never reconstruct them:

- `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`
- `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`

## Required prepared-input validation

The earlier audit observations and program/result binding are historical preparation
evidence. Approval or reuse requires the current
[program/result binding](phase5-item5-b-update02-evidence_2026-09-11/prepared-invocation-binding.json),
SHA-256 `3aa074372b408abfbb0f1f812d474439e269d458bbda70c0228a61c2a9bc5ebd`.
It binds the validator and audit program, helper, post-acceptance checkpoints,
configuration/replay expectations, current recorded audit result and original ledger.
It preserves the original audit's different digest as historical provenance.

Run the [read-only validator](phase5-item5-b-update02-validate_2026-09-11.py.txt)
from `$COCKPIT` before an approval decision and again immediately before execution:

```sh
env -u PYTHONOPTIMIZE python3 -B "$COCKPIT/saved_plans/phase5-item5-b-update02-validate_2026-09-11.py.txt" \
  --binding-sha256 3aa074372b408abfbb0f1f812d474439e269d458bbda70c0228a61c2a9bc5ebd
```

The validator rejects a changed binding or bound file, a current-result/program
digest mismatch, changed proposal fields or changed retained inputs. It reruns the
audit only after validating the binding and requires the fresh result to agree.
A bare audit collection, old result or unchanged ledger alone cannot satisfy this
gate. A mismatch requires a revised binding/packet and exact decision; do not edit
historical evidence to make it match. No validation result grants execution authority.

## Proposed payload and write ledger

The [machine-readable ledger](phase5-item5-b-update02-evidence_2026-09-11/proposed-writes.json)
is normative. Its SHA-256 is
`8794cd60d6ac74f0611130324e4a63f6b8697008d65d53371baed830d52485a1`.
It binds exact source and destination paths, before/after SHA-256, permission modes,
source Git blobs, the complete predicted baseline and every changed tracked source
path. The [audit program](phase5-item5-b-update02-audit_2026-09-11.py.txt) recomputes
these fields without mutation. Compare the stable ledger fields immediately before
execution; timestamps and the observer's cockpit revision are observation metadata.
Any input, payload, scope, ownership or verification change requires an amended packet
and decision before dependent work.

| Destination | Exact proposed write |
|---|---|
| `$KIT` tracked paths | Advance the detached checkout from the input to `e6d6e77d118454349f8e8bb046e99ef3009c5f5c`. Apply exactly `source_checkout_writes`, including source-only records and the release manifest. Preserve all existing ignored files. Create only parent directories needed by listed additions. Source records are not fixture payloads. |
| `$REPO/scripts/devkit/conftest.py` | Replace with the [supplied source payload](phase5-item5-b-update02-evidence_2026-09-11/payloads/scripts/conftest.py.txt). Kit-owned regular-file state-root detection and documented inherited special-file limitation. |
| `$REPO/scripts/devkit/tests/test_state_guard.py` | Replace with the [supplied test payload](phase5-item5-b-update02-evidence_2026-09-11/payloads/scripts/tests/test_state_guard.py.txt). Kit-owned regular-file and root-symlink coverage. |
| `$REPO/docs/agentic-dev-kit/workflows/upgrade.md` | Replace with the [supplied workflow text](phase5-item5-b-update02-evidence_2026-09-11/payloads/docs/agentic-dev-kit/workflows/upgrade.md.txt). Kit-owned correction of the newline-normalized renderer comparison claim. |
| `$REPO/kit-manifest.json` | Re-record the install baseline from actual destination bytes against the independent source. Require exact equality to the [predicted baseline](phase5-item5-b-update02-evidence_2026-09-11/payloads/kit-manifest.json.txt). Never copy the source release manifest here. |
| `$KIT/.git` | Local object fetch from `$COCKPIT` with `--no-tags --no-write-fetch-head --no-auto-maintenance --no-recurse-submodules`, followed by detached checkout at the exact source. Object/index/HEAD/reflog/lock writes are Git-generated, observed before/after rather than assigned invented hashes. Preserve config, remotes and existing branch refs. |
| `$REPO/.git` | Create the absent `chore/item5-b-update-e6d6e77` from the fixture input, stage only the named fixture payloads and baseline, and commit the attempt. Preserve `chore/item5-b-field-exit` and all other existing refs at their inputs. Record Git-generated objects/index/HEAD/reflog/commit-message/lock changes. No push, remote/config change or update to the existing PR branch. |
| `$OUT` | Create only if absent. Retain exact authority, copied packet/ledger, before/attempt/final inventories and identities, verified non-Git byte archives and Git bundles, destination/config/baseline reports, raw command/environment/time/status/output records, result and hash index. Allow independent `source-verification/`, `fixture-state/`, `source-state/`, `fixture-pytest-cache/`, `source-pytest-cache/`, `uv-cache/`, `uv-tools/`, `ruff-cache/`, and `tmp/`. No historical evidence path is reused. |
| Kit records | Record the later exact decision and execution evidence in new records, update maintained sprint status and handoff, and finish a ready kit PR through pr-watch and standing scoped merge authority. Historical questions, ledgers and evidence remain byte-preserved. |

The predicted baseline SHA-256 is
`61d9aaf2c8bafe6da1957111a41e0bc1d8197e08b84c9b12f24fa996535b48fe`.
This is a proposed constant, not a retained baseline reading. Change `kit_commit`
to the exact source and replace only the ledger's installed-file hashes. Preserve
`kit_version`, `adopter_owned`, `not_installed` and installed scope; retain kit-layout
keys while writing mapped fixture destinations. Do not introduce release-only
`required_by` metadata. A baseline records bytes, not successful behavior.

## Preservation and limits

The audit's `preserve_fixture_inventory` is the complete non-Git preservation set:
every fixture path except the ledger payloads and baseline. Keep the accepted
markerless `AGENTS.md`, `CLAUDE.md`, configured roadmap/history/friction documents,
tracked and ignored config, lane policy, hooks/registrations, generated adapters
and lenses, custom wrap-up, initializer, ignored/cache files and CI workflow at their
recorded bytes, modes and file kinds. Preserve `.git/hooks/pre-push` and Git config
from the administration checkpoint. Required fixture parents already exist.

ACCEPT-01 remains ownership acceptance only. The custom wrap-up's `Preserve this
adapter.` body is deliberately nonfunctional; keeping it does not verify wrap-up.
Doctor or adapter classifications are not client loading/trust/execution evidence.

**Accepted inherited limitation:** special-file roots remain outside this repair's
coverage. In particular, a FIFO at the state root remains invisible to the inherited
snapshot and can obstruct engine state persistence. No special-file detection or recovery is supplied or claimed.
Regular-file/root-symlink checks do not establish special-file safety. If such a
root or an unexpected file kind is found before execution, stop for a separate
decision; do not open it to probe behavior or silently widen this update.

This local proposal deliberately leaves fixture PR #1 at its recorded head. Its
adopter-owned CI workflow and PR body still name source `60fe0dc...`; their retained
hosted result cannot verify the proposed source or a new local fixture commit.
Continuing that PR needs a separately reviewed exact CI/body/publication/review
decision. No existing approval is used to push the new branch, retarget the PR,
close it, change its draft state or merge it. Fixture merge remains excluded.

No initialization, hook installation, configuration migration, adapter/lens refresh,
client/trust/profile exercise, fixture settings change, tracker/notification payload,
live triage/systemize route, broad cleanup or replay is included. The kit's own
independent record reviewers are not fixture field exercises.

## Execution order and verification, only after approval

Before every write sequence, enter the owning absolute root and assert `pwd -P`
equals it. Use absolute paths for every write and hash the intended destinations.
Reject symlink aliases, nonregular or multiply-linked copy targets and aliased
parents. Apply these checks explicitly to `kit-manifest.json` as well: its
`--record-install` writer writes in place, so a hardlink would change an unlisted
alias. The audit checks its lexical path, regular-file kind and single-link status
before accepting inputs; recheck them immediately before the baseline command.
The fixture and source Git administration must contain only lexical directories
and single-link regular files. The audit rejects linked reflogs and other aliased
Git paths before any dependent write. Immediately before each Git mutation sequence
(including rollback), recheck both retained administrations with this read-only guard.

The audit and immediate guard also reject inherited `GIT_*` environment controls,
except an absent `GIT_PAGER` or the literal `GIT_PAGER=cat`. This includes reads:
Git tracing can write outside the ledger during an otherwise read-only command.
Use the same checked environment for the dependent commands, including the baseline
writer's Git calls; any environment change requires the guard again. A refusal
requires correcting the invoking environment and rerunning validation, not ignoring
the check or silently stripping controls only from the audit.

```sh
env -u PYTHONOPTIMIZE python3 -B - "$COCKPIT" "$REPO" "$KIT" <<'PYGITGUARD'
from pathlib import Path
import runpy
import sys
cockpit, repo, kit = map(Path, sys.argv[1:])
check = runpy.run_path(str(cockpit / 'saved_plans/phase5-item5-b-update02-audit_2026-09-11.py.txt'))['check_git_administration']
check(repo)
check(kit)
PYGITGUARD
```

Proceed only after that guard succeeds; no Git write is authorized after a refusal. Require complete checkpoint equality, empty status/index, exact input
refs/remotes and absent attempt branch/evidence root. Re-read the fixture forge
tuple and original complete review receipts before any fix; a mismatch stops.
Do not reinterpret UPDATE FINAL as today's checkpoint.

Create and verify new fixture/source non-Git byte archives with modes and link
targets, plus Git bundles containing input HEADs and existing refs, before changing
either retained tree. Save administration inventories separately; a bundle is not
a backup of ignored bytes or Git config/hooks. Verify archive membership/content
and bundle integrity, then perform the ledger's source fetch/checkout. Check every
tracked source destination against its Git blob and release-manifest hash and
require the full source delta to equal the ledger.

Create the new fixture branch from the input and copy only its payloads. Compare
full typed config through the installed destination reader against the audit's
independent expected mappings. Compare every preserved path, then run from `$REPO`:

```sh
env -u PYTHONOPTIMIZE python3 -B - "$REPO" "$KIT" <<'PYBASELINE'
import stat
import subprocess
import sys
from pathlib import Path
repo, kit = map(Path, sys.argv[1:])
p = repo / 'kit-manifest.json'
s = p.lstat()
assert p.resolve() == p and stat.S_ISREG(s.st_mode) and s.st_nlink == 1
subprocess.run([sys.executable, '-B', str(repo / 'scripts/devkit/kit_doctor.py'),
                '--root', str(repo), '--record-install', '--from-kit', str(kit)],
               check=True)
PYBASELINE
```

Capture stdout/stderr under `$OUT`, never redirect into the baseline. Require
actual baseline bytes to equal the predicted payload. Read staged-path validation
and `git diff --cached --check` before a separate commit invocation. Commit the
attempt before suites so fixture results name an immutable revision. No concurrent
test, checkout, stage, commit, baseline or other checkout-state writers.

Route nonempty role-specific `DEVKIT_STATE_ROOT`, `UV_CACHE_DIR`, `UV_TOOL_DIR`,
`RUFF_CACHE_DIR`, `TMPDIR` and pytest cache paths under `$OUT` before any tool starts.
Set `PYTHONDONTWRITEBYTECODE=1`, unset `PYTHONOPTIMIZE`, and use `python -B`.
Record actual environment, argv, cwd, input/source/attempt SHAs, date, start/end,
exit status and full unmodified output. Run suites serially, without arbitrary
wall-clock kills; actively wait for terminal output and read pytest's actual summary.

| Command / working directory | Required evidence and boundary |
|---|---|
| `python3 -B "$REPO/scripts/devkit/kit_doctor.py" --root "$REPO" --manifest "$KIT/kit-manifest.json" --json` / `$REPO` | Full installed-byte/dependency/baseline report; no unverified mismatch or unapproved decline. No client/function claim. |
| `python3 -B "$KIT/scripts/kit_doctor.py" --root "$REPO" --adapter-report --adapter-source "$KIT" --json` / `$REPO` | Preserve the accepted custom wrap-up's `adopter-owned` classification and the expected generated bindings/lenses. Keep the newline-normalized comparison limit explicit. |
| `python3 -B "$REPO/scripts/devkit/check_doc_budget.py"` / `$REPO` | Configured fixture budget report. No archival workflow execution. |
| `uv run --with pytest --with pyyaml python -B "$REPO/scripts/devkit/run_installed_tests.py" --root "$REPO"` / `$REPO` | Complete manifest-selected installed suite at the attempt SHA; retain selection, skips/reasons, summary and status. No deselection rerun substitutes for this result. |
| `make test` / `$OUT/source-verification` | Clone independently with `git clone --no-hardlinks --no-checkout "$KIT" "$OUT/source-verification"`, detach the clone at the proposed source, then run source lint/syntax/pytest. This avoids verification caches in retained `$KIT`. |
| Separate `bash -n` for `scripts/dev_session.sh`, `scripts/reconcile_sessions.sh`, `scripts/lib/repo_root.sh`, `scripts/hooks/pre-push`, and `sh -n init.sh` / source verification clone | Invoke each with its absolute clone path. These cover #561's known recipe gap; they do not repair it or execute shell behavior. |
| Destination hashes, full inventories, typed config, baseline, Git identity and replay comparison after commands / cockpit with absolute roots | Permit only declared deltas and attempt-owned output. Keep source and fixture verification observations distinct. |

The retained fixture has no project Makefile: do not import one or claim fixture
`make test`. Source `make test` remains mandatory. Disclose the known #393 deep-JSON
failure separately, using its actual traceback; never call a failing suite passing.
A different failure, changed skip scope, missing terminal summary, unexpected write
or source/payload mismatch stops execution for assessment. Do not repair tests or
change selection in this attempt. Successful installed verification would establish
only that recorded run at that fixture SHA; it does not complete field exit.

## Conditional rollback

Retain logs and the attempted state before undo. Rollback is limited to this
attempt's ledger, conditional on destinations, index and refs still matching the
recorded attempt. Intervening work or ambiguous partial checkout/fetch stops for
a new decision. No broad reset/clean, recursive removal, historical rollback,
remote deletion or evidence deletion.

- Before any undo of an uncommitted fixture, capture NUL-delimited staged paths
  against `f770f183bf6691f1f706c676b740cf2ef5ceb766`; require every path to be in
  the fixture ledger. Unrelated staged work stops both fixture and source undo.
- If source advanced and its detached HEAD/index/tracked bytes still match the
  proposed source, switch it detached back to `60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`.
  If it never advanced, no source undo is needed. Preserve fetched objects and
  administrative history; do not restore old files under an advanced HEAD.
- For an uncommitted fixture, restore only the replaced payload/baseline bytes and
  modes from verified before-archives. Restore only the captured staged paths
  with `git restore --source=f770f183bf6691f1f706c676b740cf2ef5ceb766 --staged --`
  followed by literal path arguments; skip that command for an empty set. Require
  empty staged/worktree diffs before switching back to `chore/item5-b-field-exit`.
- For a committed fixture attempt with no later work, switch back to unchanged
  `chore/item5-b-field-exit` at the input. Keep the attempt branch/commit and evidence.
  No existing remote branch was moved, so no remote undo is proposed.
- Hash restored destinations and compare complete non-Git inventories to before
  snapshots. Preserve pre-existing ignored/cache bytes. An unexpected cache or
  administration change requires its own named restoration decision; do not
  silently erase it. Check input branch/source identity and empty tracked diffs.
  Administrative history records the attempt; it is not claimed byte-unchanged.

## Preparation review and correction

Before changing the submission, the complete independent
[adversarial receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5632042580)
and [correctness receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5632043110)
were published against `7a598687a642e7ea7c66e941ee292323cfc63500`.
The [raw review record](phase5-item5-b-update02-evidence_2026-09-11/review-round1.json.gz)
preserves their reports, commands, logs, mutation/restoration evidence and actual
compute readback. The original preparation evidence and ledger remain unchanged.

The adversarial reproduction found that an external baseline hardlink could pass
the original audit and receive an unlisted in-place write. This packet now checks
the baseline explicitly and gates the doctor's invocation on the immediate check.
The correctness reproduction established that a FIFO obstructs state persistence
while remaining invisible to the snapshot; the accepted limitation above uses that
explanation. These corrections change preparation safeguards and wording, not the
selected source or fixture payloads, and grant no retained execution authority.

The hardened audit ran from `/Users/topi/Coding/agentic-dev-kit` at
`7a598687a642e7ea7c66e941ee292323cfc63500`, with the candidate guard in the working
tree, on 2026-09-11 using the audit command above. Its
[result](phase5-item5-b-update02-evidence_2026-09-11/audit-preflight-hardened.json.gz)
reports `matches-post-acceptance-checkpoints; proposal-only`; stable proposal fields
equal the original ledger. The original audit result remains the original observation,
with its program bytes preserved in the review record and the reviewed Git revision.
The [guard proof](phase5-item5-b-update02-evidence_2026-09-11/baseline-guard-proof.json.gz)
retains the disposable-copy rejection, mutation, restoration and exact packet-wrapper
checks, with their command/directory/revision/date stamps. Kit PR #733 owns subsequent
review and verification receipts; none is retained-fixture execution evidence.

The subsequent complete
[adversarial receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5632476783)
and [correctness receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5632477163)
were published at `e461b092ee66fdb20ea62aea3d193034f58d622c` before the next fix.
The [raw round record](phase5-item5-b-update02-evidence_2026-09-11/review-round2.json.gz)
also preserves the configured bot's complete review and inline finding before that
fix. The adversarial reproduction demonstrated an external reflog alias changed by
branch creation; the audit and immediate Git guard now reject aliased administration.
The bot identified the original/current audit digest difference; the required validator
above now binds the current result and program without rewriting the old observation.

The [administration guard proof](phase5-item5-b-update02-evidence_2026-09-11/git-administration-proof.json.gz)
retains the hostile reflog rejection and the mutation that defeats it, with byte
restoration. The [binding proof](phase5-item5-b-update02-evidence_2026-09-11/binding-proof.json.gz)
retains refusal of a wrong decision digest, optimized Python, changed program bytes
and an internally inconsistent recorded result. These commands ran on 2026-09-11 in
the named disposable copies at `e461b092ee66fdb20ea62aea3d193034f58d622c` with the
candidate preparation changes; their actual argv/cwd and limits are preserved.
The read-only validator command in that proof also ran from
`/Users/topi/Coding/agentic-dev-kit` at the same revision/date with those candidate
changes. Its [result](phase5-item5-b-update02-evidence_2026-09-11/prepared-validation.json.gz)
reports `prepared-inputs-and-program-binding-verified; proposal-only` and retains the
fresh retained-tree audit. That historical binding selected the
[administration audit observation](phase5-item5-b-update02-evidence_2026-09-11/audit-git-administration.json.gz).
The source and destination ledger remain the original proposal.

At `88c5b044d5a42e33d2c4b0158be0957b4014678a`, the complete
[correctness receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633056489)
and the [incomplete adversarial runtime receipt and author trace proof](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633065607)
were preserved before the environment guard and permission-coverage qualification.
The interrupted runtime supplies no merge clearance. The
[raw record](phase5-item5-b-update02-evidence_2026-09-11/review-round3.json.gz)
preserves its unfinished draft and failure without completing them retrospectively.
The required binding above selects the
[runtime-guard audit observation](phase5-item5-b-update02-evidence_2026-09-11/audit-runtime.json.gz).
The [guard proof](phase5-item5-b-update02-evidence_2026-09-11/runtime-guard-proof.json.gz)
and [validator result](phase5-item5-b-update02-evidence_2026-09-11/prepared-runtime-validation.json.gz)
retain their actual commands, candidate revision, date and boundaries. They are
preparation evidence, not retained-update execution or independent merge clearance.

The [complete correctness receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633355983)
at `207683b073f4d34cf22c5d9e1635f1c23239b6d4` was preserved before correcting
the validator's generated invocation metadata. It now records Python's original
argument vector, including interpreter flags. The
[new validation observation](phase5-item5-b-update02-evidence_2026-09-11/prepared-invocation-validation.json.gz)
retains the actual launcher comparison; older receipts are unchanged.
The [adversarial runtime failure](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633204702)
at that revision supplies no final report or merge clearance. The
[round record](phase5-item5-b-update02-evidence_2026-09-11/review-round4.json.gz)
preserves the completed correctness review and interrupted adversarial run.
Required review of the corrected packet and kit publication
remain pending; no further attempt is made to bypass the runtime restriction.

The later [source-review triage](phase5-item5-b-update02-review-triage_2026-09-11.md)
preserves CodeRabbit's complete review at
`cf373efd3a4d00b36987f73574d567eef004594a` and the inherited source findings.
It proposes a separate kit-only repair and holds the retained-update decision
pending source-scope disposition. The frozen payloads, ledger and binding below
remain unchanged; this record neither accepts the findings as limitations nor
selects a replacement source. Required independent review remains incomplete.

## Exact decision and next session

**Approval question:** Do you approve **ITEM5-B-UPDATE-02 as scoped in this packet
and ledger SHA-256 `8794cd60d6ac74f0611130324e4a63f6b8697008d65d53371baed830d52485a1`,
with prepared-input binding SHA-256
`3aa074372b408abfbb0f1f812d474439e269d458bbda70c0228a61c2a9bc5ebd`**:
advance the retained source to `e6d6e77d118454349f8e8bb046e99ef3009c5f5c`, apply
only the listed fixture payloads, record the predicted baseline, create the named
local attempt branch/commit and evidence root, run the declared local verification
and conditional rollback, and deliver the resulting scoped kit records, while
retaining the accepted special-file-root limitation and excluding fixture
publication/PR continuation/merge, initialization, client/trust/profile exercises,
settings changes and tracker payloads?

No answer, preparation, review or merge of this kit packet is execution approval.
The exact response and packet/ledger hashes must be retained before approved work.

The [maintained sprint status](codex-parity-plan_2026-08-23.md#sprint-status--reconciled-2026-09-10)
keeps Phase 5 item 5 incomplete. Ownership acceptance, functional verification and
field-exit completion remain distinct. Item 6 and its replay evidence remain
complete without repeat or new credit for cs-toolkit #2222/#2223/#2255. #723 remains
the approved upstream deferral; #585 stays earlier outside Phase 6; #724 delivered
the #722 batch. The friction sweep remains parked pending its exact operator decision.

**Next session:** obtain the source-scope decision in the linked review triage.
Complete required review and kit PR follow-through before requesting the retained
update decision. Preserve this exact unanswered question if a later source decision
requires a replacement packet; fixture PR continuation and field exit stay separate.
