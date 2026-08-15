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
#   • held    — an OPERATOR-class lane whose open PR is        → counts toward H
#               merge-ready: green, review-clean, and carrying
#               an independent-review receipt bound to the
#               current head. The lane is finished; only the
#               operator's merge decision is missing, so the
#               batch itself can no longer advance it.
#   • open    — a PR is still open with work left on it        → batch not closeable
#   • parked  — no merged PR; sub-reason surfaced so a dead    → counts toward K
#               lane can never hide behind the aggregate:
#                 · PR closed unmerged
#                 · N commit(s), no PR opened (unpushed?)
#                 · EMPTY — 0 commits, never started
#                 · no PR, branch absent (verify it ran)
#
# Emits a table + the "launched N, merged M, parked K" tally the wrap-up step
# prints before writing its block. A `held H` term is appended to that tally
# only when at least one lane is held, so a batch with none prints the line it
# has always printed.
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
# Exit: 0 = every launched lane merged; 4 = every launched lane merged or held,
# at least one held (nothing left for the batch — the operator owes a merge
# decision); 3 = at least one lane open or parked (review each before writing
# the block); 64 = usage error. 0 still means MERGED and nothing else — see the
# rationale at the return statements.

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

# Timeout prefix (possibly empty) so no probe here can hang the wrap-up on a
# slow network — same idiom as dev_session.sh's list. Factored out because the
# `held` probe needs the same guard with a longer budget than a single `gh` call.
_timeout_prefix() {
    if command -v timeout >/dev/null 2>&1; then
        echo "timeout $1"
    elif command -v gtimeout >/dev/null 2>&1; then
        echo "gtimeout $1"
    fi
}

# Best-effort `gh` with a short timeout. A timeout/auth failure yields an
# empty string, which classifies as "no PR" (conservative: leans toward flagging
# a scope as parked rather than silently asserting it merged).
_gh() {
    local to
    to="$(_timeout_prefix 10)"
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

# Branch → session-dir index (parallel arrays; bash 3.2 has no associative
# arrays and the rest of this file already uses that idiom).
#
# Lanes are keyed on BRANCH, but the two artifacts `held` needs — the persisted
# merge class and the lane's pr-watch state sandbox — are keyed on SCOPE, i.e.
# on the session directory `dev_session.sh new` created. Indexing every session
# dir by the branch it recorded makes those reachable no matter how the lane
# surfaced (explicit scope, --match glob, worktree, session dir), and matches
# the branch dev_session.sh's own `rm`/`pr-watch`/`merge` resolve.
SESS_BR=()
SESS_DIR=()

# _index_sessions <prefix> — populate the branch → session-dir index. Same
# branch resolution as the discovery pass below: the recorded `branch` file
# wins, else the default-namespace reconstruction for a pre-metadata session.
_index_sessions() {
    local prefix="$1" d scope sbr
    [[ -d "$SESSIONS_DIR" ]] || return 0
    for d in "$SESSIONS_DIR"/*/; do
        [[ -d "$d" ]] || continue
        scope="$(basename "$d")"
        if [[ -s "${d}branch" ]]; then sbr="$(cat "${d}branch")"; else sbr="${prefix}/${scope}"; fi
        [[ -n "$sbr" ]] || continue
        SESS_BR+=("$sbr")
        SESS_DIR+=("${d%/}")
    done
}

# _session_dir_for_branch <branch> — the indexed session dir, or "" if the
# branch has no session OR more than one session claims it.
#
# The scan is exhaustive rather than first-match. `dev_session.sh new` refuses a
# branch that already exists, so two sessions recording one branch takes a
# `new`/`new` race or a dir left behind out of band — but when it happens,
# first-match makes the verdict depend on the order the shell globbed
# `$SESSIONS_DIR/*/`: the same lane reads `operator` from one dir and `self`
# from the other, and the probe reads the wrong lane's receipt. Refusing an
# ambiguous key keeps the answer deterministic and on the safe side (no session
# ⇒ never `held`), and says so once instead of resolving it silently.
#
# Counted `while` rather than `for i in "${!SESS_BR[@]}"`: under `set -u`,
# bash 3.2 (the macOS default, and what `check-syntax` runs) errors on the
# index expansion of an EMPTY array, which is the common case here.
_session_dir_for_branch() {
    local branch="$1" i=0 n found=""
    n="${#SESS_BR[@]}"
    while [[ "$i" -lt "$n" ]]; do
        if [[ "${SESS_BR[$i]}" == "$branch" ]]; then
            if [[ -n "$found" ]]; then
                echo "⚠ two sessions record branch '$branch' ($found, ${SESS_DIR[$i]}) —" >&2
                echo "  its merge class is ambiguous, so it is never classified as held." >&2
                printf ''
                return 0
            fi
            found="${SESS_DIR[$i]}"
        fi
        i=$((i + 1))
    done
    printf '%s' "$found"
}

# _held_check <branch> <pr> — is this open PR's lane HELD for the operator?
#
#   0 — held: operator-class lane, and the PR is merge-ready
#   1 — not held (lane is genuinely still open)
#   2 — could not be determined; caller reports `open` and says why
#
# Two pieces of evidence, both already on disk or already reachable:
#
# 1. The PERSISTED merge class (`<session>/merge_class`, written by
#    `dev_session.sh new`). Note the asymmetry with dev_session.sh's `merge`,
#    which defaults a MISSING merge class to `operator`: there, defaulting to
#    operator REFUSES an autonomous merge, so it fails safe. Here, defaulting
#    to operator would WIDEN `held` and let an unknown lane claim a terminal
#    state, so absent metadata must mean "not held". Same value, opposite
#    default, because the safe direction is opposite.
#
# 2. `mergeable` from a non-persisting pr_watch poll against the lane's own
#    state sandbox — the engine's own predicate for "green, review-clean, and
#    carrying an independent-review receipt bound to the current head". Read,
#    never re-derived: a rollup verdict recomputed here would be a second copy
#    of a contract that can drift from the engine's (the same reason
#    dev_session.sh's merge gate reads the flag instead of rebuilding it), and
#    unacked review findings are not visible in `gh pr list` output at all — so
#    a locally-derived "looks green" would call a lane with open findings
#    finished. `--no-persist` keeps this probe read-only: reconciliation must
#    never mutate a lane's seen-set, settle baseline or receipt.
_held_check() {
    local branch="$1" pr="$2"
    local session_dir merge_class to report

    session_dir="$(_session_dir_for_branch "$branch")"
    [[ -n "$session_dir" ]] || return 1
    [[ -s "$session_dir/merge_class" ]] || return 1
    merge_class="$(cat "$session_dir/merge_class")"
    [[ "$merge_class" == "operator" ]] || return 1

    # No `command -v uv` / `-f pr_watch.py` pre-check, and no empty-`$report`
    # check either: all three would be equivalent mutants. An absent `uv`, an
    # absent engine, a timeout, a transport failure and an empty reply all end at
    # the same place — a non-zero invocation, or a parse below that raises — and
    # all of them mean the one thing: the probe did not run, so rc 2 and the
    # caller's stderr note.
    to="$(_timeout_prefix 60)"
    # shellcheck disable=SC2086
    report="$(DEVKIT_STATE_ROOT="$session_dir/state" \
        $to uv run "$SCRIPT_DIR/pr_watch.py" "$pr" --json --no-persist 2>/dev/null)" || return 2

    # `mergeable` is the precise name and fails CLOSED when absent; `done` is its
    # unchanged legacy alias. `converged` must NEVER be read here — it is true on
    # a green, comment-clean PR carrying no review receipt.
    printf '%s' "$report" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(2)
if not isinstance(d, dict):
    sys.exit(2)
sys.exit(0 if d.get("mergeable") is True else 1)
' || return $?
    return 0
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

    # Index the session dirs up front — `held` needs each lane's merge class and
    # state sandbox regardless of which of the four selection paths surfaced it,
    # and the reconstruction fallback needs the resolved `--prefix`.
    _index_sessions "$prefix"

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
    local merged=0 open=0 parked=0 held=0 parked_notes="" held_notes="" unknown_notes=""
    local i disp branch pr_json classified state rest num title status detail pr_disp reason
    local held_rc

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
                pr_disp="#$num"
                held_rc=0
                _held_check "$branch" "$num" || held_rc=$?
                if [[ "$held_rc" -eq 0 ]]; then
                    held=$((held + 1)); status="held"
                    detail="awaiting operator merge — $title"
                    held_notes="${held_notes}  • ${disp}: PR #${num} — ${title}"$'\n'
                else
                    open=$((open + 1)); status="open"; detail="in flight — $title"
                    # rc 1 is the ordinary "not held" answer and must stay silent.
                    # Anything else means the probe could not run (no uv, no
                    # pr_watch.py, timeout, transport failure) — the lane is
                    # reported `open` either way, but a probe that never ran must
                    # not be indistinguishable from one that ran and said no.
                    [[ "$held_rc" -eq 1 ]] || unknown_notes="${unknown_notes}  • ${disp}: PR #${num}"$'\n'
                fi ;;
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
    # `held H` and `open O` are appended only when non-zero, so a batch with
    # neither prints the exact line it always has. `held` sits before `open`:
    # both are unmerged, and the held ones are the ones nobody is still working.
    local tally
    tally="$(printf 'launched %d, merged %d, parked %d' "$launched" "$merged" "$parked")"
    [[ "$held" -gt 0 ]] && tally="${tally}$(printf ', held %d' "$held")"
    [[ "$open" -gt 0 ]] && tally="${tally}$(printf ', open %d' "$open")"
    printf '%s\n' "$tally"
    if [[ "$open" -gt 0 ]]; then
        echo "⚠ ${open} lane(s) still OPEN — batch not fully closed; finish or park before writing the block."
    fi
    if [[ -n "$held_notes" ]]; then
        echo "→ held for operator sign-off — green, review-clean, receipt bound to head."
        echo "  Nothing left for the batch; merge or park each, and name it in the block:"
        printf '%s' "$held_notes"
    fi
    if [[ -n "$parked_notes" ]]; then
        echo "⚠ parked — name each in the wrap-up block (never fold into \"all shipped\"):"
        printf '%s' "$parked_notes"
    fi
    if [[ -n "$unknown_notes" ]]; then
        {
            echo "⚠ could not evaluate for 'held' (no uv / no pr_watch.py / probe failed) —"
            echo "  reported OPEN, which may understate them:"
            printf '%s' "$unknown_notes"
        } >&2
    fi

    # Exit 0 only when every launched lane MERGED. Deliberately not widened to
    # "merged or held", even though `all merged or held` is where a correctly-run
    # autonomous batch lands: 0 is read — by this file's own header, by
    # workflows/parallel.md, and by anyone who writes `&& echo all shipped` — as
    # the claim that the work is IN the protected branch. A held lane is not; the
    # operator can still decline it, and the degenerate all-operator batch would
    # exit 0 having merged nothing at all. That is precisely the aggregate that
    # papers over a lane, which is why this script exists.
    #
    # So `held` gets its OWN code instead of borrowing either neighbour. 4 means
    # "every lane is terminal and none is dead, but the operator owes a merge
    # decision" — the answer to "is the BATCH done?", kept separate from 0's
    # answer to "did everything LAND?". A caller that only ever asked `rc == 0`
    # is unaffected; one that stops on any non-zero is unaffected; only a caller
    # matching 3 exactly needs to learn 4, and that is the adopter-visible half
    # of this change.
    #
    # Precedence: open or parked outranks held. A parked lane still needs naming
    # and an open one still needs finishing, so neither may hide behind a batch
    # that is otherwise handed to the operator.
    [[ "$merged" -eq "$launched" ]] && return 0
    [[ "$open" -eq 0 && "$parked" -eq 0 && "$held" -gt 0 ]] && return 4
    return 3
}

case "${1:-}" in
    -h|--help|help)
        # Every comment line from 2 until the first non-comment line, derived
        # rather than a hardcoded end line. The previous `sed -n '2,45p'` had
        # already fallen one line short of the header and cut the Exit sentence
        # mid-clause; growing the header here would have hidden this change's
        # own exit-code contract from `--help` the same silent way.
        awk 'NR > 1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac
cmd_reconcile "$@"
