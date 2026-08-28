# First real headless lane — launch design matrix

Phase 4 item 5 of the Codex–Claude parity plan. Written **before** the launch, so the
observers are fixed before there is an outcome to rationalise. Every earlier lane ran
on a synthetic repository; this one runs on `agentic-dev-kit` itself, performing
`#602`'s scoped change.

The slice itself has no tracker item. `#602` is the task the lane performs, not the
slice.

## What is being tested

Not "does `claude -p` work" — `#611`, `#614`, and `#623` settled that on fixtures.
This tests whether the **descriptor-to-receipt chain binds a lane doing real work on
the repository that owns the launcher**, where the worktree is a linked worktree of
this tree, the state root is a real sandbox beside a real `state/`, and the pull
request lands on the real forge.

## Launch route deviation, recorded before the run

`config/dev-model.yaml` ships `parallel.claude_headless_command: [claude, -p]`.
`launch_lane.py` resolves a bare executable name only against `SAFE_EXECUTABLE_PATH`
(`/bin:/usr/bin:/opt/homebrew/bin:/usr/local/bin:/opt/local/bin`), and this host's
Claude Code is a user-local install at `/Users/topi/.local/bin/claude`, which is not on
that path. Every prior Claude lane ran in a fixture repository whose own config named
the absolute binary; this repository's tracked config cannot, because `init.sh` seeds
that same file for adopters, and `config/dev-model.local.yaml` cannot either, because
`kitconfig.OVERLAYABLE_PREFIXES` admits only `notify.user_key`.

**Route taken, on the operator's decision:** a host symlink
`/opt/homebrew/bin/claude -> /Users/topi/.local/bin/claude`, placing the runtime on the
trusted path as that path's design intends. `scripts/launch_lane.py` and
`config/dev-model.yaml` are byte-identical to `origin/main` for this run. The
underlying gap — the shipped Claude launch path cannot launch on a host with a
user-local install, and no overlay reaches `parallel.*` — is a finding of this slice
and is filed, not fixed here.

## Observer discipline

Nothing in the outcome table is read from the lane's own prose. The lane's final text
is testimony about what it believes it did; it is evidence of nothing but that belief.
Each row below names the artifact that settles it independently.

`<S>` is the session directory (`$DEVKIT_SESSIONS_DIR/<scope>`), `<D>` its
`launch-descriptor.json`, `<R>` its `launch-receipt-<descriptor_id>.json`.

## Dimensions

| # | Observation | Expected value | Authoritative observer | Durable evidence | Unavailable / false-success outcome |
|---|---|---|---|---|---|
| 1 | **Worktree** | `<D>.worktree`, a linked worktree of this repository, and the child's own physical cwd | `<R>.observed` worktree identity, bound by the child before `exec`; `git worktree list --porcelain` from the cockpit | `<R>` (copied into the record's evidence directory), `git worktree list` capture | A child whose physical cwd disagrees with the seeded `PWD` must refuse before `exec`. If `<R>` reaches `status: observed` while the cwd differs, the chain is broken and the row fails — a lane that wrote the right files from the wrong cwd is the false success this row exists to catch. |
| 2 | **Branch** | `<D>.branch` under `vcs.dev_branch_prefix` (`dev/…`), issued by `dev_session.sh`, never chosen by the cockpit or the lane | `<D>.branch` compared with `git rev-parse --abbrev-ref HEAD` in the worktree after the lane exits, and with the PR's `headRefName` from `gh pr view --json headRefName` | `<D>`, `<R>`, the PR's forge record | A lane that pushed a branch other than `<D>.branch` is a false success even with a green PR. The forge read is the observer precisely because the local ref can be rewritten after the fact. |
| 3 | **Base** | `<D>.base` = `main`, `<D>.base_oid` = the fetched-and-verified `origin/main` sha this session started from | `<D>.base_oid` compared with `git rev-parse origin/main` captured at session start; `gh pr view --json baseRefName` | `<D>`, the session-start fetch capture, the PR record | A base that moved between issue and merge is not a failure of the lane, but a base **recorded** as something other than what the PR targets is. If `origin/main` advanced mid-run, the row records both values rather than the later one. |
| 4 | **State root** | `<D>.state_root` = the per-lane sandbox; `<D>.env.DEVKIT_STATE_ROOT` identical to it; `<worktree>/.devkit_state_root` marker holding the same absolute path; `DEVKIT_REFUSE_UNSANDBOXED_STATE=1` | `<R>.observed` state identity (child-bound), the marker file read from the worktree, and `git status --short` in the **cockpit** tree showing no new `state/` writes | `<R>`, marker file bytes, cockpit `git status` capture | The dangerous false success is a lane whose `state/` writes landed in the cockpit's repo-root `state/` while the receipt still says `completed`. The cockpit-side `git status` is the independent check: it can show the failure the receipt cannot. |
| 5 | **Approval policy + profile digest** | `<R>.request.approval_policy` naming `dont-ask`, its argv (`--permission-mode dontAsk`), `config/claude-lane-settings.json` and its sha256; the parent's and child's digests agreeing; `<R>.observed.argv` containing both the policy flag and `--setting-sources ""` `--settings <profile>` | `<R>.request.approval_policy` and `<R>.observed.argv`; the profile's sha256 recomputed by the cockpit with `shasum -a 256` against the committed file | `<R>`, the recomputed digest, the profile at its `origin/main` sha | The parent refuses an observation whose argv omits the policy or the trust step, so an argv missing either must not reach `observed`. A digest recorded in this document with no recomputable file behind it is exactly `#621`'s failure; the profile is tracked at a named sha, so this one is recomputable by any later reader. |
| 6 | **Lane model and effort** | Whatever the product default resolves to — the wrapper carries neither control by design, so there is no expected value to match, only a value to record | The runtime's own session transcript at `~/.claude/projects/<encoded-worktree>/<session_id>.jsonl`: `message.model` on an `assistant` entry, top-level `effort`. `session_id` comes from the final-message JSON object, not from the lane's prose | The transcript excerpt (model/effort lines only), `<R>.terminal.final_message_sha256` binding the object the `session_id` was read from | `modelUsage` in the result names every model the session touched and cannot attribute one, so it is **not** the observer (`capability-tier-calibration-live-validation_2026-08-27.md`). If the transcript is absent or the encoded-cwd directory cannot be located, the row reports unavailable — it never falls back to `modelUsage` or to the alias in config. |
| 7 | **`permission_denials`** | `[]` on a clean run: a list-valued, empty denial record | `<R>.terminal.permission_denials`, extracted by the wrapper from the runtime's own result object | `<R>`, final-message bytes by digest | Three outcomes are distinct and must not be collapsed: `[]` (nothing denied), a non-empty list (denials — the wrapper terminalizes `failed`), and `null` (**not observed**). A `null` here would mean the `json-stdout` transport failed to expose the field and is a row failure, not a clean run — the Codex `last-message-file` record's `null` is the precedent for why this distinction is load-bearing. |
| 8 | **Final-text transport** | `<R>.terminal.final_text_transport` = `json-stdout`; exactly one JSON result object on stdout; non-empty `result`; `final_text_sha256` and `final_message_sha256` both present | `<R>.terminal`, plus the final-message file's own bytes rehashed by the cockpit | `<R>`, the final-message file copied into the evidence directory | The friction log's 2026-08-27 entry records `claude -p --output-format json` printing more than one JSON value on stdout in three of five cockpit probes at 2.1.247. The wrapper terminalizes that shape `failed`. If it recurs here, the run is a failed launch, **not** a lane failure, and the raw stdout bytes and stderr are kept before any re-run — the friction entry asks for exactly that. This host runs 2.1.250, a different client from the one that entry was taken on. |

## Terminal outcomes — total

Every launch ends in exactly one of these. There is no "and then look at what the lane
said" branch; the lane's prose is never the discriminator.

| Terminal state | Recognised by | What the slice does |
|---|---|---|
| `completed`, denials `[]` | `<R>.status == "completed"` and `terminal.permission_denials == []` | Proceed to observe the PR from the forge and run the cockpit `pr-watch`. The lane's work is still judged on the diff, not on the receipt. |
| `completed`, denials non-empty | Unreachable by construction — the wrapper terminalizes a non-empty denial list `failed` | If it is ever observed, that is a launcher defect and outranks the whole slice; stop and report. |
| `failed`, denials non-empty | `<R>.status == "failed"`, list preserved in `terminal.permission_denials`, declared policy named in the error | Read the denied calls, decide whether the profile's allow-list is genuinely too narrow for real work on this repo (a finding about the shipped profile) or the prompt asked for something out of scope (a finding about the prompt). Do not widen the profile to make the run pass. |
| `failed`, denials `null` | `<R>.status == "failed"` with no list-valued field | The result could not be extracted — transport failure, malformed/partial/multiple JSON, non-`result` object, error result, or empty `result`. Keep raw stdout and stderr before re-running. Row 8's failure mode. |
| `failed`, nonzero child exit | `terminal.returncode != 0` | The runtime itself failed. Distinguish from the above by the presence of extractable JSON. |
| `interrupted` | `<R>.status == "interrupted"`, `terminal.signal` set | The launcher caught a signal. The exclusive attempt record survives, so the descriptor cannot be silently reused; account for the partial lane, then issue a fresh descriptor. |
| No receipt at all | `<R>` absent | The parent died before finalizing, or the descriptor was refused before an attempt record existed (expiry, foreign identity, occupied path, invalid profile, unresolvable launcher). Read stderr; a refusal before the attempt record is the fail-closed path working. |
| Receipt present, `status: observed`, never terminalized | `<R>.status == "observed"` | The parent was killed between observation and terminalization. Treat as interrupted; do not read the child's output as a result. |

## Evidence retention — staying out of `#621`

`#621` records the failure this section exists to avoid: the Codex writing-lane record
computed digests inside a temporary fixture, cleanup removed the bytes, and the panel
could no longer recompute them, so the capability promotion was retracted.

This lane is not a fixture. Its artifacts live in three places with different
lifetimes, and the record must say which is which:

- **Session directory** (`$DEVKIT_SESSIONS_DIR/<scope>`, outside the repo): descriptor,
  authority seal, receipt, final-message file. Durable until someone runs
  `dev_session.sh rm <scope>`. **Not** durable to a later reader of the repository.
  Therefore the descriptor, the receipt, and the final-message bytes are **copied into
  the record's evidence directory under `saved_plans/` and committed** — that copy is
  what a later reader recomputes against, and the record says so.
- **The runtime's transcript** (`~/.claude/projects/…`): outside the repo, operator-
  owned, and carries conversation content. Only the model/effort lines are excerpted
  into the record. A later reader **cannot** recompute this one, and the record states
  that limit rather than implying provenance it does not have.
- **The forge** (the lane's branch, commits, PR, CI runs): independently readable by
  anyone with repository access, and not deletable by this session's cleanup. This is
  the `#621`-shaped "independently read-back immutable artifact", and it is what the
  parity matrix's promotion rests on — not on the copied receipt alone.

What a later reader **can** recompute: every digest in the record, against the
committed evidence copies and the tracked profile at its named sha. What they
**cannot**: the transcript excerpt, and the session directory if it has since been
removed. Both limits are stated in the record.

## Matrix movement rule, fixed in advance

The parity matrix's headless row moves **only** as far as the durable evidence carries.
The row may record: a lane on the kit's own repository, under the shipped launcher and
shipped policy, performed a scoped change, committed, pushed, opened a PR, and received
a cockpit `pr-watch` review receipt — with the receipt and its digests committed and the
PR independently readable. It may **not** record anything resting on the lane's prose,
on the transcript excerpt alone, or on a session directory that may be swept.

If any row above comes back unavailable, that row's claim does not enter the matrix.
Deciding that after seeing the outcome is how a record talks itself into a promotion,
which is why the rule is written here first.
