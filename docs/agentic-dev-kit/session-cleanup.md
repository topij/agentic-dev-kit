# Completed-session cleanup

Use this lifecycle from Claude or Codex when a session creates review rounds or
disposable worktrees. It wraps `sweep_scratch.py`; it does not replace its dependency
checks or authorize a general sweep. Configure `scratch.session_registry` as a
simple directory name, for example `cleanup-sessions`. Existing adopters add that
key explicitly. `<engine-dir>` is `paths.engines` from merged configuration.

## Clean up what this session created

A session deletes the files and directories **it created** once nothing needs them,
while it works and again before it ends. Leftover review rounds, lens worktrees,
throwaway clones and killed test runs are what fill a local disk; a later session
cannot tell them from live work, so the session that made them is the only one that
can remove them safely.

**Ownership is recorded, never inferred.** A path is this session's only when the
session created it and recorded its exact absolute path at creation: an allocation
receipt, a registry inventory, a worktree it added, or a path it noted when it ran
`mktemp`, `git clone` or an extract. A name, an age, a location or a similar-looking
sibling is not ownership. Create ad-hoc scratch under an expanded `scratch.roots`
entry (the runtime's own scratchpad only when a root covers it), never directly under
the system temp directory or inside the repository, so `sweep_scratch.py` can still
see whatever is missed.

**Clean up at each point where a thing stops being needed**, not only at the end:

| What the session created | When it is no longer needed | How to remove it |
|---|---|---|
| A review round | its receipt or findings are recorded on the PR | the round retirement in `fallback-review-panel.md`, or the registry lifecycle below |
| A lens or verifier worktree | its findings are dispositioned on the PR | `git worktree remove <path>` without `--force`, after checking its status and that its `HEAD` is reachable from a pushed ref |
| A throwaway clone, extracted archive, eval output or build tree | its result has been read and anything worth keeping copied out | delete that exact recorded path |
| A killed or abandoned test run's basetemp | the run it belonged to is over | delete that exact recorded path |
| A parallel lane this session launched and recorded | its PR merged and its PR body carries the lane's handoff | `<engine-dir>/dev_session.sh rm <scope>`, which owns the lane's sandbox removal; never delete a lane's `state/` sandbox by hand |
| The session's own linked task worktree | its PR merged, or closed with its head pushed | from the primary checkout, with the shell outside the worktree: `git worktree remove <path>` without `--force`, after checking its `HEAD` is reachable from a pushed ref; a Codex app-managed worktree goes through the native archive |

With `scratch.session_registry` configured, a worktree the session registered with
`track-worktree` retires through the sealed-inventory lifecycle below, not through a
plain `git worktree remove`.

Delete a recorded path by its exact absolute path, never through a glob, a parent
directory or a pattern. Before deleting, confirm the path is still the one recorded
and that it is not a registered worktree (remove that with `git worktree remove`)
and holds no commit that exists nowhere else.

**Never delete**, whatever a rule above seems to allow: anything this session did not
create; the primary checkout; the kit's `state/` sandboxes and anything the
configuration names as state; the registry under `<git-common-dir>/devkit/`, retained
evidence included (it leaves only through `retire-evidence` below, under operator
authorization); an allocation receipt whose retirement has not completed; the handoff and
friction-log files; shared caches such as the package manager's; or a tree with
uncommitted or unpushed work. An engine refusal or `kept` result stays kept: report
it, and never weaken a guard, reset timestamps or broaden a root to clear it.

**Authorization.** Without a standing grant, deletion follows the rest of this
document and `fallback-review-panel.md`: an engine preview, then operator
authorization covering the concrete paths. An operator may instead grant standing
authorization by writing it into the repository's `AGENTS.md`; the ready-made section
is *Session cleanup* in `docs/AGENTS-sections.md`. A standing grant covers only paths
this session created and recorded, of the kinds in the table above. It replaces
asking, not checking: every preview, `approval_token`, `--processes-finished` or
`--reviewers-finished` attestation and engine guard still applies. It never covers an
age sweep (`sweep_scratch.py --apply --older-than`), which reaches entries other
sessions created; present those for operator approval as before.

**Report what is left.** The wrap-up names the paths this session removed and every
path it created but kept, with the reason.

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
later rounds into the same inventory while it remains unsealed, after retiring the
earlier one (*Retire each round before the next* below). `allocate` refuses while an
earlier round is unretired, naming it. Only an explicit reason lets a round outlive
the next allocation; it is recorded on that round, which then retires with the
inventory:

```sh
uv run <engine-dir>/session_cleanup.py allocate <session> --root <expanded-root> --head <sha> --keep-previous "<reason>"
```

An interrupted round retirement refuses the next allocation whatever the reason:
resume it first. `list` discovers every inventory through the repository's shared
metadata.

The registry lives at `<git-common-dir>/devkit/<scratch.session_registry>/`.
It binds the common directory identity, allocation identities, original root
namespace, reviewed head and cleanup policy. Its paths survive task-checkout
removal. It accepts no imported receipt as new root authority. If allocation fails
before returning, do not launch a reviewer: a marker may have been created without
its registry record, and the failure needs reconciliation rather than guessed
ownership. Do not change protection roots, dependency repositories or the registry
during this lifecycle. Such changes keep the old inventory unavailable until its
original policy is restored; there is no migration override. `list` reports an
unavailable record with its path and reason while still listing other inventories.
The reason names each bound field that differs (`volume`, `device`, `inode`,
`identity kind`, `schema`, `id` or `policy <key>`) with its stored and current values; a key present on one side
only shows `absent` on the other, and a malformed stored value is named as
`common identity` or `policy (stored value is not a mapping)`. Changing only
`scratch.grace_window` does not invalidate recorded retirement: this lifecycle
already bypasses age through explicit ownership.

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

## Filesystem identity, and reconciling an inventory

The registry and its allocation receipts bind each directory (the common directory,
the scratch root, each round and each tracked worktree) by a filesystem identity
that survives a reboot where the platform offers one:

- `["volume", <UUID>, <inode>]` on macOS, from `getattrlist`'s volume UUID. macOS
  renumbers the device number across reboots, and on Data-volume paths `statvfs`'s
  `f_fsid` is that same number. The volume UUID belongs to the volume that holds the
  directory, which `st_dev` does not tell apart: on an APFS firmlinked system
  `stat("/")` reports the Data volume's device number, while `/` is the sealed system
  snapshot with its own UUID.
- `["device", <st_dev>, <inode>]` elsewhere, and on macOS when no volume UUID is
  readable. Linux has no standard-library route to a filesystem UUID. A device
  number that renumbers still makes these inventories unavailable, and reconcile
  below is the way back.

The two kinds never compare equal: a record bound to a volume refuses when its UUID
becomes unreadable, or reads as another volume. The kind is fixed when the record is
written, and reconcile does not rebind across kinds: a record bound to `device`
because no UUID was readable then stays unavailable once one is, and needs a new
inventory. New inventories use schema `devkit-cleanup-session/2`, and new
allocation receipts `version` 2. A schema 1 inventory, written before boot-stable
identities, keeps loading on its bare device and inode pair exactly as before, and
is never accepted on inode and path alone; it moves to schema 2 only through
reconcile, after a renumber. A version 1 receipt keeps its own device and inode
check. Rounds and worktrees recorded into a schema 1 inventory from now on bind the
new identity.

Reconcile is a preview, then an approved apply:

```sh
uv run <engine-dir>/session_cleanup.py reconcile <session>
uv run <engine-dir>/session_cleanup.py reconcile <session> --approve <approval-token>
```

It accepts the device number as the only difference, on a schema 1 inventory or on
one bound to the `device` kind: schema, id, inode and policy (which carries the
canonical common directory) must still match, and any other difference refuses.
Every recorded round and worktree path must be absent and no recorded worktree may
still be registered with Git; an error inspecting a path other than its absence
refuses reconcile. It also refuses an unapproved interrupted removal, checked once
every other bound field is trusted. The preview writes nothing and lists the
differences, the stored and current schema and identity, the rounds it will mark
removed, which of those retained no evidence (`rounds_without_seal`) and the absent
worktrees. Its token binds the stored record and that plan, including the current
identity, and it is not itself operator consent: apply only under authorization
covering that inventory. Apply rebinds the common directory to the new identity and
schema 2, marks the listed rounds removed, records the change under `reconciled`
and marks the inventory complete. It deletes nothing, retained evidence included;
an open inventory continues as before. An inventory with a round or worktree still
present stays unavailable: those paths carry the old device number in their own
recorded identities, which reconcile cannot re-verify. The same holds for a
receipt: `--finish-review-round` refuses a device-bound round that survived a
renumbering as replaced.

## Seal: discard by default, retain only by exception

Completed review, build and evidence payloads are discarded. Their results belong in
Git and the pull request (the review dispositions `pr_watch.py --record-review`
records, the PR body, the merged commit); a local copy kept "in case we investigate
later" is not a reason to retain. Copying evidence is never needed to seal and clean
up a session.

Stop or join every reviewer, verifier and descendant first. Write a JSON manifest at
an absolute path outside the disposable inventory. The normal manifest retains
nothing and says where the results went:

```json
{
  "evidence_complete": true,
  "retain": [],
  "discard": [
    {"source": "/absolute/round", "reason": "findings and dispositions recorded on PR #123"}
  ]
}
```

Retain an item only as an exception: when a named unfinished task needs these exact
local bytes, such as a current recovery package or unique authored drafts not yet in
Git. Each retained item states that task, the next action and the condition under
which it may be deleted, and the engine refuses one without all three:

```json
{
  "evidence_complete": true,
  "retain": [
    {"source": "/absolute/round/draft.md", "kind": "source", "requires": [],
     "exception": {"task": "CUS-123 article rewrite", "next_action": "commit the draft to the article branch",
                   "delete_when": "the article branch carries the draft"}}
  ],
  "discard": [{"source": "/absolute/round/report.md", "reason": "recorded on PR #123"}]
}
```

Supported kinds are `report`, `finding`, `verification`, `compute`, `source`,
`asset` and `receipt`. Each `requires` path must also appear in `retain`. A source
may not be both retained and discarded (paths compare after normalisation), and an
empty `retain` needs at least one `discard` entry. A discard entry is a declaration:
the engine records it and does not check that its path exists or that its reason is
true. Only `source`, `kind`, `requires` and `exception` are stored from a retained
item. Every item is validated and its source hashed before any bytes are copied, so
a validation refusal copies nothing; a failure during a copy (a source that changes
mid-read, a full disk) can still leave a file no index names. `evidence_complete` is the caller's explicit assertion of the
complete evidence closure; the engine cannot infer it from arbitrary prose. Missing,
unreadable, aliased or non-regular evidence blocks sealing. Package caches,
basetemps, build trees and whole-workspace archives are never retained. The older
`retire` list (a superseded log with a reason and a retained replacement) is still
accepted.

```sh
uv run <engine-dir>/session_cleanup.py seal <session> <absolute-manifest>
```

Retained bytes are copied, content-addressed, into the inventory and hash-checked
before cleanup. The seal reports `bytes.retained` (what its items name) and
`bytes.copied` (what it newly wrote; bytes already in this inventory add none, and
items with the same content share one file).
Sealing freezes the inventory; new work uses a new session. Retained bytes are
local: a fresh clone does not contain them.

## Retire retained evidence

Once an exception's deletion condition holds, or for evidence sealed before
exceptions existed, retire it through a preview and an approved apply:

```sh
uv run <engine-dir>/session_cleanup.py retire-evidence <session> [--include <sha256> ...]
uv run <engine-dir>/session_cleanup.py retire-evidence <session> [--include <sha256> ...] --approve <approval-token>
```

The preview writes nothing. It lists `retire`, `kept` with a reason, `missing`,
active users, and `bytes` (`present_before`, `removed`, `present_after`,
`net_change`). An item is eligible once the round that sealed it is removed and its
path gone, or, for the inventory's own seal, once the inventory is complete. These
stay kept unless their bytes are named with `--include <sha256>`:

- an item with an `exception`; the preview shows its `delete_when`;
- a `source` item sealed without an exception, which may be the only copy of
  uncommitted work.

Items with the same content share one file, so `--include` names that file and
retires every item holding it: it asserts the deletion condition of each one, all
of which the preview lists. Bytes shared with a kept item stay, and so does an item
that a kept item `requires`. Each inventory holds its
own copy, so retiring one never touches another's. A retained path outside the
inventory's evidence directory refuses, and an active user of the evidence blocks
the apply. The token binds the stored record and the plan, and is not itself
operator consent. Apply only under operator authorization that names that
inventory's evidence. A standing grant under *Clean up what this session created*
does not cover it.

Apply writes a tombstone on each item (`retired` with the approval) before deleting
its bytes, and keeps the hash, size, kind, source and exception. A plan with
nothing to retire writes nothing. `preview`, `preview --round` (which summarises the
whole inventory), each `list` entry and the `retire-evidence` plan report
`evidence_summary`. Its `items` count index entries and its `bytes` count each stored
file once. Its states are `present`, `retiring` (a
tombstone whose bytes are still there: an interrupted apply, which the next preview
lists again), `retired`, and `missing` (absent with no tombstone, which nothing here
authorized and which still blocks a preview of that seal until the operator
restores the bytes or removes the item from `session.json` by hand: no engine
route clears it), plus an `exceptions`
count of items that carry a retention exception. Historical receipts can
say what existed; they never read a retired item as available or a missing one as
retired.

## Retire each round before the next

A long review loop must not hold every round's trees until the session ends. Once
a round's receipt or findings are recorded and its reviewers and their descendants
have ended, retire that round alone. `--round` takes the round's receipt `id` and
scopes `seal`, `preview` and `apply` to it, without sealing the inventory:

```sh
uv run <engine-dir>/session_cleanup.py seal <session> <absolute-manifest> --round <receipt-id>
uv run <engine-dir>/session_cleanup.py preview <session> --round <receipt-id>
uv run <engine-dir>/session_cleanup.py apply <session> --round <receipt-id> --approve <approval-token> --processes-finished
```

The manifest has the shape described in *Seal: discard by default, retain only by
exception* above, scoped to that round, and each round is sealed once. A round whose
findings are on the PR retains nothing. The preview's token binds that
round's receipt and seal and the inventory's registered writers. The authorization
rules and every guard of *Preview, approve the concrete scope, apply* below apply
unchanged. A retired round records `removed`. The round's approval is persisted only
when its removal is journalled: an interrupted round stays `removing` under that
approval and resumes with the same `apply --round`, and while any round is `removing`,
`track-process` refuses, because that token binds the registered writers. An apply
that stops before removal, on an active user or a refusal, persists nothing: resolve
the cause, preview again and apply with the new token. Each round apply records its
own `last_result` on the round. The inventory reports `complete` while every round is
removed, no round reconcile marked removed has its path back, and it tracks no
worktree, so an inventory used only for rounds needs no final
seal. Tracked worktrees and kept rounds still retire through the inventory's seal,
preview and apply.

## Preview, approve the concrete scope, apply

From the primary checkout, discover inventories and preview the desired session:

```sh
uv run <engine-dir>/session_cleanup.py list
uv run <engine-dir>/session_cleanup.py preview <session>
```

Inspect the exact paths, owner, observed bytes (`null` means unavailable), retained
evidence, active users and keep reasons. Ordinary wrap-up and session-start do not
authorize deletion. Obtain operator authorization covering these concrete paths,
or reuse explicit authorization already covering them, including a standing grant
under *Clean up what this session created* above for paths this session created. The preview's
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
ignored content, including caches: move or remove the ignored files explicitly
before retrying, after retaining through the seal, as an exception, any file a named
unfinished task still needs. A clean Git status alone
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

Once its inventory or round is sealed, a round already recorded `removed` whose
path is gone previews and applies as `absent` without its root being re-checked
(before that, `preview` and `preview --round` refuse with `seal required evidence
before cleanup`): nothing is left to act on, and its root may be gone or recreated
(a wiped temp directory, or a reconciled device number). A round reconcile marked
removed whose path has reappeared, such as on a remounted scratch volume, previews
and applies as `kept`, and no removal is attempted: it is no longer managed here, so
inspect and remove it by hand. Every other round keeps its root and identity checks,
including a removed round whose path has reappeared.

Exit status is `0` for completed cleanup, `1` for kept/active/native-archive work,
and `2` for refusal or unavailable prerequisites. Keep reasons mean incomplete
cleanup, not success. Inspect the final `last_result` in the durable index (on the
round's entry for a round retired with `--round`), recheck
retained hashes, and report residual paths and the next supported action. Applying
an already completed inventory is a no-op while its paths remain absent. Never
broaden roots, weaken dependencies or use a general age sweep to clear a refusal.
