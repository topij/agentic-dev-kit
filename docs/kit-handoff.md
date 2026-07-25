# agentic-dev-kit — Living Plan (Handoff)

> **Forward-looking handoff (Principle #1).** Read this at the start of every session
> (`/session-start`); update it at the end (`/wrap-up`). This file — not an agent's
> memory, not a scratch note — is the single source of truth for what's done, in
> progress, and next.
>
> **Why `kit-*.md` and not `handoff.md`:** `docs/handoff.md` is the *skeleton shipped to
> adopters*, rendered from `docs/templates/` by `init.sh`. If this repo pointed its own
> plan at that file, every session block here would ship into adopters' repos and the
> unrendered marker would be gone. An adopter's config uses the plain names; only the
> template repo needs this indirection.
>
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`).

Last updated: 2026-07-25 — Phase 3a shipped: the watch-loop predicate and the merge gate
are now separate, and the schema change that separates them is purely additive.

## Latest session — 2026-07-25

**Theme —** Made the Phase 3 sequencing decision, and it changed under scrutiny — twice.
Both times the correction came from asking what a *stale reader* of the mechanism would do.

- **The blocking problem was not the porting order.** `decide_done` conflated "is there
  more for me to fix?" with "is this authorized to merge?", because `cmd_merge` had no
  other hook — it re-polls `pr_watch --json` and gates on `done`. That conflation, not the
  sequence of ports, is what would have wedged cs-toolkit's nightly fixer (its Step 6.2
  watches to green-and-clean and records no receipt). Fixing it removed a whole phase from
  the plan.
- **#22 merged.** `converged` (watch loop) and `mergeable` (merge gate) are now distinct;
  `dev_session.sh merge` gates on `mergeable`. Tests 196 → 202.
- **The first cut of #22 failed open, and was rejected in review.** It redefined `done` to
  mean watch-convergence. Because `/upgrade` refreshes engines **per file** (`missing` is a
  supported state — a sized-down adoption installs some engines on purpose), a new
  `pr_watch.py` can run against an older `dev_session.sh` whose gate reads `done` — which
  would then have authorized merges on PRs with no review receipt at all.
- **So the schema only grows.** `done` stays an unchanged alias of `mergeable`. Both skew
  directions fail closed; the equivalence is pinned across the whole boolean input space
  rather than by example.
- **CodeRabbit was rate-limited**, so the configured fallback pass ran instead. It found
  three further issues, including a docstring that claimed a compatibility guarantee the
  *function* doesn't provide — the report **key** does.

**Decided**

- Enforce at the merge point, not at `done`. A watch loop asking "anything left to fix?"
  should never be answered "no" only once a review receipt exists.
- A field that a safety gate reads may be added to, never redefined.
- #19 and #23 get designed together — they are the same ambiguity on two surfaces, and
  both run into the informational-check exclusion being load-bearing against wedging.

**Learned**

- **Documentation does not reach a stale reader.** Redefining `done` was safe by every
  local reading of the new code and unsafe in fact, because the component that would have
  been wrong is the one that never sees the new docs. Version skew is not hypothetical
  here: per-file engine upgrades are a supported, documented workflow.
- **An unavailable reviewer can be indistinguishable from a clean one.** CodeRabbit's
  rate-limit arrived as a status-check *description* on a check classified informational,
  so nothing surfaced it (#23). The doctrine's "a blocked bot is an action signal" rule can
  only fire if the outage is detected.
- Reviewing one's own PR satisfies the doctrine's floor, not its intent — recorded in the
  friction log rather than treated as a solved problem.

▶ Next: fix **#19 + #23 together** (Phase 3b) — the queued-vs-unavailable ambiguity, on
both the comment and status-check surfaces. Design constraint: the informational-check
exclusion must keep preventing a wedge on a bot that never reports, so neither can be fixed
by simply letting that check block. Wants CodeRabbit actually available for review.

______________________________________________________________________

## Earlier session — 2026-07-25

**Theme —** Assessed the kit against its own ten principles, then fixed what the
assessment found. Six PRs merged; tests 83 → 188. The recurring shape: **the kit had
written down rules it was itself violating.**

- **Adoption was broken at step one.** `init.sh` shipped mode `100644`, so the documented
  `./init.sh` failed for every adopter. Its narrative-doc seeding was dead code — the kit
  *ships* `docs/handoff.md`, so the "seed only if absent" guard was permanently false and
  everyone started with a `my-project` header and a `<tracker.url — stamped by init.sh>`
  line that `init.sh` never stamped. (#8)
- **An upgrade path now exists, and it was mostly already written.** `init.sh` already had
  `migrate_runtime_schema()`; it had never run anywhere, because `./init.sh` didn't work.
  Fixing the mode unblocked the mechanism. Added `kit.version`, template rendering keyed on
  an unrendered marker, hook installation as a shim (honoring `core.hooksPath`), and
  **probing** `paths.engines` rather than defaulting it. (#8)
- **Engines became kit-owned.** `scripts/lib/kitconfig.py` — a stdlib-only config reader,
  verified byte-equal to PyYAML on the shipped config and on two real adopter configs — let
  review-bot markers, CI policy, and the cron/CI exemption move *out* of the engines and
  into config. Every shipped engine is now dependency-free. That invariant is what makes an
  upgrade a file copy instead of a manual merge. (#8, #9, #16 — closed #5)
- **Four hardcoded-literal bugs fixed.** `pre-push` diffed against a hardcoded
  `origin/main`, so on any repo whose trunk isn't `main` the guard **silently never fired**;
  `pr-watch` could never converge on a repo with no CI; `JOB_NAME` was a Jenkins-ism that
  GitHub Actions never sets. (#9)
- **Claude-side wiring caught up with Codex-side.** All seven commands had no frontmatter,
  so their surfaced descriptions were raw first lines. Added `.claude/settings.json` with
  SessionStart budget hooks and a `PostToolUse` hook that mandates PR follow-through —
  ported from cs-toolkit, which had the better mechanism. (#13)
- **`kit_doctor` + `/upgrade`.** Per-file drift against a hashed manifest, plus the four
  installation checks nothing else performed. Run read-only against the real adopters it
  found `brain`'s live breakage (config `paths.engines` pointing at a directory with no
  engine in it) and `OpenKitchen`'s four drifted files. (#16, #17)

**Decided**

- Engines are kit-owned; config is adopter-owned. Everything else follows from it.
- `differs` never claims a *cause* — a hash mismatch can't distinguish "older version" from
  "hand-edited", and claiming the latter sends someone hunting for edits they never made.
- Re-running `./init.sh` is the supported config upgrade; `/upgrade` handles engines.

**Learned**

- **The kit predicted its own bugs and shipped them anyway.** `dev_session.sh` states "any
  doc that quotes [the lane contract] should quote it, not restate it" — and `parallel.md`'s
  kickoff prompt restated it and drifted from it.
- **I then resolved that drift toward the wrong source.** The kickoff said "mark ready when
  done", the lane contract said "leave it in draft", and I treated the contract as
  authoritative. It wasn't: `CLAUDE-sections.md` — the always-on baseline — says a finished
  PR must *never* sit in draft, because ready-for-review is what triggers the review bots.
  The lane contract was the outlier, and `pr_watch` proves it: `"PR is draft"` is a merge
  blocker, so a `self` merge-class lane obeying the contract could never satisfy
  `dev_session.sh merge`. The contract forbade the exact action its own merge class
  required. Corrected in #21: marking ready is the lane's, landing it is the cockpit's.
  **The lesson isn't "check for drift" — it's that finding two sources doesn't tell you
  which one is right, and I picked by proximity rather than by testing either against the
  baseline."
- **A guard that fails open must be loud.** Three separate silent-no-op bugs this session
  (`origin/main`, the uninstalled hook, `paths.engines`). Silence is indistinguishable from
  "checked and clean".
- **Same bug class, both directions, one session.** `core.hooksPath` was fixed in `init.sh`
  (write side) and then reintroduced in `kit_doctor` (read side) hours later. See issue #15.
- **Queued ≠ unavailable.** A review receipt was recorded while CodeRabbit was merely
  queued, and its four valid findings landed after the merge. `decide_done` can't tell the
  two apart.

✔ Resolved in the session above. The proposed order (merge gate → receipts behind a flag →
wire the fixer → flip) was replaced: the flag existed to defer a breakage caused by `done`
conflating two predicates, so splitting them removed the need for it.

______________________________________________________________________

> Older session entries live in [`kit-handoff-history.md`](kit-handoff-history.md).
