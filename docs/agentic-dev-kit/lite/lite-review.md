# Review (lite)

A basic correctness review of a change before it is committed, for a repository on the
kit's **lite profile**. Lite repositories commit without pull requests, so this is the
review the change gets. The lite `wrap-up` runs it before its commit; run it on its own
before any other commit.

**It runs in the same context that wrote the change, and that is its limit.** The
reviewer shares the author's reasoning, so it catches what the change *says* that is
wrong more reliably than what the author *assumed*. Never report it as an independent
review. The full profile's independent review is the kit's fallback review panel, a
set of fresh-context reviewers; this is not that.

## 1 · Read the change as written, not as remembered

Take the change from the repository, not from your memory of making it:

```sh
base=$(git rev-parse --verify -q HEAD || git hash-object -t tree /dev/null)
git diff "$base"
git ls-files --others --exclude-standard
```

`base` is the empty tree in a repository with no commit yet, where `HEAD` does not
resolve.

When the lite `wrap-up` runs this review, the change is what it staged: read
`git diff --cached` instead, since its staging step has already classified every path.

**Classify each untracked path before opening it.** A path that indicates protected
content (contact exports, raw customer or CRM data, generated reports, `.env`-shaped
files) is not opened and is not part of the change: say you skipped it and why, and ask
the operator if it genuinely belongs. Listing paths is safe; reading one is what exposes
it.

Then read every changed hunk in full, and every other new file that belongs to the
change. A hunk you skip because you "know what it says" is the hunk this step exists to
read.

## 2 · Ask what it says

Take the stance of the full profile's correctness reviewer:

<!-- lite:begin correctness-focus -->
assume it works and ask what it says — stale comments, claims that overstate what is verified, tests whose names promise more than their bodies check
<!-- lite:end correctness-focus -->

Then check the changed lines for plain defects:

- a branch, case or input the change does not handle — an empty value, a missing
  file, an error path;
- a value computed and then ignored, or used before it is set;
- a name, path or key that differs between where it is written and where it is read;
- a comment, doc line or message elsewhere in the repository that the change makes
  false — search for the subject you changed, not only the lines you touched.

## 3 · Back every claim with a command

List each claim the change makes or that you are about to make about it: *the tests
pass*, *the doc matches the code*, *nothing else calls this*, *the build is clean*.
For each, run the command that would show it false, in this session, and keep its
result. A claim with no command behind it is dropped, not softened.

If the repository has no test command, say so; that is a finding about the repository,
not a pass.

## 4 · Settle every finding

Each finding is either

- **fixed** before the commit — then re-read the hunk you changed, because a fix is a
  new change; or
- **routed**, by the lite `wrap-up`'s friction step: down `friction.down_route` when it
  is fully explained, otherwise parked in the friction inbox. An edit the route writes
  in this repository is part of the commit: stage it by name, and read it as you read
  the change.

Never commit over a finding that is neither.

## 5 · Optional: a second pass from the runtime's own reviewer

When the runtime has a built-in reviewer — `/code-review` in Claude Code, `/review` in
Codex — run it on the same change as well. It needs nothing from the kit. Its findings
are settled the same way; its absence is not a gap in this review.

## Report

One line per finding with how it was settled, then the commands step 3 ran and their
results, then the stated limit:

```text
Review (lite, same context): <N findings: fixed / routed | no findings>
  • <finding> — <fixed | routed to <where>>
  Checked: <command> → <result>; …
  Limit: same-context review; not independent.
```
