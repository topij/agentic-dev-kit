# Wrap up

End-of-session wrap-up. Update the living handoff and commit.

## Resolve configuration

Read `config/dev-model.yaml` first. In this workflow, `<handoff>`,
`<handoff-history>`, and `<friction-log>` mean the corresponding values under
`paths`; `<engine-dir>` means `paths.engines`; `<handoff-budget>` means the
`budget` field of `<handoff>`'s entry under `doc_budgets`. A workflow invocation
means the current agent's native adapter (`/name` in Claude or `$name` in Codex).

## Steps

1. **Read the current handoff** — `<handoff>`.

1. **Review what changed this session** — check `git diff` and `git log` since the
   handoff's "Last updated" date

1. **Update `<handoff>`**:

   - Move completed work from "In Progress" to "Done" (with a one-line summary of
     what shipped)
   - Add any new items discovered during the session to the appropriate section
   - Update sprint status if a sprint boundary was crossed
   - Remove resolved housekeeping items
   - Update the "Last updated" date to today
   - Keep it concise — the handoff is a handoff document, not a changelog

1. **Capture friction** — if this session surfaced any bug, friction, or idea specific
   to a workflow (a skill, a cron/CI job, a pipeline), append a short entry to
   `<friction-log>` under a dated `## YYYY-MM-DD`
   heading: the observed issue, a severity (**H**/**M**/**L**), and a proposed fix.
   This is the documented session-end practice — it captures learnings while fresh;
   they later graduate to your tracker via the `triage-friction-log` workflow. Add to the inbox
   only — don't graduate or sweep here. Skip if nothing workflow-specific came up.

1. **Suggest a next-session starter** — if the session ends with a *clear* follow-up,
   hand the next session a running start:

   - **One obvious next thing** → add it as a final `▶ Next: <starter>` line at the end
     of the latest session block in `<handoff>`, and print the same starter in
     the chat. Make it concrete and copy-pasteable: a native workflow invocation or a
     one-line task prompt that names the file / ticket / PR (e.g. `▶ Next: pr-watch
     1131 — fix review findings then self-merge`). The `▶ Next:` line is an allowed
     addition (like the archive sweep), not a structure change to ask about.
   - **Diffuse / several threads** → don't invent a false single thread; tell the
     operator to open next session with `session-start` (it re-reads handoff +
     inbox + tracker + live repo/CI state and re-proposes what to do).
   - **No clear follow-up** → skip this step.

1. **Update any project-status doc** (e.g. a dashboard snapshot) if any metrics
   changed this session — adapt this step to whatever presentation artifact your
   project keeps; skip if you don't have one.

1. **Keep the handoff docs lean.** After adding this session's block, run
   `uv run <engine-dir>/check_doc_budget.py`. If it warns that `<handoff>` is over
   budget, run `uv run <engine-dir>/archive_plan_sessions.py --target-lines
   <handoff-budget>` — it sweeps oldest-first, one block at a time, until
   `<handoff>` is at or under that line budget, moves the swept blocks into
   `<handoff-history>`, and trims the megaline. **Do not use plain `--keep`
   here** (or run the script with no flags, which defaults to `--keep 6`):
   `check_doc_budget.py` measures **lines** while `--keep` counts **blocks**, so
   the default can report "nothing to move" while `<handoff>` stays over budget
   ([#74](https://github.com/topij/agentic-dev-kit/issues/74)). **Read the exit
   code, not merely "non-zero":** exit **3** means the target is unreachable —
   either it would require sweeping the last remaining block, or there are no
   session blocks to sweep at all. Nothing was written, so report `<handoff>`'s
   *unchanged* length against the budget and do not treat it as done. Exit **2**
   is something else entirely (unreadable or non-UTF-8 file, missing file,
   unparseable handoff, a history doc with no session-log section, a failed
   write); read the message and fix that instead of reporting an exhausted sweep.
   The script's own `--help` carries the authoritative list. **On a failed write,
   check BOTH documents before you continue** —
   `git diff --stat <handoff> <handoff-history>` — and do not trust the "no
   changes applied" wording: the write truncates before it fails, so a full disk
   or a quota can leave a document empty or partial while that message claims
   otherwise ([#164](https://github.com/topij/agentic-dev-kit/issues/164)).
   **Checking only `<handoff>` gives a false all-clear**, because the history doc
   is the likelier casualty — it *grows* while the handoff shrinks — and when the
   history write fails the handoff is rolled back, so it reads clean while the
   append-only archive has been gutted. If either is damaged, restore it with
   `git checkout -- <path>` and stop. Stage
   **both** files (`<handoff>` + `<handoff-history>`) into this commit. If
   `<friction-log>` is over budget, don't sweep it inline — note it and
   recommend the `triage-friction-log` workflow (graduating the inbox needs
   tracker writes + operator approval). This is what stops the handoff docs
   from ballooning between archive sweeps.

1. **Commit + PR the handoff update — never commit to your protected branch
   directly.** Commit as `chore: update handoff — [one-line summary of session work]`
   (stage `<friction-log>` too if you added an inbox entry this session, and
   `<handoff-history>` if the archive sweep ran). If you're already on the
   session's feature branch, this is just another commit on that branch's PR. If
   you're on the protected branch (e.g. a planning-only session), branch first
   (`chore/update-handoff-<date>`) before committing, then push and open a PR. Either
   way, once there's nothing left to push, **mark the PR ready** so it gets reviewed,
   and run the watch-and-fix loop (`pr-watch`) to merge — per your project's
   branching convention.

## Rules

- Do NOT add session-specific detail (decisions, debugging steps, conversation
  context) — that belongs in session-scoped scratch notes or memory, not the living
  handoff
- Do NOT change the handoff's structure or add new sections without asking — but the
  `archive_plan_sessions.py` sweep (moving old session blocks to `<handoff-history>`)
  and a single `▶ Next:` starter line at the end of the latest session block are both
  documented additions, not structure changes, so do them without asking
- If a backlog item was promoted to a sprint epic, move it (don't duplicate)
- If the session produced no handoff-relevant changes, say so and skip the commit
