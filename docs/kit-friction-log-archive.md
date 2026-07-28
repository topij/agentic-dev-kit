# Friction Log Archive — agentic-dev-kit

Graduated friction entries live here after they have been routed to the tracker
(GitHub Issues on this repo) or promoted into a repeated-pattern rule.

## Graduated 2026-07-28 (second sweep) — GitHub Issues (#138–#143)

Swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine tracked
in [#6](https://github.com/topij/agentic-dev-kit/issues/6) is not vendored yet). This is
the **second** sweep dated 2026-07-28 — the first (`#112`–`#125`) is the section below,
and this one graduates the two session blocks that accumulated after it.

Fourteen entries in, fourteen accounted for: **seven graduated** into six new issues,
**seven** routed as occurrence comments on the five issues they are evidence for. The
seven-into-six is not a miscount — the `pr_watch` 403 defect was recorded twice, in the
second and fourth sessions of the day, and both entries graduated into
[#139](https://github.com/topij/agentic-dev-kit/issues/139).

The six graduated issues:

- [#138](https://github.com/topij/agentic-dev-kit/issues/138) — a graduation record's
  routing claims are unverified; the tracker must be re-read **after** the writes land.
  Filed from the entry describing how the previous sweep's own record was wrong twice.
- [#139](https://github.com/topij/agentic-dev-kit/issues/139) — `pr_watch.py:687`
  discards the 403 body and asserts a cause it cannot know. *Two occurrences.* The body
  is evidence to show the operator, not an instruction to follow: in a web container the
  proxy synthesises a 403 naming an org admin that a personal repo does not have.
- [#140](https://github.com/topij/agentic-dev-kit/issues/140) — extend
  [#54](https://github.com/topij/agentic-dev-kit/issues/54)'s rule to **mechanism**
  claims. *Two instances in consecutive sessions, the second inside the correction of the
  first.*
- [#141](https://github.com/topij/agentic-dev-kit/issues/141) — the removal enumeration
  in [#56](https://github.com/topij/agentic-dev-kit/issues/56) must be per-item and
  **executed**, not a correct category judgement applied to a group that differs in
  exactly the property the judgement turns on.
- [#142](https://github.com/topij/agentic-dev-kit/issues/142) — add a **counterfactual**
  step to the panel contract for any round that removes a guard. Restore it and measure;
  do not reason about whether it was load-bearing.
- [#143](https://github.com/topij/agentic-dev-kit/issues/143) — `session-start`'s tracker
  step overflows its tool limit at 68 open issues, and the field-limited call it
  prescribes is impossible on GitHub-Issues-over-MCP.

The seven routed entries became five comments: `#45` (two entries — the fourth shape of
reviewer absence, and four consecutive PRs with no check and no comment), `#113` (two
entries — the second and third reproductions), `#75`, `#73`, and `#120`. `#23` is named
as a routing target by the swept text and deliberately received **nothing**: it is
closed, and its occurrence data was consolidated on `#45`.

The approval record for this sweep — proposals, decisions, frozen-snapshot digest, and
the post-write routing verification — is in the graduation marker in
[`kit-friction-log.md`](kit-friction-log.md), per
[#128](https://github.com/topij/agentic-dev-kit/issues/128).

### 2026-07-28 — Backlog migrated to GitHub Issues (#112–#125)

The inbox was swept by the `triage-friction-log` workflow. Twenty-four entries in,
twenty-four accounted for: **thirteen graduated** into new issues
([#112](https://github.com/topij/agentic-dev-kit/issues/112)–[#120](https://github.com/topij/agentic-dev-kit/issues/120),
[#122](https://github.com/topij/agentic-dev-kit/issues/122)–[#125](https://github.com/topij/agentic-dev-kit/issues/125)),
**ten** routed as occurrence comments on the issues they are evidence for
(#42, #45 ×3, #54, #74 ×2, #75, #76, #118), and **one** — `make test` being
undiscoverable — recorded as **discharged**, its proposed root `CLAUDE.md` having since
landed. `13 + 10 + 1 = 24`.

[#121](https://github.com/topij/agentic-dev-kit/issues/121) sits inside that numeric
range but came from the sweep itself rather than the inbox: this repo's `tracker:` config
is still `init.sh` placeholder pointing at Linear. #33 also received a comment, but a
cross-reference to #112 rather than one of the ten — see the archive for why that
distinction cost this record an audit.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

### 2026-07-28 (second session of the day)

- **A routing list is a claim about tracker state, and nothing verifies it before it is
  committed.** The `#126` sweep's record asserted where each un-graduated entry went. Two
  of those assertions were false at commit time: `#33` was listed among the ten occurrence
  comments when it had received a cross-reference about a *graduated* entry (making the
  list sum to eleven against a stated ten, so "24 in, 24 out" audited to 25), and `#23`
  was named as a routing target by three entries **and by the comment posted to `#45`**
  while receiving nothing at all. Both survived the sweep, the commit, and CI; both were
  caught only by the fallback panel, independently, and the miscount was the panel's only
  HIGH. **M** — proposed fix: before writing the graduation record, re-read the tracker
  and assert that every claimed comment exists on the issue it claims; a routing table is
  cheap to generate and currently impossible to trust. Distinct from `#54` (which asks a
  claim to name its command) — here the claim is about a remote system's state, and the
  verifying command has to run *after* the writes.
- **`pr_watch.py`'s 403 blames the token, and the token is not the problem — but neither
  is the message the proxy substitutes.** *(Corrected 2026-07-28, third session — the
  version committed in `#126` got the diagnosis right and the remedy wrong. Every claim
  below was established by running the command shown, in this container, before editing.)*
  `uv run scripts/pr_watch.py 126` exits with *"403 Forbidden — the token may lack `repo`
  scope or have expired"*. Both halves of that are wrong here, and so is taking the
  proxy's reply at face value:
  - **The tokens are set, and they are not GitHub credentials.** `GH_TOKEN` and
    `GITHUB_TOKEN` are both present in a Claude-Code-on-the-web container and both are a
    14-character proxy sentinel (`prox…`) — established by
    `python3 -c "import os; print(len(os.environ['GH_TOKEN']), os.environ['GH_TOKEN'][:4])"`
    → `14 prox`.
  - **The proxy injects a real, working credential — GitHub *is* connected.**
    `curl -H "Authorization: Bearer $GH_TOKEN" https://api.github.com/user` returns `200`
    with login `topij`, id `5101841`. The *same request with no `Authorization` header at
    all* also returns `200` with the same identity, so the sentinel is not what
    authenticates — the proxy attaches auth on the way out regardless of what the client
    sends.
  - **The block is a path allowlist, not a credential or permission problem.**
    `https://api.github.com/repos/topij/agentic-dev-kit` returns `403` **with** the
    sentinel and `403` **without** any auth header, and the public, unauthenticated
    `/octocat` returns `403` too. Identity is fine on `/user` and refused on `/repos/*`;
    only the path differs.
  - **The 403 is synthesized by Anthropic's proxy, not returned by GitHub.** Its
    `documentation_url` is `https://docs.anthropic.com/en/docs/claude-code/github-actions`.
  - **Its message is a canned string that does not describe this situation.** It reads
    *"GitHub access is not enabled for this session. An org admin must connect the Claude
    GitHub App for this organization."* Access **is** enabled — the GitHub MCP
    (`mcp__github__*`) reads and writes this repo in the same session — and
    `topij/agentic-dev-kit` is a personal repo with no organization and no org admin, so
    the prescribed action does not exist. The proxy's two 403 bodies also contradict each
    other: `/octocat` answers *"use repository-scoped endpoints
    (`repos/{owner}/{repo}/...`)"*, which is the exact path that returns the org-admin
    message. **Do not send the operator to org settings on the strength of this body.**
  - **Git is unaffected** because `git` goes through a **separate** local git proxy
    (`git remote -v` → `http://local_proxy@127.0.0.1:41729/git/topij/agentic-dev-kit`),
    which is why every push and fetch succeeded while the REST API was refused.

  **M** — proposed fix, two parts: (1) surface the response body on a 403 instead of
  asserting a cause the engine cannot know (`scripts/pr_watch.py:687`) — the body is
  **evidence to show the operator, not an instruction to follow**, and this correction is
  the reason that distinction is worth writing down; (2) decide whether the REST transport
  should detect the proxy sentinel and name the GitHub MCP as the supported path, since
  `#96`'s premise — "no `gh`, so talk REST" — does not hold when the blocked thing is the
  API host rather than the CLI. **Installing `gh` would not help**: it reads the same
  sentinel and takes the same route.
- **I filed a mechanism I had not tested, and it read as verified because it was
  specific.** The first version of the entry above stated that "the GitHub credential
  lives in the MCP server and is never exposed to the container". That is false —
  `GH_TOKEN` is set, and one `env | grep` would have shown it. The claim was inferred
  from `pr_watch`'s own error text plus the fact that MCP calls worked, and it was written
  with enough circumstantial detail to pass for a finding. It survived a fallback panel
  (both lenses reviewed the diff carrying it), CI, and my own review; it was caught only
  because the operator asked an unrelated question — *"what if we install `gh`?"* — that
  happened to require testing the claim. **M** — proposed fix: `#54`'s rule should extend
  to *mechanism* claims, not just verification claims. "X is not available in this
  environment" is a testable assertion and needs the command that establishes it in the
  same way a passing test does. Related to the routing-list entry above: both are claims
  about a system outside the repo that nothing in the workflow checks before they are
  committed.

  **Second instance, same entry, caught the next session.** The *corrected* version — the
  one that shipped in `#126` — still carried an untested claim: that the proxy's 403 body
  "says exactly what to do". It does not; it is a canned string naming an org admin who
  does not exist for this repo, and one `curl https://api.github.com/user` (no auth
  header) would have shown that GitHub access was enabled the whole time. The first
  version failed by inferring a mechanism from an error message; the second failed by
  *believing* one. Both were specific enough to read as verified, both survived the panel
  and CI, and both were corrected only because the operator went and ran the commands.
  That strengthens the proposed fix rather than changing it: the rule has to bind to any
  claim about the environment, including one quoted from the environment itself.
- **A rate-limited reviewer and an absent one are still the same signal — fourth shape.**
  On `#126` CodeRabbit registered **no check and no comment at all**, well past
  `bot_pending_grace_minutes: 15`. Not a false green, not a rate-limit notice, not a
  pending check. The three shapes recorded before this all left *something* on the PR;
  this one leaves the PR indistinguishable from one whose reviewer simply has not started.
  Nothing but an operator's judgement stopped a silent merge. **No new fix proposed** —
  occurrence data posted to `#45` and `#23`.
- **`#113` reproduced as a setup condition, one day after being filed.** This was a
  second session on 2026-07-28, so `chore/update-handoff-2026-07-28` already existed on
  the remote — the exact precondition that turned `#81` into a 160/249 revert. Avoided by
  branching off fresh `main` under a different name, i.e. by hand, because no mechanism
  exists yet. **No new fix proposed** — second occurrence for `#113`, and worth noting
  that the first occurrence caused damage while this one was caught only because the
  hazard had been filed hours earlier and was still in mind.
- **The panel's worktree pointed at the wrong ref on 2 of 2 launches**, both detected and
  corrected by the lens because the launch prompt required verify-before-review. Recording
  it as its own set: earlier sessions counted launches that isolated *correctly*, and this
  is the first set here where every launch was wrong, so the two cannot be summed. **No
  new fix proposed** — occurrence data for `#75`.
- **`#73` gained an instance that is being kept on purpose.** The swept text carries the
  previous sweep's closing line, *"Everything swept now lives in
  `kit-friction-log-archive.md`"*, which is now a self-link inside the archive it names.
  Left byte-identical because rewriting swept content would destroy the verbatim property
  that makes the archive auditable — so the sweep-warns-on-cross-references fix `#73`
  proposes needs a *warn*, not a rewrite. **No new fix proposed** — occurrence for `#73`,
  with that constraint attached.
- **Four of the panel's ten findings were defects in the PR body, not the diff** —
  including a verification claim that named no command, in the PR filing the issue about
  exactly that. Third consecutive session where the prose carried the errors and the code
  did not. **No new fix proposed** — occurrence data for `#120`, which proposes the
  cheaper message-only terminal check; three sessions of evidence now sit behind it.

### 2026-07-28 (fourth session of the day)

- **A correct general argument was used to justify deleting instances it did not cover,
  and the deletion opened the exact hole the change existed to close.** After three panel
  rounds walked through the same guard tests, the fix round deleted them on the argument
  that *"a text search over a file cannot be sound, because whoever edits it can read the
  search."* That argument is true. It did not apply to two of the three tests: they were
  built on `make -n`, which executes make and reads what it says it would run. With them
  gone, the `mutation-test` recipe silently losing `-m 'not driftcheck'` was observed by
  nothing (`make test` → 500 passed), and a behaviour-only mutation then reported a
  **kill** — `#33` restored inside the command built to escape it. Caught only because the
  next round's adversarial lens restored the deleted assertions into every bypass and
  watched them kill each one. **M** — proposed fix: when a fix round *removes* a
  mechanism, `#56` already asks for an enumeration of what it was rejecting; this says the
  enumeration must be **per-item and executed**, not a category judgement applied to a
  group. The deletion rationale here was written once and applied to three tests that
  differed in exactly the property the rationale turned on.
- **`safety-critical-changes.md` rule 1 tells you to stop, and does not say what to do
  instead when the change *is* a guard.** Four rounds, HIGHs every time, severity never
  below three. Rule 1 prescribes "a deterministic artifact" — but for a guard over an
  unbounded space of edits, the artifact is the thing under review. Stopping produced a
  deletion that was too broad; not stopping would have produced a fifth round. What
  actually resolved it was a reviewer running the *counterfactual* (restore the deleted
  code into each bypass), which no rule asks for. **M** — proposed fix: add a
  counterfactual step to the panel contract for any round that removes a guard — restore
  it and measure, rather than reasoning about whether it was load-bearing.
- **`pr_watch.py:687` still discards the 403 body and asserts a cause it cannot know.**
  `#130` corrected the *record* about this; the defect itself has no ticket. In a web
  container the whole API host is path-blocked, so `pr_watch` cannot arbitrate a merge
  gate at all — both of this session's merges were reconstructed from MCP calls by hand.
  **M** — proposed fix: surface the response body, and have the REST transport detect the
  proxy sentinel and name the GitHub MCP as the supported path. Needs a ticket.
- **`session-start`'s tracker step overflows its own tool limit at 68 open issues.** The
  MCP `list_issues` call returned 177k characters and had to be re-read from a spill file
  and field-filtered by hand. The workflow already warns that a naive "dump everything"
  call overflows, and prescribes a field-limited call — but the MCP tool exposes no field
  selection, so the prescription cannot be followed on this backend. **L** — proposed fix:
  the workflow's tracker step needs a backend-specific note for GitHub-Issues-over-MCP:
  page at `perPage: 25` and read `number`/`title`/`labels`/`state` only.
- **CodeRabbit registered nothing on a fourth consecutive PR.** `#126`, `#129`, `#130`,
  `#131` — no check, no comment, past grace on all four. The fallback panel was the only
  independent pass every time. **No new fix proposed** — occurrence data for `#45`/`#23`,
  now with four consecutive instances behind it rather than one.
- **`#113` reproduced a third time.** `chore/update-handoff-2026-07-28` already existed on
  the remote, so the wrap-up branched as `chore/wrap-up-2026-07-28-mutation-gate` by hand.
  **No new fix proposed** — third occurrence, still no mechanism.

## Graduated 2026-07-28 — GitHub Issues (#112–#125)

Swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine tracked
in [#6](https://github.com/topij/agentic-dev-kit/issues/6) is not vendored yet).
Twenty-four entries in, twenty-four accounted for: **thirteen graduated** into new
issues, **ten** routed as occurrence comments on the issues they are evidence for, and
**one** discharged by work that has since landed.

The thirteen graduated entries became
[#112](https://github.com/topij/agentic-dev-kit/issues/112)–[#120](https://github.com/topij/agentic-dev-kit/issues/120)
and [#122](https://github.com/topij/agentic-dev-kit/issues/122)–[#125](https://github.com/topij/agentic-dev-kit/issues/125)
— [#121](https://github.com/topij/agentic-dev-kit/issues/121) sits inside that numeric
range but is not one of them (see below). Four of the twenty-four entries were rated
**H**; three of the four became issues:

- [#112](https://github.com/topij/agentic-dev-kit/issues/112) — the manifest-hash gate
  reads as test coverage but is discharged by one `--generate-manifest` run, so any
  mutation result on a `KIT_OWNED` file is void unless the manifest is regenerated
  first. Inverse symptom of [#33](https://github.com/topij/agentic-dev-kit/issues/33),
  cross-referenced there.
- [#113](https://github.com/topij/agentic-dev-kit/issues/113) — a push-then-PR step can
  open a PR against a stale remote branch and exit 0; this is how `#81` came to carry
  160 insertions / 249 deletions **against `main`**, reverting the day's merged work.
  (The qualifier matters: GitHub's own file view of `#81` reports a different figure,
  because it diffs against the merge base rather than against `main`.)
- [#114](https://github.com/topij/agentic-dev-kit/issues/114) — a test written from the
  fix's own framing can pin the bug as correct; the mutation was killed by that test.
- The fourth, **`make test` is undiscoverable**, is the one entry recorded as
  **discharged**: its proposed fix was a root `CLAUDE.md` naming `make test` as *the*
  verification command, and that file now exists and does exactly that. Verified by
  reading `CLAUDE.md` in this repo at commit `18768fc`.

[#121](https://github.com/topij/agentic-dev-kit/issues/121) was not an inbox entry — it
was surfaced *by running this workflow*: `config/dev-model.yaml`'s `tracker:` block is
still `init.sh` placeholder (`backend: linear`, blank ids) while this repo's real
tracker is GitHub Issues on itself, which the engine in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) will read the moment it lands.

The ten occurrence comments went to
[#42](https://github.com/topij/agentic-dev-kit/issues/42) (one entry),
[#45](https://github.com/topij/agentic-dev-kit/issues/45) (three),
[#54](https://github.com/topij/agentic-dev-kit/issues/54) (one),
[#74](https://github.com/topij/agentic-dev-kit/issues/74) (two),
[#75](https://github.com/topij/agentic-dev-kit/issues/75) (one),
[#76](https://github.com/topij/agentic-dev-kit/issues/76) (one), and
[#118](https://github.com/topij/agentic-dev-kit/issues/118) (one) — summing to ten, so
`13 + 10 + 1 = 24` closes.

Two clarifications the review panel forced, because the first version of this section
did not survive an audit:

- **[#33](https://github.com/topij/agentic-dev-kit/issues/33) is not in that list.** It
  received a *cross-reference* to #112 — a **graduated** entry, already counted among the
  thirteen — not occurrence data for any of the ten. Listing it made the enumeration sum
  to eleven against a stated ten, so `24` in produced `25` out.
- **Not all ten carried *"No new fix proposed"***. Five did; the rest (notably the
  entries routed to #54, #118 and #42) proposed a fix that belonged on an **existing**
  issue rather than a new one. Being comment-shaped rather than ticket-shaped is what
  they have in common, not the absence of a proposal.

Three of the twenty-four entries also named
[#23](https://github.com/topij/agentic-dev-kit/issues/23) alongside #45 as a routing
target; that comment was posted after the panel caught its omission.

The panel itself produced two further issues, neither from the inbox:
[#127](https://github.com/topij/agentic-dev-kit/issues/127) — nothing mechanically
distinguishes a sweep from a deletion, and `check_doc_budget` scores the deletion higher
(proved by wiping both files and watching every gate stay green) — and
[#128](https://github.com/topij/agentic-dev-kit/issues/128), the skill's notify-channel
stop having no in-session-operator exception, which this run violated.

All twenty-four entries are kept verbatim below for the trail, along with the prior
graduation marker. Note that the swept text includes the previous sweep's closing line,
*"Everything swept now lives in `kit-friction-log-archive.md`"*, which is now a self-link
inside the archive it names — the class [#73](https://github.com/topij/agentic-dev-kit/issues/73)
exists for. It is left byte-identical deliberately: rewriting swept content would break
the verbatim property that makes this archive auditable.

### 2026-07-27 — Backlog migrated to GitHub Issues (#70–#77)

The inbox was swept by the `triage-friction-log` workflow. Thirteen entries in,
thirteen accounted for: **twelve graduated** into eight issues, **one** recorded a
measurement with *"No change proposed"*.

Four issues each merge **two** entries recorded on separate days, because the repeat is
the evidence — splitting them would lose the occurrence count that made them
issue-shaped:

- [#70](https://github.com/topij/agentic-dev-kit/issues/70) — a mutation harness that
  restores outside `finally` leaves the repo mutated; the tree must be checked *after*
  the harness exits, not only after a successful run.
- [#71](https://github.com/topij/agentic-dev-kit/issues/71) — build the
  closing-keyword guard: every match, every surface, no stripping, and the squash
  message checked at merge time. *Three occurrences across two sessions.*
- [#72](https://github.com/topij/agentic-dev-kit/issues/72) — `pr-watch` should warn at
  push time when a bot review no longer covers head, not only at receipt time.
- [#73](https://github.com/topij/agentic-dev-kit/issues/73) — the archive sweep must
  warn on relative cross-references in **both** directions. *Two occurrences; the second
  broke a reference the first sweep had written.*
- [#74](https://github.com/topij/agentic-dev-kit/issues/74) — the doc-budget remedy is a
  no-op at the default `--keep` (it measures lines, the sweep keeps blocks). *Three
  occurrences, two in this repo.*
- [#75](https://github.com/topij/agentic-dev-kit/issues/75) — invert contract item 7:
  assume the isolated worktree points at the wrong ref. *Nine of nine across two
  sessions.*
- [#76](https://github.com/topij/agentic-dev-kit/issues/76) — `--record-review` cannot
  record honest partial coverage, so the honest choice erases the trail.
- [#77](https://github.com/topij/agentic-dev-kit/issues/77) — nothing constrains the
  cockpit from editing the shared tree while a panel reviews it.

The thirteenth entry — the panel-disjointness measurement — carried *"No change
proposed"*: it is a second, stronger data point for the disjointness argument in
`fallback-review-panel.md`, which currently rests on one.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

### 2026-07-27

- **The kit has a working local test command and nothing points at it.** `make test`
  runs the full suite — **372 passed in 22s** — supplying its own dependencies via
  `uv run --with pytest --with pyyaml`. But the two probes an agent reaches for first
  both fail in a way that reads as *"pytest is unavailable in this environment"*:
  `uv run pytest` → `Failed to spawn: pytest`, `python3 -m pytest` → `No module named
  pytest`. **No markdown file in the repo mentions `make test`**, and there is no root
  `CLAUDE.md`. This session concluded the environment could not run tests, deferred
  verification to CI on two PRs, and wrote *"tests were not run locally — pytest is not
  installed"* into the body of a **merged** PR (`#80`); corrected afterwards by comment.
  **H** — proposed fix: a root `CLAUDE.md` naming `make test` as *the* verification
  command. `#54` requires every verification claim to name the command that establishes
  it, and that has no chance of holding while the only working command is undiscoverable.
  Same family as `#54`.
- **The `Makefile`'s `test` target claims a local gate that does not exist.** Its comment
  says the target *"Runs the same suites the lane contract's local gate runs before every
  push."* There is no such gate: `scripts/hooks/pre-push` deliberately runs no tests
  (line 23 — checks are kept separate and independently testable), and
  `scripts/dev_session.sh` runs none either. **M** — proposed fix: either correct the
  comment to describe what exists, or make it true by having `pre-push` run `make test`.
  The second is a design call, not a patch — `pre-push`'s own comment argues for keeping
  checks separate, and 22s lands on every push. Same family as `#54`: a comment claiming
  more than the code does.
- **The triage skill's default output is a PR its configured reviewer will never read.**
  `finalize.pr_draft` defaults to `true`, and CodeRabbit skips draft PRs outright
  (*"Review skipped: draft pull request"*). So `triage-friction-log`'s happy path
  produces a draft PR that receives no bot review, and nothing in the skill says so —
  the operator discovers it only when the review gate will not close. **M** — proposed
  fix: either default `pr_draft` to `false`, or have the skill state that a draft PR
  needs `@coderabbitai review` or a ready-flip before the review gate can be satisfied.
  Surfaced on `#78`.
- **The wrap-up branch name collides on a same-date session, and `gh pr create` turns
  the collision into a PR that reverts the day's merged work.** The handoff branch is
  `chore/update-handoff-{date}`, so a *second* session on the same date recreates an
  identical name off the current `main`. The push is correctly rejected as a
  non-fast-forward — but `gh pr create` then opens a PR against the **pre-existing
  remote branch**, exits 0, and prints a PR URL. `#81` was opened this way: it carried an
  earlier session's commits, cut from a base predating today's merges, so its diff was
  **160 insertions / 249 deletions against `main`** — un-graduating the friction inbox,
  deleting 186 lines of archive, and undoing the `reports/` work. Merging it would have
  reverted both PRs that landed earlier the same day. Caught only because the
  rejected-push hint and the PR URL landed in the same output and the head sha was then
  compared. **H** — proposed fix, two parts: (1) uniquify the wrap-up branch name (short
  sha suffix) or fail loudly when the remote branch already exists; (2) more general and
  more important — any workflow step that pushes and then opens a PR must **verify the
  push landed** before creating it. `git push -q && gh pr create` is not sufficient: with
  `-q` the rejection is a stderr hint, the exit status is swallowed by the chain, and the
  PR gets created against whatever the remote already had. Compare remote head to local
  `HEAD` first.
- **A rate-limited CodeRabbit reports its check as `pass` — two more instances.** `#78`
  and `#80` both merged with a green `CodeRabbit` check that had reviewed nothing
  (*"Review limit reached"* / *"Review rate limited"*). `pr_watch` handled both correctly
  — recorded `unavailable` and refused to converge on missing review evidence — so the
  engine is not the problem; the hazard is the **check rollup**, which reads as reviewed
  to any human scanning it. **No new fix proposed** — recording two further occurrences
  for `#45` / `#23`. `kit-handoff-history.md` records CodeRabbit rate-limiting in an
  earlier session too, so this is at least the third.

### 2026-07-27 (third session of the day)

- **`pr-watch` prescribes the fallback panel on ANY reviewer outage; a short rate-limit
  window makes re-triggering strictly better.** Recovery windows observed this session
  ranged from 13s to 48min across `#83`/`#85`/`#87`. When short, `@coderabbitai review`
  after the window produced a real review of the exact head — stronger evidence than a
  panel receipt, at zero cost. Neither `pr-watch.md` nor the workflow's
  reviewer-unavailable branch mentions the notice's "Next review available in" field or
  the re-trigger command. **M** — proposed fix: the reviewer-unavailable branch should
  read the recovery window from the outage notice; short window → wait and re-trigger,
  then fall back to the panel only if that fails; long window on a risky diff → run the
  panel now and offer the recovered bot the final head afterwards. The re-trigger half
  is validated (`#83`; `#85`'s recovered pass covered its full final diff); the
  offer-the-final-head half can still end in an acknowledged gap — `#87`'s last push
  rate-limited again and merged with the coverage gap recorded on the receipt.
- **`gh api -X PATCH … -f body=@-` writes the literal string `@-`, destroying the
  comment.** Only `-F` performs `@`-file/stdin expansion; `-f` is always a string. Three
  freshly-posted issue comments were clobbered to `@-` this session and caught only
  because a later edit re-read one. **L** — proposed fix: any workflow step that edits a
  GitHub comment via `gh api` should use `-F body=@<file>` and verify the comment's
  body length (or a content marker) after the PATCH.

### 2026-07-27 (fourth session of the day)

- **A test written from the fix's own framing can pin the bug as correct.** My
  `comparable_max_total` reset disabled the false-settle guard on the DEFAULT `gh`
  backend (`mergeable` false → **true** for every existing PR), and the test I wrote
  alongside it asserted `settling is False` / `converged is True` as the *desired*
  outcome. So the suite pinned the permissive direction and nothing pinned the guard —
  a mutation removing the reset was **killed by my own test**. Two review lenses found
  it independently; the suite could not, by construction. **H** — proposed fix: for a
  change to a gate, the test must assert the *blocking* direction survives, not that the
  new behaviour occurs. Worth a line in `safety-critical-changes.md`: when a fix changes
  what a guard concludes, pin the guard's refusal first and the fix's effect second.
- **`archive_plan_sessions.py`'s default `--keep 6` is a no-op remedy — fourth
  occurrence, third in this repo.** (The graduated-issue note above already records
  three, two here.) `check_doc_budget` warned at 470/400 lines and
  the sweep answered *"nothing to move: 6 session block(s) <= --keep 6"*, leaving the
  file over budget with the warning still firing. `--keep 4` moved 2 blocks and brought
  it to 314. This is `#74` exactly; recording the recurrence because the wrap-up workflow
  tells the operator to run the sweep and the sweep does nothing at its default.
  **M** — no new fix proposed beyond `#74`: the remedy should take the *budget* as input
  and drop blocks until it fits, rather than counting blocks.
- **Chaining `make test` into commit-and-push let me push a red tree.** I ran
  `make test && git commit && git push` as one compound command, `make test` failed on a
  stale manifest hash, and the failure scrolled past while the commit and push
  succeeded. CI on that head went red. **M** — proposed fix: the wrap-up and lane
  contracts should say verification runs as its **own** step whose result is read before
  anything is committed; a compound `&&` chain that ends in a push makes the failure
  invisible at exactly the moment it matters. Related to `#54` (name the command that
  established a claim) but distinct: here the command ran and its answer was ignored.
- **`--record-review` un-converges the PR it just certified, and the merge then needs a
  second `--mark-seen`.** Posting the coverage record made `converged` false (my own
  comment is a new comment), so `mergeable` went false with an *empty* `merge_blockers`
  list — which reads as "no reason" to anyone scanning it. Acking cleared it. This is
  `#42`; recording an occurrence plus the detail that the empty blocker list makes the
  cause unguessable from the JSON alone. **L**
- **The provided worktree was at the base ref on 5 of 5 panel launches this session**
  (`main`, empty diff), and every lens detected and corrected it because the launch
  prompt required clone-verify-report. **No cumulative figure claimed**: the earlier
  sessions' "8 of 8" counts launches that isolated *correctly*, so it cannot be added to
  a count of launches that pointed *wrong* — an easy error to make and worth not making
  in the record. **No new fix proposed** — occurrence data posted to `#75`.
- **CodeRabbit rate-limited three times in one session**, once still limited at merge
  time, and **its recovery-window figures are not retrievable afterwards** — it edits the
  rate-limit notice comment in place, so a window read live (41 minutes on `#91` this
  session) is overwritten by the next edit and cannot be audited later. That is the
  finding: every claim in this log about a recovery window is an ephemeral observation
  with no artifact behind it, which is why they keep failing verification. **L** —
  proposed fix: when the reviewer-unavailable branch reads the window, record the value
  and the timestamp on the PR, so the decision to wait-and-re-trigger versus run the
  panel is auditable. Supports the session-3 entry proposing that branch.

### 2026-07-28

- **A reviewer's plan quota is not a rate-limit window, and `unavailable_markers`
  cannot tell them apart.** CodeRabbit's notice read *"you've reached your PR review
  limit … Next review available in: 56 minutes"*, but re-triggering two minutes past
  that window produced nothing, and it never registered a check on the next PR either.
  The kit's reviewer-unavailable branch assumes a window you can wait out and re-trigger
  after — the session-3 entry above is built entirely on that assumption. A quota needs
  the panel immediately and no re-trigger attempt. **M** — proposed fix: distinguish the
  two in the unavailable branch; treat *"review limit reached"* as non-recoverable
  within the session rather than something to wait out.
- **A three-space list continuation is correct CommonMark and silently renumbers the
  list under Python-Markdown.** `1. ` is three columns, so three spaces is the
  CommonMark content column and GitHub rendered it correctly — Python-Markdown requires
  four and otherwise closes the list, emitting a fresh `<ol>` that restarts at 1. In
  `safety-critical-changes.md` that turned rule 4 into rule 1 while the header still
  said *"Four rules apply"*, and ten files outside the session records cite those rules
  by number (fourteen counting the records themselves). A bot review of
  that exact head passed it clean; rendering in both engines caught it. **M** — proposed
  fix: render kit-owned docs in both engines as a check, or fix the convention at
  four-space continuations and say so where the docs are edited.
- **A gate that reads labels nothing produces is not a gate.** `#102` shipped a rule
  keying on finding severity and a regression/imprecision axis — both lens *output* —
  when no contract item and neither `focus` string in `dev-model.yaml` ever asked a lens
  for either. It read as working only because the cockpit supplied severity ad hoc in
  its own launch prompts, which is exactly the drift the panel doc's single-source rule
  exists to prevent. Fixed in-PR (contract item 9), recorded because the *class* is
  general: any doctrine that consumes a field must name where the field is required.
  **M** — proposed fix, beyond `#102`: when a rule starts consuming a lens-reported
  field, the contract must be amended in the same change.
- **A rate-limited CodeRabbit reported its check as `SUCCESS` again** — on `#101`'s
  `4a0d499`. Correcting this entry as first merged, which got both attributions wrong.
  The false green did not sit on the defective diff: `4a0d499` is the head that *fixed*
  the indentation bug above, and the head that carried the bug (`d8bf1af`) received a
  genuine completed review that passed it clean — the next entry. Nor was it the first
  false green that could have shipped something: `#91`'s final head `d96d4a1` reported
  `SUCCESS` / *"Review rate limited"* while panel round 3 found ~7 HIGH against that
  exact head. **No new fix proposed** — occurrence data for `#45` / `#23`.
- **A fully working bot review missed a defect that renumbered doctrine.** `#101`'s
  first head `d8bf1af` — the one carrying the indentation bug — received a genuine,
  completed CodeRabbit review (walkthrough, five pre-merge checks passed) that
  reported it clean, while the defect turned rule 4 into rule 1 in a file ten others
  outside the session records cite by number. That is a worse failure mode than the
  rate-limited false green, which reviewed nothing: this review ran and vouched for
  the head. It was recorded
  nowhere — the entry above had attributed the miss to the rate-limited pass. **M** —
  no fix proposed beyond the render-in-both-engines check the indentation entry
  proposes; recorded so "bot reviewed and missed it" is not conflated with "bot never
  reviewed", which the occurrence data for `#45` / `#23` counts.
- **`#76` reproduced twice in one session.** Neither `#101` nor `#102` had its final
  head reviewed by any lens, and `--record-review --head` can only assert that the exact
  head was reviewed — so on both the honest choice was to record nothing and write the
  coverage table into a PR comment instead. Both merged with `mergeable: false` and an
  explicit operator decision. **No new fix proposed** — occurrence data for `#76`, with
  the detail that the honest path always forces an operator merge.
- **Deferred from `#102`, not yet issue-shaped**: the act-on gate has a fail-closed
  default for an ambiguous *change* but none for an ambiguous *finding*, and the party
  resolving that axis is the author who benefits from the cheaper answer (contract item
  9 now pushes it to the reporting end, which is a mitigation rather than a fix); the
  *"say which one you applied in the PR"* antecedent now has two candidates;
  `docs/CLAUDE-sections.md:116-118` enumerates the doctrine as five items for adopters
  to paste and is now incomplete; step 5 gains no forward pointer to the gate that
  narrows it; and class 2's worst-case test (*"a wrong message"*) fits a report field
  better than a doctrine file, which is acted on by every future author. **L**
- **The manifest-hash gate reads as test coverage and is not.** Three times this session
  a mutation to new behaviour was "caught" only by `test_kit_repo_self_check_is_clean`,
  which compares `kit-manifest.json` hashes. That gate is discharged by one documented
  command (`kit_doctor.py --generate-manifest`) — exactly what a real edit would run —
  after which the mutant is fully green. Any mutation result on a `KIT_OWNED` file is
  therefore meaningless unless the manifest is regenerated first, and a reviewer who
  skips that step will record a kill that did not happen. **H** — proposed fix: have the
  mutation-testing guidance (and `#33`, which already covers the false-kill direction)
  state the regenerate-first step as mandatory, and consider making `--generate-manifest`
  refuse to run against a tree with uncommitted engine edits so the discharge is visible.
- **A verification claim can be true, name a command, and still mislead through scope.**
  Two of this session's false claims survived because the command cited was narrower than
  the claim: `git status --porcelain docs/` supports "docs/ untouched" but was offered as
  evidence for "the only side effect is a root `AGENTS.md`", which the unscoped command
  disproves; and "fresh render in a scratch clone → all five docs seeded" omitted the
  `rm docs/kit-*.md` the run actually began with. `#54` requires naming the command; it
  does not require that the command's scope match the claim's scope. **M** — proposed
  fix: extend `#54` to "name the command *and* the setup it ran against", or require the
  claim to be restated as exactly what the command shows.
- **Panel rounds converge on the code long before they converge on the prose.** Round 5
  found zero code regressions after 4000 differential probes, while still returning six
  imprecisions in the commit message. Every round from 1 to 4 found a false claim in the
  previous round's fix, and none of those were in shipped behaviour — they were in
  descriptions of it. The current stopping criterion (blast radius) handles the code well
  and gives no guidance for prose, so the choice to stop was mine each time rather than
  the doctrine's. **M** — proposed fix: consider a separate, cheaper terminal check for
  record accuracy — one lens, message-only, run once before merge — rather than carrying
  prose review through every full round at full cost.
- **`#74` reproduced during this very wrap-up.** The budget check reported
  `docs/kit-handoff.md` at 463/400 and prescribed the archive sweep; the sweep at its
  default `--keep 6` reported *"nothing to move: 6 session block(s) <= --keep 6"* and the
  doc stayed at 463. The prescribed remedy is a no-op precisely when the warning fires,
  because the check counts **lines** and the sweep keeps **blocks**. Getting under budget
  needed `--keep 4`, chosen by trying `--dry-run` until the projected line count fit —
  i.e. the operator does the search the tool should do. **No new fix proposed** — third
  occurrence for `#74`, now with the detail that the workflow text (*"it deterministically
  keeps the newest ~6 session blocks"*) names the default that fails, so an agent
  following wrap-up literally will run the no-op, see the warning persist, and have no
  documented next step. Worth having the sweep accept a target line count, or having the
  budget check emit the `--keep` that would satisfy it.

## Graduated 2026-07-27 — GitHub Issues (#70–#77)

Swept by the `triage-friction-log` workflow. Thirteen entries, fully accounted for:
**twelve graduated** into eight issues ([#70](https://github.com/topij/agentic-dev-kit/issues/70)–[#77](https://github.com/topij/agentic-dev-kit/issues/77)),
four of which each merge two entries recorded on separate days; **one** recorded a
measurement with *"No change proposed"*. All thirteen are kept below for the trail,
along with the prior graduation marker.

### 2026-07-26 — Backlog migrated to GitHub Issues (#54–#56)

The inbox was swept by the `triage-friction-log` workflow. Three entries graduated:

- [#54](https://github.com/topij/agentic-dev-kit/issues/54) — every verification claim
  must name the command that establishes it (supersedes the narrower "wrap-up should
  fact-check the handoff" proposal).
- [#55](https://github.com/topij/agentic-dev-kit/issues/55) — `safety-critical-changes.md`
  rule 1 should name a tightening threshold.
- [#56](https://github.com/topij/agentic-dev-kit/issues/56) — removing a mechanism
  requires enumerating what it was rejecting.

Three further entries needed no ticket: their proposed fixes had **already shipped** in
PR #31 — the panel contract now requires lenses to execute and mutation-test (contract
items 4–5), rule 3 carries the blast-radius stopping criterion, and contract item 7
mandates isolated worktrees.

The remaining five: four were already tagged with an issue id (#10, #18, #19, #33), and one
recorded a guard working correctly with *"No change proposed"*. Eleven entries in, eleven
accounted for.

Everything above now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

### 2026-07-27

- **A mutation harness that restores outside `finally` leaves the repo mutated.** My
  restore line was unreachable when the script died parsing pytest output (a bare
  `python3` with no pytest returned no stdout, and `splitlines()[-1]` raised). The
  working tree kept a live mutant until `git status` caught it. Neither existing warning
  covers it: `#50` is about stale `.pyc`, and `fallback-review-panel.md` contract item 5
  warns only about **false kills** from a checksum/drift test (it does not mention
  `.pyc` at all). Both frame the hazard as "the result may be wrong"; neither says the
  repo may be left broken. **H** —
  proposed fix: contract item 5 should say the restore belongs in a `finally` (or a
  git-clean check) and that any harness must verify the tree is clean *after* it exits,
  not only after a successful run.
- **The closing-keyword trap fired again, because I weakened a correct rule on the
  strength of an experiment that did not test what I thought.** `#61` was closed by the
  squash-merge of `#68` and reopened by hand.

  **What is actually measured** — three data points, with their confounds stated,
  because two earlier write-ups of this stated more than the data supports:

  | artifact | form | outcome |
  | --- | --- | --- |
  | `#68` body | `Closes #61` inside a **fenced block** | inert (`closingIssuesReferences: []`) |
  | `9c6ab3a` commit message | `Closes #61` in an **inline** span | **fired** — closed `#61` |
  | `#63` body | `Does NOT close #60` **and** a plain `fix #60` | fired; which one is **not isolated** |

  **What is NOT measured, though I twice wrote as if it were:** whether an *inline* span
  is inert in a PR body. The two backtick data points differ in **two** variables at once
  — fenced-vs-inline *and* body-vs-commit — so "GitHub excludes inline code spans" and
  "fenced blocks are inert everywhere, inline spans fire everywhere" fit the evidence
  equally well. Under the second reading, the fix I proposed last round (strip inline
  code from a PR body before checking) reopens the exact hole that closed `#61`.

  Likewise the *negation* hypothesis: `#63`'s body carries a plain, non-negated `fix #60`
  alongside the negated mention, so a check that only flags keywords **near a negation**
  would have passed that body clean.

  **H** — **stop deriving a mechanism; take the conservative rule.** Three attempts to
  state this precisely have each been wrong, which is rule 1's threshold. The original
  2026-07-26 rule below — never write a closing keyword adjacent to an issue number you
  do not intend to close, in any form, on any surface — would have prevented all three
  incidents; the measurement talked me *out* of a correct rule. It stands as written, and
  the proposed check follows it rather than any theory of markdown:

  - flag **every** match on **every** surface — PR body, every commit message, and the
    squash message — with **no stripping** of code spans or fenced blocks;
  - cover the forms the naive regex misses and GitHub honours: `owner/repo#61`, a full
    issue URL, and `Closes: #61` (a colon, not whitespace);
  - check the **squash message at merge time** specifically. It is composed *after* the
    PR body was reviewed, and nothing reviews it — verified: `9c6ab3a`'s message matches
    neither `#68`'s title, its body, nor any of its three branch commits, and no hook in
    `scripts/` inspects commit messages at all;
  - the operator confirms each match. Over-firing is the acceptable failure here.

  Occurrence count, corrected: **three occurrences across two sessions** (`#63` and `#64`
  were the same session; `9c6ab3a` is this one).
- **A review bot with an incremental model keeps a stale review across a rewrite.**
  CodeRabbit reviewed the pre-split head, then declined `@coderabbitai review`
  ("does not re-review already reviewed commits") and hit its Fair Usage limit on
  `@coderabbitai full review`. The PR was force-pushed and then substantially rewritten,
  so the only bot review covered code that no longer existed. `pr_watch`'s
  `bots_behind_head` recorded it correctly — the friction is that **nothing warns at
  push time**, when re-requesting is still cheap. **M** — proposed fix: have `pr-watch`
  surface `covers_head: false` as a distinct, louder line right after a push that
  changes the diff shape, rather than only at receipt time. Related: `#27`, `#44`.
- **The panel's worth is disjointness, and this run measured it.** Round 1: the
  adversarial lens found the enclosing-repo and `GIT_DIR` regressions; the correctness
  lens independently found the `~`-expansion disagreement between `init.sh` and the new
  detector. Almost no overlap. Round 2's correctness lens then found the *misattributed
  defect* — a false sentence in the commit message written to describe round 1's own
  outcome, which could not have existed when round 1 ran. **No change proposed** —
  recording it because `fallback-review-panel.md` argues disjointness from one prior
  data point, and this is a second, stronger one worth citing there. Note the honest
  framing of what the panel beat: the four regressions were missed by CI, by the suite
  **as it then stood**, and by the mutation run **at that head** — not by the 372-test
  suite quoted elsewhere, which only exists *because* those findings were fixed.
- **The archive sweep broke a cross-reference again — and this time it broke one the
  PREVIOUS sweep had written.** The 2026-07-26 entry below reports the sweep orphaning
  *"see the Phase 3b block above"*. Today's sweep moved Phase 3b itself into the history
  file, so the surviving text — *"see the Phase 3b block, still live in
  kit-handoff.md"* — became false in a second way: the target is now in the very file
  the sentence sits in. Fixed by hand in this commit. **M** — the entry below proposes
  warning on `(above|below)`-style references in *moved* blocks; this instance shows the
  warning must also cover references **into** a moved block from anywhere in either
  document, since the block that moved was the reference's *target*, not its location.
  Same family as `#53`.
- **The doc-budget remedy no-op reproduced a third time** (see the 2026-07-26 entry
  below). `check_doc_budget` reported 421/400; the remedy it names printed *"nothing to
  move: 5 session block(s) <= --keep 6"*; `--keep 4` was needed and found by guessing.
  **No new fix proposed** — recording the third occurrence. The entry below already
  records two; this makes it three, two of them in *this* repo, which is a pattern
  rather than a run of bad luck.
- **A review lens's isolated worktree pointed at the wrong ref again — 5 of 5 this
  session, 9 of 9 across two.** (Last session's entry below records 4 of 4; this session
  ran 2 lenses × 2 rounds on `#65` plus 1 on `#68`.) Every lens detected it and cloned
  the target itself, because the prompt required reporting the path and diff stat.
  **H** — proposed fix: this is no longer a
  caveat, it is the default behaviour. Contract item 7 should stop saying "verify" and
  start saying "assume the worktree is wrong; clone the target yourself first", with the
  path/diff-stat report as a required field of the lens output (the existing 2026-07-26
  entry proposed the report; this one is about inverting the default).

### 2026-07-26

- **The doc-budget remedy does not fire at the default `--keep`.** `check_doc_budget`
  measures **lines**; `archive_plan_sessions` keeps **blocks**. This handoff hit
  448/400 lines with 5 blocks, so the remedy the warning names printed *"nothing to
  move: 5 session block(s) <= --keep 6"* and the file stayed over budget. The agent has
  to guess a `--keep` and re-run until the line count drops — which is exactly the
  manual fiddling the deterministic engine exists to remove. **M** — proposed fix: give
  `archive_plan_sessions` a `--target-lines` mode (sweep oldest-first until under
  budget), or have `check_doc_budget`'s remedy string compute and name the `--keep` that
  would work. Reproduced twice this session (kit and cs-toolkit).
- **A runtime's isolated worktree points at the session's base ref, not the PR head.**
  All **four** review-lens launches this session (2 lenses × 2 rounds) landed on `main`
  with an empty `git diff main...HEAD`. Every one detected it and cloned the real target
  — because the launch prompt required them to *report the path and diff stat they saw*.
  `fallback-review-panel.md` contract item 7 says to verify; what actually surfaced it
  was making the report **mandatory output**. **H** — proposed fix: promote "state the
  path reviewed and the diff stat" from advice to a required field of the lens report in
  contract item 8, and say plainly that a lens which cannot show a non-empty diff has not
  reviewed anything. A clean pass over an empty diff is indistinguishable from a real one.
- **`--record-review` has no way to record honest partial coverage.** It correctly
  refuses a receipt bound to a stale head (`PR head changed during review`), but the only
  alternative is a receipt claiming the current head — which the panel did not review. So
  the honest choice is **no receipt at all**, and the audit trail then loses the fact that
  a two-lens panel ran at all. **M** — proposed fix: allow recording against the reviewed
  sha with the head-gap represented rather than rejected (the existing `bots_behind_head`
  field is the precedent). Related: #32.
- **Negating a GitHub closing keyword still arms it.** A PR body was edited before merge
  to retract a closure claim; the retraction read *"Does NOT close #60"*. GitHub matched
  `close #60`, and merging closed an issue documenting an **unfixed** bug. Caught after
  the fact and reopened. **M** — proposed fix: one line in the wrap-up / pr-watch
  doctrine — never write a closing keyword adjacent to an issue number you do not intend
  to close, even negated; write "#60 stays open". cs-toolkit's `CLAUDE.md` already carries
  the Linear-side twin of this hazard.
- **The cockpit edited the shared tree while lenses were reviewing it.** A lens reported
  the shared checkout changing mid-run (5 files, mtimes inside its window) and correctly
  noted it was not the author. Its own review was unaffected — it worked from an isolated
  clone — but it had to spend output distinguishing "concurrent editor" from "corruption".
  Contract item 7 constrains the **lenses**; nothing constrains the **cockpit**. **M** —
  proposed fix: add a cockpit-side clause — do not mutate the shared tree between
  launching a panel and reading its findings.
- **The archive sweep breaks *relative* cross-references, and its docstring says it
  doesn't.** `archive_plan_sessions.py:20` claims *"It only ever moves content — every
  cross-reference (ticket ids, PR links, commit shas, …) is preserved."* Every kind it
  enumerates is **absolute**. A relative one is not preserved: this session's sweep moved
  the Phase 3a block into the history file while Phase 3b stayed live, orphaning
  *"see the Phase 3b block above"* — the target is now in a different file. Caught by
  CodeRabbit on the wrap-up PR, not by the sweep, which reported success. **M** —
  proposed fix: have the sweep scan moved blocks for `(above|below)`-style references
  and warn (not rewrite — rewriting is the class of surgery `init.sh`'s deleted marker
  migration proved dangerous). Same family as #53, which is about the pointer the sweep
  *writes*; this is about the references it *carries*.

## Graduated 2026-07-26 — GitHub Issues (#54–#56)

Swept by the `triage-friction-log` workflow. Eleven entries, fully accounted for:

- **3 graduated** to issues [#54](https://github.com/topij/agentic-dev-kit/issues/54),
  [#55](https://github.com/topij/agentic-dev-kit/issues/55) and
  [#56](https://github.com/topij/agentic-dev-kit/issues/56).
- **3 needed no ticket** — their proposed fixes had already shipped in PR #31.
- **4 were already tagged** with an issue id (#10, #18, #19, #33).
- **1 recorded a guard working correctly**, with *"No change proposed"*.

All eleven are kept below for the trail.

### 2026-07-25 — Backlog migrated to GitHub Issues

Two H-severity entries were **removed from this file** and filed as
[#26](https://github.com/topij/agentic-dev-kit/issues/26) (fallback review needs to be a
*panel*) and [#27](https://github.com/topij/agentic-dev-kit/issues/27) (a receipt
survives a redesign its reviewer never saw). #27's cheap half shipped in PR #29; the
issue stays open for the shape-change half.

Also closed this session, so their inbox entries below are **done**, kept only for the
trail: **#19** (premature receipt — closed by PR #25) and **#10** (lane-worktree gate
failure — closed by PR #28).

### 2026-07-25 — inbox

- **The `cp -r` quickstart can't distinguish kit-owned from adopter-owned files (severity: M).**
  Any file the kit tracks lands in an adopter's repo, which is why this repo's own narrative
  docs had to be renamed `kit-*.md` rather than simply filled in. `kit-manifest.json` now
  encodes the ownership boundary (`adopter_owned`), so a manifest-aware installer could copy
  correctly and the rename would become unnecessary. Filed as issue #18.

- **`--record-review` accepts a receipt while the primary bot is still queued (severity: M).**
  Recorded a fallback receipt on #16 when CodeRabbit's check read `PENDING — Review queued`;
  its four valid findings landed after the merge. The doctrine distinguishes *unavailable*
  from *slow*, but nothing mechanically does. Candidate: treat a configured bot's own
  `PENDING` check as a merge blocker while no receipt exists — but that inverts the
  informational-check exclusion in the one case where the exclusion is load-bearing (it is
  what stops the loop wedging on a bot that never reports), so it needs care. Filed as #19.

- **A lane's local gate fails for reasons unrelated to its diff (severity: H).**
  All three lanes this session hit the same two `state_paths` test failures, caused purely by
  running from inside a marker-carrying worktree. A gate that goes red for environmental
  reasons teaches agents to ignore a red gate. Already filed as issue #10 — raising severity
  here because three independent occurrences in one session makes it a pattern, not an
  incident.

- **A fix round on gate logic is where the next bug comes from — every time (severity: M, pattern).**
  Seven review rounds on PR #25. Every one found something real, and **rounds 3 through 7
  each found a defect introduced by the previous round's fix**: an incomplete poison-clock
  fix that still wedged on a *parseable* future date (R3); a section-scoping fix applied
  to 1 of 3 guards in the same function (R4); a replacement warning message that walked
  inline-list adopters into the corruption the deleted mechanism used to cause (R5); a
  style detection that missed a real flow spelling (R6); and a list spelling promoted to
  "supported" that the kit's own reader cannot parse (R7). Session-wide: **13 rounds
  across three PRs, all 13 with findings, 7 of them self-inflicted by the prior fix.**
  `safety-critical-changes.md` rule 3 **already** says "Re-review after every fix round
  until a full pass finds nothing new" and that "fix rounds on gate logic routinely
  introduce their own regressions" — so the floor is written and was followed. What this
  session adds is different, and is what should graduate: (a) a *base rate* — 13/13 rounds
  with findings means "until a pass finds nothing new" may never terminate, so the rule
  needs a stopping criterion it currently lacks; and (b) the criterion that actually got
  used, which is **blast radius, not round count** — a merge gate and a
  reported-never-gating display field cannot share a stopping point.

- **Reading the code is not the same as running it, and the gap is not small (severity: M).**
  Three defects this session were invisible to careful reading and obvious on execution:
  CodeRabbit's pending check reports `startedAt: 0001-01-01T00:00:00Z`, so an
  "unmeasurable age fails open" branch was not an edge case but the *only* path that bot
  ever took (the #19 guard was dead code for its own target); making `append_to_section`
  return non-zero looked plainly correct and aborted `init.sh` under `set -eu` on any
  config missing an optional section; and `kitconfig` silently resolves a next-line flow
  list to `{}`. **Candidate graduation:** the review-panel prompt (#26) should require
  the lens to *execute* the changed paths and to mutation-test new branches — mutation
  is what proved **five** properties across the session were unpinned despite tests that
  named them (on #29: anchored author matching, newest-review-per-bot, the `bots=`
  threading; on #25: the `init.sh` list-style branch and `grep -qi`'s
  case-insensitivity). Three of those five are #29's.

- **Narrative surfaces drift from the diff, and nobody re-reads them (severity: M).**
  #25's PR body needed three corrections (a stale test count, and two descriptions of a
  design the diff had replaced); #29's asserted an anchored-match property no test pinned;
  and **this very wrap-up** was fact-checked and came back with 13 issues, three of them
  HIGH — including a number that a review round on #25 had *explicitly corrected*
  ("four ways to corrupt" → three) and which I reintroduced while writing up the lesson
  that PR bodies keep drifting. Every instance was caught by a review pass, never by the
  author. **Proposed fix:** `wrap-up` should fact-check the handoff against `git log` /
  `gh` before committing — the handoff is read at the start of every future session, so a
  wrong number there propagates further than a wrong PR body. Filing this at M rather
  than L because the failure recurred *inside the document describing it*.

- **The cockpit bundled wrap-up narrative edits into a lane branch, and only the hook caught it (severity: L, but the guard worked).**
  While waiting on CI for PR #29 I updated `kit-handoff.md` and `kit-friction-log.md`, then
  `git add -A` swept them into the lane commit. `pre-push` refused, named both files, and
  said where the lane's handoff belongs instead. Recording it because it is the **positive**
  case this log rarely captures: a fail-closed guard firing on its author, with a message
  that made the fix obvious. Worth keeping in mind when weighing whether a guard is worth
  its friction — this one cost ten seconds and prevented a narrative-file conflict with the
  wrap-up PR. No change proposed.

### 2026-07-26 — inbox

> **At the 150-line budget.** A `triage-friction-log` sweep is required before the
> next entry — the two H entries below are issue-shaped and #33 is already filed.

- **Mutation testing this repo reports false kills — filed as [#33](https://github.com/topij/agentic-dev-kit/issues/33) (severity: H).**
  `kit_doctor`'s self-check rehashes every kit-owned file, so any byte change to an
  engine fails it and every mutant looks killed. The **mechanism** is trivially
  reproducible (change one comment in an engine; only the manifest test fails). The
  **figure** — a lens reporting 17/17 killed on #31, and 7 survivors once that test
  was excluded — is attested rather than independently measured; the 17 are enumerated
  nowhere. Those 7 were closed inside #31. Filed at H because it is **retroactive**:
  mutation evidence cited across #25, #28, #29 and #31 may be worthless wherever the
  reviewer did not exclude that test, and "N mutants died" was used as a reason to stop
  reviewing. A false-negative testing tool is worse than none, because it is used to
  justify confidence. #33's mechanical fix (a `driftcheck` marker) is not built; only
  the panel doc's prose warning ships.

- **Concurrent review lenses in one working tree destroy each other's work (severity: H).**
  On #31 the adversarial lens mutated `pr_watch.py` to test it; the correctness lens,
  running at the same time, saw those mutations as an external process corrupting the
  repo and ran `git checkout --` to "restore" it. They fought for ~10 minutes. One
  lens's results were unreliable; when I stopped the other it left a live mutant behind
  (`if False and _PANEL_LENS_NAMES:`) that **silently disabled a guard in my working
  tree**, and I caught it only because a test failed citing an error string that should
  no longer have existed. Already fixed as contract item 7 (isolated worktrees) and
  `.gitignore`/`init.sh` entries, so this is recorded for the pattern rather than as an
  open item: **any doctrine that says "run N reviewers concurrently" owes them
  isolation**, and mine did not until it bit.

- **Deleting a check reintroduced the bug it was masking (severity: M).**
  The roster check removed from #31 was the only thing catching `,` as punctuation in
  `--lenses` — so `"adversarial, focused on the merge gate"` (an honest way to record
  ONE lens) rendered as two, suppressing the one-lens warning that was the field's
  entire remaining value. The commit that deleted it quoted that exact input as an
  example of what it still blocked. **Fixed inside #31** — recorded for the pattern. **Lesson worth generalising:** when removing a
  mechanism as unfit, enumerate what it was rejecting and confirm each case is either
  still rejected elsewhere or deliberately allowed — the deletion commit did neither.

- **Four rounds of tightening a matcher is the signal to delete it, and the rule
  already says so (severity: M, pattern).**
  `safety-critical-changes.md` rule 1: *"Treat 'we tightened the matcher' as a stopgap,
  not a fix."* On #31 I tightened it four times before accepting that. The adversarial
  panel told me by round 3 that the artifact was unverifiable from the engine — same
  actor, same invocation, nothing bound to what ran — and I built two more epicycles
  before acting on it. **Proposed fix:** rule 1 could name a threshold ("a second
  tightening of the same matcher is a design signal, not a bug fix") so the decision
  point is written down rather than requiring the author to notice it.
