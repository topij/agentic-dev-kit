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
fixture changes were committed on its `main`; they did not alter the source revision.

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

`codex --version` in `/Users/topi/Coding/agentic-dev-kit` at source revision
`bdfd6ee702a630f0575f0c186f51b3bbbcd1810a` on 2026-08-30 printed
`codex-cli 0.149.1`. The run was persistent: no `--ephemeral` carrier was used, and the
minimal attestation was copied before the runtime session was removed.

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
- source-file SHA-256 readings from the stamped source revision.

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
  poll bind the review evidence to the synthetic head;
- `codex-writing-lane-applied-compute` — the persistent runtime session attests the
  applied model, effort, cwd and session id repeated by the manifest.

The record does **not** promote the precise per-command approval transitions described
by the runtime's final prose, native user/project configuration reach, structured
denial read-back, denial causes, synthetic CI, a synthetic merge, or behavior of a
future client. The launcher receipt still carries `terminal.permission_denials: null`;
nothing here repairs or generalizes that transport limitation. The shipped Codex lane
default remains `read-only`.

## Verification and hostile mutations

The public CLI owns the promotion check. The reviewer fixes the expected values from
the review target and authoritative observers before reading the bundle's own labels:

```text
UV_CACHE_DIR=/private/tmp/session-start-uv-cache uv run \
  scripts/verify_live_validation_bundle.py \
  saved_plans/codex-writing-lane-evidence_2026-08-30/bundle.json \
  --promotion \
  saved_plans/codex-writing-lane-evidence_2026-08-30/promotion.json \
  --expect-authority docs/agentic-dev-kit/runtime-parity.md \
  --expect-source-repository https://github.com/topij/agentic-dev-kit \
  --expect-source-revision bdfd6ee702a630f0575f0c186f51b3bbbcd1810a \
  --expect-reviewed-head 5c4006d18e65e0443dc7b22f48c099ad07ce1da9 \
  --expect-runtime codex \
  --expect-client-version "codex-cli 0.149.1" \
  --json
```

That command in `/Users/topi/Coding/agentic-dev-kit`, using the verifier at
`76baa4079e885fae33a2d0efef3d18f402a2a4ff` on 2026-08-30, returned
`status: verified`, `promotion: true`, and the claim IDs enumerated above. The first
review pass had shown that comparing only the manifest and receipt let a
self-consistently relabeled pair pass; the independent expectation arguments above are
the resulting trust root.

The repository suite drives the same public CLI through hostile mutations. It refuses:

- surviving prose or a surviving declared digest when the named artifact is absent or
  altered;
- a self-consistent bundle and promotion receipt relabeled to another source revision,
  reviewed head, runtime, client, source repository, or capability authority;
- an ephemeral carrier for an applied-compute claim;
- a compute-dependent claim that omits the minimal runtime attestation;
- a retained runtime attestation that disagrees with its applied-compute binding;
- undeclared artifact neighbors, credential-key spelling variants, invalid UTF-8, and
  non-integer schema versions;
- a promotion receipt whose manifest digest no longer matches.

The kit-only positive control re-verifies this tracked bundle and promotion receipt so
later artifact loss, mutation, or rebinding makes the repository gate fail.

## Cleanup result

After the copied destination verified, the exact local fixture root
`/private/tmp/adk-codex-writing-20260830` was removed. In
`/Users/topi/Coding/agentic-dev-kit`, the absence command
`test ! -e /private/tmp/adk-codex-writing-20260830` returned zero on 2026-08-30. The
retained promotion therefore no longer depends on the local descriptor, rollout, auth
symlink, caches, or worktrees; its independent-binding verification is stamped above.

Deletion of the private synthetic GitHub repository did **not** succeed: GitHub returned
HTTP 403 because the current credential lacks the `delete_repo` scope. The cockpit did
not broaden operator authentication unattended. The private repository
`topij/adk-codex-writing-evidence-20260830` therefore remains as residue; the retained
bundle does not depend on it and its pre-cleanup private-repository read-back is in
`artifacts/forge-readback.json`.
