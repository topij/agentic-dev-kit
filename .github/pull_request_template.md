## What this changes

<!-- What a reader would notice, in a sentence or two. -->

## Issue

<!-- "Closes #N" only if merging should close it; otherwise "Refs #N". -->

## Verification

<!-- The command you ran and its result, e.g. "make test at <sha>: passed".
     If you could not run make test, say why. -->

## Risk

<!-- What breaks if this is wrong, and for whom. Say whether it touches a file
     under `review.safety_critical_paths` (a gate, a destructive operation, CI,
     a hook script or a hook registration) or a contract adopters pin. -->

## How to revert

<!-- How to undo this after merge: revert the commit, and what else an adopter
     who already took the change must restore (kit-owned files, config keys,
     state files). "Revert the commit" is a fine answer when it is the whole
     answer. -->

## Checklist

- [ ] I was assigned the issue, or opened one first for a larger change
- [ ] If I edited a file listed in `kit-manifest.json`, I ran
      `python3 scripts/kit_doctor.py --generate-manifest` and committed the result
- [ ] If the change is observable to adopters, I added a `changelog.d/` fragment
- [ ] If I touched a file under `review.safety_critical_paths`, I said so under Risk
