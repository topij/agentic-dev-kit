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

## 2026-08-01 — Backlog migrated to GitHub Issues (#192–#196)

Eighth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Eight entries in, eight accounted for:** five new issues
([#192](https://github.com/topij/agentic-dev-kit/issues/192)–[#196](https://github.com/topij/agentic-dev-kit/issues/196)),
two occurrence comments (`#180`, `#71`), and one proposal the operator declined. All seven writes
were re-read from the tracker after landing per `#138` — and the issues were compared **by body**,
not by title, which closes the asymmetry the previous marker disclosed about itself.

**Approval.** The operator replied `5 skip, approve others` in the Slack DM thread (channel
`D083840DP7B`, parent ts `1785559251.831209`). Item 5 — a fix round's `git add -A` staging a
`.DS_Store` — was declined as not worth its friction. Its source entry is nonetheless swept to the
archive with the rest, so that friction now has **no tracker representation**; this sentence is the
only pointer to it.

**Frozen inbox:** 16,795 bytes, `sha256 d793a1bb…`, reproducing from
`git show 84931f1:docs/kit-friction-log.md | tail -n +14 | shasum -a 256` — run in this session,
digest matched.

Reading the tracker before drafting again changed two proposals, and both times the entry was the
less accurate source. Routing table, verification commands, and what this sweep does **not**
establish: on the PR. Swept entries are verbatim in the archive under `Graduated 2026-08-01`.

## 2026-08-01 (post-sweep)

- **The notify identity and the operator identity are the same account, so the approval detector
  cannot tell the batch apart from its own approval.** This sweep's DM went through the Slack MCP
  under the operator's own token into their self-DM, so the proposal message, the reminder, and the
  operator's `5 skip, approve others` reply all carry author `U082VD4SR2N`. Session B's documented
  rule — *"if the only replies are from the bot itself … exit 0 with state intact"* — is
  unevaluable under that configuration, and matching against `approver_user_ids` admits the
  pipeline's own messages as operator replies. A human reads the thread correctly; the automated
  detector the skill specifies cannot. **M** — proposed: a marker the pipeline stamps on its own
  messages, or a bot identity in config distinct from `notify.user_key`. Reply-ts ordering against
  `posted_at` is **not** sufficient alone and was rejected on review: it establishes only that a
  message arrived later, and the pipeline's own reminder is itself later than `posted_at`, so
  ordering re-admits exactly what it is meant to exclude. Filed as
  [#198](https://github.com/topij/agentic-dev-kit/issues/198). The reply itself was correct and
  in-thread; this is not a defect in it.
- **The approval grammar has no "approve the rest" form, and the safe default makes the natural
  phrasing file nothing.** `5 skip, approve others` is unambiguous to a reader but matches no
  documented rule: bulk approve is `lgtm` / `approve all`, per-item approve is `<numbers> approve`,
  and anything unmentioned defaults to skip. A literal parser would have skipped item 5, found no
  approve verb bound to the rest, and filed **zero** tickets while reporting success. **M** — the
  failure is silent and in the safe direction, which is exactly why it would survive unnoticed.
  Proposed: add an explicit `others`/`rest approve` form, or have the parser refuse a reply it
  cannot fully account for rather than defaulting it away. Filed as
  [#198](https://github.com/topij/agentic-dev-kit/issues/198) alongside the bullet above — one
  issue, two separately testable acceptance criteria.

## 2026-08-01 (post-merge, mutation and receipt hygiene)

- **Mutation-testing a file that carries uncommitted work makes `git checkout --` destructive.**
  I mutated `scripts/hooks/pr_followup_hook.py` while it held three uncommitted review fixes, then
  reverted the mutant with `git checkout -- <file>` — which discarded the fixes too. Caught only
  because the tests written minutes earlier went red; had the mutation targeted code those tests
  did not cover, the fixes would have vanished silently and the PR would have merged without them.
  **M** — `fallback-review-panel.md` contract item 7 already says to mutate in an isolated copy of
  the repo, but it frames that as protecting *other lenses* from your writes. This is the same
  hazard pointed inward: the cockpit's own tree. Proposed: extend item 7 to say mutate only
  committed code, or copy the file aside and restore from the copy rather than from git — `git
  checkout --` cannot distinguish your mutant from your work.
- **A review receipt can name a lens that has not run, and the cockpit is as able to do it as
  anyone.** I recorded `--record-review "fallback:delta" --lenses correctness` before spawning the
  correctness lens, then ran the lens to make the claim true. The engine accepts `--lenses` as a
  typed string and verifies nothing. **M** — occurrence data for
  [#32](https://github.com/topij/agentic-dev-kit/issues/32), whose whole subject is that the lens
  roster is self-reported; what this occurrence adds is that the failure is easy to commit
  *accidentally*, mid-way through doing the right thing, rather than as a shortcut. No new proposal
  — the lens-written entries `#32` already asks for would settle it — but the sequencing hazard is
  worth naming: record after the lens returns, never before.
- **`.agents/skills/**` is not manifest-tracked, so a Codex adapter can drift from the config it
  documents.** Adding a `lens_compute.codex` sentence to `.agents/skills/pr-watch/SKILL.md` and
  regenerating the manifest produced no diff at all. The review bot independently flagged the same
  gap. **L** — these adapters are the Codex runtime's only consumer of several config keys, so a
  silent drift there makes a key inert on that runtime with nothing reporting it. Proposed: extend
  `KIT_OWNED` to the adapter files, or state at `#47` why they are deliberately excluded.
- **A config key can express a control the runtime cannot actually apply.**
  `review.fallback_panel.lens_compute` carries `effort`, but Claude Code's delegation tool has no
  per-agent effort parameter, so on that runtime it reaches a lens only as prompt text. This one is
  documented at every surface — but only because a dogfooding run surfaced it after the key had
  already been designed, written, tested and opened as a PR. **M** — nothing prevents the next such
  key, and the failure is quiet: config that reads as a control and behaves as a suggestion.
  Proposed: when a config key selects compute or capability, state per runtime whether it is
  mechanical or advisory, and consider a `kit_doctor` check that a declared runtime key has a named
  consumer.
- **A guard that refuses looks exactly like a command that failed, and the recovery instinct is to
  re-run without the guard.** `gh pr create` was chained to the closing-keyword scan. The scan
  **refused** — correctly: the PR body quoted a banned construction in the course of describing it.
  All the chain emitted was an absence, no URL, so I read it as a transient failure and re-ran
  `gh pr create` **without the chain**, publishing the body the guard had just declined. **H** —
  this is [#180](https://github.com/topij/agentic-dev-kit/issues/180) inverted and is the more
  dangerous half: `#180` is about a guard that is not chained; this is a guard that *is* chained,
  fires correctly, and loses to the operator's next keystroke.
  **What each half rests on, since a review round challenged exactly this.** The refusal is
  reproducible — the scan still exits 1 on that body content, so *"the chain would not have
  published this"* is checkable rather than narrated. The re-run without the chain leaves no
  server-side trace and cannot be corroborated from the forge; treat it as my account. What the
  record shows independently is the **consequence**: the banned construction was live in the PR body
  for roughly fourteen minutes, and throughout that window the body asserted the scan was *"clean
  over both surfaces"* while naming only the doc lines and the commit message. The body was itself
  a surface, and its claim of cleanliness was false about the document making it.
  **`#195` was not altered** — it reached its final state at `05:29:21Z`, before this PR existed,
  and nothing has moved it since.
  An earlier draft cited *"no timeline event from the PR"* as the evidence for that, and the commit
  publishing the claim falsified it on the spot by naming `#195` in its own message, which GitHub
  auto-links. **State is the checkable property here; timeline is not.** **Proposed — and
  review of this entry sharpened it, which is worth recording because the first proposal was too
  weak.** A louder failure message is not a fix: `REFUSED: <reason>` on the failure path is a useful
  diagnostic, but it does not stop the next keystroke from dropping the chain, and prescribing
  operator discipline against that is Principle #8's *"a rule that lives only in a doc is a wish"*
  aimed at my own remedy. The enforceable version is that the guarded path is the **only**
  publishing path — scan inside it, direct unguarded publication rejected — which is
  [#71](https://github.com/topij/agentic-dev-kit/issues/71)'s ask rather than a separate one. So
  this is occurrence data for `#71` and evidence for its priority: the guard being ad-hoc rather
  than shipped is precisely what made dropping it a single edit.
- **`gh pr view <branch>` can resolve to a *merged* PR when a branch name repeats.** Compounding the
  above, and the reason I mis-diagnosed it: the wrap-up branch pattern
  `chore/update-handoff-{date}` repeats whenever two wrap-ups land on one date, and this session's
  did. `gh pr view <branch> --json number,isDraft` printed `PR #191 isDraft=false` — a PR **merged
  the previous session** from a branch of the same name — so the check answered confidently about a
  different, already-merged PR and sent me looking for a transient `gh` failure instead of at my own
  refused guard. Caught only by listing open PRs and finding none. **M** —
  [#179](https://github.com/topij/agentic-dev-kit/issues/179)'s shape with a concrete mechanism, and
  it weakens [#170](https://github.com/topij/agentic-dev-kit/issues/170) directly: verifying the
  draft bit landed is only sound when bound to the PR just created. Proposed: verify by the PR
  **number** `gh pr create` prints, never by branch name; and consider a wrap-up branch pattern that
  cannot repeat within a day.
