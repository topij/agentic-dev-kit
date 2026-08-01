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
