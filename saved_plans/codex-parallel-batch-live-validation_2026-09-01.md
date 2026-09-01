# Codex parallel-batch retained live validation — 2026-09-01

## Result

This Codex-produced run satisfies the Phase 4 retained-evidence exit for the
bounded claims in its promotion receipt. The independently supplied promotion
expectations, exact artifact map, and semantic recomputation are checked outside
the bundle in
[`codex_parallel_batch_expected.json`](../scripts/tests/fixtures/codex_parallel_batch_expected.json)
and `test_the_promoted_codex_parallel_batch_remains_independently_recomputable`.
The retained redacted bytes are in
[`codex-parallel-batch-evidence_2026-09-01/`](codex-parallel-batch-evidence_2026-09-01/).

The promoted source revision is
`6679856f7c9f14eac921f3b033c0077729bb17e1`. The synthetic fixture base is
`f13b3e995558ee2f14b656bba2e1a0f74d2254c2` in the private repository
`topij/adk-codex-parallel-evidence-20260901`. The fixture carries only its declared
test configuration differences; the execution ledger byte-matches every retained
lane, session, reconciliation, and verifier dependency to the promoted source.

## Retained observations

- `parallel-alpha` is bound by descriptor and launcher receipt to
  `dev/parallel-alpha`, its descriptor-scoped worktree and state root, fixture base
  `f13b3e995558ee2f14b656bba2e1a0f74d2254c2`, and exact reviewed head
  `59ad80980fb3c9d609c41c6ffc7f7fed0e12db97` on pull request `#2`.
- `parallel-beta` is bound by descriptor and launcher receipt to
  `dev/parallel-beta`, its descriptor-scoped worktree and state root, the same
  fixture base, and exact reviewed head
  `57e4209a79080d7605cd8e42cb53fe8bdc5d3f38` on pull request `#1`.
- The cockpit filesystem read-back shows distinct canonical worktree paths and
  distinct canonical state-root paths. Each worktree marker agrees with its
  descriptor and launcher observation. Git object and remote read-backs bind each
  head to only its declared note path.
- Each ready pull request remains `OPEN` with no merge commit. Its scope-local
  `pr-watch` receipt is bound to that pull request's exact head and records the
  independently run `adversarial` and `correctness` lenses through
  `fallback:panel`.
- `scripts/dev_session.sh merge parallel-alpha` and
  `scripts/dev_session.sh merge parallel-beta` each returned the operator-authority
  refusal. `scripts/reconcile_sessions.sh parallel-alpha parallel-beta` at fixture
  base `f13b3e995558ee2f14b656bba2e1a0f74d2254c2` on 2026-09-01 returned exit `4`
  and printed a `held` row for each scope. The final GitHub read-back still showed
  both pull requests open and unmerged.

The manifest's schema-level review anchor is the alpha head because schema version
`1` has one `review.head`. The beta head is not inferred from that anchor: it is
separately fixed by the Git, forge, scope receipt, panel-run, external artifact-map,
and semantic-control bytes.

## Review disposition and caveats

The alpha correctness lens reported a Low record-prose imprecision: the lane note's
sentence naming an evidence role does not itself contain the worktree or state-root
identities. The GitHub disposition classifies the note as a lane-output marker and
binds the promoted identity claim to the descriptor, marker, launcher receipt, and
cockpit filesystem read-backs instead. No fixture commit was made, so the reviewed
head stayed fixed. The other retained reports filed no finding.

The fixture changes no executed code. The independent lenses nevertheless ran the
fixture's full suite. `make test` at alpha head
`59ad80980fb3c9d609c41c6ffc7f7fed0e12db97` and beta head
`57e4209a79080d7605cd8e42cb53fe8bdc5d3f38` on 2026-09-01 printed `11 failed,
2312 passed, 51 skipped` in the fixture configuration. The same failures reproduce
at the fixture base and arise from deliberately removed CI/review requirements and
their hook expectations, not either note-only lane diff. This record therefore does
not promote a clean fixture-suite claim.

The first sandboxed launcher attempts stopped before the Codex child ran because the
host denied access to the user's Codex state. They remain outside the promoted
bundle and are not counted as lane observations. The first alpha adversarial lens
was interrupted when the operator closed the host; it produced no report and was
rerun from a fresh context. Only the completed rerun is retained.

The source closure deliberately excludes review-helper implementation bytes whose
ordinary `token = …` local-variable text triggers the bundle's credential backstop.
The exact rendered prompts, run records, reports, scope receipts, and review heads
are retained. The source closure covers the behavior under validation: configuration,
lane session and launcher engines, reconciliation, state/config libraries, and the
bundle verifier.

## Promotion verification

Disposable hostile copies were required to fail for the cases enumerated in
[`codex-parallel-batch-design_2026-09-01.md`](codex-parallel-batch-design_2026-09-01.md).
The run refused an absent lane receipt, a restamped altered descriptor, a claim that
dropped the other lane, a relabeled review head, a relabeled operator class, absent
ledger source bytes, a credential-like JSON key, and a promotion invocation without
independent expectations. The positive retained bytes were then verified again.

The source commit has no final newline in its Git commit object. That exposed a
verifier defect which reconstructed every commit with one. The verifier now records
and recomputes the actual EOF form while remaining backward-compatible with existing
proofs. The regression test uses a real recomputed Git object ID rather than a mocked
verdict.

`UV_CACHE_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/full-test-cache uv
run --with pytest --with pyyaml pytest scripts/tests/test_live_validation_bundle.py
-q` at `3534e93e806edd605facdd3bc08fe86302fcd750` on 2026-09-01 printed `211
passed, 3 warnings in 10.64s`. The warnings are pytest cleanup warnings for its own
temporary hostile trees; the test command returned exit `0`.

The independently parameterized verifier command at
`3534e93e806edd605facdd3bc08fe86302fcd750` on 2026-09-01 returned status
`verified` with retained snapshot SHA-256
`abb797907e8358366bf8124d3592cf1887e990b36e333c523e58c27ea2d2d2d4`. That
snapshot is recomputed from the bundle's directory and file bytes rather than read
from its manifest.
