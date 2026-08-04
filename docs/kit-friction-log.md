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

## 2026-08-04

**`fallback-review-panel.md` never mentions `panel_prompt.py`, so a panel is run by
hand-authoring every lens prompt — the exact failure that engine exists to prevent.**
Severity **H**.

Ran seven panel rounds on PR `#289` and hand-wrote both lens prompts each round, from the
doctrine, because the doctrine's "Running it" section describes what a lens must be told and
never says anything renders it. Only afterwards did `scripts/panel_prompt.py` turn up. Its
own docstring opens with the reason it exists:

> Assemble a fallback-review-panel launch prompt instead of hand-authoring it. … **Nothing
> rendered that.** Every prompt was hand-written from the doctrine, once per lens per round,
> and `#214` records what it cost.

Established rather than assumed: `git grep panel_prompt` outside the script, its own tests,
`kit-manifest.json` and `kit_doctor.py`'s `KIT_OWNED` returns nothing. So the engine is
shipped, kit-owned and tested, and unreachable from the only document that tells you to run a
panel — which means every adopter hand-authors prompts too.

What it cost here is the failure `#214` names: an omitted contract item is **invisible**,
because a lens cannot report the absence of an instruction it never received. The three
properties the script guarantees — the contract quoted rather than restated, the base resolved
from the remote every run, and identical inputs producing an identical prompt so a round's
framing differences are deliberate — were all things I re-established by hand each round, and
the third one I simply did not have: my round-to-round prompt variance was not deliberate.

Proposed fix: `fallback-review-panel.md` "Running it" step 2 names the engine and shows the
invocation, the way `pr-watch.md` names `pr_watch.py`. Worth checking at the same time whether
`--carry-forward` is the channel the round-N prompts should have used, since this session
passed prior-round framing as hand-written prose in the lens brief instead.

## 2026-08-03 — Backlog migrated to GitHub Issues (#250–#256)

Ninth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Fifteen entries in, fifteen accounted for:** seven new issues
([#250](https://github.com/topij/agentic-dev-kit/issues/250)–[#256](https://github.com/topij/agentic-dev-kit/issues/256)),
five occurrence comments (`#32`, `#47`, `#71`, `#205`, `#246`), and two entries already tagged
`#198` that route nowhere. All twelve writes were re-read from the tracker after landing per
`#138` — compared **by body**, with every commented issue confirmed still open afterwards.

**Approval.** The operator replied `lgtm` in the Slack DM thread (channel `D083840DP7B`, parent
ts `1785731335.010039`) — a bulk approve of all twelve, with nothing declined.

**Frozen inbox:** 16,413 bytes, `sha256 4d731234…`, reproducing from
`git show a447957:docs/kit-friction-log.md | tail -n +14 | shasum -a 256` — run in this session,
digest matched. The current inbox was byte-identical to it at finalize, so every block swept and
nothing was held back.

Reading the tracker before drafting changed three routings, two of them substantively; the
routing table and what this sweep does **not** establish are on the PR. Swept entries are
verbatim in the archive under `Graduated 2026-08-03`.
