# Fixture Step 3c handoff

Fixture: `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`
Branch: `chore/adopt-agentic-dev-kit`

> The adoption is staged on this branch. The next step is `./init.sh --no-clobber`, and you
> should run it yourself so you see and confirm each prompt.
>
> **Run it with `--no-clobber`.** With that flag it writes only files that are genuinely
> missing — it will not render over anything already on disk, including the six paths it
> would otherwise claim by a marker on line 1 (`AGENTS.md`, `CLAUDE.md`, and your
> configured `paths.handoff`, `paths.handoff_history`, `paths.friction_log`,
> `paths.friction_log_archive`). Anything it declines is printed as
> `left untouched (--no-clobber): <path>` and listed again at the end of the run.
>
> Read that end-of-run list, because those files are the ones the run did not finish. For
> each: if it is an unrendered skeleton you want filled in, delete it and re-run; if it is
> yours, delete line 1 to claim it permanently, and it will never be a candidate again.
> Without the flag `init.sh` renders over every one of them with no backup, reporting only
> `seeded` — which is right for a fresh repo and wrong here.
>
> It seeds the docs and entry points that are **missing**, leaving every file already on
> disk byte-identical; installs the pre-push hook **unless a non-shim hook is already there**,
> in which case it says so and leaves yours alone; and appends the kit's `.gitignore`
> entries — all of them except `config/*.local.yaml`, which the adoption already added
> because it could not wait for this step. Nothing else in the adoption seeds a doc,
> installs the hook, or adds the rest of those ignores. Read what it prints — the
> conditionals above are reported per file.
>
> Once it has run, move any adoption-friction entries from your temporary adoption notes
> into the seeded `paths.friction_log`. No pull request exists yet because creation waits
> for this run and the verification that follows it.

Resolved paths from this fixture: `AGENTS.md` (MARKED); `CLAUDE.md`, `ROADMAP.md`, `notes/history.md` (IN_USE); `notes/friction.md`, `notes/friction-archive.md` (ABSENT). The only marker observed was the first line of `AGENTS.md`.

This bounded exercise stops here. No operator init run is claimed.
