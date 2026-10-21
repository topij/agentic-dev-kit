## `panel_prompt.py --last-reviewed` refuses a sha older than the branch's fork point

CHANGED (engine CLI surface): `--last-reviewed <sha>` now exits 2 unless
`git merge-base <base> <head>` is an ancestor of `<sha>` or equal to it (#1166). Two
cases that rendered before are refused: a base-branch commit from before the pull
request, and a head reviewed before the branch merged the base. For the first, pass
the `--head` of the last recorded receipt. For the second, run that round as a full
pass without `--last-reviewed`.
