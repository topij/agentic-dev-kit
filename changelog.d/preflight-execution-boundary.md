## Pinned preflight execution and offline object reads

Refresh `panel_prompt.py`, `check_record_prose.py`, their tests, and the fallback
review doctrine. Regenerate review prompts: their preflight invocation now runs
committed checker and config-parser blobs with digest verification, isolated
imports, and dependency requirements taken from the committed checker metadata.
Retain the generated invocation for review evidence instead of substituting a
working-tree script path.

Use Git with `--no-lazy-fetch` support. Missing partial-clone objects now produce
unavailable coverage without fetching; populate required objects explicitly
before reviewing. A supplied review scratch tree must contain the pinned engine
objects as well as the comparison objects.
