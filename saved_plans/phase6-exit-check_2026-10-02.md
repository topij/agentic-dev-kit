# Phase 6 exit check — 2026-10-02

[#880](https://github.com/topij/agentic-dev-kit/issues/880) asks for the Phase 6 exit to
be checked as the [parity plan](codex-parity-plan_2026-08-23.md) states it, with the
command and revision behind each of its parts. The exit, from the plan's *Phase 6*
section:

> Done when the parity matrix is enforced by deterministic checks and confirmed by the
> Phase 5 adopter run.

Every observation below was taken at `7040d289942a80b0a87f6447048d29e3f37964d5`
(`main`) on 2026-10-02, unless it names another revision. **This record makes no
declaration of its own.** Declaring the exit is the operator's call, as it was for Phase 5;
the record documents the operator's decision where one was taken.

## What "the parity matrix" covers

Phase 1 of the plan defines the matrix as "a maintained runtime-capability matrix
covering workflows, persistent instructions, safety activation, hooks, permissions,
model controls, subagents, external integrations, adoption, upgrade, and drift
detection". It also says to "Derive structural parity checks from that declaration
instead of restating the expected adapter set in tests."
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

Some rows describe behaviour whose repository side has tests of its own. For example,
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

## Re-run after item 10 — 2026-10-02

[#919](https://github.com/topij/agentic-dev-kit/issues/919), Phase 6 item 10, added a
deterministic check over the table. This section re-checks the exit as written against
it. The sections above stand as they were taken at `7040d28`.

### The table: now enforced

`runtime-parity.md`'s front matter now declares the *Capability matrix* rows with their
statuses (`capability_matrix`) and the records the per-runtime sub-table links
(`lane_isolation_records`). `scripts/tests/test_runtime_parity_matrix.py` holds each
table to its declaration: the rows, their order, each status cell's opening term
against a vocabulary the file states, and the sub-table's runtime and record per row.
It also resolves the file's relative links and in-file anchors, in the Markdown and HTML
forms it parses. The adoption
fixtures now scan a fixed `.claude/`, `.agents/`, `.codex/` set, so the positive check
names the cause of the `adoption.surfaces.codex` mutation above.

Mutations, each in its own `git clone --no-hardlinks` of the branch, detached at
`53980ae889d9abbbb960c42944d428712a6e9469`, applied by a script that asserted one
match, read back with `git diff --stat`, then run with
`env -u FORCE_COLOR make mutation-test` on 2026-10-02:

| Mutation | Result | Matrix test |
|---|---|---|
| Delete everything from `## Capability matrix` up to `## Live promotion boundary` | `16 failed, 3968 passed, 1 skipped, 1 deselected in 717.67s (0:11:57)` | failed |
| Delete the *Runtime memory tripwire* row | `11 failed, 3973 passed, 1 skipped, 1 deselected in 673.68s (0:11:13)` | failed |
| Rename the sub-table's heading, breaking `#headless-lane-isolation-per-runtime` | `7 failed, 3977 passed, 1 skipped, 1 deselected in 691.79s (0:11:31)` | failed |
| Change the *Adapter upgrade* row's status cell from `aligned:` to `gap:` | `8 failed, 3976 passed, 1 skipped, 1 deselected in 716.17s (0:11:56)` | failed |

How to read the failure counts: `env -u FORCE_COLOR make test` at the same revision
on 2026-10-02 printed `2 failed, 3983 passed, 1 skipped in 726.14s (0:12:06)`. Those two
were `test_kit_doctor.py::test_repo_only_paths_are_hashed_but_not_offered_to_an_adopter`
and `test_portability.py::test_runtime_parity_contract_rejects_a_gap_with_no_real_surface`,
both from #919's own change and both repaired in `605de00`, which touches neither the
parity doc nor the matrix test. Each mutation's kill is
`test_runtime_parity_matrix.py::test_the_capability_matrix_matches_its_declaration`,
which passed in that baseline. The other failures in each count are the matrix test's
own negative controls, whose text anchors the mutation removed.

### Part 2 after item 10

Item 10 adds no adopter run, so the cs-toolkit replay still confirms `workflow_contract`
and was compared against no table row. One sentence in Part 2 above overstates, and is
corrected here rather than in place: not every table row names its own live record.
Some cite a stamped record, in the cell or through the *Lifecycle validation boundary*
and *Live promotion boundary* sections. This record checked no other row against any
run. The check above holds every row to the declaration; whether a row's claim is true
is left unaudited, and #919 stays open to carry that audit.

### Verdict after item 10

| Half | Enforced by deterministic checks | Confirmed by the Phase 5 adopter run |
|---|---|---|
| `workflow_contract` | yes | yes |
| `adoption` | yes; the positive check now names the cause | not applicable, as above |
| Table and sub-table | yes, at `53980ae` | no |

**The exit as written still does not hold for the table**, on its second clause alone.

### Decision

On 2026-10-02 the operator chose to declare the exit under a recorded amendment rather
than hold it again. #923's review panel found the amendment as first worded overstated
what confirms the table's rows. On 2026-10-03 the operator chose to declare under the
narrowed amendment below rather than hold.

**The operator declared the Phase 6 exit, under this amendment:** the parity matrix is
enforced by deterministic checks. Its declaration is confirmed by the Phase 5 adopter
run. Its table's rows that cite a stamped live record rest on that record. The others
were checked against no run here: the check holds them to the declaration, and their
truth is left unaudited, as *Part 2 after item 10* sets out. The parity plan is archived
behind the matrix in the same change, which is #880's step 4.
