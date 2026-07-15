#!/usr/bin/env bash
# dev_session.sh — manage isolated parallel dev sessions (worktree + state sandbox).
#
# The easy front-door for working several agent/dev sessions at once without
# them clobbering each other's git checkout OR each other's state/cache/. Each
# session gets:
#   • its own git worktree off fresh origin/<base> on a new branch, and
#   • its own absolute DEVKIT_STATE_ROOT sandbox, so every state/ write the
#     session makes lands in the sandbox, never prod.
#
# This is the activation the state-sandbox primitive (scripts/lib/state_paths)
# was waiting for: nothing exports DEVKIT_STATE_ROOT on its own, so the sandbox
# runs in zero sessions until something sets it. `new` is what finally sets it.
#
# Usage:
#   scripts/dev_session.sh new <scope> [--base main] [--prefix dev] [--branch <full>] [--force] [--headless] [--runtime <name>] [--launcher <command>]
#   scripts/dev_session.sh list [--watch [interval]]
#   scripts/dev_session.sh path <scope>
#   scripts/dev_session.sh rm <scope> [--force] [--keep-branch]
#   scripts/dev_session.sh print-contract
#
# `list --watch [interval]` is a live board: it re-renders every <interval>
# seconds (default 30) and marks rows whose state changed since the last render
# (a CI ✓/✗/… flip, a new commit, a DIRTY-count change, or a PR-state change)
# with a `*` until Ctrl-C. Bare `list` is a one-shot snapshot, byte-identical to
# before.
#
# `new` prints a copy-paste line that cd's into the worktree, exports the
# sandbox, and prints a runtime-configured launch command — or `source
# <session>/activate` in any shell.
#
# `new --headless` instead writes a sticky `<worktree>/.devkit_state_root`
# marker (the sandbox path) and prints a JSON descriptor to stdout — so an
# unattended launcher (background agent / cloud runtime) can point an agent at the
# worktree and its state/ writes isolate via the marker, no env export needed.
# Diagnostics go to stderr in this mode so stdout is clean JSON. The
# descriptor also carries `prompt_preamble` — the canonical lane-contract text
# a launcher MUST prepend verbatim to the lane's prompt — and an `env` map
# (currently `DEVKIT_REFUSE_UNSANDBOXED_STATE: "1"`) the launcher MUST export
# into the lane's process so a marker-resolution failure refuses rather than
# silently falling back to prod `state/`. The same env var is also baked into
# the worktree's `activate` snippet for the interactive fallback (`source
# <session>/activate`). Interactive `new` (no `--headless`) and cron are
# byte-identical — neither sets this flag.
#
# `print-contract` prints ONLY the lane-contract text (no JSON, no worktree
# side effects) — for a launcher that wants the raw preamble once and reuses it
# across many lanes (e.g. a parallel-workflow fan-out path), or for
# eyeballing the current contract.
#
# Sessions live outside the repo (a sibling `dev-model-sessions/` dir by
# default; override with $DEVKIT_SESSIONS_DIR), so the repo tree stays clean
# and cron — which sets neither env var — is completely unaffected.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/repo_root.sh
source "$SCRIPT_DIR/lib/repo_root.sh"
REPO_ROOT="$(devkit_find_repo_root "$SCRIPT_DIR")" || {
    echo "[dev-session] error: no .git repository found above $SCRIPT_DIR" >&2
    exit 1
}
ENGINE_DIR_REL="${SCRIPT_DIR#"$REPO_ROOT"/}"

# Sessions container (sibling of the repo by default). Each session is one
# subdir holding wt/ (worktree) + state/ (sandbox) + activate (env snippet).
SESSIONS_DIR="${DEVKIT_SESSIONS_DIR:-$(dirname "$REPO_ROOT")/dev-model-sessions}"

# Parallel-session branches get their own namespace so they can't collide with
# hand-named feature branches. Default "dev" — keep this in sync with
# `vcs.dev_branch_prefix` in config/dev-model.yaml if you change it there.
DEFAULT_PREFIX="${DEV_SESSION_PREFIX:-dev}"

# Sticky sandbox marker written at the worktree root by `new --headless`. MUST
# match scripts/lib/state_paths's STATE_ROOT_MARKER — the resolver reads it to
# select the sandbox when DEVKIT_STATE_ROOT is unset.
STATE_ROOT_MARKER=".devkit_state_root"

# Env var that makes an unsandboxed state/ write a hard error instead of a
# warning (scripts/lib/state_paths's REFUSE_UNSANDBOXED_ENV). `new
# --headless` sets this to "1" by default (pulling the guard forward from warn
# to refuse for headless lanes specifically) — a lane whose marker resolution
# fails refuses to write prod state/ rather than silently falling through.
# Interactive `new` and cron never set it — byte-identical.
REFUSE_UNSANDBOXED_ENV_VALUE="1"

# Whether the current `new` is headless. Set by cmd_new flag parsing; consulted
# by _info so headless stdout carries ONLY the JSON descriptor a launcher parses.
HEADLESS=0

# The canonical headless-lane launch contract. Every mechanism that hands a
# lane prompt to an agent (the --headless JSON descriptor's `prompt_preamble`,
# `print-contract`, and any Workflow fan-out / single-background-Agent paths
# your own dispatcher documents) MUST inject this text verbatim ahead of the
# task-specific prompt — a rule that only lives in a memory or in prose can't
# bind a freshly spawned lane. Keep this the SINGLE source of the contract
# text — any doc that quotes it should quote it, not restate it independently.
_lane_contract() {
    local handoff friction protected
    local escaped_engine_dir escaped_handoff escaped_friction escaped_protected
    handoff="$(_config_scalar paths "" handoff)"
    friction="$(_config_scalar paths "" friction_log)"
    protected="$(_config_scalar vcs "" protected_branch)"
    escaped_engine_dir="$(_sed_replacement "$ENGINE_DIR_REL")"
    escaped_handoff="$(_sed_replacement "${handoff:-<configured handoff>}")"
    escaped_friction="$(_sed_replacement "${friction:-<configured friction log>}")"
    escaped_protected="$(_sed_replacement "${protected:-the protected branch}")"
    sed \
        -e "s|@ENGINE_DIR@|$escaped_engine_dir|g" \
        -e "s|@HANDOFF@|$escaped_handoff|g" \
        -e "s|@FRICTION_LOG@|$escaped_friction|g" \
        -e "s|@PROTECTED_BRANCH@|$escaped_protected|g" <<'CONTRACT'
LANE CONTRACT (binding):
- Actively poll your PR's CI at a bounded cadence (e.g. `gh pr checks <PR#>` every few minutes, capped around 30 min) until it is fully green. Never stop to idly wait on a "monitor", a timer, or someone else's watcher — you are the one polling.
- Your run ends ONLY at the terminal state. Never stop early to wait for a watcher, monitor, or timer of any kind — if you need to wait on anything, poll it yourself with a bounded until-loop.
- Stop at draft-PR-green and hand off. Open your PR as a DRAFT on first push and leave it in draft. Do not mark it ready, do not merge — the cockpit owns ready-for-review, the review pass, and the terminal merge.
- `gh`'s draft bit is flaky: after `gh pr create --draft`, run `uv run @ENGINE_DIR@/pr_watch.py <pr> --assert-draft` — a create that silently lands non-draft triggers premature bot review.
- Report every finding, decision, and open question in your FINAL TEXT response — that is the durable channel back to the cockpit. Never rely exclusively on a runtime-specific peer-message mechanism.
- If you spawn sub-agents of your own, hold them to the same rule: they return findings in their final text rather than relying exclusively on peer messages.
- Never edit @HANDOFF@ or @FRICTION_LOG@ — those are cockpit-owned shared narrative files. Put your handoff (what shipped, lessons, deferrals) in the PR body instead.
- Run `git branch --show-current` before every commit to confirm you are on your own lane branch, never @PROTECTED_BRANCH@.
CONTRACT
}

_die() {
    echo "[dev-session] error: $*" >&2
    exit 1
}

# Progress/diagnostic line. In --headless mode it goes to stderr so stdout stays
# clean for the JSON descriptor; interactive keeps it on stdout.
_info() {
    if [[ "$HEADLESS" -eq 1 ]]; then
        echo "$@" >&2
    else
        echo "$@"
    fi
}

# Best-effort `gh` with a short timeout so `list` never hangs on a slow network.
_gh() {
    local to
    if command -v timeout >/dev/null 2>&1; then
        to="timeout 8"
    elif command -v gtimeout >/dev/null 2>&1; then
        to="gtimeout 8"
    else
        to=""
    fi
    # shellcheck disable=SC2086
    $to gh "$@" 2>/dev/null || true
}

_slug_ok() {
    [[ "$1" =~ ^[a-z0-9][a-z0-9-]*$ ]]
}

# Read one scalar from the kit's deliberately simple, hand-authored YAML config.
# This avoids adding a YAML dependency to the shell launcher. It supports exactly
# the top-level/subsection/scalar shape used by runtime.default and
# runtime.launchers.<name>.
_config_scalar() {
    local section="$1" subsection="$2" key="$3"
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
                gsub(/^"|"$/, "", value)
                print value
                exit
            }
        }
    ' "$REPO_ROOT/config/dev-model.yaml" 2>/dev/null
}

_sed_replacement() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//&/\\&}"
    value="${value//|/\\|}"
    printf '%s' "$value"
}

_resolve_launcher() {
    local requested_runtime="$1" requested_launcher="$2"
    local runtime launcher
    runtime="${requested_runtime:-${DEVKIT_RUNTIME:-$(_config_scalar runtime "" default)}}"
    launcher="${requested_launcher:-${DEVKIT_AGENT_LAUNCHER:-}}"
    if [[ -z "$launcher" && -n "$runtime" && "$runtime" != "none" ]]; then
        launcher="$(_config_scalar runtime launchers "$runtime")"
    fi
    [[ "$launcher" == "none" ]] && launcher=""
    printf '%s\t%s\n' "${runtime:-none}" "$launcher"
}

# True when $1 is a branch `rm` must never delete, regardless of merged status:
# the session's base branch, or the universal mainlines main/master. The last
# line of defense against a worktree HEAD that wandered onto main after a
# post-merge `git checkout` resolving branch=main and running `git branch -D
# main`, deleting the cockpit's checkout. $2 is the session's base branch
# (every caller passes it, defaulting to "main" before the call — the function
# itself requires it and aborts under `set -u` if omitted).
_is_protected_branch() {
    local b="$1" base="$2"
    # allow-hardcoded — main/master are the universal protected mainlines by definition
    [[ "$b" == "$base" || "$b" == "main" || "$b" == "master" ]]
}

cmd_new() {
    local scope="" base="main" prefix="$DEFAULT_PREFIX" branch="" force=0
    local requested_runtime="" requested_launcher="" runtime="" launcher=""
    HEADLESS=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --base) [[ $# -ge 2 ]] || _die "--base needs a value"; base="$2"; shift 2 ;;
            --prefix) [[ $# -ge 2 ]] || _die "--prefix needs a value"; prefix="$2"; shift 2 ;;
            --branch) [[ $# -ge 2 ]] || _die "--branch needs a value"; branch="$2"; shift 2 ;;
            --force) force=1; shift ;;
            --headless) HEADLESS=1; shift ;;
            --runtime) [[ $# -ge 2 ]] || _die "--runtime needs a value"; requested_runtime="$2"; shift 2 ;;
            --launcher) [[ $# -ge 2 ]] || _die "--launcher needs a value"; requested_launcher="$2"; shift 2 ;;
            -*) _die "unknown flag: $1" ;;
            *) [[ -z "$scope" ]] && scope="$1" && shift || _die "unexpected arg: $1" ;;
        esac
    done
    [[ -n "$scope" ]] || _die "usage: dev_session.sh new <scope> [--base main] [--prefix dev] [--branch <full>] [--force] [--headless] [--runtime <name>] [--launcher <command>]"
    _slug_ok "$scope" || _die "scope must be a lowercase slug ([a-z0-9-]): got '$scope'"
    [[ -z "$branch" ]] && branch="${prefix}/${scope}"
    IFS=$'\t' read -r runtime launcher <<< "$(_resolve_launcher "$requested_runtime" "$requested_launcher")"

    # Refuse a protected branch as the session branch BEFORE any side effect. `--branch`
    # is unvalidated, so `new x --branch main --force` would otherwise tear the existing
    # session down and then `git branch -D main` — the catastrophe via `new`'s recreate
    # path. Checked here (not inside --force) so a refusal NEVER destroys the current
    # worktree/state first.
    if _is_protected_branch "$branch" "$base"; then
        _die "refusing to use protected branch '$branch' (base/main/master) as a session branch"
    fi

    # In --headless mode, fold ALL of this function's stdout into stderr (saving
    # the real stdout on fd 3) so stray output — git's "HEAD is now at …",
    # branch-tracking notices, progress — can't pollute the JSON descriptor, which
    # is the ONLY thing written back to fd 3 at the end. Interactive is untouched.
    if [[ "$HEADLESS" -eq 1 ]]; then
        exec 3>&1 1>&2
    fi

    local session_dir="$SESSIONS_DIR/$scope"
    local worktree="$session_dir/wt"
    local sandbox="$session_dir/state"

    if [[ "$force" -eq 1 ]]; then
        # Recreate: tear down any existing worktree/session/branch first, so the
        # `git worktree add -b` below doesn't collide with a stale one.
        if [[ -d "$worktree" ]]; then
            git -C "$REPO_ROOT" worktree remove --force "$worktree" 2>/dev/null || true
        fi
        rm -rf "$session_dir"
        git -C "$REPO_ROOT" worktree prune 2>/dev/null || true
        # $branch was already proven non-protected at the top of cmd_new, so this
        # recreate-time delete can never target main/master/base.
        git -C "$REPO_ROOT" branch -D "$branch" 2>/dev/null || true
    else
        if [[ -e "$session_dir" ]]; then
            _die "session '$scope' already exists at $session_dir (use --force to recreate, or 'rm $scope' first)"
        fi
        if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$branch"; then
            _die "branch '$branch' already exists locally (use --branch to pick another, or --force)"
        fi
    fi

    _info "[dev-session] fetching origin/$base …"
    git -C "$REPO_ROOT" fetch origin "$base" -q || _die "could not fetch origin/$base"

    if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
        _die "branch '$branch' already exists on origin — pick another scope/--branch"
    fi

    _info "[dev-session] creating worktree at $worktree (branch $branch off origin/$base)"
    mkdir -p "$session_dir"
    git -C "$REPO_ROOT" worktree add -b "$branch" "$worktree" "origin/$base" \
        || _die "git worktree add failed"

    mkdir -p "$sandbox"

    # Carry gitignored MCP credentials into the worktree, if present.
    if [[ -f "$REPO_ROOT/.mcp.json" ]]; then
        cp "$REPO_ROOT/.mcp.json" "$worktree/.mcp.json"
    fi

    # Activation snippet: the sandbox is this session's state/ (writes isolate
    # here); DEVKIT_ROOT points the read-cascade's prod twin at the MAIN
    # checkout so the session can still reuse its fresh caches read-only.
    cat > "$session_dir/activate" <<ACTIVATE
# source this to enter the '$scope' dev session
cd "$worktree" || return 1
export DEVKIT_STATE_ROOT="$sandbox"
export DEVKIT_ROOT="$REPO_ROOT"
echo "[dev-session] $scope active — branch $branch, sandbox \$DEVKIT_STATE_ROOT"
ACTIVATE

    # A --headless session's activate snippet ALSO fails closed — if someone
    # falls back to `source activate` on a headless-created worktree (or the
    # marker resolution somehow misses), an unsandboxed state/ write still
    # refuses rather than silently landing in prod state/. Appended as a
    # separate write (not folded into the heredoc above) so interactive `new`
    # stays byte-identical: this line is ONLY ever written when HEADLESS=1.
    if [[ "$HEADLESS" -eq 1 ]]; then
        printf 'export DEVKIT_REFUSE_UNSANDBOXED_STATE="%s"\n' "$REFUSE_UNSANDBOXED_ENV_VALUE" \
            >> "$session_dir/activate"
    fi

    # Record the session's identity — its OWN branch + base — so `rm` deletes THIS
    # branch at teardown, never whatever branch the worktree happens to be sitting
    # on (a worktree that wandered onto main post-merge could otherwise make `rm`
    # target main). Lives beside the worktree in the out-of-repo session dir, so it
    # is never committed. Written for both the interactive and --headless paths.
    printf '%s\n' "$branch" > "$session_dir/branch"
    printf '%s\n' "$base" > "$session_dir/base"

    if [[ "$HEADLESS" -eq 1 ]]; then
        # Resolve to ABSOLUTE paths before writing the marker/descriptor. $sandbox
        # and $worktree inherit DEVKIT_SESSIONS_DIR, which may be relative; a
        # relative marker is rejected by state_paths's marker resolver (and a
        # relative DEVKIT_STATE_ROOT by state_paths's state_root()), so the lane
        # would be created but its later state/ writes would fail instead of
        # sandboxing. The dirs exist by now (worktree add + mkdir above), so
        # `cd … && pwd -P` is safe and also normalizes symlinks for a durable
        # on-disk marker.
        local worktree_abs sandbox_abs repo_root_abs
        worktree_abs="$(cd "$worktree" && pwd -P)" || _die "could not resolve worktree path"
        sandbox_abs="$(cd "$sandbox" && pwd -P)" || _die "could not resolve sandbox path"
        repo_root_abs="$(cd "$REPO_ROOT" && pwd -P)" || _die "could not resolve repo root"

        # Sticky marker: makes the sandbox a property of the worktree on disk, so
        # a background agent's stateless Bash calls (no shared shell, no surviving
        # `export`) resolve it via the state-paths resolver with no env gymnastics
        # in the prompt. Gitignored so a lane never commits it.
        printf '%s\n' "$sandbox_abs" > "$worktree_abs/$STATE_ROOT_MARKER"

        # Machine-readable descriptor (NOT the human copy-paste block) so a
        # launcher can `json.load` it. Built via python3 so paths with spaces /
        # special chars — and the multi-line contract text — stay valid JSON.
        # Written to fd 3 (the saved real stdout) so it is the sole thing on
        # the caller's stdout. `prompt_preamble` is the canonical lane-contract
        # text the launcher MUST prepend verbatim to the lane's prompt; `env`
        # is the map of env vars the launcher MUST export into the lane's
        # process — currently just the fail-closed sandbox guard.
        python3 - "$scope" "$branch" "$worktree_abs" "$sandbox_abs" "$repo_root_abs" "$base" \
            "$(_lane_contract)" "$REFUSE_UNSANDBOXED_ENV_VALUE" "$runtime" "$launcher" >&3 <<'PY'
import json
import sys

scope, branch, worktree, state_root, repo_root, base, prompt_preamble, refuse_unsandboxed, runtime, launcher = sys.argv[1:11]
print(
    json.dumps(
        {
            "scope": scope,
            "branch": branch,
            "worktree": worktree,
            "state_root": state_root,
            "repo_root": repo_root,
            "base": base,
            "prompt_preamble": prompt_preamble,
            "env": {"DEVKIT_REFUSE_UNSANDBOXED_STATE": refuse_unsandboxed},
            "runtime": runtime,
            "launcher": launcher or None,
        }
    )
)
PY
        return 0
    fi

    echo
    echo "✓ session '$scope' ready."
    echo
    if [[ -n "$launcher" ]]; then
        echo "  Start it with $runtime (copy-paste):"
        echo "    cd \"$worktree\" && export DEVKIT_STATE_ROOT=\"$sandbox\" && export DEVKIT_ROOT=\"$REPO_ROOT\" && $launcher"
    else
        echo "  Activate it, then start your agent runtime:"
        echo "    source \"$session_dir/activate\""
    fi
    echo
    echo "  …or in any shell:  source \"$session_dir/activate\""
    echo "  When done:         \"${BASH_SOURCE[0]}\" rm $scope"
}

# Gather one TAB-separated record per active session, the shared data behind both
# bare `list` and `list --watch`:
#   scope <TAB> branch <TAB> pr <TAB> ci <TAB> dirty <TAB> sandbox <TAB> sig
# `sig` is the change-tracking signature watch mode diffs on. It folds in the
# short HEAD sha and the PR state/draft/review on top of the displayed columns, so
# a new commit or a PR-state flip (draft→open, review approved) is detected even
# though neither is its own column. Bare `list` ignores `sig`. The single
# python3 parse (vs two) is the only consolidation — the resulting `pr` and `ci`
# strings are unchanged. Keeps the _gh short-timeout idiom so a slow network
# can't hang a watch loop.
_collect_board() {
    local d scope worktree branch head dirty pr ci pr_json parsed num state draft review sig pr_ok
    for d in "$SESSIONS_DIR"/*/; do
        worktree="${d}wt"
        [[ -d "$worktree" ]] || continue
        scope="$(basename "$d")"
        branch="$(git -C "$worktree" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
        head="$(git -C "$worktree" rev-parse --short HEAD 2>/dev/null || echo '?')"
        dirty="$(git -C "$worktree" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
        pr="—"; ci="—"; state=""; draft=""; review=""; pr_ok=0
        pr_json="$(_gh pr view "$branch" --json number,state,isDraft,reviewDecision,statusCheckRollup)"
        if [[ -n "$pr_json" ]]; then
            pr_ok=1
            # CI rollup → one glyph. The failing/pending vocabularies mirror
            # scripts/pr_watch.py:summarize_checks (the other cockpit CI surface) so
            # the board and pr-watch agree — notably TIMED_OUT/ACTION_REQUIRED render
            # ✗, not a misleading ✓, and EXPECTED/QUEUED render … (pending).
            parsed="$(printf '%s' "$pr_json" | python3 -c '
import sys, json
d = json.load(sys.stdin)
n = d.get("number")
num = str(n) if n else "—"
roll = d.get("statusCheckRollup") or []
states = [c.get("conclusion") or c.get("state") for c in roll]
FAIL = ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE")
PEND = ("PENDING", "IN_PROGRESS", "QUEUED", "WAITING", "REQUESTED", "EXPECTED", None)
if not states: ci = "—"
elif any(s in FAIL for s in states): ci = "✗"
elif any(s in PEND for s in states): ci = "…"
else: ci = "✓"
print("\t".join([num, ci, str(d.get("state") or ""), str(d.get("isDraft")), str(d.get("reviewDecision") or "")]))
' 2>/dev/null || true)"
            if [[ -n "$parsed" ]]; then
                IFS=$'\t' read -r num ci state draft review <<< "$parsed"
            else
                num="—"; ci="?"
            fi
            pr="#$num"
        fi
        sig="${branch}|${head}|${pr}|${ci}|${dirty}|${state}|${draft}|${review}"
        # Trailing pr_ok lets _list_render distinguish "gh failed/timed out this
        # frame" (carry forward last-known PR data) from a real PR change.
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$scope" "$branch" "$pr" "$ci" "$dirty" "${d}state" "$sig" "$pr_ok"
    done
}

cmd_list() {
    local watch=0 interval=30 max_iters=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --watch)
                watch=1; shift
                # An optional numeric interval may immediately follow --watch.
                # Reject 0 — `sleep 0` would busy-loop, hammering gh every render.
                if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
                    interval="$1"; shift
                    [[ "$interval" -ge 1 ]] || _die "--watch interval must be a positive integer (got $interval)"
                fi
                ;;
            --max-iters)
                [[ $# -ge 2 ]] || _die "--max-iters needs a value"
                [[ "$2" =~ ^[0-9]+$ ]] || _die "--max-iters must be a non-negative integer"
                max_iters="$2"; shift 2 ;;
            -*) _die "unknown flag: $1" ;;
            *) _die "unexpected arg: $1 (list takes no positional args)" ;;
        esac
    done

    if [[ "$watch" -eq 1 ]]; then
        _list_watch "$interval" "$max_iters"
        return
    fi

    # Bare one-shot board — byte-identical to the pre-watch output.
    printf "%-16s %-26s %-7s %-4s %-7s %s\n" "SCOPE" "BRANCH" "PR" "CI" "DIRTY" "SANDBOX"
    printf "%-16s %-26s %-7s %-4s %-7s %s\n" "----" "------" "--" "--" "-----" "-------"
    [[ -d "$SESSIONS_DIR" ]] || { echo "(no sessions — $SESSIONS_DIR does not exist yet)"; return 0; }
    local found=0 scope branch pr ci dirty sandbox sig pr_ok
    while IFS=$'\t' read -r scope branch pr ci dirty sandbox sig pr_ok; do
        found=1
        printf "%-16s %-26s %-7s %-4s %-7s %s\n" "$scope" "$branch" "$pr" "$ci" "$dirty" "$sandbox"
    done < <(_collect_board)
    [[ "$found" -eq 1 ]] || echo "(no active sessions)"
}

# Abbreviate $HOME → ~ in an absolute path. No-op when HOME is unset/empty (the
# `${HOME:-}` read keeps this safe under `set -u` — a bare $HOME would abort) or
# when the path is not under HOME. Used by the live board to keep cells short.
_home_abbrev() {
    local p="$1" home="${HOME:-}"
    if [[ -n "$home" && "$p" == "$home"/* ]]; then
        printf '~/%s' "${p#"$home"/}"
    else
        printf '%s' "$p"
    fi
}

# Render the board ONCE, marking with a leading `*` every row whose signature
# changed vs the snapshot in <sigfile>, then rewrite <sigfile> with the current
# signatures. An empty/absent sigfile is the baseline render — nothing is marked
# (you can't diff against nothing), it only records — which is why a watch loop's
# first frame highlights nothing. A row for a session not in the snapshot (a new
# lane that appeared) marks too. ANSI bold is added only on a TTY; the `*` marker
# is always emitted so the change is visible (and testable) when piped. Kept
# separate from the loop so it is unit-testable against a supplied snapshot file.
_list_render() {
    local sigfile="$1"
    local had_baseline=0
    [[ -s "$sigfile" ]] && had_baseline=1

    printf "%-2s %-16s %-26s %-7s %-4s %-7s %s\n" "" "SCOPE" "BRANCH" "PR" "CI" "DIRTY" "SANDBOX"
    printf "%-2s %-16s %-26s %-7s %-4s %-7s %s\n" "" "----" "------" "--" "--" "-----" "-------"

    # The snapshot always opens with a sentinel line so even an empty-board frame
    # leaves a non-empty file — otherwise the next frame reads "no baseline" and
    # wouldn't mark the first session that appears. awk lookups never match it (no
    # real scope is "#baseline").
    local tmp; tmp="$(mktemp "${TMPDIR:-/tmp}/dev_session_sig.XXXXXX")"
    printf '#baseline\n' > "$tmp"

    local found=0 scope branch pr ci dirty sandbox sig pr_ok prev marker
    local c_branch c_head c_pr c_ci c_dirty c_state c_draft c_review
    local p_pr p_ci p_state p_draft p_review p_skip
    while IFS=$'\t' read -r scope branch pr ci dirty sandbox sig pr_ok; do
        found=1
        prev="$(awk -F'\t' -v s="$scope" '$1==s{print $2; exit}' "$sigfile")"
        # Carry forward the PR-derived columns when gh failed/timed out this frame
        # (pr_ok=0) but a prior snapshot exists, so a transient gh blip isn't
        # reported as a change (the whole board lighting up). The git-stable fields
        # (branch/head/dirty) stay live, so a real commit or dirty-count change in
        # the same frame still marks.
        if [[ "$pr_ok" -eq 0 && -n "$prev" ]]; then
            IFS='|' read -r c_branch c_head c_pr c_ci c_dirty c_state c_draft c_review <<< "$sig"
            IFS='|' read -r p_skip p_skip p_pr p_ci p_skip p_state p_draft p_review <<< "$prev"
            pr="$p_pr"; ci="$p_ci"
            sig="${c_branch}|${c_head}|${p_pr}|${p_ci}|${c_dirty}|${p_state}|${p_draft}|${p_review}"
        fi
        printf '%s\t%s\n' "$scope" "$sig" >> "$tmp"
        # Compact the sandbox for the live board: every sandbox lives under the
        # shared $SESSIONS_DIR (printed once in the watch banner), so strip that
        # prefix → the cell is just "<scope>/state" and the row no longer wraps
        # past the terminal width (the long-absolute-path mess on small terminals).
        # A path outside SESSIONS_DIR (unusual) falls back to ~-abbreviation. Bare
        # `list` is untouched — it keeps the full absolute path (byte-identical AC).
        local sandbox_disp="$sandbox"
        if [[ "$sandbox_disp" == "$SESSIONS_DIR/"* ]]; then
            sandbox_disp="${sandbox_disp#"$SESSIONS_DIR"/}"
        else
            sandbox_disp="$(_home_abbrev "$sandbox_disp")"
        fi
        marker=""
        [[ "$had_baseline" -eq 1 && "$prev" != "$sig" ]] && marker="*"
        if [[ -n "$marker" && -t 1 ]]; then
            printf '\033[1m%-2s %-16s %-26s %-7s %-4s %-7s %s\033[0m\n' "$marker" "$scope" "$branch" "$pr" "$ci" "$dirty" "$sandbox_disp"
        else
            printf '%-2s %-16s %-26s %-7s %-4s %-7s %s\n' "$marker" "$scope" "$branch" "$pr" "$ci" "$dirty" "$sandbox_disp"
        fi
    done < <(_collect_board)
    mv -f "$tmp" "$sigfile"
    if [[ "$found" -ne 1 ]]; then
        # Mirror bare `list`'s two empty states (dir-absent vs present-but-empty).
        if [[ -d "$SESSIONS_DIR" ]]; then
            echo "(no active sessions)"
        else
            echo "(no sessions — $SESSIONS_DIR does not exist yet)"
        fi
    fi
}

# Live board: re-render every <interval>s, marking changed rows, until Ctrl-C (or
# <max_iters> renders, if given — mainly for scripting/tests). Each render diffs
# against the previous via a private snapshot file cleaned up on exit.
_list_watch() {
    local interval="$1" max_iters="$2" sigfile sigfile_q
    sigfile="$(mktemp "${TMPDIR:-/tmp}/dev_session_watch.XXXXXX")"
    # Remove the snapshot on any exit; treat Ctrl-C / TERM as a clean stop (exit 0)
    # rather than the 130/143 a bare signal would yield. The path is %q-escaped and
    # embedded into the trap string now, so the EXIT handler neither dereferences a
    # function-local that's out of scope by script-exit time (under `set -u`) nor
    # breaks on a TMPDIR containing shell metacharacters.
    printf -v sigfile_q '%q' "$sigfile"
    # on_tty: a real, escape-capable terminal (not piped/redirected, not dumb) — so
    # piped runs stay clean escape-free text and the tests stay valid, and a TERM
    # without cursor control doesn't get raw control bytes sprayed at it.
    local on_tty=""; [[ -t 1 && "${TERM:-}" != "dumb" ]] && on_tty=1
    # use_alt: drive the board on the alternate screen buffer (like top/less) so the
    # loop repaints in place instead of scrolling a fresh copy into scrollback, and
    # the pre-watch screen is restored on exit. ONLY for an UNBOUNDED watch (the
    # Ctrl-C-terminated dashboard) — a bounded --max-iters run must leave its final
    # frame on the normal screen, not have the EXIT-trap restore wipe it on
    # completion (it still repaints in place via the per-frame clear below).
    local use_alt=""; [[ -n "$on_tty" && -z "$max_iters" ]] && use_alt=1
    local _restore="rm -f -- $sigfile_q"
    [[ -n "$use_alt" ]] && _restore="printf '\\033[?1049l'; $_restore"
    # shellcheck disable=SC2064 # intentional: expand the escaped path/restore now, not on signal.
    trap "$_restore" EXIT
    # shellcheck disable=SC2064 # intentional: expand the escaped path/restore now, not on signal.
    trap "$_restore; exit 0" INT TERM
    [[ -n "$use_alt" ]] && printf '\033[?1049h'

    # Sandbox root shown once in the banner so each row's SANDBOX cell can stay the
    # short "<scope>/state" tail (see _list_render) instead of a wrapping abs path.
    local sroot; sroot="$(_home_abbrev "$SESSIONS_DIR")"

    # Loop until <max_iters> renders (if given), with no trailing sleep after the
    # last frame. `--max-iters 0` renders zero times; unset runs until Ctrl-C.
    local iter=0
    while [[ -z "$max_iters" || "$iter" -lt "$max_iters" ]]; do
        [[ -n "$on_tty" ]] && printf '\033[H\033[2J'
        printf '[dev-session] watch — every %ss · %s · sandboxes under %s · Ctrl-C to stop\n\n' "$interval" "$(date '+%H:%M:%S')" "$sroot"
        _list_render "$sigfile"
        iter=$((iter + 1))
        [[ -z "$max_iters" || "$iter" -lt "$max_iters" ]] && sleep "$interval"
    done
    # The loop's last command (the guarded sleep) is falsy on the final frame;
    # return 0 explicitly so a clean finish isn't reported as failure under `set -e`.
    return 0
}

cmd_path() {
    local scope="${1:-}"
    [[ -n "$scope" ]] || _die "usage: dev_session.sh path <scope>"
    _slug_ok "$scope" || _die "scope must be a lowercase slug ([a-z0-9-]): got '$scope'"
    local worktree="$SESSIONS_DIR/$scope/wt"
    [[ -d "$worktree" ]] || _die "no session '$scope' (looked in $worktree)"
    echo "$worktree"
}

# Print ONLY the canonical lane-contract text (no JSON, no side effects) — for
# a launcher that wants the raw preamble once and reuses it across every lane
# in a batch (e.g. a parallel-workflow fan-out path), rather than
# parsing it back out of each --headless JSON descriptor.
cmd_print_contract() {
    _lane_contract
}

cmd_rm() {
    local scope="" force=0 keep_branch=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force) force=1; shift ;;
            --keep-branch) keep_branch=1; shift ;;
            -*) _die "unknown flag: $1" ;;
            *) [[ -z "$scope" ]] && scope="$1" && shift || _die "unexpected arg: $1" ;;
        esac
    done
    [[ -n "$scope" ]] || _die "usage: dev_session.sh rm <scope> [--force] [--keep-branch]"
    _slug_ok "$scope" || _die "scope must be a lowercase slug ([a-z0-9-]): got '$scope'"
    local session_dir="$SESSIONS_DIR/$scope"
    local worktree="$session_dir/wt"
    [[ -d "$worktree" ]] || _die "no session '$scope' at $worktree"

    # Resolve the session's OWN base first (recorded by `new`; default main) so the
    # protected-branch guard below knows the real integration ref.
    local expected_branch base dirty
    base="main"  # allow-hardcoded — default base; the session's real base is recorded by `new`
    [[ -s "$session_dir/base" ]] && base="$(cat "$session_dir/base")"

    # Resolve the branch THIS session OWNS — the name `new` recorded, else the
    # default-namespace reconstruction `<prefix>/<scope>`. We NEVER read the
    # worktree's live HEAD: a HEAD that wandered onto another branch (main after a
    # post-merge checkout, or any unrelated branch parked here) must never become the
    # delete target. A pre-metadata session created with a custom --prefix/--branch
    # may therefore orphan its branch here (reconstruction can't know the custom
    # name) — strictly safer than mis-deleting a wandered HEAD.
    expected_branch=""
    [[ -s "$session_dir/branch" ]] && expected_branch="$(cat "$session_dir/branch")"
    [[ -z "${expected_branch//[[:space:]]/}" ]] && expected_branch="${DEFAULT_PREFIX}/${scope}"

    # Determine dirtiness, distinguishing "clean" from "couldn't tell". Under
    # `set -euo pipefail` a broken worktree (a dangling gitlink) makes `git status`
    # non-zero; capturing it in an `if` condition keeps set -e from aborting, and we
    # mark it "?" (undeterminable) so it's treated as POSSIBLY-dirty — requiring
    # --force rather than silently discarding work or aborting opaquely.
    if ! dirty="$(git -C "$worktree" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"; then
        dirty="?"
    fi
    if [[ "$dirty" != "0" && "$force" -eq 0 ]]; then
        _die "worktree has uncommitted or undeterminable changes ($dirty) — commit/push first, or use --force to discard"
    fi

    echo "[dev-session] removing worktree $worktree"
    git -C "$REPO_ROOT" worktree remove ${force:+--force} "$worktree" 2>/dev/null \
        || git -C "$REPO_ROOT" worktree remove --force "$worktree"
    rm -rf "$session_dir"

    if [[ "$keep_branch" -eq 0 ]]; then
        if _is_protected_branch "$expected_branch" "$base"; then
            # The guard that stops the delete-the-wrong-branch catastrophe regardless
            # of how the delete target resolved: a protected branch (the base, or
            # main/master) is never `rm`'s to delete, whatever its merged status.
            echo "[dev-session] refusing to delete protected branch '$expected_branch' — left intact"
        elif ! git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$expected_branch"; then
            echo "[dev-session] no local branch '$expected_branch' to delete (already gone)"
        else
            # "Landed" = the work reached its base one of two ways: an ancestor merge,
            # OR a squash-merged PR — whose commit is NOT an ancestor of the base, so
            # the ancestor check alone wrongly keeps the branch. The PR-state check
            # (via `gh pr list --state merged`) catches the squash case and survives
            # `--delete-branch` (the PR record persists after the remote ref is gone).
            # Either way we've confirmed it landed, so `-D` is safe.
            local landed=0
            # Structural ancestor test, NOT a text-parse of `branch --merged` matched
            # by regex — an unvalidated `--branch` name with a metachar (e.g. a `.`)
            # could match a SIBLING merged branch and falsely delete unmerged work.
            # `--is-ancestor` is reflexive, so a branch at the base tip counts as landed.
            if git -C "$REPO_ROOT" merge-base --is-ancestor "refs/heads/$expected_branch" "origin/$base" 2>/dev/null; then
                landed=1
            else
                # Squash-merge: not an ancestor of the base. Confirm via a merged PR for
                # this head ref AND that its recorded head SHA equals the local tip — so a
                # REUSED branch name carrying new unmerged commits is never force-deleted
                # (its tip SHA won't match the old merged PR's headRefOid).
                local merged_oid local_oid
                merged_oid="$(_gh pr list --head "$expected_branch" --state merged --json headRefOid --jq '.[0].headRefOid // empty')"
                local_oid="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "refs/heads/$expected_branch" 2>/dev/null || true)"
                if [[ -n "$merged_oid" && "$merged_oid" == "$local_oid" ]]; then
                    landed=1
                fi
            fi
            if [[ "$landed" -eq 1 ]]; then
                if git -C "$REPO_ROOT" branch -D "$expected_branch" 2>/dev/null; then
                    echo "[dev-session] deleted landed branch $expected_branch"
                else
                    echo "[dev-session] WARNING: landed branch '$expected_branch' could not be deleted (checked out in another worktree?) — remove it manually"
                fi
            else
                echo "[dev-session] kept branch '$expected_branch' (no merged PR and not an ancestor of origin/$base; delete manually if intended)"
            fi
        fi
    fi
    echo "✓ session '$scope' removed."
}

main() {
    local sub="${1:-}"
    [[ $# -gt 0 ]] && shift || true
    case "$sub" in
        new) cmd_new "$@" ;;
        list|ls) cmd_list "$@" ;;
        path) cmd_path "$@" ;;
        rm|remove) cmd_rm "$@" ;;
        print-contract) cmd_print_contract "$@" ;;
        ""|-h|--help|help)
            sed -n '2,52p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            ;;
        *) _die "unknown subcommand '$sub' (try: new | list | path | rm | print-contract)" ;;
    esac
}

# Run main only when executed, not when sourced (tests source this file to
# exercise _collect_board / _list_render directly with a controlled snapshot).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
