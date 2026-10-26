## Review: a `fallback:delta` receipt needs both draw verdicts from each lens

CHANGED (gate semantics, CLI surface): `scripts/pr_watch.py --record-review
fallback:delta` now refuses, with exit 2, unless `--disposition` carries each named
lens's draw verdicts. The rules, with surrounding whitespace and case ignored:

- A line holding only a lens-name-shaped word and a colon (`correctness:`), other
  than a draw name, is a header. A header for a lens `--lenses` names opens a block for that lens. Any
  other header, or a blank line after the block's first non-blank line, ends it.
  A lens may have several blocks.
- Across its blocks, each named lens needs exactly one line beginning
  `prose-class:` and one beginning `safety-critical:`, unadorned (no bullet, quote
  or bold), each followed by the whole word `confirmed` or `disputed`. Only that
  word is checked: the prompt's literal unfilled `confirmed|disputed` template is
  refused, `confirmed or disputed` counts as confirmed, and the reason after the word
  is not checked.

A refusal names each draw line it saw but did not count, and why. Other lines, such
as `repair:` lines and text around the blocks, are posted unchanged. The check reads
the text, so a line the rendered comment hides, such as one inside an HTML comment,
counts. The refusal comes before the engine reads the pull request, so a refused
call posts no comment and writes no receipt; an omitted PR number is still resolved
from the forge first. It checks only the lenses `--lenses` names, and it does not act
on a `disputed` verdict.

What to do: record a delta pass with `--disposition -` and paste each lens's verdict
lines on stdin under its name, for example:

```text
correctness:
prose-class: confirmed — <reason>
safety-critical: confirmed — <reason>
```

A delta receipt recorded without `--disposition`, or with the verdicts posted in a
separate comment, is now refused. Take `scripts/pr_watch.py`,
`scripts/panel_prompt.py` and their test files together: one test in
`scripts/tests/test_pr_watch.py` holds the engine's draw names equal to
`panel_prompt.DELTA_DRAWS`, and one in `scripts/tests/test_panel_prompt.py` checks
that the rendered prompt asks for verdict lines under the same two names.
