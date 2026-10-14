# Contributing

Thanks for wanting to help. This is a personal project (see the note in
[`README.md`](README.md)), so reviews may take a while, and some changes won't fit
however good they are. The steps below keep the round trip short.

## Before you start

- **Claim the issue first.** Comment on it to say you're taking it, and wait to be
  assigned before you write code. That stops two people from fixing the same thing.
  It matters most on `good first issue` tickets.
- **For anything beyond a small fix, open an issue first** and describe the change.
  That applies in particular to the safety-critical files listed under
  `review.safety_critical_paths` in [`config/dev-model.yaml`](config/dev-model.yaml):
  a change there gets an extra review, described in
  [`safety-critical-changes.md`](docs/agentic-dev-kit/safety-critical-changes.md).
- **Read [`AGENTS.md`](AGENTS.md).** It is the contract every change here follows,
  whether a person or an agent writes it. If you use an AI coding agent, it reads
  that file on its own.

## Setting up

You need `git` 2.44 or later, `make`, Python 3, and [`uv`](https://docs.astral.sh/uv/).
On Windows, use WSL.

```
make install-hooks   # the pre-push hook catches a stale kit-manifest.json
make test            # the verification command; it takes a while
```

`make test-fast` is fine while you iterate, but it skips some tests. The PR should
report a `make test` run.

## Rules that catch first-time contributors

- **Editing a kit-owned file means regenerating the manifest.** If the file you changed
  is listed in [`kit-manifest.json`](kit-manifest.json), run this as your last step and
  commit the result with your change:

  ```
  uv run scripts/kit_doctor.py --generate-manifest
  ```

  It writes `kit-manifest.json` itself, so don't redirect its output onto the file.
  Use this `uv run` spelling: it is the one a headless lane's profile allows. CI runs `python3 scripts/kit_doctor.py` and fails while the manifest is stale. That
  applies to a comment-only change too, because the manifest hashes bytes.
- **An observable change needs a changelog fragment.** Add a new file in
  [`changelog.d/`](changelog.d/), as `AGENTS.md` describes. A comment, doc wording or a
  test-only change needs none.
- **Change a workflow's behaviour in its shared doc** under
  [`docs/agentic-dev-kit/workflows/`](docs/agentic-dev-kit/workflows/), never only in
  `.claude/skills/` or `.agents/skills/`.
- **Only write `Closes #N`** (or `Fixes`, `Resolves`) for an issue your PR should
  close. GitHub closes it on merge.
- **Don't name a branch `dev/...`.** That prefix is reserved for the kit's own lanes.

## Opening the pull request

Fill in the template. Say how you verified the change. If you couldn't run
`make test`, say so and why; that is fine, and better than leaving it out.

The first time you contribute, CI waits for a maintainer to approve the run, so a
pending check right after you open the PR is expected.
