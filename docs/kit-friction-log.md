# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **This repo's tracker is GitHub Issues on itself**, so most friction is filed directly as
> issues rather than parked here — which is the routing Principle #2 prescribes, not a
> neglected inbox. Anything that appears below a graduation marker is un-graduated: not yet
> issue-shaped, or waiting for the next `triage-friction-log` sweep.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-07-28 — Backlog migrated to GitHub Issues (#112–#125)

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

## 2026-07-28 (second session of the day)

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
