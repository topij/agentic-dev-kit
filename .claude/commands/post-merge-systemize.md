> **v0 kit status — engine not yet vendored.** This skill documents the *doctrine* and the
> pattern-finding pipeline, but its deterministic engine — the merged-PR fetch/digest scripts
> and pipeline config it references (`scripts/…`, `config/…`) — is **not shipped in kit v0**
> (they depend on a forge/PR client and a tracker client that are project-specific). Until a
> later kit revision vendors them, either wire your own engine against this prose or run the
> skill in a lighter LLM-only mode. The four fully-wired skills (`session-start`, `wrap-up`,
> `parallel`, `pr-watch`) ship their engines and work out of the box.

Weekly pattern-finding across the last 7 days of merged PRs: read each PR's review
comments (review bots, an operator review pass, human) + originating tracker tickets,
then ask **"what pattern shows up in ≥2 PRs this week that a CLAUDE.md rule,
skill-prompt, or config change would have prevented?"** Route findings: ≥2-PR patterns
→ a small draft CLAUDE.md/skill PR; single-incident → a `docs/friction-log.md`
append; single-incident-but-high-severity → a tracker ticket. No pattern → a one-line
status DM and exit. The pattern-finding half of the friction flywheel (Principle #2 in
`PRINCIPLES.md`).

> **The cardinal discipline: NO retro-policing.** A normal week produces a "no
> patterns" DM, *not* a CLAUDE.md edit. Per-PR or single-incident findings do **not**
> graduate to always-loaded prompt rules — they go to the friction-log inbox (or the
> tracker if high-severity). Only a pattern spanning **≥2 distinct PRs** (the
> `pattern_threshold`) earns a rule edit. Bikeshedding CLAUDE.md weekly is the
> explicit failure mode this skill must avoid. When in doubt, route *down* (inbox),
> not *up* (rule).

> **Execution-context rules — read before starting.**
>
> - **Non-interactive runs never pause for input.** This skill is designed to be
>   fired by a scheduler (a cron/CI runner invoking your agent non-interactively).
>   There is no operator to answer mid-run. If a required config is missing or a
>   required tool is down, stop with a clear error so your runner's failure-alert path
>   surfaces it; never wait for input that will never arrive.
> - **Single-session.** Unlike `/triage-friction-log`, there is no DM approval
>   round-trip. The draft PR *is* the review surface — the operator reviews and
>   merges (or closes) it via your forge. The skill never blocks on approval.
> - **Test mode is signalled explicitly.** This run is in test mode if, and only if,
>   the invocation contained the `test` keyword. Nothing else counts (worktree path,
>   branch name, etc.). In test mode the skill writes no PR, no tracker ticket, and no
>   inbox edit — it DMs the proposed routing with a `*[TEST]*` prefix.
> - **Skill-bash rules.** `working_dir` is the repo root, so `scripts/X.py` paths
>   resolve directly (`uv run scripts/fetch_merged_prs.py`). Avoid Bash parameter
>   expansion in generated commands if your harness rejects it — substitute literal
>   values at emit time instead. Branch off the protected branch's origin ref
>   explicitly so the worktree base never leaks into the PR.

**Shared primitives used by this skill:**

- `scripts/fetch_merged_prs.py` — deterministic forge-API-based fetcher →
  `state/cache/merged-prs_<date>.json`. The skill never re-derives PR data itself.
- `scripts/digest_merged_prs.py` — deterministic slimmer →
  `state/cache/merged-prs-digest_<date>.json`. Strips the raw bundle to just the
  actionable review findings (~20x smaller) with `severity`/`resolved`/
  `cites_guideline` per finding. **The skill reads this digest for Step 2, never the
  raw bundle** — that is what keeps the run inside a scheduler's timeout (reasoning
  over the full raw bundle is what times a naive version of this job out).
- `scripts/heartbeat_cli.py` — step-boundary heartbeats so a timeout DM shows where
  the run died. Have your job scheduler/config mark this job as heartbeat-emitting.
- your notify library / MCP — the status / summary DM.
- your tracker's issue-create tool — single-incident-high-severity ticket filing
  (project `tracker.project_name`).

______________________________________________________________________

## Entry points

| Input      | Behavior                                                                                                                 |
| ---------- | ------------------------------------------------------------------------------------------------------------------------ |
| *(none)*   | Weekly run — `lookback_days` (7) window ending now.                                                                      |
| `backfill` | One-time bootstrap — 28-day window (a "run on the last 4 weeks" exit criterion). Otherwise identical.                    |
| `test`     | Weekly window in **test mode** — analyse + DM the proposed routing, but write nothing (no PR, no ticket, no inbox edit). |

______________________________________________________________________

## Configuration

Read a dedicated pipeline config file (e.g. `config/post-merge-systemize.yaml`) at
the start of every run. Never hardcode channel names, user IDs, tracker IDs, branch
patterns, or the pattern threshold — always read from config.

| Key                                                    | Description                                                                            |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `notify_user_key`                                       | Key under your notify config for the DM target.                                        |
| `lookback_days`                                         | Weekly window size (7). `backfill` overrides to 28.                                     |
| `pattern_threshold`                                     | Minimum distinct PRs a finding must span to graduate to a rule edit (2).                |
| `cache_pattern`                                         | Output pattern for the fetcher bundle.                                                  |
| `digest_cache_pattern`                                  | Output pattern for the slim digest the skill actually analyses.                         |
| `batch_size`                                            | PRs per batch when map-reducing a large week (25).                                       |
| `single_pass_max_prs`                                   | At/below this many finding-bearing PRs → cluster in one pass; above → map-reduce (60).  |
| `github_repo` (or your forge's equivalent)              | `owner/name`; empty → infer from cwd.                                                   |
| `review_sources` / `operator_login`                     | Comment-source classification (consumed by the fetcher).                                |
| `friction_log_path`                                     | Where single-incident findings land (`docs/friction-log.md`).                           |
| `tracker.team_id` / `tracker.project_id` / `tracker.label_name` | Config for high-severity single-incident tickets — `tracker.project_id` should match `config/dev-model.yaml → tracker.project_name`. |
| `finalize.branch_pattern` / `commit_subject` / `pr_draft` | The ≥2-PR-pattern CLAUDE.md/skill-prompt PR (`vcs.systemize_branch_pattern`).           |

______________________________________________________________________

## Pre-flight check

```
Config:            [✓ loaded | ✗ post-merge-systemize config not found]
Forge auth:        [✓ authenticated | ✗ not logged in — required]
Notify channel:    [✓ available | ✗ not configured]
Tracker (optional): [✓ available | ⚠ unavailable — high-severity tickets skipped, noted in DM]
```

- Forge (`gh` or equivalent) unauthenticated → stop. The whole skill is downstream of
  the PR fetch.
- Notify channel unavailable → stop. The status DM is the load-bearing output on
  no-pattern weeks.
- Tracker unavailable → continue degraded: high-severity single-incident findings
  fall back to a `friction-log.md` append with a `**File as tracker ticket:**` prefix,
  and the DM notes the gap.

______________________________________________________________________

## Step 1 — Fetch + digest the week's merged PRs

**MANDATORY first action — run this `heartbeat_cli.py start` call before any other
Step 1 work.** The wrapper's opening tick may read a placeholder "launching" step;
that is not the skill's own start.

```bash
uv run scripts/heartbeat_cli.py start --job post-merge-systemize --step step-1-fetch
```

Run the fetcher (28-day window for `backfill`, else config default):

```bash
uv run scripts/fetch_merged_prs.py
```

For `backfill`:

```bash
uv run scripts/fetch_merged_prs.py --lookback-days 28
```

Capture the fetcher's stderr summary line (PR count + comments-by-source) for the DM.

**If `pr_count` is 0:** DM the operator a one-liner (`"No merged PRs in the last Nd —
nothing to systemize."`), run `heartbeat_cli.py complete --reason complete`, and exit
clean. Nothing to analyse.

Then slim the bundle to the analysis digest — **this is the file you analyse in Step
2, not the raw bundle** (reasoning over the full raw bundle is exactly what times a
naive version of this job out):

```bash
uv run scripts/digest_merged_prs.py
```

Tick the heartbeat and read the digest JSON from the path the script printed:

```bash
uv run scripts/heartbeat_cli.py tick --job post-merge-systemize --step step-2-cluster
```

The digest carries per-finding `severity` (mapped from your review bots' own severity
scale), `resolved` (a ✅-addressed / fixed-in-commit trailer — a resolved
single-incident rarely needs routing), and `cites_guideline` (a marker like "As per
coding guidelines" — a strong tell that the finding **recurred despite an existing
rule**, i.e. a rule-citation, not a new rule). It also reports `findings_pr_count`,
`single_pass_recommended`, `batch_size`, and `n_batches` — Step 2 reads these to
decide single-pass vs map-reduce.

**Heavy-week input bound.** The digest applies a per-run cap (`max_findings_prs_per_run`,
default 75) so the map-reduce pass count stays inside the timeout regardless of PR
velocity — the unbounded set is what times a naive version of this job out on a heavy
week. When the week exceeds the cap the digest keeps the **highest-signal**
finding-bearing PRs (ranked by max severity, then unresolved count, then finding
count) and sets `capped: true`, `total_findings_prs` (the pre-cap count), and
`dropped_pr_count`. This is **not** a silent truncation — when `capped` is true you
MUST surface it in the Step 4 DM (see the heavy-week line there) so the operator knows
a tail went un-analysed and can raise the knob or shard. `findings_pr_count` (and
hence the batch math) is always the post-cap count.

Only *merged* PRs are in the bundle, so a "skip PRs still draft at week's end" filter
is satisfied by construction — a draft PR is never merged.

______________________________________________________________________

## Step 2 — Find cross-PR patterns

Work from the **digest** (`prs[].findings[]`), not the raw bundle. Each finding
already carries `source`, `path`, `severity`, `resolved`, `cites_guideline`, and the
cleaned `text` (bot/operator sources only — plain human comments and other noise were
dropped at digest time). Use `tracker_refs` per PR for ticket context.

**Choose the pass shape from the digest's hints — this is what keeps a busy week
inside the timeout:**

- **`single_pass_recommended: true`** (≤ `single_pass_max_prs` finding-bearing PRs —
  the common case): read all `prs[].findings[]` at once and cluster directly.
- **`single_pass_recommended: false`**: **map-reduce.** Process the `prs[]` in
  `n_batches` slices of `batch_size`. For each batch, extract its candidate shapes
  (shape sentence + the PR numbers + source(s) + a representative quote) into a
  running list, and **tick the heartbeat with the batch index**
  (`heartbeat_cli.py tick --job post-merge-systemize --step batch-<i>-of-<n>`) so a
  stall is locatable. After the last batch, run **one reduce pass** over the
  accumulated candidate shapes: merge shapes that are the same root cause across
  batches, union their distinct PR numbers, then classify + route exactly as below.
  The batch boundary is purely a working-set bound — a shape that spans two batches
  still counts its PRs together at reduce time.

**Cluster the review findings by *root-cause shape*, not by surface text.** Examples
of a shape (illustrative only — use your own repo's recurring bug shapes once you
have history): "a lookup with a default value doesn't fire on present-but-null", "an
aggregate counter computed independently of the materialized records it summarizes",
"asymmetric input coercion — one input guarded, its siblings not", "a loosely-typed
config format silently coerces a string to a boolean", "a repo-relative default path
resolves wrong under a different install layout".

For each candidate cluster, record: the shape (one sentence), the **distinct PR
numbers** it appears in, the review source(s) that caught it, and a representative
quote.

**Then classify each cluster:**

| Spans                         | Severity                                                     | Route →                                                |
| ------------------------------ | -------------------------------------------------------------- | ---------------------------------------------------------- |
| **≥ `pattern_threshold` PRs** | any                                                            | **(A)** Draft CLAUDE.md / skill-prompt edit (Step 3A). |
| 1 PR                           | high (a bug that would clearly recur / data-loss / security) | **(C)** Tracker ticket (Step 3C).                      |
| 1 PR                           | normal                                                         | **(B)** friction-log append (Step 3B).                  |

**Let the digest fields pre-sort the routing:** a finding with `cites_guideline: true`
that recurs is almost always a *rule-citation* (route per the "Already covered" branch
below — the rule held, caught in review — **not** a new rule). A single-incident with
`resolved: true` was already fixed in its PR, so route it only if the *shape* is still
worth a rule/inbox note, not the instance. Use `severity` to gate the 1-PR high vs
normal split.

**Before proposing any rule (A), grep the relevant CLAUDE.md for an existing rule
covering the shape.** Root `CLAUDE.md` and any path-scoped rule files your project
keeps. Two outcomes:

- **Already covered** → do **not** re-propose. Instead note it in the DM as a
  *rule-citation* signal: "pattern X recurred in #a/#b despite the existing rule in
  CLAUDE.md §Y — the rule held / didn't prevent it." This is the friction-flywheel
  impact loop (a downstream review citing a prior rule). If the recurrence suggests
  the rule is too weak, route it to the inbox (B) as a "tighten existing rule" note —
  not a fresh rule.
- **Not covered** → eligible for (A).

If **no cluster** reaches `pattern_threshold` and there are no high-severity
single-incidents, skip to Step 4 (status DM, no writes). This is the expected outcome
most weeks.

______________________________________________________________________

## Step 3A — Draft the CLAUDE.md / skill-prompt PR (≥2-PR patterns only)

For each qualifying pattern, make the **smallest** edit that would have caught it —
usually one tightening sentence in the most-specific CLAUDE.md/rule file (prefer a
narrower, path-scoped rule over the always-loaded root file; only touch root
`CLAUDE.md` when the shape is genuinely cross-cutting). Keep root `CLAUDE.md` lean —
it's loaded into every session.

Append a provenance marker to each rule so the impact loop is greppable later:

```
<!-- systemize:YYYY-MM-DD ≥2PR shape; PRs #a,#b -->
```

Then open the draft PR (mirrors `scripts/finalize_triage.py`'s proven order — fetch,
branch off the protected branch's origin ref, commit scoped paths, push, draft PR).
Substitute the literal UTC date for `<today>`:

```bash
git fetch origin main --quiet
git checkout -B chore/systemize-<today> origin/main
```

Re-apply your edits onto the freshly-checked-out base (read-after-checkout is the
safe order — a stale in-memory diff applied onto a fresh checkout is a common source
of silently-reverted edits), then commit **only** the doc/skill/config paths you
changed — never `reports/`, `state/`, or data files:

```bash
git add CLAUDE.md path/to/scoped/CLAUDE.md   # only the files you actually edited
git commit -m "docs(systemize): N cross-PR pattern(s) -> CLAUDE.md/skill rules"
git push --set-upstream origin chore/systemize-<today>
gh pr create --draft --title "docs(systemize): N cross-PR pattern(s) -> rules" --body "<body>"
```

PR body: one section per pattern — the shape, the PRs it spanned, the review
source(s) that caught it, and the exact rule added (file + section). Make the
reviewer's "is this a rule I'd follow forever?" judgment easy. Capture the PR URL for
the DM.

______________________________________________________________________

## Step 3B — Append single-incident findings to friction-log.md

For each normal single-incident finding, append an entry under the most-fitting
`## /skill` heading (or `## Infra / cross-workflow`) in `friction_log_path`, following
the existing table format (issue + date surfaced + severity H/M/L + proposed fix).
Reference the PR number and the review source. These do **not** get committed by this
skill — they ride the next `/triage-friction-log` cycle into your tracker. (In test
mode, show the proposed appends in the DM instead of writing them.)

______________________________________________________________________

## Step 3C — File high-severity single-incidents in your tracker

For each high-severity single-incident, file via your tracker's issue-create tool:

- `team` → `tracker.team_id`; `project` → `tracker.project_name` (always — your
  project's fixed default).
- `title` — concise, prefixed `[systemize]`.
- `description` — the shape, the PR it came from, the review quote, and the proposed
  fix.
- Apply `tracker.label_name` — resolve/create via the label tools if needed; don't
  block filing on a label miss.

Capture `{identifier, url}` for the DM. If the tracker is unavailable (pre-flight
degraded), fall back to a 3B append prefixed `**File as tracker ticket:**`.

______________________________________________________________________

## Step 4 — Status / summary DM

Resolve the DM target from your notify config. Post one message (chunk per your
notify config's message-size limit if long):

**No-pattern week:**

```text
:mag: *Systemize — week ending <date>*
Scanned [N] merged PRs ([bot1] / [bot2] / [operator] review comments).
No ≥2-PR pattern this week. [k single-incident note(s) → friction-log.md.]
```

**Pattern week:**

```text
:mag: *Systemize — week ending <date>*
Scanned [N] merged PRs. Found [p] cross-PR pattern(s):
• <shape 1> — PRs #a, #b
• <shape 2> — PRs #c, #d, #e
→ Draft PR: <pr_url>
[Single-incident: k → friction-log.md, m → tracker (…).]
[Rule-citation: pattern X recurred despite CLAUDE.md §Y.]
```

**Heavy-week line (MANDATORY when `digest.capped` is true).** Append this to
whichever template applies, so the capped tail is never silent:

```text
:warning: Heavy week: analysed the top [findings_pr_count] of [total_findings_prs] finding-bearing PRs (cap [max_findings_prs]); [dropped_pr_count] lower-signal PR(s) not scanned this run — raise max_findings_prs_per_run or shard the week.
```

Prefix the header with `*[TEST]*` in test mode.

**MANDATORY final action — run this `heartbeat_cli.py complete` call before printing
the run summary or returning.** Without it your scheduler can't tell a clean finish
from an `exit 0` after a rate-limit / partial run, and a tolerance check downstream
may demote the run to `incomplete`:

```bash
uv run scripts/heartbeat_cli.py complete --job post-merge-systemize --reason complete
```

Never call `complete --reason error` (or any non-`complete` reason) except on a
genuine hard stop (missing config, non-zero fetcher exit, notify channel down) — a
stderr WARNING, a zero-PR week, and a no-pattern week are all clean `--reason
complete` exits, not errors.

**End.** Output a concise run summary: PRs scanned, patterns found, routes taken (PR
URL / inbox count / tracker identifiers), DM posted.

______________________________________________________________________

## Error handling

| Situation                                     | Action                                                                                                                                                                                                                                                                                                  |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Post-merge-systemize config missing            | Stop. Clear error → failure DM.                                                                                                                                                                                                                                                                        |
| Forge unauthenticated / fetcher exits non-zero | Stop. Surface the fetcher stderr tail.                                                                                                                                                                                                                                                                  |
| Fetcher exits 0 but prints a stderr WARNING    | **Not** a failure. The fetcher's exit code is authoritative — exit 0 means success even if stderr carries a WARNING (e.g. a `--limit` cap note from `fetch_merged_prs.py`). Only a non-zero exit is a stop condition; a printed WARNING alongside exit 0 is informational and must not abort the run. |
| `pr_count == 0`                                | DM "nothing to systemize" + exit clean. No analysis.                                                                                                                                                                                                                                                    |
| Notify channel unavailable                     | Stop — the status DM is load-bearing.                                                                                                                                                                                                                                                                   |
| Tracker unavailable                             | Continue; high-severity findings fall back to a flagged inbox append; note in DM.                                                                                                                                                                                                                       |
| `git`/PR step fails                            | The edits are on disk in the worktree. Log the error, DM the proposed rule + the failure, do **not** retry blindly. The pattern is still captured in the DM for manual PR-opening.                                                                                                                     |
| No pattern ≥ threshold                         | Expected. Status DM, no writes. Not an error.                                                                                                                                                                                                                                                           |

______________________________________________________________________

## Test mode

`test` keyword activates a no-write overlay:

- Steps 1–2 run normally (real fetch, real analysis).
- Step 3A/3B/3C **write nothing** — no branch/commit/PR, no inbox edit, no tracker
  create. The skill logs "would have: opened PR with rules X,Y / appended N inbox
  entries / filed M tickets".
- Step 4 DM is posted with a `*[TEST]*` header prefix so the routing is reviewable
  without side effects.

The point is to exercise fetch → cluster → route classification without spending a
PR, a tracker write, or an inbox edit.
