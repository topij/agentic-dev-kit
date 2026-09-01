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
