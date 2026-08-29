# Claude `permissions.allow` whole-tool grants — live validation

Produced from a Claude Code session on 2026-08-29 to settle `#606`'s residual after
`#637` (squash `83b959e`): `scripts/kit_doctor.py`'s `_bash_allow_prefixes` treated
`Bash`, `Bash(*)` and `Bash(:*)` as granting every command, and that was the one
behavioural claim in `#637` that shipped without a stamp.

Two earlier probes disagreed on two of the three spellings, and neither settled it. The
cockpit probe reached only the **deny** matcher, because headless `-p` does not gate on
the absence of an `allow` rule. The correctness lens reached the allow side by injecting
settings inline past an untrusted-workspace suppression, and stated that as a caveat on
its own result. This record replaces both with a measurement taken under a configuration
whose allow-gating is itself demonstrated.

## Client and harness

- Client: `claude --version` → `2.1.251 (Claude Code)`.
- Harness: `probe-bash-allow_2026-08-29.sh`, beside this file.
  `sha256 7298972c943ada93005b5cd158afb781c8102f8f117552b1e9c65b929c8bf0be`.
  Every run below was taken with those bytes.
- Invocation, per run:

  ```
  claude -p --restricted --tools Bash --strict-mcp-config \
         --settings '{"permissions":{"allow":<RULE>,"deny":[],"ask":[]}}' \
         --output-format json
  ```

  with a fresh `mktemp -d` as the working directory and the prompt on stdin.

**Why this configuration and not the obvious one.** `--restricted` ignores the user,
project and local settings files, so the rule under test is the only rule in play;
`--tools Bash` leaves one tool, so the model has no non-Bash route to the observable;
`--strict-mcp-config` drops MCP servers. `CLAUDE_CONFIG_DIR` is deliberately **not**
redirected: pointing it at a throwaway directory removes the credentials along with the
settings, and the client then answers `Not logged in`, which an earlier iteration of
this harness scored as a refusal. The harness now reports that shape as
`HARNESS-ERROR` instead.

**The observable is the filesystem, not the transcript.** Each run asks for one command
that creates `ran.marker` in the empty working directory; the verdict is whether that
file exists afterwards. Beside it, `--output-format json` carries the client's own
`permission_denials` array, which records a refusal the harness did not have to infer
from anything the model said.

## The control that makes the rest readable

A configuration that does not gate on `allow` would return `RAN` for every rule and
look like agreement. So the empty allow list is run as a control:

| run | rule | marker | `permission_denials` |
|---|---|---|---|
| `neg-ctrl`, `neg-ctrl-r2` | `[]` | absent | 1 — `touch ran.marker` |
| `negctrl-cmd2` | `[]` | absent | 1 — `printf x > ran.marker` |
| `pos-ctrl`, `pos-ctrl-r2` | `["Bash(touch:*)"]` | present | 0 |

**This configuration gates on `allow`.** With no rule the exact probe command was
refused and the client recorded the denial; with a covering rule the same command ran.

## The three spellings

Each spelling was run twice with `touch ran.marker`, and once with a second, differently
shaped command (`printf x > ran.marker`, which adds a redirection) to check that a grant
is not specific to one verb.

| rule | `touch` | `touch` repeat | `printf >` | verdict |
|---|---|---|---|---|
| `Bash` | RAN | RAN | RAN | **grants every command** |
| `Bash(*)` | RAN | RAN | RAN | **grants every command** |
| `Bash(:*)` | refused | refused | refused | **grants nothing** |

Every `Bash(:*)` refusal carried a `permission_denials` entry naming the command, so it
is the permission layer refusing and not the model declining.

## The exact-vs-prefix pair, re-measured on this side

`_bash_allow_prefixes` also documents that a rule without the `:*` suffix is an exact
command match rather than a prefix. That claim had been measured against the deny
matcher only, with the shared grammar carrying it across. The same harness settles it
directly:

| run | rule | command | marker | denials |
|---|---|---|---|---|
| `exact-match` | `Bash(touch ran.marker)` | `touch ran.marker` | present | 0 |
| `exact-plusarg` | `Bash(touch ran.marker)` | `touch ran.marker extra.txt` | absent | 1 |
| `prefix-plusarg` | `Bash(touch:*)` | `touch ran.marker extra.txt` | present | 0 |

The allow side agrees with the deny-side reading, so that docstring's caveat is now a
measurement rather than an inference from a shared grammar.

## What changed in the code

- `Bash(:*)` left the whole-tool tuple in `_bash_allow_prefixes`. It needs no
  compensating branch: it still matches `_BASH_PERMISSION_RULE`, contributes the empty
  prefix, lexes to no words, and `_grants_invocation` rejects an empty word list — so it
  grants nothing by the same route every other non-covering rule does.
- `test_a_whole_tool_bash_grant_covers_every_engine` lost its `Bash(:*)` case, which
  moved to `test_a_rule_that_does_not_reach_the_engine_leaves_it_ungranted`.

## What this does not establish

- Only the `Bash` tool was exercised. Whether `Edit(:*)` or another tool's bare-suffix
  form behaves the same way is untested; nothing here should be read as a claim about
  the rule grammar in general.
- The runs are headless `-p` under `--restricted`. An interactive session merges user
  and project settings this configuration deliberately excludes, and its trust prompt is
  a separate gate; the rule *semantics* are the shared part, and are what was measured.
- `--permission-mode` was left unset in every run. The other modes were not swept.
