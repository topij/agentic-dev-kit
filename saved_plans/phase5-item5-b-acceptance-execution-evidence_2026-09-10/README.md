# ITEM5-B acceptance execution evidence

The [execution record](../phase5-item5-b-acceptance-execution_2026-09-10.md) owns
interpretation and limits. `authority.json` binds the exact operator message to the
original decision packet, payload ledger and fresh pre-write audit. The original
proposal ledger remains historical; its preparation flag is not the later authority.

- `acceptance-audit.json` is the raw pre-write UPDATE FINAL comparison.
- `pr729-readback.json` retains the required delivery and review checkpoints.
- `payload-ledger.json`, `payload-applied.json` and `backups-verified.json` bind the
  approved file destinations and the verified local archive/bundle.
- `configuration.json`, `preserved.json` and `baseline.json` retain the pre-write
  acceptance bindings. The approved friction replacement is recorded separately.
- Local command names pair a `.json` argv/environment/status record with complete
  `.stdout.log` and `.stderr.log` files. Kit verification uses `kit-verification.json`.
- `repo-create.json`, `base-push.json`, `default-branch.json`, `head-push.json`,
  `pr-create.json` and `pr-ready.json` retain publication readbacks. Repository API
  data is projected to the requested identity; unrelated private names and credential
  metadata are omitted from the durable record.
- `fixture-ci-job.json` and `fixture-ci-job.log` bind the hosted run and terminal log.
- `fixture-*-full-report.md`, `fixture-*-compute.json` and `fixture-*-receipt.json`
  retain complete independent reports, actual compute and pre-fix forge readbacks.
- `result.json`, `retained-state.json`, `forge-*-exit.json` and
  `fixture-final-poll.json` preserve the review stop and exact next decision.
- `external-sha256.json` binds retained local artifacts; `sha256.json` binds this
  directory, excluding itself. `execute.py.txt` and `checkpoint.py.txt` preserve
  the historical helper programs; they are not standalone resume instructions.

The execution's retained root is
`/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910`.
Its before/final inventories include non-Git files and separate Git administrative
inventories. Byte archive, Git bundle, isolated verification copies, caches and state
remain in the approved local locations. The final retention ledger binds external
artifacts by absolute path and SHA-256; it does not copy caches into the kit.

Copied full review reports are verbatim. Their relative evidence links resolve in
the original `full_report` location recorded in each receipt; the external retention
ledger binds those supporting files.

Historical UPDATE/replay evidence is not rewritten. These records do not authorize
rerunning the mutation drivers, refreshing the baseline or merging the fixture PR.

`record-validation.json` records the initial record snapshot before kit review at
`d2d32d56e3bdedcd0b32b1210a459f6429e3d6fd`; its patch hash is historical. The repair
proposal's `manifest-verification.json` and `amendment-validation.json` own the later
manifest amendment and its validation. Do not apply the initial patch-hash assertion
to the amended proposal.
