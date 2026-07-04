> **v0 kit status — engine not yet vendored.** This skill documents the *doctrine* and the
> intended two-session (draft → operator approval → finalize) mechanism, but its
> deterministic engine — the parse/draft/finalize scripts and pipeline config it references
> (`scripts/…`, `config/…`) — is **not shipped in kit v0** (they depend on a tracker client,
> a notify channel, and a state-machine that are project-specific). Until a later kit revision
> vendors them, either wire your own engine against this prose or run the skill in a lighter
> LLM-only mode. The four fully-wired skills (`session-start`, `wrap-up`, `parallel`,
> `pr-watch`) ship their engines and work out of the box.

Triage the `docs/friction-log.md` inbox: turn the current un-graduated inbox entries
(everything not yet swept to the archive) into LLM-drafted tracker-issue payloads, DM
the operator a numbered approval list, then file the approved ones in your tracker
(project `tracker.project_name`) and open a draft PR prepending a new graduation
header to the source markdown.

- **Session A (draft):** parse → LLM-draft proposals → DM operator numbered list →
  save state → end
- **Session B (finalize, a later scheduled run OR a manual `resume`):** read DM
  thread → parse approve/skip/modify grammar → file tracker issues → prepend
  graduation marker + sweep the graduated inbox into the archive + open draft PR →
  delete state. If run on a schedule and the operator hasn't replied yet, Session B
  posts a "still waiting" reminder and exits 0 with state intact for the next sweep or
  manual run.

> **Execution-context rules — read before starting.**
>
> - **Non-interactive runs never pause for input.** This skill is designed to be
>   fired by a scheduler (a cron/CI runner invoking your agent non-interactively).
>   There is no operator to answer mid-run. If a required config is missing or a
>   required tool/MCP is down, stop with a clear error so your runner's failure-alert
>   path surfaces it; do not wait for input that will never arrive.
> - **The skill never edits your tracker or `docs/friction-log.md` in Session A.**
>   Session A is read-and-DM only. The actual writes happen in Session B, after the
>   operator's DM reply.
> - **Test mode is signalled explicitly.** This run is in test mode if, and only if,
>   (a) the invocation contained the `test` keyword, or (b) the loaded state file has
>   `"test_mode": true`. Nothing else counts (worktree path, branch name, etc.).
>
> **Shared primitives used by this skill:**
>
> - your pipeline-state helper — state persistence following the shared
>   dated-state-file pattern (Principle #9 in `PRINCIPLES.md`); the same shape a
>   release-review pipeline would use.
> - an approval-keyword / cancel-keyword detector over the DM thread text.
> - `scripts/triage_friction_log.py` — parser + LLM proposer + report writer.
> - `scripts/finalize_triage.py` — graduation-marker prepend + inbox-sweep-by-
>   frozen-list into the archive (`--frozen-inbox`) + branch/commit/push/draft-PR
>   (Session B only).
> - your tracker's client library or MCP — for filing approved proposals.
> - your notify library / MCP — synchronous DM to the operator.

______________________________________________________________________

## Entry points

| Input    | Behavior                                                                           |
| -------- | ----------------------------------------------------------------------------------- |
| *(none)* | **Auto-detect:** if state file exists, resume Session B; otherwise start Session A |
| `resume` | Session B — explicitly load state                                                  |
| `new`    | Session A — force a new run even if state file exists (overwrites state)           |
| `test`   | Session A in **test mode** — uses test-mode overlay (see Configuration)            |

______________________________________________________________________

## Configuration

Read a dedicated pipeline config file (e.g. `config/friction-triage.yaml`) at the
start of every run. Never hardcode channel names, user IDs, tracker IDs, or branch
patterns — always read from config.

| Key                       | Description                                                                          |
| ------------------------- | ------------------------------------------------------------------------------------- |
| `notify_user_key`         | Key under your notify config for the operator DM target                              |
| `state_path`              | Repo-root-relative path for the pipeline's state file                                |
| `source_path`             | Path to `docs/friction-log.md`                                                       |
| `report_pattern`          | Output pattern for the parser's report (e.g. `reports/triage_{date}.md`)             |
| `tracker.team_id`         | Tracker team id (Linear-shaped backends) — leave blank for others                    |
| `tracker.project_id`      | Tracker project id — should match `config/dev-model.yaml → tracker.project_name`      |
| `tracker.label_name`      | Label applied to every triage-filed ticket                                          |
| `approval_keywords`       | Bulk-approve keywords — default keywords come from your shared approval helper       |
| `cancel_keywords`         | Bulk-cancel keywords                                                                  |
| `finalize.branch_pattern` | Branch name format (default `chore/triage-{date}`, `vcs.triage_branch_pattern`)       |
| `finalize.commit_subject` | Commit-message subject template                                                      |
| `finalize.pr_draft`       | Open the PR as a draft on first push (default `true`)                                |

______________________________________________________________________

## Pre-flight check

```
Config:           [✓ loaded | ✗ friction-triage config not found]
Source file:      [✓ docs/friction-log.md found | ✗ missing]
Tracker credential: [✓ present | ✗ missing — required for Session B]
Notify channel:   [✓ available | ✗ not configured]
State file:       [✓ found — resume Session B | — no active session]
```

- Tracker credential missing **and** entering Session B → stop with a clear error.
  (For Session A only, a missing credential is a warning — the LLM draft can still
  run; the operator just won't be able to finalize until they provision it.)
- Notify channel unavailable → stop in both sessions. The DM is load-bearing for the
  review loop.
- State file found + no args → auto-resume Session B. Use `new` to force a new
  Session A.
- **Scheduler state guard (automated mode only):** when running as a scheduled
  automation, if the state file exists, skip the run entirely. Log: `"Skipping
  scheduled draft — active triage session already in flight (state file present).
  Resume or cancel via /triage-friction-log resume."` Exit 0 (not an error). This
  prevents a scheduled run from overwriting an in-progress review cycle.

______________________________________________________________________

## Session A — Step by step

### Step 1: Run the parser + LLM proposer

Invoke `scripts/triage_friction_log.py`. It walks `docs/friction-log.md` and treats
**every entry still in the active inbox** as a candidate — candidacy is
presence-based, not date-based: `finalize_triage.py` sweeps graduated entries out to
the archive, so whatever remains is by construction the un-graduated set. It excludes
only the graduation marker(s) and entries already tagged with a tracker identifier. It
drafts a tracker-issue payload per actionable item via your default-tier model, writes
the result to `reports/triage_<today>.md`, and **also writes a frozen-inbox
snapshot** — the raw inbox text (everything below the H1 + intro) exactly as it stood
at this moment — to `state/triage/frozen-inbox_<today>.json`:

```bash
uv run scripts/triage_friction_log.py
```

Capture the script's stderr log lines for the operator DM (the graduation-marker date
it logs — informational, not a cutoff — candidate count, drafted-proposal count, any
truncation warnings, and the snapshot path it logs). Do not skip the LLM drafting step
in production — a no-LLM debug mode should dump only the candidate JSON (the snapshot
is still written either way).

**If the parser exits non-zero:** stop. The exit message is usually a missing
graduation marker (e.g. a brand-new file that has never been through a migration
sweep — the parser refuses rather than proposing every entry) — surface it in the
failure DM. No snapshot is written on this path either (it aborts before reaching that
step).

**If candidate count is 0:** the parser writes no report (but does still write the
snapshot) and exits 0. DM the operator a one-liner ("No un-graduated entries to
triage; the inbox holds only the graduation marker.") and exit clean without creating
state. There's nothing for Session B to do.

### Step 2: Resolve the DM target

Read your notify config for the operator's DM identifier (`notify_user_key` from
Step-0 config, resolved against `config/dev-model.yaml → notify.user_key`). If
missing, stop with: `"Config error: friction-triage config → notify_user_key resolved
to no id. Set the corresponding key in your notify config."`

Store the resolved user identifier as `notify_user_id` in state — it's also the value
you pass to Step 3's DM-send call (most chat APIs auto-open / reuse the DM with that
user). The actual DM-channel identifier is **not** always the same as the user
identifier — it comes back in Step 3's response and gets stored separately as
`channel_id` for Session B's thread-read call.

### Step 3: Post the numbered proposal DM

The DM is the operator's primary review surface. The report file is a fallback /
persistent artifact.

Format:

```text
:clipboard: *Triage — friction-log graduation candidates*

[N] proposals drafted from the current un-graduated inbox.
Source: [reports/triage_<today>.md] (also pushed in next branch).

*1.* `[label1, label2, …]` — *[title 1]*
> [first ~60 chars of body … truncated with `…` if longer]

*2.* `[label1, label2, …]` — *[title 2]*
> [first ~60 chars of body]

…

*Reply in this thread* to approve / skip / modify. Grammar:
• `1,3,5 approve`  — approve items 1, 3, 5 verbatim
• `2 skip`          — skip item 2 (drop, don't file)
• `4 modify: <text>` — file item 4 but with this body instead of the proposed one
• `lgtm` / `approve all` — approve all remaining items
• `cancel` / `skip`     — abort the whole batch (no tickets filed)

When done, run `/triage-friction-log resume` from your agent session.
```

Chunk long messages per your notify config's message-size limit. For >8 proposals,
post the header + items 1-8 as the top-level message, then thread-reply with items 9+
in batches. Approval grammar references stay in the top-level message so the operator
always sees them first.

### Step 4: Save state

Write to the path from your friction-triage config's `state_path` (default
`state/triage/triage-pipeline-state.json`). Create the parent directory if it doesn't
exist.

`channel_id` is the **DM-channel identifier** returned by Step 3's send call, NOT the
operator's user identifier — Session B's thread-read call rejects a user id where it
expects a channel id. `notify_user_id` stays as the user identifier for the approval
detector to match message authors against.

```json
{
  "phase": "awaiting-approval",
  "file_path": "reports/triage_<today>.md",
  "channel_id": "...",
  "thread_ts": "...",
  "approver_user_ids": ["..."],
  "notify_user_id": "...",
  "round": 1,
  "posted_at": "ISO-8601",
  "extra": {
    "cutoff_date": "YYYY-MM-DD",
    "report_path": "reports/triage_<today>.md",
    "frozen_inbox_path": "state/triage/frozen-inbox_<today>.json",
    "proposals": [
      {
        "candidate_id": "...",
        "title": "...",
        "body": "...",
        "labels": ["area:...", "type:bug", "priority:p2"]
      },
      ...
    ],
    "test_mode": false
  }
}
```

The `proposals` list under `extra` is the full LLM output verbatim — Session B
replays it against the operator's DM grammar without re-running the parser. This is
intentional: re-running between the two sessions could produce different proposals
(LLM drift, new entries added meanwhile), and we want the operator's approval to bind
to exactly what they saw.

`cutoff_date` is the most-recent graduation-marker date the parser logged —
**informational only** (it appears in the DM header and report). Candidacy is
presence-based, not gated on it: the parser proposes every un-graduated entry
regardless of date, so a friction entry dated the same day as (or older than) the
marker is no longer silently dropped.

`frozen_inbox_path` is the path Step 1 logged when it wrote the frozen-inbox
snapshot — the raw inbox text (everything below the H1 + intro) exactly as it stood
when Session A drafted. Session B passes this straight through to
`finalize_triage.py --frozen-inbox` (Step 5) so the sweep only archives entries that
existed at draft time; anything a human or another session adds to
`docs/friction-log.md` between Session A and Session B stays in the active file
instead of being silently archived unfiled. State written by an older skill version
(no `frozen_inbox_path` field) still resumes fine — Session B falls back to the
whole-inbox sweep in that case (see Step 5).

**End Session A.** Output:

```text
Session A complete.
[N] proposals drafted; DM posted to [user].
Resume with /triage-friction-log resume after replying.
```

______________________________________________________________________

## Session B — Step by step

### Step 1: Load state

Read the state file from your friction-triage config's `state_path`. If absent: stop
with `"No active session found. Start a new run with /triage-friction-log."`

### Step 2: Read the DM thread

Use your notify tool's thread-read call with `channel_id` + `thread_ts` from state.
Collect all replies since `posted_at`.

If the only replies are from the bot itself or there are no replies at all, DM the
operator:

```text
:hourglass: Triage batch awaiting approval. No reply detected in the DM thread.
Reply with approve/skip/modify per the grammar in the original message, then re-run `/triage-friction-log resume`.
```

Then exit 0 with state intact.

### Step 3: Parse the operator's reply grammar

Walk all replies from `approver_user_ids` (effectively `[notify_user_id]` for this
skill) in chronological order. For each reply, parse against this grammar:

- **Bulk cancel** — message text contains `cancel` (whole word) or `skip` (alone, not
  followed by numbers). → Abort entire batch. Skip to Step 6 (cleanup).
- **Bulk approve** — message text contains `lgtm`, `approve all`, or `ship it`. → Mark
  every proposal currently in `extra.proposals` as approved with no modifications.
- **Per-item approve** — `<numbers> approve` where `<numbers>` is a comma-separated
  list (e.g. `1,3,5 approve`). Bare numbers without the `approve` verb (e.g. `1,3,5`)
  also count as approve — the common operator shorthand.
- **Per-item skip** — `<numbers> skip` or `skip <numbers>`.
- **Per-item modify** — `<n> modify: <free text>` or `modify <n> <free text>`.
  Replaces the proposal's `body` (markdown) with the free text. Title and labels stay
  as drafted.

Build a final decision per proposal: `approve` (file as-is), `approve_modified` (file
with replacement body), or `skip` (don't file). Default for proposals the operator
didn't mention is **skip** — they have to explicitly approve. Explicit-opt-in is
safer than batched-approve-by-default; if the operator wants everything, they have the
`lgtm` shortcut.

Log the decision table to stderr for traceability.

### Step 4: File approved tickets via your tracker

For each `approve` / `approve_modified` proposal, file it through your tracker client
(a client library call, or your tracker's issue-create tool via MCP). If your MCP
route doesn't accept a pre-resolved label-id list (which matters for atomicity), a
small direct client-library call may be a better fit than the MCP route — document
whichever your project uses.

Resolve `team`/`project` from config (`tracker.team_id` → `tracker.project_name`,
always — this project's fixed default per your own config convention), `title` +
`description` from the proposal (modified body for `approve_modified`), `labels` from
the LLM's proposed labels. Don't force-apply the pipeline's own `tracker.label_name`
from config here unless your MCP wrapper pre-resolves labels reliably — apply it
out-of-band via a comment/label-update call if needed; the per-proposal labels already
give reasonable area/type/priority filterability.

For each successful create, capture `{identifier, url, title}` from the response.

**If any create fails:** log the error, continue with the rest. Do not abort the
whole batch on one failure — the operator can re-run with `new` against the trimmed
list later. At the end, if any creates failed, include them in the failure-DM tail.

### Step 5: Run scripts/finalize_triage.py

Once at least one ticket has been filed successfully, invoke the finalize helper to
prepend a graduation marker to `docs/friction-log.md`, **sweep the graduated
(frozen-at-draft-time) inbox into `docs/friction-log-archive.md`**, commit both edits
on a fresh branch off the protected branch's origin ref, push, and open a draft PR.

Pass the filed tickets via stdin as JSON, and pass `--frozen-inbox` pointing at the
snapshot path from state's `extra.frozen_inbox_path` (Step 4):

```bash
uv run scripts/finalize_triage.py --frozen-inbox state/triage/frozen-inbox_<today>.json < /tmp/filed-tickets.json
```

…where `/tmp/filed-tickets.json` is the list of `{identifier, url, title}` records
gathered in Step 4. The script:

1. Computes a compact identifier-range summary from the filed identifiers if your
   tracker uses sequential numeric ids (e.g. `PROJ-N..M, PROJ-K`); otherwise lists
   them individually.
1. **Diffs the frozen-inbox snapshot against the current inbox** (everything below
   the H1 + intro), splitting both into heading-anchored, fence-aware entry blocks.
   Matching is **exact-content**: a current block that is byte-identical to a
   snapshot block existed when Session A drafted → **swept** into a new `## Graduated
   YYYY-MM-DD — <tracker> (<range>)` section in `docs/friction-log-archive.md`,
   verbatim with headings demoted one level (the prior graduation marker and any
   entry present at draft — including LLM-skipped or already-tagged ones — go here).
   Every other current block is **kept**, verbatim, in the active file: entries
   *added* during the Session A → Session B window, and — deliberately, the safe
   direction — any entry *edited in place* since the snapshot (an "Update:" note). A
   kept-because-edited entry is simply re-proposed next pass (a duplicate the
   operator skips); no block is ever swept unless it byte-matches a Session-A block,
   so an untriaged entry can never be archived unfiled.
1. Rewrites `docs/friction-log.md` as the H1 + intro + the new `## YYYY-MM-DD —
   Backlog migrated to <tracker> (<range>)` marker + any window-added entries kept per
   the point above, so the active file never accumulates *triaged* post-mortems below
   the marker, while never silently dropping *untriaged* ones either. (If the archive
   file is missing it falls back to the legacy keep-everything-inline prepend and
   warns, ignoring `--frozen-inbox` entirely — there's no sweep to narrow in that
   path.)
1. Creates a branch per `vcs.triage_branch_pattern` (`chore/triage-YYYY-MM-DD`) off
   the protected branch's origin ref.
1. Commits **both** doc edits (no other paths).
1. Pushes the branch.
1. Opens a draft PR.

It prints a JSON summary to stdout with `branch`, `commit_subject`, `header_line`,
`ticket_range`, `pr_url`, `filed_count`. Capture this for the success DM.

**If the script fails:** the tickets are still filed in your tracker (Step 4
succeeded), but the doc edits are uncommitted. Log the failure, leave the edits on
disk for the operator to commit manually, and surface the error in the DM. **Do not
delete state** — the operator may want to re-run just the finalize step after
resolving the git/PR issue.

**Fallbacks (both fail toward *no data loss*, never a hard stop — a finalize whose
tickets are already filed must never abort over a local snapshot file):**

- **`--frozen-inbox` omitted entirely** (an older session with no
  `extra.frozen_inbox_path`): the script sweeps the *whole* current inbox, same as
  before this feature — the operator explicitly opted out of window protection.
- **`--frozen-inbox` provided but the snapshot is missing/malformed:** the script
  **fails toward keep** — it keeps *every* entry inline (archives nothing) and warns,
  rather than whole-sweeping and risking loss of a window-added entry. The active
  file isn't trimmed this pass and entries are re-proposed next run (a duplicate the
  operator skips), but nothing is lost. Restore the snapshot to trim cleanly.

> **Why this matters.** A naive finalize that sweeps the *whole* active inbox lets a
> friction entry added *between* Session A's draft and this finalize get archived
> without ever being a tracker candidate — silent, undetected data loss. Diffing
> against the frozen-inbox snapshot Step 1 wrote at draft time closes that gap:
> window-added entries are recognized as new and stay in the active file, below the
> new marker, ready for the *next* triage pass instead of being lost in the archive.
> A multi-hour gap between draft and finalize sessions is the common case this
> closes.

### Step 6: Confirm + clean up

DM the operator:

```text
:white_check_mark: *Triage complete.*
[N] tickets filed in [tracker project]:
• <url|identifier> — fix X
• <url|identifier> — fix Y
…

Source doc updated on draft PR: <pr_url|chore/triage-YYYY-MM-DD>
```

If any creates failed in Step 4, list them with their error in a separate thread
reply.

Delete the state file. The `reports/triage_<today>.md` report is kept (git-tracked
alongside other reports, no automatic cleanup).

**End Session B.** Output:

```text
Pipeline complete.
• Filed: [N] tickets
• Source doc PR: [pr_url]
• Branch: chore/triage-YYYY-MM-DD
```

______________________________________________________________________

## Error handling

| Situation                                    | Action                                                                                                       |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Parser exits non-zero in Session A            | Stop. Surface stderr tail in failure DM. Do not create state.                                                  |
| Zero candidates                               | DM "nothing to triage" + exit clean. No state.                                                                 |
| Notify channel unavailable                    | Stop. The DM is load-bearing.                                                                                  |
| Tracker credential missing in Session B       | Stop with explicit "set the tracker credential in your secrets store". State preserved for re-run after fix. |
| Operator DM has no reply                      | DM reminder + exit 0 with state intact. The next scheduled sweep OR a manual resume picks it back up.        |
| Operator DM has `cancel` / `skip`             | Delete state, DM "Triage cancelled — no tickets filed.", exit 0.                                              |
| Tracker create fails for some proposals       | Continue with the rest. Surface failures in the final DM tail. Don't abort.                                   |
| `finalize_triage.py` fails                    | Tickets are still filed. Leave file edit on disk, DM the error, keep state for retry.                          |
| State file corrupted                          | Stop. Show contents. Ask operator how to proceed (next session).                                               |

______________________________________________________________________

## Test mode

`test` keyword in the invocation activates a lighter-weight overlay:

- The notify target is unchanged (the operator still gets the DM, just from a test
  run)
- Tracker ids/labels are unchanged — but the skill **never files tickets** in test
  mode. The proposals are surfaced in the DM with a `*[TEST]*` prefix on the header
  line, and Step 4 logs "would have filed: …" instead of actually filing.
- `finalize_triage.py` is invoked with `--dry-run`, so the doc edit lands on disk for
  inspection but no branch/commit/push/PR happens.
- The state file is written with `"test_mode": true` so `resume` keeps the overlay
  active.

The point is to exercise the parser → DM → operator-reply parsing path without
spending tracker writes or opening throwaway PRs.
