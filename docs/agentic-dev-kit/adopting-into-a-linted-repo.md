# Adopting into a repo that lints and formats

> **The one rule.** Your linter and formatter must not touch the kit's engines.
> An engine your tooling rewrites reports as `differs` on every `kit_doctor` run,
> and returns to `differs` after each commit that touches it — which destroys the
> signal `/upgrade` depends on.

This page is doctrine (kit-owned). The specific paths and hook names are yours.

## Why this is not optional

Engines are **kit-owned**: copied in byte-identical, replaced wholesale on upgrade,
never edited in your repo. `kit_doctor` enforces that by hashing every engine against
`kit-manifest.json`. Anything that rewrites a byte — a formatter, an autofixer, a
trailing-whitespace hook — is indistinguishable from you editing the file by hand.

**To be precise about the damage, because overstating it is its own problem:** a
reformatted engine is not unrecoverable. `/upgrade` handles `differs` by diffing the
local file and replacing it, and a formatter-only diff is the easy case. The cost is
that it *recurs* — the formatter rewrites the file again on the next commit that
touches it — and, worse, that it makes `differs` uninformative. `/upgrade`'s whole
Step 3 rests on reading that diff to tell "simply older" from "locally edited"; once
every engine is permanently `differs` for formatting reasons, a genuine local edit is
buried in the noise. You lose the signal, not the file.

The failure is quiet. Red CI you notice; `ruff --fix` silently reformatting a file on
commit you do not. **Measured on a real adoption** (cs-toolkit, kit issue #58): the
first `pre-commit run` after install rewrote *both* installed Python engines. The kit
ships no formatter config of its own, so its engines are not clean under any
particular adopter's — and cannot be, because there is no single formatting that
satisfies a repo on `line-length = 120` and one on the default `88`.

So the kit does **not** try to match your formatter. You exclude its directory.

## Do this at adoption time, before the first commit

### 1. Give the engines their own directory

Set `paths.engines` to a directory that holds *only* kit files — `scripts/devkit/`
is the convention. A directory is the only exclusion unit that does not drift as the
kit adds files. Enumerating individual filenames re-creates the hand-maintained-list
problem that kit issues #37 and #47 exist to fix.

`/adopt` already prescribes `scripts/devkit/` when your `scripts/` has colliding
names. Do it for lint containment even when nothing collides.

### 2. Exclude that directory from lint and format

Put the exclusion in your **tool config**, not in individual hooks — a repo typically
invokes its linter from three places (a Makefile target, CI, and pre-commit), and
they must agree. For ruff:

The two config files take **different shapes**, and mixing them up is a parse error,
not a silent fallback:

```toml
# pyproject.toml — keys nest under [tool.ruff]
[tool.ruff]
extend-exclude = ["scripts/devkit"]
force-exclude = true
```

```toml
# ruff.toml / .ruff.toml — the file IS the [tool.ruff] table; no header
extend-exclude = ["scripts/devkit"]
force-exclude = true
```

A `[tool.ruff]` header inside a standalone `ruff.toml` fails with
``unknown field `tool` ``. (The kit's own `ruff.toml` is the second shape.)

**`force-exclude` is required, and it is the subtle one.** Without it, ruff honours
excludes only for paths it discovers itself. pre-commit passes filenames
*explicitly*, so the exclusion is ignored on exactly the invocation that rewrites
your files. Same class of flag exists for black (`force-exclude`) and other tools —
check yours.

### 3. Exclude `kit-manifest.json` from entropy-based secret scanners

The manifest's `files` map is a sha256 per kit-owned file (plus a `role`), alongside
`kit_version` and an `adopter_owned` list. Every hash reads as a
high-entropy string: on cs-toolkit, `detect-secrets` flagged 24 of them. **Exclude
the file rather than adding it to a baseline** — the kit re-cuts the manifest every
release, so a baseline entry goes stale on every upgrade, whereas a path exclusion
does not. Pattern-based scanners (gitleaks and friends) are unaffected and should
keep scanning it.

If your repo mirrors that exclude pattern anywhere else — a script that shares the
regex, say — update both. cs-toolkit has exactly such a mirror, with a test that
catches the drift.

### 4. Verify the exclusion actually excludes

Do not assume it worked. Prove it, in this order. (`bash`, not POSIX `sh` — the
loop needs process substitution so the drift flag survives; a pipeline would run
it in a subshell and the exit status would always be 0.)

```bash
ENGINES=scripts/devkit          # your paths.engines
KIT=/path/to/agentic-dev-kit    # the checkout you copied from

# 1. EVERY tracked file under the engines dir is byte-identical to the kit.
#    Enumerate them — do not glob. `*.py` and `lib/*.py` silently miss
#    lib/state_paths/, the shell engines (dev_session.sh, reconcile_sessions.sh,
#    lib/repo_root.sh) and hooks/pre-push — all manifest-owned, and the shell
#    ones are the likeliest to be rewritten by a formatter you forgot about.
drift=0
while IFS= read -r f; do
  cmp -s "$f" "$KIT/scripts/${f#"$ENGINES"/}" || { echo "DRIFT: $f"; drift=1; }
done < <(git ls-files -- "$ENGINES")
[ "$drift" -eq 0 ] || { echo "engines drifted from the kit"; exit 1; }

# 2. run your hooks against them, then repeat step 1 — this is the real test.
#    Anything that changed means the exclusion is not working.
git ls-files -- "$ENGINES" | xargs pre-commit run --files

# 3. confirm you excluded only what you meant to
ruff check --show-files $(git ls-files '*.py') | wc -l          # with the exclusion
ruff check --no-force-exclude --show-files $(git ls-files '*.py') | wc -l
# the difference must be exactly your kit files, and nothing else
```

Step 1 does double duty: a file under `$ENGINES` with **no counterpart in the kit**
also reports as `DRIFT`, because `cmp` cannot open the missing target. That is the
stray-file detection `kit_doctor` does not give you (see the residual-risk section
below) — so run it from CI, not just once at adoption.

Step 3 matters because `force-exclude` also activates your tool's *default*
excludes for explicitly-passed files. On cs-toolkit the difference was exactly 2 of
798 tracked files — the two kit engines — but that is a property to measure, not
assume.

## The residual risk, and how to close it

A directory exclusion is broad on purpose, and that cuts both ways: **any non-kit
file placed in the engines directory silently escapes linting**, and `kit_doctor`
will not report it — its `unknown-version` state covers kit-owned files missing from
the manifest, not stray files in the engines directory.

Close it with a repo-local test:

> every file under `paths.engines` must be one the kit ships

That test is adopter-owned (it depends on your test framework), which is why it is a
recommendation here rather than a shipped check.

## What NOT to do

- **Do not fix a lint finding by editing the engine.** It reports as drift, and the
  next upgrade reverts it. File it upstream — a defect in a byte-identical kit file
  goes to the kit, never into the adopter. That rule is what keeps upgrades possible.
- **Do not silence findings with per-file `# noqa` in engines.** Same problem: it is
  a byte change.
- **Do not add the engines to a formatter's "already formatted" baseline.** Baselines
  go stale on every kit release.
