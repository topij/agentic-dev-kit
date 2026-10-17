## Allocate and retire managed review rounds

Before assembling a reviewer prompt, allocate a fresh round with
`sweep_scratch.py --create-review-round <expanded-scratch-root> --head <full-sha>`.
Retain its JSON receipt outside the round and build each detached lens tree as a
direct child. `panel_prompt.py` now requires `--scratch` and refuses unmanaged,
aliased or wrong-head allocations.

After saving evidence and ending reviewer processes, remove registered lens
worktrees, preview `--finish-review-round <receipt>`, then apply it with
`--apply --reviewers-finished`. Report any kept round; dependency protections
still apply. Ordinary age sweeps retain their grace window and approval policy.

Use `sweep_scratch.py --disk --json` for session-start and wrap-up reporting.
Add the installed sweep engine path to your `review.safety_critical_paths` and
runtime safety-rule bindings. Keep configuration roots limited to disposable
scratch; unmanaged historical temp directories need separate investigation.
