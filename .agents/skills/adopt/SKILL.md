---
name: adopt
description: Selectively adopt agentic-dev-kit into an existing repo — inspect what's already present, propose an install plan the operator confirms, then install only the missing pieces without clobbering existing files. Use when integrating the kit into a mature repository rather than a fresh one.
---

# Adopt

1. Work from the repository root of the repo being adopted into.
2. Read `config/dev-model.yaml` if one exists, and resolve configured paths from it. Its
   absence is itself a signal the workflow handles — do not invent one.
3. Read `docs/agentic-dev-kit/workflows/adopt.md` completely.
4. Follow that workflow. It is a judgment pass, not a copy: inspect what the repo already
   has, propose an install plan, and get the operator's confirmation before writing.
5. Never clobber an existing file. The workflow's final step hands the operator
   `./init.sh --no-clobber`; run nothing that renders over a file the operator has not
   agreed to lose.
6. Use the current runtime's review and commit mechanisms; require user authorization for
   external mutations not already requested.
