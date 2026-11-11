# Wrap up (lite)

Decide whether the session left anything to hand over, record only that in the living
plan, route the friction it found, review the change, and commit. For a repository on
the kit's **lite profile**: one operator and an agent, commits on a branch (pushed as a
pull request where the repository takes changes that way), and no engines, review loop
or tracker integration.

The full profile's version is the kit's `wrap-up` workflow, which a lite install does
not carry. The clauses between `lite:begin` and `lite:end` markers are shared with it
word for word, and a kit test keeps them so; change one in the full doc and the lite
doc together.

**A session can end with nothing to hand over.** A commit message already records what
changed, and the next `session-start` reads it first-hand. A copy in the plan is one
more thing to go stale. When the test below leaves nothing and no friction is owed, say
so and make no record edit.

## Read the configuration

Read `config/dev-model.yaml` directly, as the lite `session-start` does: `<handoff>`
is `paths.handoff`, `<friction-log>` is `paths.friction_log`, `<down-route>` is
`friction.down_route` when set, and `<declared-paths>` is the list the risk tier in
[`lite-review.md`](lite-review.md) reads: `review.safety_critical_paths` as committed,
by that section's rules, never the working tree's copy. `<protected-branch>` is
`vcs.protected_branch` when set: the branch that takes changes only through pull
requests. **An absent key is a declaration, not an unknown:** the repository takes
direct commits, and the commit goes to the branch checked out without asking. A
repository whose branch takes changes only through pull requests must set the key;
`adopt` asks for it. `<backlog>` is `backlog.path` when set: the repository's own story
backlog, which the block in the lite `session-start`'s *Backlog* section reads, key and
file both. Absent or null, there is no backlog: step 1 still runs that block, which
then prints `backlog: not configured`, and every other step that names `<backlog>` is
skipped.

Read `vcs.protected_branch` from **every copy** of the config, not only the working
tree's: the committed one by the same read the risk tier uses
(`git show HEAD:config/dev-model.yaml`, or the staged file on a branch with no commit
yet), the staged one (`git show :config/dev-model.yaml`), and the working tree's file.
Otherwise an unstaged edit that deletes the key would send the commit to the branch it
protects, and the risk tier would not see it, because the tier judges only staged
paths. A copy that does not exist yet (nothing staged on an unborn branch) is skipped;
one Git cannot show is the risk tier's unreadable-config stop. `<protected-branch>` is
the branch any copy names. When the copies disagree on whether one is named, tell the
operator, and treat it as set.

Each of these is a hard stop before any edit; say which to the operator:

- a missing config file, a missing `paths` key, or an unreadable document;
- a `<declared-paths>` the risk tier cannot read, by its rules in `lite-review.md`,
  including a committed config Git cannot show: it could not tell which changes it
  covers, and guessing would skip the review it exists to require. That section names
  the way out;
- a `profile` other than `lite`, or none: this is not a lite repository, and this
  workflow does not apply to it;
- a `vcs.protected_branch` key, in any copy, that is present but unusable: null or
  empty, blank after trimming, not a string, a template placeholder still in angle
  brackets, a name holding any character other than ASCII letters, digits, `.`, `_`,
  `/` and `-`, or a name that is no branch here. Judge the characters first, by reading
  the value, before it reaches any command: a value is data, and only one that passes
  goes into these checks, in double quotes. It is a branch here when
  `git check-ref-format --branch "<name>"` exits 0 and either
  `git show-ref --verify -q "refs/heads/<name>"` exits 0 or
  `git for-each-ref --format='%(refname)' "refs/remotes/*/<name>"` prints a ref, on
  whichever remote holds it. The commit step could not tell which branch takes no
  direct commit, and guessing could commit to it;
- copies whose `vcs.protected_branch` name two different branches: the commit step
  could not tell which one the pull request targets;
- a key outside the lite config schema at any level, a key given twice at one level,
  or a section of the wrong shape, in any copy. The schema is `profile`, `kit.version`, `paths.handoff`,
  `paths.friction_log`, `friction.down_route`, `review.safety_critical_paths`,
  `vcs.protected_branch` and `backlog.path`. `paths` is a mapping; each of `kit`,
  `friction`, `review` and `vcs` is a mapping or null (a bare `vcs:` left after
  removing its optional line), and any other value, such as `vcs: main` or `review:
  [deploy/]`, is the wrong shape: read as absent, it would declare nothing it holds.
  `backlog` is held to the one form the lite `session-start`'s *Backlog* section
  declares, by the stop below. A lite repository reads no other key, so another one is most likely a
  misspelling or a misplaced line: `vsc:`, `protected-branch`, `reveiw:`, a
  `protected_branch` dedented out of `vcs`. A YAML parser keeps only the last of two
  equal keys, so a second `vcs:` left by a merge or a paste drops the first. Read as
  absent, either would silently switch off what the key was written to declare: the
  branch it was meant to protect would take the commit, or the paths it declared would
  skip the risk tier;
- a `backlog` the lite `session-start`'s *Backlog* block reports `unusable:`: not in
  the form that section declares, or a `path` that is not plain by its rules. The block
  reads the working tree's copy, which is the backlog this workflow edits; never paste
  the value into a command to check it. A `backlog.path` naming the same file as
  `paths.handoff` or `paths.friction_log` stops as well: the commit step splits those
  files from the backlog;
- no branch checked out: `git symbolic-ref --short -q HEAD` prints nothing, so a
  commit would land on a detached HEAD that no branch keeps.

**The way out of the `vcs.protected_branch`, `backlog` and schema stops above** is outside the
lite workflows, as the risk tier's is (*Risk tier* in [`lite-review.md`](lite-review.md)):
once the operator has read the config and said to go ahead, they commit the corrected
`config/dev-model.yaml` on its own. They make that commit on a new branch and open a
pull request for it, unless they say the branch checked out takes direct commits. A
committed copy is wrong until that commit lands, and editing the working tree does not
clear the stop. A stop that only the staged or working-tree copy causes clears when
that copy is corrected: restage the fixed file, or unstage it with
`git restore --staged config/dev-model.yaml`. A key outside the schema is corrected by fixing its spelling or place,
by deleting it, or, when something of the repository's own reads it, by moving its
value to a file of the repository's own: a lite config holds only the kit's keys. A
newer kit that adds a key installs, in the same change, the wrap-up that reads it. The
other stops are not the config's to fix: no `profile: lite` means this workflow does
not apply, and a missing document or a detached HEAD is fixed where it is.

## Steps

Run every command below from the repository root (`cd "$(git rev-parse --show-toplevel)"`).
The paths the configuration names are relative to it, and Git reads a path from the
current directory.

1. **Read `<handoff>` and `<friction-log>`.** Either one missing or unreadable is a hard
   stop, as it is for the lite `session-start`: name it to the operator and make no
   edit. The commit step names both paths to `git restore --staged`, which refuses a
   path that does not exist, so a missing file would leave the record edits in the
   wrong commit.

   Then run the lite `session-start`'s *Backlog* block. `backlog: not configured`
   means there is no `<backlog>`. A line beginning `unusable:` is the configuration
   stop above. A line beginning `unavailable:`, or any other non-zero exit, is a hard
   stop here, unlike in the `session-start`: this workflow keeps the backlog's
   statuses, and the plan records none of them, so a wrap-up that skipped the backlog
   would lose what the session shipped. Keep its output for the backlog step below.

1. **Review what changed this session**, since this session began, not since the plan's
   newest line:

   ```sh
   if git rev-parse --verify -q HEAD >/dev/null; then
     base=HEAD; git log --oneline -20
   elif ref=$(git symbolic-ref -q HEAD) && [ -z "$(git for-each-ref --count=1 "$ref")" ]; then
     base=$(git hash-object -t tree /dev/null)  # an unborn branch: no commit yet
     echo "no commits yet"
   else
     base=; echo "stop: HEAD does not resolve" >&2
   fi
   git status --short
   git diff "$base"
   ```

   `base` is `HEAD`, or the empty tree when the branch has no commit yet: `HEAD` does
   not resolve and the branch it names does not exist. If the block prints `stop:`, or a
   command after it fails, `HEAD` names a ref or commit that cannot be read: stop and
   tell the operator, since what the commands print then is not the change. Each block
   that uses `base` assigns it itself, because a runtime may run every block in a fresh
   shell.

1. **Run the repository's own wrap-up reads**, if its `AGENTS.md` names any for
   `wrap-up` (the deploys made this session, the pull requests merged in its service
   repositories). They count as part of what changed. A read that fails is reported as
   unavailable, never as its empty value, as the lite `session-start` says of its
   sources.

1. **Decide whether there is anything to hand over.** Ask of each thing the session
   did or learned whether a commit message, an existing plan line or a friction entry
   already records it. What is left is the plan's content, and it is short:

   <!-- lite:begin handoff-content -->
   - a **decision** with no other home — a choice between options, a scope cut, an
     operator ruling that no pull request or issue carries;
   - an **abandoned approach**, and why, when nothing else says it was tried;
   - **half-finished state** — an unpushed branch, a running job, a temporary tree,
     a review round still on disk — that the next session would otherwise trip over;
   - a **next step with no ticket**, or a change to a workstream's `▶ Next:` because
     the session finished, moved or replaced the one there;
   - a **new line of work**, or a workstream the operator closed.
   <!-- lite:end handoff-content -->

   When `<backlog>` is configured, a story's status is the backlog's record, kept by
   the step below: the plan carries no copy of it. A line that restates one, in an
   entry this session updates, is removed when it agrees with the backlog. Where they
   disagree (the plan calls a story done that the backlog does not mark `done`, or the
   other way round), show the operator both and ask which is right. Keep that line
   when you update `<handoff>`: the backlog step removes it, after the backlog holds
   the status the operator named, and it stays when they leave it open. Never remove
   it on the backlog's word alone: the plan may hold the correct record.

1. **Update `<handoff>`** with only what the test left.

   - **If `<handoff>` has a `## Workstreams` section**, keep one `### <name>` entry per
     line of work, named for its subject: a one-line status and its own `▶ Next:`.
     Update only the entries this session worked on, confirmed with the operator in
     one line.
   - **Otherwise `<handoff>` is the repository's own plan** (for example a plan another
     tool maintains). Edit its existing status and next-step lines in place, in its
     own format. Do not add sections or restructure it without asking.
   - Closing a line of work is the operator's call; ask, never infer it.

   Write claims that stay true:

   <!-- lite:begin record-prose -->
   - **A verification claim names its command and the directory it ran in.**
     "Verified" with neither is the claim a later review round exists to find.
   - **A "why this is safe" sentence cites a test that would fail if it were
     false** — or is deleted.
   - **Point, don't restate.** The issue, pull request or commit that holds a
     fact is its record; the handoff carries a pointer. Every restatement is a fresh copy to go stale.
   <!-- lite:end record-prose -->
   - **If a command prints it, do not write it.** Counts and statuses go stale; name the
     command, or drop the claim.

1. **Update `<backlog>`**, when it is configured, for each story this session worked
   on. Set `doing` on a story it started and did not finish, and `done` on one it
   finished: every acceptance line this session could check was checked, by a command
   or a person, and passed. The rule below on completion applies: a commit message or
   a branch name says a story was attempted, not that it is done. Keep the file's own
   convention for the note after the word (`Status: done (<date>; <what checked it>)`
   in the bama format), change no other line of a story, and confirm the changes with
   the operator in one line. A story the session added, or one it found no longer
   wanted, is changed only on the operator's word (`dropped`). So is a story whose
   status the plan disagreed with, settled above: set the status the operator named,
   even when this session did not work on the story, with a note that names the
   operator's word as what checked it (`Status: done (<date>; the operator's word)`).

   A story this session worked on whose status the block reported as a problem is not
   guessed at: show the operator its `problem` line and ask. Then run the block again:
   the edit must add no `problem` or `blocked` line, and every other story's `story`
   line must read as it did, apart from a status the operator settled above. The block
   reads only those lines, so check the diff as well: no line of a story the session did
   not work on changed, apart from that status line.

   Only when that check passes, remove from `<handoff>` each line the operator settled
   above; the commit step commits it with the other record edits. A line whose backlog
   edit failed, or that the operator left open, stays.

1. **Route this session's friction**, each finding when it is found. A finding that
   has all three of a **reproduction**, a **named mechanism** and a **proposed fix** is
   already actionable: take it down `<down-route>` (fix it now, or record it where that
   route says). With no `<down-route>` configured, ask the operator where it goes. A
   write outside this repository needs the operator's go-ahead on the exact content.

   **Park it in `<friction-log>`** instead — a short entry under a dated
   `## YYYY-MM-DD` heading with the observed issue, a severity (**H**/**M**/**L**) and
   whichever of the three parts you have — when either of these is true:

   <!-- lite:begin park-conditions -->
   - **Any of the three is missing.** A real **H** you cannot yet explain —
     *"something about the review felt wrong and I cannot say what"* — belongs here
     precisely *because* it has no mechanism. The inbox is where a finding waits to
     become explicable, not where a complete one waits for a sweep.
   - **The point is accumulation.** A single instance of a shape that is only worth
     acting on if it recurs needs somewhere to pile up. Friction becomes a rule
     only as a **pattern**, and a pattern is only visible once its instances share
     a home; a queue of work items is not that home.
   <!-- lite:end park-conditions -->

   When entries in the inbox share a shape, propose the rule they add up to; adding
   it to the repository's instructions is the operator's call.

1. **Validate and stage what the commit will contain.** Do this before the review below,
   so the review reads only paths that have been classified and staged.

   - Check and read the tracked changes:

     ```sh
     if git rev-parse --verify -q HEAD >/dev/null; then
       base=HEAD
     elif ref=$(git symbolic-ref -q HEAD) && [ -z "$(git for-each-ref --count=1 "$ref")" ]; then
       base=$(git hash-object -t tree /dev/null)  # an unborn branch: no commit yet
     else
       base=; echo "stop: HEAD does not resolve" >&2
     fi
     git diff "$base" --check
     git diff "$base"
     ```

     Stop on `stop:` or a failing command, as in the review step above. Read the whole
     diff for churn, duplicated blocks, secrets and edits unrelated to
     the session.
   - Stage each tracked file the session changed by name, the `<handoff>`,
     `<friction-log>` and `<backlog>` edits included (`git add -- <path>`). `git status --short` shows
     a changed but unstaged file as ` M`; the commit leaves it behind.
   <!-- lite:begin stage-by-name -->
   - **Then account for every untracked file, and stage by name.** No diff of any
     kind shows the *contents* of an untracked file, so everything above can pass
     while a new file goes unreviewed into the commit:

     ```sh
     git ls-files --others --exclude-standard
     ```

     **Classify each path before opening it — do not read the list unconditionally.**
     A wrap-up runs in repos that hold contact exports, generated reports, raw CRM
     or customer data, and `.env`-shaped files, and `--exclude-standard` only omits
     what `.gitignore` already covers, so restricted data reaches this list exactly
     when someone forgot to ignore it. Reading such a file to decide whether to
     stage it pulls it into the agent's context, a transcript, and possibly a tool
     call — an exposure that staging discipline does not undo. **For anything whose
     path indicates protected content, do not open it:** treat it as not-for-this-
     commit, leave it unstaged, and say you skipped it and why. Ask the operator if
     it genuinely needs to be in the wrap-up.

     Everything else is either part of this wrap-up — read it and stage it
     deliberately — or somebody's work-in-progress that a wildcard add would sweep
     in. **So never stage with `git add -A` or `git add .` here.** Name the paths.
     This workflow knows exactly which files it touched; a wildcard is how it
     acquires ones it did not. Note the asymmetry: *listing* the paths is always
     safe and is what the staging discipline needs, while *reading* is the step
     that carries the risk — which is why the two are separated here.

     Seeing the file is not enough on its own. On this rule's first live use the
     untracked file *was* listed, was read as "pre-existing, not mine", and was
     then swept in by a wildcard add anyway — 228 lines of someone's design note
     into a commit about something else, carried through review and merge. The
     check that works is mechanical: list them, then stage by name.
   <!-- lite:end stage-by-name -->
   - Then `git diff --cached --check` over what is now staged, which the check above
     ran before the new files were added. Fix what it reports before going on.

   <!-- lite:begin completion-inference -->
   **Never infer completion from a branch name, a commit message, a process exit
   code, or a ticket reference alone.** Each of those reports that something was
   *attempted*, and a wrap-up's job is to record what is *true*.
   <!-- lite:end completion-inference -->

1. **Review the staged change before committing it.** Run the lite review,
   [`lite-review.md`](lite-review.md), over what the step above staged (`git diff --cached`),
   the record edits included. Fix each finding or route it as above before going on.
   A fix, and the friction-log or down-route edit a routed finding writes, is staged by
   name, and the review re-reads it. When `<declared-paths>` is configured, run the
   review's *Risk tier* check over the staged change. When it prints a path, a
   declared path or the config itself, the tier applies as well: a fresh-context
   review of the staged change, and the operator's go-ahead before the commit.

1. **Commit**, on the branch checked out — unless it is `<protected-branch>`, which
   takes no direct commit. The session may have staged a config change since the
   configuration was read, so read the staged copy's `vcs.protected_branch` again
   first, by *Read the configuration*'s rules: a stop there stops here, including a staged branch that differs
   from the one an earlier copy named (the different-branches stop), and a branch it
   names where no copy named one becomes `<protected-branch>`. On `<protected-branch>`, move to a session branch first, named the way the
   repository names its branches (for example `chore/<slug>`) and confirmed with the
   operator in one line: `git switch -c <name>`. The staged change and the working tree
   come with it. Either commit everything staged
   as the session's last commit, or make two commits. Two commits need all three of:
   a branch that already has a commit, a staged change to `<handoff>` or
   `<friction-log>`, and a staged change to some other path. Check the last two:

   ```sh
   git diff --cached --quiet -- ':(top)<handoff>' ':(top)<friction-log>'; echo "record: $?"
   git diff --cached --quiet -- ':/' ':(top,exclude)<handoff>' ':(top,exclude)<friction-log>'; echo "other: $?"
   ```

   Each prints `1` when that part of the index has a staged change and `0` when it has
   none; any other value is a failed command, so stop and tell the operator. `:(top)`
   and `:/` match from the repository root wherever the shell is. When either prints
   `0`, there is nothing for one of the two commits: commit once. When the risk tier
   ran, commit once as well, so no declared path lands in a commit without its
   `Risk-review:` trailer ([`lite-review.md`](lite-review.md), *Risk tier*).

   For two, unstage `<handoff>` and `<friction-log>` first
   (`git restore --staged -- <handoff> <friction-log>`), commit the rest, then stage
   those two by name and commit them as `chore: update plan — <one line>`. The second
   commit holds only those two files; any other file a routed finding edited goes in
   the first, and so does a `<backlog>` edit, beside the work whose status it records.

1. **Push and open the pull request**, only when `<protected-branch>` is set. Push the
   branch to the remote `<protected-branch>` lives on (`git push -u origin HEAD` when
   that is `origin`). When it lives on more than one remote, ask the operator which
   one takes the pull request, and push there. Then open a pull request against `<protected-branch>` with the
   forge's own tool (`gh pr create --base <protected-branch>` on GitHub), or let the
   push update the one already open for this branch. Its description says what changed
   and the review's result; when the risk tier ran, it also carries what
   [`lite-review.md`](lite-review.md)'s *Risk tier* asks of it. Merging is the
   operator's. Report a failure rather than calling the work handed over: a push that
   fails leaves the commits local, and a pull request that fails to open leaves the
   branch pushed with no pull request. Give the command's error either way.

1. **Report** what was recorded and where, the stories whose status changed,
   what was routed, the pull request when one
   was opened or updated, the review's result (and the risk tier's, when it ran), and
   the next step for each line of work it touched — or that there was nothing to hand
   over, and which commits already say it all.

## Rules

<!-- lite:begin no-working-detail -->
- Do NOT add session working detail (debugging steps, conversation context) — that
  belongs in session-scoped scratch notes or memory, not the living handoff. A
  decision the session took is not working detail: when no pull request or issue
  records it, the entry of the workstream it bears on does
<!-- lite:end no-working-detail -->
- Do NOT change the plan's structure without asking.
- If the session changed nothing and the test left nothing, say so and make no commit.
