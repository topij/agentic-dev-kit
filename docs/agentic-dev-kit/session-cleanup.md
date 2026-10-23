# Completed-session cleanup

Use this lifecycle from Claude or Codex when a session creates review rounds or
disposable worktrees. It wraps `sweep_scratch.py`; it does not replace its dependency
checks or authorize a general sweep. Configure `scratch.session_registry` as a
simple directory name, for example `cleanup-sessions`. Existing adopters add that
key explicitly. `<engine-dir>` is `paths.engines` from merged configuration.

## Record ownership before work starts

Run from the exact repository root. Start an inventory and retain the returned
`id` as `<session>`:

```sh
uv run <engine-dir>/session_cleanup.py start
uv run <engine-dir>/session_cleanup.py allocate <session> --root <expanded-root> --head <sha>
```

Resolve `<expanded-root>` from `scratch.roots` using this checkout's path. Create
that exact directory if absent. Allocation returns the sweeper's receipt and
persists it before a reviewer may start. Use its `path` for the round, and retain
its JSON outside the round for `panel_prompt.py` and standalone diagnosis. Allocate
earlier and later rounds into the same inventory while it remains unsealed. For
review loops that retire each round before the next starts, start a fresh inventory
per round; `list` discovers them together through the repository's shared metadata.

The registry lives at `<git-common-dir>/devkit/<scratch.session_registry>/`.
It binds the common directory identity, allocation identities, original root
namespace, reviewed head and cleanup policy. Its paths survive task-checkout
removal. It accepts no imported receipt as new root authority. If allocation fails
before returning, do not launch a reviewer: a marker may have been created without
its registry record, and the failure needs reconciliation rather than guessed
ownership. Do not change protection roots, dependency repositories or the registry
during this lifecycle. Such changes keep the old inventory unavailable until its
original policy is restored or explicitly reconciled; there is no migration override.
`list` reports an unavailable record with its path and reason while still listing
other inventories. Changing only `scratch.grace_window` does not invalidate recorded
retirement: this lifecycle already bypasses age through explicit ownership.

Register actual writer process ids while they exist. Joining a parent is not
proof its descendants ended:

```sh
uv run <engine-dir>/session_cleanup.py track-process <session> --pid <pid>
```

Register disposable linked worktrees after their final commit, before sealing:

```sh
uv run <engine-dir>/session_cleanup.py track-worktree <session> <absolute-path> --runtime git
uv run <engine-dir>/session_cleanup.py track-worktree <session> <absolute-path> --runtime codex
```

Use `codex` only for app-managed worktrees and `git` for ordinary Git worktrees.
The primary checkout is never eligible. The registry binds the recorded head and
directory identity; a later commit requires a new inventory. Branch names are
recorded but branches are not deleted by this engine. A branch's forge lifecycle
remains separate from local scratch retirement. Ordinary Git retirement requires
the recorded commit to be reachable from a shared branch, tag or remote-tracking
ref; preserve an unreferenced detached commit on a branch before retrying.
Checkout-local refs such as bisect/worktree/rewritten refs disappear on removal
and cannot establish retention. Other custom ref namespaces are conservatively
insufficient too. Codex's native archive preserves its commit snapshot instead.

## Retain required evidence, then seal

Stop or join every reviewer, verifier and descendant first. Write a JSON manifest
at an absolute path outside the disposable inventory. Enumerate final terminal
reports, unresolved findings and dispositions, reviewed-head and compute receipts,
concise verification/mutation/restoration proof, and merge/ticket readbacks when
they exist. Include authoritative live-validation bytes, screenshot source and
finished assets, capture receipts, policy snapshots and any required source input.
Package caches and basetemps belong in allocated scratch, never in retained evidence.

```json
{
  "evidence_complete": true,
  "retain": [
    {"source": "/absolute/round/report.md", "kind": "report", "requires": ["/absolute/round/capture.png"]},
    {"source": "/absolute/round/capture.png", "kind": "asset", "requires": []}
  ],
  "retire": [
    {"source": "/absolute/round/verbose.log", "reason": "Terminal report preserves the result", "replaced_by": ["/absolute/round/report.md"]}
  ]
}
```

Supported kinds are `report`, `finding`, `verification`, `compute`, `source`,
`asset` and `receipt`. Each `requires` path must also appear in `retain`.
`evidence_complete` is the caller's explicit assertion of the complete evidence
closure, including links and manifests; the engine cannot infer that closure from
arbitrary prose. Missing, unreadable, aliased or non-regular evidence blocks sealing.
Content-addressed copies preserve original bytes and are hash-checked before cleanup.

```sh
uv run <engine-dir>/session_cleanup.py seal <session> <absolute-manifest>
```

The sealed `session.json` is the retention index: it maps original source paths to
retained bytes, their hashes, dependencies and intentionally retired diagnostics.
Historical documents are preserved byte-for-byte, not rewritten; resolve their old
paths through this index. Enumerate superseded logs in `retire` with a reason and
retained replacement. Unlisted scratch is covered only by the caller's evidence
closure assertion, never by filename or age heuristics. Sealing freezes the inventory;
new work uses a new session. Back up this local evidence with the repository's Git
metadata; a fresh clone does not contain it, and deleting the repository deletes it.

## Preview, approve the concrete scope, apply

From the primary checkout, discover inventories and preview the desired session:

```sh
uv run <engine-dir>/session_cleanup.py list
uv run <engine-dir>/session_cleanup.py preview <session>
```

Inspect the exact paths, owner, observed bytes (`null` means unavailable), retained
evidence, active users and keep reasons. Ordinary wrap-up and session-start do not
authorize deletion. Obtain operator authorization covering these concrete paths,
or reuse explicit authorization already covering them. The preview's
`approval_token` binds the inventory and seal; it is not itself operator consent.
Do not generate an apply invocation from a vague or unattended request.

After every writer and descendant has ended, run:

```sh
uv run <engine-dir>/session_cleanup.py apply <session> --approve <approval-token> --processes-finished
```

Approval is persisted for retries. The process flag is a renewed completion
attestation, not permission to kill processes. Known PIDs, including reused PIDs,
block cleanup while present. Local `lsof` observation supplements that attestation;
missing, timed-out or partial observations block cleanup. Only processes/files
visible to the current user are covered. Run from outside every disposable path.
The supported environment is POSIX with Git and `lsof`; other hosts must preserve
the inventory and report the unavailable capability.

Ordinary worktrees are removed by Git without force, after identity, head, status
and dependency checks. Both runtimes refuse index flags that hide tracked changes
(`assume-unchanged` or `skip-worktree`): inspect the affected paths and clear those
flags before retrying, preserving any work they conceal. Both runtimes also refuse
ignored content, including caches:
retain required files through the seal, verify their retained bytes, then explicitly
move or remove the original ignored files before retrying. A clean Git status alone
does not establish that ignored data is disposable. App-managed worktrees return
`archive-with-runtime` only after these checks: use Codex's native archive tool on
that exact attachment under the same authorization. Re-run apply from the primary
checkout after the archive. Never recursively delete an app-managed checkout.

Round retirement uses the existing sweeper with fresh dependencies at act time.
Worktree retirement also reads its configured Git-store, worktree and root protections
before recommending native archive and immediately before ordinary Git removal.
Shared Git stores, inbound alternates and external registered worktrees stay
protected within its configured repository scope. The fixture-only route is the
owned-round contract in `fallback-review-panel.md`; neither unchanged fixture bytes
nor a clean Git status proves global disposability. Unconfigured repositories and
unrecorded external consumers remain outside that scan's proof. Quiescence is
required; the registry is not a security boundary against concurrent same-user writes.

Interrupted deletion can resume only after its approved removal intent was
durably recorded following the sweeper's final guards. A missing round marker is
tolerated in that state because recursive removal may have already unlinked it;
replacement directories, changed roots and malformed surviving markers still
refuse. Standalone `--finish-review-round` still requires its marker.

Exit status is `0` for completed cleanup, `1` for kept/active/native-archive work,
and `2` for refusal or unavailable prerequisites. Keep reasons mean incomplete
cleanup, not success. Inspect the final `last_result` in the durable index, recheck
retained hashes, and report residual paths and the next supported action. Applying
an already completed inventory is a no-op while its paths remain absent. Never
broaden roots, weaken dependencies or use a general age sweep to clear a refusal.
