# Live-validation evidence bundles

Live runtime validation may promote a capability only when an independent reviewer can
recompute the claim from retained, redacted artifacts after every synthetic fixture,
lane session, external repository, and runtime session eligible for cleanup is gone.
A narrative record and a digest without the bytes it names are historical observations,
not durable capability evidence.

`<engine-dir>/verify_live_validation_bundle.py` is the repository-owned verifier for this
contract. Run it successfully against the copied destination before crossing a cleanup
boundary:

```text
uv run <engine-dir>/verify_live_validation_bundle.py <bundle>/bundle.json \
  --promotion <bundle>/promotion.json \
  --expect-authority docs/agentic-dev-kit/runtime-parity.md \
  --expect-source-repository <repository-url> \
  --expect-source-revision <full-source-sha> \
  --expect-reviewed-head <full-reviewed-head-sha> \
  --expect-runtime <runtime> \
  --expect-client-version <exact-client-version>
```

Verification is necessary, not sufficient. The named redaction reviewer still owns the
semantic checks no scanner can establish: that every capture is relevant, minimized,
truthfully excerpted from its authoritative observer, and free of private material.

## Directory and manifest contract

A bundle is a repository-owned directory containing only `bundle.json`,
`promotion.json` when a capability is promoted, and an `artifacts/` directory. Every
JSON object must have unique member names, every number must be finite, and integers
must fit the verifier's declared digit bound; parser ambiguity is not evidence.
`bundle.json` has this closed shape:

```json
{
  "schema_version": 1,
  "bundle_id": "runtime-capability-date",
  "source": {
    "repository": "https://github.com/owner/source",
    "revision": "<full source sha>"
  },
  "review": {
    "head": "<full reviewed head sha>",
    "observer": "<authoritative review read-back>"
  },
  "runtime": {
    "name": "codex",
    "client_version": "<exact client version output>",
    "session_persistence": "persistent",
    "applied_compute": {
      "model": "<runtime-observed model>",
      "effort": "<runtime-observed effort>",
      "cwd": "<runtime-observed cwd>",
      "session_id": "<runtime session id>",
      "attestation": "artifacts/runtime-attestation.json"
    }
  },
  "redaction": {
    "reviewed": true,
    "reviewer": "<reviewer identity>",
    "excluded": [
      "authentication-material",
      "credentials",
      "tokens",
      "unrelated-user-data",
      "unrelated-workspace-data"
    ]
  },
  "artifacts": [
    {
      "path": "artifacts/<file>",
      "sha256": "<digest of the retained destination bytes>",
      "kind": "<permitted kind>",
      "observer": "<authoritative observer>"
    }
  ],
  "claims": [
    {
      "id": "<bounded capability claim>",
      "evidence": ["artifacts/<file>"],
      "requires_applied_compute": false
    }
  ]
}
```

The manifest is the binding surface: its source revision, reviewed head, runtime and
client apply to every artifact digest and every claim-to-evidence link it contains.
An artifact record adds the authoritative observer for those exact retained bytes.
The verifier refuses unknown fields so an unimplemented assertion cannot hide beside
the enforced contract.

`promotion.json` is a separate, closed receipt. It names `bundle.json`, carries the
digest of its exact bytes, repeats the source revision, reviewed head, runtime and
client, names the parity authority being changed, and enumerates the promoted claim
IDs. The verifier compares every repeated field and, for promotion, requires the
reviewer to supply independently selected expected authority, source repository,
source revision, reviewed head, runtime, and client values. Obtain those expectations
from the review target and authoritative observer before reading the bundle labels; a
self-consistent manifest and receipt are not their own trust root. This is what refuses
a valid-looking pair relabeled to the wrong source revision or reviewed head.

## Permitted retained artifacts

Retain the smallest artifact that preserves the authoritative observation. The
verifier admits these kinds:

- `launcher-receipt`, `descriptor`, and `final-message` for the wrapper's own request,
  identity, transport, and terminal observations;
- `runtime-attestation` for a minimal runtime-owned session/turn-context excerpt;
- `command-capture` for bounded stdout/stderr or event excerpts whose exact bytes are
  the observer;
- `filesystem-readback`, `git-readback`, `forge-readback`, and `review-receipt` for
  independent destination observations;
- `source-digest` for copied engine/config bytes at the stamped source revision.

Artifacts must be regular UTF-8 text files below `artifacts/`, use a permitted text
suffix, appear exactly once in the manifest, fit the verifier's declared size bounds,
and have no undeclared file, directory, special-file, hidden, or unreadable neighbor.
The verifier walks the directory itself rather than treating an unreadable subtree as
empty. Symlinks are never evidence: they preserve access to the ephemeral source rather
than the bytes that must survive it.

## Excluded material and redaction

Never retain credentials, tokens, authentication or authorization material, private
keys, credential-bearing configuration, auth symlinks, unrelated operator files,
unrelated workspace source, full environment dumps, or a raw runtime transcript or
rollout containing conversation content. A private synthetic repository is not a
redaction boundary; these exclusions apply before committing its artifacts too.

Prefer structural minimization over replacement strings. Extract only the fields the
claim needs into a new artifact, inspect those destination bytes, and digest those
bytes. The verifier rejects credential-like JSON keys and common secret encodings in
both raw text and decoded JSON strings as a backstop. `redaction.reviewed: true` records
the required semantic review; it is not a claim that the scanner can prove absence of
every secret.

Synthetic fixture paths and synthetic repository identifiers may remain when they are
the evidence. Operator home paths and unrelated workspace paths do not. If a path is
load-bearing but private, use a stable placeholder in a bounded read-back and retain
the independently checked mapping outside the repository; do not promote a claim that
requires a later reader to recover that private mapping.

## Applied compute and ephemeral carriers

An argv model or effort is an instruction, not the authoritative observer of what the
runtime applied. When a claim depends on model, effort, or cwd, it must set
`requires_applied_compute: true`, use `session_persistence: persistent`, and include a
`runtime-attestation` whose observer is `runtime-session-context`. That artifact has
only this shape:

```json
{
  "session_id": "<id>",
  "turn_context": {
    "model": "<applied model>",
    "effort": "<applied effort>",
    "cwd": "<applied cwd>"
  }
}
```

The manifest repeats those fields and the verifier requires exact equality. A Codex
`--ephemeral` run deliberately retains no session rollout, so the verifier refuses it
for an applied-compute claim. Use a persistent run, copy the minimal attestation, verify
the copied destination, and only then remove the runtime session. A claim that does not
depend on applied compute may use an ephemeral carrier, but must leave
`runtime.applied_compute` null and may not imply model, effort, or cwd from argv.

## Capture, verify, promote, clean up

1. Fix the design matrix, permitted artifacts, observers, source revision, and expected
   review head before the live run.
2. Capture into the synthetic fixture. Keep credentials and unrelated data outside it.
3. Copy only permitted, minimized artifacts into the repository-owned bundle.
4. Re-read and digest the destination bytes. Fill `bundle.json`; never copy a digest
   computed only at the source.
5. Fill `promotion.json` only for claims the parity authority will actually promote.
6. Fix the expected authority/source/review/runtime/client values independently from
   the review target and authoritative observers. Run the verifier with those values
   and the promotion receipt. Review the retained bytes directly and independently
   recompute the claim.
7. Commit and review the bundle with the parity change. The reviewed synthetic/task
   head in the bundle and the reviewed implementation head are distinct when two pull
   requests exist; name both in the narrative instead of substituting one for the other.
8. Cross the cleanup boundary only after the verified repository destination exists.
   Verify fixture and synthetic-repository deletion separately and report any residue.

Failure at any step leaves the observation historical and the capability unpromoted.
Retry from the live source; never repair a missing artifact by preserving its old digest
or restating its conclusion in prose.
