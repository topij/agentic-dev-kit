Title: Adopt staging can pass kitconfig verification while init.sh rejects an indentless doc_budgets list

Project: topij/agentic-dev-kit

Labels: bug

Severity: M

The Codex continuation of the fixture staged by PR #682 reached the operator-approved
initialization step on 2026-09-06. The staged config matched the retained corrected
config and loaded as the complete intended tracked and merged mappings through the
installed kitconfig reader. The initializer nevertheless refused it before the prompts.

Reproduction: run `./init.sh --no-clobber` interactively in
`/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`, at fixture baseline
`08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus the retained staged adoption.
The installed kit source was `ab0a6d62308b298478b2f85fc961f14348f35365`;
the session's kit checkout was `d898660c5da63a91f1916fa6b5f84357b5622ee4`.
That command on 2026-09-06 exited `1` and printed:

```text
error: config/dev-model.yaml has a top-level key init.sh cannot migrate safely.
```

The staged config is retained in
`saved_plans/codex-adopt-field-evidence_2026-09-05/staged-config.yaml`.
Its block list under `doc_budgets` uses YAML's indentless form:

```yaml
doc_budgets:
- path: ROADMAP.md
  budget: 400
```

The top-level scan in `preflight_migration_config()` treats every non-indented,
non-comment line as a mapping key. A root-level list item therefore fails its
`^[A-Za-z_][A-Za-z0-9_.-]*:` predicate. kitconfig accepts this list representation;
passing the consumer comparison introduced by PR #685 does not establish compatibility
with the initializer's different grammar.

The fixture continuation indented the doc_budgets block. It also normalized the empty
prompted tracker scalars from single quotes to double quotes so the shell prompt reader
would show the intended empty defaults. Complete tracked and merged mapping comparisons
through the installed reader still matched the independently retained expectations.
The interactive initializer then reached its prompts and completed. This is fixture
recovery evidence, not an implementation change or completed adoption.

Proposed scope: extend the shared adopt staging guidance to cover the installed
initializer's accepted config representation as well as kitconfig, with a reproduction
using the retained staged YAML. Preserve the operator initialization boundary and
semantic mapping comparisons. Do not broaden either parser merely to accept this
serialization choice.

Duplicate search used `gh issue list --repo topij/agentic-dev-kit --state all
--search <term> --limit 100 --json number,title,state,url` with the terms `indentless`
and `init.sh config serialization`. In `/Users/topi/Coding/agentic-dev-kit` at
`d898660c5da63a91f1916fa6b5f84357b5622ee4` on 2026-09-06, each invocation returned
`[]`. `gh issue view 683 --repo topij/agentic-dev-kit --json number,state,title,body,url`
at that same directory, revision and date returned its delivered installed-kitconfig
comparison scope. This report concerns the remaining initializer consumer.
