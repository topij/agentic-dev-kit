#!/bin/sh
# init.sh — bootstrap for the agentic-dev-kit.
#
# Run from the root of the repo you copied this kit into — at adoption, and
# again after pulling a kit update (that is the supported upgrade path).
# Idempotent: re-running re-prompts (showing the current value as the default),
# migrates an older config schema forward without guessing over existing
# values, and never clobbers a doc that is already in use — only one that is
# missing, or whose FIRST LINE opens an HTML comment beginning with one of two
# markers: `devkit-template: unrendered` on a shipped narrative skeleton, or
# `devkit-source: kit-own` on the kit's own root AGENTS.md / CLAUDE.md.
#
# Requires: sh, plus awk, grep, sed, mv, rm, cat, head, mkdir, chmod, touch,
# basename, dirname, date and git. No non-stdlib dependencies.

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
  4. Renders the four narrative docs and both root entry points — AGENTS.md
     (the contract) and CLAUDE.md (the Claude binding that imports it) — from
     docs/templates/, but only when a target is missing or its FIRST LINE
     OPENS AN HTML COMMENT beginning with the unrendered marker or the kit-own
     marker. A file that merely mentions a marker is in use and is left
     byte-identical.
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

# One YAML-aware trailing-comment scanner, shared by get_field and set_field
# (sh has no awk includes, so the function text is spliced into both programs).
# comment_idx(rest) returns the 1-based index where a trailing comment starts,
# or 0. The rules are YAML's (and therefore PyYAML's):
#   - a quote opens a quoted scalar only at the FIRST non-space position; a
#     mid-scalar apostrophe (O'Brien) or quote is literal. An earlier version
#     of this scan opened on any quote character, which silently absorbed a
#     real trailing comment into the value (issue #62, review round on #87).
#   - inside a leading-quoted scalar, # is literal until after the close quote.
#   - in a plain scalar, # opens a comment only when preceded by whitespace:
#     `board#view42` is one token, `board #view42` is a value and a comment.
# The kit's other readers do NOT fully agree with YAML here: kitconfig's
# _strip_comment opens a quote at any position, and devkit_config_scalar strips
# " #…" even inside quotes. Issue #88 tracks converging them; this scanner
# takes YAML's side rather than copying either divergence.
AWK_COMMENT_IDX='
  function comment_idx(rest,   n, i, j, qc, c, prev) {
    n = length(rest)
    i = 1
    while (i <= n && substr(rest, i, 1) ~ /[ \t]/) i++
    if (i > n) return 0
    c = substr(rest, i, 1)
    if (c == "\"" || c == "'\''") {
      qc = c
      j = i + 1
      while (j <= n) {
        if (substr(rest, j, 1) == qc) {
          if (qc == "'\''" && substr(rest, j + 1, 1) == qc) { j += 2; continue }
          break
        }
        j++
      }
      for (j = j + 1; j <= n; j++)
        if (substr(rest, j, 1) == "#") return j
      return 0
    }
    prev = " "
    for (j = i; j <= n; j++) {
      c = substr(rest, j, 1)
      if (c == "#" && prev ~ /[ \t]/) return j
      prev = c
    }
    return 0
  }
'

# get_field <section-line> <subsection-line-or-empty> <key-regex>
# Prints the current value (double quotes stripped, comment stripped, trimmed).
get_field() {
  wantsec="$1"
  wantsub="$2"
  keyre="$3"
  awk -v wantsec="$wantsec" -v wantsub="$wantsub" -v keyre="$keyre" "$AWK_COMMENT_IDX"'
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
        cidx = comment_idx(rest)
        if (cidx > 0) { rest = substr(rest, 1, cidx - 1) }
        gsub(/^[ \t]+|[ \t]+$/, "", rest)
        # Strip one MATCHING pair of double quotes, the way kitconfig does. The
        # old independent-ends gsub ate the closing quote of a value that only
        # ENDS with one (`he said "hi"` -> `he said "hi`) — panel round on #87.
        if (length(rest) >= 2 && substr(rest, 1, 1) == "\"" && substr(rest, length(rest), 1) == "\"") {
          rest = substr(rest, 2, length(rest) - 2)
        }
        print rest
        exit
      }
    }
  ' "$CONFIG_FILE"
}

# set_field <section-line> <subsection-line-or-empty> <key-regex> <new-value-literal>
# Replaces the value for the matched field in place, preserving any
# trailing "# comment" on that line untouched.
#
# The VALUE reaches awk via the environment, never `-v`: `awk -v var=value`
# runs backslash-escape processing on the assignment, so a `\n` or `\\` in a
# prompted answer would be transformed before substitution (issue #62). The
# section/key parameters stay `-v` — they are this script's own literals, not
# adopter data.
set_field() {
  wantsec="$1"
  wantsub="$2"
  keyre="$3"
  newval="$4"
  tmpfile="${CONFIG_FILE}.tmp.$$"
  newval="$newval" awk -v wantsec="$wantsec" -v wantsub="$wantsub" -v keyre="$keyre" "$AWK_COMMENT_IDX"'
    BEGIN { cursec = ""; cursub = ""; newval = ENVIRON["newval"] }
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
        # comment_idx (shared above) finds the comment to re-attach — a blind
        # index() re-attached the tail of the old value as a growing
        # pseudo-comment on every re-run (issue #62).
        cidx = comment_idx(rest)
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
#
# Always returns 0. It is called under `set -eu` by migrations that do not test
# its status, so returning non-zero on "section not found" aborts init.sh
# entirely — which is how an earlier version of this change broke adoption for
# every config lacking one optional section. Callers that need to know whether
# the write landed must check the file afterwards; `ensure_review_key` does.
#
# The header is matched by PREFIX, not equality, so `review: `, `review:\r` and
# `review:  # comment` are still the section. The old `$0 == section` missed all
# three and disagreed with section_range about whether the section existed.
append_to_section() {
  section="$1"
  block="$2"
  tmpfile="${CONFIG_FILE}.tmp.$$"
  blockfile="${tmpfile}.block"
  # Blocks are authored at the kit's own 2-space body indent. Writing them
  # verbatim into a section indented differently produces a mapping with two
  # indent levels — which PyYAML refuses to load at all, taking the WHOLE config
  # down, while the stdlib reader tolerates it and silently applies last-key-
  # wins. Re-indent to whatever the section actually uses.
  body_indent=$(section_lines "$section" "$CONFIG_FILE" \
    | awk 'NF && $0 !~ /^[[:space:]]*#/ { match($0, /^[[:space:]]*/); print RLENGTH; exit }')
  printf '%s\n' "$block" \
    | awk -v extra="$(( ${body_indent:-2} - 2 ))" '
        { printf "%*s%s\n", (extra > 0 ? extra : 0), "", $0 }
      ' > "$blockfile"
  awk -v section="$section" -v blockfile="$blockfile" '
    function emit( line) {
      while ((getline line < blockfile) > 0) print line
      close(blockfile)
    }
    index($0, section) == 1 && $0 ~ /^[A-Za-z_]/ { inside = 1; header = NR }
    inside && NR != header && $0 ~ /^[A-Za-z_][A-Za-z0-9_]*:/ && !inserted {
      emit()
      inserted = 1
      inside = 0
    }
    { print }
    END { if (inside && !inserted) emit() }
  ' "$CONFIG_FILE" > "$tmpfile" && mv "$tmpfile" "$CONFIG_FILE"
  rm -f "$blockfile"
}

# Add one `review:` key if the review SECTION does not already define it.
# Per-key rather than per-block: the old migration appended a block defining
# five keys behind a single `noise_markers` guard, so an adopter who had
# `unavailable_markers` but not `noise_markers` got a SECOND definition of it —
# and both YAML readers resolve last-key-wins, silently replacing their list.
# Section-scoped and indent-agnostic: a whole-file `grep '^  key:'` both misses
# a 4-space-indented `review:` block (then appends a 2-space duplicate into it,
# which is not even valid YAML) and is satisfied by a same-named key under an
# unrelated section (then silently skips).
ensure_review_key() {
  key="$1"
  block="$2"
  if [ -n "$(section_lines review: "$CONFIG_FILE" | grep -E "^[[:space:]]+$key:")" ]; then
    return 0
  fi
  append_to_section "review:" "$block"
  if [ -n "$(section_lines review: "$CONFIG_FILE" | grep -E "^[[:space:]]+$key:")" ]; then
    echo "added review.$key to config/dev-model.yaml"
  else
    echo "WARNING: could not add review.$key to $CONFIG_FILE — add it by hand." >&2
    return 1
  fi
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
    # FIRST match only. append_to_section writes to the first occurrence, so a
    # reader that reported the last one would have the two helpers disagreeing
    # about which block they are talking about on a duplicated section.
    !start && index($0, section) == 1 && $0 ~ /^[A-Za-z_]/ { inside = 1; start = NR; next }
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
  # The names probed for are derived from kit-manifest.json ("role": "engine") —
  # the generated projection of KIT_OWNED, which kit_doctor's engines probe
  # derives from since #59, and the one form of that list sh can read.
  # Restating them here as literals was issue #67: a sized-down install holding
  # only kit_doctor.py and lib/kitconfig.py matched none of the three named
  # files, so this function stamped `engines: scripts` for a tree whose engines
  # live in scripts/devkit. The manifest ships next to init.sh, so it is present
  # at install time; the old triple remains only as the fallback for a copy that
  # lost it. Manifest paths are under the kit's own `scripts/` layout and are
  # probed relative to each candidate — the same prefix swap kit_doctor._remap
  # does.
  #
  # lib/ entries are excluded from DETECTION on purpose: their basenames are
  # generic (repo_root.sh, kitconfig.py), so an adopter's own scripts/lib/ file
  # would make the earlier candidate shadow a kit vendored at scripts/devkit —
  # the review panel on #87 demonstrated exactly that. A top-level engine name
  # is distinctive. The trade accepted here: an install shipping ONLY lib/
  # helpers would fall back to `scripts` undetected — lib/ files are
  # import-only helpers of the top-level engines, and a silent wrong match on
  # an adopter's own file is the worse failure than a conservative default.
  # (kit_doctor keeps lib/ names in ITS probe: it checks a directory the
  # adopter already configured, not a guess.)
  probes=""
  if [ -f kit-manifest.json ]; then
    probes="$(awk -F'"' '
      /^    "/ { key = $2 }
      /^      "role": "engine"/ {
        if (index(key, "scripts/") == 1 && index(key, "scripts/lib/") != 1)
          print substr(key, 9)
      }
    ' kit-manifest.json 2>/dev/null || true)"
    if [ -z "$probes" ]; then
      echo "note: kit-manifest.json is present but no engine entries could be read from it —" >&2
      echo "      falling back to the built-in engine probe list for paths.engines detection." >&2
    fi
  fi
  [ -n "$probes" ] || probes="check_doc_budget.py
pr_watch.py
dev_session.sh"
  # set -f while $probes is word-split unquoted: a glob character in a
  # manifest path must stay literal, never pathname-expand (CodeRabbit on
  # #87). Restored on every exit path — hence the break-out variable rather
  # than returning from inside the loop.
  found=""
  set -f
  for candidate in scripts scripts/devkit scripts/kit scripts/agentic-dev-kit tools/devkit bin/devkit; do
    for probe in $probes; do
      if [ -f "$candidate/$probe" ]; then
        found="$candidate"
        break 2
      fi
    done
  done
  set +f
  printf '%s\n' "${found:-scripts}"
}

# Guards are SECTION-scoped, not whole-file `grep '^  key:'`. That form is a bug
# in two directions at once: it misses the key when the adopter's section uses a
# different indent (so the migration re-runs forever, appending a duplicate each
# time), and it is satisfied by a same-named key under an unrelated section (so
# the migration never runs and says nothing). Both were shipped here.
migrate_runtime_schema() {
  if [ -z "$(section_lines paths: "$CONFIG_FILE" | grep -E '^[[:space:]]+engines:')" ]; then
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

  if [ -z "$(section_lines review: "$CONFIG_FILE" | grep -E '^[[:space:]]+fallback_commands:')" ]; then
    old_fallback=$(get_field "review:" "" "^  fallback_command:")
    [ -n "$old_fallback" ] || old_fallback="/code-review"
    append_to_section "review:" "  fallback_commands:
    claude: $old_fallback
    codex: \"/review\""
    echo "added runtime review fallbacks to config/dev-model.yaml"
  fi

  if [ -z "$(section_lines models: "$CONFIG_FILE" | grep -E '^[[:space:]]+tiers:')" ]; then
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

  ensure_review_key noise_markers '  # Read by pr_watch.py. These used to be literals inside the engine, which meant
  # adopting required EDITING the engine — and an edited engine can never be
  # replaced by a kit update (Principle #10).
  noise_markers:
    - "<!-- this is an auto-generated comment: summarize by coderabbit"
    - "<!-- this is an auto-generated comment: review in progress"
    - "<!-- walkthrough_start -->"
    - "actionable comments posted: 0"
    - "<!-- linear-linkback -->"' || true

  ensure_review_key unavailable_markers '  unavailable_markers:
    - "bugbot needs on-demand usage enabled"
    - "review limit reached"
    - "rate limited by coderabbit"
    - "review rate limited"       # the status-check wording of "review limit reached"
    - "couldn'"'"'t start this review"
    - "review skipped"
    - "no review credits"' || true

  ensure_review_key fallback_panel '  # The independent pass when a configured bot cannot review. One isolated,
  # fresh-context reviewer PER LENS — `safety-critical-changes.md` rule 2 wants two
  # disjoint lenses, which a single command cannot be. `fallback_commands` elsewhere
  # in this section is the DEGRADED one-lens mode for a runtime that cannot isolate
  # a reviewer (a migration appends this block, so the two can land in either order).
  # Which lenses is yours; how to run one is kit doctrine, in
  # docs/agentic-dev-kit/fallback-review-panel.md.
  fallback_panel:
    receipt_source: "fallback:panel"
    # Compute for each panel lens, keyed by runtime. `model` and `effort` are
    # independent and BOTH OPTIONAL — set either, both, or neither; a runtime
    # exposing one control carries one key. Omit a runtime and its lenses inherit
    # the cockpit session'"'"'s compute, which is the behaviour before this key
    # existed. Read by scripts/hooks/pr_followup_hook.py.
    #
    # HOW FAR EACH KEY REACHES depends on the runtime, and on Claude Code today
    # they differ. Its delegation tool takes a `model` parameter, so `model` is a
    # real control. It takes NO per-agent effort parameter, so `effort` reaches
    # the lens only as an instruction in its prompt — honest intent, not a
    # guarantee, and mechanical the moment a runtime exposes it. See
    # docs/agentic-dev-kit/fallback-review-panel.md.
    lens_compute:
      claude:
        model: sonnet
        effort: high
      codex:
        effort: high
    lenses:
      - name: adversarial
        focus: "assume the change is wrong and try to prove it — bypasses, fail-open paths, wedges, and whether the new guard actually guards"
      - name: correctness
        focus: "assume it works and ask what it says — stale comments, claims that overstate what is verified, tests whose names promise more than their bodies check"' || true

  ensure_review_key informational_checks '  informational_checks: [coderabbit]' || true

  ensure_review_key require_ci '  # False only for a repo with NO CI at all — otherwise pr-watch never converges.
  require_ci: true' || true

  ensure_review_key bot_pending_grace_minutes '  # How long a configured review bot'"'"'s own check may sit pending before the merge
  # gate stops waiting for it. Below this, a pending bot blocks `mergeable` (a
  # receipt recorded now would bind to a review that has not happened); above it,
  # the bot is treated as never going to report, so a dead bot cannot wedge the
  # gate. Never affects `converged`.
  bot_pending_grace_minutes: 15' || true

  # `review.bots` became load-bearing for the merge gate in the same change:
  # pr_watch reads it to decide which checks and comment authors belong to a
  # reviewer. The interactive prompt later only REWRITES an existing line, so a
  # `review:` section predating the key would silently fall through to the
  # engine default — benign while the default matches, dangerous for an adopter
  # whose reviewer is not CodeRabbit.
  ensure_review_key bots '  bots: [coderabbit]' || true

  # The status-check wording of the same rate-limit outage (issue #23).
  #
  # DETECT AND INSTRUCT — deliberately not an in-place edit. Three review rounds
  # produced three distinct ways for list surgery to corrupt an adopter's config:
  # inserting at the wrong indent orphaned every existing entry; a whole-file key
  # anchor wrote into a same-named list under another section; and inserting
  # before "the first line that is not an item" splices a multi-line item in
  # half, yielding YAML that PyYAML refuses to load — each while the
  # post-conditions passed and success was printed. The payoff was ONE string in
  # a list an adopter can add in five seconds. That trade is not worth defending
  # a fourth time, so this now reads the config and tells them what to add.
  markers=$(section_lines review: "$CONFIG_FILE" | awk '
    /^[[:space:]]+unavailable_markers:/ { in_list = 1; print; next }
    # Comments, blanks and continuation lines all stay inside the list — ending
    # it early truncates the view and reports a marker as missing when it is
    # simply further down.
    in_list == 1 && $0 !~ /^[[:space:]]*[a-zA-Z_]+:/ { print; next }
    in_list == 1 { exit }
  ')
  # Match the marker in the VALUES only. The kit's own shipped config carries a
  # trailing `# the status-check wording of …` comment on that very line, so a
  # raw-line grep would also be satisfied by an adopter who has the phrase in a
  # comment and not in the list. Quote-aware: a plain `s/#.*//` would also cut a
  # marker containing an issue number (`- "tracked in #23: review rate limited"`)
  # and then ask for a marker that is already there.
  marker_values=$(printf '%s\n' "$markers" | awk '{
    out = ""; qc = ""
    for (i = 1; i <= length($0); i++) {
      c = substr($0, i, 1)
      if (qc == "" && (c == "\"" || c == "'\''")) { qc = c }
      else if (qc != "" && c == qc) { qc = "" }
      else if (qc == "" && c == "#") { break }
      out = out c
    }
    print out
  }')
  if [ -n "$markers" ] && ! printf '%s\n' "$marker_values" | grep -qi 'review rate limited'; then
    # The instruction has to match the list style the adopter actually uses.
    # Telling someone with an inline list to add a `- ` item would have them
    # hang a block item off a flow scalar — this step is read-only, but it would
    # still be walking them into the same corruption the surgery used to cause.
    #
    # Presence of `- ` items is the discriminator, not a `[` on the key line: a
    # flow list may put its value on the FOLLOWING line, where a key-line test
    # sees no bracket and hands out the corrupting advice.
    if printf '%s\n' "$markers" | grep -qE '^[[:space:]]*- '; then
      style=block
    elif printf '%s\n' "$markers" | head -n 1 | grep -qE ':[[:space:]]*\[.*\]'; then
      style=flow
    elif printf '%s\n' "$markers" | grep -q '\['; then
      # A flow list whose brackets are NOT closed on the key line. Valid YAML,
      # but `scripts/lib/kitconfig.py` — the reader every engine uses — parses
      # it to `{}` or `"["`, so the adopter's ENTIRE marker list is already
      # being ignored. Asking them to add one more string to it would be
      # confident, inert advice; the list not working at all is the bigger news.
      style=unreadable
    else
      # A key with no value at all: the reader falls back to the engine
      # defaults, which already contain the marker. Nothing to ask for.
      style=none
    fi
    if [ "$style" = unreadable ]; then
      echo "ACTION NEEDED: review.unavailable_markers in $CONFIG_FILE is a flow list" >&2
      echo "  spanning more than one line. The kit's config reader cannot parse that" >&2
      echo "  spelling, so NONE of your markers are in effect. Put the whole list on the" >&2
      echo "  key's own line (\`unavailable_markers: [\"a\", \"b\"]\`) or use a block list," >&2
      echo '  and include "review rate limited" — see issue #23.' >&2
    elif [ "$style" != none ]; then
      echo "ACTION NEEDED: add \"review rate limited\" to review.unavailable_markers" >&2
      echo "  in $CONFIG_FILE." >&2
      if [ "$style" = flow ]; then
        echo '  Yours is written as an inline list — add the string inside the brackets.' >&2
      else
        echo '    - "review rate limited"' >&2
      fi
      echo "  Without it, a review bot that reports a rate limit ONLY as a status-check" >&2
      echo "  description (CodeRabbit does this) reads as a clean review. See issue #23." >&2
    fi
  fi

}

# ── narrative-doc templates ──────────────────────────────────────────────
# The kit SHIPS docs/handoff.md and docs/friction-log.md, so a `cp -r` or a
# "Use this template" clone always lands them before init.sh runs — which used
# to make the "seed only if absent" guard permanently false, and every adopter
# started with an unrendered skeleton. The marker below is what distinguishes
# "the pristine file the kit shipped" from "a handoff someone is actually
# using": a file whose FIRST LINE does not open a marker comment is in use and is
# never touched — a rendered doc that merely quotes a marker is in use too, which
# is the whole point of the anchoring `_seedable` does (see there for the exact
# rule and the two destructive misses that produced it).
#
# The position matters and is pinned by the suite, since this guard depends on
# it. Matching anywhere in the body meant any in-use file that merely QUOTED the
# marker in prose was treated as pristine and silently overwritten — no backup,
# and the run still reported "seeded". That hit EVERY target: a rendered, in-use
# docs/handoff.md mentioning the marker was destroyed the same way (verified
# against the pre-fix script).
#
# The guard defines "in use" identically for all six targets. AGENTS.md used to
# be the exception — the kit shipped no pre-marked skeleton of it, so it was
# reached by file ABSENCE rather than marker presence, and could therefore never
# be shipped. It no longer is: the kit ships its own AGENTS.md and CLAUDE.md
# carrying KIT_OWN_MARKER, and both go through the same predicate as the rest.
TEMPLATE_MARKER="devkit-template: unrendered"

# The kit's OWN entry points (root AGENTS.md and CLAUDE.md) carry this marker on
# line 1 instead. They exist so a session working *in the kit* is bound by the
# kit's contract — but the quickstart is `cp -r /path/to/agentic-dev-kit/. .`,
# which lands them in the adopter's root, where every word of them is false.
#
# Without a marker they are reached by neither branch of the guard below: they
# exist, and their first line is not TEMPLATE_MARKER, so seed_doc calls them
# "already in use" and the adopter silently keeps the KIT's contract — pointing
# at docs/kit-handoff.md, prescribing `make test`, naming the kit's tracker.
# That is worse than the no-entry-point state it was added to fix, and it is
# invisible: nothing reports it, because "left untouched" is also the correct
# outcome for a file the adopter really is using.
#
# So the discriminator is a marker here too, and AGENTS.md stops being the one
# target reached by ABSENCE. The kit may now ship both files; what it may not do
# is ship them unmarked. `test_kit_own_entry_points_carry_the_marker` pins that.
#
# No apostrophe in the literal, deliberately: every marker here is matched from
# shell, and this repo has already been bitten twice by a value that changed
# meaning between quoting contexts (issue #62, and the awk `-v` escape
# processing above). `kit-own` costs one word and closes that off.
KIT_OWN_MARKER="devkit-source: kit-own"

# _imports_agents_md <path> — true when the file carries an ACTIVE `@AGENTS.md`
# import: one outside fenced code blocks and inline code spans. Claude Code does
# not evaluate import syntax inside either, so a CLAUDE.md that merely DOCUMENTS
# the convention in backticks does not load the shared contract and must not
# read as though it does.
#
# No file the kit ships is that shape — an earlier version of this comment said
# docs/templates/CLAUDE.md.tmpl was, and a grep disproves it: its only
# @AGENTS.md is the live import. The hazard is an adopter's own CLAUDE.md, and
# the code-span form is what prose about the mechanism naturally reaches for —
# docs/getting-started.md:44 writes it that way, though that file never reaches
# this predicate, which only ever reads the adopter's root CLAUDE.md.
#
# This is the TEMPLATE_MARKER class again, one function over: that guard's first
# version matched the marker anywhere in the body, so a file quoting it in prose
# was treated as pristine and silently overwritten. That one was caught by a
# review lens; this one by the review bot, in the PR that re-documented it.
#
# WHAT THIS IMPLEMENTS, and what it does not. Enough of CommonMark's inline and
# leaf-block rules to tell a live import from a quoted one: fenced blocks (0-3
# leading spaces, matched fence character and length, blank-only close), and code
# spans delimited by backtick runs of EQUAL length, carried across lines. It is
# not a Markdown parser. It does not implement backslash escapes, link reference
# definitions, or the rule that strips one space from each end of a span's
# content — none of which change whether an `@AGENTS.md` is inside a span, a
# fence, or a comment, which is the only question asked here.
#
# Residuals, stated rather than discovered:
#   - an `@AGENTS.md` inside a Markdown LINK TARGET still counts;
#   - one inside a BLOCKQUOTE counts, and that is probably right — a blockquote
#     is live prose in CommonMark and Claude Code strips only code spans and
#     fences, so `> @AGENTS.md` plausibly IS an import. Left counting rather
#     than guessed at.
# The first is the permissive direction — it suppresses the hint rather than
# raising a false one — and no realistic CLAUDE.md writes it.
_imports_agents_md() {
  awk '
    # Length of the backtick run starting at pos, 0 if none.
    function run(s, pos,   n) {
      n = 0
      while (substr(s, pos + n, 1) == "`") { n++ }
      return n
    }
    # Leading indent in columns. A tab returns 4 so it can never open a fence.
    function indent(s,   i, c, n) {
      n = 0
      for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (c == " ") { n++ } else if (c == "\t") { return 4 } else { break }
      }
      return n
    }
    {
      line = $0
      from = 1

      # 1. A code span already open from an earlier line closes on a run of
      #    EXACTLY its own length. Until then every line is span content — a
      #    fence marker inside one is content too, so this is checked first.
      if (spanlen > 0) {
        i = 1
        closed = 0
        while (i <= length(line)) {
          if (substr(line, i, 1) == "`") {
            n = run(line, i)
            if (n == spanlen) { spanlen = 0; from = i + n; closed = 1; break }
            i += n
          } else { i++ }
        }
        if (!closed) { next }

      # 1b. An HTML comment open from an earlier line. Claude Code strips
      #     block-level comments before injecting, so an @AGENTS.md inside one
      #     is not an import — and `<!-- TODO: add the @AGENTS.md import -->`
      #     is a plausible thing to write, which then suppressed the hint that
      #     exists to catch exactly that (panel round 6, adversarial).
      } else if (incomment) {
        i = index(line, "-->")
        if (i == 0) { next }
        incomment = 0
        from = i + 3

      # 2. Fences. At most THREE leading spaces — four makes it an indented code
      #    block, which is not a fence, and treating it as one swallowed the
      #    live import that followed. A fence closes only on a run of the same
      #    character at least as long with nothing but blanks after it; an
      #    opening fence may carry an info string (```markdown).
      } else if (fence) {
        bare = line
        sub(/^[[:space:]]*/, "", bare)
        if (indent(line) <= 3 && (substr(bare, 1, 3) == "```" || substr(bare, 1, 3) == "~~~")) {
          ch = substr(bare, 1, 1)
          n = 0
          while (substr(bare, n + 1, 1) == ch) { n++ }
          tail = substr(bare, n + 1)
          sub(/[[:space:]]*$/, "", tail)
          if (ch == fchar && n >= flen && tail == "") { fence = 0 }
        }
        next
      } else {
        bare = line
        sub(/^[[:space:]]*/, "", bare)
        ind = indent(line)
        if (ind <= 3 && (substr(bare, 1, 3) == "```" || substr(bare, 1, 3) == "~~~")) {
          fchar = substr(bare, 1, 1)
          flen = 0
          while (substr(bare, flen + 1, 1) == fchar) { flen++ }
          fence = 1
          next
        }
        # Four or more spaces is an INDENTED CODE BLOCK: content, not live
        # prose, and its backticks open nothing. Scanning it as prose let an
        # unterminated run open a span that then swallowed the live import
        # below — the same defect as reading the line as a fence, reached the
        # other way. Known limit, and the safe direction: a lazy paragraph
        # continuation indented four spaces IS live in CommonMark, and is
        # skipped here, so the hint fires on a file that does import.
        if (ind >= 4) { next }
      }

      # 3. Whatever is left is live text with its code spans removed. A span is
      #    delimited by runs of EQUAL length, so a ``double`` span is one span
      #    and not two empty ones — the single-backtick regex this replaces read
      #    ``@AGENTS.md`` as live prose and suppressed the hint. An unterminated
      #    run opens a span that continues on the next line.
      rest = substr(line, from)
      live = ""
      i = 1
      while (i <= length(rest)) {
        if (substr(rest, i, 1) == "`") {
          n = run(rest, i)
          j = i + n
          closed = 0
          while (j <= length(rest)) {
            if (substr(rest, j, 1) == "`") {
              m = run(rest, j)
              if (m == n) { closed = 1; break }
              j += m
            } else { j++ }
          }
          if (closed) { live = live " "; i = j + n; continue }
          spanlen = n
          break
        }
        # An HTML comment, checked AFTER backticks so a `<!--` inside a code
        # span stays span content — CommonMark parses code spans before inline
        # HTML, and the templates here open with a comment on line 1.
        #
        # No apostrophe anywhere in this awk program: it is a single-quoted
        # shell string, so one closes it and the next line becomes syntax. That
        # is what happened when this comment first said "the repo" possessively
        # — `sh -n` caught it, the suite reported 94 unrelated failures.
        if (substr(rest, i, 4) == "<!--") {
          j = index(substr(rest, i), "-->")
          if (j == 0) { incomment = 1; break }
          live = live " "
          i = i + j + 2
          continue
        }
        live = live substr(rest, i, 1)
        i++
      }
      if (live ~ /(^|[^[:alnum:]])@AGENTS\.md([^[:alnum:]]|$)/) { found = 1; exit }
    }
    END { exit !found }
  ' "$1"
}

# _seedable <path> — true when the target may be written: it is missing, or line
# 1 opens an HTML comment whose FIRST TOKEN is one of the two markers.
#
# The precise property, because two looser versions of it shipped first and each
# destroyed a real file with no backup, reported as `seeded`:
#
#   line 1 matches  <!--  [blanks]  <marker>  [blank or end]
#
# Both ends are anchored. The left alone was not enough — an HTML comment that
# merely mentions a marker mid-sentence passed. The right needs the trailing
# blank or `devkit-source: kit-ownership` matches by prefix.
#
# What this does NOT claim: prose can still qualify if someone writes a comment
# that opens with the marker text. That shape is the marker — the documented way
# to claim such a file is to delete line 1 — so it is the accepted case rather
# than a residual hole. What is excluded is a comment that talks ABOUT the
# convention, which is the shape an adopter actually writes.
#
# For AGENTS.md and CLAUDE.md the loose form was a REGRESSION, not an inherited
# risk: before the kit shipped its own, AGENTS.md was seeded by ABSENCE — an
# existing one was never touched whatever it contained — and CLAUDE.md had no
# seeding path at all. The anchor keeps that property while letting the kit ship
# both, and is applied to TEMPLATE_MARKER too: both markers flow through one
# predicate, and leaving one loose would be the same bug with another literal.
#
# The failure direction is now "an oddly-formatted skeleton is not re-seeded",
# which loses no data.
# _opens_with_marker <rest-of-comment> <marker> — true when the comment's first
# token IS the marker. Anchoring only the LEFT side (`<!--`) is not enough, and
# that was this guard's second miss: `"<!--"*"$MARKER"*` still accepted
#
#   <!-- see the kit's devkit-source: kit-own convention for why this exists -->
#
# because the right side stayed an unanchored substring. Reproduced end-to-end by
# the panel's adversarial lens, round 2 — a real file destroyed, no backup,
# reported as `seeded`. The trailing `[[:space:]]*` arm is what stops
# `devkit-source: kit-ownership` matching by prefix.
#
# LC_ALL=C, in a subshell so it is scoped to the comparison: `[[:space:]]` is
# LOCALE-DEPENDENT, and nothing else here pins the locale. Under the UTF-8
# locale a developer machine actually runs, the shell matched NBSP and U+2028
# while kit_doctor's POSIX_BLANKS did not — so a marker line whose space had
# been typo'd to NBSP (routine when text is pasted from a rich-text source) was
# SEEDABLE to init.sh and "in use" to the doctor. init.sh would overwrite it and
# the doctor would say nothing (panel round 7, adversarial, reproduced across
# four locales). Pinning to C makes the two agree AND picks the safe side: an
# odd blank now means "leave it alone" rather than "overwrite it".
_opens_with_marker() {
  (
    LC_ALL=C
    export LC_ALL
    case "$1" in
      "$2") exit 0 ;;
      "$2"[[:space:]]*) exit 0 ;;
    esac
    exit 1
  )
}

_seedable() {
  # Missing is seedable; existing-but-not-a-regular-file never is. `[ -f ]`
  # alone conflated the two: a DIRECTORY named AGENTS.md is not a regular file,
  # so it read as missing, `mv` moved the rendered temp file INSIDE it, and the
  # run reported `seeded AGENTS.md` having written nothing at that path (panel
  # round 3, adversarial). A broken symlink lands here too, and is likewise left
  # alone rather than silently replaced.
  #
  # A SYMLINK to a regular file resolves as one, so a link whose target opens
  # with a marker is seedable — and `mv` then replaces the LINK with the
  # rendered file. The link target is left byte-identical (mv rewrites the
  # directory entry, it does not follow), so no content is lost; what is lost is
  # the link relationship, and the run says only `seeded`. Disclosed rather than
  # changed: it follows from "marker on line 1 means the kit owns this file",
  # and refusing to seed through a link would be a new rule no review asked for.
  if [ -e "$1" ] || [ -L "$1" ]; then
    [ -f "$1" ] || return 1
  else
    return 0
  fi
  # Everything after line 1's opening `<!--`, leading blanks removed. Empty when
  # line 1 does not open an HTML comment at all, which is the common case for a
  # file the adopter wrote.
  # LC_ALL=C for the same reason as `_opens_with_marker`: this `[[:space:]]` is
  # locale-dependent too, and the two must strip the same characters the doctor
  # strips.
  _rest="$(head -n 1 "$1" 2>/dev/null | LC_ALL=C sed -n 's/^<!--[[:space:]]*//p')"
  [ -n "$_rest" ] || return 1
  _opens_with_marker "$_rest" "$TEMPLATE_MARKER" && return 0
  _opens_with_marker "$_rest" "$KIT_OWN_MARKER" && return 0
  return 1
}

# _render <template> <target> — substitute the {{TOKENS}} and write.
# awk (not sed) so a value containing / or & — a tracker URL, most obviously —
# is substituted literally rather than reinterpreted as replacement syntax.
# The values reach awk via the environment, never `-v`: `-v` runs
# backslash-escape processing on the assignment, which would transform a `\`
# in a value before substitution — the exact hazard an earlier version of this
# comment claimed awk avoided (issue #62). `today` stays `-v`: it is generated
# by this script, not adopter data.
_render() {
  _tmpl="$1"
  _out="$2"
  project="$name" tracker="$render_tracker_url" enginedir="$render_engine_dir" \
  handoff="$render_handoff_link" handoffhist="$render_handoff_history_link" \
  frictionarch="$render_friction_archive_link" \
  handoffpath="$render_handoff_path" protectedbranch="$render_protected_branch" \
  awk -v today="$(date +%Y-%m-%d)" '
    BEGIN {
      project = ENVIRON["project"]; tracker = ENVIRON["tracker"]
      enginedir = ENVIRON["enginedir"]; handoff = ENVIRON["handoff"]
      handoffhist = ENVIRON["handoffhist"]; frictionarch = ENVIRON["frictionarch"]
      handoffpath = ENVIRON["handoffpath"]; protectedbranch = ENVIRON["protectedbranch"]
    }
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
      line = subst(line, "{{HANDOFF_PATH}}", handoffpath)
      line = subst(line, "{{FRICTION_ARCHIVE}}", frictionarch)
      line = subst(line, "{{PROTECTED_BRANCH}}", protectedbranch)
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
  if ! _seedable "$_target"; then
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

# yaml_scalar <value> — the text to stamp for a historically-unquoted prompted
# scalar: double-quoted when the value carries a YAML indicator this helper
# knows AND double-quoting is lossless, raw otherwise (issue #62).
# Double-quote style makes `\` and `"` significant to YAML and get_field does
# not unescape, so blanket quoting would turn a value containing either into an
# unloadable config or a value the kit's readers disagree on (found by the
# review panel on #87). Such values — and a value already carrying its own
# single-quoted style — are stamped as the plain scalars they always were: the
# pre-existing edge, made no worse. NOT covered on purpose: plain-scalar type
# resolution (a name of `true`/`007`/`~` type-flips under PyYAML, exactly as it
# always did when stamped raw). kitconfig and devkit_config_scalar strip one
# matching quote layer on read; get_field above strips a matching double pair.
yaml_scalar() {
  case "$1" in
    "") printf '""\n' ;;
    *'"'*|*'\'*|"'"*) printf '%s\n' "$1" ;;
    *':'*|*'#'*|'['*|']'*|'{'*|'}'*|','*|'-'*|'?'*|'&'*|'*'*|'!'*|'|'*|'>'*|'%'*|'@'*|'`'*|' '*|'	'*|*' '|*'	') printf '"%s"\n' "$1" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

# quoted_scalar <value> — for the fields that have ALWAYS stamped double-quoted
# (tracker.project_name, linear ids, tracker.url, notify.user_key): keep that
# style, but degrade to a raw plain scalar when double-quoting cannot be
# lossless — a value containing `"` or `\` inside double quotes is YAML the
# readers reject or disagree on. Found by the review panel on #87: with
# set_field now preserving backslashes faithfully, blanket-quoting turned a
# valid `url: x\py` into an unloadable config on the re-run path.
quoted_scalar() {
  case "$1" in
    *'"'*|*'\'*) printf '%s\n' "$1" ;;
    *) printf '"%s"\n' "$1" ;;
  esac
}

cur_name=$(get_field "project:" "" "^  name:")
name=$(ask "Project name" "$cur_name")
set_field "project:" "" "^  name:" "$(yaml_scalar "$name")"

cur_runtime=$(get_field "runtime:" "" "^  default:")
runtime=$(ask "Agent runtime (claude | codex | none)" "$cur_runtime")
set_field "runtime:" "" "^  default:" "$(yaml_scalar "$runtime")"

cur_backend=$(get_field "tracker:" "" "^  backend:")
backend=$(ask "Tracker backend (linear | github-issues | jira | none)" "$cur_backend")
set_field "tracker:" "" "^  backend:" "$(yaml_scalar "$backend")"

cur_project_name=$(get_field "tracker:" "" "^  project_name:")
tracker_project_name=$(ask "Tracker project name" "$cur_project_name")
set_field "tracker:" "" "^  project_name:" "$(quoted_scalar "$tracker_project_name")"

if [ "$backend" = "linear" ]; then
  cur_team_id=$(get_field "tracker:" "linear:" "^    team_id:")
  team_id=$(ask "Linear team id" "$cur_team_id")
  set_field "tracker:" "linear:" "^    team_id:" "$(quoted_scalar "$team_id")"

  cur_project_id=$(get_field "tracker:" "linear:" "^    project_id:")
  project_id=$(ask "Linear project id" "$cur_project_id")
  set_field "tracker:" "linear:" "^    project_id:" "$(quoted_scalar "$project_id")"
fi

cur_tracker_url=$(get_field "tracker:" "" "^  url:")
tracker_url=$(ask "Tracker board URL (shown in the friction-log header; blank is fine)" "$cur_tracker_url")
set_field "tracker:" "" "^  url:" "$(quoted_scalar "$tracker_url")"

# Refuse to silently inherit somebody else's tracker.
#
# This file ships with the kit carrying the kit's own board, and `ask()` keeps the
# committed value without prompting when stdin is not a tty — so a piped or scripted
# `./init.sh` would seed an adopter a live, foreign, public tracker that
# triage-friction-log then files real issues into. Erroring is the whole point: the
# silent path is the hazard.
#
# Only fires when there is an origin remote to compare against and it disagrees, so
# the kit's own repo and the test fixtures (which have no remote) are unaffected. No
# hardcoded owner/repo — the comparison is against whatever this checkout points at.
if [ ! -t 0 ] && [ -z "${DEVKIT_ALLOW_FOREIGN_TRACKER:-}" ]; then
  case "$tracker_project_name" in
    */*)
      origin_url=$(git remote get-url origin 2>/dev/null || true)
      if [ -n "$origin_url" ]; then
        case "$origin_url" in
          *"$tracker_project_name"*) : ;;
          *)
            echo "error: non-interactive run would keep tracker.project_name =" >&2
            echo "       '$tracker_project_name', which does not match this repo's origin" >&2
            echo "       ($origin_url). That is another project's tracker, and workflows" >&2
            echo "       would file issues into it." >&2
            echo "  Fix: set tracker.project_name in $CONFIG_FILE, or run ./init.sh" >&2
            echo "       interactively, or set DEVKIT_ALLOW_FOREIGN_TRACKER=1 if this is" >&2
            echo "       deliberate." >&2
            exit 1
            ;;
        esac
      fi
      ;;
  esac
fi

cur_branch=$(get_field "vcs:" "" "^  protected_branch:")
branch=$(ask "Protected branch (PRs target this, never commit to it directly)" "$cur_branch")
set_field "vcs:" "" "^  protected_branch:" "$(yaml_scalar "$branch")"

cur_user_key=$(get_field "notify:" "" "^  user_key:")
user_key=$(ask "Notify user id for approval DMs (blank is fine; see config/dev-model.local.yaml)" "$cur_user_key")
set_field "notify:" "" "^  user_key:" "$(quoted_scalar "$user_key")"

cur_bots_raw=$(get_field "review:" "" "^  bots:")
# Strip surrounding [ ] and item quotes — BOTH styles: a hand-written
# `bots: ['coderabbit']` is valid YAML, and stripping only double quotes fed
# the single-quoted item back through the re-serializer as the literal bot
# name `'coderabbit'`, which pr_watch then silently fails to match (review
# panel on #87). We ask for a plain comma list.
cur_bots_display=$(printf '%s' "$cur_bots_raw" | sed -e 's/^\[//' -e 's/\]$//' -e 's/"//g' -e "s/'//g")
bots_answer=$(ask "Review bots (comma-separated, or 'none')" "$cur_bots_display")
# Tolerate an answer typed with brackets ("[coderabbit]") — it is the same
# comma list, not a nested one (issue #62).
bots_answer=$(printf '%s' "$bots_answer" | sed -e 's/^[[:space:]]*\[//' -e 's/\][[:space:]]*$//')
if [ "$bots_answer" = "none" ] || [ -z "$bots_answer" ]; then
  bots_value="[]"
else
  # Serialize "a, b,c" as a proper flow list with every item QUOTED — an item
  # is data, not YAML (issue #62). The answer arrives on stdin, so nothing
  # escape-processes it; quotes already on a re-run's kept default are stripped
  # before re-quoting, keeping the re-stamp stable.
  bots_value="[$(printf '%s\n' "$bots_answer" | awk -F',' '{
    out = ""
    for (i = 1; i <= NF; i++) {
      item = $i
      gsub(/^[ \t]+|[ \t]+$/, "", item)
      gsub(/^["'\'']|["'\'']$/, "", item)
      # A quote or backslash cannot be part of a legitimate bot handle, and
      # inside a double-quoted flow item either would corrupt the whole list
      # the way the scalar helpers now refuse to — drop them rather than
      # stamp unloadable YAML (CodeRabbit on #87).
      gsub(/["\\]/, "", item)
      if (item == "") continue
      out = out (out == "" ? "" : ", ") "\"" item "\""
    }
    print out
  }')]"
fi
set_field "review:" "" "^  bots:" "$bots_value"

# ── seed narrative docs and entry points from templates ──────────────────
# Rendered when the target is MISSING, or its FIRST LINE opens an HTML comment
# beginning with either marker — see `_seedable`.
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
# AGENTS.md renders at the repo root, so its handoff link is the repo-relative
# configured path — the sibling-relative `_doc_link` forms above would 404 from
# there whenever the handoff lives in a subdirectory (the default).
render_handoff_path="$handoff_path"
render_protected_branch="$branch"
[ -n "$render_protected_branch" ] || render_protected_branch="main"

seed_doc "handoff" "$handoff_path"
seed_doc "handoff-history" "$handoff_history_path"
seed_doc "friction-log" "$friction_path"
seed_doc "friction-log-archive" "$friction_archive_path"
# The two runtime entry points (#92). AGENTS.md holds the contract; CLAUDE.md is
# a thin binding that imports it, because Claude Code reads CLAUDE.md and NOT
# AGENTS.md, and its `@path` import expands into context at session start. So one
# file states the contract and both runtimes load it in full — the alternative,
# a copy of the contract per runtime, is the fork `safety-critical-changes.md`
# forbids and `#273` is filed about.
#
# Both are seeded, and both are reached by the kit-own marker rather than by
# absence — see KIT_OWN_MARKER. An adopter's own file carries neither marker and
# is never touched; unlike an engine, the rendered files are theirs to extend.
seed_doc "AGENTS" "AGENTS.md"
seed_doc "CLAUDE" "CLAUDE.md"

# A CLAUDE.md the adopter was already using is left untouched, which is correct —
# but then nothing pulls AGENTS.md into a Claude session, and the two runtimes
# read different contracts. That is the exact divergence this pair exists to
# prevent, reached through the guard that protects their file. Report it; never
# edit their file to fix it.
if [ -f CLAUDE.md ] && ! _imports_agents_md CLAUDE.md; then
  echo "note: CLAUDE.md does not import AGENTS.md, and Claude Code reads CLAUDE.md only."
  echo "      Add a line '@AGENTS.md' near its top so both runtimes read one contract."
fi

# ── .gitignore: state sandbox paths ───────────────────────────────────────

touch .gitignore
add_ignore_line() {
  entry="$1"
  if ! grep -qxF "$entry" .gitignore 2>/dev/null; then
    # Append a newline first when the file does not end in one, or the new entry
    # concatenates onto the last line and silently un-ignores it: a .gitignore
    # ending `.env` (no newline) became `.envstate/`, so `.env` stopped being
    # ignored by the very helper that exists for secret hygiene (panel).
    if [ -s .gitignore ] && [ "$(tail -c 1 .gitignore | wc -l)" -eq 0 ]; then
      printf '\n' >> .gitignore
    fi
    printf '%s\n' "$entry" >> .gitignore
    echo "added '$entry' to .gitignore"
  fi
}
add_ignore_line "state/"
add_ignore_line ".devkit_state_root"
# A runtime that isolates review lenses by worktree may place one here. The
# "No writes in the tree you were given" contract item of fallback-review-panel.md
# forbids a lens from writing inside a tree it
# did not create, so this is not lens scratch — it is somebody else's tree, and
# either way it must never be committed back into the repo.
add_ignore_line ".claude/worktrees/"
# Staged writes from scripts/lib/atomic_write.py, which publishes a narrative doc
# by renaming a temp over it rather than truncating it (#164). The module removes
# its own temp on every path it controls, but SIGKILL runs no handler — and the
# debris lands beside the living handoff, which is where wrap-up stages files.
add_ignore_line "*.devkit-tmp"
# Pipeline reports (triage proposals, systemize digests) are derived scratch from
# the same runs that write state/, and the workflows commit only the doc/skill/
# config paths they edited — never reports/.
add_ignore_line "reports/"
# The local config overlay. kitconfig.load_config() merges it over
# config/dev-model.yaml per leaf, so it is where a value that must not enter git
# lives — the operator id an approval DM targets, a tracker team id. This line is
# the whole protection: .gitignore is adopter-owned, so without seeding it here an
# adopter following docs/getting-started.md would write an identity into a tracked
# path while every doc told them it was ignored (panel, adversarial lens).
add_ignore_line "config/*.local.yaml"
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
echo "models, review.fallback_panel.lenses) and edit to taste."
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
