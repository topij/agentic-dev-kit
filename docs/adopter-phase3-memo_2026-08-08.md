# Memo to the next devkit session — what cs-toolkit's Phase 3 established

> Written 2026-08-08 from inside cs-toolkit, alongside
> `in-parallel-oy/cs-toolkit#1883` (Phase 3 — "converge the install").
>
> **The evidence rule, stated precisely enough to be checkable.** Every claim about
> the *state of a file or repository* names the command that produced it and the
> directory it ran in. Claims of three other kinds appear here too, and each is
> labelled rather than dressed up as a measurement:
>
> - **Observed in-session** — something that happened while working, with no command
>   to re-run (e.g. the follow-through hook firing on this PR's own `gh pr create`:
>   the reminder arrived as `PostToolUse` context, which is the observation).
> - **Judgement** — why something was carried rather than fixed. The *facts* under a
>   judgement carry provenance; the decision itself is a call, not a measurement.
> - **Unsettled** — in *Open questions*, never in the findings.
>
> This paragraph is narrower than the one it replaces, which claimed a command for
> *every* claim. A reviewer pointed out that two classes of statement here could not
> honour it — and a rule the document itself breaks is worse than no rule, since it
> teaches the next reader to skim the provenance rather than check it.
>
> **Scope discipline**, inherited from the Phase 0 memo because it was that
> memo's best feature: this is *what the kit must do*, ordered by what blocks an
> adopter. Items that merely improve the kit are marked **[improves]** and sorted
> last.
>
> **Method note, inherited from that memo's two errors.** Phase 0's memo made one
> false claim from a kit *document* (`adopt`/`upgrade` unextracted — already done
> by #330, nearly buying a sprint) and one from a plausible guess about the kit's
> *tests* ("no coverage of the hook registrations" — there were two; the real
> defect was that they compare text). So: nothing here is sourced from
> `kit-convergence-plan.md`, `kit-handoff.md`, or an issue body. Every statement
> about the kit was re-derived against the filesystem at `7baca48`.

## Were the briefed preconditions true? Yes — both, and here is the check

The session was handed two load-bearing assertions. Both held.

**1. `adopt.md` and `upgrade.md` were declined and absent.** True.
`python3 -c "import json; ..."` over `cs-toolkit/kit-manifest.json` returned
`in not_installed=True` for both, and `ls docs/agentic-dev-kit/workflows/` listed
only `parallel-headless.md`, `parallel.md`, `pr-watch.md`, `session-start.md`,
`wrap-up.md`. So a Phase 3 session there genuinely had no installed procedure to
follow — it would have improvised the workflow the kit exists to standardise.

**2. The vendored `kit_doctor.py` was blind to `init.sh` until refreshed.** True,
and it is worth stating precisely *why*, because the mechanism generalises.
AST-parsing the `KIT_OWNED` tuple out of each copy (not grepping — `init.sh`
appears 36 times in the vendored engine as prose in usage strings, which is
exactly how a grep-based check would have concluded the opposite):

| copy | `KIT_OWNED` entries | `init.sh` tracked |
|---|---|---|
| `cs-toolkit/scripts/devkit/kit_doctor.py` (before) | 35 | **no** |
| `agentic-dev-kit/scripts/kit_doctor.py` @ `7baca48` | 36 | yes |

**`KIT_OWNED` lives in the engine, not the manifest.** Passing `--manifest
<kit>/kit-manifest.json` does not backport a newly tracked path, so no amount of
manifest freshness would have let the old engine see the installer. Refresh the
engine *before* measuring anything, or the measurement is silently narrower than
it reports.

## A third precondition was stated and was NOT current — check HEAD yourself

The brief said the kit was "on main at `796e16a`". At session start
`git rev-parse --short HEAD` in `/Users/topi/Coding/agentic-dev-kit` returned
**`7baca48`**, two commits ahead.

It did not matter — `git diff --stat 796e16a..HEAD` showed three files, all
documentation (`kit-friction-log.md`, `kit-friction-log-archive.md`,
`kit-handoff.md`), so no engine, manifest or registration moved. But the general
form is the point, and it is the same lesson the Phase 0 memo learned the
expensive way: **a commit named in a brief is a claim with a timestamp.** The
baseline recorded by this phase stamps `7baca48`, not `796e16a`.

## The invariant that made `init.sh` safe to replace

`shasum -a 256` on `cs-toolkit/init.sh` and on `git show 7485512b:init.sh` in the
kit both returned `01f7ea7ea6048c7ef382ad17603f843b1286ca36835a6849193847f58abf7ac7`.

That single fact is what licensed replacing the file outright: byte-identity with
a known kit commit proves the *entire* delta is version drift and none of it is
local rendering, **at any size**. The kit's own plan document previously carried
"852 differing lines" for this, which was stale within the day. A hash match does
not go stale. Prefer it.

Corollary the adopter acted on: the local `init.sh` predated #301/#303/#359, so
running it would have printed a registration advisory with no `--runtime`, the
pre-Phase-0 `scripts/hooks/` path, and none of the empty-string guard —
re-forking precisely what Phase 0 un-forked. **It was replaced, never run.**

## Findings that block an adopter — ordered

### 1. `kit_doctor` cannot measure the registrations the hook depends on — [#379](https://github.com/topij/agentic-dev-kit/issues/379), new

`.claude/settings.json` and `.codex/hooks.json` are in neither `KIT_OWNED` nor an
adopter's manifest, so the doctor can report a byte-perfect install while the hook
is dead. Established by AST-parsing `KIT_OWNED` (`registration entries: NONE`,
`test entries: NONE`) and scanning `cs-toolkit/kit-manifest.json` (no key matching
`settings.json`, `hooks.json`, or `test`), against the same run's
`16 unchanged, 0 differ, 0 missing, 0 unknown`, exit 0.

**This is #360's shape applied to the registrations.** #360 was "the file that
performs the install is outside the measurement." This is "the files that decide
whether the kit's one mandatory mechanism fires are outside it too." We have now
hit that class twice — #359 and #368 — and in both the operator-visible symptom is
a hook that silently stopped firing.

Note the ownership subtlety, because "just add them to `KIT_OWNED`" is wrong: these
files are legitimately the adopter's, which is *why* `init.sh` only prints them
(#303). Hashing them would report every adopter permanently `locally-edited`, which
is #286's failure. The tractable question is whether the registration **resolves**,
not whether it matches: a check that extracts the quoted hook path, expands the
repo-root placeholder, and asserts the target exists would have caught both #359
and #368 without hashing anything.

The only reason cs-toolkit catches this class is a hand-written, **adopter-local**
`tests/test_pr_followup_hook.py` that resolves the hook *from each registration*
and executes it. `KIT_OWNED` tracks no tests, so no other adopter has it.

### 2. SessionStart reaches Claude only, and there is no shape to copy — [#380](https://github.com/topij/agentic-dev-kit/issues/380), new

`grep -n "SessionStart" init.sh` → no match. `grep -rn "SessionStart" .codex/
docs/agentic-dev-kit/` → no match. `.claude/settings.json` carries the two-hook
block; `.codex/hooks.json` has `PostToolUse` only. The convergence plan assigns
this to the kit but no issue tracked it (searching `SessionStart` across all
issues returns #14, #161, #301 — none of them this).

The consequence for Phase 3 is that **the adopter could not do this half of its
own step 5 without inventing a shape**, which is the definition of a fork. It was
carried instead; see *Deliberately carried*.

One correction to the plan's question 3 while here: it assumed Claude's
`startup`/`resume`/`clear` matcher shape transfers, from documentation. The
`SessionStart` entry in this machine's `~/.codex/hooks.json` — written by a
shipping third-party integration — carries **no `matcher` key at all**. Worth
establishing before anyone writes the registration.

### 3. #359 closed one registration, not the class — [#363](https://github.com/topij/agentic-dev-kit/issues/363), already open, commented

The asymmetry is now concrete and I added it to #363 rather than opening a
duplicate: at `7baca48` the **Claude** registration is
`python3 "$CLAUDE_PROJECT_DIR/scripts/hooks/pr_followup_hook.py" --runtime claude`
— no `2>/dev/null`, no `[ -n ... ]` — and
`grep -n "def test_the_claude_registration" scripts/tests/test_init_sh.py` returns
nothing, while the Codex registration now has four executed tests. **The untested
registration is the unguarded one.** Reachability is lower (Claude Code sets
`CLAUDE_PROJECT_DIR`), but "lower reachability" was also the pre-ship assessment
of #359.

> **This corrects the Phase 0 memo's second error, in the direction that flatters
> the kit.** That memo said the kit had "no coverage of the hook registrations."
> False then, and further from true now: `scripts/tests/test_init_sh.py` contains
> `test_the_codex_registration_survives_a_git_less_tree`,
> `..._execs_rather_than_forking_the_interpreter`,
> `..._guards_a_git_that_fails_while_printing_a_path`, and
> `..._guards_an_empty_root_that_git_reports_as_success`. I nearly re-published
> the same claim from memory before grepping. Grep first.

## [improves] Findings that do not block

### 4. `kit_doctor` nags forever about a declined `pre-push` — [#381](https://github.com/topij/agentic-dev-kit/issues/381), new

`'scripts/hooks/pre-push' in not_installed` is `True` in cs-toolkit's manifest, yet
the same report prints `⚠ pre-push hook: NOT installed — run ./init.sh` three lines
above `✓ intact for this adoption — 20 file(s) declined`. The narrative check was
never taught about `not_installed`, so #286's failure survives in that code path.
The decline is principled and permanent here (kit #46), so the warning can never be
cleared — and a permanent warning is how the next real one gets skimmed past.

### 5. The convergence plan's Phase 3 text would have caused a bad install

Phase 3 says "Engines per cs-toolkit's declared Phase 2." The adopter does not
declare a "Phase 2" — `config/dev-model.yaml` declares **2A** (done: the review
engine + adapters) and **2B**, deferred with a reason. A session following the plan
literally would install the kit's `dev_session.sh`. Reading the two files:
`grep -n "CS_TOOLKIT_STATE_ROOT" cs-toolkit/scripts/dev_session.sh` matches at
lines 8, 12, 72, 241, 269, 321 — including `export CS_TOOLKIT_STATE_ROOT="$sandbox"`
— while the same grep against `agentic-dev-kit/scripts/dev_session.sh` returns
**nothing**. So the literal reading swaps out a state-sandbox contract and its
destructive-path guards.

The plan also contradicts itself on step 5: *Immediately, in parallel* assigns the
Codex SessionStart hooks to **the kit**, while *Phase 3* lists "SessionStart wiring
on both runtimes **there**" as adopter work.

This is the same class the plan's own closing section names — stale or imprecise
plan text that a reader acts on. It cost nothing here only because the adopter's
config was read first and disagreed loudly.

## Deliberately carried, not fixed locally

Phase 0 established that carrying a defect keeps it a kit debt with a named owner,
whereas fixing it downstream starts a fork. Its handling of #359 is the precedent
that worked: carried in Phase 0, shipped by the kit, **taken here in Phase 3**.

| Carried | Why | Owner |
|---|---|---|
| Claude registration hardening | Fixing it downstream re-forks a registration the kit is about to change | #363 |
| Codex SessionStart hooks | No kit shape exists to adopt; inventing one is a fork | #380 |
| The kit's `dev_session.sh` (Phase 2B) | Would replace `CS_TOOLKIT_STATE_ROOT` + destructive-path guards the kit's copy lacks — the underlying fact is the paired `grep -n "CS_TOOLKIT_STATE_ROOT"` in finding 5 (6 matches in the adopter's copy including `export …` at line 241; **zero** in the kit's); that the swap is therefore unsafe without operator review is a judgement | adopter's own 2B |
| The kit's `pre-push` | All-or-nothing; adopter's carries two guards no config key expresses | #46 |
| All 8 actionable review findings, plus 1 nitpick, on kit-owned files | Fixing any would fork a byte-identical file and make the adopter's doctor report `locally-edited` forever | #382, #383, #343 |

Each is recorded with its reason in `cs-toolkit/config/dev-model.yaml`, so the next
session there finds the reasoning rather than a bare absence.

## The adopter's review bot audits the kit — and that is a mechanism, not a bonus

CodeRabbit reviewed `#1883` and posted **8 actionable findings plus 2 nitpicks. Every
actionable one landed on a kit-owned file** — `adopt.md` (2), `upgrade.md` (3),
`init.sh` (2), `kit_doctor.py` (1). **Zero** landed on the four files cs-toolkit
actually owns and authored in this PR.

That distribution is worth staring at. Kit-owned files enter an adopter's diff *only*
at install or refresh, and when they do, a review bot with no loyalty to the kit reads
them **against the adopter's stated contract**. That is a review pass the kit cannot
run on itself, because in the kit's own repo these files are never in a diff.

None were fixed downstream — each would have forked a byte-identical file and made
this repo's doctor report `locally-edited` in perpetuity — so all were routed here:

| Finding | Routed to | Verdict |
|---|---|---|
| `adopt.md:147`, `upgrade.md:15` — both still say `init.sh` is manifest-untracked | **[#382](https://github.com/topij/agentic-dev-kit/issues/382)**, new | real, and the most valuable of the batch |
| `init.sh:166` — `comment_idx` mishandles `\"` in double-quoted YAML scalars | **[#383](https://github.com/topij/agentic-dev-kit/issues/383)** item 1, new | real correctness bug in the installer |
| `kit_doctor.py:345` — role-filter comment describes behaviour the code lacks | **[#383](https://github.com/topij/agentic-dev-kit/issues/383)** item 2 | real |
| `adopt.md:20`, `upgrade.md:42` — unpinned mutable `HEAD` cloned to a fixed `/tmp`, then executed | comment on **#343** | real; adjacent to #343's existing scope |
| `init.sh:910-936` — duplicated paragraph | comment on **#383** | trivial |
| `upgrade.md:54` — "use `scripts/devkit/kit_doctor.py` in the fallback" | **declined** | **wrong** — see below |
| `init.sh:1461` — "add the entry-point templates with `KIT_OWN_MARKER`" | **declined** | describes the intended configuration |

**#382 is the one to act on first.** Both documents tell an operator that `init.sh` is
manifest-untracked — `adopt.md:147` "it does not affect the baseline", `upgrade.md:15`
"`kit_doctor` cannot report the drift either (`#339`)". #362 falsified both, and these
are *instructions*, not background: they tell the next adopter not to check the
installer, which is precisely what #360 was closed to make checkable. The tracking
changed in the engine and the manifest; nothing swept the prose, and nothing could —
there is no check binding a workflow doc's claim to the behaviour it describes.

**The declined finding worth recording**, because the confusion is instructive:
CodeRabbit proposed rewriting `upgrade.md`'s fallback to
`/tmp/agentic-dev-kit/scripts/devkit/kit_doctor.py`. But `/tmp/agentic-dev-kit` is a
checkout of **the kit**, whose own layout is `scripts/kit_doctor.py` —
`ls <kit>/scripts/devkit/kit_doctor.py` is ABSENT. It had absorbed `scripts/devkit`
from the PR's own contract (that is *cs-toolkit's* `paths.engines`) and applied it to
the kit. The suggestion would have pointed a documented command at a path existing in
no kit checkout. A careful reader conflating an adopter's engines path with the kit's
own layout is itself a signal: that sentence is teaching exactly this distinction and
could mark it more loudly. Adjacent to #358 and #316.

**One nitpick was on cs-toolkit's own code and was right**, so it was fixed here
(`e47b4cf`): the new git-less-tree test asserted only `not (tmp_path/".git").exists()`,
but `--show-toplevel` walks the *whole* ancestor chain, and `run_registration_via_shell`
copies `os.environ`, so an inherited `GIT_DIR`/`GIT_WORK_TREE` or any work tree above
pytest's tmpdir would fail the test for reasons unrelated to the guard. Demonstrated
load-bearing rather than assumed — with an ancestor made a git repo, the registration
run from a child gives `exit 2` without `GIT_CEILING_DIRECTORIES` and `exit 0` with it.
The test had been passing on an environmental accident (`/private/tmp` is not a repo
here), not on a property of the test.

## Open questions — unsettled, not findings

**1. Does Codex read a PROJECT-level `.codex/hooks.json` at all, and fire
SessionStart from it?** Not settled, and it is not settleable on the adopter's
host. A probe repo (`git init`, `.codex/hooks.json` with a sentinel-writing
SessionStart hook) produced no sentinel, but the run died first.

`codex --version` → **`codex-cli 0.42.0`**. Probe repo: a throwaway `git init` tree
under this session's scratchpad (`.../scratchpad/codexprobe1`), NOT the adopter
checkout — deliberately, so no agent ran loose in a tree with uncommitted Phase 3
work. Run from that directory:

```console
$ codex exec --sandbox read-only "Reply with exactly: OK"
ERROR: unexpected status 400: {"detail":"The 'gpt-5.6-sol' model requires a newer
version of Codex. Please upgrade..."}
```

`-c model=gpt-5` fails differently (`not supported when using Codex with a ChatGPT
account`), and `codex debug --help` lists only `seatbelt` / `landlock` — no hooks
introspection. So the absent sentinel does **not** distinguish "project-level hooks
are not read" from "the session never started". Needs a host with a working Codex CLI.

**2. Therefore: cs-toolkit's Codex `PostToolUse` hook has never been observed
firing *by Codex*.** This bears directly on how Phase 0's and Phase 3's done-when
should be read, so it should not stay implicit. Both phases verified the hook by
**executing the registration command string through a real shell** — which proves
the command, the path, the guard and the hook all work, and is what the 26-test
adopter suite does. Neither verified that *Codex dispatches it*.

On Claude the distinction is closed — **observed in-session**, so flagged as such
rather than given a command to re-run: the follow-through hook fired unprompted when
this work ran `gh pr create` for `#1883`, from the installed path, and its reminder
arrived as `PostToolUse` context. That *is* the observation; there is no way to
re-derive it after the fact except by opening another PR. On Codex it remains open,
and #379 is the reason nothing would tell you if it were broken.

**3. Phase 0's unsettled observable (#364) did not recur.** No session was observed
invoking a stale hook path during Phase 3. That is one clean run, not evidence of
absence — the path did not move in this phase, which is probably why.

## What this phase says about the forcing function

Phase 0 predicted that upgrading a real adopter surfaces kit issues that reasoning
about adopters does not. Phase 3's score, stated plainly rather than favourably:

- **Five new issues** — #379, #380, #381 from the work itself; #382, #383 from the
  review pass — plus concrete instances added to three open ones (#363, #343, #287).
- **#379 is the interesting one**, for the same reason #360 was: it is not an
  addition to a list, it is the *same structural blind spot* the previous phase
  found, in a place nobody looked. #360 was "the installer is outside the
  measurement." #379 is "so are the registrations." Both were found by moving or
  touching the thing, never by reading about it. **A third look is warranted:
  what else does the doctor depend on that it cannot see?** That question, not the
  issue count, is this memo's main output.
- **#382 exposes a second-order cost of fixing #360** that nobody budgeted: changing
  what the manifest tracks silently falsified two workflow documents, and the change
  shipped anyway because prose has no test. Every future `KIT_OWNED` change carries
  the same tax.
- **The adopter's review bot is a kit instrument.** Every actionable finding landed on
  a kit-owned file and none on the adopter's own. That is not luck — it is what
  happens when files that are never in a diff at home finally appear in one, judged
  against a contract they did not write. If that generalises, the kit gets a free
  audit each time an adopter installs or refreshes, and **the audit is only free if
  the adopter is disciplined about not fixing the findings locally.** Every one of
  those fixes would have been a fork.
- **Two of the pre-review items were already tracked** (#363, #287), a healthier ratio
  than Phase 0's, which suggests the tracker is catching up with what adopting costs.
