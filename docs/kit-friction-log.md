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

## 2026-08-12

**A multi-round panel cannot tell a lens what a previous round already disposed of.**
Severity **M**. A lens has fresh context by design, so it re-raises a finding the cockpit
already answered — on `#437` the same enforcement gap was raised in an early round, filed
as an issue, and raised again identically two rounds later. Re-raising is correct
behaviour for the lens and costs the cockpit a repeated reply each round, and a cockpit
that tired of replying would start ignoring a live finding that happened to look familiar.
`panel_prompt.py --carry-forward` is the obvious home — it already carries the
round-to-round aim — but it carries what prior rounds *covered*, not what was *decided*.
Proposed fix: give the launch prompt a dispositions section (finding, disposal, where the
artifact lives) and require a lens re-raising one to say why the disposal is wrong, rather
than restating the finding. Related: `#405` (nothing checks a round was posted), `#420`.

**The lens contract's scratch rule collides with the permission layer, in every run.**
Severity **L**. `fallback-review-panel.md` tells each lens to namespace its scratch by lens
and revision; lenses reach for remove-then-recreate to honour that, and `rm -rf` is refused
here. Every lens on `#437` reported the refusal and worked around it the same way — a fresh,
never-reused directory name — which is what the namespacing rule wanted anyway. The rule is
right and the route it implies is not. Proposed fix: say so in the contract — a fresh path
per lens per revision, never a removal — which is one sentence and removes a refusal from
every lens run.

## 2026-08-11 — Backlog migrated to GitHub Issues (#419–#423)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Eight entries in,
eight accounted for:** five new issues
([#419](https://github.com/topij/agentic-dev-kit/issues/419)–[#423](https://github.com/topij/agentic-dev-kit/issues/423)),
two occurrence comments (`#305`, `#313`), and one entry already filed as `#417` before
this sweep began — archived with the rest, routed nowhere new. All seven writes were
re-read from the tracker after landing per `#138`, compared **by body**, and both
commented issues were confirmed still open afterwards.

**Approval.** The operator approved all seven in an interactive session; nothing was
declined. The numbered proposal DM is in the Slack thread (channel `D083840DP7B`, parent
ts `1786448223.387429`), and this block is the committed approval record `#128` asks the
interactive path to carry — the proposals, the decision, and the snapshot digest, none of
which survive in `state/` or `reports/`, both gitignored.

**Frozen inbox:** 12,309 bytes, sha256
`2393e19e0a2d5cc960a5beb2ab257a2bef62b9b769a165c83b07da486ca8d272`, reproducing from
`git show a539587:docs/kit-friction-log.md | tail -n +14 | shasum -a 256`. The revision
qualifier is load-bearing rather than decorative: this sweep rewrites the file, so the
same pipeline against the working tree hashes post-sweep content and returns something
else. Naming that other digest here is not possible — the sentence naming it would sit
inside the region being hashed, so any value written invalidates itself. Taken at draft
time and re-checked at finalize; the digests matched, so the inbox was byte-identical to
the snapshot and every block swept with nothing held back.

**Reading the tracker before drafting moved two entries off the new-issue path.** The
panel-loop entry proposed a stopping-rule change that `#305` already carries as its
direction 3, so it became an occurrence comment there — what is new is that `#412` reached
the same state on a loop that terminated *correctly*, which separates the state from the
termination and argues the doctrine should record *which* occurred. The `gh --limit` entry
is the same defect `#313` already reproduces, so it became a comment carrying the third
instance and the per-tool rule that issue's proposed validator needs. Filing either as new
would have fragmented a family that already has three members (`#209`, `#305`, `#211`).

**The two doctrine extensions are siblings.**
[#422](https://github.com/topij/agentic-dev-kit/issues/422) (predictive claims) and
[#423](https://github.com/topij/agentic-dev-kit/issues/423) (out-of-repo evidence) both extend
`#54`/`#140` and are cross-linked; they were kept separate because the discriminators
differ — one has no command to name, the other has one the reader cannot run.

Swept entries are verbatim in the archive under `Graduated 2026-08-11`.
