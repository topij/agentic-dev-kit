# Adopting into a repo that lints and formats

> **The one rule.** Your linter and formatter must not touch the kit's engines.
> A kit engine that your tooling edits can never be replaced by `/upgrade` again —
> which is the entire property `kit-manifest.json` and `kit_doctor` exist to protect.

This page is doctrine (kit-owned). The specific paths and hook names are yours.

## Why this is not optional

Engines are **kit-owned**: copied in byte-identical, replaced wholesale on upgrade,
never edited in your repo. `kit_doctor` enforces that by hashing every engine against
`kit-manifest.json`. Anything that rewrites a byte — a formatter, an autofixer, a
trailing-whitespace hook — is indistinguishable from you editing the file by hand,
and it reports as `differs` forever after.

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

```toml
# pyproject.toml (or ruff.toml)
[tool.ruff]
extend-exclude = ["scripts/devkit"]
force-exclude = true
```

**`force-exclude` is required, and it is the subtle one.** Without it, ruff honours
excludes only for paths it discovers itself. pre-commit passes filenames
*explicitly*, so the exclusion is ignored on exactly the invocation that rewrites
your files. Same class of flag exists for black (`force-exclude`) and other tools —
check yours.

### 3. Exclude `kit-manifest.json` from entropy-based secret scanners

The manifest is a sha256 per kit-owned file and nothing else. Every hash reads as a
high-entropy string: on cs-toolkit, `detect-secrets` flagged 24 of them. **Exclude
the file rather than adding it to a baseline** — the kit re-cuts the manifest every
release, so a baseline entry goes stale on every upgrade, whereas a path exclusion
does not. Pattern-based scanners (gitleaks and friends) are unaffected and should
keep scanning it.

If your repo mirrors that exclude pattern anywhere else — a script that shares the
regex, say — update both. cs-toolkit has exactly such a mirror, with a test that
catches the drift.

### 4. Verify the exclusion actually excludes

Do not assume it worked. Prove it, in this order:

```sh
# 1. the engines are byte-identical to the kit you copied from
for f in <engines-dir>/*.py <engines-dir>/lib/*.py; do
  cmp "$f" "<kit-checkout>/scripts/${f#<engines-dir>/}" || echo "DRIFT: $f"
done

# 2. run your hooks against them, then check identity AGAIN — this is the real test
pre-commit run --files <engines-dir>/*.py
# ...repeat step 1. Anything that changed means the exclusion is not working.

# 3. confirm you excluded only what you meant to
ruff check --show-files $(git ls-files '*.py') | wc -l          # with the exclusion
ruff check --no-force-exclude --show-files $(git ls-files '*.py') | wc -l
# the difference must be exactly your kit files, and nothing else
```

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
