# Triage friction log — tracker writes and finalize

Read this file completely, together with
[`triage-friction-log.md`](../triage-friction-log.md) and its other reference files,
before the first action of any run. It is part of that workflow and as normative as it;
a section cited by name, or as *above* or *below*, may sit in that file or another of
its reference files.

## Contents

- Tracker writes and accounting
- Finalize and sweep

## Tracker writes and accounting

Trigger tracker access only for approved items. Recompute the payload digest and compare
it with the approval record before any tracker action. Search for the exact idempotency
marker and record the complete pre-existing match set. One authoritative pre-existing
exact payload match records `verified` with its read-back identifier without a create.
Any multiple or non-exact marker match is ambiguous and stops operator-held. Only an
authoritative empty match set permits persisting `attempting` and calling create. After a
success response, read back the item and require an exact tracker match, as the
`tracker-write` state defines it, on project, title, body, labels, marker, and returned
identifier before recording `verified`.

If the create fails or returns ambiguously, read back by the exact marker before any
retry. One exact payload match verifies the write. No match proves no landing only when
the tracker read is complete and authoritative; multiple or non-exact matches remain
ambiguous. Preserve state and stop operator-held. Continue to later creates only after
the current item is verified; never turn a partially attempted batch into an archive
sweep. Every approved proposal must be verified or the batch remains held.

Test mode performs the readiness and approval checks but never calls a tracker create,
update, or comment operation. It records `would-create` in test state and report; that
record is not live approval and cannot be resumed as live.

## Finalize and sweep

Finalize only after every approved tracker payload is verified. The sweep set is the
union of verified-filed items and items explicitly decided `archive`. Parked,
unmentioned, canceled, failed, ambiguous, and window-added items are never in that set.
Re-read the current inbox and require every proposed sweep block to be byte-identical to
its frozen block. An edited approved block is operator-held; do not archive a stale
snapshot or widen to the whole inbox. Window-added blocks stay active verbatim.

Write the graduation-marker heading with a record block under it, from this run's own
state and nothing else: the engine mode, one line per filed issue link and per archived
candidate naming the source entry it came from (candidate id, the entry's date heading
and its bold lead), and the verbatim approval command with its approver, one span per
command line. The engine's state and
report are not committed, so the record is the only account of what the sweep did that
the repository keeps. It is not what keeps the marker: that is the title recognizer
below, which keeps a bare marker too. State-derived free text (an approval command, an
operator identity) goes through the same literal-content rule as report rendering, so it
can never open a heading or entry line of its own; so do a source entry's date heading
and lead. Recognise a graduation marker by the
same substring the draft session already excludes candidates on — never a second,
independently maintained pattern — and never delete one as an empty section, including
when it is the file's last section. Instead, before writing its own marker, move every
earlier graduation-marker section (its heading through to the next heading outside code)
to the archive unchanged, in file order and ahead of the swept blocks, so the inbox keeps
only this sweep's marker and each sweep leaves the file no longer than the entries it
kept. A marker-titled section that holds an entry line is not a marker record and stays,
as do parked entries' dated sections. When a sweep removes every entry of a dated
section, the prose between its heading and its first entry goes to the archive with
them, directly under the same heading and ahead of any entry already archived there,
and the section leaves the inbox; a section that keeps an entry keeps its prose. When
removing a dated section that genuinely is empty, also remove the blank line that separated it from whatever precedes it if nothing
follows: otherwise an emptied trailing section leaves a blank line at EOF. In the archive,
swept blocks whose date heading the archive already has join the last section with that
exact heading (outside fenced code) instead of repeating it; others go in a new section
appended at the end, with a blank line before its heading. Either way the archive ends in
exactly one newline.

Commit validation, which re-renders a retained sweep commit from state, also accepts the
four renderings older engines committed: the one that left an emptied section's intro in
the inbox, the one that also left earlier markers in the inbox,
the one before source entries (lists of issue
links and candidate ids, each swept date group appended under its own heading, the last
block's trailing blank line kept), and the one before the marker record existed (a bare
marker, a bare marker treated as an empty section, and no separator management). A
completed or in-flight state that such an engine committed must stay valid after an
upgrade. New sweeps are never rendered those ways, and a commit matching none of the
renderings is operator-held.

Test mode stops after rendering the proposed diff in the report. Render that diff by the
same literal-content rule. It does not edit
`<friction-log>` or `<friction-log-archive>` on disk and does not create a branch,
commit, push, or pull request.

In engine-backed mode invoke `triage.finalize_engine` only if it accepts the exact
accounted block set and implements this declaration; an older helper that whole-sweeps
the frozen snapshot is not ready. In LLM-only mode perform the same exact-content
transformation and label it `agent-executed`.

Before each branch, commit, push, pull-request, `pr-watch`, or merge-read-back action,
append its exact intent and persist the `forge-finalize` operation and first attempt at
`attempting`; a permitted retry appends another attempt to that same logical operation;
never infer safety from a missing response. After each action, independently read back
the declared repository/PR facts and persist the status-specific evidence before
beginning the next operation. Build each next intent from that verified read-back, not
from the preceding response or from identifiers retained in memory: commit read-back
supplies push's commit and tree, push read-back supplies pull-request creation's remote
head and tree, pull-request read-back supplies `pr-watch`'s PR identity and observed
head, and verified `pr-watch` supplies archive-sweep and merge-read-back identity, head,
and receipt. Reject a locally valid later record when any consumed identifier differs
from its predecessor's verified observation. Never switch the caller checkout. Fetch the protected branch, create a fresh isolated
worktree and `<triage-branch>` from its current origin ref, and re-read the destination
documents there. Require the current origin ref to descend from the immutable draft
head, persist it as `finalize_base_head`, and never rewrite the draft run identity. A
permitted fast-forward advance still must pass the byte-identical frozen-block check;
otherwise remain operator-held. Require a clean index, stage only `<friction-log>` and
`<friction-log-archive>`, and prove the staged path set equals that pair exactly. Commit
with `triage.commit_subject`, push, and create the pull request ready for review by
binding the validated `false` `triage.pr_draft` directly. Immediately run the native
`pr-watch --assert-ready` correction, then read back repository, base, branch, commit,
head, draft bit, PR URL, and changed paths, and require the read-back draft bit to be
`false` before the normal `pr-watch` loop. A failed assertion or a failed, ambiguous, or
draft response triggers read-back before retry and otherwise remains operator-held.
A failed `branch-create` is local. It often leaves nothing (a same-day branch-name
collision is refused before any write), but git can create the branch ref before it fails
to create the worktree, so a resume verifies rather than assumes. It is the one failed
operation a later finalization resume retries: only when it is the sole recorded
operation, only after the provider reads back that the local branch, the worktree path,
and a remote branch of that name are all absent, and only by appending another attempt
with the same intent. Any of them present keeps it operator-held.

Run `pr-watch` for the exact head and persist an `unsettled` review observation whenever
it has not reached terminal exact-head evidence. This workflow never merges the sweep pull request.
When `pr-watch` reports terminal exact-head review evidence, authoritatively read back
the PR and require its current base branch to remain the configured protected branch and
its current `headRefOid` to equal the head in that evidence. Before
allowing merge, atomically persist that head as
`reviewed_head` with the PR-watch receipt. Any later head movement invalidates the
receipt and remains terminally operator-held in this run; this schema never replaces
`reviewed_head` or invents a second review cycle from a later head.
When review is unsettled or the operator still owns the merge decision, report
`operator-held` with the PR URL and `observed_pr_head`; name `reviewed_head` only when a
retained terminal receipt establishes it. If terminal evidence exists but PR read-back
is unavailable or mismatched, remain operator-held without changing `reviewed_head`.
On a later resume, digest-check the `archive-sweep` state and atomically return to
`forge-finalize` by dropping only the derived `archive_sweep` summary while retaining
its complete verified tracker, repository, PR-creation, and PR-watch operation evidence.
Append `merge-read-back` there without issuing a merge. After verified read-back,
rederive the byte-identical archive summary for completion. The authoritative PR
read-back must prove that the pull request still names that same base, that it merged,
and that its final `headRefOid`
equals `reviewed_head` recorded in state, and the retained terminal PR-watch receipt
must still bind that same head. A missing or mismatched final head or receipt is
operator-held; an authoritative matching `merged: false` read-back is retained as an
unsettled attempt and permits a later read-back attempt without issuing a merge or
discarding the observation; never mark an unreviewed replacement head complete. Only then
retire this sweep's own artifacts and write completion to the report and state; the next
session-starting run retires that state; the completed report remains durable. A resume
that finds a verified `merge-read-back` already persisted as the last operation with no
completion written — a run that stopped between those two writes — revalidates that
recorded read-back and completes from it, without issuing another.

Before writing completion, retire the sweep's own worktree, local branch, and remote
branch — each guarded and idempotent. Each result is `removed` or `absent` with no reason,
or `kept` with a non-empty reason: the worktree recorded in the branch-create intent only when it is clean
(`git worktree remove` without `--force`; the caller-checkout conflict guard applies, so
the caller's own checkout is never removed); the local branch only with a safe delete (`git branch -d`, never
`-D`); the remote branch only when its head still equals the exact commit this run pushed
(a compare-and-delete, so a later push by someone else is never deleted). A cleanup
failure never withholds completion: record what each guard found and complete anyway. A
provider answer whose status is not `verified` records every artifact `kept`, whatever
its record says. The
results live in `completion.sweep_cleanup`, outside `receipt_core`, so a completed state
written before this field existed still validates without it, and the field is absent
whenever it was never computed. Re-running cleanup after a partial prior attempt reads an
already-removed artifact back as `absent` rather than failing.
