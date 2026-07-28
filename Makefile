# Makefile — thin entry points: `make install-hooks` and `make test`.
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
# repo, whose plan lives at docs/kit-*.md and is in use, it instead creates a
# root AGENTS.md. Either way it is a side effect this target must not have.
# So this target extracts and runs just the install_hooks()
# function body straight out of init.sh — it always reflects init.sh's
# current logic, never a stale/diverged copy — after resolving
# `paths.engines` the same way init.sh does (via config/dev-model.yaml,
# falling back to `scripts`), reusing scripts/lib/kitconfig.py to read it.
#
# test
# ----
# Runs the same suites the lane contract's local gate runs before every push.

.PHONY: install-hooks test

install-hooks:
	@engines_dir="$$(python3 -c "import sys; sys.path.insert(0, 'scripts/lib'); import kitconfig; c = kitconfig.load_config(); print(kitconfig.get(c, 'paths.engines', 'scripts'))" 2>/dev/null || echo scripts)"; \
	eval "$$(sed -n '/^install_hooks() {/,/^}/p' init.sh)"; \
	install_hooks

test:
	uv run --with pytest --with pyyaml python -m pytest scripts/lib/state_paths/tests scripts/tests -q
