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

Last updated: 2026-09-09 — cs-toolkit replay verified at its bound refs; merges operator-held.
Phase 5 remains blocked on delivery item 5, whose original fixture/source are missing.

## Latest session — 2026-09-09 (cs-toolkit replay, in Codex)

The operator approved REPLAY-01 in this session. The [replay record](../saved_plans/cs-toolkit-replay_2026-09-09.md)
retains the upgrade, separate no-change reconciliation, test limits, independent reviews,
and the byte-identical authoritative snapshots. Item 6's verification is complete at the
named refs; this is not completion of Phase 5 or authority to merge.

- [cs-toolkit #2255](https://github.com/in-parallel-oy/cs-toolkit/pull/2255) contains the
  upgrade from kit `bde4c234eaa9005e90b987007101aba98281ce88` to protected kit source
  `e698ec47d6284ccd31af5ba9d8bc5657fe992310`. Its base is `main` and its head is
  `21fe33bb040e7fdcc8f7d3d7c4402e768b1ff351`. No reconciliation PR was needed; the
  stage's exact invocation, unchanged output/tree and preceding-stage linkage are retained.
- `uv run scripts/devkit/pr_watch.py 2255 --json` in
  `/Users/topi/Coding/in-parallel/cs-toolkit` at that exact head on 2026-09-09 reported
  `converged: true`, `mergeable: true`, `done: true`. The operator holds the merge.
- The original checkout's `make test` failed in support-docs on ignored local artifact
  inventory; unchanged original test source reproduced the assertions there. Independent
  fresh clones passed `make test` at the same head. Commands, directories, dates and
  actual results are in the replay record; this failure is separate from kit #393.
- CodeRabbit found the imported non-object-manifest helper defect that the panel missed.
  The operator approved its exact filing as [#723](https://github.com/topij/agentic-dev-kit/issues/723)
  and deferral, retaining source byte identity. The PR carries that accepted limitation.
- The #722 batch is folded into this ordinary wrap-up: #578/#721 routing annotations,
  removal of the `/tmp` mechanism explanation, the missing-tree blocker, #585's settled
  earlier placement, and this next action. Existing credited exercises were not repeated.
- The kit branch is `chore/kit-replay-handoff-20260909`. This wrap-up publishes the
  snapshots and stamped replay result before its merge; its own commit is not the kit
  source used for the replay. Later ref movement is a separate event.

▶ Next: `$session-start` — read this handoff and the maintained sprint status, then
re-read cs-toolkit #2255 and the kit PR for `chore/kit-replay-handoff-20260909` before
seeking exact operator merge decisions. After delivery, obtain the Phase 5 item 5
rebuild-versus-change-approach decision. Check both original trees and stop rather than
rebuild. #585 already moved earlier; #723 is the accepted upstream follow-up.

______________________________________________________________________

## Session — 2026-09-09 (the prose-claims rule, in Claude Code)

**Theme —** Write the rule the 2026-08-22 entry parked, and keep the two mechanisms apart.

- [PR #717](https://github.com/topij/agentic-dev-kit/pull/717) merged as `b866298`,
  on the operator's word after `uv run scripts/pr_watch.py 717` reported
  `DONE — green, reviewed, merge-ready` at `d6b06466f62202fb438608bd42bcdca929349a17`.
  The merge was read back rather than inferred from the command: `gh pr view 717`
  returned state `MERGED`, and the new section is present in `AGENTS.md` on
  `origin/main`. `AGENTS.md` gains *Prose that goes false*, placed next to *Numbers in prose* because it
  is that section's other half: one governs the number you write, the other the sentence
  you ship without rewriting.
- **The two PR #711 instances stayed distinct, and the section says why neither read
  catches the other's case.** One is bounded by the commit — the paragraph the diff lands
  in, then a grep on the subject changed. The other is bounded by the kind of sentence:
  could this go false while the repository sits untouched.
- **The second mechanism needed its own rule, and the gap is exact.** *Numbers in prose*
  prohibits a number, a quantity word, or a verdict resting on one; an instruction to
  watch a merged pull request is none of those, and the dated hedge in front of it is a
  permission that section grants. So: dating the observation does not date the
  instruction built on it. Where the sentence is numeric, the new section defers.
- **The broad reading was not written, and the section records why** — `#709`'s findings
  in that same session were real defects in a mechanism. `#120` is named as enforcement,
  `#586` ruled out against its own body text.
- Placement was the open judgement call: `AGENTS.md` binds authors and both runtimes,
  which `fallback-review-panel.md` and `.claude/rules/` do not. No `wrap-up.md`
  counterpart, so it binds this repository and not an adopter's. No adopter-counterpart decision was made in that session.
- **Applying the rule to its own commit found a hole in the draft.** The first read was
  bounded by the diff's neighbourhood and could not reach a sentence the same commit
  falsified elsewhere in the file. The 2026-08-29 marker is left as written and the
  correction appended to the entry it points at, which is `#696`'s proposed remedy.
- Two instance claims taken from PR #711's round dispositions did not survive checking
  against the diffs, and both were corrected rather than carried: `1bcb04e` puts the
  stale count on the line it rewrote, and `8942cea` replaced the dated hedge with the
  merge sha. Check them at those commits rather than here.
- The 2026-08-22 friction entry now records its park condition as discharged to the rule
  rather than to the tracker, so triage reconciles instead of re-filing. `#712` and `#713`
  were left untouched and the inbox was not swept.
- **This session's issue-shaped friction went to the tracker on the operator's go-ahead:**
  [`#719`](https://github.com/topij/agentic-dev-kit/issues/719) (a lens correcting its own
  report after that round's receipt is written) and
  [`#720`](https://github.com/topij/agentic-dev-kit/issues/720) (`--lenses` takes one
  comma-separated value while the doctrine's example reads as space-separated), plus an
  occurrence comment on [`#574`](https://github.com/topij/agentic-dev-kit/issues/574) for a
  lens writing into its handed tree — searched first, and it widens `#574` past base
  currency rather than opening a second issue. Each was read back from the tracker after
  landing. The self-imposed-timeout entry was later routed to #578 on 2026-09-09;
  the #722 reconciliation is appended to that entry.

**Verification.** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
`d6b06466f62202fb438608bd42bcdca929349a17` on 2026-09-09 printed `1 failed, 2484 passed,
1 skipped in 393.65s (0:06:33)`, failing the pre-existing
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero` that
`#393` tracks; `make` exited non-zero for it. Both lenses ran the same command
independently in their own worktrees at that sha and reached the same single failure.

**Review.** Panel rounds at `06ff7d7` and `d6b0646`, each receipt recorded before that
round's fixes; both dispositions are on the pull request. The second was a full panel
rather than a delta pass because the first round's fix touched executed prose.
Correctness reported nothing in either round; adversarial's round-1 citation-style finding
was fixed and its other findings replied to as disclosed limitations. CodeRabbit was asked
at the converged head, because automatic review is off here and `#518` says a panel receipt
does not discharge that request; it answered *"No actionable comments were generated"* in a
comment rather than a review object, which the engine reports and deliberately does not
count as evidence. The panel receipt was left standing rather than replaced by
`coderabbit:comment-verdict`.

The current replay decision and next-session starter are in the latest session block.

______________________________________________________________________

## Session — 2026-09-09 (hooks continuation, in Codex)

**Theme —** Finish the authorized live observations and retain their limits.

- The [continuation record](../saved_plans/codex-hooks-continuation_2026-09-09.md)
  binds CLI `/hooks`, the operator's desktop Settings → Hooks capture, engine-entry
  evidence and the doctor invocations to their commands, revisions and dates.
  It distinguishes execution after trust from discovery, and scopes the disabled
  observation to the CLI. The desktop result does not assert every client's default.
- The operator approved temporarily removing the ordinary user hooks setting for
  the desktop observation, then restoring it. The record retains the config
  amendment, fresh local task, script restoration and original-tree audits.
  The disposable desktop project remains in the app.
- Earlier discovery, tracker dispositions and field exercises were not credited
  again. REPLAY-01 subsequently supplied the cs-toolkit replay decision; the
  latest session block owns that result and the remaining operator-held work.
- The session's desktop profile-identification friction was parked in the inbox
  after the operator left; no tracker payload was approved or posted. The
  operator-held triage and Claude prose-claims work were not performed.

______________________________________________________________________

## Session — 2026-09-07 (#698 doctor correction and #706 push gate, in Claude Code)

**Theme —** Take the two delegate-shaped items and `#534`'s panel follow-ups, and let the
fallback panel do its work on a gate.

- [PR #708](https://github.com/topij/agentic-dev-kit/pull/708) merged as `ec75075`.
  `kit_doctor` grades `[features].hooks` whenever a Codex registration exists rather than
  only when `.codex/config.toml` does — this repo was itself the affected population. The
  new `unset` state reports at `·` and does not reach the exit code, which was the
  operator's calibration decision: the approved observation recorded a client discovering
  registrations with the switch unset, so failing the run would assert what that probe did
  not establish. An explicit `false` still exits 1.
- [PR #709](https://github.com/topij/agentic-dev-kit/pull/709) merged as `6f2cc24`.
  `scripts/hooks/pre-push` refuses a push whose commit carries a stale
  `kit-manifest.json`. Checked against the real remote from `main` at `6f2cc24` by
  committing an edit to `scripts/kit_doctor.py` without regenerating and attempting the
  push, which was refused naming that file; the probe branch was then deleted. Re-run it
  that way rather than trusting this sentence. An adopter's `--record-install` baseline is
  exempt.
- **Four panel rounds on `#709` produced four HIGH findings, every one the same shape:
  the guard reporting a clean check while not having checked.** Valid-but-non-object JSON
  crashed it into silence; an entry with no `sha256` was dropped silently; the
  adopter-baseline skip warned on every adopter push forever, contradicting the CHANGELOG
  written in the same commit; and a newline in a manifest key desynchronised the
  positional `git cat-file --batch` reader, **laundering a genuinely tampered file past
  the guard with exit 0 and an empty stderr**. The last was found by building the attack,
  not by reading. Round 4 confirmed the repair closes the class rather than the instance.
- [PR #710](https://github.com/topij/agentic-dev-kit/pull/710) carries `#534`'s two
  panel follow-ups from PR #705's disposition — `is_install_baseline`'s untested except
  arm, now pinned, and the `_shipped()` body duplicated across two test modules, now one
  accessor in `conftest.py`. It merged as `dc6a74e`, so `#534` needs no fresh start on
  either — only the typed decline reasons it always kept out of scope.
- The recurring shape is now unmissable and is in `docs/kit-friction-log.md`: across every
  round this session, each finding was in a claim the author made rather than in a
  mechanism. The 2026-08-22 entry parked exactly that pattern for accumulation on two
  docs-only PRs; it has now recurred on code, repeatedly. The operator subsequently approved the narrow rule, delivered by PR #717.
  Its latest-session account above distinguishes the mechanisms.
- **`#561` is worse than its title.** A genuinely unparseable `pre-push` passed `make
  test`: `check-syntax` hands four filenames to one `bash -n` and `pre-push` is last, so
  it is never parsed. `bash -n good.sh bad.sh` exits 0 with a broken second file. The hole
  for that one file is now shut by `#709`; the general fix is still `#561`'s.
- **A `make test` failure reproduces on clean `main` and CI cannot see it.** Recorded with
  its stamps in the friction log; local `uv run` resolves 3.14.7 against CI's pinned 3.12,
  and `#393` names the mechanism family but a different test. Non-deterministic, so the
  interpreter split is a candidate contributor rather than an established cause.
- `#698`, `#706`, `#534`, `#561` and `#393` all stay open.

**Subsequent reconciliation — 2026-09-09.** The approved tracker writes landed as
#712, #713 and the #561/#393 occurrences, and PR #717 delivered the prose-claims rule.
The [hooks continuation](../saved_plans/codex-hooks-continuation_2026-09-09.md)
records the later live observations and their client-specific limits. These completed
steps are not fresh instructions.

For any future approved fixture execution, check continuity against
`saved_plans/adopt-reg01-application-evidence_2026-09-07/fixture-inventory-after-reg01.json`,
then work in a disposable copy. **Check both original trees and stop rather than rebuild
if either is missing:**

    fixture: /private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture
    source:  /private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source

Use `stat -f "%N atime=%Sa mtime=%Sm"` on the paths yourself rather than relying on
an earlier timestamp sentence. `test -e` from kit revision
`e698ec47d6284ccd31af5ba9d8bc5657fe992310` on 2026-09-09 found both paths absent.
Phase 5 delivery item 5 is blocked pending the operator's decision whether to rebuild
from retained baselines or change approach. Item 6 does not depend on those trees.

______________________________________________________________________

## Session — 2026-09-07 (#534 residual repairs, in Claude Code)

**Theme —** Repair what `#534` still carried, and field-verify the item that merged
without ever being checked in an adopter.

- [PR #705](https://github.com/topij/agentic-dev-kit/pull/705) merged as `7cb0868`.
  Item 1 (`_repo_layout` engine-dir resolution) was **not** re-done: it merged in
  PR #545, and `kit-handoff-history.md`'s 2026-08-21 block records the residual — those
  issues stayed open because nothing verified their acceptance criteria in the field.
  That verification is what this session did.
- **The proposed kit-repo-only marker cannot carry cause 1, and the reason generalises.**
  It skips on a *missing path*, and the question these tests need answered is whether the
  file at that path is the kit's copy. `conftest.py` gains the predicate it cannot
  express, derived from `kit_commit` being written only by `--record-install`.
  `test_shipped_manifest_covers_every_kit_owned_file` is restated rather than skipped, so
  an adopter gains coverage where they had a permanent red.
- **`.codex/hooks.json` and `.claude/settings.json` are the sharp case** — the kit prints
  both and writes neither (`#303`), so in an adopter those paths hold hand-written
  registrations and a path check accepts them. Reference copies now ship, engine-relative
  and `KIT_OWNED`, with a drift guard pinning reference to live.
- **Field-verified in disposable copies of the adopter fixture**, the original asserted
  equal to `fixture-inventory-after-reg01.json` before and unchanged after each run.
  Item 1 resolves there; a cause-1 test went from failing to passing, and others from
  failing to skipping. The silent false pass was proven fixed **by mutation, not by a passing run** —
  a pass is what that defect looks like — and that mutation is what caught a read site an
  edit had missed.
- **What the panel found is where the risk sat.** Its rounds are enumerated with their
  heads and fixes in the [disposition](https://github.com/topij/agentic-dev-kit/pull/705#issuecomment-5574151329).
  Every finding was in a claim the author made — a predicate said to be safe, an accessor
  said to decline gracefully, a test said to guard a fix, a docstring describing a step
  its function does not perform — and none was in a mechanism. Rounds whose CI was green
  still carried them.
- **`#534` stays open.** The typed decline reasons are deliberately out of scope; the
  disposition also carries the follow-up candidates the panel raised and this PR did not
  take.
- An occurrence on [`#393`](https://github.com/topij/agentic-dev-kit/issues/393#issuecomment-5573705268)
  records that the interpreter `uv run` resolves locally and the version
  `.github/workflows/test.yml` pins are not the same, so a suite failure reproducible on
  `main` is invisible to CI. That issue stays open.

- **Session friction routed at close-out.** [`#706`](https://github.com/topij/agentic-dev-kit/issues/706)
  files the manifest going stale between `--generate-manifest` and the commit, caught only
  by the full suite. The guard is not broken — it caught every instance — so the finding is
  about when it reports, and the proposed fix moves that to `scripts/hooks/pre-push`.

The later replay decision and next action are in the latest session block.

______________________________________________________________________

## Session — 2026-09-07 (live Codex hooks batch)

**Theme —** Complete the parked Codex observations and preserve their scope.

- The [batch record](../saved_plans/codex-hooks-batch_2026-09-07.md) retains the live
  `/hooks` excerpts, configuration stack, continuity audits and tracker receipts.
  It distinguishes project trust from trust of the current hook definitions and
  discovery from execution.
- The fixture's registration appeared in `/hooks`; the disposable unset case also
  exposed its registrations. See the command/date/revision-bound record for the
  observations and their limits. The original fixture was not used for the unset case.
- The operator approved and posted the reserved `#608`/`#255` dispositions and closed
  those issues as completed. The credited PR #680 probe was not repeated.
- The approved [observation on #698](https://github.com/topij/agentic-dev-kit/issues/698#issuecomment-5569204436)
  scopes the remaining installer/doctor correction. It does not establish hook execution
  after trust or a default shared by every Codex client.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md) carries
  those decisions without advancing Phase 5 exit. The later replay decision and
  remaining operator-held work are in the latest session block. The `#534` repairs
  were outside this Codex batch.

The #534 repair and hooks continuation are recorded above. Preserve their credited
exercises; the latest session block owns the next action.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
