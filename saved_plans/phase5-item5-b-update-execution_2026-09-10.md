# ITEM5-B-UPDATE-01 — execution record

The operator approved `ITEM5-B-UPDATE-01 as scoped` on 2026-09-10. This record
applies the [decision packet](phase5-item5-b-update-decision_2026-09-10.md) at
kit record revision `4ee132ae4f4a4a0d0fd600e6da6e5325e5f68b34`; its repair source
remains exactly `60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`.

## Applied update and preservation

The execution bound absolute paths before writes:

- `REPO=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture`
- `KIT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source`
- `OUT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/update-60fe0dc-20260910`

The source advanced locally from detached
`8418118e40728c667c32a28a182697139bc7a5ef` to the repair pin. The fixture attempt
was committed as `413132b01d14c735d94753231bf325904135285f` on
`chore/item5-b-update-60fe0dc`; the historical `chore/adopt-agentic-dev-kit` ref
was retained at `07bacf5bda3b1e7a6718c7d4528336ef81dc2143`.

The packet's exact ledger owns the applied file set. On 2026-09-10,
`python3 -B "$REPO/scripts/devkit/kit_doctor.py" --root "$REPO" --record-install --from-kit "$KIT"`
ran from `$REPO` at `07bacf5bda3b1e7a6718c7d4528336ef81dc2143` with the approved
payloads in the working tree, against the repair source pin. It produced baseline
SHA-256 `9e2196df3b7239b599819abcfc20271b0389b70f78f22837a0709575145b9126`.
`record-install.json` and `baseline-recorded.json` retain the invocation, output and
actual baseline bytes; the release manifest was not copied into the fixture.

The [execution evidence](phase5-item5-b-update-evidence_2026-09-10/sha256.json) retains the fresh before-audit, backup verification,
source Git-object comparison, payload destination hashes/modes, complete
tracked/merged configuration mappings and ownership readbacks. The archive and bundle
files remain at the declared `OUT` paths; their hashes accompany the repository evidence.
No original evidence directory was replaced. Retained-tree initialization was not repeated;
initializer calls within the declared tests use their controlled temporary fixtures.

## Verification

The verification observations below were made on 2026-09-10. The fixture directory is `$REPO`
at `413132b01d14c735d94753231bf325904135285f`; the source directory is `$KIT`
at `60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`. The absolute roots above apply to
this table. [Command records](phase5-item5-b-update-evidence_2026-09-10/verification-commands.json)
retain argv, cwd, task environment, start/end times, status and output hashes.

| Command and working directory | Actual result and limit |
|---|---|
| `python3 -B "$REPO/scripts/devkit/kit_doctor.py" --root "$REPO" --manifest "$KIT/kit-manifest.json" --json`; `$REPO` | Exit `0`; the [full report](phase5-item5-b-update-evidence_2026-09-10/installed-doctor.stdout.log) records installed-byte, dependency, baseline, registration and lens states. This is not client-loading or trust evidence. |
| `python3 -B "$KIT/scripts/kit_doctor.py" --root "$REPO" --adapter-report --adapter-source "$KIT" --json`; `$REPO` | Exit `0`; the [adapter report](phase5-item5-b-update-evidence_2026-09-10/source-adapter-report.stdout.log) retains the custom Codex wrap-up as `adopter-owned` and the generated bindings as `kit-current`. This does not grant final preserved-file acceptance. |
| `python3 -B "$REPO/scripts/devkit/check_doc_budget.py"`; `$REPO` | Exit `0`; the [budget output](phase5-item5-b-update-evidence_2026-09-10/fixture-document-budget.stdout.log) records the configured document readings. No archival workflow was exercised. |
| `uv run --with pytest --with pyyaml python -B "$REPO/scripts/devkit/run_installed_tests.py" --root "$REPO"`; `$REPO` | Exit `0`; `2129 passed, 128 skipped in 898.84s (0:14:58)`. The [complete log](phase5-item5-b-update-evidence_2026-09-10/installed-suite.stdout.log) retains the selected modules and actual skip reasons. No exclusion rerun replaced this result. |
| `make test`; `$KIT` | Exit `2`; `1 failed, 2497 passed, 1 skipped in 472.05s (0:07:52)`. The [complete log](phase5-item5-b-update-evidence_2026-09-10/source-make-test.stdout.log) retains lint, syntax-recipe and pytest output. The failure is the previously disclosed #393 deep-JSON node; it is kept separate from the installed result. No source repair or causal-resolution claim is made. |
| Separate `bash -n` calls for `$KIT/scripts/dev_session.sh`, `$KIT/scripts/reconcile_sessions.sh`, `$KIT/scripts/lib/repo_root.sh`, `$KIT/scripts/hooks/pre-push`, and `sh -n "$KIT/init.sh"`; `$KIT` | Each command exited `0`. These parse checks cover the documented #561 recipe gap; they do not execute the shell paths. |

The suites ran serially with checkout writes paused. Their environment routed state,
uv/Ruff/pytest caches and temporary files under `$OUT`, with bytecode writes disabled.
The before/final inventories, configuration mappings, preservation hashes, Git readbacks
and replay hashes are retained in the [evidence ledger](phase5-item5-b-update-evidence_2026-09-10/sha256.json).
The post-command comparisons detected no unexpected source or fixture differences. These are
checkpoint observations; they do not prove that no transient write occurred between reads.

No rollback was performed. Verified byte archives and Git bundles remain under `$OUT`;
[backup verification](phase5-item5-b-update-evidence_2026-09-10/backups-verified.json)
and the approved packet retain the bounded rollback route. A later rollback must first
revalidate the actual state; it must not discard intervening work.


## Remaining decision

This update does not complete Phase 5 item 5. Final preserved-file acceptance,
fixture PR lifecycle, adoption completion and the untested systemize routes remain
separate decisions. No client exercise, fixture remote, fixture PR, tracker payload or
user-profile change was executed under this approval.

Completed item 6 and its replay evidence retain their recorded credit. Do not repeat
cs-toolkit #2222, #2223 or #2255. Kit #723 remains the approved upstream deferral.
The operator placed #585 earlier in the sprint, outside Phase 6. Kit #724 already
delivered the #722 record batch. Neither original missing path was reconstructed.

Next session: review the preserved-file acceptance at the recorded fixture revision,
then prepare the exact next field-exit decision without launching a client or opening
a fixture PR under this consumed update approval.
