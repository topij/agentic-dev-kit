#!/usr/bin/env bash
# reconcile_sessions.sh — reconcile each launched lane (any mechanism) to a merged PR.
#
# A joint wrap-up must not be able to claim a lane shipped without resolving
# its PR. An aggregate "all merged" can otherwise paper over a silently-dead
# session (never started, 0 commits, no PR, branch still at the main tip — yet
# the batch gets closed as done). This makes the per-branch check a
# deterministic command instead of an LLM tally.
#
# The check is keyed on branch / PR head ref, so it reconciles a batch launched
# by ANY mechanism — dev_session.sh sessions, background-Agent worktrees,
# headless lanes, or bare branches — not just dev_session.sh session metadata.
#
# For every launched lane it resolves a terminal state from the PR record
# (which survives branch deletion) plus the local branch:
#   • merged  — a merged PR exists for the branch              → counts toward M
#   • open    — a PR is still open (CI/review in flight)       → batch not closeable
#   • parked  — no merged PR; sub-reason surfaced so a dead    → counts toward K
#               lane can never hide behind the aggregate:
#                 · PR closed unmerged
#                 · N commit(s), no PR opened (unpushed?)
#                 · EMPTY — 0 commits, never started
#                 · no PR, branch absent (verify it ran)
#
# Emits a table + the "launched N, merged M, parked K" tally the wrap-up step
# prints before writing its block.
#
# Usage:
#   scripts/reconcile_sessions.sh <scope|branch> [...] [--prefix <configured>] [--base <configured>]
#   scripts/reconcile_sessions.sh --match '<glob>' [--match '<glob>'] ...
#   scripts/reconcile_sessions.sh                      # discover in-flight lanes
#
# Lane selection (keyed on branch / PR head ref, deduped across sources):
#   • <scope>          — a bare token maps to <prefix>/<scope>
#   • <branch>         — a token containing '/' is a full branch name as-is
#   • --match '<glob>' — every local + remote branch matching the glob (e.g.
#                        'feat/some-scope-*'); covers lanes whose worktrees are
#                        gone but whose branches/PRs remain
#   • no args          — union of dev_session.sh session dirs AND live git
#                        worktrees (background-Agent / headless lanes), deduped
#                        by branch
# Explicit args/--match stay authoritative for wrap-up; discovery is a convenience
# (a torn-down lane drops out of both session dirs and the worktree list).
#
# Exit: 0 = every launched lane merged; 3 = at least one open or parked (review
# each before writing the block); 64 = usage error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/repo_root.sh
source "$SCRIPT_DIR/lib/repo_root.sh"
REPO_ROOT="$(devkit_find_repo_root "$SCRIPT_DIR")" || {
    echo "[reconcile] error: no .git repository found above $SCRIPT_DIR" >&2
    exit 64
}
CONFIG_FILE="$REPO_ROOT/config/dev-model.yaml"
CONFIGURED_PROTECTED_BRANCH="$(devkit_config_scalar "$CONFIG_FILE" vcs "" protected_branch || true)"
[[ -n "$CONFIGURED_PROTECTED_BRANCH" ]] || {
  echo "[reconcile] error: config must define vcs.protected_branch" >&2
  exit 1
}
git check-ref-format --branch "$CONFIGURED_PROTECTED_BRANCH" >/dev/null 2>&1 || {
  echo "[reconcile] error: invalid vcs.protected_branch '$CONFIGURED_PROTECTED_BRANCH'" >&2
  exit 1
}
DEFAULT_BASE="${DEV_SESSION_BASE:-$CONFIGURED_PROTECTED_BRANCH}"
CONFIGURED_PREFIX="$(devkit_config_scalar "$CONFIG_FILE" vcs "" dev_branch_prefix || true)"

# Sessions container — mirror dev_session.sh so no-arg discovery lines up with
# the sibling that created the sessions.
SESSIONS_DIR="${DEVKIT_SESSIONS_DIR:-$(dirname "$REPO_ROOT")/dev-model-sessions}"
DEFAULT_PREFIX="${DEV_SESSION_PREFIX:-${CONFIGURED_PREFIX:-dev}}"

_die() {
    echo "[reconcile] error: $*" >&2
    exit 64
}

# Best-effort `gh` with a short timeout so reconciliation never hangs on a slow
# network — same idiom as dev_session.sh's list. A timeout/auth failure yields an
# empty string, which classifies as "no PR" (conservative: leans toward flagging
# a scope as parked rather than silently asserting it merged).
_gh() {
    local to
    if command -v timeout >/dev/null 2>&1; then
        to="timeout 10"
    elif command -v gtimeout >/dev/null 2>&1; then
        to="gtimeout 10"
    else
        to=""
    fi
    # shellcheck disable=SC2086
    $to gh "$@" 2>/dev/null || true
}

# Pick the CURRENT PR (newest by number — a reused branch can back several PRs
# over time) from a `gh pr list --json number,title,state` array on stdin and
# report ITS state. Prints a single tab-separated "<STATE>\t<number>\t<title>"
# line, or "NONE" if no PR exists. Robust to empty/garbage input (gh down → NONE).
_classify_pr() {
    python3 -c '
import sys, json
try:
    rows = json.load(sys.stdin)
except Exception:
    print("NONE"); sys.exit(0)
if not isinstance(rows, list):
    print("NONE"); sys.exit(0)
rows = [r for r in rows if isinstance(r, dict)]
if not rows:
    print("NONE"); sys.exit(0)
# A branch can back multiple PRs over time (e.g. a scope reused after rm). The
# CURRENT PR is the newest, so pick by descending PR number and report ITS
# state. Ranking by state (merged-always-wins) would let a stale merged PR mask
# the current in-flight one and falsely report "shipped" — the exact failure
# this guards against; over-flagging parked is the safe direction here.
rows.sort(key=lambda r: r.get("number") if isinstance(r.get("number"), int) else -1, reverse=True)
top = rows[0]
state = top.get("state") or "?"
num = top.get("number")
title = (top.get("title") or "").replace("\t", " ").replace("\n", " ").strip()
print("\t".join([str(state), str(num), title]))
' 2>/dev/null || echo "NONE"
}

# Reason a no-PR scope is parked. Distinguishes a dead/empty session from
# unpushed work — a distinction the rm "kept branch" warning could not make.
# Read-only: only show-ref + rev-list.
_branch_reason() {
    local branch="$1" base="$2"
    if ! git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$branch"; then
        echo "no PR, branch absent — verify it ran"
        return
    fi
    local ahead
    ahead="$(git -C "$REPO_ROOT" rev-list --count "origin/$base..$branch" 2>/dev/null || echo '?')"
    if [[ "$ahead" == "0" ]]; then
        echo "EMPTY — 0 commits, never started"
    elif [[ "$ahead" == "?" ]]; then
        echo "no PR opened (commit count vs origin/$base unknown)"
    else
        echo "$ahead commit(s), no PR opened (unpushed?)"
    fi
}

# Lane set, deduped by resolved branch (a branch can surface from more than one
# source — an explicit scope, a --match glob, a git worktree, a session dir).
# Display label + branch are parallel arrays; LANE_SEEN is a space-delimited set
# of branches already added (branch names can't contain spaces or glob metachars,
# so a literal `case` membership test is safe).
LANE_DISP=()
LANE_BR=()
LANE_SEEN=" "

# _add_lane <display> <branch> <base> — record a lane unless its branch is the
# base (never reconcile the integration branch against itself) or already seen.
_add_lane() {
    local display="$1" branch="$2" base="$3"
    [[ "$branch" == "$base" ]] && return 0
    case "$LANE_SEEN" in
        *" $branch "*) return 0 ;;
    esac
    LANE_SEEN="${LANE_SEEN}${branch} "
    LANE_DISP+=("$display")
    LANE_BR+=("$branch")
}

cmd_reconcile() {
    local prefix="$DEFAULT_PREFIX" base="$DEFAULT_BASE"
    local scopes=() match_globs=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --prefix) [[ $# -ge 2 ]] || _die "--prefix needs a value"; prefix="$2"; shift 2 ;;
            --base) [[ $# -ge 2 ]] || _die "--base needs a value"; base="$2"; shift 2 ;;
            --match) [[ $# -ge 2 ]] || _die "--match needs a value"; match_globs+=("$2"); shift 2 ;;
            -*) _die "unknown flag: $1" ;;
            *) scopes+=("$1"); shift ;;
        esac
    done

    # 1) Explicit scope/branch args (authoritative for wrap-up). A token with '/'
    #    is a full branch as-is; otherwise it's a scope → <prefix>/<scope>.
    local s br
    for s in "${scopes[@]+"${scopes[@]}"}"; do
        if [[ "$s" == */* ]]; then br="$s"; else br="${prefix}/${s}"; fi
        _add_lane "$s" "$br" "$base"
    done

    # 2) --match <glob>: every local AND remote branch matching the glob, keyed on
    #    branch name. Covers lanes whose worktrees were torn down but whose
    #    branches/PRs remain. `git branch --list` uses fnmatch (a '*' spans '/').
    local g name
    for g in "${match_globs[@]+"${match_globs[@]}"}"; do
        while IFS= read -r name; do
            [[ -n "$name" ]] && _add_lane "$name" "$name" "$base"
        done < <(git -C "$REPO_ROOT" branch --list "$g" --format='%(refname:short)' 2>/dev/null || true)
        while IFS= read -r name; do
            name="${name#origin/}"
            [[ -n "$name" ]] && _add_lane "$name" "$name" "$base"
        done < <(git -C "$REPO_ROOT" branch -r --list "origin/$g" --format='%(refname:short)' 2>/dev/null || true)
    done

    # 3) No explicit scopes AND no --match → discover in-flight lanes from BOTH
    #    dev_session.sh session dirs AND live git worktrees (background-Agent /
    #    headless lanes), unioned + deduped by branch. Explicit args/--match stay
    #    authoritative for wrap-up: `rm` removes a torn-down lane from both.
    if [[ "${#scopes[@]}" -eq 0 && "${#match_globs[@]}" -eq 0 ]]; then
        if [[ -d "$SESSIONS_DIR" ]]; then
            local d sbr
            for d in "$SESSIONS_DIR"/*/; do
                [[ -d "${d}wt" ]] || continue
                s="$(basename "$d")"
                # Prefer the branch `dev_session.sh new` recorded (it owns the real
                # name, incl. a custom --branch/--prefix); fall back to the
                # default-namespace reconstruction for pre-metadata sessions. This makes
                # a metadata-keyed `--branch <custom>` lane resolve to the SAME real name
                # the worktree-list path below derives, so the two dedupe to one lane
                # instead of surfacing a phantom "branch absent". (Base stays the run's
                # global --base — reconcile tracks one base per run, not per lane — so a
                # pre-metadata custom-branch session can still double-surface.)
                if [[ -s "${d}branch" ]]; then sbr="$(cat "${d}branch")"; else sbr="${prefix}/${s}"; fi
                _add_lane "$s" "$sbr" "$base"
            done
        fi
        local line wtbr
        while IFS= read -r line; do
            case "$line" in
                "branch refs/heads/"*)
                    wtbr="${line#branch refs/heads/}"
                    _add_lane "$wtbr" "$wtbr" "$base" ;;
            esac
        done < <(git -C "$REPO_ROOT" worktree list --porcelain 2>/dev/null || true)
        [[ "${#LANE_BR[@]}" -gt 0 ]] \
            || _die "no scopes given, no --match, and no active sessions/worktrees under $SESSIONS_DIR"
    fi

    # Explicit scopes/--match that resolved to nothing (e.g. a glob with no hits,
    # or only the base branch) is still a usage error, never a quiet all-clear.
    [[ "${#LANE_BR[@]}" -gt 0 ]] || _die "nothing to reconcile (scopes/--match matched no branches)"

    if ! command -v gh >/dev/null 2>&1; then
        echo "⚠ gh not found — PR state unavailable; classifying by local branch only." >&2
    fi

    printf '%-28s %-8s %-6s %s\n' "LANE" "STATUS" "PR" "DETAIL"
    printf '%-28s %-8s %-6s %s\n' "----------------------------" "--------" "------" "------"

    local launched="${#LANE_BR[@]}"
    local merged=0 open=0 parked=0 parked_notes=""
    local i disp branch pr_json classified state rest num title status detail pr_disp reason

    for i in "${!LANE_BR[@]}"; do
        disp="${LANE_DISP[$i]}"
        branch="${LANE_BR[$i]}"

        pr_json="$(_gh pr list --head "$branch" --state all --json number,title,state --limit 30)"
        classified="$(printf '%s' "$pr_json" | _classify_pr)"
        state="${classified%%$'\t'*}"
        num=""
        title=""
        if [[ "$state" == "MERGED" || "$state" == "OPEN" || "$state" == "CLOSED" ]]; then
            rest="${classified#*$'\t'}"
            num="${rest%%$'\t'*}"
            title="${rest#*$'\t'}"
        fi

        pr_disp="—"
        case "$state" in
            MERGED)
                merged=$((merged + 1)); status="merged"; pr_disp="#$num"; detail="$title" ;;
            OPEN)
                open=$((open + 1)); status="open"; pr_disp="#$num"; detail="in flight — $title" ;;
            CLOSED)
                parked=$((parked + 1)); status="parked"; pr_disp="#$num"
                detail="PR closed unmerged — $title"
                parked_notes="${parked_notes}  • ${disp}: PR #${num} closed unmerged"$'\n' ;;
            *)
                parked=$((parked + 1)); status="parked"
                reason="$(_branch_reason "$branch" "$base")"
                detail="$reason"
                parked_notes="${parked_notes}  • ${disp}: ${reason}"$'\n' ;;
        esac

        printf '%-28s %-8s %-6s %s\n' "$disp" "$status" "$pr_disp" "$detail"
    done

    echo
    if [[ "$open" -gt 0 ]]; then
        printf 'launched %d, merged %d, parked %d, open %d\n' "$launched" "$merged" "$parked" "$open"
        echo "⚠ ${open} lane(s) still OPEN — batch not fully closed; finish or park before writing the block."
    else
        printf 'launched %d, merged %d, parked %d\n' "$launched" "$merged" "$parked"
    fi
    if [[ -n "$parked_notes" ]]; then
        echo "⚠ parked — name each in the wrap-up block (never fold into \"all shipped\"):"
        printf '%s' "$parked_notes"
    fi

    # Exit 0 only when every launched lane merged (open == parked == 0); else 3
    # so a caller/the skill treats "not all landed" as a stop-and-account signal.
    [[ "$merged" -eq "$launched" ]] && return 0
    return 3
}

case "${1:-}" in
    -h|--help|help)
        sed -n '2,45p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
esac
cmd_reconcile "$@"
