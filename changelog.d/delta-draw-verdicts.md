## Review: a `fallback:delta` receipt needs both draw verdicts from each lens

CHANGED (gate semantics, CLI surface): `scripts/pr_watch.py --record-review
fallback:delta` now refuses, with exit 2, unless `--disposition` is given and holds,
for each lens `--lenses` names, a block opened by a line that is exactly `<lens>:`
with one line beginning `prose-class:` and one beginning `safety-critical:`, each
followed by `confirmed` or `disputed`. Lines between and around the blocks, such as
`repair:` lines, are posted unchanged. The refusal comes before any forge read, so a
refused call posts no comment and writes no receipt.

What to do: record a delta pass with `--disposition -` and paste each lens's verdict
lines on stdin under its name, for example:

```text
correctness:
prose-class: confirmed — <reason>
safety-critical: confirmed — <reason>
```

A delta receipt recorded without `--disposition`, or with the verdicts posted in a
separate comment, is now refused. Take `scripts/pr_watch.py`, its test file
`scripts/tests/test_pr_watch.py` and `scripts/panel_prompt.py` together: a test holds
the engine's draw names equal to the ones the lens prompt asks for.
