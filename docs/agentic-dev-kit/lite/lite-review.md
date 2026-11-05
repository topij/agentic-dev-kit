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

**A repository can declare paths that need more.** When `review.safety_critical_paths`
in `config/dev-model.yaml` lists them and the change touches one, the *Risk tier*
below adds one fresh-context reviewer and the operator's go-ahead before the commit.
Everything else still gets this same-context review alone.

## 1 · Read the change as written, not as remembered

Take the change from the repository, not from your memory of making it:

```sh
if git rev-parse --verify -q HEAD >/dev/null; then
  base=HEAD
elif ref=$(git symbolic-ref -q HEAD) && [ -z "$(git for-each-ref --count=1 "$ref")" ]; then
  base=$(git hash-object -t tree /dev/null)  # an unborn branch: no commit yet
else
  base=; echo "stop: HEAD does not resolve" >&2
fi
git diff "$base"
git ls-files --others --exclude-standard
```

`base` is `HEAD`, or the empty tree when the branch has no commit yet: `HEAD` does not
resolve and the branch it names does not exist. If the block prints `stop:`, or a command after
it fails, `HEAD` names a ref or commit that cannot be read: stop and tell the operator,
since what the commands print then is not the change.

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

## Risk tier: a fresh-context review for declared paths

Read `review.safety_critical_paths` from `config/dev-model.yaml`:

- **absent, or an empty list:** the tier is not configured; skip this section, and
  the report says so;
- **a list of non-empty strings:** each is a path the repository declares
  safety-critical — for example its firewall rules, its access configuration, its
  deploy scripts and their runbooks; go on below;
- **anything else:** stop and tell the operator. Guessing which paths it meant would
  skip the review it exists to require.

### Does the change touch a declared path?

The tier reviews the **staged** change, so stage it first. The lite `wrap-up` has
already staged it by name; run on its own, stage this change's paths by name, as
*Classify each untracked path before opening it* above says, before going on. Then
list the staged paths that fall under a declared entry:

```sh
git diff --cached --name-only -- ':(glob)<entry 1>' ':(glob)<entry 2>'
```

Write one `':(glob)<entry>'` argument per declared entry, in single quotes so the
shell does not expand it. Each entry is matched from the repository root: `*` matches
within one directory and `**` across directories, so `deploy/**` covers everything
under `deploy/` and `docs/deploy.md` covers that one file. Git narrows the diff to
these entries before it looks for renames, so a file moved out of a declared path is
listed under its old name, and one moved in under its new name.

A path printed means the tier applies to this change. Nothing printed means it does
not, and the report says `not touched`. A failed command is a stop, not a pass.

### Launch one fresh-context reviewer

Use the runtime's isolated-task mechanism: a subagent in Claude Code, a new
`codex exec` session started in the repository root in Codex. It must not see this
session's conversation. Hand it the prompt below with its placeholders filled, and
nothing else: no summary of the change, no account of what is risky, no findings
from the same-context review. Telling it what to think is what a fresh context exists
to keep out.

Fill `<stance>` with this line, word for word, which is the stance of the full
profile's adversarial reviewer:

<!-- lite:begin adversarial-focus -->
assume the change is wrong and try to prove it — bypasses, fail-open paths, wedges, and whether the new guard actually guards
<!-- lite:end adversarial-focus -->

```text
You are reviewing a change you did not write. It is staged in the Git repository
at <repository root>. Read it with:

    git -C <repository root> diff --cached --no-renames

Read each file it touches in full: as staged with
`git -C <repository root> show :<path>`, and as it was before with
`git -C <repository root> show HEAD:<path>`. A file the change adds has no
earlier version, and one it deletes has no staged version. The repository
declares these touched paths safety-critical: <the paths the check above printed>.

Your stance: <stance>.

For a change like this, look in particular for:
- a fail-open path: a check, rule or guard that lets something through when its
  input is missing, empty, malformed or unreachable;
- exposure: a port, service, secret, credential or file that becomes reachable
  or readable by more people or hosts than before;
- lock-out: a change that could cut the operator off from the system it
  configures, with no stated way back;
- a step that cannot be undone, taken without a backup or a check first.

Rules:
- Do not edit, stage, commit or delete anything in the repository. To run
  something, copy what it needs to a temporary directory outside the repository
  and run it there.
- Run what you can instead of only reading: a config checker, a dry run, a test.
- Name the command behind every claim you make.

Report, in this order:
1. What you reviewed: the commands you ran and the files you read.
2. Findings, most severe first, numbered F1, F2 and on, each with a severity
   (high, medium or low), the file and line, and your evidence.
3. What you checked and found clean, and how.
4. A last line of exactly `Verdict: clean` if you have no finding, and otherwise
   `Verdict: findings`.
```

If the runtime cannot start an isolated reviewer, say so to the operator, answer the
prompt's questions yourself in this session, and record the verdict as
`not independent`. Do not describe that pass as a fresh-context review.

### Settle the findings, then ask the operator

Settle each finding as *4 · Settle every finding* above does: fixed or routed. A fix
is a new change, so stage it and run the tier again with a **new** reviewer over the
new staged change, not the earlier one resumed. If a second pass still reports a high or medium finding that
is neither fixed nor routed, stop fixing and hand the decision to the operator.

Then show the operator the reviewer's report and its verdict, and commit only on
their explicit go-ahead. The verdict informs that decision; it is not the decision.
Where the operator merges pull requests in this repository, the go-ahead is that
merge.

### Record the verdict on the commit

The commit that holds the declared paths ends its message with a trailer:

```text
Risk-review: fresh-context adversarial — <clean | findings settled | not independent>
```

`clean` means the last pass reported no finding; `findings settled` means each finding
was fixed or routed, and the commit body lists each one with how it was settled;
`not independent` means no isolated reviewer ran. `git commit --trailer
"Risk-review: …"` adds it, or write it as the message's last paragraph.

## Report

One line per finding with how it was settled, then the commands step 3 ran and their
results, then the risk tier's result, then the stated limit:

```text
Review (lite, same context): <N findings: fixed / routed | no findings>
  • <finding> — <fixed | routed to <where>>
  Checked: <command> → <result>; …
  Risk tier: <not configured | not touched | <verdict>, operator go-ahead <given | pending>>
  Limit: same-context review; not independent.
```

The `Limit` line describes the same-context review. When the risk tier ran a
fresh-context reviewer, the `Risk tier` line is where that independent pass is
reported.
