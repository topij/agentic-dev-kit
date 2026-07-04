#!/bin/sh
# init.sh — bootstrap for the agentic-dev-kit.
#
# Run once from the root of the repo you copied this kit into. Idempotent:
# re-running re-prompts (showing the current value as the default) and only
# ever adds missing lines — it never clobbers docs/handoff.md,
# docs/friction-log.md, or duplicates .gitignore entries.
#
# Requires: sh, awk, grep, mv. No non-stdlib dependencies.

set -eu

CONFIG_FILE="config/dev-model.yaml"

usage() {
  cat <<'EOF'
Usage: ./init.sh [--help]

Bootstraps the agentic-dev-kit in the current repo:

  1. Prompts for project.name, tracker.backend (+ project name and, for
     Linear, team/project ids), vcs.protected_branch, notify.user_key, and
     review.bots — each showing the current value in config/dev-model.yaml
     as the default. Press Enter to keep the default.
  2. Stamps the answers into config/dev-model.yaml in place.
  3. Seeds docs/handoff.md and docs/friction-log.md from the kit's
     skeletons, but ONLY if those files don't already exist.
  4. Appends the kit's state-sandbox paths to .gitignore if they're
     missing (never duplicates a line on re-run).
  5. Prints the next step: run /session-start.

Safe to re-run at any time. Run it from the repo root (the directory that
contains config/dev-model.yaml).
EOF
}

for arg in "$@"; do
  case "$arg" in
    --help|-h)
      usage
      exit 0
      ;;
  esac
done

if [ ! -f "$CONFIG_FILE" ]; then
  echo "error: $CONFIG_FILE not found." >&2
  echo "Run this script from the root of the repo you copied the kit into" >&2
  echo "(the directory that contains config/dev-model.yaml)." >&2
  exit 1
fi

# ── field get/set helpers ───────────────────────────────────────────────
# The config file is a flat, hand-authored YAML doc with predictable
# indentation (0 spaces = top-level section, 2 spaces = field or
# subsection, 4 spaces = field nested one subsection deep). These helpers
# track which section/subsection we're in as they scan, so a field name
# that repeats under two different sections (e.g. "backend:" under both
# tracker: and notify:) is never ambiguous.

# get_field <section-line> <subsection-line-or-empty> <key-regex>
# Prints the current value (quotes stripped, comment stripped, trimmed).
get_field() {
  wantsec="$1"
  wantsub="$2"
  keyre="$3"
  awk -v wantsec="$wantsec" -v wantsub="$wantsub" -v keyre="$keyre" '
    BEGIN { cursec = ""; cursub = "" }
    {
      line = $0
      if (line ~ /^[A-Za-z_][A-Za-z0-9_]*:[ \t]*$/) {
        cursec = line
        gsub(/^[ \t]+|[ \t]+$/, "", cursec)
        cursub = ""
        next
      }
      if (line ~ /^  [A-Za-z_][A-Za-z0-9_]*:[ \t]*$/) {
        cursub = line
        gsub(/^[ \t]+|[ \t]+$/, "", cursub)
        next
      }
      if (cursec == wantsec && cursub == wantsub && line ~ keyre) {
        idx = index(line, ":")
        rest = substr(line, idx + 1)
        cidx = index(rest, "#")
        if (cidx > 0) { rest = substr(rest, 1, cidx - 1) }
        gsub(/^[ \t]+|[ \t]+$/, "", rest)
        gsub(/^"|"$/, "", rest)
        print rest
        exit
      }
    }
  ' "$CONFIG_FILE"
}

# set_field <section-line> <subsection-line-or-empty> <key-regex> <new-value-literal>
# Replaces the value for the matched field in place, preserving any
# trailing "# comment" on that line untouched.
set_field() {
  wantsec="$1"
  wantsub="$2"
  keyre="$3"
  newval="$4"
  tmpfile="${CONFIG_FILE}.tmp.$$"
  awk -v wantsec="$wantsec" -v wantsub="$wantsub" -v keyre="$keyre" -v newval="$newval" '
    BEGIN { cursec = ""; cursub = "" }
    {
      line = $0
      if (line ~ /^[A-Za-z_][A-Za-z0-9_]*:[ \t]*$/) {
        cursec = line
        gsub(/^[ \t]+|[ \t]+$/, "", cursec)
        cursub = ""
        print line
        next
      }
      if (line ~ /^  [A-Za-z_][A-Za-z0-9_]*:[ \t]*$/) {
        cursub = line
        gsub(/^[ \t]+|[ \t]+$/, "", cursub)
        print line
        next
      }
      if (cursec == wantsec && cursub == wantsub && line ~ keyre) {
        idx = index(line, ":")
        prefix = substr(line, 1, idx)
        rest = substr(line, idx + 1)
        cidx = index(rest, "#")
        if (cidx > 0) {
          comment = substr(rest, cidx)
          printf "%s %s  %s\n", prefix, newval, comment
        } else {
          printf "%s %s\n", prefix, newval
        }
        next
      }
      print line
    }
  ' "$CONFIG_FILE" > "$tmpfile" && mv "$tmpfile" "$CONFIG_FILE"
}

# ask <prompt> <default> -> prints the answer (default kept on empty input
# or when stdin isn't a terminal, e.g. running init.sh from a non-interactive
# script).
ask() {
  prompt="$1"
  default="$2"
  if [ -t 0 ]; then
    printf '%s [%s]: ' "$prompt" "$default" >&2
    IFS= read -r answer || answer=""
  else
    answer=""
  fi
  if [ -z "$answer" ]; then
    printf '%s\n' "$default"
  else
    printf '%s\n' "$answer"
  fi
}

if [ ! -t 0 ]; then
  echo "note: no terminal attached — keeping all current config/dev-model.yaml values." >&2
fi

# ── prompts ──────────────────────────────────────────────────────────────

cur_name=$(get_field "project:" "" "^  name:")
name=$(ask "Project name" "$cur_name")
set_field "project:" "" "^  name:" "$name"

cur_backend=$(get_field "tracker:" "" "^  backend:")
backend=$(ask "Tracker backend (linear | github-issues | jira | none)" "$cur_backend")
set_field "tracker:" "" "^  backend:" "$backend"

cur_project_name=$(get_field "tracker:" "" "^  project_name:")
tracker_project_name=$(ask "Tracker project name" "$cur_project_name")
set_field "tracker:" "" "^  project_name:" "\"$tracker_project_name\""

if [ "$backend" = "linear" ]; then
  cur_team_id=$(get_field "tracker:" "linear:" "^    team_id:")
  team_id=$(ask "Linear team id" "$cur_team_id")
  set_field "tracker:" "linear:" "^    team_id:" "\"$team_id\""

  cur_project_id=$(get_field "tracker:" "linear:" "^    project_id:")
  project_id=$(ask "Linear project id" "$cur_project_id")
  set_field "tracker:" "linear:" "^    project_id:" "\"$project_id\""
fi

cur_branch=$(get_field "vcs:" "" "^  protected_branch:")
branch=$(ask "Protected branch (PRs target this, never commit to it directly)" "$cur_branch")
set_field "vcs:" "" "^  protected_branch:" "$branch"

cur_user_key=$(get_field "notify:" "" "^  user_key:")
user_key=$(ask "Notify user key (a key into your project's own notify config)" "$cur_user_key")
set_field "notify:" "" "^  user_key:" "\"$user_key\""

cur_bots_raw=$(get_field "review:" "" "^  bots:")
# Strip surrounding [ ] for display, since we ask for a plain comma list.
cur_bots_display=$(printf '%s' "$cur_bots_raw" | sed -e 's/^\[//' -e 's/\]$//')
bots_answer=$(ask "Review bots (comma-separated, or 'none')" "$cur_bots_display")
if [ "$bots_answer" = "none" ] || [ -z "$bots_answer" ]; then
  bots_value="[]"
else
  # normalize "a, b,c" -> "[a, b, c]"
  bots_value="[$(printf '%s' "$bots_answer" | sed -e 's/[[:space:]]*,[[:space:]]*/, /g' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')]"
fi
set_field "review:" "" "^  bots:" "$bots_value"

# ── seed narrative docs (never clobber) ──────────────────────────────────

if [ ! -f docs/handoff.md ]; then
  mkdir -p docs
  cat > docs/handoff.md <<EOF
# ${name} — Living Plan (Handoff)

> **Forward-looking handoff (Principle #1).** Read this at the start of every session
> (\`/session-start\`); update it at the end (\`/wrap-up\`). This file — not an agent's
> memory, not a scratch note — is the single source of truth for what's done, in
> progress, and next.
>
> Older session blocks graduate to [\`handoff-history.md\`](handoff-history.md) once this
> file crosses its line budget (a warn-only tripwire — \`scripts/check_doc_budget.py\`).
> Session-scoped scratch plans are exactly that: scratch. This is the handoff.

Last updated: YYYY-MM-DD — <one-line theme of the most recent session>

## Latest session — YYYY-MM-DD

**Theme —** <what this session was about, in a line or two.>

- <what shipped>
- <what was decided>
- <what was learned>

▶ Next: <the single clearest next step — what the next \`/session-start\` should pick up.>

______________________________________________________________________

> Older session entries live in [\`handoff-history.md\`](handoff-history.md).
EOF
  echo "seeded docs/handoff.md"
else
  echo "docs/handoff.md already exists — left untouched"
fi

if [ ! -f docs/friction-log.md ]; then
  mkdir -p docs
  cat > docs/friction-log.md <<'EOF'
# Friction Log

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real
> use — a bug, an awkward workflow, a recurring annoyance — recorded the moment it's
> fresh, at session end. A periodic triage (`/triage-friction-log`) reads new entries and
> routes each one: single incidents go **down** to the tracker; a genuine, multi-occurrence
> **pattern** graduates **up** into a rule or skill change. Route down by default, up only
> on repetition — so the flywheel self-regulates instead of ratcheting every week.
>
> Each entry: the observed issue, the date surfaced, a rough severity (**H**igh / **M**edium
> / **L**ow), and a proposed fix or next step. Link related PRs, commits, or tracker items
> when available. Graduated entries are swept to
> [`friction-log-archive.md`](friction-log-archive.md) so this file stays just the current
> inbox plus the most-recent graduation marker.
>
> Tracker board: set `tracker.url` in `config/dev-model.yaml`.

## YYYY-MM-DD — inbox

- **<one-line issue> (severity: <H/M/L>).** <what happened, and a proposed fix or next step.>
EOF
  echo "seeded docs/friction-log.md"
else
  echo "docs/friction-log.md already exists — left untouched"
fi

# ── .gitignore: state sandbox paths ───────────────────────────────────────

touch .gitignore
add_ignore_line() {
  entry="$1"
  if ! grep -qxF "$entry" .gitignore 2>/dev/null; then
    printf '%s\n' "$entry" >> .gitignore
    echo "added '$entry' to .gitignore"
  fi
}
add_ignore_line "state/"
add_ignore_line ".devkit_state_root"

# ── done ───────────────────────────────────────────────────────────────

echo ""
echo "agentic-dev-kit is bootstrapped."
echo "Review config/dev-model.yaml for any remaining values (paths, doc_budgets,"
echo "models, tracker.url, review.fallback_command) and edit to taste."
echo ""
echo "You're set — run /session-start next."
