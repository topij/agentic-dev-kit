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
# For every launched lane it resolves a state from the PR record (which survives
# branch deletion) plus the local branch. Three of the four are TERMINAL —
# merged, held, parked; `open` is the one that says reconciliation is not
# finished, which is why it, alone, keeps the batch un-closeable:
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
# the block); 64 = usage or forge-resolution error. 0 still means MERGED and
# nothing else — see the rationale at the return statements.

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

# Bounded `gh` with a short timeout. Callers preserve its status: an
# authentication, transport, or timeout failure is unknown state, never an
# authoritative empty response.
_gh() {
    local to
    to="$(_timeout_prefix 10)"
    # shellcheck disable=SC2086
    $to gh "$@"
}

# Pick the CURRENT same-repository PR (newest by number — a reused branch can
# back several PRs over time) from the forge response. The `--head` query alone
# is not identity evidence because a fork can reuse the branch name. Every row
# must have the declared shape; well-formed foreign rows are ignored before
# ranking. Prints `<STATE> TAB <number> TAB <title> TAB <head OID>`, or `NONE`
# only for an authoritative response with no matching row.
_classify_pr() {
    local repo_owner="$1" branch="$2" base="$3"
    python3 -c '
import json, string, sys
expected_owner, expected_branch, expected_base = sys.argv[1:4]
try:
    rows = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
if not isinstance(rows, list):
    raise SystemExit(1)
if not all(isinstance(row, dict) for row in rows):
    raise SystemExit(1)
matching = []
for row in rows:
    if type(row.get("number")) is not int:
        raise SystemExit(1)
    if row.get("state") not in {"OPEN", "CLOSED", "MERGED"}:
        raise SystemExit(1)
    if not isinstance(row.get("title"), str):
        raise SystemExit(1)
    for key in ("baseRefName", "headRefName"):
        value = row.get(key)
        if not isinstance(value, str) or not value or value != value.strip():
            raise SystemExit(1)
    head_oid = row.get("headRefOid")
    if not isinstance(head_oid, str) or len(head_oid) != 40 or any(ch not in string.hexdigits for ch in head_oid):
        raise SystemExit(1)
    owner = row.get("headRepositoryOwner")
    if not isinstance(owner, dict) or not isinstance(owner.get("login"), str) or not owner["login"]:
        raise SystemExit(1)
    if type(row.get("isCrossRepository")) is not bool:
        raise SystemExit(1)
    if (
        row["isCrossRepository"] is False
        and owner["login"].casefold() == expected_owner.casefold()
        and row["headRefName"] == expected_branch
        and row["baseRefName"] == expected_base
    ):
        matching.append(row)
if not matching:
    print("NONE"); sys.exit(0)
# A branch can back multiple PRs over time (e.g. a scope reused after rm). The
# CURRENT PR is the newest, so pick by descending PR number and report ITS
# state. Ranking by state (merged-always-wins) would let a stale merged PR mask
# the current in-flight one and falsely report "shipped" — the exact failure
# this guards against; over-flagging parked is the safe direction here.
matching.sort(key=lambda row: row["number"], reverse=True)
top = matching[0]
state = top.get("state") or "?"
num = top.get("number")
title = (top.get("title") or "").replace("\t", " ").replace("\n", " ").strip()
print("\t".join([str(state), str(num), title, top["headRefOid"]]))
' "$repo_owner" "$branch" "$base" 2>/dev/null
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
#
# Dirs are stored ABSOLUTE (`cd … && pwd -P`, the same normalization
# dev_session.sh applies before writing a headless lane's state-root marker).
# $SESSIONS_DIR is absolute by default but $DEVKIT_SESSIONS_DIR may not be, and
# pr_watch.py treats a RELATIVE $DEVKIT_STATE_ROOT as "ignore this and use
# <repo>/state" rather than as an error — deliberately, so its loop never
# crashes. The probe below would then read the MAIN checkout's per-PR file,
# which can hold real unrelated history for the same PR number, and no failure
# would be visible anywhere. Absolute here closes that off at the source.
_index_sessions() {
    local prefix="$1" d scope sbr abs
    [[ -d "$SESSIONS_DIR" ]] || return 0
    for d in "$SESSIONS_DIR"/*/; do
        [[ -d "$d" ]] || continue
        scope="$(basename "$d")"
        if [[ -s "${d}branch" ]]; then sbr="$(cat "${d}branch")"; else sbr="${prefix}/${scope}"; fi
        [[ -n "$sbr" ]] || continue
        abs="$(cd "$d" 2>/dev/null && pwd -P)" || abs=""
        [[ -n "$abs" ]] || abs="${d%/}"
        SESS_BR+=("$sbr")
        SESS_DIR+=("$abs")
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

# Print the first surviving ref that is not a stable snapshot of the PR head.
# Local and remote-tracking refs are independent resume evidence: a stale local
# ref must not hide newer pushed work, and a ref that moves between reads must
# not be treated as a terminal snapshot. Return 0 for a mismatch/move, 1 when
# every surviving ref is stable at the expected head, and 2 on a Git read error.
_surviving_tip_mismatch() {
    local branch="$1" expected_head="$2"
    local refs labels i ref label first second ref_rc
    refs=("refs/heads/$branch" "refs/remotes/origin/$branch")
    labels=("local" "remote-tracking")
    for i in 0 1; do
        ref="${refs[$i]}"
        label="${labels[$i]}"
        if git -C "$REPO_ROOT" show-ref --verify --quiet "$ref"; then
            first="$(git -C "$REPO_ROOT" rev-parse --verify "$ref^{commit}" 2>/dev/null)" \
                || return 2
            second="$(git -C "$REPO_ROOT" rev-parse --verify "$ref^{commit}" 2>/dev/null)" \
                || return 2
            if [[ "$first" != "$second" ]]; then
                printf '%s tip moved during reconciliation (%s != %s)' \
                    "$label" "${first:0:12}" "${second:0:12}"
                return 0
            fi
            if [[ "$second" != "$expected_head" ]]; then
                printf '%s tip differs from PR head (%s != %s)' \
                    "$label" "${second:0:12}" "${expected_head:0:12}"
                return 0
            fi
        else
            ref_rc=$?
            [[ "$ref_rc" -eq 1 ]] || return 2
        fi
    done
    return 1
}

# Resolve the checkout's repository once, with ambient GH_REPO removed, before
# rendering any row. Every later forge read and review probe is pinned to that
# exact nameWithOwner. A missing command, failed request, or malformed identity
# stops reconciliation; none may degrade into an invented no-PR lane.
REPO_NWO=""
_resolve_repo_nwo() {
    [[ -z "$REPO_NWO" ]] || return 0
    REPO_NWO="$(cd "$REPO_ROOT" && unset GH_REPO && _gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null)" \
        || return 1
    REPO_NWO="${REPO_NWO%%$'\n'*}"
    case "$REPO_NWO" in
        ""|/*|*/|*/*/*|*[[:space:]]*) REPO_NWO="" ;;
        */*) : ;;
        *) REPO_NWO="" ;;
    esac
}

# _held_check <session-dir> <branch> <pr> <base> <head> — is this open PR's
# lane HELD for the operator?
#
#   0 — held: operator-class lane, and the PR is merge-ready
#   1 — not held (lane is genuinely still open)
#   2 — could not be determined; caller reports `open` and says why
#
# The durable identity and the act-time report must agree:
#
# 1. The PERSISTED merge class (`<session>/merge_class`, written by
#    `dev_session.sh new`). Note the asymmetry with dev_session.sh's `merge`,
#    which defaults a MISSING merge class to `operator`: there, defaulting to
#    operator REFUSES an autonomous merge, so it fails safe. Here, defaulting
#    to operator would WIDEN `held` and let an unknown lane claim a terminal
#    state, so absent metadata must mean "not held". Same value, opposite
#    default, because the safe direction is opposite.
#
# 2. The persisted base must match the authoritative PR base. A missing base is
#    incomplete session identity and therefore cannot widen the lane to held.
#
# 3. A non-persisting pr_watch poll against the lane's own state sandbox must
#    report `mergeable` and `converged` for this exact PR, base, and head, with
#    an explicit empty blocker list. Read the engine verdicts; do not rebuild
#    their predicates from forge rollups. `--no-persist` keeps this probe
#    read-only: reconciliation must never mutate a lane's seen-set, settle
#    baseline, or review receipt.
_held_check() {
    local session_dir="$1" branch="$2" pr="$3" base="$4" head_oid="$5"
    local merge_class recorded_base to report
    local probe_env

    [[ -n "$session_dir" ]] || return 1
    [[ -d "$session_dir/state" && -s "$session_dir/base" && -s "$session_dir/merge_class" ]] || return 1
    recorded_base="$(cat "$session_dir/base")"
    [[ "$recorded_base" == "$base" ]] || return 1
    merge_class="$(cat "$session_dir/merge_class")"
    [[ "$merge_class" == "operator" ]] || return 1

    # No `command -v uv` / `-f pr_watch.py` pre-check, and no empty-`$report`
    # check either: all three would be equivalent mutants. An absent `uv`, an
    # absent engine, a timeout, a transport failure and an empty reply all end at
    # the same place — a non-zero invocation, or a parse below that raises — and
    # all of them mean the one thing: the probe did not run, so rc 2 and the
    # caller's stderr note. Repository identity was resolved before row output;
    # this check only preserves the helper's fail-closed contract.
    to="$(_timeout_prefix 60)"
    _resolve_repo_nwo
    [[ -n "$REPO_NWO" ]] || return 2
    probe_env=(env "DEVKIT_STATE_ROOT=$session_dir/state" "DEVKIT_ROOT=$REPO_ROOT" "GH_REPO=$REPO_NWO")
    # shellcheck disable=SC2086
    report="$("${probe_env[@]}" \
        $to uv run "$SCRIPT_DIR/pr_watch.py" "$pr" --json --no-persist 2>/dev/null)" || return 2

    # `mergeable` is the merge-authorization verdict; `converged` confirms that
    # the observed forge state is internally settled. Both fail closed when
    # absent, and exact identity plus an explicit blocker list prevent a valid
    # report for another head from terminalizing this lane.
    printf '%s' "$report" | python3 -c '
import json, sys
expected_pr, expected_base, expected_head = sys.argv[1:4]
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(2)
if not isinstance(d, dict):
    sys.exit(2)
blockers = d.get("merge_blockers")
if not isinstance(blockers, list):
    sys.exit(2)
ready = (
    d.get("mergeable") is True
    and d.get("converged") is True
    and str(d.get("pr")) == expected_pr
    and d.get("base") == expected_base
    and d.get("head") == expected_head
    and not blockers
)
sys.exit(0 if ready else 1)
' "$pr" "$base" "$head_oid" || return $?
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

    command -v gh >/dev/null 2>&1 \
        || _die "gh is required to reconcile pull-request state"
    _resolve_repo_nwo \
        || _die "could not resolve the GitHub repository for $REPO_ROOT"
    [[ -n "$REPO_NWO" ]] \
        || _die "GitHub returned an invalid repository identity for $REPO_ROOT"
    local repo_owner="${REPO_NWO%%/*}"

    local launched="${#LANE_BR[@]}"
    local merged=0 open=0 parked=0 held=0 parked_notes="" held_notes="" unknown_notes="" rows="" row=""
    local i disp branch lane_base session_dir pr_json classified state rest num title head_oid status detail pr_disp reason
    local held_rc tip_detail tip_rc tip_differs

    for i in "${!LANE_BR[@]}"; do
        disp="${LANE_DISP[$i]}"
        branch="${LANE_BR[$i]}"
        lane_base="$base"
        session_dir="$(_session_dir_for_branch "$branch")"
        if [[ -n "$session_dir" && -s "$session_dir/base" ]]; then
            lane_base="$(cat "$session_dir/base")"
        fi

        pr_json="$(GH_REPO="$REPO_NWO" _gh pr list --repo "$REPO_NWO" --head "$branch" --state all \
            --json number,title,state,baseRefName,headRefName,headRefOid,headRepositoryOwner,isCrossRepository \
            --limit 100 2>/dev/null)" \
            || _die "could not resolve PR state for '$branch' in '$REPO_NWO'"
        classified="$(printf '%s' "$pr_json" | _classify_pr "$repo_owner" "$branch" "$lane_base")" \
            || _die "GitHub returned invalid PR state for '$branch' in '$REPO_NWO'"
        state="${classified%%$'\t'*}"
        num=""
        title=""
        head_oid=""
        if [[ "$state" == "MERGED" || "$state" == "OPEN" || "$state" == "CLOSED" ]]; then
            rest="${classified#*$'\t'}"
            num="${rest%%$'\t'*}"
            rest="${rest#*$'\t'}"
            title="${rest%%$'\t'*}"
            head_oid="${rest#*$'\t'}"
        fi

        # The PR record survives branch deletion. Observe every surviving local
        # and remote-tracking ref twice: either ref can carry resume work, and a
        # move during reconciliation is not a terminal snapshot. Callers must
        # still keep launched refs quiescent for the duration of this snapshot;
        # Git offers no lock shared with an unrelated pusher.
        tip_detail=""
        tip_differs=0
        if [[ "$state" == "MERGED" || "$state" == "OPEN" ]]; then
            if tip_detail="$(_surviving_tip_mismatch "$branch" "$head_oid")"; then
                tip_differs=1
            else
                tip_rc=$?
                [[ "$tip_rc" -eq 1 ]] \
                    || _die "could not resolve surviving branch tips for '$branch'"
            fi
        fi

        pr_disp="—"
        case "$state" in
            MERGED)
                pr_disp="#$num"
                if [[ "$tip_differs" -eq 1 ]]; then
                    open=$((open + 1)); status="open"
                    detail="$tip_detail — $title"
                else
                    merged=$((merged + 1)); status="merged"; detail="$title"
                fi ;;
            OPEN)
                pr_disp="#$num"
                if [[ "$tip_differs" -eq 1 ]]; then
                    open=$((open + 1)); status="open"
                    detail="$tip_detail — $title"
                    held_rc=1
                else
                    held_rc=0
                    _held_check "$session_dir" "$branch" "$num" "$lane_base" "$head_oid" || held_rc=$?
                fi
                if [[ "$tip_differs" -eq 0 && "$held_rc" -eq 0 ]]; then
                    held=$((held + 1)); status="held"
                    detail="awaiting operator merge — $title"
                    held_notes="${held_notes}  • ${disp}: PR #${num} — ${title}"$'\n'
                elif [[ "$tip_differs" -eq 0 ]]; then
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
                reason="$(_branch_reason "$branch" "$lane_base")"
                detail="$reason"
                parked_notes="${parked_notes}  • ${disp}: ${reason}"$'\n' ;;
        esac

        printf -v row '%-28s %-8s %-6s %s' "$disp" "$status" "$pr_disp" "$detail"
        rows="${rows}${row}"$'\n'
    done

    # Forge/read/shape failures abort above before any authoritative-looking
    # row is emitted. Render only after the whole requested snapshot succeeded.
    printf '%-28s %-8s %-6s %s\n' "LANE" "STATUS" "PR" "DETAIL"
    printf '%-28s %-8s %-6s %s\n' "----------------------------" "--------" "------" "------"
    printf '%s' "$rows"
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
            # The parenthetical is an enumeration of the rc-2 causes, so it has to
            # grow with them — a cause missing from it reads to the operator as
            # "not my case".
            echo "⚠ could not evaluate for 'held' (no uv / no pr_watch.py /"
            echo "  probe failed or returned malformed state) —"
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
        # rather than a hardcoded end line. The hardcoded one had already drifted
        # behind the header and was truncating it mid-sentence, and every edit
        # that grows the header silently truncates more.
        awk 'NR > 1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac
cmd_reconcile "$@"
