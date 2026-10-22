# The reviewer eval

The kit changes its reviewer often: a lens's `focus`, `lens_compute`'s model and effort,
`panel_prompt.py` itself. Until `#1156` it had no way to tell whether such a change made
review better or worse. This directory holds a case set built from the kit's own review
misses, and `scripts/review_eval.py` scores the lenses against it. The idea and its
shape come from *How the Claude Code team does code review* (claude.dev, 2026-10-15):
every miss becomes a case, the reviewer runs against the whole set, and a change to it
is kept only when the score holds or rises.

## The case set

[`cases.yaml`](cases.yaml) has two lists.

- **Bug cases** are a pull request's diff (`base`, `head`) that a review should have
  flagged, with the known findings as `path` and `lines` at the head and the issue they
  come from. `confirmed` says who checked the case against that issue and how. An
  unconfirmed case is scored, but reported apart from the confirmed set.
- **Clean cases** are diffs no known defect came from. Every finding a lens reports on
  one is a candidate false alarm. Read each before counting it: the measure that matters
  is a false alarm that would lead an author to a harmful change.

Add a case whenever a review miss is found: a finding that landed after the merge, a
defect a later pull request fixed, an issue named after something a lens should have
caught. Use full shas from the protected branch's history, and the lines at the head.

## Running it

The runner needs the kit's full history (`git fetch --unshallow` in a shallow clone)
and an expanded `scratch.roots` entry. Per lens and case it allocates a review round,
builds a fresh repository there holding only the case's base and head history, detached
at the head, renders the same prompt a real round gets, runs your command in that tree
with the prompt on stdin, keeps its stdout as the report, kills the command's process
group, and retires the round. A process that left the group (`setsid`) is out of reach
of that kill: if one still holds the command's output, the run stops with exit 1 and
leaves that round in place, unretired, for you to retire once the process ends. A
command that exits non-zero or prints no report also stops the run with exit 1, since an
empty report would score as a clean case with no false alarms.

Run it from a kit checkout with no uncommitted or untracked changes: a lens's `focus` is
read from the working tree and the result is stamped with its `HEAD`, so the runner
refuses a dirty checkout. The engines run from the checkout the script itself is in;
when that is not `--root`, the result's `engine_checkout` records its revision and
whether it was dirty. A run that stops on a case still writes `result.json` under
`--out`, with `complete: false` and what it scored before the failure, and a run
removes an earlier run's `result.json` there before it starts.

**The tree hides the answer, the sandbox does not.** A linked worktree would share the
kit's refs and objects, so a lens could find the fix commits or this case file in its
own history; the fresh repository has neither, and every case shows the lens the same
branch name, `review-eval/case`. The prompt's repository line is withheld, since a local
origin would name the kit checkout itself. The runner does not confine the command,
though: a lens that reads outside its tree can still open the kit checkout, and the
preflight invocation names the kit revision, so a lens with network access can look the
fix up. Give the command a sandbox that keeps it in its working directory and off the
network where the runtime has one, and read a hit whose report cites files outside the
diff with that in mind. On Codex,
`--sandbox workspace-write -c sandbox_workspace_write.network_access=false` does both.
In the first recorded Codex run, a lens that had network fetched the current `main` into
its scratch copy.

```sh
uv run <engine-dir>/review_eval.py --runtime claude \
  --scratch-root <expanded scratch.roots entry> --out <dir outside the repo> \
  --lens-command '<command that runs one lens>'
```

**The command applies the compute**, as it does in a real round (*What compute a lens
gets* in [`fallback-review-panel.md`](../fallback-review-panel.md)). On Codex,
`codex exec` with `-m <model>` and `-c model_reasoning_effort=<level>` applies both. On
Claude Code, `claude -p --model <model>` applies the model, and the effort is the
session's. The command must let the lens read files and run `git` in the tree, since
the contract asks it to. The result records the command verbatim beside the score.

Run it once per runtime. `--lens` and `--case` narrow a run, and `--timeout` bounds each
lens run.

## Reading the score

`result.json` has a `summary` per lens: confirmed bug cases and hits, unconfirmed bug
cases and hits, clean cases and their candidate false alarms. A hit means the report
cited `path:line` overlapping a known finding's lines, in a citation at most 40 lines
wide. A clean case's candidate false alarms are the `F<n>` numbers that open a line of
its report, or, in a report that numbers none, its distinct citations. Neither count
reads a section the lens contract has it write about what it checked (*Verified clean*,
*What I reviewed*, *Executed* and the like), so a line it cleared is not a hit. A
heading whose title opens with that name opens such a section, and a bold label that
is the name, such as `**Executed:** ran it`, drops only its own line. A section runs to the next heading or
to the next paragraph that opens with an `F<n>` number, so a finding listed after it
without a heading of its own still counts, and so does a paragraph there that opens
with an earlier finding's number to clear it. That is a proxy. A report can cite the
right lines for the wrong reason, or describe the bug without a citation, so
read each case's `matched_citations` and report before recording the score.

A score is a reading. Record it where the change is decided, in the pull request that
changes a lens, stamped with the runtime, the command, `kit_revision` and the date.

## What it does not do yet

- It runs no verifier. Whether the verifier (*Verifying findings*) improves a round is
  measured by running the same cases with and without it, and that comparison is still
  owed (`#1155`, `#1156`).
- It does not judge false alarms. The clean cases' counts are candidates until someone
  reads them.
