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

## 2026-08-13

**`parallel-headless.md` requires an `env` map that the runtime the kit ships an adapter
for cannot supply.** Severity **M**. The contract makes the descriptor's `env` field
mandatory for an unattended lane and says a fan-out tool that cannot replace the spawned
process's environment must not drive a state-writing lane. Claude Code's delegation tool
takes no environment parameter, and every lane writes `state/` — the lane contract itself
has each lane run `pr_watch.py --assert-draft/--assert-ready`. So the kit's own documented
headless path is unavailable in Claude Code, and the contract's stated alternative
(a subprocess per lane with the env set inline) needs `--dangerously-skip-permissions` on
this host, since the operator's allowlist covers none of `git commit`, `git push`,
`git add`, `gh pr create`, `gh pr ready`, `uv run`. What was actually lost is narrower
than the blanket prohibition suggests and worth stating: isolation held on the on-disk
marker, because the cockpit exports no `DEVKIT_*` and there was nothing to inherit; only
`DEVKIT_REFUSE_UNSANDBOXED_STATE=1`, the warn→refuse backstop, went missing. Ran on the
marker plus a prompt-level "never cd outside your worktree, assert `pwd` before writes"
rule, at the operator's decision, with the cockpit's `state/` digest snapshotted before
launch and re-checked at every lane return — it never moved. Proposed fix: either name the
marker-only route a sanctioned degraded mode with the cwd rule as its stated condition, or
have `new --headless` emit an activation the launcher can apply without an env map.
Related: `#399` (whose third occurrence was exactly a `cd` out of the tree), `#428`.

**`reconcile_sessions.sh` has no terminal state for a lane held for operator sign-off.**
Severity **M**. It resolves each scope to merged, parked, or open, and exits 3 while any
scope is open. An operator-class lane that is finished — green, reviewed, receipt bound —
reports **open**, identical to one still working, because its PR is neither merged nor
closed. `parallel.md`'s joint wrap-up says not to write the block until every scope is
merged or consciously parked, so a batch containing any operator lane can never reconcile
closed, which is the state every correctly-run autonomous batch ends in. The tally line it
prints (`launched N, merged M, parked K`) has the same gap. Proposed fix: a fourth state —
`held` — for a scope whose persisted merge class is `operator` and whose PR is open,
green, and carrying a current-head receipt; it is distinguishable from `open` with data
the reconciler can already reach.

**A `noise_markers` entry has drifted from the wording the bot actually emits.** Severity
**L**. `config/dev-model.yaml` lists `"actionable comments posted: 0"`; CodeRabbit's
current clean-result phrasing is *"No actionable comments were generated in the recent
review."* — verified absent on `#441`, where that comment was nonetheless filtered because
two other markers matched it. So the marker meant to catch this case has been matching
nothing, and `converged` was correct by redundancy. The failure is silent by construction:
nothing reports a marker that never fires, and the first symptom would be a clean review
blocking the loop as an unacknowledged comment. Proposed fix: assert each marker still
matches something observed in the wild, or retire the count-phrased one as dead config.

**The panel demonstrated the disposition gap recorded below, in the same night.** Severity
**M**, and this is an occurrence rather than a new entry: `#445`'s round 3 re-raised,
identically, a finding round 2 had disposed of — which is exactly what the 2026-08-12
entry immediately below predicts. Recorded here because that entry is still un-ticketed,
so there is no issue to comment on; it should carry this occurrence when it graduates.

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

**The lens contract's scratch rule implies a route the permission layer refuses.**
Severity **L**. `fallback-review-panel.md` tells each lens to namespace its scratch by lens
and revision; lenses reach for remove-then-recreate to honour that, and `rm -rf` is refused
here, so each works around it with a fresh never-reused path — which is what the
namespacing rule wanted anyway. The rule is right and the route it implies is not.
Proposed fix: say so in the contract — a fresh path per lens per revision, never a
removal — one sentence that removes a refusal from every lens run.

**Provenance, deliberately narrow:** a lens reported this first-hand in `#440`'s own panel,
which is where a reader can check it. An earlier draft of this entry claimed *every* lens on
`#437` hit it. That was drawn from session transcripts rather than from anything `#437`
publishes, and both `#440` lenses independently went looking for it in that PR's record and
found nothing — which is `#423`'s subject exactly, so the claim was narrowed to what an
artifact carries rather than restated more confidently.

**A full panel's launch prompt handed each lens the author's own class draws.**
Severity **M**. Found by a lens reviewing this very entry's PR, against my orchestration
rather than against the diff. `fallback-review-panel.md` hands the author's stated draws to
the **delta pass** on purpose — an anchoring accepted deliberately — and says the opposite
for a full panel: *"Full-panel lens prompts are untouched by all of this"*, plus "do not
push the gate into the lens prompts". I passed the draws through
`panel_prompt.py --carry-forward` on every full panel from `#437`'s third round onward, so
each of those was anchored toward confirming me. The lens that caught it had re-derived
both draws independently and said so, so the damage looks small — but "it happened not to
matter" is not a property of the mechanism. Proposed fix: `--carry-forward` is the wrong
carrier for a draw, since its own rendered heading is about what prior rounds *covered*;
either refuse draws there for a full panel, or give the delta pass its own flag so the two
cannot be confused. Related: the disposition-carrying gap in the entry above, which wants a
separate channel for the same reason.

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
