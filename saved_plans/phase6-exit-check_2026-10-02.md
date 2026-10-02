# Phase 6 exit check — 2026-10-02

[#880](https://github.com/topij/agentic-dev-kit/issues/880) asks for the Phase 6 exit to
be checked as the [parity plan](codex-parity-plan_2026-08-23.md) states it, with the
command and revision behind each of its parts. The exit, from the plan's *Phase 6*
section:

> Done when the parity matrix is enforced by deterministic checks and confirmed by the
> Phase 5 adopter run.

Every observation below was taken at `7040d289942a80b0a87f6447048d29e3f37964d5`
(`main`) on 2026-10-02, unless it names another revision. **This record declares
nothing.** Declaring the exit is the operator's call, as it was for Phase 5.

## What "the parity matrix" covers

Phase 1 of the plan defines the matrix as "a maintained runtime-capability matrix
covering workflows, persistent instructions, safety activation, hooks, permissions,
model controls, subagents, external integrations, adoption, upgrade, and drift
detection", with structural checks "derive[d] … from that declaration".
[`runtime-parity.md`](../docs/agentic-dev-kit/runtime-parity.md) holds it in two halves,
and names them differently itself:

- **The declaration**, its front matter: `workflow_contract` and `adoption`. The file
  calls this "the machine-readable workflow inventory and adoption footprint".
- **The table**: *Capability matrix* and its *Headless lane isolation per runtime*
  sub-table. The file calls this "the matrix below", which "records broader capability
  parity that cannot be expressed as an adapter path".

The exit names no half, so this check takes both.

## Method

The deterministic checks were found by reading every reader of the file in `scripts/`,
`scripts/lib/`, `scripts/tests/`, both conftests, the `Makefile` and `.github/`.
Each finding was then tested by a mutation. Each mutation ran in its own
`git clone --no-hardlinks` of the main checkout, detached at the revision above. The
edit was applied by a script that asserted it matched exactly once, and was read back
with `git diff` before the run.

The runs use `make mutation-test`, or its pytest line, and not `make test`.
`kit-manifest.json` pins the file's SHA-256, so any byte change fails
`test_kit_repo_self_check_is_clean` and CI's manifest step. Regenerating the manifest
clears both. They record that the file changed, not what it says. The `Makefile`'s
comment above `mutation-test` gives the same reason.

## Part 1 — "enforced by deterministic checks"

### The declaration: enforced

Readers:

- `workflow_contract` is read by
  `test_portability.py::test_runtime_parity_contract_covers_workflows_and_adapters` and
  its `evidence`-marked variants. They check that the declared shared, Claude and Codex
  paths equal what is on disk, that each path follows its naming convention, and that
  the status vocabulary holds. It is also read by `test_adoption_fixtures.py`, where each
  fresh install must hold every declared file and each adapter must be its rendered
  template, and by `runtime_smoke.py`'s skill and command rows.
- `adoption` is read by `test_adoption_fixtures.py`. Each fresh Codex-only, Claude-only
  and dual-runtime install must hold exactly the declared footprint under `.claude/`,
  `.agents/` and `.codex/`.

Mutations:

| Mutation | Command | Result |
|---|---|---|
| Delete the `post-merge-systemize` entry from `workflow_contract` | `uv run --with pytest --with pyyaml python -m pytest -q -m 'not driftcheck' scripts/tests/test_portability.py::test_runtime_parity_contract_covers_workflows_and_adapters scripts/tests/test_adoption_fixtures.py` | `19 failed, 5 passed in 4.00s`, among them the coverage test and every fresh-install case |
| Replace `adoption.surfaces.codex` (`- .codex/hooks.json`) with `[]` | the same | `3 failed, 21 passed in 5.66s`: `test_an_undeclared_runtime_file_fails`, one per adopter, each `DID NOT RAISE` |

The second kill came from the negative control alone. `_assert_install_matches_declaration`
derives the directories it scans for undeclared files from the declaration. Once the
only declared `.codex/` file is removed, `.codex/` leaves the scan, and the install's
`.codex/hooks.json` is no longer compared against anything. The negative test plants
`.codex/undeclared.json` under a hard-coded directory list, so it is the one that
notices. The mutation is caught, but the positive check's failure message would not
point at the cause.

### The table: not enforced

Readers: one test reads table text.
`test_kit_doctor.py::test_shipped_runtime_adapters_equal_the_renderer_for_both_runtimes`
asserts three phrases, which appear only on the *Adapter upgrade* row: "fetched kit's
adapter renderer", "authored command preserved" and "authored skill preserved". No test
reads any other row, the per-runtime sub-table, or a link or anchor in the file. The
kit-doc link guard was built and reverted, and
[#216](https://github.com/topij/agentic-dev-kit/issues/216) carries its rebuild.

Mutation:

| Mutation | Command | Result |
|---|---|---|
| Delete everything from `## Capability matrix` up to `## Live promotion boundary`: the whole table and the sub-table | `env -u FORCE_COLOR make mutation-test` | `1 failed, 3967 passed, 1 skipped, 1 deselected in 700.40s (0:11:40)`; the one failure is the *Adapter upgrade* phrase test above, at `test_kit_doctor.py:444` |

This repeats, for the whole table, what
[#880's 2026-10-01 comment](https://github.com/topij/agentic-dev-kit/issues/880) found
for the sub-table at `edce2ca`.

Many rows describe behaviour whose repository side has tests of its own. For example,
the *Lifecycle validation boundary* section says repository checks keep the Claude-only
memory engine out of the shipped Codex hooks. Those tests pin the behaviour and not the
row: the row can be deleted or contradicted, and they still pass. This record does not
audit which rows' subjects are pinned that way.

## Part 2 — "confirmed by the Phase 5 adopter run"

The parity plan's *Sprint status* records Phase 5 as declared complete by the operator
on 2026-09-30, under the amendments of the
[Phase 5 E audit](phase5-e-audit_2026-09-30.md). The adopter run its *Done when* names
is the item 6 replay, [cs-toolkit replay](cs-toolkit-replay_2026-09-09.md), bound to kit
source `e698ec47d6284ccd31af5ba9d8bc5657fe992310`.

- **`workflow_contract` is unchanged since that run.** Front matter extracted from
  `git show e698ec4:docs/agentic-dev-kit/runtime-parity.md` and from the same file at
  `7040d28`, then compared with `diff`. The only difference is the 14-line `adoption`
  block, added by #904 (`0c7669a`).
- **The run's adapter report covers that declaration exactly.** A script compared the
  Claude and Codex paths declared at `e698ec4` with the entries in
  `saved_plans/cs-toolkit-replay-evidence_2026-09-09/adapter-report.json`. It printed
  `declared == reported paths: True` and `states: ['kit-current']`. The report also
  carries both runtimes' adapters into a Codex adopter. That is what
  `other_runtime: installed`, decided later on #878, records.
- **The `adoption` block postdates the run.** It is also scoped to the template route,
  which a mature adopter's upgrade does not take. The fresh-install fixtures in Part 1
  are its confirmation, and they are deterministic tests, not an adopter run.
- **The run confirms no table row.** The replay exercised an upgrade. The table's rows
  each name their own live records, under the matrix's *Live promotion boundary*. These
  commits changed the file after `e698ec4`: #781 (`902dbf6`), #887 (`e559b5f`), #902
  (`65e9d2d`), #904 (`0c7669a`), #906 (`c6b663d`) and #911 (`0298191`)
  (`git log e698ec4..7040d28 -- docs/agentic-dev-kit/runtime-parity.md`).

## Verdict at `7040d28` on 2026-10-02

| Half | Enforced by deterministic checks | Confirmed by the Phase 5 adopter run |
|---|---|---|
| `workflow_contract` | yes | yes |
| `adoption` | yes, through the negative control for the last surface of a runtime directory | not applicable: it postdates the run and is template-route only; the fresh-install fixtures confirm it |
| Table and sub-table | no: one row's three phrases only | no |

**The exit as written holds for the declaration and not for the table.** Declaring it
now would narrow "the parity matrix" to the declaration. That is an amendment, and the
rule the Phase 5 audit worked under applies: "Never present reduced coverage as
completion of the original full scope."

## Decision

On 2026-10-02 the operator chose to hold the exit rather than declare it under an
amendment, and to add a deterministic check over the table as Phase 6 item 10,
[#919](https://github.com/topij/agentic-dev-kit/issues/919). #919 owns the exit from
here. That means re-running this check against the exit as written and, if it holds,
archiving the parity plan behind the matrix, which is #880's step 4. Until then the
parity plan stays as it is.
