# ITEM5-B — approved setup and local verification

The operator replied `Approve ITEM5-B as scoped` to the
[decision packet](phase5-item5-decision_2026-09-09.md) at
`edc199f42bc65b1850172ea79b791ef358577ae1` on 2026-09-09, then requested autonomous
continuation. The approved setup and checks ran. **Successful adoption verification
was not established:** the installed suite failed. The setup approval is consumed;
source repairs, another fixture update, client exercises and completion remain separate.

## New baseline and evidence

- Fixture: `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture`, branch
  `chore/adopt-agentic-dev-kit`, input commit `8533c334637e8776ca7a4fe3a9fd8c6c64e35707`,
  installed baseline commit `07bacf5bda3b1e7a6718c7d4528336ef81dc2143`.
- Independent source: `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source`,
  detached at `8418118e40728c667c32a28a182697139bc7a5ef`, with its local clone origin
  removed. The fixture has no remote. Neither original missing path was reconstructed.
- [Evidence ledger](phase5-item5-b-evidence_2026-09-09/sha256.json): exact commands,
  prompt transcript, config mappings, copy ledger, baseline, inventories, registration
  hashes, complete suite logs and failure excerpts. The archived `.py.txt` drivers
  document this execution; they are **not resume commands** and must not be rerun.

`initializer-terminal.txt`, `installed-suite.log` and `kit-suite.log` retain raw
terminal whitespace, including CRLF in the initializer transcript. They are excluded
explicitly from authored-file whitespace checks; their integrity is checked by the
evidence ledger rather than by normalizing the recorded bytes.

The staging program bound absolute roots, asserted cwd before writes and compared
destination hashes. Only `scripts/` was remapped to `scripts/devkit/`; the installer,
docs, adapters and reference files retained their root-relative destinations.
The custom Codex wrap-up adapter and policy without its ownership marker were preserved.
The installed reader compared the complete tracked and merged config mappings with
the retained intended mappings; post-init comparison also checked scalar types.

`bash <fixture>/init.sh --no-clobber` used the packet's exact answers. Its
[terminal](phase5-item5-b-evidence_2026-09-09/initializer-terminal.txt) reported:

| Resolved path | Recorded action |
|---|---|
| `ROADMAP.md`, `notes/history.md`, `AGENTS.md`, `CLAUDE.md` | Already in use; left untouched. Retained input hashes matched afterward. |
| `notes/friction.md`, `notes/friction-archive.md` | Seeded. |
| `config/claude-lane-settings.json`, `.claude/agents/adversarial.md`, `.claude/agents/correctness.md` | Seeded; lens bytes matched the installed current renderer. |
| `.git/hooks/pre-push`, `.gitignore` | Installed the shim and appended the reported ignore entries. |

The retained REG-01 payloads were then placed at `.codex/hooks.json`,
`.codex/config.toml` and `.claude/settings.json`, with destination hashes checked.
This installs configuration, including the Claude permission grants; it does not
establish what a client loaded or trusted. No client session was launched in the fixture.

## Verification and limits

These commands ran on 2026-09-09. Their linked stamps give the exact argv, cwd, source
pin, revision, state override, timestamps, output digest and Git status. The installed
and source suites ran serially with separate external `DEVKIT_STATE_ROOT` directories.

| Command and directory | Revision | Actual result |
|---|---|---|
| Installed `check_doc_budget.py` and `kit_doctor.py --manifest <source>/kit-manifest.json`, cwd fixture | `07bacf5bda3b1e7a6718c7d4528336ef81dc2143` | [Budget output](phase5-item5-b-evidence_2026-09-09/document-budget.log) and [doctor output](phase5-item5-b-evidence_2026-09-09/installed-doctor.log) exited zero. The doctor used the independent source manifest and named the expected baseline. |
| Source `kit_doctor.py --root <fixture> --adapter-report --adapter-source <source> --json`, cwd fixture | Source `8418118e40728c667c32a28a182697139bc7a5ef`; fixture `07bacf5bda3b1e7a6718c7d4528336ef81dc2143` | [Report](phase5-item5-b-evidence_2026-09-09/source-adapter-report.log) exited zero, preserving the custom wrap-up as `adopter-owned`. |
| `uv run --with pytest --with pyyaml python -B <fixture>/scripts/devkit/run_installed_tests.py --root <fixture>`, cwd fixture | `07bacf5bda3b1e7a6718c7d4528336ef81dc2143` | [Complete log](phase5-item5-b-evidence_2026-09-09/installed-suite.log): `58 failed, 2066 passed, 120 skipped in 353.54s (0:05:53)`, exit 1. |
| `make test`, cwd source | `8418118e40728c667c32a28a182697139bc7a5ef` | [Complete log](phase5-item5-b-evidence_2026-09-09/kit-suite.log): `1 failed, 2484 passed, 1 skipped in 401.06s (0:06:41)`, make exit 2. The failing node is the known #393 deep-JSON test. |

The [inventory comparison](phase5-item5-b-evidence_2026-09-09/inventory-comparison.json)
records tool-cache additions and no changes or removals to pre-existing inventoried
paths across verification. Inventories exclude `.git`; the
[terminal result](phase5-item5-b-evidence_2026-09-09/verification-result.json) separately
records empty Git status in the fixture and source. The nested runner exercises the
declared installed modules; its skips and failures remain part of the result. No
exclusion rerun, fixture repair or source repair was used to turn it into a pass.

## Failure assessment and proposed repair writes — not authorized

The [extracted failures](phase5-item5-b-evidence_2026-09-09/installed-failure-excerpts.json)
match every summary failure node to its retained traceback. Extraction does not claim
a complete root-cause proof. The tracebacks and source reads establish these examples:

- `test_init_sh.py` uses the live adopter config as `shipped_config()` while expecting
  kit defaults, source comments and kit-owned document markers. Substitutions targeting
  the kit's `bots`, tracker and handoff values can make no change in this fixture.
- `test_kit_doctor.py` adapter setup uses the adopter as its source corpus and rejects
  the preserved wrap-up. Its CLI test then parses empty stdout before checking the
  returned status. `test_portability.py` also expects generated wrap-up content.
- `test_mutation_gate.py::test_the_drift_test_actually_executes` expects its child
  self-check never to skip. `git show 7cb0868935e907bbc3f9d8b7d36fe885a6f9edbb --
  scripts/tests/test_kit_doctor.py`, read from the cockpit at `edc199f42bc65b1850172ea79b791ef358577ae1`
  on 2026-09-09, shows #705 adding `require_kit_source()` to that child. Its legitimate
  adopter skip now conflicts with the unchanged parent assertion: an introduced
  applicability regression, separate from the pre-existing config/adapter assumptions
  and from #393. This attribution uses the source diff; no historical fixture was rerun.

`gh issue view 534 --repo topij/agentic-dev-kit --json body,comments`, read on
2026-09-09 at cockpit `edc199f42bc65b1850172ea79b791ef358577ae1`, supplies the existing
kit-only-invariant, cross-test dependency and adopter-input scope, including its appended
corrections. The proposed next kit-only slice is:

| Proposed path | Intended repair and required evidence |
|---|---|
| `scripts/tests/test_init_sh.py` and controlled test fixtures under `scripts/tests/fixtures/` | Separate source-contract inputs from live adopter config and documents; prove the intended hostile edits actually land before testing their rejection. |
| `scripts/tests/test_kit_doctor.py`, `scripts/tests/test_portability.py` and their controlled adapter fixtures | Use an explicit generated source corpus when testing kit-owned adapters; retain separate tests that preserve custom adopter adapters. Check CLI status before parsing its output. |
| `scripts/tests/test_mutation_gate.py` | Align the liveness assertion with the child's declared source applicability, while proving it still detects an improperly skipped drift check in a kit source tree. |
| `kit-manifest.json`, `CHANGELOG.md`, ordinary result/handoff records | Account for changed or added shipped test inputs and explain the adopter action in the same repair PR. |

This is a proposed scope, not a prepared patch or permission to mutate the retained
fixture. Run `make test` and meaningful isolated installed-layout checks for an approved
repair; retain the #393 result separately. Updating ITEM5-B to a repaired pin needs its
own exact source/destination decision. The occurrence is parked in the friction inbox:
the operator was asleep and had not approved an exact tracker-comment payload.

## Maintained sprint state and next action

Phase 5 item 5 remains incomplete. Successful installed verification, preserved-file
acceptance, fixture PR lifecycle and the untested systemize routes retain their separate
boundaries. Item 6's replay stays complete at its recorded refs; #2222/#2223/#2255 were
not rerun or re-credited. #723's accepted deferral, #585's earlier placement outside
Phase 6 and the delivered #722 batch in kit #724 remain unchanged.

**Next session:** review and approve the kit-only #534 repair slice above. Recheck the
new fixture against its retained inventory before any later approved write; do not
repeat ITEM5-B setup or reconstruct either original missing path.


**Continuation — 2026-09-10:** the operator approved the kit-only repair slice above.
The [repair record](phase5-item5-kit534-repair_2026-09-10.md) supersedes this record's
historical approval request and next-session instruction. The retained fixture remains
subject to its separate update decision; this correction does not renew setup approval.
