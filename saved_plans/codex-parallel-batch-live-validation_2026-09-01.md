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
lane, session, review-decision, and reconciliation dependency to the promoted source.

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

The manifest carries the ordered `review.heads` set for alpha and beta. The promotion
receipt repeats that complete set, and the independent verifier invocation supplies
each head separately in the same order. Git, forge, scope receipt, panel-run, external
artifact-map, and semantic-control bytes bind each set member to its lane.

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

The source closure retains the exact `pr_watch.py` bytes that decided the scope
receipts and reconciliation's `held` outcome. Its Git proof and the fixture proof
bind those bytes to the promoted source and the synthetic fixture base. The exact
rendered prompts, run records, reports, scope receipts, and review heads are retained;
the prompt renderer need not be replayed to recover the prompt bytes supplied to a
lens. The repository-owned verifier that promotes the bundle is reviewed and
versioned by this PR; it is not mislabeled as an execution dependency of the older
source revision that the lane run exercised.

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

The root PR's adversarial lens then found that the first bundle had retained the old
source-revision verifier as an execution dependency even though that verifier could
not accept the new EOF field. The finding was accepted: the corrected bundle removes
that file from both source ledgers and the complete claim map, while the PR-versioned
verifier remains the promotion mechanism rather than being mislabeled as lane-run
source.

A fresh adversarial lens at the corrected root-PR head found that the retained
descriptors were reduced projections whose bytes did not match their durable launch
authority digests, that the review-decision source closure omitted `pr_watch.py`, and
that the new commit-EOF boolean guard lacked a malformed-value test. Each finding was
accepted. The regenerated bundle retains each authentic descriptor byte-for-byte,
retains and Git-proves the executed review engine, and the semantic control checks the
descriptor-authority hashes directly. The verifier's Python-source redaction backstop
parses assignments so a runtime value carried by a credential-named local variable is
not mistaken for retained credential material; statically recoverable credential
assignments and known secret shapes remain refused. The EOF regression now covers a
falsey non-boolean value.

The next fresh adversarial lens found that the Python-source exception still admitted
a credential literal embedded in a dynamic expression, and that the batch promotion
used the singular reviewed-head schema while its exact-head claim spanned alpha and
beta. Both findings were accepted. Credential-target expressions now inspect embedded
literal fragments while allowing the structural authorization scheme used by the
retained review engine. The bundle, promotion receipt, CLI expectation, external
fixture, and semantic control now bind the complete ordered reviewed-head set.

A fresh adversarial lens at `e600eba2d04241ddc069c4e19f090544540be2c8` on
2026-09-01 then demonstrated that a coordinated relabeling of the manifest,
promotion receipt, and external fixture could still replace that set without changing
the retained lane evidence. It also demonstrated that the Python-source exception
admitted credential-bearing function and lambda defaults. The findings were accepted.
The semantic control now derives the ordered global set from the lane heads it checks
against the filesystem, forge, and exact-head review receipts. The source-ledger path
now treats positional, keyword-only, and lambda defaults as assignments and refuses
statically recoverable credential values there.

`UV_PYTHON=3.12
UV_CACHE_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-cache
UV_TOOL_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-tools
make test` in the clean detached worktree
`/private/tmp/adk-codex-parallel-20260901.xlAufG/final-c9a3cda` at
`c9a3cda743c95287d56af2f8197b4de8a827ea5b` on 2026-09-01 printed `2387
passed, 3 warnings in 410.07s` and returned exit `0`. The warnings are pytest
cleanup warnings for its own temporary hostile trees.

The next fresh adversarial lens at
`d1632475dd235f4f04b794ef544e0919db582758` on 2026-09-01 demonstrated that an
inline callable could still hide a credential literal from the new AST traversal.
The finding was accepted without widening into credential-assignment forms that
predate this PR. Call expressions now inspect the callable as well as its arguments,
and the public source-ledger tests cover the demonstrated assignment and default
forms.

`UV_PYTHON=3.12
UV_CACHE_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-cache
UV_TOOL_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-tools
make test` in the clean detached worktree
`/private/tmp/adk-codex-parallel-20260901.xlAufG/final-e847246` at
`e847246420a653dc22e75660d554f97b02b4ee13` on 2026-09-01 printed `2389
passed, 3 warnings in 395.39s` and returned exit `0`. The warnings are pytest
cleanup warnings for its own temporary hostile trees.

The convergence adversarial lens at
`50f8a3d19bf6e2d38bb175ac5cfb9fc3fdf822d5` on 2026-09-01 then demonstrated
that the environment-lookup exception ignored uppercase literal defaults as though
they were lookup keys. It separately showed that coordinated digest updates could
replace the persisted operator session metadata with `self` without failing the
semantic control. The findings were accepted. Environment lookup scanning now exempts
only the positional or named key argument, and the semantic control compares each
persisted session record exactly with its lane identity and operator authority.

`UV_CACHE_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/full-test-cache uv
run --with pytest --with pyyaml pytest scripts/tests/test_live_validation_bundle.py
-q` at `d3243e780d93078148fa890520e59247b37e2e42` on 2026-09-01 printed `211
passed, 3 warnings in 10.60s`. The warnings are pytest cleanup warnings for its own
temporary hostile trees; the test command returned exit `0`.

The independently parameterized verifier command at
`d3243e780d93078148fa890520e59247b37e2e42` on 2026-09-01 returned status
`verified` with retained snapshot SHA-256
`bf417bebff866a4fac9e34d37ea9b14047b53a9e3df61283d43709a0a601a205`. That
snapshot is recomputed from the bundle's directory and file bytes rather than read
from its manifest.

After the accepted descriptor, review-source, and malformed-field findings were
repaired, `UV_PYTHON=3.12
UV_CACHE_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-cache
UV_TOOL_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-tools
make test` in the clean detached worktree
`/private/tmp/adk-codex-parallel-20260901.xlAufG/final-45f8db3` at
`45f8db3312cec3300f6dacea90b2306462cb3c93` on 2026-09-01 printed `2382 passed,
3 warnings in 367.56s` and returned exit `0`. The warnings are pytest cleanup
warnings for its own temporary hostile trees.

The independently parameterized verifier command in that same worktree at
`45f8db3312cec3300f6dacea90b2306462cb3c93` on 2026-09-01 returned status
`verified` with retained snapshot SHA-256
`990c3788d41c346ab70096f89459db4df77c5834628418b833cfa665ce9be447`.

After the credential-expression and reviewed-head-set findings were repaired,
`UV_PYTHON=3.12
UV_CACHE_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-cache
UV_TOOL_DIR=/private/tmp/adk-codex-parallel-20260901.xlAufG/post-review-py312-tools
make test` in the clean detached worktree
`/private/tmp/adk-codex-parallel-20260901.xlAufG/final-1374e65` at
`1374e658aca81928fbda2d5081a4e2b0af150d02` on 2026-09-01 printed `2384 passed,
3 warnings in 369.55s` and returned exit `0`. The warnings are pytest cleanup
warnings for its own temporary hostile trees.

The independently parameterized verifier command in that same worktree at
`1374e658aca81928fbda2d5081a4e2b0af150d02` on 2026-09-01 returned status
`verified` with retained snapshot SHA-256
`473bf7058b2bb6d3957b3ec042c1899ed5e02d86c2389da848980bb749c576e5`.
