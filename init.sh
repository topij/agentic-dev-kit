#!/bin/sh
# init.sh — bootstrap for the agentic-dev-kit.
#
# Run from the root of the repo you copied this kit into — at adoption, and
# again after pulling a kit update (that is the supported upgrade path).
# Idempotent: re-running re-prompts (showing the current value as the default),
# migrates an older config schema forward without guessing over existing
# values, and never clobbers a narrative doc that is already in use — only one
# still carrying the shipped `devkit-template: unrendered` marker.
#
# Requires: sh, awk, grep, mv. No non-stdlib dependencies.

set -eu

CONFIG_FILE="config/dev-model.yaml"

usage() {
  cat <<'EOF'
Usage: ./init.sh [--help]

Bootstraps the agentic-dev-kit in the current repo:

  1. Prompts for project.name, runtime.default, tracker.backend (+ project name and, for
     Linear, team/project ids), vcs.protected_branch, notify.user_key, and
     review.bots — each showing the current value in config/dev-model.yaml
     as the default. Press Enter to keep the default.
  2. Stamps the answers into config/dev-model.yaml in place.
  3. Migrates an older config schema forward in place (kit.version) and
     stamps the current generation.
  4. Renders the four narrative docs from docs/templates/ — but only when a
     target is missing or still carries the unrendered marker, so a handoff
     you are actually using is left byte-identical.
  5. Appends the kit's state-sandbox paths to .gitignore if they're
     missing (never duplicates a line on re-run).
  6. Installs the pre-push hook as a shim (honoring core.hooksPath).
  7. Prints the runtime-specific session-start invocation.

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

# Insert a block immediately before a top-level section. Used only for schema
# additions introduced after the first template release; existing values are
# preserved rather than guessed over.
insert_before_section() {
  anchor="$1"
  block="$2"
  tmpfile="${CONFIG_FILE}.tmp.$$"
  blockfile="${tmpfile}.block"
  printf '%s\n' "$block" > "$blockfile"
  awk -v anchor="$anchor" -v blockfile="$blockfile" '
    function emit( line) {
      while ((getline line < blockfile) > 0) print line
      close(blockfile)
    }
    index($0, anchor) == 1 && $0 ~ /^[A-Za-z_]/ && !inserted { emit(); inserted = 1 }
    { print }
    END { if (!inserted) emit() }
  ' "$CONFIG_FILE" > "$tmpfile" && mv "$tmpfile" "$CONFIG_FILE"
  rm -f "$blockfile"
}

# Append a block to a named top-level section, immediately before the next one.
append_to_section() {
  section="$1"
  block="$2"
  tmpfile="${CONFIG_FILE}.tmp.$$"
  blockfile="${tmpfile}.block"
  printf '%s\n' "$block" > "$blockfile"
  awk -v section="$section" -v blockfile="$blockfile" '
    function emit( line) {
      while ((getline line < blockfile) > 0) print line
      close(blockfile)
    }
    $0 == section { inside = 1 }
    inside && $0 != section && $0 ~ /^[A-Za-z_][A-Za-z0-9_]*:/ && !inserted {
      emit()
      inserted = 1
      inside = 0
    }
    { print }
    END { if (inside && !inserted) emit() }
  ' "$CONFIG_FILE" > "$tmpfile" && mv "$tmpfile" "$CONFIG_FILE"
  rm -f "$blockfile"
}

# The 1-based line range [start end] of a top-level section's body, or "0 0" if
# the section is absent. A section runs from its header to the next line that
# starts in column 1 with a key.
#
# These two helpers exist because every whole-file `grep '^  key:'` in a
# migration is a latent bug in two directions at once: it misses the key when
# the adopter's file uses a different indent, and it MATCHES a same-named key
# under an unrelated section. Both were shipped and both were caught in review.
section_range() {
  awk -v section="$1" '
    index($0, section) == 1 && $0 ~ /^[A-Za-z_]/ { inside = 1; start = NR; next }
    inside && /^[A-Za-z_][A-Za-z0-9_]*:/ { print start + 1, NR - 1; found = 1; exit }
    END { if (!found) print (inside ? start + 1 : 0), (inside ? NR : 0) }
  ' "$2"
}

# The body lines of a top-level section (empty when absent).
section_lines() {
  range=$(section_range "$1" "$2")
  start=${range% *}
  end=${range#* }
  [ "$start" -gt 0 ] || return 0
  awk -v s="$start" -v e="$end" 'NR >= s && NR <= e' "$2"
}

# Migrate the original single-runtime schema in place. Re-running init.sh is
# documented as idempotent; silently leaving an old config without these keys
# would make the new runtime-aware launchers appear bootstrapped while falling
# back to the wrong behavior.
# Where this repo's engines actually live. Probing beats defaulting: an adopter
# who vendored the kit under scripts/devkit/ (the documented namespaced layout)
# would otherwise be migrated to `engines: scripts`, and every workflow's
# `<engine-dir>/…` reference would resolve to a path with no engines in it —
# silently, since nothing validates the value. Falls back to `scripts` only when
# no engine is found anywhere.
detect_engines_dir() {
  for candidate in scripts scripts/devkit scripts/kit scripts/agentic-dev-kit tools/devkit bin/devkit; do
    for probe in check_doc_budget.py pr_watch.py dev_session.sh; do
      if [ -f "$candidate/$probe" ]; then
        printf '%s\n' "$candidate"
        return 0
      fi
    done
  done
  printf 'scripts\n'
}

migrate_runtime_schema() {
  if ! grep -q '^  engines:' "$CONFIG_FILE"; then
    detected_engines="$(detect_engines_dir)"
    append_to_section "paths:" "  # Directory containing the deterministic kit engines.
  engines: $detected_engines"
    echo "added paths.engines: $detected_engines to config/dev-model.yaml"
  fi

  if ! grep -q '^runtime:' "$CONFIG_FILE"; then
    insert_before_section "doc_budgets:" 'runtime:
  default: claude
  launchers:
    claude: claude
    codex: codex
'
    echo "added runtime mappings to config/dev-model.yaml"
  fi

  if ! grep -q '^  fallback_commands:' "$CONFIG_FILE"; then
    old_fallback=$(get_field "review:" "" "^  fallback_command:")
    [ -n "$old_fallback" ] || old_fallback="/code-review"
    append_to_section "review:" "  fallback_commands:
    claude: $old_fallback
    codex: \"/review\""
    echo "added runtime review fallbacks to config/dev-model.yaml"
  fi

  if ! grep -q '^  tiers:' "$CONFIG_FILE"; then
    old_cheap=$(get_field "models:" "" "^  cheap:")
    old_default=$(get_field "models:" "" "^  default:")
    old_expensive=$(get_field "models:" "" "^  expensive:")
    [ -n "$old_cheap" ] || old_cheap="haiku"
    [ -n "$old_default" ] || old_default="sonnet"
    [ -n "$old_expensive" ] || old_expensive="opus"
    append_to_section "models:" "  tiers:
    cheap: mechanical
    default: standard
    expensive: judgment
  runtime_mappings:
    claude:
      cheap: $old_cheap
      default: $old_default
      expensive: $old_expensive
    codex:
      cheap: low
      default: medium
      expensive: high"
    echo "added runtime model mappings to config/dev-model.yaml"
  fi
}

# Schema additions introduced after the v2 template release. Same idempotent
# shape as migrate_runtime_schema: only ever ADD a missing block, never guess
# over an existing value — re-running init.sh is the supported upgrade path, so
# a migration must be safe to apply to a config that already has it.
migrate_kit_schema() {
  if ! grep -q '^kit:' "$CONFIG_FILE"; then
    # Prepend, so the version stamp reads first. There is no earlier section to
    # anchor before, so insert_before_section targets the first one that exists.
    insert_before_section "project:" 'kit:
  # Which generation of the kit'"'"'s config schema this repo is on. `init.sh` stamps
  # it and migrates an older config forward in place, so re-running `./init.sh`
  # after pulling a kit update is the supported upgrade path.
  version: 2
'
    echo "stamped kit.version=2 in config/dev-model.yaml"
  fi

  if ! grep -q '^  noise_markers:' "$CONFIG_FILE"; then
    append_to_section "review:" '  # Read by pr_watch.py. These used to be literals inside the engine, which meant
  # adopting required EDITING the engine — and an edited engine can never be
  # replaced by a kit update (Principle #10).
  noise_markers:
    - "<!-- this is an auto-generated comment: summarize by coderabbit"
    - "<!-- this is an auto-generated comment: review in progress"
    - "<!-- walkthrough_start -->"
    - "actionable comments posted: 0"
    - "<!-- linear-linkback -->"
  unavailable_markers:
    - "bugbot needs on-demand usage enabled"
    - "review limit reached"
    - "rate limited by coderabbit"
    - "review rate limited"       # the status-check wording of "review limit reached"
    - "couldn'"'"'t start this review"
    - "review skipped"
    - "no review credits"
  informational_checks: [coderabbit]
  # False only for a repo with NO CI at all — otherwise pr-watch never converges.
  require_ci: true'
    echo "added review marker/CI config to config/dev-model.yaml"
  fi

  # A config migrated BEFORE this key existed already has noise_markers, so the
  # block above is skipped and this needs its own guard. Two separate additions,
  # two separate guards — a single guard would silently skip whichever key the
  # adopter's config happens not to have.
  if ! grep -q '^  bot_pending_grace_minutes:' "$CONFIG_FILE"; then
    append_to_section "review:" '  # How long a configured review bot'"'"'s own check may sit pending before the merge
  # gate stops waiting for it. Below this, a pending bot blocks `mergeable` (a
  # receipt recorded now would bind to a review that has not happened); above it,
  # the bot is treated as never going to report, so a dead bot cannot wedge the
  # gate. Never affects `converged`.
  bot_pending_grace_minutes: 15'
    echo "added review.bot_pending_grace_minutes to config/dev-model.yaml"
  fi

  # `review.bots` became load-bearing for the merge gate in the same change:
  # pr_watch reads it to decide which checks and comment authors belong to a
  # reviewer. The interactive prompt later only REWRITES an existing line, so a
  # `review:` section predating the key would silently fall through to the
  # engine default — benign while the default matches, dangerous for an adopter
  # whose reviewer is not CodeRabbit.
  #
  # Scoped to the review SECTION, at any indent. A `^  bots:` guard would both
  # miss a 4-space-indented `review:` block (appending a duplicate at 2 spaces,
  # which the reader resolves last-key-wins — silently dropping the adopter's
  # real value) and be satisfied by an unrelated `bots:` under another section.
  if [ -z "$(section_lines review: "$CONFIG_FILE" | grep -E '^[[:space:]]+bots:')" ]; then
    append_to_section "review:" '  bots: [coderabbit]'
    if [ -n "$(section_lines review: "$CONFIG_FILE" | grep -E '^[[:space:]]+bots:')" ]; then
      echo "added review.bots to config/dev-model.yaml"
    else
      echo "WARNING: could not add review.bots to $CONFIG_FILE — add it by hand," >&2
      echo "         or pr_watch will assume your review bot is CodeRabbit." >&2
    fi
  fi

  # The status-check wording of the same rate-limit outage. Added separately for
  # the same reason: an adopter migrated before it existed keeps their list.
  #
  # EVERYTHING here is scoped to the review section and warns on any path it
  # cannot complete. Both properties are load-bearing and both were got wrong
  # first time: a whole-file idempotency grep matches the phrase in a
  # `noise_markers` entry and skips the migration AND its warning; a whole-file
  # key anchor happily inserts the marker into a same-named list under a
  # different section, then reports success. A migration that silently no-ops is
  # indistinguishable from one that ran, and one that silently writes to the
  # wrong place is worse.
  markers_block=$(section_lines review: "$CONFIG_FILE" | awk '
    /^[[:space:]]+unavailable_markers:/ { in_list = 1; print; next }
    # Comments and blank lines do NOT end the list — treating them as the end
    # truncates the idempotency view, which re-inserts a marker that is already
    # there a few lines further down.
    in_list == 1 && ($0 ~ /^[[:space:]]+- / || $0 ~ /^[[:space:]]*(#.*)?$/) { print; next }
    in_list == 1 { exit }
  ')

  if [ -n "$markers_block" ] \
     && ! printf '%s\n' "$markers_block" | grep -qi 'review rate limited'; then
    # Two list shapes are unsafe to append to, and both are valid YAML the
    # config reader accepts:
    #   - an inline flow list (`unavailable_markers: ["a", "b"]`) — appending a
    #     `- ` line under it yields a key with both a scalar value and children
    #   - a block list whose dashes sit at the KEY's own indent (what several
    #     YAML formatters emit) — inserting at a deeper indent silently orphans
    #     every original entry, and the marker-present post-condition still passes
    # So: require a bare key line, and reuse the indent of the list's own first
    # item rather than assuming one.
    key_line=$(printf '%s\n' "$markers_block" | head -n 1)
    item_indent=$(printf '%s\n' "$markers_block" \
      | awk 'NR > 1 && /^[[:space:]]+- / { sub(/-.*/, ""); print; exit }')
    if printf '%s\n' "$key_line" | grep -qE '^[[:space:]]+unavailable_markers:[[:space:]]*(#.*)?$' \
       && [ -n "$item_indent" ]; then
      tmp="$CONFIG_FILE.tmp.$$"
      # `start`/`end` bound the edit to the review section's line range, so a
      # same-named key elsewhere in the file cannot be targeted by mistake.
      awk -v indent="$item_indent" \
          -v start="$(section_range review: "$CONFIG_FILE" | cut -d' ' -f1)" \
          -v end="$(section_range review: "$CONFIG_FILE" | cut -d' ' -f2)" '
        inserted == 0 && in_list == 1 && $0 !~ /^[[:space:]]+- / {
          print indent "- \"review rate limited\"       # status-check wording of \"review limit reached\""
          inserted = 1
          in_list = 0
        }
        NR >= start && NR <= end && /^[[:space:]]+unavailable_markers:/ { in_list = 1 }
        { print }
        END {
          if (inserted == 0 && in_list == 1)
            print indent "- \"review rate limited\"       # status-check wording of \"review limit reached\""
        }
      ' "$CONFIG_FILE" > "$tmp"
      # Post-conditions, not a trusted exit code. The marker is inserted EARLY,
      # so "the marker is present" alone would also accept a file truncated
      # mid-write (disk full, signal) — hence the record count must be exactly
      # one more than the original. `awk END{print NR}` rather than `wc -l` so a
      # file with no trailing newline is counted the same way on both sides.
      before=$(awk 'END { print NR }' "$CONFIG_FILE")
      after=$(awk 'END { print NR }' "$tmp")
      if printf '%s\n' "$(section_lines review: "$tmp")" | grep -qi 'review rate limited' \
         && [ "$after" -eq "$(( before + 1 ))" ]; then
        mv "$tmp" "$CONFIG_FILE"
        echo "added the status-check rate-limit marker to config/dev-model.yaml"
        rate_limit_marker_added=1
      else
        rm -f "$tmp"
      fi
    fi
    if [ -z "${rate_limit_marker_added:-}" ]; then
      echo "WARNING: could not add the \"review rate limited\" marker to review.unavailable_markers" >&2
      echo "         in $CONFIG_FILE — add it by hand, or a rate-limited review bot that reports" >&2
      echo "         the outage only as a status-check description will read as a clean review." >&2
    fi
  elif [ -z "$markers_block" ]; then
    # No unavailable_markers under review: at all. The engine default applies,
    # which already contains the marker — but say so rather than staying silent,
    # since "absent" and "present and migrated" are indistinguishable otherwise.
    echo "note: review.unavailable_markers is absent from $CONFIG_FILE;" >&2
    echo "      pr_watch's built-in defaults apply (they include the new marker)." >&2
  fi
}

# ── narrative-doc templates ──────────────────────────────────────────────
# The kit SHIPS docs/handoff.md and docs/friction-log.md, so a `cp -r` or a
# "Use this template" clone always lands them before init.sh runs — which used
# to make the "seed only if absent" guard permanently false, and every adopter
# started with an unrendered skeleton. The marker below is what distinguishes
# "the pristine file the kit shipped" from "a handoff someone is actually
# using": a rendered/edited file has no marker and is never touched.
TEMPLATE_MARKER="devkit-template: unrendered"

# _render <template> <target> — substitute the {{TOKENS}} and write.
# awk (not sed) so a value containing /, &, or \ — a tracker URL, most obviously —
# is substituted literally rather than reinterpreted as replacement syntax.
_render() {
  _tmpl="$1"
  _out="$2"
  awk -v project="$name" -v today="$(date +%Y-%m-%d)" \
      -v tracker="$render_tracker_url" -v enginedir="$render_engine_dir" \
      -v handoff="$render_handoff_link" -v handoffhist="$render_handoff_history_link" \
      -v frictionarch="$render_friction_archive_link" '
    function subst(s, tok, val,   i, acc) {
      acc = ""
      while ((i = index(s, tok)) > 0) {
        acc = acc substr(s, 1, i - 1) val
        s = substr(s, i + length(tok))
      }
      return acc s
    }
    {
      line = $0
      line = subst(line, "{{PROJECT_NAME}}", project)
      line = subst(line, "{{DATE}}", today)
      line = subst(line, "{{TRACKER_URL}}", tracker)
      line = subst(line, "{{ENGINE_DIR}}", enginedir)
      line = subst(line, "{{HANDOFF_HISTORY}}", handoffhist)
      line = subst(line, "{{FRICTION_ARCHIVE}}", frictionarch)
      line = subst(line, "{{HANDOFF}}", handoff)
      print line
    }
  ' "$_tmpl" > "${_out}.tmp.$$" && mv "${_out}.tmp.$$" "$_out"
}

# seed_doc <template-basename> <target-path>
seed_doc() {
  _name="$1"
  _target="$2"
  _tmpl="docs/templates/${_name}.md.tmpl"
  [ -n "$_target" ] || return 0
  if [ ! -f "$_tmpl" ]; then
    echo "note: template $_tmpl missing — skipped $_target" >&2
    return 0
  fi
  if [ -f "$_target" ] && ! grep -qF "$TEMPLATE_MARKER" "$_target" 2>/dev/null; then
    echo "$_target already in use — left untouched"
    return 0
  fi
  mkdir -p "$(dirname "$_target")"
  _render "$_tmpl" "$_target"
  echo "seeded $_target"
}

# ── git hooks ────────────────────────────────────────────────────────────
# "A rule that lives only in a doc is a wish" (Principle #8) applies to the kit
# itself: shipping scripts/hooks/pre-push without installing it made the kit's
# own mechanism-over-memory exemplar inert in every adopting repo. Install a
# shim rather than copying the hook body, so the hook stays current when the
# engine is updated, and rather than a relative symlink, so it survives the
# engines dir being vendored at any depth.
install_hooks() {
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "note: not a git repo yet — run 'git init' then re-run ./init.sh to install hooks" >&2
    return 0
  fi
  # core.hooksPath wins over $GIT_DIR/hooks when set (pre-commit and several
  # monorepo setups do set it). `rev-parse --git-path hooks` does NOT honor it,
  # so installing there would put the shim somewhere git never reads — an
  # inert hook, which is the exact failure this whole change exists to remove.
  hookdir="$(git config --get core.hooksPath 2>/dev/null || true)"
  if [ -z "$hookdir" ]; then
    hookdir="$(git rev-parse --git-path hooks 2>/dev/null || echo .git/hooks)"
  fi
  mkdir -p "$hookdir"
  for hook in pre-push; do
    src="${engines_dir}/hooks/${hook}"
    if [ ! -f "$src" ]; then
      continue
    fi
    chmod +x "$src" 2>/dev/null || true
    if [ -e "$hookdir/$hook" ] && ! grep -q 'devkit-hook-shim' "$hookdir/$hook" 2>/dev/null; then
      echo "note: existing $hookdir/$hook left untouched (not a kit shim) — chain it to $src by hand" >&2
      continue
    fi
    cat > "$hookdir/$hook" <<SHIM
#!/bin/sh
# devkit-hook-shim — regenerated by ./init.sh; edit $src, not this file.
root="\$(git rev-parse --show-toplevel)" || exit 0
[ -x "\$root/$src" ] || exit 0
exec "\$root/$src" "\$@"
SHIM
    chmod +x "$hookdir/$hook"
    echo "installed $hookdir/$hook -> $src"
  done
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

migrate_runtime_schema
migrate_kit_schema

# ── prompts ──────────────────────────────────────────────────────────────

cur_name=$(get_field "project:" "" "^  name:")
name=$(ask "Project name" "$cur_name")
set_field "project:" "" "^  name:" "$name"

cur_runtime=$(get_field "runtime:" "" "^  default:")
runtime=$(ask "Agent runtime (claude | codex | none)" "$cur_runtime")
set_field "runtime:" "" "^  default:" "$runtime"

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

cur_tracker_url=$(get_field "tracker:" "" "^  url:")
tracker_url=$(ask "Tracker board URL (shown in the friction-log header; blank is fine)" "$cur_tracker_url")
set_field "tracker:" "" "^  url:" "\"$tracker_url\""

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

# ── seed narrative docs from templates ───────────────────────────────────
# Rendered when the target is MISSING or still carries the unrendered marker.
# The old "seed only if absent" guard could never fire: the kit ships these
# files, so a copy-in / template-clone always landed them first and every
# adopter was left with an unrendered skeleton.

render_engine_dir="$(get_field "paths:" "" "^  engines:")"
[ -n "$render_engine_dir" ] || render_engine_dir="scripts"
engines_dir="$render_engine_dir"
if [ -n "$tracker_url" ]; then
  render_tracker_url="$tracker_url"
else
  render_tracker_url="set \`tracker.url\` in \`$CONFIG_FILE\`"
fi

handoff_path="$(get_field "paths:" "" "^  handoff:")"
[ -n "$handoff_path" ] || handoff_path="docs/handoff.md"
handoff_history_path="$(get_field "paths:" "" "^  handoff_history:")"
[ -n "$handoff_history_path" ] || handoff_history_path="docs/handoff-history.md"
friction_path="$(get_field "paths:" "" "^  friction_log:")"
[ -n "$friction_path" ] || friction_path="docs/friction-log.md"
friction_archive_path="$(get_field "paths:" "" "^  friction_log_archive:")"
[ -n "$friction_archive_path" ] || friction_archive_path="docs/friction-log-archive.md"

# Cross-links inside the rendered docs must point at the CONFIGURED paths, not
# the kit's default filenames — an adopter who repointed paths.handoff_history
# would otherwise ship a doc whose "older entries live in …" link 404s. When the
# two docs are siblings (the common case) a bare filename is the correct relative
# link; otherwise fall back to the repo-relative path.
_doc_link() {
  # _doc_link <from-path> <to-path>
  if [ "$(dirname "$1")" = "$(dirname "$2")" ]; then
    basename "$2"
  else
    printf '%s\n' "$2"
  fi
}
render_handoff_history_link="$(_doc_link "$handoff_path" "$handoff_history_path")"
render_handoff_link="$(_doc_link "$handoff_history_path" "$handoff_path")"
render_friction_archive_link="$(_doc_link "$friction_path" "$friction_archive_path")"

seed_doc "handoff" "$handoff_path"
seed_doc "handoff-history" "$handoff_history_path"
seed_doc "friction-log" "$friction_path"
seed_doc "friction-log-archive" "$friction_archive_path"

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
# dev_session.sh copies a repo-root .mcp.json into each lane worktree so lanes
# inherit MCP access. If yours holds literal credentials rather than ${ENV}
# references, that copy must never be committable from a lane.
if [ -f .mcp.json ] && grep -qE '"(.*_)?(TOKEN|SECRET|KEY|PASSWORD|AUTHORIZATION)" *: *"[^$]' .mcp.json 2>/dev/null; then
  add_ignore_line ".mcp.json"
  echo "note: .mcp.json appears to hold literal credentials — added to .gitignore." >&2
  echo "      Prefer \${ENV_VAR} references so it can stay tracked." >&2
fi

# ── git hooks ────────────────────────────────────────────────────────────

install_hooks

# ── done ───────────────────────────────────────────────────────────────

echo ""
echo "agentic-dev-kit is bootstrapped (kit schema v2)."
echo "Review config/dev-model.yaml for any remaining values (paths, doc_budgets,"
echo "models, review.fallback_commands) and edit to taste."
echo ""
echo "Upgrading later: pull the new kit files, then re-run ./init.sh — it"
echo "migrates an older config forward in place and never touches a narrative"
echo "doc that is actually in use."
echo ""
case "$runtime" in
  codex) echo "You're set — invoke \$session-start next." ;;
  claude) echo "You're set — run /session-start next." ;;
  *) echo "You're set — invoke the session-start workflow in your agent runtime next." ;;
esac
