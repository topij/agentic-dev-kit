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
  --expect-review-repository <review-repository-url> \
  --expect-reviewed-head <full-reviewed-head-sha> \
  --expect-redaction-reviewer <reviewer-identity> \
  --expect-runtime <runtime> \
  --expect-client-version <exact-client-version> \
  --expect-session-persistence <persistent|not-applicable|ephemeral> \
  --expect-applied-compute \
  '{"model":"<model>","effort":"<effort>","cwd":"<cwd>","session_id":"<id>","attestation":"artifacts/runtime-attestation.json"}' \
  --expect-claim \
  '{"id":"<claim>","evidence":["artifacts/runtime-attestation.json","artifacts/<file>"],"requires_applied_compute":true}'
```

Verification is necessary, not sufficient. The named redaction reviewer still owns the
semantic checks no scanner can establish: that every capture is relevant, minimized,
truthfully excerpted from its authoritative observer, and free of private material.

## Directory and manifest contract

A bundle is a repository-owned directory containing only `bundle.json`,
`promotion.json` when a capability is promoted, and an `artifacts/` directory. Every
JSON object must have unique member names, every number must be finite, and integers
must fit the verifier's declared digit bound; parser ambiguity is not evidence. If a
`promotion.json` is present, the verifier refuses bundle-only verification: the caller
must supply `--promotion` and every independent expected binding. The byte ceiling
covers the manifest, receipt, and artifacts, and the artifact- and claim-count
ceilings apply before per-entry validation or artifact I/O.
Directory inventories are stable snapshots: the verifier refuses a bundle root or
artifact directory whose descriptor identity changes during its walk, then confirms
the manifest, promotion receipt, and every declared artifact against the retained
bytes after the final inventory. A concurrent writer is therefore not a permitted
evidence carrier: the verifier does not lock the filesystem, so run it against a
private destination with no writer and treat any later change as invalidating the
verification.
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
    "repository": "https://github.com/owner/review-target",
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
      "capture_request": "<exact observer command or request>",
      "captured_on": "<UTC YYYY-MM-DD>",
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
An artifact record adds the authoritative observer, exact capture command or request,
and UTC capture date for those exact retained bytes. Together with the manifest source
revision and reviewed head, those fields stamp each retained reading rather than
leaving its age or provenance to narrative inference.
The verifier refuses unknown fields so an unimplemented assertion cannot hide beside
the enforced contract.

`promotion.json` is a separate, closed receipt stored beside the `bundle.json` it
names; an external receipt cannot replace the bundle's own copy. It carries the digest
of the manifest's exact bytes, repeats the source revision, review repository, reviewed
head, redaction reviewer, and complete runtime object, names the parity authority being
changed, and enumerates the promoted claim IDs. The verifier compares every repeated
field and, for promotion, requires the reviewer to supply independently selected
expected authority, source repository, source revision, review repository, reviewed
head, redaction reviewer, runtime, client, session-persistence carrier, and complete
promoted claim objects. When a claim depends on applied compute, the caller must also
supply the complete expected applied-compute object with `--expect-applied-compute`.
The bundle may retain validated claims that are not promoted. Only the IDs enumerated
by `promotion.json` are selected and compared with the independent expected claim
objects.
Applied compute carried only by an unpromoted retained claim remains structurally
validated but is outside the promotion; omit `--expect-applied-compute` unless a
selected claim depends on it.
Supply each claim with
repeatable `--expect-claim` compact JSON, including its ordered evidence paths and
applied-compute dependency. Obtain those expectations from the review target and
authoritative observer before reading the bundle labels; a self-consistent manifest and
receipt are not their own trust root. This refuses a valid-looking pair relabeled to the
wrong source or review repository, revision, reviewed head, reviewer, or applied
compute; a claim renamed to imply a broader capability; and a claim whose evidence
links were thinned.

A tracked capability promotion also needs a repository-owned semantic control with an
exact path-to-digest map fixed outside the bundle. That control must hash the retained
destination and compare the manifest's path/digest map with the same independent
values. Without it, contradictory receipt or narrative bytes can be changed together
with their manifest and promotion digests while remaining self-consistent. Structural
verification still owns absence, alteration against the declared digest, inventory,
and generic bindings; the independent map owns the exact promoted artifact bytes.

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
- `source-digest` for a bounded ledger of copied engine/config bytes at the stamped
  source revision, and `source-file` for each exact retained byte sequence the ledger
  names and a promoted claim depends on;
- `source-git-proof` for the exact commit content and minimal Git tree-object metadata
  that proves each named source-file blob belongs to the stamped revision.

A source-digest ledger is not a substitute for its source bytes. It has exactly one
`source revision: <sha>` header matching the manifest. Every `source/` row requires a
`source proof: artifacts/<file>.json` header, and every ledger must retain at least one
`source/` row plus that proof. A fixture ledger may add one
`fixture base revision: <sha>` and one `fixture proof: artifacts/<file>.json` header,
but those never replace the source revision. The fixture proof must prove both every
`fixture/` row and every `source/` execution dependency in that ledger at the fixture
revision; a fixture whose executed dependency differs from the retained source bytes
is not evidence for a wrapper-attributed claim. Each data row is
`<sha256><two spaces><source-or-fixture/path><two spaces>git-blob:<sha>`.
An optional `captured on: <UTC YYYY-MM-DD>` header must match the artifact record.
Retain every row's path as a `source-file` with the same SHA-256 and link the ledger,
all named source files, and every used proof from the claim. The verifier refuses an
unlisted source file or proof.

A source Git proof is closed JSON carrying its namespace, revision, exact commit lines,
and the complete entries of only the tree objects needed for the ledger paths. The
verifier reconstructs the Git commit and tree bytes, recomputes their object IDs,
walks from the commit's root tree to each path, and compares the reached blob with both
the ledger and retained source-file bytes. Extra proof trees are invalid. This keeps
revision membership independently recomputable from the redacted bundle after the
source checkout or synthetic fixture has been removed.

A wrapper-attributed claim retains the exact fixture configuration and direct
repository source dependencies used by the issuer and launcher, not only their
upstream versions. When fixture bytes differ from the source revision, retain the
fixture bytes, source and fixture revision identities, and an independently asserted
complete delta.
When execution cannot be bound to those retained bytes or an exact fixture tree, narrow
the claim to its independently observed outcome or leave it historical.

Artifacts must be regular UTF-8 text files below `artifacts/`, use a permitted text
suffix, appear exactly once in the manifest, fit the verifier's declared per-artifact
and aggregate size bounds, and have no undeclared file, directory, special-file,
hidden, or unreadable neighbor.
The verifier bounds and walks the directory itself rather than treating an unreadable
subtree as empty. Symlinks are never evidence: they preserve access to the ephemeral
source rather than the bytes that must survive it. This prohibition covers every
component of the bundle, artifact, and promotion paths, not only the final directory
entry; artifact bytes are not opened through an ancestor symlink before refusal.
Each file is opened through a non-symlink-following descriptor and read into a bounded
snapshot. Size, digest, credential scanning, JSON parsing, source-proof recomputation,
and claim validation use those same bytes. The verifier compares descriptor identity
and metadata before and after the read, then confirms the bundle-root and artifact-tree
inventories, manifest, promotion receipt, and artifact bytes again before returning
success. A promotion therefore validates the exact manifest snapshot named by its
digest rather than reopening that path as a new observation.

## Excluded material and redaction

Never retain credentials, tokens, authentication or authorization material, private
keys, credential-bearing configuration, auth symlinks, unrelated operator files,
unrelated workspace source, full environment dumps, or a raw runtime transcript or
rollout containing conversation content. A private synthetic repository is not a
redaction boundary; these exclusions apply before committing its artifacts too.

Prefer structural minimization over replacement strings. Extract only the fields the
claim needs into a new artifact, inspect those destination bytes, and digest those
bytes. The verifier rejects credential-like JSON keys, raw credential-key assignments,
YAML-tagged credential scalars, YAML credential block scalars, and common secret
encodings in raw text and decoded JSON strings as a backstop. It rejects escaped
Unicode surrogates, then repeats those scans after compatibility normalization and
removing control, format, and combining-mark characters so an invisible separator
cannot split a credential marker in either a value or a JSON key.
`redaction.reviewed: true` records the required semantic review; it is not a claim that
the scanner can prove absence of every secret.

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

Every declared artifact of kind `runtime-attestation` has that closed shape and uses
observer `runtime-session-context`, even when no promoted claim depends on applied
compute. The equality, persistent-carrier, and independent applied-compute expectation
checks become mandatory only when a claim sets `requires_applied_compute: true`.
The manifest and promotion receipt repeat those fields, the verifier requires exact
equality, and the promotion caller must supply the same values from an independent
runtime observation. The minimal attestation establishes those values for its session;
it does not by itself prove that the session performed a separately retained launcher
invocation. A claim tying applied compute to a lane run must also retain a minimized
runtime-owned correlation to that launch, such as a session-owned task nonce and final
output digest bound into the launcher receipt. If no such durable correlation exists,
leave applied compute outside that lane claim. A Codex `--ephemeral` run deliberately
retains no session rollout, so the verifier refuses it for an applied-compute claim. Use
a persistent run, copy the minimal attestation and required correlation, verify the
copied destination, and only then remove the runtime session. A claim that does not
depend on applied compute may use an ephemeral carrier, but must leave
`runtime.applied_compute` null and may not imply model, effort, or cwd from argv.

## Capture, verify, promote, clean up

1. Fix the design matrix, permitted artifacts, observers, source revision, and expected
   review head before the live run.
2. Capture into the synthetic fixture. Keep credentials and unrelated data outside it.
3. Copy only permitted, minimized artifacts into the repository-owned bundle.
4. Re-read and digest the destination bytes. Record the exact observer command or
   request and capture date beside each digest. Fill `bundle.json`; never copy a digest
   computed only at the source.
5. Fill `promotion.json` only for claims the parity authority will actually promote.
6. Fix the expected authority/source/review/redaction/runtime/client values, applied
   compute, and complete claim objects independently from the review target and
   authoritative observers. Run the verifier with those values and the promotion
   receipt. Review the retained bytes directly and independently recompute the claim's
   semantic relationships, including hashes of every retained source file, rather than
   treating structural verification as proof of what the retained fields mean.
7. Commit and review the bundle with the parity change. The reviewed synthetic/task
   head in the bundle and the reviewed implementation head are distinct when two pull
   requests exist; name both in the narrative instead of substituting one for the other.
8. Cross the cleanup boundary only after the verified repository destination exists.
   Verify fixture and synthetic-repository deletion separately and report any residue.

Failure at any step leaves the observation historical and the capability unpromoted.
Retry from the live source; never repair a missing artifact by preserving its old digest
or restating its conclusion in prose.
