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

Last updated: 2026-07-29 — the sixth sweep, a config overlay narrowed to one key across
three review rounds, and the same defect in all three (`#156`, `#157`, `#158` merged).

## Latest session — 2026-07-29 (the sixth sweep, and three rounds that all found the same thing)

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

______________________________________________________________________

## Earlier session — 2026-07-29 (three failed designs, and what shipped instead)

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

______________________________________________________________________

## Earlier session — 2026-07-29 (the fifth sweep, and a claim that was wrong in both directions)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

