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

The launcher's digest-bound final output reports that the lane created the repository
note and descriptor-state probe, committed only the note, pushed `dev/write`, opened a
non-draft private pull request, read the pull request and patch back, and stopped without
merging. The cockpit independently matched the reported note, state bytes, remote
branch, Git object, descriptor state, GitHub repository and pull request. It recorded a
`fallback:codex` correctness receipt against synthetic head
`5c4006d18e65e0443dc7b22f48c099ad07ce1da9` and re-read the settled PR-watch state.
Because the minimized bundle does not retain or bind the task prompt, the promotion
does not assert that those observed outputs matched a pre-run request.

The retained artifacts are deliberately minimized:

- the runtime's exact client-version output and minimal persistent `turn_context`;
- redacted descriptor and launcher-receipt fields that bind the lane identity, policy,
  transports, argv and terminal state;
- the exact last-message bytes whose digest the launcher receipt carries;
- bounded filesystem, Git remote/object, GitHub repository/PR, and PR-watch receipt
  read-backs;
- source-file SHA-256 ledgers and exact retained bytes for the upstream configuration,
  descriptor issuer, launcher, and their config-reader/root-discovery dependencies;
- retained commit content and minimal tree-object metadata that independently proves
  those source-file blobs belong to the named source and fixture revisions;
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

- `codex-writing-lane-observed-write-and-state` — the launcher's digest-bound final
  output reports the descriptor-bound worktree note and state probe, and the cockpit's
  retained filesystem and Git read-backs independently match those output bytes;
- `codex-writing-lane-open-nondraft-clean-private-pr` — the lane commit reached the
  remote and an independently read-back private pull request was open, non-draft, and
  reported GitHub merge state `CLEAN`; this does not claim the kit's separate
  review-and-settling gate had passed;
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
  --expect-claim '{"evidence":["artifacts/descriptor.json","artifacts/launcher-receipt.json","artifacts/final-message.txt","artifacts/filesystem-readback.txt","artifacts/git-readback.txt","artifacts/source-digests.txt","artifacts/execution-source-digests.txt","artifacts/source-proof.json","artifacts/fixture-proof.json","artifacts/fixture/config/dev-model.yaml","artifacts/source/config/dev-model.yaml","artifacts/source/scripts/dev_session.sh","artifacts/source/scripts/launch_lane.py","artifacts/source/scripts/lib/kitconfig.py","artifacts/source/scripts/lib/repo_root.sh"],"id":"codex-writing-lane-observed-write-and-state","requires_applied_compute":false}' \
  --expect-claim '{"evidence":["artifacts/descriptor.json","artifacts/launcher-receipt.json","artifacts/final-message.txt","artifacts/forge-readback.json","artifacts/git-readback.txt","artifacts/source-digests.txt","artifacts/execution-source-digests.txt","artifacts/source-proof.json","artifacts/fixture-proof.json","artifacts/fixture/config/dev-model.yaml","artifacts/source/config/dev-model.yaml","artifacts/source/scripts/dev_session.sh","artifacts/source/scripts/launch_lane.py","artifacts/source/scripts/lib/kitconfig.py","artifacts/source/scripts/lib/repo_root.sh"],"id":"codex-writing-lane-open-nondraft-clean-private-pr","requires_applied_compute":false}' \
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
of the uncorrelated applied-compute claim are part of the resulting trust root. A fresh
panel then showed that local-time capture dates failed behind the capture timezone,
digest-ledger rows did not structurally require the source bytes they named, and the
promotion's claimed complete runtime object omitted session persistence. UTC capture
dates, the closed ledger grammar with digest/Git-blob/source-file and claim-link checks,
and the independent session-persistence expectation are the resulting corrections.
A fallback panel at `c280e219566eec7567367c25c758d9c6d25fd93b` on 2026-08-30 then
found that a fixture-specific revision header could replace the manifest source
revision, the implementation rejected a documented promotion subset, and Unicode C1
controls crossed the string boundary. The mandatory source-revision header,
supplementary fixture-base header, selection by the promotion receipt, and full
Unicode-control rejection are the resulting corrections.
A fresh fallback panel at `680e402dbd2764b7a9241ce7e95f85883b1c1b2d` on
2026-08-30 found that the inverse promotion subset was refused when only an unpromoted
claim carried applied compute, source revision could occur after the ledger's opening
line despite the adopter contract, identity fields still admitted Unicode controls,
and common non-JSON credential keys escaped the redaction backstop. Promotion-scoped
compute comparison, mandatory first-line source identity, schema-wide Unicode-control
refusal, and raw credential-key and YAML-block-scalar refusal are the resulting
corrections.
A fresh fallback panel at `8e0c58dbd3fe02bb0763e04ce857a5e3f332eb90` on
2026-08-30 found that retained source bytes and Git blob IDs were self-consistent but
did not prove membership in the named revision; bidirectional and zero-width format
controls still crossed identity fields; the maintained parity plan overstated the
uncorrelated runtime attestation; and closed-schema plus artifact-observer requirements
were not mutation-pinned. Retained commit/tree proof traversal, schema-wide refusal of
Unicode control and format categories, corrected promotion wording, and public-CLI
hostile tests for the central closed-schema and observer guards are the resulting
corrections.
A correctness lens at `98ce743e72321badbafbbabb82e291965c51ac53` on
2026-08-30 found that a claim citing source bytes could omit their ledger and proof,
an ordinary artifact observer was not mutation-pinned, and nested closed schemas were
not mutation-pinned. A separately launched adversarial lens demonstrated that a
Unicode format character could split a credential marker in retained artifact content,
then the reviewer route stopped under its security-content filter and produced no
receipt. Bidirectional source-evidence closure, ordinary-observer and nested-schema
hostiles, and credential scanning after control/format removal are the resulting
corrections; the changed head still requires a fresh complete panel.
A fresh fallback panel at `15a40c86c20659789cae15d7e746832ea9ef23b1` on
2026-08-30 found that a source-digest ledger could promote with fixture-only bytes,
YAML type tags could hide a credential scalar from the redaction backstop, and the
nested closed-schema hostile set omitted enforced objects. Mandatory source rows and
source proof in every source-digest ledger, tagged-scalar refusal, and hostile
unknown-field coverage across the manifest source, review, runtime, applied-compute,
redaction, artifact, and claim objects; the promotion and its runtime; the attestation
and its turn context; Git proofs, trees, and tree entries; and the expected claim and
applied-compute objects are the resulting corrections.
A fresh correctness lens at `4c2c9bdf247a9c0ca506385236a076f7f9b8bf09` on
2026-08-30 found that the promoted descriptor carried the local calendar date rather
than the UTC date in its own `issued_at` field, and that the CHANGELOG described
schema-string control rejection as an artifact-wide rule. The adversarial lens at the
same head mutation-tested the applied-compute attestation kind and observer guards,
then stopped under its security-content filter without producing a receipt. The
correction committed as `2f0491085d0103eeb01db24cbce6a325c6a7add6` on 2026-08-30
bound the run artifacts to their UTC dates, recomputes the descriptor, launcher, and
review-receipt dates from retained timestamps, pins the attestation metadata guards,
and scopes the CHANGELOG statement to schema strings. The changed head still requires
a fresh complete panel.
A fresh correctness lens at `d08b282f89d499d16db509507aaf229726f52f99` on
2026-08-30 found that the fixture proof did not establish that the retained launcher
sources were present in the executed fixture revision, the semantic control did not
bind the authoritative ready/settled fields, and the source-ledger capture-date guard
was not mutation-pinned. A separately launched adversarial lens at the same head
demonstrated that the manifest accepted a claim array beyond the declared ceiling and
that the retained-promotion omission guard killed its hostile mutation, then stopped
under its security-content filter while probing Unicode redaction boundaries and
produced no receipt. Fixture-revision proof of every retained execution dependency,
direct semantic assertions for the forge and review-poll outcomes, capture-date and
claim-bound hostiles, escaped-surrogate refusal, and credential scanning after Unicode
compatibility normalization are the resulting corrections. The changed head still
requires a fresh complete panel.
A fresh fallback panel at `5f27d2af457216ca27b87c03fc602ebd5b7ae384` on
2026-08-30 produced a clean adversarial report and a correctness finding: disabling
tree-object hash reconstruction or extra-tree rejection survived the complete
drift-excluded suite even though the record said altered tree proofs were refused.
Public-CLI hostiles now alter retained tree entries under their declared object ID and
add a valid unreferenced proof tree, pinning both refusals. The changed head still
requires a fresh complete panel.
A fresh adversarial lens at `12b6ca54410e0b659ab9fc80a877e7cfd87944de` on
2026-08-30 demonstrated that a credential-like JSON key split by a Unicode format
character or written with compatibility characters could pass verification. A
separately launched correctness lens at the same head showed that the redaction-review
approval, exact exclusion declaration, and source-proof leaf/blob comparison were not
behaviorally pinned. Credential-key scanning now uses the normalized collapsed form,
and public-CLI hostiles pin the redaction gates and a hash-valid proof whose requested
path points to the wrong blob. The changed head still requires a fresh complete panel.
A fresh correctness lens at `a2d7ee5367b2ae557176abbb61ced8b12ab29d58` on
2026-08-30 found that the retained prompt was neither minimized nor bound, so the
promotion could establish observed output but not that it satisfied a pre-run request.
It also showed that the clean refusal for a Git commit proof without a header boundary
was not mutation-pinned. The promoted claim is now explicitly limited to
launcher-reported output independently matched by cockpit read-backs and includes the
digest-bound final message in its evidence; a public-CLI no-header hostile pins the
refusal path. The separately launched adversarial lens stopped under its
security-content filter while probing credential syntax and produced no receipt. The
changed head still requires a fresh complete panel.
A fresh adversarial lens at `179a2ffc6a0f1096872b20e0ad6395165643b013` on
2026-08-30 reported no findings. A separately launched correctness lens at the same
head showed that weakening the shared closed-object guard to admit scalar values
survived the complete drift-excluded suite, after which a scalar `source` escaped the
documented refusal path with an uncaught type error. Public-CLI hostiles now replace
the manifest, its closed nested objects, promotion, runtime attestation, Git proof
objects, and independent expectation objects with scalars and require exit `2` without
a traceback. The changed head still requires a fresh complete panel.
A fresh adversarial lens at `0406f2f61fc500bbed2be1104359cc22fc37fdc9` on
2026-08-30 changed a retained artifact immediately after its digest read and showed the
verifier accepting semantic bytes different from the digested bytes. A separately
launched correctness lens at the same head promoted a non-compute claim citing a
`runtime-attestation` whose object did not have the contract's closed shape. The
verifier now uses a stable descriptor snapshot for every byte-dependent operation,
confirms retained bytes again before success, and validates every runtime-attestation
shape while keeping applied-compute equality and carrier checks conditional. Public-CLI
hostiles inject manifest and artifact changes during descriptor reads and promote a
malformed non-compute attestation. The changed head still requires a fresh complete
panel.
A fresh correctness lens at `bad1cdd884de9026c402d62115ce59c8d7b425dd` on
2026-08-30 replaced the final byte-confirmation helper with a no-op; the complete
`make mutation-test` gate still passed, showing that the descriptor-read hostile
exercised only the initial snapshot. A separately launched adversarial session built a
scratch probe that added an undeclared artifact immediately after the inventory walk,
then stopped under its security-content filter before producing a review receipt.
Public-CLI hostiles now change the manifest, an artifact, and the promotion
receipt after their initial snapshots, and add undeclared bytes after the earlier
inventory walks. Final bundle-root, artifact-inventory, and byte confirmations refuse
those mutations. The changed head still requires a fresh complete panel.
A fresh adversarial lens at `e69b76bc02aa2255372518cd2671cda6c7232672` on
2026-08-30 altered a declared artifact and added an undeclared artifact as the final
promotion inventory iterator reached exhaustion; the public CLI returned
`status: verified` for each hostile. A separately launched correctness lens at the
same head found that the promoted “ready” claim exceeded the retained forge read-back,
which establishes only that the private pull request was open, non-draft, and reported
GitHub merge state `CLEAN`. It also moved the manifest claim-count guard after
per-claim validation; `make mutation-test` in its isolated scratch checkout at that
revision on 2026-08-30 reported `2289 passed, 1 deselected, 3 warnings in 382.21s`.
Directory walks now compare their descriptor identity across and after traversal,
retained bytes are confirmed after the final inventory, the promoted claim is narrowed
to the forge properties, and the count-order hostile makes an over-limit entry
malformed. The changed head still requires a fresh complete panel.
A fresh adversarial lens at `83c9a59ed9d06704cd3fc100186ef4aade2e9ffe` on
2026-08-30 showed that the promoted raw assignments `api-key: hunter2-secret` and
`AWS-SECRET-ACCESS-KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` each returned
`status: verified`. Its ancestor-symlink hostile was refused safely, after which the
review route stopped under its security-content filter and produced no receipt. A
separately launched correctness lens at the same head found that the generic full-Git-
SHA wording contradicted the verifier's SHA-1-only proof construction and that replacing
the revision-format guard with a nonempty-string check survived the drift-excluded
suite. Raw credential assignments now cover hyphen and underscore separators, the
schema explicitly supports SHA-1 object-format repositories, and a self-consistent
invalid-revision hostile pins the format refusal. The changed head still requires a
fresh complete panel.
A fresh adversarial lens at `f393daac78397022a03d833e2f09e03e5cdc9375` on
2026-08-30 reproduced a raw undecodable byte in `--expect-claim` escaping the
documented refusal path with `UnicodeEncodeError`, a traceback, and exit `1`. A
separately launched correctness lens at the same head replaced the byte-identical
`artifacts/` directory between the bundle-root and artifact-tree inventories; the
public CLI returned `status: verified` even though the top-level directory identity
changed during the invocation. The JSON-bearing expectation options now validate
surrogateescaped input before encoding, and the CLI binds the initial bundle-root and
artifact-directory identities through its final success check. Public-CLI hostile
probes pin the directory-replacement and malformed-argument refusal paths. The changed
head still requires a fresh complete panel.
The documented verifier command above in `/Users/topi/Coding/agentic-dev-kit` at
`823ee30f4df13be211285ed85fedc6244f5d1a44` on 2026-08-30 returned
`status: verified`, `promotion: true`, and
`codex-writing-lane-observed-write-and-state`,
`codex-writing-lane-open-nondraft-clean-private-pr`, and
`codex-writing-lane-exact-head-review-receipt`.
The documented verifier command above in `/Users/topi/Coding/agentic-dev-kit` at
`62a8f372d34fbb9fed6d49abd08d8bc7f477ad6d` on 2026-08-30 returned
`status: verified`, `promotion: true`, and
`codex-writing-lane-observed-write-and-state`,
`codex-writing-lane-ready-private-pr`, and
`codex-writing-lane-exact-head-review-receipt`. The middle historical claim ID was
later narrowed and renamed by the review response recorded above.
`UV_CACHE_DIR=/private/tmp/adk-651-uv-cache UV_PYTHON=3.12 make test` in that
directory at the same revision and date reported `2256 passed, 3 warnings in
368.47s`.
An earlier run of that command in `/Users/topi/Coding/agentic-dev-kit`, using the
verifier at
`d276f80de1368b46149e26d1f29eb41485c180de` on 2026-08-30, returned
`status: verified`, `promotion: true`, and
`codex-writing-lane-observed-write-and-state`,
`codex-writing-lane-ready-private-pr`, and
`codex-writing-lane-exact-head-review-receipt`.

The repository suite drives the same public CLI through hostile mutations. It refuses:

- surviving prose or a surviving declared digest when the named artifact is absent or
  altered;
- a self-consistent bundle and promotion receipt relabeled to another source or review
  repository, source revision, reviewed head, redaction reviewer, runtime, client,
  session-persistence carrier, applied-compute object, capability authority, claim ID,
  thinner claim-to-artifact relationship, or contradictory retained artifact bytes;
- an ephemeral carrier for an applied-compute claim;
- a compute-dependent claim that omits the minimal runtime attestation;
- a retained runtime attestation that disagrees with any applied-compute binding;
- a malformed runtime attestation even when its claim does not depend on applied
  compute, or a manifest or artifact changed during its descriptor read;
- a source-digest ledger with an unsupported row, an absent or mismatched source-file,
  a mismatched Git blob, a missing or altered commit/tree proof, a source path absent
  from the named revision, or a claim link that omits bytes or proof named by its ledger;
- undeclared bundle-root or artifact-tree neighbors, unreadable subtrees, special
  files, a symlinked bundle root, duplicate JSON members, credential-key spelling
  variants, secret markers hidden by JSON escaping, invalid UTF-8, non-finite or
  oversized JSON numbers, non-string persistence values, non-integer schema versions,
  symlink loops, and unreadable artifact bytes without a traceback;
- a bundle root or artifact directory changed during its inventory, an undeclared
  artifact added as the final inventory exhausts, or a declared artifact changed
  before the post-inventory byte confirmation;
- a promotion receipt whose manifest digest no longer matches.
- a retained promotion receipt omitted from the invocation, an ancestor-symlinked
  bundle, artifact, or promotion path, unstamped artifact metadata, common passphrase,
  Basic-auth, Slack-token, quoted, unquoted, or YAML block-scalar password assignment,
  client-secret, auth-token, Unicode-split credential markers, and AWS credential
  shapes, duplicate artifact paths, and
  either independently guarded aggregate input envelope or an artifact tree beyond the
  declared bounds.

The kit-only structural control re-verifies this tracked bundle and promotion receipt.
The claim-semantic control independently asserts the complete claim-to-artifact map and
the load-bearing literal identities and relationships among the client-version capture,
descriptor, launcher, final-message, destination and retained source-file read-backs,
private open/non-draft/`CLEAN` pull request, exact-head review receipt, and redaction
reviewer. It pins
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
