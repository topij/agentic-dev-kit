# Handoff History — agentic-dev-kit

Archived session narratives from [`kit-handoff.md`](kit-handoff.md). Keep active direction
and the next step there; this file is append-only history.

## Session log
### 2026-07-30 (one flag, six rounds, and a bug older than the PR)

**Theme —** `#74` shipped. The durable results are two: the review found a **pre-existing
data-loss bug in the tool that owns this file**, and it measured where six rounds of its own
effort actually went.

- **`#160` merged (`85cdeb0`).** `archive_plan_sessions.py --target-lines N` sweeps oldest-first
  until the handoff is at or under a *line* budget, so the remedy `check_doc_budget` names can
  actually discharge it — `--keep` counts blocks and was a no-op at its default. `budget_line_count`
  makes both tools measure a line the same way; `check_doc_budget` substitutes `{budget}` so the
  number lives in one place. **28 new test functions / 31 cases** (`--collect-only`: 56 → 87).
  Verified in production at this wrap-up: 419 → 355 lines.
- **`#164` filed — the find of the session, and it is NOT fixed.** `Path.write_text` truncates
  before writing, so a failed write destroys the document and the handler still prints *"no changes
  applied"*. Measured on a real full filesystem: a **26,807-byte handoff went to 0 bytes** while the
  tool reported nothing had happened. Latent in the archive engine all along.
- **`atomic_write` was attempted for it and REVERTED** — four HIGH regressions, found independently
  by both lenses: `os.replace` replaces a symlinked doc rather than writing through it, file
  mode/ownership reset every sweep, a fixed temp name lets concurrent runs publish each other's
  bytes, and a pre-existing temp symlink becomes an arbitrary-file clobber. All silent, all at
  exit 0.
- **The mitigation that shipped instead was itself defective three times, which is the session's own
  thesis biting the session.** `02c70ac` — `--help` still promised a rollback the first write never
  gets, a sentence true only while `atomic_write` existed and left standing through the revert.
  `15c8651` — the check named `<handoff>`, but under ENOSPC the *history* fails and the handoff
  rolls back clean, so the instruction **green-lit the damage it was written to catch** (measured:
  an archive committed at 12 of 39 sessions). `37aebd9` — the recovery said
  `git checkout -- <handoff>`, which discards this session's own block.
- **Also filed:** `#161` (LOW imprecisions; **two mutants still survive** — the megaline trim and
  `--target-lines < 1`), `#162` (the sweep is not byte-preserving), `#163` (where the review cycles
  went).

**Learned**

- **A fix stops at the first site**, and it is not a prose problem. The sharpest was
  `(OSError, UnicodeDecodeError)` applied to one of two exception classes *on the same line*,
  leaving exit 1 producible against a contract admitting only 0/2/3 — with the correct fix already
  sitting in `check_memory_budget.py:192-197` under a comment giving the reason. `#163` enumerates
  five occurrences; the PR's 13 commits carry more, **twice inside a fix for this very pattern**.
  Counts on `#163` predate rounds 5–6 and were not refreshed — treat the issue as the record and
  this line as a pointer.
- **A fix round that adds a new mechanism is where the next HIGH comes from.** Three times across
  seven review passes: round 2's `.format()` template → round 3's crash; round 5's `atomic_write` →
  round 6's four HIGHs → reverted; round 6's mitigation paragraph → the confirmation pass. The
  doctrine already says a new mechanism gets filed however squarely a finding prompted it; this is
  the measured version of why.
- **A hypothesis was stated as falsifiable and refuted within one round.** Apparent lens
  specialisation (adversarial finds mechanism, correctness finds prose) was coincidence — round 5's
  correctness lens led with a mechanism defect. On `#163` rather than dropped, because doctrine
  built on it would have rested on nothing.
- **Execution found the bugs that mattered; reading found more of them.** The filled ramdisk,
  `RLIMIT_FSIZE` and a planted symlink produced `#164` and the `atomic_write` HIGHs — nothing else
  would have. But the one-of-two-sites class, which is most of the session's fixes, was found by
  reading. The fuzz harnesses lived in session scratch and are gone: those runs are attestations,
  not reproducible evidence.

**Open, and owned by nothing yet**

- **This handoff block was itself panel-reviewed, and both lenses found it flattering.** It
  originally described the fallback mitigation in one sentence while three commits fixed defects in
  it, carried a stale test count, and asserted `#163` figures that contradicted `#163`. Corrected
  here. **The merged tree of `#160` was never seen by a lens** — the final panel reviewed `84dc129`,
  three doc/test commits followed, and the PR's review record says so explicitly (`#27`).
- **`#42` reproduced at merge time** on `#160`: posting the review record un-converged it
  (`review_evidence.valid: true`, blockers empty, `mergeable: false`) and needed `--mark-seen`.
  Occurrence data on the issue, not the inbox.
- **`#73` gained a new instance from this session's sweep** — the moved block says *"see the latest
  session's open list"* about `#132`, which resolves to nothing inside the history file. Not
  repaired here; recorded so the count is honest.
- The inbox is **168/150** and unchanged: today's friction went to the tracker (`#161`–`#164`),
  the routing Principle #2 prescribes. The guard-chaining rule (`check && act`) is the one entry
  that lives only there.

▶ Next: **`#163` Sink 1 + `#75`** — every lens run this session (18 of 18) sat on the base commit
with an empty `origin/main...HEAD` diff and re-derived a workaround. But the cheap fix is not the
`git archive` recipe: worktrees share the object store, so `git diff origin/main...<sha>` and
`git show <sha>:<path>` work directly, and the archive recipe was *refused by the sandbox* for one
lens. So: teach the launch prompt to diff against the **named sha** rather than `HEAD` (`#163`
Sink 1), and invert contract item 7 as `#75` actually asks. Then `#124`.

**Then the cs-toolkit thread, and note the vocabulary:** Phase 2's blockers remain
`#41`/`#37`/`#134` as the live blocks below state — all three still open, nothing discharged them.
What this session added is the argument that `#47` is their common cause, and that a prerequisite
slice (`#112`, `#33`, `#133`, `#135`, `#107` — the mutation/drift gate) should land first so the
verification everything after it relies on is trustworthy. That slice is a proposal, not an
established gate; `#164` also remains unfixed and the wrap-up sweep touches that code every session.

### 2026-07-29 (the sixth sweep, and three rounds that all found the same thing)

**Theme —** Three PRs merged. The result worth keeping is narrower than it first looked: across
three review rounds on one change, **justification prose was wrong in every round** — a recurring
defect category the mechanism's own tests cannot catch. Mechanism defects were found in every round
too; the first draft of this block claimed otherwise and a lens refuted it from the commits.

- **`#156` merged (`3d503c2`).** Sixth `triage-friction-log` sweep. Five inbox entries in, five
  accounted for: `#155` filed (a remark attributed to the operator must be quoted at its original
  scope) plus seven occurrence comments. Friction log 179 → 133 lines.
- **`#157` merged (`e9773ba`).** `#121`'s two halves. A gitignored `config/dev-model.local.yaml`
  merged over the tracked config for **`notify.user_key` only**; `tracker.*` stamped in the tracked
  file with a guard so no adopter inherits it — a non-interactive `init.sh` refuses a
  `project_name` that does not match the checkout's origin remote. Three adopter-facing defects
  fixed on the way: `/adopt` never seeded the ignore rule and never runs `init.sh`; the rule
  covered one filename while the loader derives `<name>.local.<ext>` for any path; and
  `add_ignore_line` turned a `.gitignore` ending `.env` into `.envstate/` across six call sites.
- **`#158` merged (`e76dd2c`).** `fallback-review-panel.md` now names the three failed
  stopping-rule designs, in addition to pointing at the fuller accounts, and separates a question they do not answer:
  **lens count is not bounded by class**, and the only sanctioned single-lens pass is Degraded
  mode, conditioned on runtime capability rather than on what the change contains.

**Learned**

- **Justification prose was wrong in all three rounds.** `_deep_merge`'s docstring said "two
  shapes" while implementing six; the overlay allowlist said its keys are "read by no shell reader"
  while `init.sh` read exactly them; a list rule was motivated by a key the same file asserts can
  never be set. It is written from *intent*, and intent is the one thing a reviewer cannot check
  against the code — nor can a test, which is why it recurred while the mechanism's defects were
  each fixed once. Correcting it added surface the next round then found defects in; **deleting it
  ended the loop**. That is the claim, and it is narrower than "the mechanism was never wrong",
  which a lens refuted: every round also found real mechanism defects, including three
  adopter-facing ones this block lists above.
- **One of the two late bugs was a regression from the previous round's fix, not both.**
  `pr_watch` re-raising at module import came from round 2's change and killed `--help`. The
  valueless-key-wipes-a-list hazard did not: round 1's guard was map-only from the start, so that
  route predates round 1 and survived it. The first draft claimed both, on four surfaces.
- **Generality was the defect, not the merge logic.** A config overlay honoured by one of several
  readers diverges everywhere. Narrowing to one key closed five findings at once — and `tracker.*`
  had to be removed after it made `session-start` on this repo query a project named
  "My Project Dev".
- **A single lens is a real pass.** One correctness lens on an 18-line docs change found six
  substantive issues, including a gloss that was roughly the inverse of what it described.
  Recorded as `fallback:claude`, not `fallback:panel`; the engine's own warning that one lens is
  not a green light is on the receipt.

▶ Next: `session-start` — several threads are open (`#121` still wants the friction-log header read
from config; `#124` and the `finalize.pr_draft` default now contradict the stated preference that
PRs not sit as drafts) and none is obviously first.

### 2026-07-29 (three failed designs, and what shipped instead)

**Theme —** An attempt to stop the previous sessions' review spirals. It failed three times, and
the failures are the result worth keeping.

- **`#153` merged (`b46f794`).** `fallback-review-panel.md` gains one section of *authoring*
  guidance — keep the record short, put detail in the PR, shorten a record that has needed
  repairing twice, and treat adopter-executed prose, commit messages and any record standing in
  for a control as first class. It loosens no control and says so explicitly. It also gave
  `workflows/pr-watch.md` the panel's missing precondition — that criterion applies only when the
  review bot is unavailable — and separated the poll/fix loop bound from per-change review rounds.
- **Three designs died first**, each killed by a panel on a real hole: a class defined by file
  type inside a section organised by function; the same class with functional tests, which the
  handoff passed while being the file the next session is told to act on; and a class-independent
  stop signal that beat the first class and whose trigger the author sets by choosing how verbose
  the fix round is.
- **Global git identity corrected** — `user.email` was `topi.jarvinen@gmail..com` (double dot) and
  `user.name` lacked its umlaut. Five commits from 2026-07-05/15 carry it; nothing from these
  sessions does, because GitHub's squash attribution used the account identity. Not rewritten.

**Learned**

- **Any rule whose trigger the author sets is a control the author can opt out of.** All three
  designs were versions of that, and the third one self-immunised: the commit proposing it
  rewrote the section, which by its own test made every later finding "prose the last fix wrote".
- **The premise was wrong.** "The record rounds did not earn their keep" does not survive: they
  caught a falsely closed issue, a false claim published to two tracker surfaces, and a falsified
  operator-approval record. The waste came from records being *elaborate*, not from being
  reviewed — and deleting prose (141 → 93 lines) is the only intervention that provably worked.

**Open, and owned by nothing yet**

- **The inbox is 179/150** and a sweep is due — the **fourth** consecutive session ending over
  budget (196, 203, 179, 179 since `06490a1`, against a budget of 150 throughout).
- **`#120` now carries this session's findings** — it proposes the cheaper terminal check these
  three designs were attempts at, so the reasons they broke are recorded there rather than only
  in this block.
- `#149`, `#150`, `#145`, `#146`, `#138`, `#139`, `#140`, `#141`, `#142`, `#143` and the rest per
  `session-start`.

▶ Next: `triage-friction-log` — the inbox has been over budget for four sessions. **Caveat before
running it unattended:** `notify.user_key` is blank, so the workflow stops at Step 2 by design; the
in-session-operator path is open regression `#128`, and `#124` records that its default draft PR
goes to a reviewer that will never read it.

No friction entries were added this session on purpose, and only one of the two lessons is in
doctrine: the record-length one is in `fallback-review-panel.md`, while *"any rule whose trigger
the author sets is a control the author can opt out of"* is recorded on `#120` — the tracker, not
the inbox, because it is the constraint any future attempt at that ticket must satisfy.

### 2026-07-29 (the fifth sweep, and a claim that was wrong in both directions)

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

### 2026-07-29 (the second sweep, and a documentation audit)

**Theme —** Two merges and nine panel rounds. The deliverables are routine; the durable
result is a measurement: **across nine rounds and at least fifteen isolated lenses, no HIGH finding
was in executable code** — one was in a squash message, which closed an issue before any round
found it (see below), so prose is not the same as inert. Every one was in prose — some of them inside `.py`/`.sh`
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

### 2026-07-28 · 4 (the mutation gate shipped; four panel rounds)

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

### 2026-07-28 (the inbox graduated; the panel audited the record)

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

### 2026-07-28 (`#92` shipped; the record corrected; five panel rounds)

**Theme —** Two deliverables, and a five-round panel that spent most of its findings on
this branch's own claims rather than on the code. The `AGENTS.md` template is the small
half; the durable result is a data-loss bug caught before it shipped and a much sharper
picture of where self-review fails.

- **`#104` merged (`985dcd0`), closing `#92`.** `docs/templates/AGENTS.md.tmpl` — the
  Codex entry point — rendered by `init.sh` through the same seed guard as the narrative
  docs, with two new tokens (`{{PROTECTED_BRANCH}}`, `{{HANDOFF_PATH}}`, repo-relative).
  `KIT_OWNED` row in, manifest 25 → 26. The verification command is deliberately a
  fill-me placeholder, not a token: `init.sh` knows no such value, so rendering one would
  have meant guessing (`#110` tracks giving it a real config key).
- **Seven corrections to the permanent record**, each re-verified against its primary
  source before editing rather than taken from the review that prompted them.
- **The rule-citation count went six → nine → ten.** Nine was itself wrong; the miss was
  `scripts/kit_doctor.py:101`. Two isolated lenses reached ten independently.
- **A live data-loss bug, caught pre-merge.** `seed_doc` matched the unrendered marker
  *anywhere* in a file, so any in-use doc that merely quoted the marker in prose was
  silently overwritten — no backup, run still printed "seeded". Reproduced against the
  pre-fix script on both a hand-written `AGENTS.md` and a rendered `kit-handoff.md`. The
  marker now counts on line 1 only, in `init.sh`, in `kit_doctor`, and in the tests.

**Learned**

- **Three separate pieces of new behaviour shipped unpinned** — the seeding call, both
  token substitutions, and later the `kit_doctor` predicate. Each survived the full suite
  when deleted. The manifest-hash gate reads as coverage and is not: it is discharged by
  one documented regenerate command, after which the mutant is green.
- **A fix round introduced a regression while fixing that same class.** Aligning
  `kit_doctor` with `init.sh` via `Path.read_text()` swapped one divergence for another,
  because universal-newline translation ends a "first line" at a lone CR where `head -n 1`
  ends only at LF. Round 3 caught it; round 2 had asserted the two matched "exactly".
- **A test can certify destroyed data as fine.** The line-1 assertions used
  `splitlines()[0]`, which breaks on nine separators production does not. A `U+2028`
  before the marker passed the suite while `init.sh` would seed over the live plan.
- **Rounds 1–4 each found a false claim in the previous round's fix**, most of them mine:
  a fabricated rationale in a test docstring, a "harmless" characterisation of a bug that
  was destroying data, a verification claim whose setup step was omitted, a side-effect
  claim whose cited command was scoped narrowly enough to hide the difference, and four
  consecutive sweeps declared complete that were not. The pattern is specific: the errors
  cluster in prose *about* verification, not in the verification itself.
- **Two lenses beat one, twice.** Round 3's correctness lens explicitly cleared the CR
  case as "behaviourally equivalent for all realistic inputs" — it had tested CRLF but not
  CR-only, where the adversarial lens proved divergence by execution. A lens's "verified
  clean" is worth exactly the edge cases it ran.
- **Convergence is visible when it happens.** Round 5 came back clean on the code: 4000
  randomized byte documents and a 30-cell separator matrix driving the test helper, the
  `kit_doctor` predicate and the real `head -n 1 | grep -qF` over identical bytes, with
  zero disagreements. That, not round count, is what ended the loop.

**Open, and owned by nothing yet**

- **`#105`–`#110`** — this session's six: `/adopt` never seeds `AGENTS.md`; `kit_doctor`
  aborts on unreadable/directory/invalid-UTF-8 docs where `init.sh` fails safe; the marker
  predicate is duplicated between `kit_doctor` and its tests and kept in sync by a
  docstring; `AGENTS.md`'s config-derived links freeze at first render; the intermittent
  `test_portability.py` flake; and the template's fill-me placeholder.
- **`#77` reproduced** — I edited the shared tree while a lens was reviewing it. The lens
  caught it on its own initiative, not because the contract asks. Occurrence logged there.
- **`#47` gained a third instance** — `docs/AGENTS-sections.md` untracked, alongside `#37`
  and `#41`. Not fixed, because adding one more hand-maintained row is what `#47` exists
  to stop.
- **`#93`, `#95`, `#97`, `#98`** unchanged; `#54` is directly relevant after this session.
- `#50`, `#66`, `#71`, `#72`, `#75`, `#76`, `#86`, `#88` and the rest per `session-start`.

▶ Next: `triage-friction-log` — **discharged**, shipped as `#126` later the same day. The
inbox is now 28 lines; the 287-line figure above is that session's reading, kept as the
record of why the sweep was called for.

### 2026-07-28 (fix-round scope shipped; the severity gate it exposed)

**Theme —** Two doctrine changes, the second existing because the first cost far more
than it should have. `#101` took three panel rounds and six isolated reviewers for one
paragraph; `#102` is the rule that stops that recurring.

- **`#101` merged (`238de25`), closing `#100`.** Rule 3 gains *"a fix round addresses
  only what the review found"* — a new mechanism is an addition however squarely a
  finding prompted it, so it gets filed. Plus a paragraph in `fallback-review-panel.md`
  stating that lever replaces none of the stopping criterion.
- **One of `#101`'s two HIGHs came from my own fix rounds — not both.** Round 2's HIGH
  was a gap the rule inherited: it did not catch two of the three cases it is built on,
  and `205d0a4`'s own message records that `#100`'s proposed wording has it too — round
  1's carve-out licensed those cases outright but did not create the gap. Round 3's
  HIGH was mine: two fresh readers, given only the paragraph, both permitted the case,
  both quoting my carve-out clause.
- **`#102` merged (`87dfa83`).** The blast-radius classification now also decides which
  findings to act on. A gate, send path, destructive operation, or kill/recovery path —
  plus any change that does not clearly sit in one class — gets **every** finding acted
  on; only on the second, reported-but-never-acted-on class is the gate HIGH always,
  plus anything at any severity that says the change is a *regression* rather than
  merely imprecise. New contract item 9 makes lenses report both labels.
- **CodeRabbit reviewed neither PR's final state** — one clean pass on `#101`'s first
  head, then a plan quota that no waiting clears. The fallback panel was the independent
  pass throughout: five rounds, ten isolated lenses across the two PRs.

**Decided**

- **Two failed tightenings ⇒ delete, applied to my own clause.** `#101`'s carve-out was
  itself an unrequested mechanism added mid-fix-round in response to a MED — the shape
  the paragraph prohibits, reproduced inside it. Deleted rather than reworded a third
  time.
- **Severity level alone is the wrong gate.** `#102`'s own first round returned 0 HIGH /
  7 MED, four of which said the paragraph loosened a control it claimed to tighten. The
  discriminator that works is regression-vs-imprecision.
- **The gate belongs at the act-on stage, never in the lens prompts.** `#101` was
  docs-only and drew two real HIGHs; a lens told to calibrate down for "it's only docs"
  would have downgraded exactly those two. It is also the anchoring contract item 2
  forbids.

**Learned**

- **A gate that reads labels nothing produces is not a gate.** `#102`'s HIGH: "act on
  HIGH" and "says regression" are lens output, and no contract item or `focus` string
  ever asked for either. It read as working only because I supplied severity ad hoc in
  my own launch prompts — the drift the single-source rule exists to stop.
- **A three-space list continuation is correct CommonMark and broken Python-Markdown**,
  which silently renumbered rule 4 to rule 1 while the header still said "Four rules
  apply". Ten files outside the session records cite these rules by number (fourteen
  counting the records themselves). Caught by rendering in both engines,
  not by review — a genuine completed bot review of the head carrying it passed clean.
- **I shipped a false claim in a commit message** (`4ac203e`), retracted in the PR body
  before merge, so it never reached `main`.
- **`#76` reproduced twice**: neither PR's final head was lens-reviewed, and
  `--record-review --head` can only assert the exact head, so both merged with the
  coverage recorded as PR prose and no receipt.

**Open, and owned by nothing yet**

- **`#92`, `#93`** — untouched; `#92` was the planned follow-on and now lands under both
  new rules.
- **`#95`, `#97`, `#98`** — the three panel-found defects on `main`, unchanged.
- `#47`, `#54`, `#66`, `#71`, `#72`, `#75`, `#76`, `#77`, `#86`, `#88` and the rest per
  `session-start`.

▶ Next: `#92` — ship `docs/templates/AGENTS.md.tmpl` rendered by `init.sh`, added to
`KIT_OWNED` and the manifest so `kit_doctor` reports it. Read `#92` for the generic
spine to lift; note in the template that adopters are expected to extend it.

### 2026-07-27 · 4 (gh-less REST transport; `#91` closed, `#96` merged)

**Theme —** One feature, five review rounds, two PRs. The first attempt was closed
unmerged because *severity rose every round* — each round hardened one more boundary and
the next round found the next one. The second bounds the new transport structurally
instead, and merged.

- **`#96` merged (`fd75cd7`), closing `#90`.** `pr_watch` can poll without `gh` (REST
  over `urllib`, `GH_TOKEN`/`GITHUB_TOKEN`), and on that backend it **polls only**:
  `mergeable` is false by construction and `--record-review` / `--assert-draft` /
  `--assert-ready` refuse. Suite 418 → 488, and 488 again with `gh` off PATH.
- **`#91` closed unmerged** with its rationale on the PR. Three panel rounds found 2, 2,
  then ~7 HIGH — **three of them introduced by the previous round's own fixes**. Six of
  the seven were "some degraded response makes REST report `mergeable: true`".
- **The bound costs nothing**: `dev_session.sh cmd_merge` resolves through `gh repo view`
  + `gh pr list` *before* it reads `mergeable`, so a gh-less session never had a merge
  path. `#96` turns that accident into an enforced invariant.
- **Filed six issues** (`#92`–`#95`, `#97`, `#98`) — the Codex-adapter pair, the
  broadening bar, and three defects the panel found that predate this work. `#96` is the
  PR, not an issue.

**Decided**

- **A structural bound beats validating every boundary** (rule 1's "deterministic
  artifact"). Five rounds of per-boundary tightening never converged; one guard in one
  place ended the class. Kept to two functions so `#94`'s broadening is a deletion plus
  its 13-row bar, not a rewrite.
- **Two of my own mechanisms deleted under rule 1 rather than tightened**: a request
  ceiling that created a fail-open by starving the one caller that swallows its
  exception, and a settle-baseline reset that disabled the false-settle guard on the
  **default `gh` backend** for every existing PR.
- **A third lens earns its place when the first two keep finding the same shape.** Two
  general lenses each found one HIGH per round — in the tests on round 1, engine
  fail-opens after that; a lens briefed only on "enumerate every external input, trace
  it to a permissive verdict" found three the others never saw. Its 56-row input
  enumeration is distilled to the 13-row acceptance table now on `#94`.
- **Coverage recorded piecewise, again.** The final delta (a reviewer-requested doc line
  + a manifest hash) is unreviewed and says so, with `bots_behind_head` on the receipt.

**Learned**

- **My own fixes were the largest single source of HIGH findings** — three of the seven
  fail-opens across both PRs, one of them on the *default* `gh` backend, with a test
  that pinned its permissive outcome as correct. The reviewed, *requested* fixes held; the unrequested
  hardening I added alongside them is what broke.
- **My claims were the dominant defect four rounds running** — a comment naming a
  consumer that did neither thing claimed, "nothing branches on this" about a field that
  gates a merge, "read-only" surviving on the two surfaces operators read, a commit
  claiming a docstring fix it never applied. Also: the cs-toolkit reasoning backwards and
  the diff-size comparison wrong twice, both flattering, both corrected on the record.
- **I pushed a red tree** by chaining `make test` into commit-and-push and acting past a
  failure on screen.
- **The provided worktree was at the base ref on 5 of 5 panel launches**, and every lens
  detected it because the prompt required clone-verify-report. Posted to `#75`; no
  cumulative claimed — the earlier sessions' figures count a different thing.

**Open, and owned by nothing yet**

- **`#94`** — broadening REST to merge authorization, with the fail-open enumeration as a
  written bar. Needs a real consumer first; nothing can merge gh-lessly today.
- **`#95`** — a pre-existing fail-open on `main`: a PR can forge a check that cancels its
  own reviewer's pending block. **`#98`** — pre-existing too, but it *hides* blockers
  rather than opening the gate: `render` sanitises comment bodies and not the path/author
  beside them, so a filename can walk the cursor over them. **`#97`** — no guard stops a kit test hitting the network.
- **`#92`, `#93`** — the kit ships Codex skills but no `AGENTS.md`; cs-toolkit forked the
  wrap-up workflow into a 160-line skill. `#93` must recover upstream content *before*
  thinning it.
- **The cs-toolkit `pr_watch` swap is unblocked** and is the *fix* for that repo's two
  transport fail-opens, not the trigger (correction recorded on `#94`).
- `#47`, `#66`, `#54`, `#71`, `#72`, `#75`, `#77`, `#86`, `#88` and the rest per
  `session-start`.

▶ Next: `session-start` — several independent threads (`#92`/`#93` Codex adapter, the
cs-toolkit swap, `#47`, `#100`, and three panel-found defects on `main`), so let it
re-propose.

### 2026-07-27 · 3 (CLAUDE.md; init.sh harness + fixes; review loop worked)

**Theme —** Worked the review-round problem directly. Three PRs merged, each watched to
convergence with real independent review: two CodeRabbit passes obtained by re-triggering
after rate-limit windows, four fallback-panel rounds that caught two config-bricking
regressions **in my own fix** before they shipped.

- **`#83` merged (`63acfcf`).** Root `CLAUDE.md` naming `make test` as *the* verification
  command — the discoverability precondition for `#54`. CodeRabbit reviewed the exact
  head clean after a re-trigger (its rate window was 13s).
- **`#85` merged (`cde96e8`), closing `#84`.** init.sh fixture harness: 14 tests — 10 pins
  plus 4 strict-xfail reproductions of `#62`/`#67`. `#84` corrected the record first: init.sh
  was **not** at zero coverage — its migration path was well covered; the three open
  bugs lived in the uncovered paths — detection (`#67`), hostile-value stamping (`#62`),
  hooks (`#66`); seeding and `.gitignore` were uncovered but bug-free.
- **`#87` merged (`7c71385`), closing `#67` + `#62`.** Manifest-derived engines
  detection (top-level names only), lossless-only quoting (`yaml_scalar` /
  `quoted_scalar`), one shared YAML-correct comment scanner, ENVIRON value transport,
  quoted bots serialization. Suite 372 → 418 across the session.
- **The panel earned its cost on `#87`**: round 1 caught my always-quote change turning
  an interior `"` into an unloadable config and `\` into a reader split-brain — worse
  than the bug it fixed; round 2 caught the same class surviving on the five
  always-quoted fields, plus a bots single-quote regression. None were caught by the
  suite as it stood at those heads.
- **Stale `chore/update-handoff-2026-07-27` deleted** after verifying full supersession
  (its fixed text is on main/archive; the graduated issues quote the fixed numbers).
- **Filed `#86`** (.mcp.json sniff misses the kit's own documented credential shape) and
  **`#88`** (the three config readers disagree on where a value ends). **Corrected**
  `#67`'s Note (it miscited `#36`, the pre-push twin).

**Decided**

- **A rate-limited reviewer with a short recovery window gets re-triggered, not waived
  or substituted.** `@coderabbitai review` after the window produced real reviews of the
  exact head on `#83` and `#87`. Windows observed ranged from 13s to 48min — panel when
  long, re-trigger when short.
- **Piecewise review coverage is recorded piecewise.** `#87`'s final delta
  (reviewer-prescribed fixes only) merged without a bot pass of its own; the receipt's
  `bots_behind_head` annotation plus a PR comment state exactly what covered what.
- **Quote only when lossless.** Blanket-quoting stamped values is a corruption class,
  not a fix — values YAML would reinterpret (`"`, `\`, leading `'`) stamp raw as they
  always did.

**Learned**

- **The handoff's own claim was the defect again — fifth consecutive session.** "init.sh
  has no automated test coverage" was false (four migration tests run it); caught this
  time by grounding before filing rather than by a reviewer, and the corrected framing
  changed both the issue and the work.
- **Panel isolation went 8 for 8** when every launch prompt assumed the worktree was
  wrong and required clone-verify-report — the inversion `#75` proposes, working as
  predicted (contrast: 9 of 9 wrong across the prior two sessions). Occurrence data
  posted to `#75`.
- **`#44`'s shape depends on how the review was triggered**: clean reviews on `#83`/`#85`
  arrived as edited comments (no review object — coverage machinery blind, receipts
  recorded by hand); `#87`'s re-triggered pass submitted a real review object with a
  commit SHA, so `coverage` populated (`covers_head: true`). Posted to `#44`. The
  rate-limited check reporting **pass** recurred four more times (posted to `#45`).

**Open, and owned by nothing yet**

- **`#86`, `#88`** — this session's filings; both small and well-specified.
- **`#47`** — called the highest-leverage unbuilt thing in three recent sessions. A scope
  note is posted on the issue itself: `#87` left init.sh's fallback triple as a
  deliberate manifest-lost fallback, so `#47`'s tree-derivation should say whether that
  restatement is in or out of its scope.
- **`#66`** — still behind the `#61` design call. `#54`, `#71`, `#72`, `#75` (now with
  supporting data), `#77`, and the rest of the backlog per session-start.

▶ Next: `#47` — derive `KIT_OWNED` from the shipped tree and fail CI on divergence; its
own body names `#36`/`#37`/`#40`/`#41` as the gap class it closes.

### 2026-07-27 (friction-log inbox graduated; `reports/` contract settled)

**Theme —** Ran the triage sweep the doc-budget warning had been asking for. Thirteen
entries in, thirteen accounted for. Both PRs merged **without an independent review** —
CodeRabbit was rate-limited on its plan while its status check reported **pass**, twice.

- **`#78` merged (`8b1d6b2`).** 13 un-graduated entries → 8 issues (`#70`–`#77`) plus one
  no-ticket. Four of the eight each merge **two** entries recorded on separate days,
  because the occurrence count is the evidence (`#71` three occurrences, `#75` nine of
  nine). Friction log 190 → 50 lines, back under its 150 budget.
- **`#79` filed, `#80` merged (`4e9cad9`).** `reports/` carried two contradictory
  contracts — `post-merge-systemize` said never commit it, `triage-friction-log` said
  git-track it, and `.gitignore` matched neither, so the first rule was unenforced. Now
  ignored here and in `init.sh`, with both skill lines corrected.
- **The triage engine is still unvendored (`#6`)**, so the sweep ran in the skill's
  LLM-only mode: marker, archive sweep and finalize done by hand against the same
  contract, with a frozen-inbox snapshot for window safety.

**Decided**

- **A rate-limited reviewer is not a waiver, but the operator may waive it.** Both
  waivers were explicit and scoped — the second was re-asked rather than extended,
  because that diff touched `init.sh` and not only docs — and both are recorded on the
  PR and in the squash body. **No review receipt was written**: a receipt would flip
  `mergeable` and let automation merge unreviewed work.
- **Use closing keywords deliberately rather than avoiding them.** `#80` carried one
  intended `Closes #79`, linted before push and verified after opening. Across two squash
  merges: `#79` closed, `#70`–`#77` all still open. The rule forbids *unintended*
  adjacency, not the mechanism.

**Learned**

- **`make test` exists and runs the whole suite in 22s** (372 passed). I probed
  `uv run pytest` and `python3 -m pytest`, both failed, and wrote *"tests were not run
  locally — pytest is not installed"* into `#80`'s body. False; corrected on the PR.
  Nothing in the repo points at `make test`, and there is no root `CLAUDE.md`. Fourth
  consecutive session where a claim of mine was the defect.
- **The kit's own triage skill defaults to a draft PR, and CodeRabbit skips drafts
  outright.** The workflow's happy path produces a PR its configured reviewer will never
  read, and the skill says nothing about it.
- **A rate-limited CodeRabbit reports `pass`** — the `#23` surface, now with two fresh
  instances in merged PRs and a third in the history file.

**Open, and owned by nothing yet**

- **`#70`–`#77`** — this sweep's output, untouched. `#71` (closing-keyword guard) and
  `#75` (invert contract item 7, nine of nine) carry the strongest evidence.
- **`chore/update-handoff-2026-07-27` holds unmerged work and needs an operator call.**
  `f3d4e6e` ("fix eight claim errors a review lens found in this handoff") and `30ab573`
  ("fix a cross-reference this sweep broke") are **not ancestors of `main`** — an earlier
  session's branch that never landed, possibly superseded by `42873d8`. Left intact
  rather than cleaned up. It is also what `#81` was accidentally opened against.
- Everything open at the end of the **2026-07-27 `#59` + `#61.1`** session still stands:
  three `init.sh` defects with no coverage and nothing tracking that gap, `#61`, `#47`,
  `#50`, `#60`. (Named rather than "the block below" — an archive sweep moves blocks
  between files and orphans relative pointers; that is `#73`.)

▶ Next: **a root `CLAUDE.md` naming `make test`, then the `init.sh`-coverage issue** —
today's false "tests not run locally" claim on a merged PR is the second verification-claim
defect in as many sessions and the fix is one file; then pick up the carry from the
`#59` + `#61.1` session, where three `init.sh` bugs are open against a file with zero
coverage and no issue tracking that gap.

### 2026-07-27 (#59 + #61.1 shipped; #61.2 built and reverted)

**Theme —** Fixed what the cs-toolkit adoption found in `kit_doctor`. The review panel
ran twice; round 1 found **four regressions against `main`** — my change making things
*worse* than the code it replaced: `--root` on a non-repo answering from the *enclosing*
repository, an inherited `GIT_DIR` overriding it, an unreadable manifest version
degrading from a loud crash to a silent `✓`, and `version: 2.0` going from accepted to a
hard `--generate-manifest` failure. **None were caught** by CI, by the suite as it then
stood (355 tests), by my own mutation run at that head, or by CodeRabbit.

- **`#65` merged (`a18f085`), closing `#59`.** The engines probe derives from
  `KIT_OWNED` instead of naming three files; a quoted `kit.version` no longer crashes
  the report, an unreadable one says so instead of advising a migration, and it exits 2
  because CI gates on that code.
- **`#61`'s hook-detection half was deleted, not shipped.** Asking git resolved the
  false negatives and introduced worse: answering from an *enclosing* repository when
  `--root` was not one, and honoring an inherited `GIT_DIR`. `_hook_dirs`'s **body** is
  byte-identical to `main`; the only change is 25 docstring lines stating the gaps as
  known — including a false POSITIVE the revert does *not* fix (`.git/hooks` is appended
  unconditionally, so a hook there reports installed even when git reads elsewhere).
- **`#66`, `#67` filed** — both `init.sh`, both found by the panel while reviewing
  something else.

**Decided**

- **The detector must resolve the same way as the writer.** Probing settled a
  disagreement the kit shipped with: `rev-parse --git-path hooks` *does* honor
  `core.hooksPath` and tilde-expands it; `git config --get` does not. `init.sh`'s
  comment asserts the opposite, and it installs an **inert hook** for a `~`-form path.
- **Blast radius, not round count — and say which you applied, in the PR.** A read-only
  report's worst case is a wrong message, so two panel rounds with decaying severity is
  proportionate. What that does *not* cover was written down too.
- **Rule 1 applied to a half, not a PR.** Two failed shapes for hook detection ⇒ revert
  that half and ship the rest, rather than tightening a third time or holding #59.

**Learned**

- **My claims keep being the defect.** A commit message attributed a defect to the
  reverted half when it *ships*; a PR table misstated `main`'s behaviour; and the
  wrap-up's own handoff block then miscited `#36`, overstated a test count, and got a
  GitHub rule backwards — all caught by a review lens, none by me. This is the third
  consecutive session where claim-vs-artifact drift is the most common finding.
- **An under-determined measurement talked me out of a correct rule.** `#68`'s
  squash-merge closed `#61` (reopened by hand) because I had weakened the standing
  "never write a closing keyword next to an issue number, even negated" rule after
  measuring one PR body as inert. That experiment varied **two** things at once —
  fenced-vs-inline *and* body-vs-commit — so it never established the thing I concluded
  from it. Three attempts to state the rule precisely have each been wrong; the
  conservative original would have prevented all three incidents. Stop deriving the
  mechanism (rule 1).
- **Two of my tests pinned nothing**, including the one whose stated thesis is "don't
  restate the list": it re-derived its expectation from the real `KIT_OWNED` with the
  prefix filter left out, so deleting that filter left the suite green.
- **A mutation harness must restore in a `finally`.** Mine died parsing pytest output
  and left the file mutated — `#50`'s hazard by a route `#50` does not describe.
- **CodeRabbit is incremental**, so a force-pushed or substantially rewritten PR keeps a
  stale review and reports nothing new. Its pass covered the pre-split head only;
  `bots_behind_head` recorded that rather than waving it through.

**Open, and owned by nothing yet**

- **Three `init.sh` defects** — `#62` (unquoted YAML stamping), `#66` (inert `~` hook),
  `#67` (the same hardcoded triple `#59` just fixed, where it *writes* bad config).
  `init.sh` has no automated test coverage and **no issue tracks that** — `#36` is the
  `pre-push` twin, and `#67`'s body miscites it for `init.sh`; both need correcting.
- **`#61`** — open (closed in error by `#68`'s squash-merge, reopened by hand): the
  hook-detection half, with the panel's
  evidence, the shape a correct fix needs, and a table of 9 `git config` value forms of
  which the current scan misparses 5.
- **`#47`** still the highest-leverage unbuilt thing, and it subsumes `#67`.
- **`#50`, `#60`** unchanged.

▶ Next: **file the `init.sh`-coverage issue, then `#67` + `#62` behind it** — three
`init.sh` bugs are open, the file has zero coverage, and nothing tracks that gap, so the
harness is the unblocking step and it needs a ticket of its own first. `#66` needs the
`#61` design call and should follow.

### 2026-07-26 (cs-toolkit Phase 1; kit lint; #60 attempted and reverted)

**Theme —** Adopted the kit into cs-toolkit (its ancestor), then fixed upstream what
the adoption found. **Everything the review panel caught had already passed my own
review and a green suite** — including two of my own fixes and two of my own tests.

- **cs-toolkit Phase 1 shipped** (`#1791`, merged, main green). Config surface +
  `init.sh` + manifest + `kit_doctor` + `kitconfig`, additive and inert. First reading:
  2 unchanged, 0 differ, 22 missing, 0 unknown. `#1792` open with the handoff memo.
- **Kit `#63` merged, closing `#58`.** `ruff.toml` + a CI lint step. On its **first run**
  it found a live crash the whole suite had missed: `yaml.YAMLError` in an `except`
  tuple with no `yaml` import (`F821`), so every config-resolution failure raised
  `NameError` from inside the handler written to report it cleanly.
- **Five issues filed from one adoption** — `#58`–`#62`. Two fixed; `#59`, `#61`, `#62`
  open.

**Decided**

- **Engines must be excludable as a DIRECTORY, and the kit must say so.** Adopters
  cannot be made lint-clean: cs-toolkit runs `line-length 120`, another runs 88, and no
  formatting satisfies both. `adopting-into-a-linted-repo.md` is the durable half of
  `#58`; the lint config is the smaller half.
- **Two failed tightenings ⇒ delete the mechanism** (rule 1, applied to my own work).
  `#60`'s fix probed upward for a config marker and escaped into a parent project —
  unbounded, then bounded and *still* escaping one level up in the shallowest layout.
  Removed rather than tightened a third time. **`#60` stays open** with both attempts,
  why a depth bound cannot work, and the `paths.engines`-validation shape that could.
- **Convergence beats formatting.** cs-toolkit is the ancestor and is AHEAD in places,
  so "adopt the kit's engine" is a regression there. A capability the adopter has and
  the kit lacks goes **upstream first**.

**Learned**

- **The panel's isolation pointed at the wrong repo, again — in both lenses, both
  rounds.** Each was placed on `main` with an empty diff. All four detected it because
  the prompt required reporting the path and diff stat; without that, four confident
  all-clears over nothing. Contract item 7 is load-bearing and its warning is not
  hypothetical.
- **A test can be precise about the wrong value.** My `#60` escape tests padded the
  fixture with a spare directory level, pushing the foreign config exactly one index
  past the bound — so they passed while the real case escaped. Mutation testing showed
  the bound was pinned *exactly*; it pinned exactly the wrong number.
- **Two of my tests pinned nothing.** One planted both markers, so the probe it named
  was never load-bearing — deleting it left the suite green. Both were in the block
  whose stated job was preventing that.
- **Regex guards catch the spelling you thought of.** The `datetime.UTC` guard missed
  `import datetime as dt` and a parenthesised multi-line import. CodeRabbit and the
  adversarial lens found it independently; a 340-test run did not.
- **Negating a closing keyword still arms it.** The PR body was edited to retract a
  closure claim and read "Does NOT close #60" — GitHub matched `close #60` and closed
  it on merge. Caught post-merge and reopened.

**Open, and owned by nothing yet**

- **`#60`** — reopened, unfixed, with the analysis. Three resolvers, not one.
- **`#59`, `#61`, `#62`** — `kit_doctor` cannot see itself; `kit.version: "2"` crashes
  it; `init.sh` stamps YAML unquoted.
- **`#47`** still the highest-leverage unbuilt thing; `#50` still casts doubt backwards.
- **`#63`'s last two commits merged unreviewed** — the panel covered `f40070e`, the head
  moved twice after. `--record-review` correctly refused a stale head, so no receipt
  claims otherwise. Recorded on the PR as an accepted risk, not a clean bill.

▶ Next: **`#59` then `#61`** — both are `kit_doctor` telling an adopter something false
on the first screen they see (`✗ contains no kit engine` while running from that very
directory; a traceback from a read-only diagnostic). Small, self-contained, and they
fix the tool every future adoption leans on. `#60` needs a design pass, not a patch.

### 2026-07-26 (adopter upgrades)

**Theme —** Ran the OpenKitchen upgrade end to end. **It worked**, and the doing of
it produced 17 issues — most of them not about the upgrade but about the kit's own
quality mechanisms disagreeing with each other.

- **5 PRs merged.** OpenKitchen `#256` (pre-v2 install → schema v2: config migrated
  with no value changed, pre-push hook finally *installed*, all 10 `differs` files
  refreshed), `#257` (`review.bots: []`), `#258` (doc sync). Kit `#43` (panel
  isolation doctrine) and `#49` (test suite detached from ambient config, closing
  `#48`).
- **`#48` blocked a one-value adopter config change**, and inverted the founding
  invariant: `pr_watch` resolves config at *import* time, so ~32 kit tests silently
  required the ambient repo to configure a review bot. Setting the truthful
  `review.bots: []` turned them red on assertions about *engine* behaviour. Fixed
  upstream, never patched in the adopter.
- **OpenKitchen has no reviewer at all.** CodeRabbit is installed but on the Free
  plan: 25/25 recent PRs have one walkthrough and **zero reviews**. So the fallback
  panel is that repo's **primary** reviewer, not a substitute for a bot that is down
  — and `review.bots` now says so.

**Decided**

- **A defect in a byte-identical kit file goes upstream, never into the adopter.**
  Applied 9 times on `#256` alone. An edited engine can never be replaced by a kit
  update, which is the whole property the upgrade exists to preserve.
- **The founding invariant is symmetric.** "Engines kit-owned, config adopter-owned"
  also means *a legitimate adopter config value must never break a kit-owned test*.
  That half was silently false.
- **Blast radius, not round count** — applied explicitly on `#49` (test
  infrastructure ⇒ stop at 2 panel rounds) and **stated in the PR**, including what
  stopping does *not* cover.

**Learned**

- **The kit's quality mechanisms cover different subsets and nothing checks they
  agree.** `KIT_OWNED` tracks 24 of 37 shipped files; the manifest tracks 0 test
  files; the suite covers 0 lines of `pre-push`. Every gap between them is where a
  file can be shipped, depended on, linked to, and invisible to all three — the root
  cause of `#36`, `#40`, `#41`, `#51`, and how a dangling doc link shipped. `#47` is
  the single check that closes the class.
- **Mutation testing can be silently poisoned.** A mutation preserving source
  *length* leaves stale bytecode that Python treats as valid, so a `git`-clean
  restore does not restore. The suite ran mutant code for minutes; grep found nothing
  because comments do not survive compilation (`#50`). **This invalidates mutation
  evidence gathered earlier in the session, including on the already-merged `#256`.**
- **My own claims were the most common defect.** Five-plus instances of
  claim-vs-artifact drift — two wrong numbers in a PR body, a bug report asserting a
  test did not exist when two do, an undercount of 3-vs-13, an invented "7 tests
  fail", and a false "untouched" claim that survived a round of corrections because I
  fixed the commit message and not the body. **Every one was caught by a reviewer,
  none by me.**
- **A fix round on the fix is still where the next bug comes from.** `#49` round 2
  found a MED/HIGH inside round 1's fix: a guard that *failed open by skipping*,
  because its skip predicate was computed with the function under test.
- **A review lens handed the wrong repo reports all-clear.** Both lenses on `#256`
  got a worktree of the *kit* while reviewing the *adopter*; both noticed and cloned
  the target themselves. Fixed as doctrine in `#43` — isolation must be **of the repo
  under review**, verified not assumed.

**Open, and owned by nothing yet**

- **`#46` — `pre-push` is all-or-nothing, and it BLOCKS cs-toolkit.** That repo's hook
  carries two guards the kit's does not (`auto/daily` protection, detect-secrets), and
  no config key can express either.
- **`#47`** — derive `KIT_OWNED` from the shipped tree. Highest leverage of the 17.
- **`#50`** — casts doubt backwards on merged mutation evidence.
- **`#44`/`#45`** — the merge gate cannot see a clean CodeRabbit review (it arrives as
  a comment), and cannot tell a structurally-non-reviewing bot from a pending one.
- ✔ **The friction-log inbox was graduated** (`triage-friction-log`, run inline in
  LLM-only mode since its engine is unvendored — `#6`). Three entries became `#54`
  (every verification claim must name the command that establishes it), `#55` (rule 1
  needs a tightening threshold) and `#56` (removing a mechanism requires enumerating
  what it rejected); three more needed no ticket because their fixes had already
  shipped in `#31`. Inbox 150 → 32 lines.

▶ Next: **cs-toolkit Phase 1 only** — install `config/dev-model.yaml` + `init.sh` +
`kit-manifest.json` + `kitconfig.py` + `kit_doctor.py` (additive, zero behaviour
change) to get a real `kit_doctor` reading, then stop. Defer the `pr_watch` swap
(the nightly fixer is in active development this week) and the `pre-push` swap
(blocked on `#46`). **Correction to the runbook**: the `done` → `converged` change
is in `.claude/commands/pr-watch.md` lines 11/13/39, **not** `nightly-fixer.md`,
which only delegates — following it literally finds nothing and the failure is a
silent infinite poll.

### 2026-07-26 (#26, overnight)

**Theme —** Built `review.fallback_panel`, then spent four rounds trying to make the
receipt's coverage claim verifiable *by the engine*, then deleted all of it. The
deletion is the result, not the failure.

- **#31 merged, closing #26.** `review.fallback_panel` is the primary substitute when
  a bot can't review: one isolated, fresh-context reviewer per lens.
  `fallback_commands` stays as the explicitly degraded one-lens mode. The lens
  *contract* — fresh context, raw diff, no author framing, execute rather than only
  read, mutation-test, report-don't-fix — is the part worth having written down, and
  lives in the new kit-owned `docs/agentic-dev-kit/fallback-review-panel.md`.
- **`pr_followup_hook` now names the panel.** It fires on every `gh pr create`/`ready`,
  which made it the most-read statement of fallback policy in the kit — and it was
  advertising the degraded mode.
- **#32 filed** — the design that would actually verify coverage (each lens recording
  its own receipt from its own context), with all four defeats written up.
- **#33 filed, and it is the one to read first.** `kit_doctor`'s drift self-check
  rehashes every kit-owned file, so *any* byte change to an engine fails it — which
  makes a mutation-testing run report every mutant as killed while nothing behavioural
  caught anything. Its proposed fix (a `driftcheck` pytest marker) is **not built**;
  only a prose warning in the panel doc ships.

**Decided**

- **Four tightenings of a matcher is the signal to delete it.** `safety-critical-
  changes.md` rule 1 says treat "we tightened the matcher" as a stopgap. I tightened
  it four times — source equality, lens names, a required roster, a counted roster —
  and each was defeated by the next round, the last by one decorated character in a
  field the caller writes themselves. What ships records the claim and labels it a
  claim.
- **Report, never gate — now for a fourth field.** `--lenses` joins `signal`,
  `bot_signal` and `coverage`. All four make an omission legible; none blocks.

**Learned**

- **Mutation testing this repo reports FALSE KILLS.** `kit_doctor`'s self-check
  rehashes every kit-owned file, so any byte change fails it — a run can report 100%
  killed while nothing behavioural caught anything. **I verified the mechanism
  directly** — disabling a behaviour outright fails only the manifest test. The
  *figure* "17/17 reported, 7 survived when excluded" is a reviewing lens's report,
  restated: the 17 mutants are enumerated nowhere, so treat it as attested, not
  measured. **This invalidates mutation evidence cited in #25, #28, #29 and #31
  itself** wherever the reviewer did not exclude that test. Contract item 5 now warns
  about it; #33 tracks the mechanical fix. (Those 7 survivors were themselves closed
  inside #31 — 7/7 caught by named tests once real coverage was added — so nothing is
  known to be live on `main` because of this.)
- **Two review lenses in one working tree corrupt each other.** One mutates files to
  test them; the other reads that as external corruption and `git checkout --`s it.
  Stopping one left a live mutant behind that silently disabled a guard. Contract
  item 7: isolated worktrees.
- **Deleting a check can reintroduce a bug it was masking.** The roster check was the
  only thing catching comma-as-punctuation in `--lenses`; removing it brought back the
  exact forgery the commit before it claimed to block, plus an honest input
  misrendering. **Fixed inside #31** (`_countable_lenses` counts entries that look like
  lens names, not prose) — recorded for the pattern, not as a live defect.
- **A silent `str.replace()` no-op let me assert a fix that never landed** — twice.
  Every substitution in this session's later rounds reports MISS rather than passing
  quietly.

**Open, and owned by nothing yet**

- **#32** — verifying lens coverage rather than self-reporting it. The honest version
  of what #31 tried.
- **#33** — the drift self-check's false kills. H severity and retroactive; its
  mechanical fix (a `driftcheck` marker) is unbuilt.
- **The autonomous self-merge path never displays review coverage.** `dev_session.sh
  merge` gates on `mergeable` alone, so the `review evidence:` line — the whole
  remaining value of #31 — is invisible on exactly the path
  `autonomous-session-playbook.md` argues review independence matters most on. Known
  and documented in `workflows/pr-watch.md`, deliberately not fixed at the end of a
  seven-round review; #32 is the real answer.
- **Adopter upgrades are written but not run.** `~/Documents/openkitchen-devkit-upgrade.md`
  and `~/Documents/cs-toolkit-devkit-adoption.md`. Held at the operator's request until
  #31 landed — it has now landed, so both are unblocked.

▶ Next: **run the OpenKitchen upgrade** (`~/Documents/openkitchen-devkit-upgrade.md`).
It is a real adopter on a pre-#8 install that cannot migrate its own config until
`init.sh` and `kitconfig.py` are copied in, and its pre-push hook is not installed.
cs-toolkit is the larger job — an *adoption*, not an upgrade, plus a fixer change from
`done` to `converged` that will otherwise wedge an unattended nightly loop.

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

