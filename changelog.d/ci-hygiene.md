## `init.sh` adds `.claude/settings.local.json` to `.gitignore`

`./init.sh` now appends `.claude/settings.local.json` to `.gitignore`, on every run
that does not find that exact line already there. It is a hygiene line like
`config/*.local.yaml`: it is added whether or not the file exists, and whether or not
`.gitignore` already carries another rule about `.claude/`.

What you must do depends on what your repository holds:

- **You do not track the file.** Run `./init.sh` (an upgrade's Step 2 does) and commit
  the `.gitignore` change. If you would rather not run it, add the line by hand.
- **You track the file on purpose.** Nothing breaks: git ignores only untracked paths,
  so the tracked file stays tracked and its edits still show.
- **You tracked it by accident.** The line does not untrack it. Run
  `git rm --cached .claude/settings.local.json` and commit that removal.
