#!/usr/bin/env bash
# Probe the ALLOW side of a Claude Code permission rule.
#
# Isolation: --restricted ignores user, project and local settings files, so the
# only permission rules in play are the ones this script passes via --settings.
# --tools Bash leaves exactly one tool, so the model has no non-Bash route to the
# observable. The config dir is NOT redirected: --restricted already ignores the
# user settings file, and pointing CLAUDE_CONFIG_DIR at a throwaway dir removes
# the credentials with it ("Not logged in"), which the harness would then have to
# tell apart from a denial.
#
# Observable: whether the file `ran.marker` exists in a fresh cwd afterwards.
# That is ground truth about whether the command executed, independent of
# anything the model says about it.
#
# The `cd` is confined to a subshell: this repo's AGENTS.md records two sessions
# lost to a `cd` outliving its command.
set -u
label="$1"; shift
allow_json="$1"; shift
mode_args=("$@")

root="$(cd "$(dirname "$0")" && pwd)"
dir="$(mktemp -d "${TMPDIR:-/tmp}/adk-allow-XXXXXX")"

settings="{\"permissions\":{\"allow\":${allow_json},\"deny\":[],\"ask\":[]}}"
out="$root/out-${label}.json"
err="$root/err-${label}.txt"

(
  cd "$dir" || exit 97
  env -u ANTHROPIC_API_KEY claude -p \
    --restricted \
    --tools Bash \
    --strict-mcp-config \
    --settings "$settings" \
    --output-format json \
    ${mode_args[@]+"${mode_args[@]}"} \
    >"$out" 2>"$err" <<PROMPT
Use the Bash tool to run exactly this command, once, and then stop:

${CMD:-touch ran.marker}

Do not use any other command. Do not explain. If the command is refused, say REFUSED.
PROMPT
)
status=$?

# A client that never launched leaves no output file. Reporting that as
# DID-NOT-RUN would read as a denial, which is the one confusion this probe
# cannot afford, so it gets its own verdict.
why="$(python3 -c 'import json,sys
try: d=json.load(open(sys.argv[1]))
except Exception as e: print("unparseable:%s" % e); raise SystemExit
r=(d.get("result") or "")
# An error that is not a permission refusal invalidates the run rather than
# answering it: not-logged-in, a bad flag, a model error.
bad=("Not logged in","Invalid API key","Credit balance","error during execution")
print("clienterr:%s" % r[:80] if d.get("is_error") and any(b in r for b in bad) else "")
' "$out" 2>/dev/null)"
if [ ! -s "$out" ]; then
  verdict="HARNESS-ERROR(no client output)"
elif [ -n "$why" ]; then
  verdict="HARNESS-ERROR($why)"
elif [ -f "$dir/ran.marker" ]; then verdict="RAN"; else verdict="DID-NOT-RUN"; fi
printf '%-14s allow=%-22s mode=%-26s exit=%-3s => %s\n' \
  "$label" "$allow_json" "${mode_args[*]+${mode_args[*]}}" "$status" "$verdict"
echo "$dir" > "$root/dir-${label}.txt"
