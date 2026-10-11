## Runtime adapters: Claude bindings are skills, and three workflows run only when named

CHANGED (report / return shape): the Claude adapter for each workflow moved from
`.claude/commands/<slug>.md` to `.claude/skills/<slug>/SKILL.md`, and its front matter
now carries `name`. `kit_doctor.py --adapter-report` reports the new path and a new
state, `kit-retired`, for a kit-generated command left at the old path. During
`/upgrade`, install each skill the report lists as `missing`, then delete every
`kit-retired` command. An authored command at the old path is `adopter-owned`, and the
skill beside it is then reported `adopter-owned` rather than `missing`. Claude Code runs
a skill in preference to a same-named command, so move that command's policy into
config or the shared workflow before taking the kit's skill. A consumer that switches on
the report's `state` must accept `kit-retired`.

CHANGED (gate semantics): `adopt`, `upgrade` and `triage-friction-log` no longer load
on the model's own judgement. Each runs only when invoked by name: `/adopt`, `/upgrade`
and `/triage-friction-log` in Claude Code, and `$adopt`, `$upgrade` and
`$triage-friction-log` in Codex. The Claude skills carry
`disable-model-invocation: true`. For Codex, add this to each of those three skills'
`.agents/skills/<slug>/agents/openai.yaml`, or take the kit's copy of the file:

```yaml
policy:
  allow_implicit_invocation: false
```
