# Codex adopt context field exercise — 2026-09-05

This is an agent-executed field observation through the shared adopt workflow,
ending at its operator handoff. It is not a completed adoption, a fresh-client
skill-discovery test, or the Phase 5 exit.

## Bound inputs

- Kit source: `ab0a6d62308b298478b2f85fc961f14348f35365` at
  `/Users/topi/Coding/agentic-dev-kit`.
- Disposable local fixture: `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`,
  baseline `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2`.
- Runtime: the current Codex session explicitly read the kit's
  `.agents/skills/adopt/SKILL.md` and followed
  `docs/agentic-dev-kit/workflows/adopt.md`. The fixture had no remote.
- [Retained fixture inputs](codex-adopt-field-evidence_2026-09-05/fixture-inputs.json)
  include a synthetic local override; no production notification identity was used.

## Executed and observed

The cockpit created the synthetic baseline, then bound `REPO` to the fixture and
`KIT` to the existing kit checkout for Adopt Step 0. It asserted the canonical
working directory before each write sequence and used absolute destination paths.
Step 1 loaded the fixture through the kit's `kitconfig.load_config()` and inspected
its paths and first lines directly; it did not substitute the kit's own config.
The [inspection output](codex-adopt-field-evidence_2026-09-05/inspection.json)
retains the argv, source and fixture revisions, output, and original input hashes.

The merged read selected `ROADMAP.md`, `notes/history.md`, `notes/friction.md`,
`notes/friction-archive.md`, and `scripts/devkit`. It returned the synthetic local
`notify.user_key` value rather than the tracked value. First-line inspection
classified `AGENTS.md` as `MARKED`; `CLAUDE.md`, `ROADMAP.md`, and
`notes/history.md` as `IN_USE`; and the friction paths as `ABSENT`.
The existing Codex `wrap-up` skill was a preservation collision. No repo-wide
lint or external review service was configured in this synthetic fixture.

Step 2 presented the exact staging plan in the current session. The operator
replied `approved` on 2026-09-05. That approval covered staging on
`chore/adopt-agentic-dev-kit`, keeping the existing paths and values, installing
missing pieces, and stopping before `init.sh` or a fixture PR.

Step 3 copied the non-repo-only manifest paths, missing runtime adapters and lens
definitions, and reference files. Script destinations were remapped under
`scripts/devkit/`. The existing Codex `wrap-up` was retained. The config gained
missing defaults while preserving its prior values; its serialization did not
retain the reference config's comments. No claim is made that this staged config
retains runtime-status annotations. The marked `AGENTS.md` was preserved on the
approved plan rather than merged with the safety sections.
The [copy ledger](codex-adopt-field-evidence_2026-09-05/copy-ledger.json),
[staged config](codex-adopt-field-evidence_2026-09-05/staged-config.yaml), and
[destination read-back](codex-adopt-field-evidence_2026-09-05/staging-readback.json)
retain what actually landed. Copied bytes were compared with source bytes at the
destination; pre-existing inputs other than the config retained their hashes.

Step 3b executed the installed `kit_doctor.py --record-install --from-kit` against
the bound kit. Its [terminal output](codex-adopt-field-evidence_2026-09-05/record-install.json)
and [destination baseline](codex-adopt-field-evidence_2026-09-05/install-baseline.json)
retain the result. The baseline's `kit_commit` was checked against the source SHA.
This is a baseline observation, not Step 4 verification of a completed adoption.

## Refused, held, and untested

- The first staging `uv` invocation was refused access to its host cache after
  branch creation and before copies. The
  [refusal record](codex-adopt-field-evidence_2026-09-05/permission-refusal.txt)
  distinguishes that failure from the approved retry that completed staging.
- Installation waited for the Step 2 reply. This was an agent-observed approval
  boundary, not a mechanically tested approval guard.
- The exercise stopped at the
  [Step 3c operator handoff](codex-adopt-field-evidence_2026-09-05/operator-handoff.md).
  `init.sh --no-clobber` was copied and handed off, never run. Narrative seeding,
  hook installation, Step 4 portability/doctor checks, and Steps 5–6 remain untested.
- No fixture PR, merge, tracker write, or notification send was attempted. No
  fresh-client adapter discovery or adversarial prompt-resistance claim is made.
- The cs-toolkit replay, final Phase 5 exit, other remaining field exercises, and
  tracker dispositions were outside this slice. TRI-03/TRI-04/TRI-05 were untouched.

## Kit verification

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`ab0a6d62308b298478b2f85fc961f14348f35365` on 2026-09-05 printed
`1 failed, 2436 passed, 1 skipped in 361.84s (0:06:01)`.
The [stamp](codex-adopt-field-evidence_2026-09-05/verification-stamp.json) records
an extended timeout and the preflight check for concurrent suite/watch processes;
the tree had no pending changes, and no `pr_watch` invocation ran alongside it.
The [retained output](codex-adopt-field-evidence_2026-09-05/make-test.log) identifies
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`:
its exit assertion passed, but the hook emitted output. This is the #393-shaped
failure named by the preceding handoff stamp at
`bb27a58ae640a7541d34bc984333565e4a435166` on 2026-09-05.
The run preceded this record/plan/handoff patch and does not test its prose claims.
