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

## #453 — 2026-08-13

- **BREAKING (gate semantics)** — the #428 guard is now split across **two** files
  that must be taken **together**: `<engine-dir>/conftest.py` (new, kit-owned and
  tracked in `kit-manifest.json`, so `/upgrade` Step 3 lists it) carries the
  detection half, and `<engine-dir>/tests/conftest.py` keeps the prevention
  fixture. **Taking only the second silently leaves you with no detection** —
  nothing fails to tell you so. Not filed as `ADDED`, whose meaning in this file
  is "new surface you may adopt or ignore": ignoring this one degrades a guard.
- **CHANGED (gate semantics)** — with both files in place, a pytest run's exit
  code now flips on a write into the real `<repo>/state/` for **every** collected
  directory rather than only `<engine-dir>/tests`. **A run of
  `<engine-dir>/lib/state_paths/tests` alone can now fail** with `REGRESSION
  (#428)` where it previously passed. If your vendored suite writes there
  deliberately, sandbox it via `$DEVKIT_STATE_ROOT` before upgrading.
- **CHANGED (gate semantics)** — **any pytest run whose CWD is a test directory
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
