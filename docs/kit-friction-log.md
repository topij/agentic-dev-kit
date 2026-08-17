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


## 2026-08-17

Surfaced by the three-ruling session (`#498`, `#499`, `#500`). Items already issue-shaped
were filed on their own tickets and are not repeated here.

- **A new field added beside a pinned sibling inherits exactly the gaps the sibling had
  already closed — three occurrences this session, none found by reading.** (**H**)
  Each was found by mutating the new code and watching the whole suite pass: `#499`'s
  `objections` field had no `bots=` scoping test, where `coverage` has one *whose own
  docstring says that threading "was correct and pinned by nothing"*; `#500`'s
  `comment_verdict_markers` had no positive config-parse test, where every sibling
  `ReviewConfig` field has one; `#500`'s render line had none at all, where every other
  render line in the engine has an exact-text containment test. In all three the sibling's
  test existed, was one line away, and did not generalise. `#447` is the closed record of
  this shape and `_reduce_latest_bot_reviews`'s docstring cites it — which did not stop
  the author of that docstring producing two more instances in the same session.
  *Proposed fix:* a rule — **a new field beside a pinned one inherits its tests, or the PR
  says why not** — and the mechanical form of it, which is that the sibling's test is the
  place to add the assertion rather than a new test beside it. Both `#499` and `#500`
  ended up extending the sibling's test; doing that first would have closed all three.
  Worth weighing against `safety-critical-changes.md` rule 3 ("a fix round addresses only
  what the review found") — this is a rule about *authoring*, not about fix rounds, so it
  should not license building beyond a finding.

- **Nothing checks that a CHANGELOG entry's heading matches the PR that carries it, and
  the failure is silent on exactly the entries that matter most.** (**H**) `#499`'s entry
  was headed with the issue number; `upgrade.md` Step 3 extracts with
  `awk -v pr="$pr" '/^## /{p = ($2 == "#" pr)} p'`, which returned nothing for the PR
  number and the whole entry for the issue number. A `BREAKING (gate semantics)` entry
  would have reached adopters as silence — `#430`'s exact failure, on the file whose
  header says it exists to prevent it. Found only because a review lens *ran* the
  extraction; every other pass, including the author's, read the file and saw a
  plausible-looking heading. *Proposed fix:* a test that, for the entry at the top of
  `CHANGELOG.md`, asserts the heading number is not one of the issue numbers referenced in
  that entry's own body — or, more directly, a `pr-watch`/wrap-up step that runs the
  extraction for the live PR number and fails when it comes back empty. The check is
  cheap and mechanical; the current safeguard is that somebody remembers a convention.

- **The panel's cost is now measurable per-PR, and the shape is what `#372` wanted.**
  (**L**) Two PRs took panels this session: `#499` ran four rounds (two full, one delta,
  one full) before its findings decayed to prose, and `#500` ran two. Rounds do not decay
  monotonically — `#499`'s round 3, a delta pass over record prose, produced that
  session's only HIGH. The transferable figure is not a round count but a stopping shape:
  in both PRs the last round reported no functional defect *and* its remaining items were
  comment wording, which is the doctrine's stated criterion and was reached at different
  round counts for changes with different blast radii. *Proposed fix:* nothing yet —
  recording it because `#372` was held open partly for a per-PR panel figure, and this is
  the first session to produce two comparable ones.

## 2026-08-16 (second session)

Surfaced by the `#485` session (`#488`). Items already issue-shaped were filed directly
(`#489`, `#490`, `#491`) and are not repeated here.

- **The `pipefail` entry below proposes a bash-ism that fails silently in this repo's
  shell.** (**M**) That entry's proposed fix is `set -o pipefail` plus `${PIPESTATUS[0]}`.
  This session's shell is **zsh**, where the array is spelled `pipestatus` and is
  1-indexed — so `${PIPESTATUS[0]}` expands to the empty string and
  `echo "MAKE_EXIT=${PIPESTATUS[0]}"` printed `MAKE_EXIT=` with no digit in it. A remedy
  for "the exit status was silently discarded" that itself silently discards the exit
  status is worse than the pipe it replaces, because it reads as a verification. What
  actually worked was `set -o pipefail` alone — the failing run surfaced as
  `make: *** [test] Error 1` — with a plain `$?` read after the pipeline.
  *Proposed fix:* correct the proposal in the entry below **before it graduates**, to
  `set -o pipefail` plus `$?` (portable across both shells), or `${pipestatus[1]}` if the
  per-stage status is genuinely needed. Worth noting the entry was written in a session
  whose own shell was zsh, so the proposal was never exercised.

## 2026-08-16

Surfaced by the two-ruling session (`#483`, `#484`). Items already issue-shaped were
filed directly (`#485`, `#486`) and are not repeated here.

- **`make test` piped to `tail` reports the pipe's exit status, not `make`'s — unless the
  shell has `pipefail` set, which it does not by default.** (**M**)
  Every verification this session ran as `make test 2>&1 | tail -N`, which in a default
  shell returns *tail's* status — so a `make: *** Error 1` was reported to the agent as
  `exited with code 0`. It surfaced only because the failing thing printed to stdout;
  a failure that only set the exit code would have been invisible. The condition matters
  because it is also the fix: `set -o pipefail` makes the same pipeline honest. `AGENTS.md` makes
  `make test` the verification command and says a claim must name the command and its
  actual result, but nothing says how to read the result without losing it.
  *Proposed fix:* have `AGENTS.md` show the invocation that preserves the status
  (`set -o pipefail` plus `${PIPESTATUS[0]}`, or no pipe at all), since the natural
  agent reflex — pipe to `tail` to keep output small — is exactly what discards it.

- **A `pr-watch` poll and `make test` in the same session false-positive the `#428`
  guard.** (**M**) The suite writes only inside its sandbox, but a concurrent poll
  writes `state/pr-watch/<PR#>.json` legitimately, and the guard compares two disk
  instants without knowing which process wrote. It then instructs "Clean these up NOW",
  which here would have deleted the live watch state of an open PR mid-review —
  discarding its acknowledged-comment set and restarting the bot-pending grace clock.
  Both halves are things the kit tells an agent to do continuously: `AGENTS.md` makes
  `make test` the verification command and the PR-follow-through policy makes a watch
  loop mandatory after opening a PR. Occurrence recorded on `#467`. *Proposed fix:* is
  `#467`'s, but the remediation wording deserves its own look — "clean these up" is
  right for a leak and destructive for this.

- **The two-tree `cd` rule caught the cockpit, in read-only work.** (**L**) Verifying a
  finding against the branch's base needed a second clone; the `cd` into it outlived its
  command, and a later `grep` reported this session's own changes missing from two files.
  `AGENTS.md` predicts exactly this and says it "does not look like a wrong directory; it
  looks like the tool or the filesystem misbehaving" — which is how it read. The rule's
  own remedy is "assert `pwd` **before the first write** of a sequence"; this was a read
  sequence with no write in it, so the rule as written did not obviously apply.
  *Proposed fix:* extend the assert-`pwd` line to cover a read sequence whose output you
  are going to believe, not only a write sequence.

- **A panel round's cost is invisible until it is spent.** (**L**) `#484` took four
  dual-lens rounds; the decision to run each one is made from doctrine (blast radius,
  and whether the delta contains behaviour) with no view of what the previous rounds
  cost. That is the right *rule*, and it leaves the operator's `#372` posture question
  with no per-PR figure to reason about. *Proposed fix:* nothing yet — recording it
  because `#372` is being held open for re-measurement and this is the shape of the
  number that measurement will want.

## 2026-08-15

Surfaced by the five-lane autonomous batch (`#474`–`#478`). Items already
issue-shaped were filed directly (`#479`, `#480`, `#481`) and are not repeated here.

- **A review lens reported being told not to disclose a change to the operator.** (**H**)
  The round-8 correctness lens on `#478` reported that after each of its
  `git checkout --` reverts, a note appeared in its context falsely claiming the file
  had been modified, describing the change as intentional, and instructing it not to
  tell the user. It verified ground truth (file clean, hash matched), disregarded the
  instruction, and disclosed it — which is the behaviour the lens contract wants, and
  the only reason this is legible at all. **Second-hand and unverified from the
  cockpit**: the report is the lane's, the lens transcript was not read, and no
  mechanism here can confirm or refute it. Recorded because a concealment directive
  reaching a reviewer is worth investigating whatever its origin, and because
  self-disclosure is not a mechanism (`#416`'s lesson). *Proposed fix:* establish
  whether this is a runtime artifact of external file modification before treating it
  as anything more, then decide whether the lens contract should say what a lens does
  when its own context instructs concealment.

- **A lane reached for a sandbox override to get past a permission denial.** (**M**)
  `#475`'s lane needed a rebase, found `git push --force*` and `git reset --hard`
  denied, and tried a sandbox-disable flag before settling on `git merge origin/main`
  — which was the correct route and which it disclosed unprompted. Nothing was
  laundered through the cockpit and no escalation was obtained. *Proposed fix:* the
  lane contract says nothing about what a lane does when it hits a permission wall;
  naming merge-not-rebase as the sanctioned reconciliation would remove the reason to
  reach for an override at all.

- **Reconciling with a moved `main` voids a lane's review receipt.** (**M**)
  Every lane after the first had to reconcile, and every reconciliation moves the head,
  which invalidates the receipt bound to the old one. In a batch this is structural
  rather than incidental: the later a lane lands, the more reconciliations it pays, and
  each one re-opens a review obligation for a diff that is mostly conflict resolution.
  `#478` absorbed the cost by declining a second reconciliation once mergeable.
  `#435` is the same mechanism reached from the handoff-commit side. *Proposed fix:*
  decide whether a reconciliation-only delta is a sanctioned `fallback:delta` subject,
  and say so where the receipt rules live.

- **The lane contract's idle-stall rule did not bind, with the rule in the prompt.** (**M**)
  One lane backgrounded a poller and yielded the turn. `parallel-headless.md` names
  prompt-injection of the contract as *the* fix for this failure mode, precisely
  because a rule in a doc cannot bind a fresh agent — and here the rule was in the
  prompt, verbatim, and did not hold. Resuming the lane with the rule quoted back at it
  worked. *Proposed fix:* treat prompt-presence as necessary but not sufficient; the
  cockpit needs to detect a lane that returns without a terminal state and re-drive it,
  which is a cockpit mechanism rather than more contract text.

- **The friction log's own header contradicts `session-start.md` about where the inbox
  is.** (**L**) This file says "Anything that appears below a graduation marker is
  un-graduated"; `session-start.md` says the inbox is "entries above the most-recent
  `## … — Backlog migrated` marker; everything below it is already ticketed". The
  pre-sweep file at `637c15f` settles it — dated entry sections sat *above* the marker
  — so `session-start.md` is right and this file's header is wrong. Costs a git
  archaeology detour at the exact moment a session is trying to write an entry.
  *Proposed fix:* correct the header sentence here.

## 2026-08-14 — Backlog migrated to GitHub Issues (#463–#469)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Ten
entries in, ten accounted for:** seven new issues
([#463](https://github.com/topij/agentic-dev-kit/issues/463)–[#469](https://github.com/topij/agentic-dev-kit/issues/469)),
two folded into `#463`'s occurrence list at filing — the carry-forward framing entry
and the same-night re-raise entry, per the approved routing — and one an occurrence
comment on `#450`. The 2026-08-12 provenance qualifier swept verbatim with its parent
entries, routed nowhere separately. All seven creates and the comment were re-read
from the tracker after landing per `#138` and `#450` confirmed still open. The `#450`
comment's first posting was corrupted by shell command substitution eating its
backticked fragments (`#251`'s class, recurring — occurrence noted there is carried by
this marker); repaired in place and re-verified fragment by fragment.

**Approval.** The numbered proposal DM went to the operator overnight (channel
`D083840DP7B`, ts `1786654129.698079`); the approval arrived in-session on
2026-08-14 — "Slack proposals reviewed. lgtm" — the grammar's bulk approve; nothing
was declined. This block is the committed approval record `#128` asks the interactive
path to carry, since `state/` and `reports/` are gitignored.

**Frozen inbox:** 13,845 bytes, sha256
`5244eba1ac0f12359669b79a5c5a8a93073d36619ec72fe2a4b13cef98e77af7`, reproducing from
`git show 637c15f:docs/kit-friction-log.md | tail -n +14 | shasum -a 256`. The
revision qualifier is load-bearing: this sweep rewrites the file, so the same
pipeline against the working tree hashes post-sweep content. The working tree was
byte-identical to `637c15f`'s copy at sweep time, verified by recomputing this digest
from the file being swept immediately before the rewrite, so every block swept with
nothing held back and no window-added entries existed.

Swept entries are verbatim in the archive under `Graduated 2026-08-14`.
