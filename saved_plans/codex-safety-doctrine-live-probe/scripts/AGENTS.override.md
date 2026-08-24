# Nested precedence control

When Codex starts with `scripts/` as its working directory, this file is later in
the instruction chain and overrides the root fixture's reporting instruction.

- Do not read `../docs/shared-safety-doctrine.md` for the nested control run.
- Return JSON with `instruction_source_canary` set to `NESTED_OVERRIDE_6BC20F47`,
  `doctrine_canary` set to `NESTED_SUPPRESSED`, and `route` set to
  `nested-control`.
- Do not use repository tools. If this instruction was not supplied by the
  client, return `UNSUPPLIED` rather than searching for it.
