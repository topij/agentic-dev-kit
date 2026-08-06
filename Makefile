# Makefile — thin entry points: `make install-hooks`, `make test`, `make mutation-test`.
# `check-syntax` and `lint` are the CI-parity gates `test` and `mutation-test`
# compose from; call them directly to run just one gate.
#
# install-hooks
# -------------
# Does NOT reimplement the pre-push hook shim installer. `init.sh`'s own
# install_hooks() (git-worktree-aware, honors `core.hooksPath`, regenerates a
# shim rather than copying the hook body or symlinking it — see init.sh's own
# comments on why) is the single source of truth. Running the whole of
# `./init.sh` here would also re-trigger its interactive project/tracker
# prompts and its narrative-template seeding step — well outside what a target
# named "install-hooks" should touch. On a repo whose narrative docs still
# carry the `devkit-template: unrendered` marker on line 1 (an adopter who has
# not yet claimed them) that seeding rewrites those docs; in this kit's own
# repo, whose plan lives at docs/kit-*.md and is in use, it instead re-renders
# the root AGENTS.md and CLAUDE.md, which carry the kit-own marker and so are
# seedable here. Either way it is a side effect this target must not have.
# So this target extracts and runs just the install_hooks()
# function body straight out of init.sh — it always reflects init.sh's
# current logic, never a stale/diverged copy — after resolving
# `paths.engines` the same way init.sh does (via config/dev-model.yaml,
# falling back to `scripts`), reusing scripts/lib/kitconfig.py to read it.
#
# check-syntax
# ------------
# `bash -n` on the shell scripts a hook or session can source, `sh -n` on
# init.sh (it declares no shebang requiring bash, and CI checks it with `sh`,
# not `bash` — matched here on purpose), and the executable-bit check the
# documented `./init.sh` first command depends on. Mirrors CI's "Check shell
# syntax" + "init.sh must be executable" steps verbatim, in the same order,
# so a broken script fails here with the line CI would name — not as a wall
# of unrelated pytest failures. That gap is issue #292: an apostrophe inside
# a single-quoted awk program in init.sh closed the string, and `make test`
# reported 94 failing tests across four unrelated modules while naming
# nothing; `sh -n init.sh` named the line immediately.
#
# lint
# ----
# `ruff check --no-fix`, pinned to CI's exact version (0.16.0) via `uvx
# ruff@0.16.0` rather than whatever `ruff` happens to be on PATH. This
# repo's ruff.toml selects rules that changed between patch releases before
# (#292's tracking comment measured PATH ruff at 0.15.4 against CI's pinned
# 0.16.0 and found a real rule-set difference), so an unpinned local run can
# disagree with CI in either direction — pass a file CI rejects, or flag one
# CI doesn't. `uvx ruff@<version>` fetches and runs that exact release
# regardless of what is installed, closing the skew instead of trusting it
# away. See ruff.toml's own header for why config lives there and not in a
# root pyproject.toml.
#
# test
# ----
# Runs the same gates CI's `test` job runs before the pytest suites, in CI's
# order (lint, then shell syntax, then the executable check, then pytest) —
# see #292. A syntax or lint failure now surfaces as itself instead of as
# noise in the pytest suite's output.
#
# mutation-test
# -------------
# Gets the exact same preconditions as `test` — `lint` AND `check-syntax`,
# not just the latter. A mutation that happens to break shell syntax should
# read as a syntax error, not as a mass "kill" across every unrelated pytest
# module (issues #33/#112's false-kill problem arriving from a new direction,
# per #292); that argues for `check-syntax` on its own. But
# `scripts/tests/test_mutation_gate.py::test_the_mutation_target_actually_excludes_the_drift_check`
# already pins, by executing `make -n` on both targets, that `mutation-test`'s
# recipe must be byte-identical to `test`'s with only `-m 'not driftcheck'`
# appended — precisely so the two targets can never silently cover a
# different scope from each other. Carving `lint` out of `mutation-test`
# alone would trip that test, and would recreate #292's own shape one layer
# down: two commands a session is told are equivalent quietly stop being so.
# So `lint` comes along too, with a real cost worth naming: a mutation that
# also happens to violate ruff (an unused name, a touched import) now aborts
# `mutation-test` before pytest runs at all, reading as neither killed nor
# survived. That is a narrower, louder failure than the syntax-noise case
# `check-syntax` fixes — it names ruff as the blocker instead of pytest as
# the (false) verdict — but it is a real gap a mutation author should expect.
#
# `test` runs both suites in full. `mutation-test` runs the same suites MINUS
# the byte-comparison drift check (issues #33, #112). Use `mutation-test` —
# never plain `make test` — when deciding whether a deliberate mutation was
# caught, because
# `test_kit_repo_self_check_is_clean` rehashes every kit-owned file and so
# fails for ANY mutation to one, behavioural coverage or not. A run that
# leaves it in reports a kill for every mutation to a KIT_OWNED file — the
# paths in kit-manifest.json, NOT the whole repo: a mutation to
# scripts/tests/ or init.sh never trips it. `scripts/check_memory_budget.py`
# was in that never-trips list until #37 tracked it, and is not any more —
# which is the hazard in miniature: this comment tells a contributor which
# mutations are safe to trust, so tracking a file silently makes it wrong.
# One lens once REPORTED 17/17 killed, which was 7 survivors with it excluded.
# Attested, not measured: the 17 mutants are enumerated nowhere, and
# docs/kit-handoff-history.md says so explicitly. Quoted for the shape of the
# effect, not as a figure anything here reproduces.
#
# Regenerating the manifest instead also produces a truthful result, and is NOT
# what this target does, because it is per-mutant bookkeeping whose failure mode
# is silent and in the confident direction — forget it once and the mutant reads
# as killed.

.PHONY: install-hooks test mutation-test check-syntax lint

install-hooks:
	@engines_dir="$$(python3 -c "import sys; sys.path.insert(0, 'scripts/lib'); import kitconfig; c = kitconfig.load_config(); print(kitconfig.get(c, 'paths.engines', 'scripts'))" 2>/dev/null || echo scripts)"; \
	eval "$$(sed -n '/^install_hooks() {/,/^}/p' init.sh)"; \
	install_hooks

lint:
	uvx ruff@0.16.0 check --no-fix

check-syntax:
	bash -n scripts/dev_session.sh scripts/reconcile_sessions.sh scripts/lib/repo_root.sh scripts/hooks/pre-push
	sh -n init.sh
	test -x init.sh

test: lint check-syntax
	uv run --with pytest --with pyyaml python -m pytest scripts/lib/state_paths/tests scripts/tests -q

mutation-test: lint check-syntax
	uv run --with pytest --with pyyaml python -m pytest scripts/lib/state_paths/tests scripts/tests -q -m 'not driftcheck'
