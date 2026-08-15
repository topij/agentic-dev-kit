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
  `gh repo view` **per run** (not per lane) for that resolution. It writes nothing. Where `uv` or the engine is
  absent, or the probe fails or times out, the lane reports `open` as before and the
  reason is named on **stderr** — **if you capture stderr, expect that block.** `#465`.
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
