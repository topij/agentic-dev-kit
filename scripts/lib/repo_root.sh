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
