## Lite profile: an optional `backlog.path` key for a story backlog the lite session-start and wrap-up read

ADDED (config key): `backlog.path`, read only by the lite profile (#1399). It names the
repository's own story backlog, in the format of the bama `user-stories` skill: a
`### <id> <title>` heading per story, one `Status:` line whose first word is `todo`,
`doing`, `done` or `dropped`, and an optional `Depends:` line. The lite schema in
`lite-wrap-up.md` now lists it. It has one declared form, a `backlog:` line and an
indented `path:` line; `backlog:` alone, `null` or `~` means none, and any other
spelling, a flow mapping among them, is refused.

ADDED: the lite `session-start` runs a block in its new *Backlog* section that reads
`backlog.path` from the config itself and then the backlog. It reports the plan and the
backlog where they disagree, the stories it cannot read and those that can never become
ready, and draws its pick from the first ready `doing` or `todo` story instead of the
plan's next step. A configured backlog it cannot read, including one with a code fence
or HTML comment that never closes, is reported unavailable, with a 🔴 Now item.

ADDED (gate semantics): the lite `wrap-up` sets the status of each story the session
worked on, and records no story status in the plan. A configured backlog it cannot
read is a hard stop. So are a `backlog` outside the declared form, a `backlog.path`
that is not a plain path inside the repository (ASCII letters, digits, `.`, `_`, `/`
and `-`, relative, with no `.` or `..` component and no leading `-`, not a symbolic
link, and resolving inside the repository), and one naming the plan or the friction
log. These backlog stops read the working tree's config; the schema stop, which now
lists `backlog.path`, reads every copy as before.

`kit_doctor.py` is unchanged: it accepts a lite install with the key and without it.

What to do: nothing, unless a lite repository keeps a story backlog. To use one, take
this kit first (a lite `wrap-up` older than this change stops on the new key as outside
its schema), then add to `config/dev-model.yaml`:

```yaml
backlog:
  path: docs/STORIES.md
```

and commit it. Without the key, the lite workflows report no backlog and draw the next
step from the plan, as before. The block still runs every session, so a machine whose
`awk` cannot read the config gets an `unavailable:` line: a 🔴 Now item in the
`session-start`, and a hard stop in the `wrap-up`.
