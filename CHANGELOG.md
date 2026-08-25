# Changelog

**What this file is for.** An adopter refreshing kit-owned engines is told by
`/upgrade` Step 3 *which* file to take. This file is the other half: what taking it
will **change**. It exists so that a red test after a file copy is a five-minute
expected edit rather than a debugging detour (`#430`).

**What it records — and only this.** Changes **observable at the API surface**: the
things that break a repo pinning the old contract.

| axis | what it covers |
|---|---|
| report / return shape | keys and values an engine's report or a function's return grew, lost, or changed meaning |
| gate semantics | when `converged` / `mergeable` / `done` / a hook's exit code flips |
| config keys | a `config/dev-model.yaml` key added, removed, renamed, or given a new default |
| engine CLI surface | a flag, argument, or exit code an adopter or CI invokes |

Each line names the issue(s) and states **what you must do**. Nothing else belongs
here — a change with no adopter-visible consequence gets no entry.

**It is deliberately not a record of *why*.** The rationale for a change lives in the
comment beside the code that implements it, which is the one place it stays true when
the code moves. Duplicating it here would create a second copy to keep correct, and
the stale copy is the one an adopter would read. If you want to know *why* the merge
gate waits for a settle baseline, read `build_report`. This file tells you only *that*
it does.

**How to read it during an upgrade.** Do not read from the top. `/upgrade` Step 1
resolves your recorded baseline kit commit into exactly the set of entries below that
are new to you; follow that.

**Ordering and headings.** Newest first. An entry is headed by the **PR** that made
the change, because the entry is authored in that PR rather than stamped on
afterwards — see `AGENTS.md`, Ground rules. There are no release tags: adopters pin a
kit *commit*, not a version.

**Axes.** `BREAKING (…)` — a repo pinning the old contract fails. `CHANGED` —
observable but compatible. `ADDED` — new surface you may adopt or ignore.

`#407` is the oldest entry; nothing before it is backfilled. This file starts where it
starts.

---

## #596 — 2026-08-25

- **CHANGED (gate semantics) — `session-start` now stops before rendering its normal
  briefing when repository/config or repository-state reads fail; unavailable forge,
  CI/cron, tracker, configured drift, or candidate-remediation reads produce explicit
  degraded results instead of empty, clean, or `Now` claims.** **Refresh
  `docs/agentic-dev-kit/workflows/session-start.md`. Keep the existing runtime adapter;
  it loads the shared declaration and needs no new config key or connector name. Resolve
  config through `kitconfig.load_config()` or your equivalent merged-view mechanism so
  the local overlay is not ignored. Treat the workflow as read-only, and let
  non-interactive invocations render once and exit. Always attempt and classify the
  forge, CI/cron, and tracker sources; only an explicitly unconfigured or untriggered
  declaration may be omitted.**
- **CHANGED (gate semantics) — `wrap-up` now stops before staging when required
  repository/config, record-write, or document-budget capabilities fail; tracker
  unavailability, silence, decline, or missing exact-payload approval parks the complete
  finding in the friction log, while an interactive issue-shaped finding must be
  searched and presented for an exact-payload decision instead of parked by default.
  A changed record reaches a terminal state only after its branch/PR/`pr-watch` path
  settles and merge authority either permits the merge or holds the exact head for the
  operator. Non-lane pull requests without a project merge policy default to
  operator-authorized merge; they never default to autonomous merge. Conditional
  capabilities are classified when triggered rather than claimed ready before the
  handoff edit.** **Refresh
  `docs/agentic-dev-kit/workflows/wrap-up.md`. Keep the existing runtime adapter and
  config. Resolve the merged config view, and do not treat a configured tracker, prior
  approval, or standing autonomous authority as approval for a create, modification,
  or occurrence-comment payload, or as authority to merge.**

---

## #595 — 2026-08-24

- **ADDED (config keys) — `config/dev-model.yaml` now declares the shared
  `systemize.*` workflow policy** (`#243`; `#7` stays open). **Re-run `./init.sh`
  after taking this kit update to add the shipped block. If your config already
  contains a partial `systemize:` block, the installer preserves it rather than
  guessing your policy; merge the missing shipped keys manually before invoking the
  workflow. Keep the shipped `{date}`, `{window}`, and `{mode}` placeholders in every
  artifact pattern so live, test, normal-window, and backfill runs do not share a
  same-day artifact. Set `systemize.operator_logins` to the exact forge identities
  whose review findings the workflow may trust; `./init.sh` prompts for that list and
  requires its one-line YAML flow-sequence form. Before re-running, rewrite tagged,
  quoted, anchored, explicit, duplicated, or inline-commented top-level section keys
  into unique bare YAML keys; write `systemize:` without an inline comment and keep
  its child keys bare at the shipped two-space indentation. The installer refuses
  tagged, anchored, aliased, typed, escaped, or ambiguous operator-login items before
  migration writes; use simple plain login tokens or simple quoted strings.**
- **CHANGED (gate semantics) — `post-merge-systemize` now fails closed when the
  required repository, config, or complete merged-PR history is unavailable, and
  when only part of the configured engine set is installed; an entirely absent
  engine set selects the labelled agent-executed path** (`#243`; `#7` stays open).
  **Keep the shared state-path resolver under `paths.engines`; install every configured
  fetch/digest/heartbeat engine or none of that optional set. Treat the report as the
  durable degraded path when an optional forge write, tracker, reviewer, or notification
  capability is unavailable. Tracker writes additionally require the operator to
  approve the exact payload. Resolve a local change to an intended rule destination
  before retrying that route; it now requires a clean isolated worktree and an exact
  staged-path set. Move or repoint any existing artifact target whose declared kind and
  complete run identity do not match the current run; the workflow will not replace
  it.**
- **CHANGED (gate semantics) — the old Claude command directly creates tracker items
  and does not load the shared approval gate** (`#243`). **`/upgrade` ordinarily keeps
  an existing runtime adapter, so replace
  `.claude/commands/post-merge-systemize.md` with the kit's thin binding during this
  upgrade after diffing any local changes into config or the shared workflow. Do not
  schedule the old command against the new config.**

---

## #593 — 2026-08-24

- **ADDED (engine CLI, report shape) — `pr_watch.py --record-review
  fallback:delta` accepts `--compose-parent <reviewed-parent-sha>` and reports
  validated `review_evidence.coverage` / `coverage_error` fields for composed
  receipts** (`#32`). **Call the flag only with the exact head named by the standing
  full-panel receipt, keep the parent and final commits available in the local Git
  object store, and allow the additive fields in strict JSON consumers.** Legacy
  receipts and delta recording without the flag retain their prior shape.
- **CHANGED (gate semantics) — a composed current-head receipt no longer authorizes
  merge when its full parent, delta chain, Git ancestry, final head, recorded lenses,
  exact changed paths (including both sides of a rename), or preserved per-pass
  review caveats cannot be re-established.** **Fetch the missing objects or rerun the
  required review at the current head; do not hand-edit the persisted receipt to
  bypass the failed validation.**

---

## #590 — 2026-08-23

- **BREAKING (report / return shape, gate semantics) — `kit_doctor` now reports
  exactly identified Codex lifecycle wiring as
  `verified`, structural drift as `misconfigured`, and unsupported object keys around
  an exact command as `unverifiable`; the latter states make its process exit non-zero**
  (`#243`). The bounded check applies to the portable document-budget and
  PR-follow-through engines across `.codex/hooks.json` and inline
  `.codex/config.toml`, including project hook enablement and duplicate recognizable
  references. It does not assign lifecycle meaning to altered shell strings. **If you parse
  the JSON report, accept `verified`, `misconfigured`, and `unverifiable` as
  registration states. Reconcile an unverifiable object to the exact command and
  structural fields printed by `./init.sh`; altered command strings receive only
  generic path diagnostics. Then
  review the current definition through `/hooks`. When canonical `hooks` and deprecated
  `codex_hooks` are both present, keep the canonical value authoritative; both values
  must still be boolean. If bare Python lacks a standard-library TOML parser, rerun the
  doctor through `uv`.** Repository
  inspection does not establish project trust, definition trust, or live execution.

---

## #588 — 2026-08-23

- **CHANGED — the Codex `SessionStart` registration printed by `./init.sh` and
  shipped in `.codex/hooks.json` no longer invokes `check_memory_budget.py`**
  (`#243`). That engine reads Claude Code's external `MEMORY.md`; Codex keeps the
  portable `check_doc_budget.py` registration. **Existing hook configuration is
  adopter-owned: remove the memory-budget command by hand, reconcile the document
  command printed by `./init.sh`, then review and trust its current definition through
  `/hooks`.** The printed guidance now says that omitting a matcher covers every
  supported start source.
- **ADDED — `kit_doctor` tracks
  `docs/agentic-dev-kit/runtime-parity.md` as kit-owned doctrine** (`#243`). An
  older install baseline reports the absent path as `new-upstream`. **During
  `/upgrade`, take the file to adopt the machine-readable adapter inventory and
  capability matrix, or explicitly decline it.**

---

## #580 — 2026-08-22

- **`kit_doctor`'s text report now opens with a dedicated block when this repo's copy
  of `docs/agentic-dev-kit/workflows/upgrade.md` has drifted** (`#577`), above the
  installation checks and above the drift list — which still carries the file as
  before. The block exists because that file's drift is not like the others': an
  upgrade runs Steps 2-3 from the copy on disk and replaces it only in Step 4, so a
  drifted copy drives the whole run, and the paragraph telling you to check for that
  is inside the copy you do not have yet. **If you parse the text report, expect a
  leading block that was not there.** Nothing else moved: no flag, no `--json` key
  (the state is still read off `files`), and no exit code — `drifted` already carried
  this file, so a run that renders the block was already exiting non-zero. It fires on
  every drift state and on no absent state.
- **The `/upgrade` runtime adapters now tell you to re-read the workflow from the
  Step 0 clone before Step 2** (`.claude/commands/upgrade.md`,
  `.agents/skills/upgrade/SKILL.md`). **These are adopter-owned and `/upgrade` Step 4
  keeps your version, so upgrading does not give you this — copy the new text in by
  hand**, or the gap above stays open on the one surface that is read before any of
  the workflow is. Same reason `#553`'s entry gives for the `triage-friction-log`
  adapter: your copy will not be overwritten, and it will not be updated either.

---

## #558 — 2026-08-22

- **`dev_session.sh merge` now REFUSES a `pr_watch --json` report whose `pr`,
  `base`, or `head` carries a control character, where it previously
  mis-parsed one and could authorize the merge** (`#537`). The gate emits those
  fields tab-joined and the shell splits them, so a tab inside an earlier field
  shifted every later one; measured, a report whose real base was `WRONG` and
  whose real head was empty was AUTHORIZED. Control characters are now mapped
  to a space before the join, which no git ref or PR number can contain, so the
  identity checks fail closed. **If you vendor `scripts/dev_session.sh`, take
  the new copy.** No report key, config key, or CLI flag changed, and no report
  any real `pr_watch` emits parses differently — a lane that merged before
  still merges.
- **`_resolve_lane_pr` (used by both `dev_session.sh merge` and
  `dev_session.sh pr-watch`) refuses the same shape in `gh pr list` metadata**
  (`#537`). Its base / branch / head-repo-owner checks were bypassable by the
  same field shift. Same scrub, same fail-closed direction.
- Both are pinned by new tests in `scripts/tests/test_portability.py`; if you
  vendor that file too, take it with the engine.

---

## #553 — 2026-08-21

- **`triage-friction-log` is now a shared workflow at
  `docs/agentic-dev-kit/workflows/triage-friction-log.md`, tracked in
  `kit-manifest.json`** (`#243`). Its doctrine previously lived only in
  `.claude/commands/triage-friction-log.md`, which no manifest entry covered,
  so `/upgrade` never refreshed it and `kit_doctor` could not report it as
  `differs` however stale it was. **Do not expect your first `kit_doctor` run to
  name the new workflow at all.** `inspect()` iterates the `KIT_OWNED` tuple in
  the *running* script and consults `--manifest` only for the hash of a path
  that tuple already knows, so the run `/upgrade` Step 1 prescribes — your own
  installed `kit_doctor.py` against the new kit's manifest — reports
  `0 missing` and never mentions it. What that run does show is
  `scripts/kit_doctor.py` itself as `differs`; taking that update is what makes
  the workflow visible. **Afterwards** a pre-existing baseline gets an
  informational `new-upstream` block — never a finding — and a repo with no
  baseline recorded reports `missing`. No state here fails a gate, and
  `/upgrade` offers the doc either way. **If you edited your copy of the Claude command, your edits
  survive — and that is the hazard, not a reassurance.** `/upgrade` Step 4
  keeps an adopter's existing runtime adapter rather than refreshing it, so
  your thick edited copy stays in place and keeps being what your
  `triage-friction-log` invocation runs. It will not be overwritten, and it
  will not be updated either: every future change to this workflow lands in the
  shared doc. Move your edits there and let the adapter become a pointer, or
  accept that you are pinned to your fork. A new Codex binding ships at
  `.agents/skills/triage-friction-log/`; ignore it if you do not run Codex.
- **The workflow's paths are now resolved from `config/dev-model.yaml` instead
  of hardcoded.** It named `docs/friction-log.md` and `scripts/<engine>.py`
  literally; it now resolves `<friction-log>`, `<friction-log-archive>`,
  `<engine-dir>`, `<state-dir>` and `<tracker>`. **If your `paths.friction_log`
  or `paths.engines` is anything other than the kit default, this workflow
  followed the wrong path before and follows yours now** — that is a behaviour
  change, not only a wording one. No config key was added, removed, or
  redefined; the keys it reads already existed.
- No engine is vendored by this change and no report shape, gate semantic, or
  CLI surface moved. `#6` still tracks the triage engine.

## #538 — 2026-08-21

- **A pending review bot's `identity` is now resolved on a healthy poll, not
  only on an outage-marked one** (`#535`). `review_bots.pending[].identity` and
  `.trusted` were `""` / `false` for every mid-review row on the `gh` backend
  and on REST's status-context surface, because `fetch_check_details` gated the
  identity read on a row that could *cancel* a pending block. **If you pin
  `identity: ""` or `trusted: false` on a healthy pending entry, that
  expectation breaks** — a real reviewer's own pending check now reports its
  creator and `trusted: true`. A REST check-*run* is unchanged; it already
  carried `app.slug`. Cost while a bot check is pending: **one** extra REST
  call (the plural `/commits/{sha}/statuses`), or **up to three** extra `gh`
  invocations on the `gh` backend — a check-runs page and a statuses page
  always, plus the head-move recheck only when those resolved at least one
  identity. None once every bot row is terminal and unmarked.
- **`⚠ review coverage` and `⚠ review owed` are now silent while a trusted bot
  is mid-review** — the suppression `#521` and `#518` documented but which
  never fired on the `gh` backend or for a REST status context. A REST **check
  run** already resolved its creator from `app.slug` and was unaffected, so
  whether you see a change here depends on your transport and on which surface
  your reviewer posts. **If you assert on either line's presence during a bot's
  pending window, that assertion inverts.** Neither line gates anything; `mergeable`,
  `converged` and `merge_blockers` are unchanged.
- **`⚠ review owed` is additionally silent for a bot whose outage is announced
  on its own TRUSTED CHECK** (`#535` item 4) — it previously told you to request a
  review from a reviewer that had just announced it could not run, in the same
  render that prescribed the fallback panel. Two shapes still leave the line
  firing, deliberately: an **untrusted** outage row cancelled nothing (`#95`),
  and a **comment**-borne outage is a statement about the past that
  `collect_comments` returns unscoped by head or age — one stale rate-limit
  comment would otherwise silence the line for the rest of the PR's life. In
  both, the reviewer is still owed a look.

## #527 — 2026-08-20

- **`kit-manifest.json` now tracks the kit's own test suite** (`#493`): all 16
  files under `scripts/tests/` and the 2 under `scripts/lib/state_paths/tests/`
  are now in `KIT_OWNED`, under a new role, `"test"`. Previously a vendored
  copy of the suite was invisible to `kit_doctor` — `0 differ` regardless of
  how stale it was — which let a vendored `conftest.py` missing the
  `_hermetic_state_root` fixture go undetected while its runs wrote into a
  real `state/pr-watch/` tree. **A pre-existing baseline** gets an
  informational `new-upstream` block naming up to 18 files on every
  `kit_doctor` run until you run `/upgrade` to accept or decline them; the
  intact/not-intact verdict is unaffected. **If you already vendored part or
  all of the suite**: your next `kit_doctor` run reports real drift on those
  files for the first time (previously silent), and `/upgrade` refreshes them
  like any other kit-owned file. No config key or CLI surface changed.

## #530 — 2026-08-20

- **`review_evidence.head` is now `null` on the `bot-coverage` route** (`#495`) —
  it previously named the receipt's head unconditionally, so a STALE receipt
  sitting beside qualifying bot coverage at the current head reported the stale
  sha next to `valid: true`. `head` now joins the other receipt-only keys
  (`source`, `lenses`, `override`, `bot_signal`): populated only when `route` is
  `"receipt"`, `null` on `"bot-coverage"`. **If you read `review_evidence.head`
  to learn which commit the evidence covers, read the report's own top-level
  `head` instead** — that is what the evidence is always keyed to, on either
  route.

## #525 — 2026-08-20

- **`⚠ review coverage:` staleness warning now requires a TRUSTED pending bot to
  suppress it** (`#521`), not merely a name-matching one. Previously the warning
  ("this bot's last review was of an older commit") was silenced by ANY pending
  entry for that bot, and `review_bots.pending` is matched by check **name** — a
  case-insensitive substring — so a same-repo PR's own workflow (`checks: write`)
  could post a check named e.g. `coderabbit-shim-status` and suppress the coverage
  warning about its own diff, for up to `bot_pending_grace_minutes`. The line now
  reads the same `identity`/`trusted` fields `#520` added to `review_bots.pending`
  entries: a missing, forged, or unresolvable identity counts as untrusted, and the
  warning FIRES. **No report-shape change** — `identity`/`trusted` already existed
  on every `pending` entry. If you scrape poll output, expect this warning to fire
  in more cases than before (specifically, wherever it used to be silenced by an
  untrusted pending check) — that is the fix, not a regression. **The merge gate is
  unchanged**: `blocking` still governs it, unchanged and fail-closed, exactly as
  `#520` left it.

## #520 — 2026-08-19

- **New poll line `⚠ review owed:`** (`#518`) — printed when the report is
  `converged`, `review_bots.signal` is `ok`, and at least one configured bot is
  unaccounted for: no review of its own covering the current head, no
  `review_bots.comment_verdicts` entry, and no review in flight. The line **names
  the unaccounted bots**, so a multi-bot config gets one answer per reviewer rather
  than a single verdict speaking for all of them. **Informational: it blocks
  nothing.** `converged`, `mergeable`,
  `review_evidence` and `merge_blockers` are unchanged, and a `fallback:panel`
  receipt still authorizes the merge — the line still prints in that state, which is
  the point of it. If you scrape poll output, this is a new line; **this line itself
  adds no JSON key** — the next bullet is the one that changes the report shape.
- **`review_bots.pending` entries grew `identity` and `trusted`** (report shape) —
  the check creator GitHub records, and whether it is trusted to speak for that bot
  (`#95`'s rule, the same two fields `review_bots.unavailable` already carries).
  Additive: if you parse `review_bots`, nothing was removed or renamed.
  **`blocking` deliberately does not read them and the merge gate is unchanged** — a
  forged pending check still blocks, which is fail-closed, since it can only block the
  PR that forged it and it ages out at `bot_pending_grace_minutes`. The new
  `⚠ review owed` line is the first consumer that *does* require trust: a check name
  is matched as a substring and is the PR's own to choose, so an untrusted row must
  not be able to silence "nobody has reviewed this" on the PR that posted it.
- **`docs/agentic-dev-kit/workflows/pr-watch.md`: the `converged` loop step now
  settles the coverage request before recording the receipt**, and states that an
  already-true `mergeable` does not discharge it. If you have vendored or forked that
  workflow, take this step; a loop running the old wording can reach merge with the
  configured reviewer never asked. Engine behaviour does not depend on it.

## #500 — 2026-08-17

- **`review_bots` grew a `comment_verdicts` key** (report shape) — configured bots
  that announced a *completed* review of the current head in a **comment**, creating
  no review object (`#44`). Entries are `{bot, sha}`. **Reported only: no gate reads
  it.** `mergeable`, `review_evidence` and `merge_blockers` are unchanged, by ruling —
  keying a merge gate on a reviewer's prose would let an upstream wording change
  decide merges. If you parse `review_bots`, this is additive.
- **`config/dev-model.yaml` gained `review.comment_verdict_markers`** — comment text
  announcing a completed review, matched case-insensitively as substrings. Defaults to
  `["no actionable comments were generated", "actionable comments posted:"]`. The
  installer only adds absent keys, so **an existing config keeps working unchanged**
  and inherits these defaults; set it only if your reviewer words its verdict
  differently. A marker matching nothing costs you the report line and nothing else.
- **New poll line `ⓘ review reported:`** on that state, naming the sha and the
  `--record-review "<bot>:comment-verdict" --head <sha>` command. If you scrape poll
  output, this is a new line; it is informational and never blocks.
- Receipt source **`<bot>:comment-verdict`** is now a named literal for that case,
  recorded with **no `--lenses`**. Deliberately outside the `fallback:` namespace —
  those stand for a substitute pass, and this stands for the real reviewer on a
  surface the gate cannot read. Sources are free-form, so nothing rejects the old
  spelling; the name is for the audit trail.

## #499 — 2026-08-17

- **BREAKING (gate semantics)** — the `#488` objection blocker is now read from each
  configured bot's latest **verdict** (`APPROVED` / `CHANGES_REQUESTED` /
  `DISMISSED`) rather than from its latest **review of any kind**. A bot's own
  follow-up `COMMENTED` or `PENDING` review at the same head no longer clears its
  standing `CHANGES_REQUESTED` — previously it did, *and* then supplied the
  independent-review evidence, taking a PR from two merge blockers to zero with no
  commit pushed, nothing dismissed, and no forge audit trail. **If you rely on that
  behaviour, you were relying on a fail-open**; the routes out are unchanged, and are
  now exactly three — address the findings and push, dismiss the review on the forge,
  or have the reviewer re-review this same head and approve. Each of the three leaves
  the forge showing why the objection no longer applies — a superseding commit, a
  dismissal, or a later approving verdict. The follow-up `COMMENTED` showed only that
  a review happened, which nothing reads as a clearance.
  Nothing to do on upgrade unless a PR of yours is currently merging through the old
  path, which will now correctly refuse. Pinned by
  `test_a_bots_own_later_non_verdict_review_cannot_clear_its_objection` and
  `test_the_objection_read_pins_both_clauses_and_ignores_a_failed_check_read` in
  `scripts/tests/test_pr_watch.py`.
- **`review_bots` grew an `objections` key** (report shape) — the verdict-only
  reduction over the same review list that `coverage` reduces newest-wins. Same entry
  shape as `coverage` (`{bot, sha, submitted_at, covers_head, state}`). If you parse
  `review_bots`, this is additive. **If you compute an objection yourself from
  `review_bots.coverage`, move it to `objections`** — `coverage` deliberately still
  reports the newest review whatever it says, because a bot's ordinary *clean* review
  is `COMMENTED` and `#350`'s evidence route depends on that.
- **Corrects the wording of the `#488` entry below**, which says "own latest review of
  the **current head** is `CHANGES_REQUESTED`". Read strictly that described the
  defect, not the intent. It should read *latest verdict*; the entry is left as
  written rather than edited so the record stays honest about what shipped.

## #488 — 2026-08-16

- **BREAKING (gate semantics)** — `mergeable` (and its `done` alias) is now **false**
  while a configured `review.bots` entry's own latest review of the **current head**
  is `CHANGES_REQUESTED`, and a `--record-review` receipt no longer overrides that.
  A PR your review bot has asked for changes on will stop reporting mergeable even
  with a valid current-head receipt, so an autonomous `dev_session.sh merge` that
  previously fired on such a PR will now refuse. **To clear it, address the findings
  and push** — the blocker is bound to the head, so a new commit leaves the objection
  covering an older one and it clears on the next poll; a review dismissed on the
  forge clears it too. There is **no override flag**:
  `--allow-pending-bot-review` covers a *silent* bot and does not apply. Only
  `CHANGES_REQUESTED` blocks — `PENDING`, `DISMISSED`, an empty state, and any state
  this engine does not recognize raise no blocker, so a PR whose bot review carries
  one of those is unaffected. A repo with `review.bots: []` is unaffected entirely.
  **This supersedes the `CHANGES_REQUESTED` caveat in `#484` below**, which recorded
  that a receipt could authorize a merge over a standing objection and that `#484`
  left it that way. `#485`.
- **CHANGED (report shape)** — `merge_blockers[]` may contain a new entry,
  `configured review bot requested changes on current head: <bot>` (comma-separated
  when several). Anything matching on the exact blocker set must expect it. On the
  REST backend this fires **alongside** the existing
  `review decision is CHANGES_REQUESTED`, because `_rest_review_decision` aggregates
  every reviewer; under `gh` it is usually the only one of the two, which is what
  made `#485` reachable. `#485`.
- **ADDED (return shape)** — `objecting_bot_coverage(review_bots, head)` is public
  beside `qualifying_bot_coverage`, returning the sorted configured bots with a
  standing objection to `head`. Unlike its sibling it does **not** require
  `review_bots["signal"] == "ok"`: the objection is read from `pr view` review
  objects, not from the check read that `signal` describes. `#485`.

## #484 — 2026-08-15

- **CHANGED (gate semantics)** — `mergeable` no longer requires a `--record-review`
  receipt in every case. It is now satisfied by current-head independent-review
  **evidence** from either of two routes: a receipt bound to the head (unchanged), or a
  configured `review.bots` entry whose own review covers that exact head **and carries a
  standing verdict** — `APPROVED` or `COMMENTED`. A review that is `DISMISSED`,
  `PENDING`, `CHANGES_REQUESTED`, or in any state this engine does not recognize is
  **not** evidence, and leaves the receipt requirement standing. Note especially the
  `CHANGES_REQUESTED` case if you relied on the separate `reviewDecision` blocker to
  cover it — **it covers it on one transport and not the other.** Under `gh`, that field
  is GitHub's own and reflects required-reviewer rules, so it can read `""` while a
  non-required bot asks for changes; on the REST fallback, `pr_watch`'s own
  `_rest_review_decision` aggregates every reviewer regardless, so the blocker does fire.
  The evidence rule above holds on both, which is why it does not defer to that blocker. **If you record a receipt
  on a PR your review bot already reviewed, stop — you no longer need
  to, and every available `<source>` literal names a fallback pass that did not run.**
  A repo with `review.bots: []` is unaffected: with no configured bot there is no
  coverage route, and the receipt stays the only way through. Nothing is loosened for
  a PR the bot has *not* reviewed at the current head — an unusable commit SHA on the
  review, a verdict that arrived only as a comment (`#44`), or a failed bot-state read
  all yield no evidence and leave the receipt requirement standing. A pending bot's
  grace blocker and an unacknowledged outage notice keep their existing authority.
  **`CHANGES_REQUESTED` is not claimed to** — a recorded receipt has always been able
  to authorize a merge over a bot's standing objection, because `--record-review`
  refuses only on a bot's *pending check row*, never on its submitted verdict. That is
  unchanged by this release and is why the new route excludes the state outright rather
  than deferring to that blocker. `#350`.
- **CHANGED (report shape)** — `review_evidence` grew two keys. **`route`** is
  `"receipt"`, `"bot-coverage"`, or `null`, and names which route satisfied the gate
  (`"receipt"` wins when both hold). **`bots`** is the sorted list of configured bots
  whose coverage qualified, and is populated even when `route` is `"receipt"`. **If
  you assert on the exact shape of `review_evidence`, add both keys.** The
  receipt-describing keys — `source`, `lenses`, `override`, `bot_signal` — are
  unchanged and stay receipt-only, so they are `null`/`[]` on the coverage route.
  `#350`.
- **ADDED (report shape)** — each `review_bots.coverage[]` entry gains a **`state`** key:
  the upper-cased GitHub review state of that bot's last review, or `""` when the payload
  carried none. **If you assert on the exact shape of a coverage entry, add it.** Coverage
  is still reported for a non-qualifying state — the advisory display shows which commit
  the bot last looked at regardless — so `state` is the only way to tell a reported entry
  from a gating one. `#350`.
- **ADDED (report shape)** — the poll render gains two lines. A coverage-route report
  prints `review evidence: the configured review bot reviewed this head (<bots>) — no
  receipt needed` in place of the receipt line; a receipt-route report that *also* has
  coverage gains an indented `+ the configured review bot also reviewed this head
  (<bots>)` beneath its existing line. **If you match the render against a fixed set of
  shapes, add these.** `#350`.

## #478 — 2026-08-15

- **BREAKING (engine CLI surface)** — `<engine-dir>/reconcile_sessions.sh` gained a
  fourth lane state, **`held`**, and a fourth exit code, **`4`**. A scope is `held`
  when its persisted merge class is `operator` (`<sessions-dir>/<scope>/merge_class`)
  and its open PR is merge-ready by `pr_watch.py`'s own `mergeable`. Exit `4` means
  every launched lane is merged or held with at least one held; exit `0` still means
  every lane **merged**, unchanged, and open or parked still outranks held at exit `3`.
  **If you branch on this script's exit code, add `4`.** A caller that only tests
  `== 0`, or that stops on any non-zero, needs no change; a caller that matches `3`
  exactly will now fall through when a lane is held. `#465`.
- **CHANGED (report shape)** — the tally line grows a `, held H` term, placed after
  `parked K` and before the existing conditional `, open O`. It is emitted **only**
  when `H > 0`, so a batch with no held lane prints `launched N, merged M, parked K`
  exactly as before. **If you parse that line, accept the optional term.** `#465`.
- **CHANGED (engine CLI surface)** — reconciling now invokes
  `<engine-dir>/pr_watch.py` (via `uv run`, `--json --no-persist`, with
  `$DEVKIT_STATE_ROOT` pointed at the lane's own sandbox and `$GH_REPO` pinned to the
  repository the run resolved through `gh`) once per operator-class open lane, plus one
  `gh repo view` to resolve that repository — **once per run when it succeeds**, and
  retried on the next such lane when it does not, so a transient failure cannot cost
  the rest of the batch its `held`. It writes nothing.
  Where `uv` or the engine is absent, where the probe fails or times out, **or where
  that `gh repo view` cannot identify the repository**, the lane reports `open` as
  before and the reason is named on **stderr** — **if you capture stderr, expect that
  block.** A repository the run could not identify is a refusal, never an unpinned
  probe: `env` only adds, so an unpinned probe would inherit the caller's own
  `$GH_REPO`. `#465`.
- **CHANGED (report shape)** — a **second, distinct stderr block** exists: when two
  session directories under `<sessions-dir>/` record the same branch, that branch's
  merge class is ambiguous, so the lane is never classified `held` and a
  `⚠ two sessions record branch '<branch>' (…)` warning names both directories. It
  fires before any probe, so it is not the "could not evaluate" block above. **If you
  match stderr against one expected shape, add this one.** `#465`.

## #477 — 2026-08-15

- **BREAKING (gate semantics)** — `"actionable comments posted: 0"` is gone from
  the engine's `_DEFAULT_NOISE_MARKERS`. A comment body whose only match was that
  string is no longer filtered: it surfaces in `new_comments` and holds
  `converged` false until acknowledged. The direction is fail-closed — this can
  only make the gate stricter — but it is a flip. **If your review bot really does
  emit that wording, put it back in your own `review.noise_markers`**; on this
  repo it had never matched a single comment on any PR.
- **CHANGED (config keys)** — `review.noise_markers` ships one entry shorter, and
  `init.sh` no longer seeds the retired entry into a *fresh* `dev-model.yaml`. An
  existing config is left alone (`ensure_review_key` only adds absent keys), so
  **delete the line from your own config by hand** if you want the new default.
  While you are there, re-check the rest of your list against what your bot
  actually posts today — a marker that matches nothing reports nothing.
  **Do not replace it with CodeRabbit's clean-verdict sentence.** `is_noise`
  matches the body with no author check, so that entry would also discard a human
  comment quoting the bot; `scripts/tests/test_pr_watch.py` now fails if you add
  it.

## #475 — 2026-08-15

- **CHANGED (engine CLI surface)** — `kit_doctor.py`'s two writing flags,
  `--generate-manifest` and `--record-install`, print their `wrote <path>
  (...)` status line to **stderr**, and now suppress it — along with any
  secondary note or warning printed in the same run, e.g.
  `--generate-manifest`'s "listed file(s) absent from this checkout"
  warning — when stderr's current descriptor is the exact file just
  written. That covers the case a stderr-only move does not, e.g. `>
  kit-manifest.json 2>&1` or `&> kit-manifest.json` (#464). Read this
  output from stderr, not stdout. Do not redirect stdout to select the
  output path, and do not merge stderr onto it either — pass `--manifest` /
  `--baseline` for a non-default one; the tool writes its target file
  itself regardless of any redirect, and prints nothing if your redirect
  happens to alias it — including a warning about absent files, so do not
  rely on stderr's absence to mean nothing is missing under such a
  redirect.

## #459 — 2026-08-13

- **BREAKING (gate semantics)** — the #428 guard's snapshot now records a kind
  for every entry the walk yields under `state/`: a symlink at its own path
  with a `symlink -> <target path>` value, the root's own presence as `./`,
  and any entry that is none of link/dir/file as `<special>`. A pytest run's
  exit code now flips on writes that previously passed silently — a symlink
  created, retargeted, or deleted under the real `state/`; a bare childless
  `state/` created by the run; a fifo or socket appearing. This widens what
  the snapshot sees, not everything the guard can conclude — the known
  residuals stay documented in `<engine-dir>/conftest.py`'s own docstrings.
  If your suite deliberately makes such entries, sandbox it via
  `$DEVKIT_STATE_ROOT` before taking the new `<engine-dir>/conftest.py`.

## #453 — 2026-08-13

- **BREAKING (gate semantics)** — the #428 guard is now split across **two** files
  that must be taken **together**: `<engine-dir>/conftest.py` (new, kit-owned and
  tracked in `kit-manifest.json`, so `/upgrade` Step 3 lists it) carries the
  detection half, and `<engine-dir>/tests/conftest.py` keeps the prevention
  fixture. **Taking only the second silently leaves you with no detection** —
  nothing fails to tell you so. Not filed as `ADDED`, whose meaning in this file
  is "new surface you may adopt or ignore": ignoring this one degrades a guard.
- **BREAKING (gate semantics)** — with both files in place, a pytest run's exit
  code now flips on a write into the real `<repo>/state/` for **every** collected
  directory rather than only `<engine-dir>/tests`. **A run of
  `<engine-dir>/lib/state_paths/tests` alone can now fail** with `REGRESSION
  (#428)` where it previously passed. If your vendored suite writes there
  deliberately, sandbox it via `$DEVKIT_STATE_ROOT` before upgrading.
- **BREAKING (gate semantics)** — **any pytest run whose CWD is a test directory
  itself no longer carries the guard**, whatever arguments it is given: `cd
  <engine-dir>/tests && pytest`, `… && pytest test_x.py` and `… && pytest .` are
  all silent on a leak, because pytest resolves rootdir — and with it confcutdir —
  from the cwd, cutting off every conftest above. Invoke the test directories **by
  path, from the repo root or the engine root**, as the Makefile does.

---

## #445 — 2026-08-13

- **ADDED (engine CLI surface)** — `panel_prompt.py --delta-draws <text>`, for a
  **delta pass** only. Renders the author's stated draws (prose class,
  safety-critical boundary) into the lens prompt with the duty to dispute them and
  the one-verdict-line-per-draw requirement `fallback-review-panel.md` asks that
  prompt to carry. An empty value is refused, like every other optional override.
  **Nothing to do unless you assemble delta-pass prompts**: omit the flag and no
  draws section is rendered.
- **CHANGED (engine CLI surface)** — `panel_prompt.py --carry-forward` renders four
  further lines after your text, telling the lens the section is not the author's
  view of the change and to report it as a finding if it reads that way. **A test
  asserting the exact text of a `--carry-forward` prompt must be updated.** Draws now
  go to `--delta-draws`; a full panel's prompt carries neither.
- **CHANGED (engine CLI surface)** — if you also refresh
  `docs/agentic-dev-kit/fallback-review-panel.md`, **every** rendered prompt changes
  whatever flags you pass: the engine quotes that file's contract section verbatim,
  and this PR adds a sentence to contract item **Scratch namespace** (reach the
  namespace by creating a fresh path, never by removing and recreating one). **A test
  pinning a rendered prompt's exact bytes must be updated even if you use no new
  flag.** Take the engine without the doctrine and only the two flags above move.

---

## #412 — 2026-08-10

- **BREAKING (report shape)** — every check row now carries an `identity` key
  (`#95`): the row's creator, `app.slug` for a check run and `creator.login` for a
  status context, empty string when it could not be read. Both backends set it —
  `_rest_check_rows` builds it on the REST path, and `fetch_check_details` sets it
  unconditionally on the `gh` path. **Exact-equality assertions on check-row dicts
  fail.** Add `identity` to the expected dict, or compare only the keys you care
  about.
- **BREAKING (report shape)** — entries in `review_bots["unavailable"]` with
  `surface: "check"` gained `identity` and `trusted` (`#95`). Same remedy as above for
  any exact-dict assertion over them.
- **BREAKING (gate semantics)** — an outage announcement on the **check** surface
  cancels a review bot's pending block only when the row's `identity` is one the
  bot's own tables admit (`#95`): the bot key, its `[bot]` form, any
  `review.bot_author_aliases` entry, or any `review.bot_app_slugs` entry. An
  unattributable row is still **reported** as unavailable, so the fallback-panel
  signal is unchanged, but it no longer clears the block — the bot falls through to
  the ordinary pending path and ages out over `review.bot_pending_grace_minutes`.
  **A test that fabricates an outage check row and asserts the block is cancelled
  must now set `identity`.** The direction is closed, not open: this can only delay a
  merge, never permit one.
- **ADDED (config key)** — `review.bot_app_slugs`, optional. Extra creator identities
  trusted to announce an outage for a bot, for repos whose bot's app slug differs
  from its login. Absent is the normal case; the trusted set is otherwise derived
  from `review.bot_author_aliases`, so a repo that configures its bot by name needs
  no edit.

## #407 — 2026-08-10

- **BREAKING (gate semantics)** — `mergeable` now additionally requires a **settle
  baseline**: the check rollup must have held the same size for at least
  `review.settle_grace_minutes` on this head (`#190`/`#39`). Until it has,
  `merge_blockers` carries an entry **beginning** `check rollup has not settled for
  current head` and always closing with a parenthetical — `(no settle baseline
  recorded)` or `(stable 1.2m of 3m)` — so match on the prefix, never the whole
  string. `mergeable` — and its alias `done` — is `False` while it is present. **A single `build_report` call
  with no `prior_settle_since` / `prior_settle_total` is `mergeable: False` by
  design**, because a missing baseline reads as "the rollup just moved". Adopters
  constructing reports directly in tests must supply both: `prior_settle_total` equal
  to the poll's `checks["total"]`, and `prior_settle_since` a timestamp at least
  `review.settle_grace_minutes` old. In the live poll loop nothing changes except
  latency — `read_settle_since` supplies both from the per-PR state file, and the
  gate opens one grace window later than it used to.

  Read this one before upgrading if you self-merge. A repo whose merge step reads
  `mergeable` is changing what merges unattended. It fails **closed** — the guard is
  additive to `merge_blockers`, so nothing merges that would not have merged before —
  but a `require_ci: false` repo pays the extra poll plus the grace for a guard that
  buys it nothing.
- **ADDED (config key)** — `review.settle_grace_minutes`, optional, default `3`. How
  long the rollup must hold its size before the merge gate believes it is complete.
  An absent key takes the default, so no config edit is required to upgrade.
