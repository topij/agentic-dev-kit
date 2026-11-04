# Wrap up (lite)

Decide whether the session left anything to hand over, record only that in the living
plan, route the friction it found, review the change, and commit. For a repository on
the kit's **lite profile**: one operator and an agent, commits on the branch the
repository works on, and no pull requests, engines or tracker integration.

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
is `paths.handoff`, `<friction-log>` is `paths.friction_log`, and `<down-route>` is
`friction.down_route` when set. Each of these is a hard stop before any edit; say which
to the operator:

- a missing config file, a missing `paths` key, or an unreadable document;
- a `profile` other than `lite`, or none: this is not a lite repository, and this
  workflow does not apply to it;
- no branch checked out: `git symbolic-ref --short -q HEAD` prints nothing, so a
  commit would land on a detached HEAD that no branch keeps;
- a branch that takes changes only through pull requests. Git does not record that
  locally, so ask the operator, naming the branch the command above printed, before
  the first edit. If it does, the repository has outgrown the lite profile, whose
  commit step commits straight to the branch.

## Steps

1. **Read `<handoff>` and `<friction-log>`.**

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
   - **Point, don't restate.** The tracker issue is the record; the handoff
     carries a pointer. Every restatement is a fresh copy to go stale.
   <!-- lite:end record-prose -->
   - **If a command prints it, do not write it.** Counts and statuses go stale; name the
     command, or drop the claim.

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
     *"something about the panel felt wrong and I cannot say what"* — belongs here
     precisely *because* it has no mechanism. The inbox is where a finding waits to
     become explicable, not where a complete one waits for a sweep.
   - **The point is accumulation.** A single instance of a shape that is only worth
     acting on if it recurs needs somewhere to pile up. Principle #2 routes a
     **pattern** up into a rule, and a pattern is only visible once its instances
     share a home; the tracker is not that home.
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
   - Stage each tracked file the session changed by name, the `<handoff>` and
     `<friction-log>` edits included (`git add -- <path>`). `git status --short` shows
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
   name, and the review re-reads it.

1. **Commit**, on the branch the repository works on. Either commit everything staged
   as the session's last commit, or, when the branch already has a commit, make two
   commits. For two, unstage `<handoff>` and `<friction-log>` first
   (`git restore --staged -- <handoff> <friction-log>`), commit the rest, then stage
   those two by name and commit them as `chore: update plan — <one line>`. The second
   commit holds only those two files; any other file a routed finding edited goes in
   the first.

1. **Report** what was recorded and where, what was routed, the review's result, and
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
