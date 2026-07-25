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

- **The fallback review pass has no independence when the cockpit authored the PR (severity: H).**
  On #22 CodeRabbit was rate-limited, so `review.fallback_commands` ran — but the agent
  running it was the same one that wrote the diff. It found three real issues, yet
  `safety-critical-changes.md` rule 2 is explicit that this is not a pass: "A single-lens
  'converged' verdict is an incomplete review, not a green light." Rule 3 also went unmet —
  the fallback's own approve was written in the same pass that produced the final commit, so
  nothing reviewed `32f3e4f`. **Proposed fix:** make `review.fallback_commands` a *panel*
  spec rather than an inline command — one fresh-context subagent per lens
  (adversarial/bypass-focused + general-correctness, the two the doctrine says find
  **disjoint** holes), each handed the raw diff with no framing from the author, and a
  distinct receipt source (`fallback:panel`) so the audit trail does not read as a primary
  review. Demonstrated the same day: a cold subagent on #24 found a stale merge-gate comment
  that three self-review passes had walked past. Severity raised from M — this is a
  documented rule being violated, not a soft gap.

- **A safety-critical PR merged without any review of its final design (severity: H).**
  Also #22: CodeRabbit's only completed review was bound to the first commit; the design then
  changed materially (the fail-open rework), and the rate limit never lifted. The receipt
  mechanism records *that a review happened at this head* — satisfied by the fallback — with
  no notion of "the primary reviewer saw an earlier, materially different design."
  **Proposed fix:** invalidate a receipt when the diff changes *shape* rather than only when
  the head moves — e.g. require a fresh receipt when a later push touches a file the recorded
  review never saw. Cheaper interim: have `pr_watch` surface the primary bot's last-reviewed
  SHA next to the current head, so the gap is visible at merge time instead of reconstructible
  only from the PR thread. Related to #23 but distinct: #23 is about detecting the outage,
  this is about what a receipt should mean when the outage outlasts a redesign.

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
