# First real headless lane on this repository — live validation

Phase 4 item 5 of the Codex–Claude parity plan. The design matrix written before the
launch is
[`first-real-headless-lane-design_2026-08-28.md`](first-real-headless-lane-design_2026-08-28.md);
its rows and its terminal-outcome table are what this record answers.

Every earlier lane ran on a synthetic repository. This one ran on `agentic-dev-kit`
itself, against `#602`. The launcher and every shipped configuration value were
unchanged for the run.

**Outcome: the lane terminalized `failed`, at a real capability boundary, with the
denial record proving it.** That is a result, not an aborted run — the boundary it
found is the finding, and the receipt is the evidence.

## What ran

Issued from the repository root:

```
scripts/dev_session.sh new pms-bindings --headless --runtime claude --merge-class operator
python3 scripts/launch_lane.py \
  --descriptor /Users/topi/Coding/dev-model-sessions/pms-bindings/launch-descriptor.json \
  --prompt-file <task prompt>
```

The launcher exited `70` and wrote `status: failed`.

`scripts/launch_lane.py`, `scripts/dev_session.sh`, `scripts/pr_watch.py`,
`config/dev-model.yaml`, and `config/claude-lane-settings.json` were byte-identical to
`origin/main` at `0934b6de0426a3ee41e661112d42743f123ddc3d` for the run;
`git diff --stat origin/main --` over those five paths printed nothing, captured in
`first-real-headless-lane-evidence_2026-08-28/00-pre-launch.txt`.

### The one deviation, and why it is not a configuration change

This host's Claude Code is a user-local install at `/Users/topi/.local/bin/claude`,
which `launch_lane.py`'s trusted executable path does not contain. The shipped
`parallel.claude_headless_command: [claude, -p]` therefore could not resolve, and
neither the tracked config (also what `init.sh` seeds for adopters) nor the gitignored
overlay (`kitconfig.OVERLAYABLE_PREFIXES` admits `notify.user_key` alone) was an
acceptable place to name the absolute binary.

The route taken, on the operator's decision, was a host symlink
`/opt/homebrew/bin/claude -> /Users/topi/.local/bin/claude`, placing the runtime on the
trusted path rather than teaching the kit a machine-specific path. The receipt records
what the launcher resolved: `request.configured_command:
["/opt/homebrew/bin/claude", "-p"]`. The underlying gap is filed, not fixed here.

## Client

`/opt/homebrew/bin/claude --version` printed `2.1.250 (Claude Code)` on 2026-08-28.
This is **not** the client the earlier records were stamped against (2.1.247), so where
this record and those disagree, they are observations of different clients.

## Dimensions — what each row returned

Row numbers are the design matrix's. Nothing below is read from the lane's own prose;
the lane's report is quoted separately, and where it makes a claim, the claim is
labelled as its claim.

| # | Dimension | Observed | Settled by |
|---|---|---|---|
| 1 | Worktree | `observed.git_top`, `observed.worktree`, and `observed.pwd_environment` all `/Users/topi/Coding/dev-model-sessions/pms-bindings/wt` | `01-receipt-observed.json`, child-bound before `exec`; independently, the runtime wrote its transcript under `~/.claude/projects/-Users-topi-Coding-dev-model-sessions-pms-bindings-wt/`, which encodes the same cwd |
| 2 | Branch | `dev/pms-bindings`, equal to `observed.persisted_branch` | `01-receipt-observed.json`; `git -C <wt> log` shows the lane's commit on it |
| 3 | Base | `main` / `0934b6de0426a3ee41e661112d42743f123ddc3d` | `02-descriptor.json`, equal to the `origin/main` sha this session fetched and verified at start (`00-pre-launch.txt`) |
| 4 | State root | `observed.state_root` = `observed.marker_state_root` = `env.DEVKIT_STATE_ROOT` = `…/pms-bindings/state`; `DEVKIT_REFUSE_UNSANDBOXED_STATE: "1"`; `repository_overrides_present: []` | `01-receipt-observed.json`, plus `06-worktree-state-root-marker.txt` read from the worktree; independently, `git -C <cockpit> status --short -- state/` printed nothing after the run |
| 5 | Approval policy and profile digest | `declared: dont-ask`; argv `--permission-mode dontAsk`; profile `config/claude-lane-settings.json` at `4ace4389fa06db1ad6336ff68d63e18c5cab97ccc2b2000d4c061d4616d6df9f`; `observed.argv` carries `--setting-sources ""` and `--settings <profile>` | `01-receipt-observed.json`; the digest recomputed independently by the cockpit with `shasum -a 256` against the tracked file |
| 6 | Lane model and effort | `claude-opus-5` at effort `high` | The runtime's own transcript, `~/.claude/projects/-Users-topi-Coding-dev-model-sessions-pms-bindings-wt/0e4c706a-2e67-4278-bcf4-ec9b35dcb86a.jsonl`, `message.model` and top-level `effort` on its `assistant` entries. The `session_id` came from the final-message object, not from the lane. `modelUsage` named `claude-haiku-4-5-20251001` and `claude-opus-5[1m]` and is not the observer, as `capability-tier-calibration-live-validation_2026-08-27.md` established |
| 7 | `permission_denials` | A **non-empty list** — the enumeration is below | `07-receipt-terminal.json`, `terminal.permission_denials`, extracted by the wrapper from the runtime's own result object |
| 8 | Final-text transport | `json-stdout`; **exactly one** JSON value on stdout; `final_message_sha256: 170e8375…`; `final_text_sha256: null` | `07-receipt-terminal.json`; the final-message bytes rehashed independently to the same digest, and re-parsed to count the JSON values |

Row 6 is the design's "no expected value, only a value to record" row: the wrapper
carries no model or effort control, so this is what the product default resolved to
under the trust route on this client, on this date.

Row 8's `final_text_sha256: null` beside a present `final_message_sha256` is the failed
path behaving as written: the wrapper terminalizes without extracting final text. The
bytes are retained and the text is readable from them.

The multi-JSON-value shape the friction log recorded on 2026-08-27 at 2.1.247 did not
occur in this run at 2.1.250. One run is not evidence it is fixed.

## The terminal outcome, against the table fixed in advance

`failed`, denials non-empty — the fourth row of the design's terminal table, and the
one whose instruction was: read the denied calls, decide whether the profile is too
narrow for real work here or the prompt asked for something out of scope, and **do not
widen the profile to make the run pass.** The profile was not widened.

`terminal.error` reads `runtime reported permission denials under declared policy
dont-ask`.

## What was denied

The enumeration, from `terminal.permission_denials`:

1. `Bash` — `for f in .claude/commands/session-start.md …; do echo "===== $f ====="; cat "$f"; done`
2. `Bash` — `grep -in 'CLAUDE.md\|AGENTS.md\|rules/' docs/…/post-merge-systemize.md; echo "--- exit $? ---"; echo "…"; grep -in 'confirm' docs/…/post-merge-systemize.md`
3. `Edit` — `<wt>/.claude/commands/post-merge-systemize.md`
4. `Write` — `<wt>/.claude/commands/post-merge-systemize.md`
5. `Edit` — `<wt>/.claude/commands/post-merge-systemize.md`

Two mechanisms, not one.

### The `.claude/` boundary

Entries 3–5 are the structural finding: **a headless Claude lane cannot write under
`.claude/`, and the profile's `Edit(**)` does not lift it.**

This is not an allow-list gap, and three independent observations rule that reading
out:

- The same lane's `Edit` of `.agents/skills/post-merge-systemize/SKILL.md` **succeeded**
  and is in its commit. So `Edit(**)` does match a dot-directory; the glob is not the
  mechanism.
- The same lane's `Edit` of `scripts/tests/test_portability.py` succeeded.
- Two separate cockpit probes, in unrelated throwaway Git repositories under the
  **same** trust route (`--setting-sources "" --permission-mode dontAsk --settings
  <the same profile>`), which share nothing with this repository but the profile.

The second probe is the one that establishes the directory's scope, because the run
above and the first probe both happened to target `.claude/commands/`. It asked for the
same one-word `Edit` — the tool `Edit(**)` grants — in each of these paths, in one
session, instructed to attempt every one regardless of earlier refusals. Its denial list
and the files' own bytes afterwards agree:

| path | outcome |
|---|---|
| `.claude/commands/t.md` | `Edit` denied, file unchanged |
| `.claude/rules/t.md` | `Edit` denied, file unchanged |
| `.claude/agents/t.md` | `Edit` denied, file unchanged |
| `.claude/t.md` | `Edit` denied, file unchanged |
| `.claude/settings.json` | `Edit` denied, file unchanged |
| `.agents/skills/demo/SKILL.md` | edited |
| `docs/t.md` | edited |
| `.github/workflows/t.yml` | edited |

So the refusal covers `.claude/` as a directory — its `rules/` and `agents/`
subdirectories included, which the lane's own run never reached — and it is not a
property of dot-directories, since `.agents/` and `.github/workflows/` were both
written in that same session. It reproduces across two file-editing tools (`Edit` here,
`Write` in the first probe) and three repositories.

`09-dotclaude-scope-probe.json` carries that probe's result object.

**Why this matters beyond `#602`.** The kit's runtime-parity work lives half in
`.claude/commands/`, `.claude/rules/`, and `.claude/agents/`. A Claude lane that cannot
write there cannot complete a parity change on its own, while the Codex writing-lane
record's lane edited its own runtime's adapter directory without obstruction. That is
an asymmetry between the runtimes that no earlier record could have surfaced, because
every earlier lane ran on a synthetic repository with no adapter directory in it.

### The Bash read-classifier boundary

Entries 1–2 are a second, smaller finding. `parallel-headless.md` records that at
2.1.247 a read-only class (`pwd`, `whoami`, `cat`, `grep`, `find`, bare `git remote -v`)
was accepted with nothing in `permission_denials`, while the profile lists no rule for
any of them. This run shows that acceptance does not extend to every shape those
commands appear in: a `for … do cat … done` loop and a `;`-chained `grep`/`echo`
compound were both denied at 2.1.250, while simple invocations of the same commands
were accepted in the same session.

So the read-only acceptance is a property of the **command shape**, not of the command
name. A lane batching reads into a loop pays a denial. Under the shipped `dont-ask`
policy, where a denial is terminal for the whole lane, that is a live hazard rather
than a round-trip cost.

## What the lane produced

One commit, `fbdaaeb`, on `dev/pms-bindings`. It carries the `.agents/` half of `#602`
and a test pin in `scripts/tests/test_portability.py` written in the shape of
`_assert_bookend_adapter_semantics`. **The lane neither pushed it nor opened a pull
request**, and stopped there, because its own new pin asserts a Claude adapter body that
the denials prevented it from writing — so the pin fails by construction and the PR
could not have been driven green.

What happened to that commit afterwards is the cockpit's doing, not the lane's, and the
distinction is the whole point of this record. On the operator's decision the cockpit
wrote the refused file as `f823c3f`, pushed the branch, and opened `#625`, whose body
states which commit each author wrote and why. So `#625` exists and has CI — and none
of it is evidence about what a lane can do unattended, because a lane did not do it.

The lane's own account is in `08-final-message.json`. Read as testimony: its denial
table matches `terminal.permission_denials` entry for entry, and its `.claude/`
diagnosis is the one the probe above confirms independently. Its inference that
`Edit(**)` covers the `Write` tool agrees with `parallel-headless.md`'s existing
statement that `Edit(**)` is the one rule governing every file-editing tool.

## Evidence, and what a later reader can recompute

Committed beside this record in
`first-real-headless-lane-evidence_2026-08-28/`:

| file | binds |
|---|---|
| `00-pre-launch.txt` | the verified `origin/main` sha, the empty launcher/config diff, the profile digest, the client version |
| `01-receipt-observed.json` | the identity chain, before terminalization overwrote it in place |
| `02-descriptor.json` | digest `5a70c515…`, equal to the receipt's `request.descriptor_sha256` |
| `03-authority-seal.json`, `04-attempt.json` | the rewrite seal and the exclusive attempt record |
| `05-lane-task-prompt.md` | digest `89a3d9ab…`, equal to the receipt's `request.task_sha256` |
| `06-worktree-state-root-marker.txt` | the sticky sandbox marker as the child read it |
| `07-receipt-terminal.json` | the terminal status, error, and denial list |
| `08-final-message.json` | digest `170e8375…`, equal to the receipt's `terminal.final_message_sha256` |
| `09-dotclaude-scope-probe.json` | the scope probe's own result object — its denial list and the `.claude/` enumeration above |

**Recomputable by a later reader:** every digest above, against these committed bytes
and against `config/claude-lane-settings.json` at the sha this record names. The
descriptor and prompt copies were verified equal to the receipt's own bindings at
capture time, which is what makes the copy admissible rather than merely present.

**Not recomputable:** the transcript excerpt in row 6 — the transcript is outside the
repository, operator-owned, and carries conversation content, so only the
`(model, effort)` reading is quoted here. And the session directory
`/Users/topi/Coding/dev-model-sessions/pms-bindings`, which any later
`dev_session.sh rm pms-bindings` removes; that is precisely why the artifacts above
were copied in before anything swept it.

This is `#621`'s contract met in the one way available without the bundle format that
issue proposes: the bytes were copied out **before** any cleanup boundary, and each is
bound to a digest the receipt itself carries. `#621` stays open — this record does not
implement the general mechanism, it just does not fall into the trap.

## What did not happen

- **The lane opened no pull request**, so there was no lane-driven CI and no lane-driven
  `dev_session.sh pr-watch <scope>` receipt. The design's rows for those are unanswered
  and nothing here promotes them. `#625` is not an answer to them: the cockpit pushed
  that branch and drove it, which is a different claim about a different actor.
- **No local suite run by the lane.** The profile grants neither `make` nor a bare
  `uv run pytest`, so a lane on this repository cannot run `make test` before pushing.
  The lane stated this rather than claiming a verification.
- **The profile was not widened**, by the lane or by the cockpit.
