# Handoff History — agentic-dev-kit

Archived session narratives from [`kit-handoff.md`](kit-handoff.md). Keep active direction
and the next step there; this file is append-only history.

## Session log
### 2026-07-25 (Phase 3b)

**Theme —** Fixed #19 + #23 together, and then spent most of the session discovering
that **the fix rounds were more dangerous than the original diff**. Seven review rounds
on #25 alone; every one found something real; five of them found a defect introduced by
the previous round's fix.

- **#25 merged — #19 and #23 closed.** `summarize_review_bots` resolves each configured
  bot to *unavailable* (outage announced on a comment body **or** a status-check
  description — the surface that was invisible) or *pending* (a verdict still coming).
  Pending blocks the merge gate until it ages past `review.bot_pending_grace_minutes`;
  unavailable never blocks and is the action signal. **Nothing reaches `converged`** —
  that is the whole design, and it is what let both be fixed at once.
- **#28 merged — #10 closed.** The state_paths suite failed from inside a lane worktree
  because its fixture cleared every sandbox *env* signal and not the *cwd* one. The
  issue predicted a per-test audit would be needed; it wasn't — every cwd-sensitive test
  already chdirs itself. A mutation pass showed the fix makes the suite *stricter*:
  three tests had been passing by accidentally discovering the real repo root.
- **#29 merged — half of #27.** `review_bots.coverage` reports which commit each bot's
  last review actually saw, and `--record-review` records it as `bots_behind_head`.
  Verified against the real #25, where it reproduces the gap I had had to work out by
  hand an hour earlier. #27 stays open for the shape-change half.
- **#26 and #27 filed** from the friction-log inbox, both with concrete sketches.

**Decided**

- The anti-wedge property lives in `converged` alone. Every new signal feeds the merge
  gate, which already needs an explicit receipt — so a gate can wait, but the poll/fix/ack
  loop can always finish.
- **Report, never gate.** All three new fields (`signal`, `bot_signal`/`override`,
  `coverage`) make an omission legible at merge time and block nothing. The faithful
  version of each risks wedging a repo whose bot is permanently unavailable.
- **Stop patching a mechanism that keeps corrupting.** The `init.sh` marker migration
  produced **three** distinct config corruptions across three rounds, each while its own
  post-conditions passed and it printed success (the fourth round's finding was about
  the *replacement message*, not the surgery). It was deleted rather than patched again;
  `init.sh` now detects the gap and prints what to add.

**Learned**

- **A fix round on gate logic is where the next bug comes from.** Session-wide:
  **13 review rounds across #25, #28 and #29 — all 13 found something.** Seven of those
  findings were defects introduced by the *previous round's fix* (five on #25, two on
  #29), twice at HIGH. **No round on any PR came back empty**; #29's fourth pass found
  no HIGH or MEDIUM but still found four LOW, including a stale comment and a dead-
  argument trap. `safety-critical-changes.md` rule 3 already says to treat "the last
  round found nothing" as provisional — this session never reached that state at all,
  so the practical question is not when the findings stop but what blast radius
  justifies stopping anyway.
- **Stopping has to be calibrated to the blast radius, not the round count.** #25 was a
  merge gate — worst case, an unreviewed PR lands. #29 is a reported-never-gating display
  field — worst case, a wrong warning. Same review doctrine, different stopping points,
  and saying which one applies is part of the merge decision. The `never gates` property
  is what made that judgment available, and it was *proved* rather than assumed — by a
  review pass sweeping report shapes ad hoc, and in-repo by
  `test_review_coverage_is_reported_and_never_gates` plus the 32-combination matrix in
  `test_done_keeps_its_original_merge_authorization_semantics`.
- **Reading is not running.** Three defects were invisible to careful reading and obvious
  on execution — most sharply, CodeRabbit's pending check reports the zero timestamp, so
  the "unmeasurable age fails open" branch was not an edge case but the *only* path that
  bot ever took. The #19 guard was dead code for its own target, and only polling the
  live PR showed it.
- **Mutation testing found what test names asserted and test bodies didn't.** Five
  properties across the session were named in tests or claimed in a PR body and pinned by
  nothing: on #29, anchored author matching, newest-review-per-bot, and the `bots=`
  threading; on #25, the `init.sh` list-style branch and `grep -qi`'s case-insensitivity.
  Each was found by breaking the code and watching the suite still pass.
- **Every whole-file `grep '^  key:'` in a config migration is a bug in two directions**
  — it misses the key at another indent *and* matches a same-named key under an unrelated
  section. This change shipped one of each.
- **Removing a dangerous mechanism does not make its replacement safe.** After deleting
  the list surgery, the replacement *message* still told inline-list adopters to add a
  block item — walking them into the same corruption by hand.

**Open, and owned by nothing yet**

- **#27's other half** — invalidating a receipt when the diff changes *shape*, not just
  when the head moves. The cheap half (visibility) shipped; the faithful half runs into
  the same wedge tension as #19/#23.
- **#26** — the fallback panel. Run manually ~10 times this session (5 rounds on #25,
  4 on #29, 1 on #28), two fresh-context lenses per round. CodeRabbit completed only 3
  reviews across 17 pushed heads, so the panel carried most — not all — of the load; one
  of its 3 was the round that caught the "ACTION NEEDED" bug. Highest-value unbuilt thing
  in the tracker.

▶ Next: **#26** (make the fallback a panel spec). CodeRabbit was rate-limited on nearly
every head all day (3 completed reviews across 17 heads), so the panel carried most of
the review load — and it is still two manual subagent launches per round, ~10 rounds this
session. Two things this session learned belong in its prompt:
require the lens to **execute** the changed paths (three defects were invisible to
reading and obvious on running), and to **mutation-test** new branches (that is what
proved five separate properties were named by tests and pinned by nothing).

### 2026-07-25 (Phase 3a)

**Theme —** Made the Phase 3 sequencing decision, and it changed under scrutiny — twice.
Both times the correction came from asking what a *stale reader* of the mechanism would do.

> **What "Phase 3" and "the cs-toolkit back-port" mean.** cs-toolkit
> (a separate private repo) is where this kit's
> mechanisms originated; the kit generalized them, and the back-port is returning the
> improved versions. Phase 3 is the review-receipt + merge-gate slice of that. The vocabulary
> has never been written down outside this handoff, which made the claim below unverifiable
> from inside this repo — recorded here so the next session doesn't have to reconstruct it.

- **The blocking problem was not the porting order.** `decide_done` conflated "is there
  more for me to fix?" with "is this authorized to merge?", because `cmd_merge` had no
  other hook — it re-polled `pr_watch --json` and gated on `done`. That conflation, not the
  sequence of ports, is what would have wedged cs-toolkit's nightly fixer — its per-lane
  review step (`.claude/commands/nightly-fixer.md` Step 6.2 in that repo) watches to
  green-and-clean and records no receipt. Fixing it removed a whole phase from the plan.
- **#22 merged.** `converged` (watch loop) and `mergeable` (merge gate) are now distinct;
  `dev_session.sh merge` gates on `mergeable`. Tests 196 → 202.
- **The first cut of #22 failed open, and my own adversarial re-read caught it — not
  CodeRabbit, whose pass on that commit raised only a `local`-declaration nit and a test
  nitpick.** It redefined `done` to
  mean watch-convergence. Because `/upgrade` refreshes engines **per file** (`missing` is a
  supported state — "a sized-down adoption omits engines deliberately (one surveyed repo
  installs 2 of 6 on purpose)"), a new
  `pr_watch.py` can run against an older `dev_session.sh` whose gate reads `done` — which
  would then have authorized merges on PRs with no review receipt at all.
- **So the schema only grows.** `done` stays an unchanged alias of `mergeable`, and both
  skew directions fail closed. Note what is pinned where: the *function* `decide_done` is
  held to the pre-split expression across all 32 boolean inputs, but the thing that actually
  protects an older `dev_session.sh` is the report **key**, and that is pinned by a matrix of
  report shapes rather than exhaustively. Worth keeping straight — the same function-vs-key
  confusion is the next bullet's finding.
- **CodeRabbit was rate-limited**, so the configured fallback pass ran instead. It found
  three further issues, including a docstring that claimed a compatibility guarantee the
  *function* doesn't provide — the report **key** does.

**Decided**

- Enforce at the merge point, never at `converged`. A watch loop asking "anything left to
  fix?" should never be answered "no" only once a review receipt exists.
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
- **#22 merged without satisfying review rules 2 or 3, and that should be recorded as a
  violation rather than a compromise.** The doctrine has no "floor" the author's own pass
  can meet: rule 2 says a single-lens verdict is "not a green light", and rule 3 wants
  re-review until a pass finds nothing new — but the fallback's approve was written in the
  same pass that produced `32f3e4f`, so no *independent* review ever covered the final
  commit — the fallback saw that code, but only as the author re-reading their own fixes.
  CodeRabbit's only review was bound to the first commit, before the redesign.
- **A cold-context subagent reviewer found what three self-review passes missed** — a stale
  comment on the merge gate itself (`dev_session.sh` `cmd_merge`), describing the design that
  was rejected. It shipped to `main` in #22 and was fixed in the wrap-up PR (#24), so the
  artifact is visible only in that diff. Authorship anchoring, not capability, is what
  self-review cannot escape.
- A second, adversarially-prompted subagent pass then found nine further issues in the
  wrap-up itself — including this handoff misattributing a test-coverage claim, and the PR
  description still carrying the "floor" framing the diff had already retracted. The two
  lenses overlapped on nothing, which is the doctrine's disjointness claim holding up.

**Open, and owned by nothing yet**

- **#22's merged design has still never had an independent review.** CodeRabbit's only pass
  covered the first commit; the request for a pass over the final design (posted on #22)
  was refused for rate limits again. Re-request it — this is a safety-critical merge gate
  running on a two-lens subagent panel and the author's own reads.
- The two H-severity entries in [`kit-friction-log.md`](kit-friction-log.md) (fallback
  independence; a receipt outliving the design it reviewed) are unfiled. Both now carry a
  proposed fix, so they are issue-shaped — `triage-friction-log` should graduate them rather
  than leaving them in the inbox.

✔ Done — shipped as PR #25 (see the Phase 3b block, swept into this file by the
2026-07-27 archive run). The design constraint held: neither surface's fix
touches `converged`.

### 2026-07-25

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
  baseline.**
- **A guard that fails open must be loud.** Three separate silent-no-op bugs this session
  (`origin/main`, the uninstalled hook, `paths.engines`). Silence is indistinguishable from
  "checked and clean".
- **Same bug class, both directions, one session.** `core.hooksPath` was fixed in `init.sh`
  (write side) and then reintroduced in `kit_doctor` (read side) hours later. See issue #15.
- **Queued ≠ unavailable.** A review receipt was recorded while CodeRabbit was merely
  queued, and its four valid findings landed after the merge. `decide_done` can't tell the
  two apart.

✔ Superseded by the Phase 3a session (PR #22). The proposed order (merge
gate → receipts behind a flag → wire the fixer → flip) was replaced: the flag existed to
defer a breakage caused by `done` conflating two predicates, so splitting them removed the
need for it.

