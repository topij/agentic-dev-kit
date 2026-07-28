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

Last updated: 2026-07-29 — the inbox graduated a second time (`#144`) and the documentation
was audited against the shipped tree (`#147`); eight new tickets (`#138`–`#146`).

## Latest session — 2026-07-29 (the second sweep, and a documentation audit)

**Theme —** Two merges and eight panel rounds. The deliverables are routine; the durable
result is a measurement: **across eight rounds and fourteen isolated lenses, no HIGH finding
was ever in executable behaviour.** Every one was in prose — two of them inside `.py`/`.sh`
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
  `init.sh`'s `# Requires:` header — which is the class worth separating from the rest.
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
- **`#75` is 12 of 12.** Every lens launch landed on `main` with an empty diff and self-corrected,
  because the launch prompt made reporting path/sha/diffstat mandatory *before* reviewing.
- **CodeRabbit: seven consecutive PRs with no check and no comment** (`#126`–`#147`).

**Open, and owned by nothing yet**

- **`#138`, `#139`, `#140`, `#141`, `#142`, `#143`, `#145`, `#146`** — this session's eight,
  enumerated rather than written as a range, because `#138`–`#146` spans `#144` (a PR, not a
  ticket) and hides any member's state from a `#N` sweep. That is how a closed `#145` sat in this
  list for six minutes. `#138` and `#127` are the pair that would make a sweep's own claims
  mechanically checkable — `#138` filed here, `#127` by the previous session — and both were
  reproduced inside this session's pilot run of them.
- **The friction inbox is well back over budget** — 196/150, from this session's seven
  entries. Another `triage-friction-log` sweep is due, and `#113`'s hazard now has a *state-path*
  instance: `state/triage/frozen-inbox_{date}.json` collides on a same-day re-run.
- **`#132`–`#136` from the previous session** — `#132` is **closed** (shipped `2026-07-28`), so
  the cs-toolkit Phase 2 blockers are `#41`/`#37`/`#134`. `#133`, `#135`, `#136` remain open.
- **`#33` and `#112` are shipped but still open** — close them deliberately after confirming
  `#131` is what each asked for.

▶ Next: `triage-friction-log` — the inbox is 196/150, the same tripwire that opened this
session, and its seven entries are the freshest evidence behind `#120`, `#138`, `#127` and `#71`.
Prefer it over `session-start` this time: `#143` (filed here) records that `session-start`'s
tracker step overflowed its tool limit at 68 open issues and that the remedy it prescribes cannot
be run on this backend — there are 79 open now, so page at `perPage: 25` and read
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

## Earlier session — 2026-07-28 (`#92` shipped; the record corrected; five panel rounds)

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

______________________________________________________________________

## Earlier session — 2026-07-28 (fix-round scope shipped; the severity gate it exposed)

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

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

