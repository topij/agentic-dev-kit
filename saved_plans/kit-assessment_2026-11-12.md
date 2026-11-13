# Whole-kit assessment and recommended plan

Assessed at `fd12e961` on 2026-11-12, from the primary checkout on macOS. This document
changes no engine, workflow or test. It says what is strong, what needs work, and what
to do next, in that order.

**How it was done.** Four read-only audits ran in parallel: security, code duplication
and structure, the test suite, and the documents and adopter experience. Each returned
findings with file and line, and the lines this document leans on were re-read
afterwards. Unless a line says *run*, a finding here is *read*: established by reading
the code path at `fd12e961`, not by executing it. Two limits follow from that:

- A read finding about a gate needs a live probe before it becomes a ticket. *Security*
  names the one that matters most.
- Tracker coverage was judged from issue titles (`gh issue list --state open
  --limit 500 --json number,title,labels,updatedAt`, 2026-11-12). Bodies were read only
  where a line below says so.

The earlier assessment of skills and instruction files,
[`skills-and-instructions-assessment_2026-10-11.md`](skills-and-instructions-assessment_2026-10-11.md),
covers runtime guidance and is not repeated here. *Documents* below reports what
happened to its first recommendation.

## Verdict

The kit's engineering is careful and its records are unusually honest about their own
limits. Its problems are not carelessness. They are about cost and about where trust
sits:

1. **It grows faster than one operator can own.** Engine code and tests each grew by
   about a quarter in the month to 2026-11-12 (M1), every workflow that was not split
   in that month grew too (M2), and the tracker took in more issues than it retired in
   July, August, September and November (M3).
2. **On the unattended path, the parts a hostile text or a confused agent can reach are
   held by prose and self-report.** The mechanisms are strong against malformed values.
   They do not establish who wrote a ticket, a comment or a review receipt, and the
   merge gate composes those into `mergeable`.
3. **The merge contract and the plumbing under it are each written more than once, and
   copies of the plumbing have already drifted.** `pr_watch.py` is a script that other
   engines do not import, so each consumer restates what its report means.
4. **Distribution lags the product.** Lite is where new installs are happening and its
   upgrade is one engine command. The full profile's upgrade is still hand-run from a
   long workflow, and there is no release for an adopter to pin.

The plan at the end takes these in an order that puts the cheap, decision-unblocking
steps first and the large refactors last.

## Measurements

Every figure this document uses is here, with its command. The date is 2026-11-12 for
all of them. Readings of the forge are not tied to a commit; the repository head was
`fd12e961` when they were taken.

| Id | Reading | Command |
|---|---|---|
| M1 | Engine and installer lines: 37306 at `0b8166b8` (2026-10-11), 47088 at `fd12e961`. Test lines: 80068 and 100792. | `git ls-tree -r --name-only <sha> scripts init.sh \| grep -E '\.(py\|sh)$\|pre-push$' \| grep -v '/tests/' \| grep -v conftest \| xargs -I{} git show <sha>:{} \| wc -l`; tests: the same listing of `scripts` filtered to `/tests/.*\.py$` |
| M2 | Workflow lines at `0b8166b8` and at `fd12e961`: `upgrade.md` 978 and 1461; `adopt.md` 580 and 875; `wrap-up.md` 617 and 789; `post-merge-systemize.md` 589 and 709; `session-start.md` 509 and 612; `parallel.md` 454 and 514; `parallel-headless.md` 407 and 545; `pr-watch.md` 789 and 610; `triage-friction-log.md` 1423 and 541; `fallback-review-panel.md` 1146 and 1647. | `git show <sha>:docs/agentic-dev-kit/workflows/<name>.md \| wc -l`, and the same for `docs/agentic-dev-kit/fallback-review-panel.md` |
| M3 | 792 issues: 375 open, 417 not open (314 completed, 81 not planned, 22 duplicate). Opened and retired by month: July 117 and 20; August 279 and 65; September 97 and 33; October 228 and 261; November to the 12th 71 and 38. Open issues' age in days, quartiles: 19, 48, 96. Open issues with none of the labels `P1`, `P2`, `P3`: 309. Open issues labelled `execution:unknown`: 241. Open titles matching `panel\|lens\|review`: 103. | `gh issue list --state all --limit 2000 --json number,state,createdAt,closedAt,labels,title,stateReason`, then grouped in Python |
| M4 | The 120 newest merged pull requests (#1106, merged 2026-10-14, to #1423): hours from opened to merged, quartiles 0.7, 1.7, 4.1; added lines, quartiles 64, 198, 493. Commits per pull request over the newest 80 of them: quartiles 3, 4, 5; the largest is 17. | `gh pr list --state merged --limit 120 --json number,createdAt,mergedAt,additions,changedFiles,title`; commits from `gh api repos/{owner}/{repo}/pulls/<n> --jq .commits` |
| M5 | The nine successful runs among the 15 newest completed `Test` runs took between 11 and 16 minutes from creation to last update, except one push run at 46 minutes. | `gh run list --limit 15 --status completed --json conclusion,createdAt,updatedAt,event` |
| M6 | First-parent commits since 2026-10-01: 229. Of those, commits that changed `kit-manifest.json`: 158. | `git log --since=2026-10-01 --first-parent --format=%h \| wc -l`, and the same with `-- kit-manifest.json` |
| M7 | `config/dev-model.yaml`: 638 comment-only lines, 192 other non-blank lines. | `awk '/^[[:space:]]*#/{c++;next} /^[[:space:]]*$/{next} {k++} END{print c,k}' config/dev-model.yaml` |
| M8 | `saved_plans/` holds 1196 tracked files, 42M on disk. | `git ls-files saved_plans \| wc -l`; `git ls-files -z saved_plans \| xargs -0 du -ch \| tail -1` |
| M9 | `scripts/tests/test_portability.py` is 22556 lines. Its helper `_assert_triage_semantics` spans lines 5170 to 14751. `scripts/tests/test_pr_watch.py` contains 350 `monkeypatch.setattr` calls. `scripts/pr_watch.py` is 7392 lines and `scripts/kit_doctor.py` 6252. | `wc -l`; Python `ast` over the file's top-level functions; `grep -c 'monkeypatch.setattr'` |
| M10 | `make test` at `435133e0`, in `.claude/worktrees/kit-assessment` on macOS, printed `6851 passed, 5 skipped in 1728.00s (0:28:47)` and exited 0. | `make test` |

## What is strong

- **Doctrine that names the failure each rule prevents, and admits what is not
  enforced.** `PRINCIPLES.md` pairs each principle with a mechanism.
  `docs/kit-enforcement.md` marks a rule `judgement, unenforced` when only a reader
  enforces it. That table is the first place to look when deciding what to build
  next.
- **A fail-closed vocabulary.** "A source that fails is reported as unavailable, never
  as its empty value" runs through `session-start.md` and `wrap-up.md`, with outcome
  tables that take the first match. It is the right default for an agent that would
  otherwise read a failed command as good news.
- **One shared workflow definition per workflow, with generated bindings.**
  `scripts/lib/runtime_adapters.py` renders both runtimes' skills, and
  `runtime-parity.md`'s front matter drives `test_runtime_parity_matrix.py`. Claude and
  Codex cannot silently diverge in the binding layer.
- **Launch authority is mechanism, not instruction.** `launch_lane.py` never invokes a
  shell, resolves a bare command only on a fixed trusted path, refuses unrestricted
  permission modes as non-members of a closed vocabulary, and binds the lane profile by
  digest (`launch_lane.py:100-127`, `337-387`, `770-887`).
- **Deletion is guarded by identity, not by name.** `sweep_scratch.py:400-424` and
  `989-1011` check direct-child containment, real path and `lstat` identity and refuse
  symlinks. `session_cleanup.py` never forces a worktree removal.
- **The merge wrapper re-reads at the moment it acts.** `dev_session.sh merge` polls
  again, refuses a class other than `standard`, and pins the merge to the polled head
  (`dev_session.sh:1047-1145`).
- **Tests that prove themselves.** Prose pins are re-run against hostile mutations of
  the text (`test_portability.py:22429-22450`). The lite documents' shell blocks are
  extracted and executed under `sh`, `bash` and `zsh` (`test_lite_profile_docs.py`).
  The Makefile targets are pinned by executing `make -n` (`test_mutation_gate.py`). A
  guard fails the suite when a test writes the real `state/` directory.
- **The flywheel turns.** Field reports from the lite installs on 2026-11-10 and
  2026-11-11 (#1414 to #1419) reached `main` as #1421 on 2026-11-11. The tracker has
  retired 417 issues (M3).
- **Delivery is fast for what it checks.** Of the 120 newest merged pull requests, half
  went from opened to merged in under 1.7 hours (M4).
- **CI is least-privilege.** `pull_request` rather than `pull_request_target`,
  `contents: read`, the third-party action pinned to a commit, and `npm ci
  --ignore-scripts` (`.github/workflows/test.yml`).
- **The lite profile is the right answer to adoption cost.** It keeps the handoff, the
  friction inbox and a risk-tiered review, installs no engine, and upgrades through
  `kit_doctor.py --upgrade-lite` run from the kit's own clone.
- **The handoff test.** "Most pull requests leave nothing" (`wrap-up.md`) is the rule
  that keeps a living plan from becoming a second changelog. *The kit's own records*
  below notes where this repository has stopped following it.

## What needs work

Ranked by what it costs the operator, an adopter or an unattended agent.

### 1. Growth against one operator's attention

M1 says engines and tests each grew by about a quarter in a month. M2 says the text
agents load grew with them: `pr-watch.md` and `triage-friction-log.md` shrank because
they were split into a main file and reference files, and every other workflow there
is longer. M3 says the backlog is the sink. Its inflow exceeded its outflow in July,
August, September and November, and the exception, October, is the month of a
deliberate backlog pass.

These properties of the backlog make it hard to choose from:

- **Priority is absent.** 309 of the 375 open issues carry no priority label (M3).
- **The largest subject is the review machinery itself.** 103 open titles match
  `panel|lens|review` (M3). The process that finds defects is the largest source of
  work about itself.
- **It holds stale and overlapping entries.** #36's title says the pre-push hook has
  zero automated test coverage; `scripts/tests/test_pre_push_hook.py` has existed since
  `6f2cc247` (2026-09-08), and the issue has no comment. #1145 and #1398 describe the
  same defect by their titles, a review receipt that lives in one checkout. #467, #677
  and #1082 each report the state guard failing on a concurrent write.

What is not measured is the cost of a review round in tokens. M4 shows the loop is
quick in wall-clock time. Whether it is proportionate cannot be judged until #1174
records usage. Decisions about review proportionality (#585) are being made without
that figure.

### 2. Provenance on the unattended path

See *Security*. The short form: the kit establishes that a value is well-formed and
that a head is the head that was reviewed. It does not establish who wrote the ticket a
lane was handed, the comment a watch loop is told to act on, or the receipt the merge
wrapper trusts.

### 3. One contract with a copy in each consumer

See *DRY*. `dev_session.sh`, `reconcile_sessions.sh` and `scripts/lib/triage/model.py`
each decide whether a `pr_watch` report authorizes a merge, and each checks a different
set of fields. The plumbing under them (state root, `git` and `gh` runners, process
stops, fence scanning) is duplicated too, and those copies differ in behaviour.

### 4. Two engines too large to change safely

See *Modularity*. `pr_watch.py` and `kit_doctor.py` are single files (M9), and
`test_pr_watch.py` patches attributes on the module object, so a split would stop its
patches from taking effect.

### 5. The text an agent must load

See *Documents*. Workflows carry incident history and notes to future editors in the
text every run reads, and no workflow has a line budget.

### 6. Distribution and upgrade

- **There is no release.** `git tag -l` prints nothing. `adopt.md` and `upgrade.md`
  clone `--depth 1` from the default branch and record `kit_commit` after the copy, so
  an adopter takes whatever `main` holds at that minute. `README.md:236` says the
  manifest is "regenerated at release"; `CHANGELOG.md` says there are no release tags.
- **The quickstart ships the kit's own records.** `README.md`'s first route is
  `cp -r /path/to/agentic-dev-kit/. .`, which copies `docs/kit-*.md` and `saved_plans/`
  (M8) into the adopter's repository, with no step that removes them.
- **The profile choice is hidden.** Lite appears in `README.md` after the quickstart
  and upgrade sections, and `docs/getting-started.md`, `docs/developer-guide.md` and
  `docs/architecture.md` do not mention it.
- **The full upgrade is hand-run.** `kit_doctor.py` reports states; the agent then
  copies files per state, refreshes `init.sh`, merges settings and regenerates lens
  definitions by following `upgrade.md` (M2). Lite's `--upgrade-lite` plans, applies
  and verifies in one command. Adopter field reports #988, #990 and #1170 are about the
  hand-run path.
- **Versions are three unrelated integers and a commit.** `kit.version` in the config,
  `kit_version` in the manifest, `CURRENT_TEMPLATE_VERSION` in
  `scripts/lib/runtime_adapters.py`, and the baseline sha.

### 7. Test suite shape and CI parity

See *Tests*.

### 8. The kit's own records

- **The handoff has become a changelog in places.** The *Scratch retention* entry in
  `docs/kit-handoff.md` narrates each merged pull request with its sha. `wrap-up.md`
  asks for a status line, an owner pointer and a `▶ Next:`.
- **`saved_plans/` is evidence storage inside a template repository** (M8). Every
  clone, including the `--depth 1` clone an adopter's agent makes, downloads it.
- **`kit-manifest.json` changes in about two of every three commits** (M6), because it
  hashes bytes. Two concurrent pull requests that each edit a kit-owned file both
  change it.

## Security

The threat model used: one operator, agents that run unattended, and a public
repository that takes issues and pull requests from outside. Issue text, pull request
text, review comments and the files in a pull request are attacker-influenceable. PR
#1397, open on 2026-11-12, is from an outside contributor, so this is not hypothetical.

Findings are described by class. None of them is a step-by-step route.

| # | Finding | Evidence | Read or run | Tracked |
|---|---|---|---|---|
| S1 | **An unattended lane holds the operator's whole forge credential, and untrusted text reaches it.** `--ticket` appends the live issue body with no check of who wrote or last edited it. The child inherits every environment variable except those starting `DEVKIT_` or `GIT_` and the keys `GH_REPO`, `PWD` and `OLDPWD`. The profile grants `Edit(**)` together with `make test`, which runs repository code as the operator's OS user, so credentials stored for that user are within its reach whatever the environment holds (not probed here). | `launch_lane.py:66-72`, `285-305`, `390-391`, `1480-1489`; `config/claude-lane-settings.json` | read | #615 and #617 cover parts; ticket-author trust and a process boundary are untracked |
| S2 | **A lane can write the review receipt its own merge is judged by.** The lane's state root is `<session>/state`, the same root `dev_session.sh merge` passes to `pr_watch.py`. The profile grants `uv run scripts/pr_watch.py:*`, and `record_review` checks the head, not the caller. With `review.bots: []`, that receipt is the whole of the independent-review evidence. | `dev_session.sh:281`, `461`, `1047`; `pr_watch.py:4875-4909`; `config/dev-model.yaml:312` | read; **probe before filing** | untracked; #815 is the nearest |
| S3 | **`pr_watch.py --json` gives the agent every comment body with no author tier.** The follow-up hook tells the agent to poll `--json` and not to yield until findings are fixed or answered. A comment from any account styled as a finding is input to that loop. | `pr_watch.py:6135-6148`; `grep -c 'author_association\|authorAssociation' scripts/pr_watch.py` prints 0 at `fd12e961`; `pr_followup_hook.py:422-426` | read | #267 covers sanitising; author trust is untracked |
| S4 | **Review lenses are isolated by instruction and attestation.** The lens definitions carry no tool restriction, and a lens runs with the operator's credentials. | `.claude/agents/adversarial.md:1-6`, whose front matter has `name`, `description`, `model` and `effort` and no tool list | read | #1025, #712, #1138, #1078, #270 |
| S5 | **The kit an adopter installs is the unpinned tip of `main`.** No tag, no signature, and the manifest hashes come from the same clone they verify. | `adopt.md:22-29`; `upgrade.md:104-112` | read | untracked; #324 covers the baseline only |
| S6 | **Granted command prefixes accept arguments that reach outside the lane.** `gh pr create`, `gh pr view` and `gh pr ready` take a repository flag; the stated reason for withholding `gh pr comment` is that flag. Body-file and message-file arguments name any readable path. | `config/claude-lane-settings.json`; `parallel-headless.md:159-161` | inferred from the CLIs' documented flags | #615 and #628 are the nearest |
| S7 | **The safety-critical list omits files on the gate engines' import path**, among them `scripts/lib/kitconfig.py` and `scripts/lib/repo_root.sh`. A pull request touching only those is classed `standard`. | `config/dev-model.yaml:378-405`; `launch_lane.py:55`; `dev_session.sh:69` | read | #928, #434, #930 |
| S8 | **CI and local test dependencies float.** GitHub-owned actions are on mutable tags; `pytest` and `pyyaml` are unpinned in CI and in `make test`, and `make test` runs inside credentialed lanes. The `toolkit` job's checkout does not set `persist-credentials: false`; the `documentation` job's does. | `.github/workflows/test.yml`; `Makefile` | read | untracked |
| S9 | **`.claude/settings.local.json` stays out of git only through the operator's global ignore file.** `git check-ignore -v` names `~/.config/git/ignore`; neither `.gitignore` nor `init.sh` seeds the entry. | run: `git check-ignore -v .claude/settings.local.json` at `fd12e961` | run | untracked |

Smaller findings already ticketed: the text render leaves author, path and check name
unsanitised (#98, #932), and `init.sh`'s `.mcp.json` credential check misses the
hyphenated header shape (#86).

**The pattern.** Where the adversary is a confused agent or a malformed value, the kit
uses mechanism: argument vectors, digests, closed vocabularies, identity-checked
deletes. Where the adversary is hostile text or a hostile agent, it uses prose: the
lane contract, the lens rules, a self-reported receipt. The documents say this
candidly. The gap is that the merge gate then treats the prose-backed claims as
evidence, and the least-trusted actor writes its own.

**What would change the picture.** A lane and a lens run as the operator's OS user, so
no local check is a boundary against them. Two things together make one: their own,
weaker forge credential, and isolation from the credentials stored for the operator.

The identity alone is not enough. A lane can edit files and run `make test`, so it
runs code as the operator's OS user, and whatever the `gh` CLI or a Git credential
helper has stored for that user stays readable whatever the child's environment
holds. That was not probed here; it follows from where those tools keep credentials.

With both, "a lane does not merge", "a lane does not record its own review" and "a
lens publishes nothing" become things the forge enforces by author, and S1's blast
radius shrinks to what the lane's credential can do. The identity needs a second
account or an app installation, and D1 below records the operator's decision to have
one. The isolation needs a separate OS user, a container or the runtime's own
sandbox. Which of those is not decided; step 2c probes them.

## DRY

**Well factored already.** Every Python engine reads configuration through
`scripts/lib/kitconfig.py`, and the pre-push hook calls it too. `kit_doctor.py` derives
dependency edges from the import graph instead of a hand list. `triage` and `systemize`
are packages with injectable runners. `panel_prompt.py` imports `kit_doctor.py`'s
lens-definition renderer, so that text has one source.

**Duplicated, with a divergence that can be cited:**

| # | What is written more than once | Where | The divergence | Tracked |
|---|---|---|---|---|
| C1 | **"This report authorizes a merge."** | `dev_session.sh:1065-1135`; `reconcile_sessions.sh:525-545`; `scripts/lib/triage/model.py:654-666` | Each re-checks a different set of fields beside `mergeable`: identity and `review_class` in `dev_session.sh`; `converged`, identity and empty `merge_blockers` in `reconcile_sessions.sh`; `converged`, `done`, empty `merge_blockers`, empty `truncated_reads` and `review_evidence.valid` in triage. `dev_session.sh:1063` warns against a second copy of the contract. No difference that lets a merge through was found. The cost is that a change to the contract has to reach each copy: #1370 reports that a `self` lane the wrapper refuses for its review class stays open in `reconcile_sessions.sh` and is never held. | untracked as a class; #1370 is an instance; #663 is adjacent |
| C2 | **Where state lives and where the repository root is.** | `pr_watch.py:153-247` beside `scripts/lib/state_paths/resolver.py:115-216`; other root walks in `kitconfig.py`, `devmodel_config.py`, `state_paths/repo_root.py`, `repo_root.sh`, `hooks/pre-push`, `scripts/conftest.py` | `pr_watch.py` walks from its own file and never raises; `state_paths` walks from the working directory and raises. `dev_session.sh` and `reconcile_sessions.sh` pass `DEVKIT_ROOT` to `pr_watch.py`, which does not read it (`grep -c DEVKIT_ROOT scripts/pr_watch.py` prints 0 at `fd12e961`). | consequences in #1145, #1398, #60, #203; the duplication is untracked |
| C3 | **Review defaults.** | `config/dev-model.yaml` `review.*`; `init.sh:1402-1415`; `pr_watch.py:350-486` | `_DEFAULT_NOISE_MARKERS` still lists "review skipped" and the Bugbot billing notice; the shipped config's `noise_markers` no longer does. | untracked; #542 is the general class |
| C4 | **Running `git` and `gh`.** | a wrapper in each of `check_record_prose.py`, `launch_lane.py`, `panel_prompt.py`, `runtime_smoke.py`, `pr_watch.py`, `kit_doctor.py`, `review_eval.py`, `session_cleanup.py`, `lib/triage/model.py`, `lib/triage/providers.py`, `lib/runtime_adapters.py`, `lib/systemize/forge.py` | Timeouts, `OSError` handling and `GIT_*` scrubbing differ per copy. `session_cleanup.py:60` sets a timeout and lets `TimeoutExpired` escape. | #414, #1219, #1394 are instances |
| C5 | **Stopping a process group.** | `launch_lane.py:1720-1750`; `runtime_smoke.py:436-448`; `review_eval.py:413-415`; `reconcile_sessions.sh:163-178` | Each treats `PermissionError` differently: retry then error, treat as stopped, suppress, not caught. | #1172 covers one |
| C6 | **Finding Markdown fences.** | `archive_plan_sessions.py:293`; `review_eval.py:229`; `lib/systemize/normalize.py:156-186`; `lib/triage/inbox.py:50-78`; `lib/triage/model.py:68-93`; and a real parser in `check_record_prose.py:359` | Only `normalize.py` accepts a fence after a list marker. `review_eval.py` and `triage/model.py` accept a backtick in a backtick fence's info string; the others do not. | #1171, #1205, #216, #925 |
| C7 | **Where a config value ends.** | `kitconfig.py:92`; `repo_root.sh:53`; `init.sh:193` | The awk reader strips ` #` inside quotes. `vcs.protected_branch` is read by awk in `dev_session.sh` and by `kitconfig.py` in the pre-push hook. | #88 |
| C8 | **Atomic writes.** | `lib/atomic_write.py` beside local versions in `launch_lane.py:536`, `session_cleanup.py:99`, `lib/systemize/artifacts.py:211`, `lib/triage/storage.py:242` | Temp naming and mode differ, so leftover temp files match no single pattern. | #784 and #777 are consequences |
| C9 | **Rules stated in more than one document.** | the ready and draft rule, the lane-wrapper rule (`wrap-up.md:104`, `122`, `751`), the closing-keyword rule | `wrap-up.md` and `session-start.md` cite a closing-keyword rule that ships to adopters in neither `AGENTS.md.tmpl` nor `AGENTS-sections.md`. The `lite:begin` markers sync the clauses they mark and are read only by `test_lite_profile_docs.py`. | #296 is the same shape |

C1 is the one to take first. It is small and it is on the merge path, and step 2a of
the plan changes what counts as review evidence: with one predicate that change lands
once. C2 has the highest running cost today, because #1145 and #1398 both come from
it.

**Hardcoding, against Principle 10.** `origin` has no config key and is literal in
`dev_session.sh`, `reconcile_sessions.sh`, `launch_lane.py`, `pr_watch.py` and
`lib/triage/providers.py` (#11 covers the hook only). `state.dirname` and `vcs.forge`
are declared and read by no engine (#145). `init.sh:1253` and `1281` carry literal
copies of the lens definitions that `kit_doctor.py` renders (#990).

**Dead code.** `scripts/lib/devmodel_config.py` describes itself as vestigial and still
ships. `state_paths.glob_state` and `glob_state_cache` have no engine caller.

## Modularity

`triage` and `systemize` show the shape that works here: a package under `scripts/lib/`,
a thin command-line shim, protocols for the forge. `pr_watch.py` and `kit_doctor.py`
predate that shape.

**`pr_watch.py`.** Configuration loads into module globals at import
(`pr_watch.py:754-765`). `build_report` takes 14 parameters and spans lines 5645 to
6175. The transport reports truncation through process globals. `REPO_ROOT` is the
working directory of each `gh` and `git` call.

**`kit_doctor.py`.** `main` spans lines 5569 to 6248 and `render` 3747 to 4347.
`KIT_OWNED` is a hand-maintained list (#47).

**The stated reason for single files does not hold.** `README.md` calls the engines
"PEP-723 single-file scripts", and `pr_watch.py:33-36` cites per-file upgrades. The
engines already import from `scripts/lib/`: `pr_watch.py:491` puts it on `sys.path`,
and `kit_doctor.py:238` and `launch_lane.py:55` import `kitconfig` from it.

**What actually blocks a split:**

- `test_pr_watch.py` loads the engine by file path and patches attributes on the module
  object (M9). Once callers live in sibling modules, a patch on the facade no longer
  intercepts them.
- `review.safety_critical_paths` names `scripts/pr_watch.py` literally. A new module
  drops out of the two-lens class unless the list, and each adopter's copy of it, is
  extended (#930).
- A per-file upgrade can pair a new entry point with an old helper.
- `kit_doctor.py` must still start on a broken install, so its new modules have to be
  lazy imports, as `runtime_adapters` already is.

**Extraction order, when it is time.** For `pr_watch.py`: state root and persistence
onto `state_paths`; the report contract as an importable predicate; transport; review
class and receipts; classification; render. For `kit_doctor.py`: the lite verify and
upgrade code; lens and compute definitions; registration inspection; the registry;
render. The first two `pr_watch.py` extractions are C2 and C1 above, and they are worth
doing whether or not the rest follows.

**Shell.** `init.sh` migrates YAML and renders templates in `awk` and `sed` and never
calls Python. `dev_session.sh`, `reconcile_sessions.sh` and `hooks/pre-push` embed
Python heredocs that no linter reads. The credible path is to move those heredocs into
an importable module first, and to have `init.sh` keep its `sh` entry point and hand
migration to a stdlib Python module once it has confirmed `python3`.
`kit_doctor.py --upgrade-lite` is the precedent.

## Tests

**Strong**, as listed under *What is strong*: mutation-proven pins, executed
documentation, the real-state guard, parsed-YAML checks of CI triggers.

**Needs work:**

- **`test_portability.py` holds a second model of the triage protocol** (M9).
  `_assert_triage_semantics` is 9582 lines, contains no import and no engine path, and
  is called from lines 5023, 14893 and 15341. It checks the workflow text against an
  in-test model, while the real engine in `scripts/lib/triage/` has its own test files.
  A reworded workflow costs an edit here, and the pin cannot catch an added
  contradiction (#791 says the same of systemize). There is no recorded reason the file
  is one file; each new test file needs a `KIT_OWNED` row, which is an incentive to
  append (#853).
- **No suite-wide hermetic layer.** The only autouse fixture is the state root. Test
  files define their own `git` runners and set `user.email` by hand. Global git
  configuration is nulled only in the files `grep -lE
  'GIT_CONFIG_GLOBAL|GIT_CONFIG_NOSYSTEM|GIT_CONFIG_SYSTEM' scripts/tests/*.py` lists
  (`test_adoption_fixtures.py`, `test_init_sh.py`, `test_kit_doctor_upgrade_lite.py`,
  `test_lite_profile_docs.py`, `test_runtime_smoke.py` and `test_portability.py` at
  `fd12e961`). An operator's `commit.gpgsign` or `core.hooksPath` reaches the temp
  repositories every other test file builds. #97 and #1394 are instances.
- **CI and local runs differ in platform.** CI is `ubuntu-latest` on Python 3.12. The
  operator's machine is macOS, and `uv` selects a newer Python there. Tests that never
  run in CI include the Darwin-only test at `test_sweep_scratch.py:1989`, the
  3.13-and-later test at `test_state_guard.py:1008`, and the case-insensitive
  filesystem tests. #1395, the macOS `/tmp` symlink refusal, is the kind of defect this
  lets through.
- **CI does not run `make test`.** `test.yml` restates its steps. `make test` lacks
  CI's run without PyYAML and its documentation job. The `Makefile`'s own "KNOWN GAP"
  note says nothing pins that `test` depends on `lint` and `check-syntax`.
- **Timing and process tests run serially with no per-test timeout.** Wall-clock
  assertions sit in `test_lane_launcher.py:1217`, `test_reconcile_sessions.py:1009` and
  `test_review_eval.py:262`. The `toolkit` job has no `timeout-minutes`. #644 and #1344
  are flakes of this kind. M5 and M10 show the price: a CI run is 11 to 16 minutes and
  a local run on the operator's machine is 29 minutes.
- **Executed documentation stops at lite.** `session-cleanup.md`'s shell blocks are
  referenced by no test file (#374 and #586 are the general tickets).

## Documents

**What happened to the October recommendation.** The earlier assessment's first
recommendation was to cut each workflow to steps plus one level of reference. Two
workflows were split: `pr-watch.md` and `triage-friction-log.md` are shorter (M2). The
others grew, and `fallback-review-panel.md`, which a panel run loads, went from 1146
to 1647 lines. Both split workflows then instruct the agent to read every reference
file completely before the first action (`pr-watch.md:17-20`,
`triage-friction-log.md:241-244`), so the split bounds a single read and not the load.

**Needs work:**

- **Incident history sits in the executed text.** One gather bullet in
  `session-start.md:256-339` carries dated measurements and an anecdote about
  `--limit 25`. `adopt.md:103-169` spends a long passage on how a probe was arrived at.
  `upgrade.md:9-24` addresses future editors of the file. `fallback-review-panel.md`
  already points to an `-evidence.md` companion for its rationale; that pattern is not
  applied to the workflows.
- **No workflow has a budget.** `doc_budgets` covers the handoff, the friction log and
  `AGENTS.md`.
- **The workflows break `writing-for-agents.md`.** Its "one home per meaning" against
  C9; its finish lines against the fact that `grep -c "Done when"` is non-zero only for
  `upgrade.md` among the workflows.
- **Unsynced copies already disagree.** `config/dev-model.yaml:17-18` calls re-running
  `init.sh` "the supported upgrade path" while `README.md:186-190` sends the reader to
  the `upgrade` workflow. `docs/getting-started.md:113-129` shows a briefing with three
  tags; `session-start.md` defines four plus environment and disk lines.
- **The config is hard to read as documentation** (M7). Kit-own values such as
  `tracker.project_name` and the safety-critical list sit among adopter placeholders
  (#930). There is no schema.
- **Lite moved validation into prose.** With no engine in the adopter's repository,
  `lite-wrap-up.md:47-106` makes the agent a schema validator, and
  `lite-session-start.md:142-285` is an inline `awk` parser loaded each session.
  #1381's review rounds showed that a prose list of config stops does not converge
  (#1368). `kit_doctor.py --verify-lite` already runs from the kit's clone and is the
  place for that check.
- **Doctrine one runtime receives.** `CLAUDE.md`'s cloud-session section (install the
  hooks on a fresh clone, the Git floor, tests that fail for environment reasons)
  applies to any runtime's fresh clone and reaches only Claude Code.

## Missed opportunities

1. **A separate, weaker credential for lanes and lenses, with isolation from the
   operator's stored credentials.** Described under *Security*. Together they turn
   "a lane does not merge", "a lane does not record its own review" and "a lens
   publishes nothing" into rules the forge enforces.
2. **An engine for the session-start gather.** `session-start.md` has the agent run the
   pull request list, a per-request `pr_watch.py` poll, the tracker read with its paging
   rules, the disk report and the cleanup list by hand, and carries the lore for each.
   This session ran them as separate commands. #1135 proposes a deterministic status
   snapshot, #663 reports that pull request data is fetched by hand and by engine, and
   #313 says the truncation rule is doctrine with no mechanism. This is Principle 9
   applied to a workflow every session runs.
3. **Releases.** A tag per adopter-visible change set, an export that leaves out
   `saved_plans/` and `docs/kit-*`, and an `adopt.md` and `upgrade.md` that take a ref
   and verify it. This also gives the changelog fragments something to compile into.
4. **`kit_doctor.py --upgrade` for the full profile.** The states already exist and
   `--upgrade-lite` shows the plan, apply and verify shape. D4 defers it.
5. **One merge predicate, importable.** C1. The triage, lane and reconcile paths then
   cannot disagree.
6. **Usage on the record before tuning review.** #1174. Review proportionality, the
   verifier tiers in #1156 and the round budget are all cost decisions.
7. **Generate instead of pin.** The lite documents, `AGENTS.md.tmpl`,
   `AGENTS-sections.md` and the config an adopter starts from could render from one
   source of rules and one schema, as the skill bindings already do.
8. **A macOS runner.** The operator develops on macOS and CI is Linux only.
9. **Lite first in the reader's path.** The profile with the installs is the one the
   README introduces last.

## Recommended plan

Each step is one pull request unless it says otherwise. Tags are `[size · review class
· environment]`, with sizes as `session-start.md` defines them. *Safety-critical* means
the step changes a file in `review.safety_critical_paths` and owes the two-lens review.
No ticket is filed by this document; filing is the operator's go-ahead.
A step's **Tickets:** line, added by step 1b, names the open tickets on that step's
subject; it does not claim that delivering them completes the step.

### Step 0. The operator's decisions

These gate the steps that follow. The operator made them on 2026-11-12, in the session
that wrote this document, taking the recommendation given for each. D4 is the
operator's own answer.

- **D1. A separate forge identity for lanes and lenses: yes, lanes first.** A second
  account with a fine-grained token scoped to this repository, for contents and pull
  requests and nothing else. `launch_lane.py` passes that token to the child in place
  of the operator's, and a ruleset on `main` leaves merging to the operator's account.
  Lenses follow with a read-only token. Not yet probed: how the ruleset and a
  fine-grained token behave together. That probe is part of step 2c. Until 2c ships,
  steps 2a and 2b raise the bar and stop short of a boundary.

  **The identity alone is not a boundary.** It becomes one only together with
  isolation from the credentials stored for the operator, as *Security* says. The
  recommendation the operator took on 2026-11-12 left that out. Review of this document
  raised it, the pull request's decision packet records it, and the operator authorized
  writing it in on 2026-11-13. Which form the isolation takes is not decided; it is
  part of step 2c.
- **D2. Hold `self`-class lane merges: yes.** In force from 2026-11-12: no lane is
  issued with `--merge-class self`, and no session runs `dev_session.sh merge`, the
  self-merge wrapper. The operator merges lane pull requests after reading them.

  **This hold is prose.** It binds a session that reads this document or the handoff
  entry that carries it, and nothing else. The kit's documents and engines still
  describe and accept self-merge. `parallel.md`'s *Per-lane merge class* table, which
  classes mechanical and standard lanes as self-merge for autonomous batches, is one
  example, and this document does not list the others.
  `dev_session.sh new` still accepts `--merge-class self` (`dev_session.sh:257-258`).
  `dev_session.sh merge` gates on the session's stored class (`dev_session.sh:1033-1035`),
  so a `self` session already on disk stays mergeable. On 2026-11-12, with the primary
  checkout at `fd12e961`, no `merge_class` file existed under the default sessions
  directory beside it (`ls <sessions-dir>/*/merge_class` matched nothing).
  `dev_session.sh list` is not that check: it shows only a session that still has its
  worktree. This pull request changes no engine and no workflow, so the mechanism is
  step 2a.

  **What the operator reads is the pull request, not the merge-ready line.**
  `reconcile_sessions.sh` reports an operator-class lane as held and merge-ready from
  a `pr_watch.py` report read under the lane's state root
  (`reconcile_sessions.sh:495-520`). That line rests on the same receipt as S2 and is
  not independent evidence.

  **It lifts when step 2a ships.** If 2a's probe finds nothing to repair, it lifts on
  the operator's decision, recorded with the probe, and only if the probe covered each
  route a lane has to the receipt (the granted `pr_watch.py --record-review`, and a
  direct write of the state file under the lane's state root) and included a control
  in which a receipt the cockpit recorded is accepted. A probe result alone lifts
  nothing.
- **D3. A LOW review finding is not ticketed until it recurs: yes, as a trial.** It is
  recorded in the pull request's typed disposition and nowhere else, and becomes a
  ticket on its second occurrence. `post-merge-systemize` already reads typed
  disposition lines from merged pull requests, so the recurrence has a reader when
  that workflow runs. This document did not establish that anything runs it on a
  schedule in this repository, and what counts as the same LOW is a judgement its run
  makes, so step 1a names when it runs during the trial. A LOW on a safety-critical
  path is still repaired in its pull request or ticketed. This
  reverses the ticket half of *LOW findings: delta review or ticket* in
  `fallback-review-panel.md`, so it is a change to that shared document in its own pull
  request (step 1a). The trial runs for a month from the day that merges and is judged
  against the monthly inflow in M3.
- **D4. Whether the full profile is meant for repositories other than the author's:
  undecided, and the option is kept.** So the plan neither builds for it nor forecloses
  it. The full-profile upgrade engine is deferred (step 6c). The steps both answers need
  go ahead: pinned installs (2d), the lite-first README and export (6a), and the
  adoption fixtures that keep the full install path tested. The lite-to-full move (6b)
  comes before the upgrade engine, because it is what lets a lite adopter grow into
  full. Revisit when a repository outside the author's asks for full, or when the next
  full upgrade of `in-parallel-oy/cs-toolkit` or `topij/OpenKitchen` reports new defects
  in the hand-run path.
- **D5. Annotated, calendar-named tags on `main` as the release unit: yes.** Cut one
  when an adopter upgrade is about to run and whenever a changelog fragment marked
  breaking lands. The tag message lists the fragments since the previous tag.
  Calendar names and not semantic versions: the tag message says which fragments a
  tag holds, and a calendar name orders tags without a ruling on what counts as major.
  `adopt.md` and `upgrade.md` take a ref, so pinning a bare commit keeps working.
- **D6. One shared stdlib fence scanner for the engines: yes.** Engines stay
  stdlib-only: they run as a bare `python3` from hooks and scheduled jobs, and the
  README says the runtime engines do not require PyYAML. `markdown-it-py` stays in
  `check_record_prose.py`, which is review-time tooling run through `uv`.

### Step 1. Make the backlog choosable

- **1a. The intake rule** `[S · standard · cloud]`. Write D3 into *LOW findings: delta
  review or ticket* in `fallback-review-panel.md`, with the date the trial ends, the
  safety-critical carve-out, and when `post-merge-systemize` runs during the trial.
  **Done when** the document sends a first-occurrence LOW to the disposition alone,
  and the handoff carries the date to judge the trial.
  **Tickets:** follow-ups #551, #1296, #1433.
- **1b. The pass** `[M · tracker only · cloud]`. One pass over the open issues, on the
  operator's approval of each batch, in the manner of the 2026-10 pass:

  - retire entries the tree has overtaken, after checking each against the tree; #36
    is the first to check;
  - fold overlapping reports into one after reading their bodies: #1398 with #1145,
    and #467 and #677 with #1082;
  - apply D3 to open LOW-residue tickets with no recorded recurrence;
  - give each survivor a priority label and a known execution environment (M3 counts
    the ones labelled `execution:unknown`);
  - group survivors under the steps of this plan where they belong.

  **Done when** `gh issue list --state open` returns no issue without a priority
  label, and each step below names its tickets.
  **Ran 2026-11-13**, each batch on the operator's approval; the closing comments on the
  tracker record each outcome.

### Step 2. Provenance on the unattended path

- **2a. Probe, then bind the receipt** `[M · safety-critical · local]`. First run S2
  live and record the result. The probe:

  - issues a throwaway lane with the default `operator` class, against a throwaway
    pull request whose base is a branch made for the probe, never `main`;
  - tries, from inside the lane's grants, each route to the receipt: the granted
    `pr_watch.py --record-review`, and a direct write of the state file under the
    lane's state root;
  - reads the report the merge wrapper reads at the sha under test, and records its
    `review_evidence` and `mergeable` (at `fd12e961` that report is
    `pr_watch.py <PR> --json --no-persist` under the lane's state root);
  - runs the control: the same read after the cockpit records a receipt;
  - does not run `dev_session.sh merge`, so it needs no `self` lane and merges
    nothing.

  If S2 holds: `dev_session.sh merge` takes review evidence only from a place the lane's
  grants do not reach. Once 2c has given lanes their own identity (D1), that is a
  disposition comment authored by the operator's identity. Until then it is the
  cockpit's own state root, and `record_review` refuses under a lane descriptor.
  **Done when** the same probe is refused at the new sha and still succeeds at the sha
  before it. D2's hold lifts when this ships.
  **Tickets:** #490, #1430.
- **2b. Author trust for text handed to an agent** `[M · safety-critical · cloud]`.
  `launch_lane.py --ticket` refuses an issue whose author is not the repository owner,
  a member or a collaborator, or that was edited after a time the operator passes at
  launch. `pr_watch.py --json` marks each comment with its author's association, and
  `pr-watch.md` says to act on trusted tiers and report the rest. Covers S1's inlet
  and S3.
  **Tickets:** #267, #539.
- **2c. A lane identity, isolation from the operator's credentials, a narrower
  environment and narrower grants** `[L · safety-critical · local]`. Per D1: probe a
  second account's fine-grained token against a ruleset on `main`, then have
  `launch_lane.py` hand the child that token from a configured environment variable.
  Pass the child an allowlist of environment variables instead of removing named ones.
  Isolate the child from the credentials stored for the operator: probe a separate OS
  user, a container and the runtime's own sandbox, and take the lightest under which
  code the lane runs cannot read them. Put
  a lane-side gate in front of `git push` and the `gh` grants, as #615 proposes, and
  extend it to S6's argument classes. Owes a changelog fragment for the new config key.
  **Done when** a lane launched with the shipped profile cannot merge its own pull
  request, its child's environment does not carry the operator's token, and a command
  the lane runs through `make test` cannot obtain the operator's forge credential.
  **Tickets:** #615, #617, #618, #1025, #1138.
- **2d. Pin what adopters install** `[S · standard · cloud]`. Per D5: `adopt.md` and
  `upgrade.md` take a ref, clone that ref, and print it before the first copy. Covers
  S5.
  **Tickets:** none filed.
- **2e. CI hygiene** `[S · safety-critical · cloud]`. Pin the remaining actions to
  commits, pin `pytest` and `pyyaml`, set `persist-credentials: false` and
  `timeout-minutes` on the `toolkit` job, and add `.claude/settings.local.json` to
  `.gitignore` and to what `init.sh` seeds. Covers S8 and S9.
  **Tickets:** #345.

### Step 3. One contract, one plumbing

- **3a. One merge predicate** `[S · safety-critical · cloud]`. A module under
  `scripts/lib/` exports the predicate; `dev_session.sh`, `reconcile_sessions.sh` and
  `triage/model.py` call it. It requires what the strictest copy requires today, and
  #1370's case becomes a named outcome of it. **Done when** a test fails if any of
  those files spells the field checks itself.
  **Tickets:** #319, #1370, #1371.
- **3b. `pr_watch.py` resolves state through `state_paths`** `[M · safety-critical ·
  local]`. Removes C2 and gives #1145 a single place to change. Owes a changelog
  fragment if a state path moves.
  **Tickets:** #1145.
- **3c. Defaults from one place** `[S · safety-critical · cloud]`. `pr_watch.py`'s
  built-in review defaults are generated from, or pinned by test to, the shipped
  config. Covers C3.
  **Tickets:** #40.
- **3d. One runner for `git` and `gh`, one process-group stop** `[M · mixed · local]`.
  A shared module with a timeout, error translation and one `GIT_*` policy, adopted an
  engine at a time. `launch_lane.py`'s group stop becomes the shared one.
  **Tickets:** #414, #1172, #1219.
- **3e. One fence scanner** `[S · standard · cloud]`. Per D6: one stdlib scanner under
  `scripts/lib/`, used by `archive_plan_sessions.py`, `review_eval.py`,
  `lib/systemize/normalize.py`, `lib/triage/inbox.py` and `lib/triage/model.py`. Covers
  C6.
  **Tickets:** #374, #1171.

### Step 4. CI and tests the same shape as the operator's machine

- **4a. CI runs `make test`, on Linux and macOS** `[S · safety-critical · cloud]`. Fold
  the run without PyYAML into the Makefile so that local and CI are one recipe. Add the
  Python that `uv` selects by default beside 3.12.
  **Tickets:** #1353.
- **4b. A hermetic layer in `scripts/tests/conftest.py`** `[M · standard · cloud]`. An
  autouse fixture nulls global and system git configuration, sets a temp `HOME`, and
  puts a `gh` that fails loudly first on `PATH`. Shared `git_repo` and `fake_gh`
  fixtures replace the per-file runners over later pull requests. Covers #97 and #1394.
  **Tickets:** #97, #543, #788, #1082, #1300, #1394.
- **4c. Retire the in-test triage model** `[L · standard · cloud]`. Move protocol
  checks onto the real engine's tests. Keep document pins to the two mechanisms that
  already exist: marked-clause equality and whole-file snapshot. Split
  `test_portability.py` by subject as the pieces come out. `mutation-test` is the
  check that nothing stopped being caught.
  **Tickets:** #791.

### Step 5. Less text for an agent to load

- **5a. Budgets and evidence companions for workflows** `[M · standard · cloud]`. Add
  each workflow to `doc_budgets` at its current length, so that growth trips the wire.
  Then move incident history and editor notes to `-evidence.md` companions, a workflow
  per pull request, starting with `session-start.md`, `adopt.md` and `upgrade.md`.
  **Tickets:** none filed.
- **5b. The gather as an engine** `[L · standard · local]`. One command returns the
  briefing's inputs as JSON with an explicit `unavailable` per source and paging done
  inside it. `session-start.md` shrinks to classify, check, render. Covers #1135, #663
  and #313. Lite keeps its prose gather.
  **Tickets:** #313, #663, #1135.
- **5c. Lite validation into `kit_doctor.py --verify-lite`** `[M · standard · cloud]`.
  The prose schema in `lite-wrap-up.md` becomes "run the check from the kit clone".
  Covers #1368 and #1427.
  **Tickets:** #1368, #1427.
- **5d. Correct the copies that disagree** `[S · standard · cloud]`. The pairs named
  under *Documents* and *Distribution and upgrade*, in one pull request.
  **Tickets:** #296, #358.

### Step 6. Distribution

- **6a. Lite first, tags and an export** `[M · standard · cloud]`. Per D5 and D4: the
  first calendar tag; a README whose first screen states the two profiles, who each is
  for and what full costs to keep current; a release export that leaves out
  `saved_plans/` and `docs/kit-*`. The `cp -r` route is replaced or gains its cleanup
  step.
  **Tickets:** #18.
- **6b. The lite-to-full move.** Already the Lite install profile workstream's open
  item. D4 puts it ahead of 6c, because it keeps full reachable for a lite adopter.
  **Tickets:** none filed.
- **6c. `kit_doctor.py --upgrade` for the full profile** `[L · standard · local]`.
  Deferred under D4 until one of its two revisit conditions holds. When it is built:
  generalise the lite planner, and move config migration out of interactive `init.sh`
  into a stdlib module `init.sh` calls.
  **Tickets:** #534, #1170.

### Step 7. Split the large engines `[L · safety-critical · local]`

Last, and only after 3a, 3b and 4b. By then the first two `pr_watch.py` seams are out,
and the tests' patching can be moved to the new modules a seam at a time.

**Tickets:** none filed.

### The first three

D2's hold on `self`-class lane merges is already in force. It is prose, and step 2a is
what replaces it with a mechanism.

If only three things happen next: **step 1**, because every later choice is easier
against a backlog with priorities; **step 2a's probe**, because it is small and says
whether S2 holds when run; and **step 3a**, because it is small, on the
merge path, and lets 2a's change to review evidence land in one place.

## What I would not do

- **Split `pr_watch.py` now.** The tests weld it shut (M9). Take the two seams that pay
  for themselves and leave the rest.
- **Add another prose or regex guard on documents.** `docs/kit-handoff.md` records that
  #1381's review rounds showed a prose list of config stops does not converge, and
  #1347 already asks for a parser in place of a pattern guard. Use a parser, a
  generated file, or nothing.
- **Add a security lens (#1152) before step 2.** A reviewer running with the operator's
  credentials, judging a receipt it could have written, is not the missing control.
- **Reopen the plugin route for lite.** It was tested on 2026-11-09 and set aside
  because a plugin's version pin holds per machine (#1320).
- **Tune review rounds further before #1174 lands.** The cost is not on the record.
- **Reformat the engines.** `ruff.toml` explains why they are lint-only, and every
  byte change moves the manifest (M6).

## What this assessment did not establish

- Whether S2 holds when run. It was read, not run.
- How a fine-grained token on a second account and a ruleset on `main` behave together
  (D1).
- Whether a lane can read the credentials stored for the operator on this machine, and
  which isolation stops it (D1, step 2c).
- The token cost of a review round, a lane or a session start.
- Whether an adopter other than the author can complete a full install unaided; no
  such attempt is on record.
- Whether anything runs `post-merge-systemize` on a schedule in this repository (D3).
- Whether `test_pre_push_hook.py` catches the three mutations #36 lists.
- The contents of issue bodies, except #36's opening and #1398's opening.
- Anything about `in-parallel-oy/cs-toolkit` or the lite repositories beyond what
  `docs/kit-handoff.md` says of them.
