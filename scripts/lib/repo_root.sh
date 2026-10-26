#!/usr/bin/env bash
# Shared repository-root discovery for shell engines.

devkit_find_repo_root() {
    local candidate
    candidate="$(cd "$1" && pwd -P)" || return 1
    while [[ "$candidate" != "/" ]]; do
        if [[ -e "$candidate/.git" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
        candidate="$(dirname "$candidate")"
    done
    return 1
}

# Default lane sessions container: a `dev-model-sessions/` sibling of the
# repository's PRIMARY worktree. Resolving it from the invoking checkout instead
# (`dirname` of the repo root) sends a command run inside a lane worktree, or
# inside a linked cockpit worktree, to a different directory than the one the
# sessions live in (#479). The primary worktree is the first record of
# `git worktree list`, which every linked worktree of one repository reports
# identically. A bare primary (no working tree), a primary that is not an
# existing absolute directory holding a `.git` entry (a separate git dir or a
# submodule lists its git directory there), or a git that cannot list
# worktrees, keeps the old answer: the sibling of the checkout passed in. scripts/pr_watch.py
# mirrors this in `_default_sessions_dir`; change both together.
devkit_default_sessions_dir() {
    local repo_root="$1" primary
    primary="$(git -C "$repo_root" worktree list --porcelain -z 2>/dev/null | python3 -c '
import sys
fields = sys.stdin.buffer.read().split(b"\0")
first = []
for field in fields:
    if not field:
        break
    first.append(field)
if not first or not first[0].startswith(b"worktree ") or b"bare" in first[1:]:
    raise SystemExit(1)
sys.stdout.buffer.write(first[0][len(b"worktree "):])
' 2>/dev/null)" || primary=""
    # A separate git dir or a submodule lists its git directory, not a checkout,
    # as the first worktree: accept only a directory that holds a `.git` entry.
    [[ -n "$primary" && "$primary" == /* && -d "$primary" && -e "$primary/.git" ]] \
        || primary="$repo_root"
    printf '%s/dev-model-sessions\n' "$(dirname "$primary")"
}

# Read one scalar from the kit's deliberately simple, hand-authored YAML config.
# Supports top-level sections, one optional subsection, and scalar values. Keeping
# this here lets every shell engine share the same config semantics without taking
# a YAML runtime dependency.
devkit_config_scalar() {
    local config_file="$1" section="$2" subsection="$3" key="$4"
    [[ -n "$subsection" ]] && subsection="$subsection:"
    awk -v want_section="$section:" -v want_subsection="$subsection" -v want_key="$key:" '
        function trim(s) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", s); return s }
        /^[A-Za-z_][A-Za-z0-9_]*:[[:space:]]*$/ {
            current_section = trim($0); current_subsection = ""; next
        }
        /^  [A-Za-z_][A-Za-z0-9_]*:[[:space:]]*$/ {
            current_subsection = trim($0); next
        }
        current_section == want_section && current_subsection == want_subsection {
            line = $0
            stripped = line
            sub(/^[[:space:]]+/, "", stripped)
            if (index(stripped, want_key) == 1) {
                value = substr(stripped, length(want_key) + 1)
                sub(/[[:space:]]+#.*/, "", value)
                value = trim(value)
                # Strip one matching layer of the simple single/double quotes
                # used by hand-authored scalar config. Leaving single quotes in
                # a branch value defeats exact protected-branch comparisons.
                if ((value ~ /^".*"$/) || (value ~ /^'"'"'.*'"'"'$/)) {
                    value = substr(value, 2, length(value) - 2)
                }
                print value
                exit
            }
        }
    ' "$config_file" 2>/dev/null
}
