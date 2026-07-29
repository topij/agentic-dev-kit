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

Last updated: 2026-07-29 — the inbox graduated for the fifth time (`#151`, merged `494b9eb`); two new
tickets (`#149`, `#150`) and a HIGH whose own fix produced a second HIGH.

## Latest session — 2026-07-29 (the fifth sweep, and a claim that was wrong in both directions)

**Theme —** One merge, four panel rounds, seven isolated lenses (two rounds on `#151`, two on the
wrap-up PR that records it). The sweep itself was never contested by any lens. The durable result is a failure mode the previous session's measurement
predicted but did not name: **an operator's narrow remark, inflated into a stronger claim and
published as operator-confirmed.** The fix for it then over-corrected, and round 2 caught that.

- **`#151` merged (`494b9eb`).** Fifth `triage-friction-log` sweep overall, dated 2026-07-29.
  Seven entries in, seven out: one graduated into two issues (`#149`, `#150`), six routed as
  seven occurrence comments (`#120`, `#138`, `#127`, `#75`, `#71`, `#45`, `#113`). LLM-only mode
  again (`#6` still not vendored). Inbox 203 → 136 against a 150 budget.
- **Two tickets filed:** `#149` (when a claim is corrected, enumerate every surface it was
  published to *at that moment*), `#150` (a scripted text replacement that matches nothing must
  fail, not report success).
- **The HIGH, and the HIGH inside its fix.** The operator said CodeRabbit is *currently* not
  available here. That was published as *"not installed, never exercised, nothing rate-limited"* —
  and then used to file a **structurally-never-reviews** verdict onto `#45`, the issue whose
  entire subject is that such a verdict cannot be made from outside. Both lenses found it
  independently. `#45`'s own body records a **Pro Plus** plan; `Review limit reached` notices sit
  on `#89` and `#99`. The correction then asserted a review count that was really a count of bot
  comments, and round 2 found *that*. Two independent re-derivations of "how many PRs did it
  actually review" disagreed with each other, so **no count was published**.
- **The silent run is twelve PRs, not seven** — `#102`, `#103`, `#104`, `#111` and `#148` were
  never counted. Third consecutive undercount in that series (four → six → seven → twelve). And
  `#151` merged silent too, so it is **thirteen** by the same rule — a lens caught the tally going
  stale inside the sentence announcing it was stale.

**Learned**

- **An operator's remark has a scope, and widening it is the same defect as inventing it.**
  "Currently not available" is not "never installed". The wider version was published on five
  surfaces and read as operator-confirmed on all of them, which is what made it durable.
  `#140` already asks for the command behind *"X is not available here"*; it arguably needs
  widening to cover *"X **is** available here, this much"* — round 2's finding.
- **Correcting a wrong number with a right one is a trap when the number is not recoverable.**
  Reviewed vs. quota-refused vs. silent is not cleanly separable from the comment stream without
  deciding what counts, and each attempt decided differently. Withdrawing the count was the only
  stable move — and the irreducibility is *better* evidence for `#45` than any count.
- **Deleting beat correcting, again — and it is now two-for-two.** Five review rounds across two
  sweeps have gone to the marker's verification section, every one finding the prose claiming more
  than the checks did. This session cut it rather than correct it a third time.
- **A check that errors can report a pass.** A closing-keyword scan built on a `grep -E`
  alternation with an empty branch was rejected by `ugrep`, exited non-zero, and the `|| echo
  clean` branch fired — printing a clean result from a check that never ran, inside the step
  guarding `#71`. A second run scanned a zero-byte surface and also read clean.
- **`#75`: 4 of 4 lens launches again**, all self-corrected. No running total is claimed; the
  addendum posted this session declares the existing tallies approximate and unreconcilable.
- **The check harness was left unfixed on purpose.** Round 2 showed checks 4/5 have headings
  larger than their assertions and that checks 1+2 share no trust chain (a forged snapshot yields
  byte-identical output). Documented, not repaired — building a harness inside a fix round is the
  mechanism-creep the panel doctrine warns against, and `#138`/`#127` exist to ask for it.

**Open, and owned by nothing yet**

- **`#149` and `#150`** — this session's two. `#149`'s own six-surface list **omits PR comments**,
  found by a lens after a retracted claim survived on one; that gap is unrecorded on the issue.
- **`#121` should absorb the config-placeholder question** rather than have it re-filed. This
  session re-derived `#121` from scratch without noticing it, and the rewrite of that entry then
  made a *larger* false claim than the one it corrected. The live inbox entry now routes there.
- **`#138` and `#127` are still the pair that would make a sweep's claims mechanically checkable**,
  and both were reproduced *again* inside this session's pilot run of them.
- **`#73` gained a *new* instance from this session's own archive sweep**, in the other direction:
  `kit-handoff-history.md` now says *"the 287-line figure **above**"* while that figure stayed in the
  live handoff. A lens found it; an earlier draft of this bullet claimed the *predicted* instance
  instead, which was the previous session's. Recorded in no routing row.
- **`#33`, `#112`, `#132` housekeeping is unchanged** from the previous session; `#132` is closed,
  so cs-toolkit Phase 2 blockers remain `#41`/`#37`/`#134`.
- **The inbox is back over budget the same day it was swept** — 179/150. The sweep took it 203 →
  136; wrapping up added four more entries and took it to 179. Not swept inline, per the
  wrap-up contract: graduating needs tracker writes and operator approval. Worth noting that a
  sweep now buys roughly one session of headroom, which is an argument for `#6` (vendor the
  engine) becoming urgent rather than merely open.

▶ Next: `session-start` — the threads are genuinely diffuse (two fresh tickets, two observations
recorded nowhere but here, and unchanged housekeeping), and nothing in the inbox is urgent despite it
being over budget. Page the tracker at `perPage: 25` reading `number`/`title`/`labels`/`state`
only — `#143` records `session-start` overflowing its tool limit at 68 open issues, and there are
~82 now.

______________________________________________________________________

## Earlier session — 2026-07-29 (the second sweep, and a documentation audit)

**Theme —** Two merges and nine panel rounds. The deliverables are routine; the durable
result is a measurement: **across nine rounds and at least fifteen isolated lenses, no HIGH finding
was ever in executable behaviour.** Every one was in prose — some of them inside `.py`/`.sh`
files, so "prose" means wherever it lives — and the prose that kept failing was the prose
*about* the verification, not the verification.

- **`#144` merged (`cdeae7a`).** Second `triage-friction-log` sweep dated 2026-07-28.
  Fourteen entries in, fourteen out: seven graduated into six issues (`#138`–`#143`), seven
  routed as five occurrence comments. Run in LLM-only mode again (`#6` still not vendored).
  Per `#128`, the graduation marker carries the approval record the DM would have — proposals,
  decisions, snapshot digest — plus an explicit statement of what its checks do *not* establish.
  Inbox 196 → 101 against a 150 budget.
- **`#147` merged (`030f053`).** Every prose surface audited against the engines, config,
  manifest and Makefile. The one that would have bitten: `CLAUDE.md` told the cockpit to branch
  `dev/<scope>`, the exact prefix `pre-push` refuses for narrative-file edits. Also corrected:
  `README`'s pytest command, a lane-sessions dir that does not exist, `path <scope>` documented
  as printing the sandbox when it prints the worktree, two live hooks and the `.mcp.json` lane
  copy documented nowhere, and `--assert-draft`/`--assert-ready` described as read-only checks
  when they *mutate* the PR.
- **Eight tickets filed:** `#138` (routing claims unverified), `#139` (`pr_watch.py:687`
  discards the 403 body), `#140` (extend `#54` to mechanism claims), `#141` (removal
  enumeration must be per-item and executed), `#142` (counterfactual step when a round removes
  a guard), `#143` (`session-start` overflows at 68 issues), `#145` (three config keys read by
  no code), `#146` (`parallel-headless.md` linked but untracked).
- **`#145` was closed by accident and reopened.** `#147`'s squash message read *"Filed rather
  than fixed:"* followed directly by the reference; GitHub matched it and closed the issue
  (`events` shows
  `closed commit_id=030f053`). The sentence asserted the opposite. This is `CLAUDE.md`'s
  closing-keyword ground rule and `#71`, firing in a session that was scanning for it — the scan
  never ran on a squash message. Occurrence data on `#71`.

**Learned**

- **The record about a change is a bigger defect source than the change.** The sweep moved the
  right bytes on its first commit and no round found otherwise; three rounds went to the record.
  The audit's edits were nearly all correct; three rounds went to its evidence. **Three** HIGHs
  were in prose that *ships* — `pr-watch.md`'s flag table, `devmodel_config.py`'s docstring, and
  the prerequisite list, which was wrong on **two** surfaces (`init.sh`'s `# Requires:` header and
  `README.md`). That is the class worth separating from the rest.
- **Correction-by-surface is the failure mode.** The same false `#23` sentence was fixed in the
  friction log (R1), found still live on `#45`'s comment (R2), then still live in `#140`'s issue
  body (R3). R4 found a fix that had silently matched nothing while its commit message reported
  it as landed.
- **Deleting beat correcting.** Two rounds of correcting the verification transcript each added
  prose and each added defects. Removing it took the file 141 → 93 and the defect surface with it.
- **A check heading is a claim.** "Every claimed comment exists on the issue it claims" asserted
  existence, author and timestamp — never content, which is how the `#23` HIGH survived a round.
  The integrity check was an unanchored substring test; a lens passed it against an archive whose
  visible text was destroyed and whose real bytes hid in an HTML comment.
- **`#75` is unanimous.** *Every* lens launch this session landed on `main` with an empty diff and
  self-corrected, because the launch prompt made reporting path/sha/diffstat mandatory *before*
  reviewing. A running count is not worth recording — the lens that reviewed this claim reproduced
  it too, so any total is stale on arrival. **At least 15, no exceptions** is the durable form.
- **CodeRabbit: seven consecutive PRs with no check and no comment** (`#126`–`#147`).

**Open, and owned by nothing yet**

- **`#138`, `#139`, `#140`, `#141`, `#142`, `#143`, `#145`, `#146`** — this session's eight,
  enumerated rather than written as a range, because `#138`–`#146` spans `#144` (a PR, not a
  ticket) and hides any member's state from a `#N` sweep. That is how a closed `#145` sat published in this
  list for ~13 minutes (closed `22:09:27Z`, list pushed `22:15:26Z`, reopened `22:28:07Z`). `#138` and `#127` are the pair that would make a sweep's own claims
  mechanically checkable — `#138` filed here, `#127` two sessions back — and both were
  reproduced inside this session's pilot run of them.
- **The friction inbox is well back over budget** — 203/150, from this session's seven
  entries. Another `triage-friction-log` sweep is due, and `#113`'s hazard has a **latent** *state-path*
  instance: `state/triage/frozen-inbox_{date}.json` would collide on a same-day re-run, and does
  not today only because the engine that writes it is not vendored (`#6`).
- **`#132`–`#136` from the previous session** — `#132` is **closed** (shipped `2026-07-28`), so
  the cs-toolkit Phase 2 blockers are `#41`/`#37`/`#134`. `#133`, `#135`, `#136` remain open.
- **`#33` and `#112` are shipped but still open** — close them deliberately after confirming
  `#131` is what each asked for.

▶ Next: `triage-friction-log` — **discharged** (`#151`). The inbox was 196/150, the same tripwire that opened this
session, and its seven entries are the freshest evidence behind `#120`, `#138`, `#127` and `#71`.
Prefer it over `session-start` this time: `#143` (filed here) records that `session-start`'s
tracker step overflowed its tool limit at 68 open issues and that the remedy it prescribes cannot
be run on this backend — there are ~80 open now, so page at `perPage: 25` and read
`number`/`title`/`labels`/`state` only if you do run it.

______________________________________________________________________

## Earlier session — 2026-07-28 · 4 (the mutation gate shipped; four panel rounds)

**Theme —** Two merges and a review loop that would not converge. The mechanism is small;
the durable result is a measured account of how a guard test can be defeated four times
running, and of a general argument being applied to instances it did not cover.

- **`#130` merged (`e8e7789`).** The `pr_watch` 403 entry from `#126` had the diagnosis
  right and the remedy wrong: it treated the proxy's *"an org admin must connect the
  Claude GitHub App"* body as actionable. It is a canned string — this is a personal repo
  with no org admin, and GitHub access was enabled throughout. Established by running the
  commands: `GET /user` returns `topij` **with the sentinel and with no auth header at
  all**; `/repos/*` and the public `/octocat` both 403; `documentation_url` is
  `docs.anthropic.com`. A path allowlist, not a credential problem.
- **`#131` merged (`9fb4baa`).** `driftcheck` marker on the byte-comparison test,
  registered in a new `scripts/tests/conftest.py` so it travels with vendored tests;
  `make mutation-test`; `fallback-review-panel.md` item 5 rewritten repo-agnostic with the
  rule that does not depend on any of it — **a kill is only a kill if a test asserting
  behaviour is what failed**. `#112`'s item 1 satisfied by construction; item 2 declined
  with reasons on the issue.
- **Five tickets filed:** `#132` (`/upgrade` cannot deliver anything under
  `scripts/tests/`), `#133` (the converse marker guard, with live instances on `main`),
  `#134` (kit tests hardcode `parents[2]`, so they fail in the `scripts/devkit/` layout),
  `#135` (a conftest `collect_ignore` is the one narrowing vector CI cannot catch),
  `#136` (panel lenses collide in the shared scratchpad, and copying a worktree is not
  isolation).

**Learned**

- **A guard test over an unbounded space cannot be finished.** Four rounds, four sets of
  HIGHs: a literal parked in a `#` comment; the first `target:` block read while make runs
  the last; `--deselect`/`-k`/`-k` with no space/`--ignore=`; symmetric narrowing; a
  dropped `.PHONY:` token. Every round's fix was the next round's finding — `rule 1`'s
  pattern, and severity never fell below three HIGHs.
- **But the general argument was applied to instances it did not cover.** "A text search
  cannot be sound" is true, and two of the three tests deleted on that basis were built on
  `make -n` — an *execution* probe. Deleting them opened the one hole the change existed
  to close: with the flag silently dropped from the recipe, the full suite stays green and
  a behaviour-only mutation then reads as a **kill**. The adversarial lens proved it by
  restoring the deleted assertions into every bypass and watching them kill each one.
- **My commit messages were the dominant defect, again — fourth session running.** Two
  measured figures were real and their write-ups under-specified what produced them (a
  "single module" narrowing that was partial; a `.PHONY` mutant needing an unstated
  flag duplication). Also promoted an *attested* 17/17 figure to "measured" **in the same
  commit that demoted it elsewhere**.
- **CodeRabbit registered nothing on four consecutive PRs** (`#126`, `#129`, `#130`,
  `#131`). The fallback panel was the only independent pass on all of them.
- **`pr_watch` cannot arbitrate the merge gate in a web container at all** — the whole
  API host is path-blocked — so both merges were reconstructed from MCP calls.

**Open, and owned by nothing yet**

- **`#132`–`#136`** — that session's five. `#132` and `#134` both land on the `scripts/devkit/`
  layout. *(`#132` has since closed — see the latest session's open list.)*
- **`#113` gained a third occurrence** — `chore/update-handoff-2026-07-28` already existed
  on the remote again; avoided by hand, still no mechanism.
- **`#33` and `#112` are shipped but still open** — close them deliberately after
  confirming `#131` is what each asked for.

▶ Next: `session-start` — **discharged**; the following session ran `triage-friction-log` and a
documentation audit instead. The cs-toolkit Phase 2 blockers named here were
`#41`/`#37`/`#132`/`#134`; `#132` has since closed.

______________________________________________________________________

## Earlier session — 2026-07-28 (the inbox graduated; the panel audited the record)

**Theme —** One deliverable, and a review panel that spent almost all of its findings on
the record rather than the sweep. The graduation is the small half; the durable result is
that the sweep's own accounting did not survive an audit, and that no gate in the repo can
tell a sweep from a deletion.

- **`#126` merged (`2d99593`).** The 24 un-graduated entries swept into
  `kit-friction-log-archive.md` behind a graduation marker; inbox 287 → 28 against a 150
  budget it had been over for three sessions. Routing: **13 graduated** into `#112`–`#120`
  and `#122`–`#125`, **10** routed as occurrence comments on issues that already existed,
  **1** discharged (`make test` discoverability, answered by the root `CLAUDE.md`).
- **Run in LLM-only mode.** `triage_friction_log.py` and `finalize_triage.py` are not
  vendored (`#6`), and `notify.user_key` is blank, so parse/draft/sweep were done by hand
  and the approval loop ran in-session instead of over DM.
- **`#121` came from running the workflow, not from the inbox** — the `tracker:` block in
  `dev-model.yaml` is still `init.sh` placeholder pointing at Linear, which `#6`'s engine
  will read the moment it lands.
- **CodeRabbit never reviewed `#126`** — no check, no comment, past its grace window. The
  fallback panel was the only independent pass.

**Learned**

- **The sweep's accounting did not survive an audit, and both lenses found the same
  defect.** The occurrence list named `#33`, summing to eleven against a stated ten, so an
  auditor checking "24 in, 24 out" got 25 with one entry double-counted. `#33` had received
  a cross-reference to `#112` — a *graduated* entry already inside the thirteen. Rated HIGH
  by the correctness lens; found independently by the adversarial one.
- **No gate in this repo can distinguish a sweep from a deletion.** Wiping both narrative
  docs to 3-line stubs leaves `make test` at 495 passed, `kit_doctor` at 0 differ, and
  `check_doc_budget` **greener** than the real branch (3/150 vs 28/150). Both files are
  `ADOPTER_OWNED`, so the drift check never compares them. Filed as `#127`.
- **A documented unconditional stop was bypassed and defended with the wrong rule.** The
  skill's notify-channel stop is absolute; the justification written into the PR body
  belonged to the non-interactive execution-context rule instead. Because `state/` and
  `reports/` are gitignored, no artifact of the proposals or the approval exists. Filed as
  `#128`, self-reported.
- **Both panel worktrees pointed at the wrong ref — 2 of 2.** Both lenses detected and
  corrected it because the launch prompt required verify-before-review. First occurrence
  set in this repo where *every* launch was wrong rather than right, so it cannot be
  folded into the earlier "8 of 8 correct" figures.
- **Four of the panel's ten findings were defects in the PR body itself**, including a
  verification claim naming no command — in the PR that files the issue about exactly
  that. Third consecutive session where the prose, not the change, carried the errors
  (`#120`).

**Open, and owned by nothing yet**

- **`#112`–`#128`** — this session's sixteen. `#112` (the manifest-hash gate is not
  coverage) is the highest-leverage: it invalidates every mutation claim over a
  `KIT_OWNED` file. `#127` and `#128` are the panel's own.
  **Superseded remedy —** this line used to end "until the regenerate-first step is
  mandatory", which is `#112`'s own proposed item 1. A later session took the opposite
  route: the drift test carries a `driftcheck` marker and is deselected *inside
  `make mutation-test`*, so there is no manifest gate left to discharge there and
  regenerate-first is deliberately *not* recommended
  (`fallback-review-panel.md` item 5 says so). Corrected here because a living plan that
  points the next session at a rejected remedy is worse than one that says nothing.
- **`#113` gained a second occurrence** — this session was a same-date second session, so
  `chore/update-handoff-2026-07-28` already existed on the remote. Avoided by branching
  off fresh `main` under a different name rather than by any mechanism.
- **`#75` gained a 2-of-2 occurrence set**; `#73` gained an instance the archive now
  carries deliberately (a swept self-link, left byte-identical to preserve the verbatim
  property).
- `#6`, `#33`, `#45`, `#54`, `#74`, `#76`, `#77`, `#93`, `#95`, `#97`, `#98` and the rest
  per `session-start`.

▶ Next: `session-start` — the threads are diffuse (sixteen fresh tickets, no in-flight PR,
nothing blocking), so let it re-read the tracker and propose. If you want one now: `#112`,
because every future mutation-testing claim depends on it.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

