# PR watch — engine reference

Read this file completely before a final authorization poll or a read-only judgement
of a pull request, and whenever a report field, blocker or flag you must act on is not
explained in [`pr-watch.md`](../pr-watch.md). It is part of that workflow and as
normative as it; a section cited by name, or as *above* or *below*, may sit in either
file.

## Contents

- Read-only act-time poll
- Notes: the seen-set, review-bot status and coverage, review evidence, the REST
  fallback, truncated reads, and tuning

## Read-only act-time poll

The normal poll persists the report's comment acknowledgment set, check-count
baseline, head, and bot-pending clock so the interactive loop can make progress.
That is intentional during the loop, but it is the wrong side effect for a final
authorization probe that must not silently acknowledge anything the operator has
not read. Use:

```sh
uv run <engine-dir>/pr_watch.py <PR#> --json --no-persist
```

`--no-persist` performs the same current-state reads and builds the same report,
but leaves the per-PR state file unchanged. It is valid only for a plain poll; it
cannot be combined with `--mark-seen`, `--record-review`, `--record-round`,
`--assert-draft`, or `--assert-ready`. A merge wrapper should use this mode for its last `mergeable`
check, after the normal watch-and-acknowledge loop has finished.

`--all-comments`, valid only with `--json` on a plain poll, adds `all_comments[]`
to the report: every comment and review submission the poll read, as
`{kind, author, path, line, state, body}`, whether or not this pull request's seen
state acknowledges it, a noise marker filters it, or its body is empty. `state` is a
review's verdict and `null` for the other kinds. The watch loop does not need it,
because `new_comments[]` is its view.
`session-start` runs it with `--no-persist` to judge an open pull request without
inheriting that pull request's acknowledgements.

## Notes

- The seen-set lives at `state/pr-watch/<PR#>.json` (gitignored). It's per-PR, so
  re-running on a different PR starts fresh.
- Known auto-noise from your review bots (walkthrough / "no actionable comments"
  summaries) is filtered out by the engine. Reviewer-unavailable notices are
  deliberately *not* noise: they surface as new comments and so block `converged`;
  acknowledging one clears `converged` but ordinarily still leaves the current-head
  review-evidence blocker on `mergeable` until the panel runs and records its
  receipt. Ordinarily, not always: an outage announced *after* the configured bot
  already reviewed this exact head leaves qualifying coverage behind it, so the
  evidence blocker is already satisfied and there is nothing for a panel to add.
  Read `review_evidence.route` rather than inferring from the outage.
- **A bot's outage is detected on both trusted surfaces, and a queued bot is not a
  finished one.** `review.unavailable_markers` are matched against comments
  authored by the exact normalized login of a configured `review.bots` entry
  (or an alias under `review.bot_author_aliases`) *and* against that bot's
  status-check description — the same rate limit is worded differently on the two
  surfaces, and matching only comments made detection depend on which one the bot
  happened to use. Author scoping matters because tracker mirrors and humans can
  quote outage text without the reviewer being unavailable. A legacy prefix-like
  author carrying an outage marker is surfaced as an **untrusted candidate** on
  its first unseen poll—it blocks convergence until handled, but never counts as
  reviewer evidence. Like every handled comment, it no longer reappears after
  `--mark-seen`; add the exact login to `bot_author_aliases` only after verifying
  it so future notices are authenticated. The report's
  `review_bots` block resolves each bot to:
  - **unavailable** — an outage announced on either surface. Rendered as
    `⚠ review unavailable …`. The status entry itself adds no
    `review_bots.blockers` item, but an unseen notice comment still blocks
    `converged`, and unavailability never satisfies the current-head review gate:
    `mergeable` stays blocked until the configured `review.fallback_panel` runs
    and records a receipt. The outage stays visible after you `--mark-seen` the
    notice comment, so the gap is still readable at merge time. Only a
    **check**-surface outage cancels the pending block below: a check describes
    the bot's state now, while comments are the whole PR history unscoped by
    head — and since rate limits are transient, an old outage comment would
    otherwise wave through every later queued review.
  - **pending** — the bot's own check is non-terminal and no outage was announced.
    A verdict is genuinely coming, so this **blocks `mergeable`** (and makes
    `--record-review` refuse) until the check ages past
    `review.bot_pending_grace_minutes` (default 15), after which the bot is treated
    as never going to report and stops blocking. Use
    `--allow-pending-bot-review` only with evidence the queued verdict will never
    arrive. CodeRabbit's pending check reports no usable timestamp
    (`0001-01-01T00:00:00Z`), so the grace clock falls back to when *this engine*
    first saw the bot pending — persisted per PR under `bot_pending_since`, scoped
    to the head, and reset by a push. A stored value the engine cannot read — or
    one dated in the future — is replaced rather than trusted, so the window stays
    bounded whatever wrote the state file.

  None of this reaches `converged`. That is deliberate and load-bearing: the watch
  loop must be able to finish while a bot that never reports sits pending forever.
  More precisely, none of the `review_bots` status or pending entries above reaches
  `converged`; an unseen outage notice still does through `new_comments`. Those
  status and pending signals feed the merge gate only.

  It also reports **`review_bots.coverage`** — the commit each bot's *last*
  review actually saw. A receipt binds to the head and a push invalidates it,
  which answers "was this exact code reviewed" but not "by whom, and how much of
  it did they see": a bot can review commit 1, go rate-limited through a
  material redesign, and the merge proceed on a fallback receipt taken at commit
  5. When a bot's last review is behind the head the render says so:

  ```
  ⚠ review coverage: coderabbit's last review was of 954b93f, not the current
    head — a receipt taken now would not stand for its review of this design;
    re-request it, or say so explicitly
  ```

  It defers to a bot that is *actively* pending — one mid-review of a just-pushed
  head is behind it by construction, and the pending line already says a verdict
  is coming. It does **not** defer once that check ages past the grace window or
  is cancelled by an announced outage: that is the engine saying the verdict is
  not coming, which is the reviewer-went-away case this exists for.

  `--record-review` records the same gap on the receipt as `bots_behind_head`,
  next to `override` and `bot_signal` — all three say what the receipt does *not*
  stand for. It is recorded even under `--allow-pending-bot-review`, since that
  override is itself the #22/#25 scenario. (Unlike the poll render, the receipt
  does not defer to a pending bot: recording a receipt is the moment the gap
  matters most.)

  Reported, never gating — deliberately the cheap half of the problem, because
  invalidating a receipt on a shape change risks wedging a repo whose bot is
  permanently unavailable.

  Once a current-head receipt exists, every poll also prints what that receipt
  **claims** to cover:

  ```
  review evidence: fallback:panel — 2 lenses claimed (adversarial, correctness)
  review evidence: fallback:codex — ⚠ ONE lens claimed (correctness) — not a dual-lens pass; it changes scripts/pr_watch.py under review.safety_critical_paths
  review evidence: fallback:lens — one lens claimed (adversarial), which is what this PR owes: no path in review.safety_critical_paths changed
  ```

  Self-reported: `--lenses` is written by whoever ran `--record-review`, and the
  engine records it without verifying it (issue #32). It is shown here so a
  one-lens pass is visible when a merge is considered rather than only in the
  record command's output. Entries that read as prose rather than a lens name
  are recorded but not counted.

  **Known gaps, so you don't mistake them for coverage:**
  - Composed receipts make `mergeable` depend on a valid parent/delta chain and
    exact Git paths, including both sides of a rename, and retain the override,
    unreadable-bot, and behind-head caveats of each recorded pass. The poll
    revalidates those mechanical facts before `dev_session.sh merge` can rely on
    them.
    The source and lens names remain self-reported: the engine cannot establish
    that the named reviews ran. Per-lens independent receipts remain issue #32's
    stronger provenance boundary.
  - `coverage` reports only bots that have reviewed *and* whose review carried a
    commit SHA. A bot that has never reviewed at all produces no entry and no
    warning — that case is the pending/unavailable machinery's, not this one's.
  - The pending block only exists once the bot has *registered* a check. In the
    window between `gh pr ready` and the bot creating its check row, "the bot
    hasn't started yet" is indistinguishable from "this repo has no bot", so a
    receipt recorded in that window is still premature. Give a freshly-readied PR
    a poll or two before recording one.
  - `review_bots.signal` is `ok` / `skipped` (no bots configured) / `unavailable`
    (the check read failed — e.g. a `gh` too old for the requested `--json`
    fields, or a PR with no checks at all). On `unavailable` **both guards are
    off**; it's reported rather than blocking, because an environment problem
    shouldn't become a wedge — and a receipt recorded while the read was
    `unavailable` carries a `bot_signal` key so the audit trail shows the guard
    didn't run. (`skipped` is not flagged: nothing was unreadable.)
  - An *older* `pr_watch.py` polling the same PR drops the persisted grace clock,
    restarting the window. Merges wait longer; nothing fails open.
- **`evidence_findings[]` says where the review evidence *isn't*.** Two entries,
  both **reported and gating nothing** — the same footing `bots_behind_head` and
  `truncated_reads` have. They describe evidence missing from the pull request
  while the merge gate is already satisfied, so blocking on either would refuse a
  merge the deterministic checks correctly authorized, on a judgement drawn from
  prose.

  ```
  ⚠ review disposition: the receipt for 01fc4e7c9ff… has no disposition comment
    on this PR — what the review found and how each finding was disposed exists
    only in the untracked per-PR state file, so the merge loses it.
  ⚠ verification stamp: this PR stamps 679b197efc…, and none of those is the
    current head 01fc4e7c9ff… — the run it names did not see the commits since.
  ```

  - `review_disposition_missing` (`#604`) — a receipt is bound to this head and
    no comment on the pull request is. Silent on the `bot-coverage` route, where
    the reviewer's own review objects are on the pull request already. The
    remedy is `--record-review --disposition`; a hand-written comment under some
    other heading does not clear it, because the check reads the marker the
    engine writes rather than matching prose.
  - `verification_stamp_behind_head` (`#603`) — the pull request carries at least
    one verification stamp in the `` `<command>` at `<sha>` on <date> `` form, or
    with the directory between them as `` at `<sha>`, in `<dir>`, on <date> ``, and
    none of them names the current head. Stamps are read from the body **and**
    from every comment, so a final stamp posted as a comment at the merged head
    clears it — that is the form to use. Silent when there is no stamp at all: an
    absent stamp is a different complaint, and firing on every prose-only pull
    request is how a report line becomes something its reader skims past. The
    matcher is anchored on the date, so a commit named in passing ("pinned at
    `3c06e70`") is not read as a claim about a run.
- **Without `gh`, the engine polls but cannot authorize a merge.** When the `gh`
  binary is absent it falls back to the GitHub REST API using
  `GH_TOKEN`/`GITHUB_TOKEN` (with neither, it exits 2 saying so). That fallback is
  deliberately **poll-only**:
  - `mergeable` is **false by construction**, with the merge blocker `the REST
    backend cannot authorize a merge — it polls only`. No response from GitHub can
    change that; it is not a judgement about the PR.
  - `--record-review`, `--record-round`, `--assert-draft` and `--assert-ready`
    **refuse** with exit 2. The two record modes write durable state bound to the
    PR head they read, and the draft flags mutate the PR, so they need `gh`.
  - `converged` works normally, which is the point: you can run the watch-and-fix
    loop from a session without `gh` and hand the merge back to one that has it.
  - `report["backend"]` says which transport produced the poll (`gh` / `rest`).
  - Broadening this is tracked as an issue in this repo's tracker; it needs every
    external input to read fail-closed first, so do not lift it casually.
  - Known gaps on the REST path, stated rather than discovered: no GitHub
    Enterprise (`GH_HOST`), no `GH_REPO` (it reads `origin`), no **fork**
    checkouts (the branch lookup reuses the `origin` owner, so a fork queries the
    fork while the PR lives upstream — pass an explicit PR number there), and
    `dev_session.sh pr-watch <scope>` itself needs `gh`, so a gh-less session must
    invoke the engine directly.
- **`truncated_reads`** lists any paginated read that stopped at the page ceiling
  rather than at the end of the data. A truncated read means the poll did **not**
  see every check or comment, so `converged` may be premature — REST list
  endpoints return oldest-first, so what gets dropped is the newest. It gates
  nothing (blocking `converged` would wedge the loop) and is printed by the human
  render as well as carried in the JSON. Empty on the `gh` backend.
- **Tune this for your own bot mix in `config/dev-model.yaml`, never in the engine.**
  `review.bots`, `review.bot_author_aliases`, `review.noise_markers`,
  `review.unavailable_markers`, `review.informational_checks` and
  `review.bot_pending_grace_minutes` are read from config; the engine only carries
  them as fallbacks for a missing config.
  `review.bots` and `review.informational_checks` ship with the *same* value and
  different jobs: the latter is a blocking policy ("this check never blocks the
  watch loop"), the former an identity ("this check belongs to a reviewer whose
  state the merge gate cares about"). Bot names match case-insensitively as a
  **substring** of a check name (your own CI and bot config). Comment authors are
  stricter: only the exact bot key, its conventional `[bot]` form, or an exact
  login configured under `review.bot_author_aliases` is trusted. The shipped
  CodeRabbit aliases cover `coderabbitai` and `coderabbitai[bot]`; custom bots
  must list differing author logins explicitly. This replaces the legacy prefix
  rule—after upgrading, an unseen prefix-like outage comment gets one actionable
  untrusted-candidate warning instead of disappearing as noise. Editing the literals inside
  `<engine-dir>/pr_watch.py` forks the engine and turns every later kit update into
  a merge conflict. A key you omit keeps the kit default; an explicit empty list
  (`noise_markers: []`) means "filter nothing".
- `review.require_ci` (default `true`) is whether a PR must have at least one real,
  non-informational check before it can report green. Leave it `true` unless the repo
  genuinely has no CI — with no checks and `require_ci: true`, `converged` can never flip
  and `dev_session.sh merge` will always refuse. Setting it `false` does **not**
  weaken the review gate: `mergeable` still requires current-head
  independent-review **evidence** by either route above, which then becomes the only
  quality gate — so set it deliberately. Note how the two settings compose:
  `require_ci: false` on a repo with `review.bots: []` leaves the receipt as the single
  gate, since the coverage route needs a configured bot to exist.
- This is interactive-only. A scheduled job that opens its own PRs should be excluded
  from this loop by your cron/CI runner's env signal (any of `DEVKIT_CI_ENV_VARS`,
  default `JOB_NAME,CI,GITHUB_ACTIONS,GITLAB_CI,BUILDKITE`), so an automated open
  never silently enters an unattended watch loop.
