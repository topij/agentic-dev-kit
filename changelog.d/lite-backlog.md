## Lite profile: an optional `backlog.path` key for a story backlog the lite session-start and wrap-up read

ADDED (config key): `backlog.path`, read only by the lite profile (#1399). It names the
repository's own story backlog, in the format of the bama `user-stories` skill: a
`### <id> <title>` heading per story, one `Status:` line whose first word is `todo`,
`doing`, `done` or `dropped`, and an optional `Depends:` line. The lite schema in
`lite-wrap-up.md` now lists it, and `backlog` is a mapping or null like the other
optional sections.

ADDED: the lite `session-start` runs a block in its new *Backlog* section that reads
`backlog.path` from the config itself and then the backlog. It reports the plan and the
backlog where they disagree, the stories it cannot read and those that can never become
ready, and draws its pick from the first ready `doing` or `todo` story instead of the
plan's next step. A configured backlog it cannot read, including one with a code fence
or HTML comment that never closes, is reported unavailable, with a 🔴 Now item.

ADDED (gate semantics): the lite `wrap-up` sets the status of each story the session
worked on, and records no story status in the plan. A configured backlog it cannot
read is a hard stop. So are a `backlog` that is not a mapping holding one `path`, a
`backlog.path` that is not a plain path inside the repository (ASCII letters, digits,
`.`, `_`, `/` and `-`, relative, with no `.` or `..` component and no leading `-`), and
copies of the config that name different paths.

ADDED: on a lite repository, `kit_doctor.py`'s text report prints a `backlog:` line
when the key is set: present, missing, unusable, or a `backlog` of the wrong shape. It
changes no exit code and no JSON field.

What to do: nothing, unless a lite repository keeps a story backlog. To use one, take
this kit first (a lite `wrap-up` older than this change stops on the new key as outside
its schema), then add to `config/dev-model.yaml`:

```yaml
backlog:
  path: docs/STORIES.md
```

and commit it. Without the key the lite workflows behave as before.
