# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **This repo's tracker is GitHub Issues on itself**, so most of this session's friction was
> filed directly as issues rather than parked here — which is the routing Principle #2
> prescribes, not a neglected inbox. Entries below are the ones that are *not* yet
> issue-shaped.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-07-25 — inbox

- **The `cp -r` quickstart can't distinguish kit-owned from adopter-owned files (severity: M).**
  Any file the kit tracks lands in an adopter's repo, which is why this repo's own narrative
  docs had to be renamed `kit-*.md` rather than simply filled in. `kit-manifest.json` now
  encodes the ownership boundary (`adopter_owned`), so a manifest-aware installer could copy
  correctly and the rename would become unnecessary. Filed as issue #18.

- **`--record-review` accepts a receipt while the primary bot is still queued (severity: M).**
  Recorded a fallback receipt on #16 when CodeRabbit's check read `PENDING — Review queued`;
  its four valid findings landed after the merge. The doctrine distinguishes *unavailable*
  from *slow*, but nothing mechanically does. Candidate: treat a configured bot's own
  `PENDING` check as a merge blocker while no receipt exists — but that inverts the
  informational-check exclusion in the one case where the exclusion is load-bearing (it is
  what stops the loop wedging on a bot that never reports), so it needs care. Filed as #19.

- **A lane's local gate fails for reasons unrelated to its diff (severity: H).**
  All three lanes this session hit the same two `state_paths` test failures, caused purely by
  running from inside a marker-carrying worktree. A gate that goes red for environmental
  reasons teaches agents to ignore a red gate. Already filed as issue #10 — raising severity
  here because three independent occurrences in one session makes it a pattern, not an
  incident.
