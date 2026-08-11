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
