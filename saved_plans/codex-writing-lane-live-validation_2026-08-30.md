# Codex writing-lane durable validation — 2026-08-30

## Authority and boundary

This is a new live run through the repository-owned retention contract added for
`#621`. It does not revise the 2026-08-27 writing-lane observation or turn that
record's deleted receipts, rollouts, and captures into evidence. That observation stays
bounded to its stamped client and source revision.

The retained bundle is
[`codex-writing-lane-evidence_2026-08-30/`](codex-writing-lane-evidence_2026-08-30/).
Its promotion receipt names
[`runtime-parity.md`](../docs/agentic-dev-kit/runtime-parity.md) as the capability
authority.

## Live construction

The cockpit copied the tracked repository at source revision
`bdfd6ee702a630f0575f0c186f51b3bbbcd1810a` into a private synthetic GitHub repository.
The fixture-only configuration selected `workspace-write`, disabled required CI for the
repository that intentionally had no checks, and configured no review bot. Those
fixture changes were committed on its `main` at
`83d3b623305a691dd874df44ca92270daa62ade9`; they did not alter the source revision.

`dev_session.sh new write --headless --runtime codex --merge-class operator` issued the
persistent descriptor retained as `artifacts/descriptor.json`. `launch_lane.py` started
`codex exec` through its config-declared transports. The runtime-owned persistent
`turn_context` retained in `artifacts/runtime-attestation.json` reports:

```json
{
  "session_id": "01a04fb1-0b63-7921-982b-23ff66c200be",
  "turn_context": {
    "cwd": "/private/tmp/adk-codex-writing-20260830/sessions/write/wt",
    "effort": "max",
    "model": "gpt-5.6-sol"
  }
}
```

`codex --version` in the `<kit-checkout>` at source revision
`bdfd6ee702a630f0575f0c186f51b3bbbcd1810a` on 2026-08-30 printed
`codex-cli 0.149.1`. The run was persistent: no `--ephemeral` carrier was used, and the
minimal attestation was copied before the runtime session was removed. The retained
attestation does not correlate that session id to the launcher invocation, so its
model, effort, and cwd remain a stamped historical observation rather than a promoted
property of the lane run.

## Independently retained observations

The lane created the requested repository note and descriptor-state probe, committed
only the note, pushed `dev/write`, opened a ready private pull request, read the pull
request and patch back, and stopped without merging. The cockpit then read the remote
branch, Git object, worktree, descriptor state, GitHub repository and pull request
independently. It recorded a `fallback:codex` correctness receipt against synthetic
head `5c4006d18e65e0443dc7b22f48c099ad07ce1da9` and re-read the settled PR-watch state.

The retained artifacts are deliberately minimized:

- the runtime's exact client-version output and minimal persistent `turn_context`;
- redacted descriptor and launcher-receipt fields that bind the lane identity, policy,
  transports, argv and terminal state;
- the exact last-message bytes whose digest the launcher receipt carries;
- bounded filesystem, Git remote/object, GitHub repository/PR, and PR-watch receipt
  read-backs;
- source-file SHA-256 ledgers and exact retained bytes for the upstream configuration,
  descriptor issuer, launcher, and their config-reader/root-discovery dependencies;
- the exact synthetic configuration at fixture revision
  `83d3b623305a691dd874df44ca92270daa62ade9`, whose complete byte delta from the
  upstream configuration is independently constrained to the declared workspace-write,
  no-bot, and no-required-CI fixture changes.

Each manifest artifact record binds those bytes to its authoritative observer, exact
capture request, and capture date; the manifest source revision and reviewed head
complete the measurement stamp.

The bundle excludes the authentication symlink and its target, controlled native
configuration, full runtime rollouts, automatic-review rollout, caches, databases,
prompt transcript, environment dump, unrelated repository files, operator-owned files,
and user/workspace data outside the synthetic fixture.

## Promoted claims

The promotion receipt names these recomputable claims:

- `codex-writing-lane-scoped-write-and-state` — the descriptor-bound lane produced the
  requested worktree note and exact descriptor-state probe;
- `codex-writing-lane-ready-private-pr` — the lane commit reached the remote and an
  independently read-back private pull request that was open and ready;
- `codex-writing-lane-exact-head-review-receipt` — the cockpit's receipt and settled
  poll bind the review evidence to the synthetic head.

The record does **not** promote the precise per-command approval transitions described
by the runtime's final prose, native user/project configuration reach, structured
denial read-back, denial causes, synthetic CI, a synthetic merge, or behavior of a
future client. The launcher receipt still carries `terminal.permission_denials: null`;
nothing here repairs or generalizes that transport limitation. The shipped Codex lane
default remains `read-only`. Applied model, effort, cwd, and session identity are also
not promoted because their retained authoritative observer is not correlated to this
launcher invocation.

## Verification and hostile mutations

The public CLI owns the promotion check. The reviewer fixes the expected values from
the review target and authoritative observers before reading the bundle's own labels:

```text
UV_CACHE_DIR=/private/tmp/adk-651-uv-cache uv run --python 3.12 \
  scripts/verify_live_validation_bundle.py \
  saved_plans/codex-writing-lane-evidence_2026-08-30/bundle.json \
  --promotion \
  saved_plans/codex-writing-lane-evidence_2026-08-30/promotion.json \
  --expect-authority docs/agentic-dev-kit/runtime-parity.md \
  --expect-source-repository https://github.com/topij/agentic-dev-kit \
  --expect-source-revision bdfd6ee702a630f0575f0c186f51b3bbbcd1810a \
  --expect-review-repository https://github.com/topij/adk-codex-writing-evidence-20260830 \
  --expect-reviewed-head 5c4006d18e65e0443dc7b22f48c099ad07ce1da9 \
  --expect-redaction-reviewer codex-cockpit-gpt-5-6-sol-max \
  --expect-runtime codex \
  --expect-client-version "codex-cli 0.149.1" \
  --expect-session-persistence persistent \
  --expect-claim '{"evidence":["artifacts/descriptor.json","artifacts/launcher-receipt.json","artifacts/filesystem-readback.txt","artifacts/git-readback.txt","artifacts/source-digests.txt","artifacts/execution-source-digests.txt","artifacts/fixture/config/dev-model.yaml","artifacts/source/config/dev-model.yaml","artifacts/source/scripts/dev_session.sh","artifacts/source/scripts/launch_lane.py","artifacts/source/scripts/lib/kitconfig.py","artifacts/source/scripts/lib/repo_root.sh"],"id":"codex-writing-lane-scoped-write-and-state","requires_applied_compute":false}' \
  --expect-claim '{"evidence":["artifacts/descriptor.json","artifacts/launcher-receipt.json","artifacts/final-message.txt","artifacts/forge-readback.json","artifacts/git-readback.txt","artifacts/source-digests.txt","artifacts/execution-source-digests.txt","artifacts/fixture/config/dev-model.yaml","artifacts/source/config/dev-model.yaml","artifacts/source/scripts/dev_session.sh","artifacts/source/scripts/launch_lane.py","artifacts/source/scripts/lib/kitconfig.py","artifacts/source/scripts/lib/repo_root.sh"],"id":"codex-writing-lane-ready-private-pr","requires_applied_compute":false}' \
  --expect-claim '{"evidence":["artifacts/forge-readback.json","artifacts/review-receipt.json"],"id":"codex-writing-lane-exact-head-review-receipt","requires_applied_compute":false}' \
  --json
```

The first review pass showed that comparing only the manifest and receipt let a
self-consistently relabeled pair pass; later hostile passes showed that preserving a
claim ID while thinning its artifact links, fabricating applied compute and lane
identity together, relabeling review provenance, or retaining source hashes without
their bytes remained self-consistent. A subsequent exact-head panel changed the design
again: contradictory launcher, final-message, and review-receipt bytes still survived
when their manifest digests were restamped; the two aggregate-envelope guards shared
one non-isolating mutation test; quoted password assignments evaded the redaction
backstop; and upstream wrapper bytes omitted the fixture configuration and direct
source dependencies. The exact artifact-digest control, separated guard mutations,
quoted-assignment refusal, executed-fixture ledger, bounded fixture delta, and removal
of the uncorrelated applied-compute claim are the resulting trust root.
That command in `/Users/topi/Coding/agentic-dev-kit`, using the verifier at
`ef15802ddaabbfef38e65ce3d5976951fa25aaa9` on 2026-08-30, returned
`status: verified`, `promotion: true`, and the claim IDs enumerated above.

The repository suite drives the same public CLI through hostile mutations. It refuses:

- surviving prose or a surviving declared digest when the named artifact is absent or
  altered;
- a self-consistent bundle and promotion receipt relabeled to another source or review
  repository, source revision, reviewed head, redaction reviewer, runtime, client,
  applied-compute object, capability authority, claim ID, thinner claim-to-artifact
  relationship, or contradictory retained artifact bytes;
- an ephemeral carrier for an applied-compute claim;
- a compute-dependent claim that omits the minimal runtime attestation;
- a retained runtime attestation that disagrees with any applied-compute binding;
- undeclared bundle-root or artifact-tree neighbors, unreadable subtrees, special
  files, a symlinked bundle root, duplicate JSON members, credential-key spelling
  variants, secret markers hidden by JSON escaping, invalid UTF-8, non-finite or
  oversized JSON numbers, non-string persistence values, non-integer schema versions,
  symlink loops, and unreadable artifact bytes without a traceback;
- a promotion receipt whose manifest digest no longer matches.
- a retained promotion receipt omitted from the invocation, an ancestor-symlinked
  bundle, artifact, or promotion path, unstamped artifact metadata, common passphrase,
  Basic-auth, Slack-token, quoted or unquoted password-assignment, and AWS credential
  shapes, duplicate artifact paths, and either independently guarded aggregate input
  envelope or an artifact tree beyond the declared bounds.

The kit-only structural control re-verifies this tracked bundle and promotion receipt.
The claim-semantic control independently asserts the complete claim-to-artifact map and
the load-bearing literal identities and relationships among the client-version capture,
descriptor, launcher, final-message, destination and retained source-file read-backs,
private ready pull request, exact-head review receipt, and redaction reviewer. It pins
every retained artifact byte independently of the manifest and keeps the uncorrelated
runtime attestation outside the promoted claim map.

## Cleanup result

After the copied destination verified, the cockpit removed the exact local fixture root
`/private/tmp/adk-codex-writing-20260830` on 2026-08-30. The retained promotion
therefore no longer depends on the local descriptor, rollout, auth symlink, caches, or
worktrees; its independent-binding verification is stamped above.

Deletion of the private synthetic GitHub repository did **not** succeed: GitHub returned
HTTP 403 because the current credential lacks the `delete_repo` scope. The cockpit did
not broaden operator authentication unattended. The private repository
`topij/adk-codex-writing-evidence-20260830` therefore remains as residue; the retained
bundle does not depend on it and its pre-cleanup private-repository read-back is in
`artifacts/forge-readback.json`.
