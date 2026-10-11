# Skills and instruction files against current runtime guidance — assessment

Assessed at `0b8166b8` on 2026-10-11, against:

- Anthropic, *Skill authoring best practices* —
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- Claude Code, *How Claude remembers your project* — <https://code.claude.com/docs/en/memory>
- Claude Code, *Skills* — <https://code.claude.com/docs/en/skills>
- Codex, *AGENTS.md* — <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
- Codex, *Build skills* — <https://learn.chatgpt.com/docs/build-skills>

Clients on the assessing machine: Claude Code `2.1.296`, codex-cli `0.153.4`
(`claude --version`, `codex --version`, 2026-10-11).

## What the kit already does right

- **One runtime-neutral source, thin bindings.** `docs/agentic-dev-kit/workflows/` holds
  behaviour; `.claude/commands/` and `.agents/skills/` only point at it. Both vendors now
  converge on the same `SKILL.md` shape, so this design ages well.
- **`CLAUDE.md` imports `AGENTS.md`.** Claude Code's memory doc names this the way to
  share one file with other tools, and it is the only pattern that also works in the
  sessions where native `AGENTS.md` reading is unavailable.
- **Descriptions** say what the workflow does and when to use it, sit far under the
  Anthropic 1,024-character and Claude Code 1,536-character caps, and the whole set is
  small against Codex's skill-list budget (2% of context, or 8,000 characters).
- **Deterministic work lives in engines** (`pr_watch.py`, `launch_lane.py`, triage
  draft/finalize), which is the "prefer scripts for deterministic operations" advice.
- **`.claude/rules/safety-critical-changes.md` uses `paths:`**, the documented way to keep
  narrow doctrine out of every session's context.

## Gaps, highest impact first

### 1. The skills are thin, but what they load is not

Each `SKILL.md` is a pointer whose one instruction is "read the workflow completely".
The guidance's 500-line ceiling and progressive disclosure are therefore met on paper and
missed in effect: the whole workflow is loaded every time.

Sizes (`wc -lc docs/agentic-dev-kit/workflows/*.md` at `0b8166b8`, 2026-10-11):

| Workflow | Lines | Bytes |
|---|---|---|
| `triage-friction-log.md` | 1423 | 116604 |
| `upgrade.md` | 978 | 63135 |
| `pr-watch.md` | 789 | 50702 |
| `wrap-up.md` | 617 | 46143 |
| `post-merge-systemize.md` | 589 | 37884 |
| `adopt.md` | 580 | 44815 |
| `session-start.md` | 509 | 35163 |
| `parallel.md` | 454 | 33182 |
| `parallel-headless.md` | 407 | 28956 |

Every workflow except `parallel.md` and `parallel-headless.md` is over the 500-line
ceiling. Consequences:

- **"Read completely" cannot be done in one read on Claude Code.** A Claude Code `Read` of
  `triage-friction-log.md` at `0b8166b8` on 2026-10-11 returned lines 1–787 of 1424 and
  reported the file as 38415 tokens against a 25000-token cap. The guidance warns that
  partial reads of long references are exactly where content gets missed.
- **Compaction drops the workflow.** Claude Code re-attaches the invoked skill's body after
  summarisation (first 5,000 tokens each, 25,000 combined). Here that body is the pointer;
  the workflow text arrived as a tool result and is summarised away.
- **No table of contents** in any workflow, against the guidance for references over
  100 lines.
- **Second-level references exist**: `pr-watch.md` and `wrap-up.md` point into
  `fallback-review-panel.md`; `parallel.md` into `parallel-headless.md`, which points on
  into `runtime-parity.md`. The guidance asks for one level from `SKILL.md`.
- **Register.** `triage-friction-log.md` is a state machine written as prose: input
  matrices, phase schemas, digest bindings. The guidance's "narrow bridge" case says to
  put that in a script and tell the model to run it. The engines already enforce much of
  it; the doc restates the enforcement for the model to re-derive.

**Recommendation.** Restructure each workflow as a real skill directory: a `SKILL.md` under
500 lines holding the steps, decision points and stop conditions, plus `reference/*.md`
files linked directly from it for schemas, recovery cutpoints and rationale. Move
normative state-machine detail behind the engines and keep only "run X, branch on its
status" in the skill. Start with `triage-friction-log`, `upgrade` and `pr-watch`.

### 2. Claude bindings use `.claude/commands/`, which Claude Code has folded into skills

Commands still work, but the skills doc says to prefer skills for new work, and commands
cannot carry supporting files, `paths`, or invocation control. Moving to
`.claude/skills/<name>/SKILL.md` unlocks:

- **`disable-model-invocation: true`** for workflows with external writes or that the
  operator should start deliberately: `triage-friction-log`, `upgrade`, `adopt`,
  `wrap-up`. Codex's equivalent is `policy.allow_implicit_invocation: false` in
  `agents/openai.yaml`; no binding sets it today.
- **`${CLAUDE_SKILL_DIR}` and dynamic context** (`` !`cmd` ``), e.g. injecting
  `pr_watch.py` status into `pr-watch` instead of instructing the model to fetch it.
- **One directory shape per runtime.** `.claude/skills/<name>/` and
  `.agents/skills/<name>/` can then hold the same `SKILL.md`, which shrinks the parity
  surface `runtime-parity.md` declares. Whether one can symlink to the other needs a live
  probe: the Claude Code docs do not say whether it reads `.agents/skills`. If a future
  client does, the kit would show every workflow twice.

Avoid Claude-only frontmatter in a `SKILL.md` that Codex also reads unless Codex is shown
to ignore unknown keys; the Claude doc notes that non-Claude-Code surfaces hard-error on
keys such as `argument-hint`.

### 3. `AGENTS.md` carries history in always-loaded context

`AGENTS.md` is 334 lines, 22714 bytes (`wc -lc AGENTS.md` at `0b8166b8`, 2026-10-11).
Claude Code's target is under 200 lines per file, and it notes that imports do not reduce
the cost. Codex stops adding project docs once the combined size reaches
`project_doc_max_bytes`, 32 KiB by default, so an adopter whose own `AGENTS.md` grows
beside the kit's sections nears a silent cutoff.

Most of the length is the *Numbers in prose* and *Prose that goes false* sections, which
carry the incidents that justify them: shas, dates, PR numbers. The Anthropic guidance
calls this time-sensitive content and asks for it in an "old patterns" section, not the
main body. Every session pays for the history, and the rule is harder to find inside it.

**Recommendation.** Keep each rule as a few imperative lines in `AGENTS.md`. Move the
incident record and rationale to a linked doc, for example
`docs/agentic-dev-kit/record-prose.md`. Block-level HTML comments are stripped by Claude
Code but not documented as stripped by Codex, so they are not a parity-safe home for it.

### 4. An unconditional claim ships to adopters

`docs/templates/CLAUDE.md.tmpl` says "Claude Code reads `CLAUDE.md` and **not**
`AGENTS.md`". Since Claude Code `2.1.277` it reads `AGENTS.md` when no `CLAUDE.md`
exists. Where a `CLAUDE.md` exists, which is always the case once the kit installs one,
Claude Code by default reads it *instead of* `AGENTS.md`. So the import is required, not
merely preferable, and the template's conclusion holds. Only the unconditional wording
is wrong. *Correction after the first draft of this record, which called the claim
stale outright.* Reword it, and its copies in `docs/getting-started.md`, `README.md` and
an `init.sh` comment, to the conditional form.

### 5. No skill evaluations or cross-model testing

The guidance's checklist asks for at least three evaluations per skill and testing on
every model the skill will run on. The kit tests engines and parity structure
(`scripts/tests/test_runtime_parity_matrix.py`) but nothing checks that a description
triggers, or that a smaller model completes a workflow. The lens agents are pinned to
`sonnet`, so they are the obvious first case. Claude Code now ships `claude plugin eval`
and `/doctor prompt-audit`; the latter audits `CLAUDE.md`, `AGENTS.md`, rules, skills,
commands and subagents for stale or conflicting instructions and could run in CI or at
`wrap-up`.

### 6. Minor

- **Description voice.** The guidance asks for third person ("Drives a pull request…");
  the descriptions are imperative ("Drive a pull request…"). Low risk, cheap fix.
- **`triage-friction-log` has no "Use when…" clause**, unlike the others.
- **Names** are consistent noun/action forms; gerund names are only a suggestion. No
  change needed.

## Suggested order

1. Fix the stale template claim. One line, adopter-visible.
2. Add invocation control to the side-effecting workflows on both runtimes.
3. Split `AGENTS.md` into rules plus a linked rationale doc.
4. Restructure the three largest workflows into `SKILL.md` plus one-level references,
   moving Claude bindings to `.claude/skills/` in the same pass.
5. Add trigger and completion evals, starting with the lens agents and `pr-watch`.

Of the suggested-order steps above, step 2 owes a changelog fragment. It changes gate
semantics, because three workflows stop loading on the model's own judgement. Steps 1 and
3 change wording only and owe none. Step 4 owes one only if it changes a report shape, a
gate, a config key or an engine CLI, and owes a check against
`docs/agentic-dev-kit/safety-critical-changes.md` if it touches `scripts/pr_watch.py` or
`scripts/launch_lane.py`.
