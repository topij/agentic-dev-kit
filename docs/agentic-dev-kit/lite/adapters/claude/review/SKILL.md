---
name: review
description: "Review a change before it is committed: a same-context correctness review, plus a fresh-context adversarial review when it touches a path the repository declares safety-critical. Use before a commit, or when asked to review the current change."
---

Read `docs/agentic-dev-kit/lite/lite-review.md` completely and follow it.

Treat `$ARGUMENTS` as the change to review, or review the uncommitted change when it
is empty. This repository is on the kit's lite profile: read `config/dev-model.yaml`
directly, as the workflow says; there is no config loader and no kit engine to run.
