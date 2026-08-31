#!/usr/bin/env python3
"""PostToolUse hook: enforce PR state, then mandate the watch-fix loop.

Registered on BOTH runtimes, and told which one it is running under via
`--runtime claude|codex` (#301):

  - `.claude/settings.json` — `hooks.PostToolUse`, matcher `Bash`, plus a broad
    `if: "Bash(*)"` tool-level filter. The hook itself must narrow the command:
    valid shell wrappers and inherited `gh` options do not start with literal
    `gh pr`, so a narrower runtime adapter silently changes the shared policy.
  - `.codex/hooks.json` — `hooks.PostToolUse`, matcher `^Bash$`. Codex's matcher
    filters the TOOL NAME only, with no equivalent of Claude's `if`, so this
    script is invoked on every Bash call there and does all the narrowing itself.

Either way it narrows to `gh pr create` / `gh pr ready` and injects an
`additionalContext` instruction so the session enforces the matching lifecycle
without being asked: ready creation / transition asserts ready before the kit's
PR follow-through loop, while bounded draft creation asserts draft and defers
that loop until the same run finishes and marks ready. Both runtimes honour the
same `hookSpecificOutput.additionalContext` contract.
This closes the gap where the kit only had prose asking the agent to run `/pr-watch`
unasked (Principle #8: "a rule that lives only in a doc is a wish").

Generalized from a project-specific version: the reminder names whichever review
bot(s) and the fallback PANEL (or, when fewer than two lenses are configured,
the single fallback command) this repo actually configures, read from
`config/dev-model.yaml` via `scripts/lib/kitconfig.py` — never a hardcoded bot name
(Principle #10, "No hardcoding"). `paths.engines` resolves where `pr_watch.py` lives
so the reminder's poll command is correct even when the kit is vendored under a
nested engines dir. If config can't be read (missing file, kitconfig import
failure, or this script's own repo-root walk fails), the reminder still fires with
generic, runtime-agnostic wording rather than skipping the nag entirely — a
degraded reminder is better than a silently missing one.

Cron-safe: a no-op when `JOB_NAME` is set (the kit's own cron/CI signal — see
`scripts/lib/state_paths/resolver.py`), so a scheduled workflow's own PR-opens never
trigger it. Always exits 0 — a hook must never fail a session.

Reads the PostToolUse JSON on stdin. The bash command is at `.tool_input.command`
and what the tool reported is at `.tool_response` — BOTH are consulted, because
the command alone matches anything that merely quotes it (#302).
To inject context from a PostToolUse hook you print
`{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": …}}`
(plain stdout is not surfaced for PostToolUse).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

# The command is a NECESSARY condition, never a sufficient one (#302). Parse
# actual shell-command starts instead of searching for a phrase: a PR body can
# quote ``gh pr ready``, while GitHub CLI's inherited ``-R/--repo`` option can
# legitimately sit between ``gh`` and ``pr``. The response below remains the
# sufficient evidence that the selected command actually changed a PR.
_SHELL_CONTROL_CHARS = frozenset(";&|()\n")
_GH_GLOBAL_OPTIONS_WITH_VALUE = frozenset(
    {"-R", "--repo", "--hostname", "--config-dir"}
)
_GH_GLOBAL_OPTIONS_WITHOUT_VALUE = frozenset({"--help", "--version"})
_CREATE_OPTIONS_WITH_VALUE = frozenset(
    {
        "-a",
        "--assignee",
        "-B",
        "--base",
        "-b",
        "--body",
        "-F",
        "--body-file",
        "-H",
        "--head",
        "-l",
        "--label",
        "-m",
        "--milestone",
        "-p",
        "--project",
        "--recover",
        "-r",
        "--reviewer",
        "-T",
        "--template",
        "-t",
        "--title",
    }
)
_CREATE_BOOLEAN_SHORT_FLAGS = frozenset("defw")
_CREATE_SHORT_OPTIONS_WITH_VALUE = frozenset("aBbFHlmprTt")
_SHELL_COMMAND_PREFIXES = frozenset(
    {"!", "{", "elif", "else", "exec", "if", "then", "until", "while", "do"}
)
_SHELL_INTERPRETERS = frozenset({"bash", "dash", "ksh", "sh", "zsh"})
_LEADING_REDIRECTION = re.compile(r"^\d*(?:<>|>>|>|<<|<)(.*)$")

# What a real invocation leaves in the response, established from `gh`'s source
# rather than assumed — the issue asked for that specifically, and the two
# subcommands genuinely differ:
#
#   `gh pr create` prints the PR URL to STDOUT. That is its primary output.
#   `gh pr ready`  prints NO url. It writes `Pull request owner/repo#N is marked
#                  as "ready for review"` to STDERR, and the already-ready case
#                  says `is already "ready for review"` — which still means a
#                  real PR exists and still deserves the reminder.
#
# The URL must be ALONE ON ITS LINE. `gh pr create` prints it and nothing else,
# so this still matches every real invocation — while a URL embedded in prose or
# JSON does not. Found live: replying to a review comment with `gh api` fired
# this hook, because the command text quoted the trigger phrase and the API's
# own response carried `…/pull/306#discussion_r…`. The bare-substring form could
# not tell that from a PR being opened.
_PR_URL = re.compile(
    r"^\s*https://(?P<host>[^/\s]+)/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/"
    r"(?P<number>\d+)/?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# `gh pr create` also prints an existing PR's URL on its own line when creation
# FAILS because that head/base pair already has a PR. A URL alone therefore is
# not success evidence when it belongs to this diagnostic. Acting on it is
# unsafe: a failed `--draft` retry against an existing ready PR would otherwise
# make the hook issue the mutating `--assert-draft` correction.
_EXISTING_PR_ERROR = re.compile(
    r"a pull request for branch .+ already exists:\s*\n\s*"
    r"https://\S+/pull/\d+/?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# The optional backslash tolerates a runtime that hands us already-escaped text.
# It is NOT load-bearing for anything this module does: nothing serialises the
# response any more, because doing so was what broke `_PR_URL`'s line anchor.
_READY_ACK = re.compile(
    r"Pull request (?P<owner>[^/\s#]+)/(?P<repo>[^/\s#]+)#(?P<number>\d+) "
    r'is (?:marked as|already) \\?"ready for review',
    re.IGNORECASE,
)

_SHELL_FUNCTION_SIGNATURE = re.compile(
    r"(?:\bfunction\s+(?P<keyword_name>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*\(\s*\))?|\b(?P<plain_name>[A-Za-z_][A-Za-z0-9_]*)"
    r"\s*\(\s*\))\s*\{"
)

# What the two registered runtimes actually send, established from their own
# sources by a review lens rather than assumed — an earlier version of this
# comment claimed stderr capture was "runtime-dependent", and that is not what
# either of them does:
#
#   Claude Code — an object with `stdout`, `stderr`, `interrupted`, `isImage`.
#   Codex       — a plain JSON string built from `aggregated_output`, which
#                 already concatenates stdout and stderr.
#
# Both are handled, and so is anything else, because `_iter_strings` below walks
# for strings instead of naming keys. An EMPTY response still counts as
# unreadable and fires: neither runtime promises a shape in its schema (Codex's
# types `tool_response` as `true`), and a missed reminder is the costly failure.

_DEFAULT_FALLBACK_COMMAND = "/code-review"
# Which runtime's `review.*` keys to read. Both registrations pass it explicitly;
# the default keeps a pre-#301 `.claude/settings.json` that passes no argument
# working after an engine refresh, rather than silently emitting no reminder.
_DEFAULT_RUNTIME = "claude"
_KNOWN_RUNTIMES = ("claude", "codex")
_DEFAULT_ENGINES_DIR = "scripts"
_DEFAULT_PANEL_RECEIPT_SOURCE = "fallback:panel"


def _lens_compute_phrase(config, kitconfig, runtime: str = _DEFAULT_RUNTIME) -> str:
    """Render ``review.fallback_panel.lens_compute.<runtime>`` as an instruction clause.

    Returns ``""`` when unset or unusable, which means "lenses inherit the
    cockpit's own compute" — the behaviour before this key existed, and the
    default for any adopter who never sets it.

    ``model`` and ``effort`` are independent and each optional, so a runtime that
    exposes only one control sets only that key. Keyed by runtime because a value
    written for one must never leak into the other's instruction — which is what
    happened before `#301`: this hook hardcoded `.claude` while its docstring said
    "this hook only ever runs under Claude Code", true when written and false the
    moment it was registered on Codex.

    An absent key for `runtime` yields `""` — lenses inherit the session's own
    compute. It never falls back to the other runtime's value.
    """
    compute = kitconfig.get(config, f"review.fallback_panel.lens_compute.{runtime}", None)
    if not isinstance(compute, dict):
        return ""
    parts = []
    for key in ("model", "effort"):
        value = compute.get(key)
        # Reject non-strings and blanks rather than rendering `model: None` into
        # an instruction the agent would then dutifully try to honour.
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        # Non-blank is NOT enough. kitconfig's YAML subset does not implement
        # block scalars, so `model: |` arrives as the literal string "|" rather
        # than raising — a non-blank string that would render `model |` into the
        # instruction. Requiring one alphanumeric character rejects that and any
        # other pure-punctuation token, while accepting every real model or
        # effort name (`sonnet`, `high`, `claude-opus-5`, `gpt-5`).
        if not cleaned or not any(ch.isalnum() for ch in cleaned):
            continue
        parts.append(f"{key} {cleaned}")
    if not parts:
        return ""
    return f" Run each lens at {' and '.join(parts)}, per review.fallback_panel.lens_compute."


def _load_review_config(runtime: str = _DEFAULT_RUNTIME) -> tuple[list[str], str, str, list[str], str, str]:
    """Read ``(review.bots, review.fallback_commands.<runtime>, paths.engines,
    review.fallback_panel lens names, review.fallback_panel.receipt_source,
    rendered review.fallback_panel.lens_compute.<runtime> clause)``.

    Best-effort: any failure (missing config, kitconfig unimportable, malformed
    values) falls back to generic defaults rather than raising — this hook must
    never fail a session over a config read.
    """
    try:
        here = Path(__file__).resolve()
        lib_dir = here.parent.parent / "lib"
        sys.path.insert(0, str(lib_dir))
        import kitconfig  # noqa: PLC0415

        config = kitconfig.load_config()
        bots = kitconfig.get_str_list(config, "review.bots", [])
        fallback = kitconfig.get(
            config, f"review.fallback_commands.{runtime}", _DEFAULT_FALLBACK_COMMAND
        )
        engines = kitconfig.get(config, "paths.engines", _DEFAULT_ENGINES_DIR)
        if not isinstance(fallback, str) or not fallback:
            fallback = _DEFAULT_FALLBACK_COMMAND
        if not isinstance(engines, str) or not engines:
            engines = _DEFAULT_ENGINES_DIR
        panel = kitconfig.get(config, "review.fallback_panel.lenses", [])
        lenses = (
            [
                lens["name"].strip()
                for lens in panel
                if isinstance(lens, dict)
                and isinstance(lens.get("name"), str)
                # A blank name would have the hook advertise a panel with an
                # unnameable lens — worse than advertising no panel at all.
                and lens["name"].strip()
            ]
            if isinstance(panel, list)
            else []
        )
        panel_source = kitconfig.get(
            config, "review.fallback_panel.receipt_source", _DEFAULT_PANEL_RECEIPT_SOURCE
        )
        if not isinstance(panel_source, str) or not panel_source.strip():
            panel_source = _DEFAULT_PANEL_RECEIPT_SOURCE
        try:
            lens_compute = _lens_compute_phrase(config, kitconfig, runtime)
        except Exception:
            # Scoped deliberately. This is the least consequential of the six
            # fields, and sharing the outer `except` let a fault confined to it
            # collapse the whole tuple to defaults — which empties `lenses` and
            # so drops PANEL advertising entirely, for a reason that has nothing
            # to do with whether a panel is configured. Losing the compute clause
            # is the proportionate failure; losing the panel is not.
            lens_compute = ""
        return (
            bots,
            fallback,
            engines,
            lenses,
            panel_source.strip(),
            lens_compute,
        )
    except Exception:
        return (
            [],
            _DEFAULT_FALLBACK_COMMAND,
            _DEFAULT_ENGINES_DIR,
            # NO default lens roster, deliberately: this path means the config
            # could not be read, so nothing has confirmed a panel exists. A
            # non-empty default here would have the hook tell the operator to
            # claim panel coverage on the strength of a config it just failed to
            # load — and nothing downstream would catch that (issue #32).
            [],
            _DEFAULT_PANEL_RECEIPT_SOURCE,
            # Same reasoning: name no compute we could not read. Empty means
            # "inherit this session's", which is always a safe instruction.
            "",
        )


def _bot_description(bots: list[str]) -> str:
    if not bots:
        return "the configured review bot(s)"
    names = [b.strip() for b in bots if isinstance(b, str) and b.strip()]
    if not names:
        return "the configured review bot(s)"
    return " / ".join(names)


def _fallback_instruction(
    fallback_command: str,
    lenses: list[str],
    panel_source: str = _DEFAULT_PANEL_RECEIPT_SOURCE,
    engines_dir: str = _DEFAULT_ENGINES_DIR,
    lens_compute: str = "",
) -> str:
    """What to run when a bot is unavailable.

    Names the PANEL when one is configured, because a single command in this
    session's own context is the author reviewing their own diff — which
    `safety-critical-changes.md` rule 2 says is not a green light. This hook
    fires whenever a PR is opened or readied, so it is the most-read statement
    of the fallback policy in the kit; pointing it at the degraded mode taught
    the wrong habit every time.

    ``lens_compute`` is the pre-rendered clause from
    :func:`_lens_compute_phrase` (``""`` when unset). It is appended to the
    PANEL branch only: the degraded mode runs in this session's own context, so
    there is no delegated lens to give a model or an effort level to.
    """
    # Two DISTINCT lenses is the panel's floor (see fallback-review-panel.md).
    # A one-lens `fallback_panel` is not a panel, so advertising one would tell
    # the operator to claim coverage they cannot have. Nothing downstream will
    # stop them: the engine records `--lenses` without verifying it (issue #32),
    # so this wording is the only thing steering it.
    if len({lens.casefold() for lens in lenses}) >= 2:
        return (
            "If a review bot is unavailable, run the fallback review PANEL — one "
            f"isolated, fresh-context reviewer per lens ({', '.join(lenses)}), per "
            "docs/agentic-dev-kit/fallback-review-panel.md — and record it with "
            f"`uv run {engines_dir}/pr_watch.py <PR#> "
            f'--record-review "{panel_source}" --lenses <names> --head <polled-sha>`. '
            "Never treat the outage as a review waiver."
            # Appended only for the PANEL branch: the degraded one-lens fallback
            # runs in the cockpit's own context, so there is no separate lens to
            # give a model or an effort level to.
            + lens_compute
        )
    return (
        f"If a review bot is unavailable, run the configured fallback "
        f"(`{fallback_command}`) instead of treating the outage as a review waiver."
    )


def _heredoc_specs(line: str) -> list[tuple[str, bool]]:
    """Return here-document delimiters opened by one shell source line."""
    specs: list[tuple[str, bool]] = []
    index = 0
    quote: str | None = None
    while index < len(line):
        char = line[index]
        if quote is not None:
            if char == "\\" and quote == '"':
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if char == "#" and (index == 0 or line[index - 1].isspace()):
            break
        if not line.startswith("<<", index) or line.startswith("<<<", index):
            index += 1
            continue

        cursor = index + 2
        strip_tabs = cursor < len(line) and line[cursor] == "-"
        if strip_tabs:
            cursor += 1
        while cursor < len(line) and line[cursor] in " \t":
            cursor += 1
        delimiter_chars: list[str] = []
        delimiter_quote: str | None = None
        while cursor < len(line):
            char = line[cursor]
            if delimiter_quote is not None:
                if char == delimiter_quote:
                    delimiter_quote = None
                    cursor += 1
                    continue
                if (
                    char == "\\"
                    and delimiter_quote == '"'
                    and cursor + 1 < len(line)
                    and line[cursor + 1] in '$`"\\'
                ):
                    delimiter_chars.append(line[cursor + 1])
                    cursor += 2
                    continue
                delimiter_chars.append(char)
                cursor += 1
                continue
            if char in {"'", '"'}:
                delimiter_quote = char
                cursor += 1
                continue
            if char == "\\" and cursor + 1 < len(line):
                delimiter_chars.append(line[cursor + 1])
                cursor += 2
                continue
            if char in " \t\r\n;&|()<>":
                break
            delimiter_chars.append(char)
            cursor += 1
        if delimiter_quote is not None:
            return specs
        delimiter = "".join(delimiter_chars)
        index = cursor
        if delimiter:
            specs.append((delimiter, strip_tabs))
    return specs


def _without_heredoc_bodies(command: str) -> str:
    """Remove here-document data while preserving the executable opener lines."""
    pending: list[tuple[str, bool]] = []
    kept: list[str] = []
    for line in command.splitlines(keepends=True):
        if pending:
            delimiter, strip_tabs = pending[0]
            candidate = line.rstrip("\r\n")
            if strip_tabs:
                candidate = candidate.lstrip("\t")
            if candidate == delimiter:
                pending.pop(0)
            kept.append("\n" if line.endswith(("\n", "\r")) else "")
            continue
        kept.append(line)
        pending.extend(_heredoc_specs(line))
    return "".join(kept)


def _without_line_continuations(command: str) -> str:
    """Apply shell backslash-newline removal outside single quotes."""
    kept: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(command):
        char = command[index]
        if char == "'":
            if quote is None:
                quote = "'"
            elif quote == "'":
                quote = None
            kept.append(char)
            index += 1
            continue
        if char == '"' and quote != "'":
            quote = None if quote == '"' else '"'
            kept.append(char)
            index += 1
            continue
        if char == "\\" and quote != "'":
            if command.startswith("\\\r\n", index):
                index += 3
                continue
            if command.startswith("\\\n", index):
                index += 2
                continue
            kept.append(char)
            if index + 1 < len(command):
                kept.append(command[index + 1])
                index += 2
            else:
                index += 1
            continue
        kept.append(char)
        index += 1
    return "".join(kept)


def _starts_shell_comment(command: str, index: int) -> bool:
    """Whether ``#`` starts a shell comment rather than an ordinary word."""
    return index == 0 or command[index - 1].isspace() or command[index - 1] in ";&|()"


def _without_shell_comments(command: str) -> str:
    """Remove shell comments while preserving quoted text and line boundaries."""
    kept = list(command)
    quote: str | None = None
    index = 0
    while index < len(command):
        char = command[index]
        if quote is not None:
            if char == "\\" and quote != "'":
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if char == "#" and _starts_shell_comment(command, index):
            while index < len(command) and command[index] != "\n":
                kept[index] = " "
                index += 1
            continue
        index += 1
    return "".join(kept)


def _shell_syntax_mask(command: str) -> str:
    """Mask quoted/comment text while retaining shell grammar positions."""
    masked = list(command)
    quote: str | None = None
    index = 0
    while index < len(command):
        char = command[index]
        if quote is not None:
            if char == "\\" and quote != "'":
                masked[index] = " "
                if index + 1 < len(masked):
                    masked[index + 1] = " "
                index += 2
                continue
            masked[index] = "\n" if char == "\n" else " "
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            masked[index] = " "
            index += 1
            continue
        if char == "\\":
            masked[index] = " "
            if index + 1 < len(masked):
                masked[index + 1] = " "
            index += 2
            continue
        if char == "#" and _starts_shell_comment(command, index):
            while index < len(command) and command[index] != "\n":
                masked[index] = " "
                index += 1
            continue
        index += 1
    return "".join(masked)


def _without_function_definitions(command: str) -> tuple[str, dict[str, str]]:
    """Remove function declarations and retain their bodies for actual calls."""
    definitions: dict[str, str] = {}
    mutable = list(command)
    cursor = 0
    while True:
        mask = _shell_syntax_mask("".join(mutable))
        match = _SHELL_FUNCTION_SIGNATURE.search(mask, cursor)
        if match is None:
            break
        open_brace = match.end() - 1
        depth = 1
        close_brace = open_brace + 1
        while close_brace < len(mask) and depth:
            if mask[close_brace] == "{":
                depth += 1
            elif mask[close_brace] == "}":
                depth -= 1
            close_brace += 1
        if depth:
            # An incomplete definition is not safely executable evidence.
            for index in range(match.start(), len(mutable)):
                if mutable[index] != "\n":
                    mutable[index] = " "
            break
        name = match.group("keyword_name") or match.group("plain_name")
        definitions[name] = command[open_brace + 1 : close_brace - 1]
        for index in range(match.start(), close_brace):
            if mutable[index] != "\n":
                mutable[index] = " "
        cursor = close_brace
    return "".join(mutable), definitions


def _command_substitutions(command: str) -> tuple[str, list[str]]:
    """Extract executable backtick and ``$(...)`` regions from shell source."""
    substitutions: list[str] = []
    mutable = list(command)
    index = 0
    quote: str | None = None
    while index < len(command):
        char = command[index]
        if quote == "'":
            if char == "'":
                quote = None
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if char == '"':
            quote = None if quote == '"' else '"'
            index += 1
            continue
        if char == "'" and quote is None:
            quote = "'"
            index += 1
            continue
        if char == "`":
            end = index + 1
            while end < len(command):
                if command[end] == "\\":
                    end += 2
                    continue
                if command[end] == "`":
                    break
                end += 1
            if end >= len(command):
                break
            substitutions.append(command[index + 1 : end])
            mutable[index : end + 1] = "$" + " " * (end - index)
            index = end + 1
            continue
        if command.startswith("$(", index) and not command.startswith("$((", index):
            depth = 1
            end = index + 2
            quote: str | None = None
            while end < len(command) and depth:
                nested = command[end]
                if quote is not None:
                    if nested == "\\" and quote != "'":
                        end += 2
                        continue
                    if nested == quote:
                        quote = None
                    end += 1
                    continue
                if nested in {"'", '"', "`"}:
                    quote = nested
                elif nested == "\\":
                    end += 2
                    continue
                elif nested == "(":
                    depth += 1
                elif nested == ")":
                    depth -= 1
                end += 1
            if depth:
                break
            substitutions.append(command[index + 2 : end - 1])
            mutable[index:end] = "$" + " " * (end - index - 1)
            index = end
            continue
        index += 1
    return "".join(mutable), substitutions


def _shell_commands(command: object, _depth: int = 0) -> list[list[str]]:
    """Tokenize executed command starts while excluding inert shell source."""
    if not isinstance(command, str):
        return []
    if _depth > 4:
        return []
    command = _without_heredoc_bodies(command)
    command = _without_line_continuations(command)
    command = _without_shell_comments(command)
    command, definitions = _without_function_definitions(command)
    command, substitutions = _command_substitutions(command)
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
        # Newlines are control tokens, not generic whitespace. This prevents the
        # first word of a later command from becoming an argument to the earlier
        # one, while quoted newlines remain inside their quoted token.
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except (TypeError, ValueError):
        return []

    commands: list[list[str]] = [[]]
    for token in tokens:
        if token and set(token) <= _SHELL_CONTROL_CHARS:
            if commands[-1]:
                commands.append([])
            continue
        commands[-1].append(token)
    executed = [shell_command for shell_command in commands if shell_command]
    for substitution in substitutions:
        executed.extend(_shell_commands(substitution, _depth + 1))
    for shell_command in tuple(executed):
        executable_index = _shell_executable_index(shell_command)
        if executable_index is None:
            continue
        body = definitions.get(shell_command[executable_index])
        if body is not None:
            executed.extend(_shell_commands(body, _depth + 1))
    return executed


def _is_assignment(token: str) -> bool:
    name, separator, _value = token.partition("=")
    return bool(
        separator
        and name
        and (name[0].isalpha() or name[0] == "_")
        and all(char.isalnum() or char == "_" for char in name[1:])
    )


def _redirection_span(shell_command: list[str], index: int) -> int:
    """Tokens occupied by one leading shell redirection, or zero."""
    match = _LEADING_REDIRECTION.match(shell_command[index])
    if match is None:
        return 0
    if match.group(1):
        return 1
    return 2 if index + 1 < len(shell_command) else 1


def _shell_executable_index(shell_command: list[str]) -> int | None:
    """Locate the executable after supported shell prefixes and wrappers."""
    index = 0
    while index < len(shell_command):
        token = shell_command[index]
        if token in _SHELL_COMMAND_PREFIXES or _is_assignment(token):
            index += 1
            continue
        redirection_span = _redirection_span(shell_command, index)
        if redirection_span:
            index += redirection_span
            continue
        if token == "command":
            index += 1
            while index < len(shell_command):
                if shell_command[index] == "-p":
                    index += 1
                    continue
                if shell_command[index] in {"-v", "-V"}:
                    return None
                if shell_command[index] == "--":
                    index += 1
                break
            continue
        if token == "env":
            index += 1
            while index < len(shell_command):
                token = shell_command[index]
                if _is_assignment(token) or token in {"-i", "--ignore-environment"}:
                    index += 1
                    continue
                if token in {"-u", "--unset"} and index + 1 < len(shell_command):
                    index += 2
                    continue
                if token.startswith("--unset="):
                    index += 1
                    continue
                if token in {"-S", "--split-string"}:
                    if index + 1 >= len(shell_command):
                        return None
                    try:
                        split_tokens = shlex.split(shell_command[index + 1])
                    except ValueError:
                        return None
                    if not split_tokens:
                        return None
                    shell_command[index : index + 2] = split_tokens
                    continue
                if token.startswith("--split-string="):
                    try:
                        split_tokens = shlex.split(token.split("=", 1)[1])
                    except ValueError:
                        return None
                    if not split_tokens:
                        return None
                    shell_command[index : index + 1] = split_tokens
                    continue
                if token == "--":
                    index += 1
                break
            continue
        if Path(token).name == "nohup":
            index += 1
            if index < len(shell_command) and shell_command[index] == "--":
                index += 1
            continue
        if Path(token).name == "time":
            index += 1
            if index < len(shell_command) and shell_command[index] == "-p":
                index += 1
            continue
        break
    return index if index < len(shell_command) else None


def _gh_command_index(shell_command: list[str]) -> int | None:
    """Locate a direct ``gh`` command after supported shell wrappers."""
    index = _shell_executable_index(shell_command)

    if index is None or Path(shell_command[index]).name != "gh":
        return None
    return index


def _interpreter_script(shell_command: list[str]) -> str | None:
    """Return the source passed to a supported shell's ``-c`` option."""
    executable_index = _shell_executable_index(shell_command)
    if executable_index is None:
        return None
    if Path(shell_command[executable_index]).name not in _SHELL_INTERPRETERS:
        return None
    index = executable_index + 1
    while index < len(shell_command):
        token = shell_command[index]
        if token == "-c" or (
            token.startswith("-")
            and not token.startswith("--")
            and "c" in token[1:]
        ):
            return shell_command[index + 1] if index + 1 < len(shell_command) else None
        if token == "--" or not token.startswith("-"):
            return None
        index += 1
    return None


def _gh_invocations(
    command: object, _depth: int = 0
) -> list[tuple[str, list[str]]]:
    """Return supported ``gh pr create|ready`` invocations and their arguments."""
    if _depth > 4:
        return []
    invocations: list[tuple[str, list[str]]] = []
    for shell_command in _shell_commands(command):
        gh_index = _gh_command_index(shell_command)
        if gh_index is None:
            script = _interpreter_script(shell_command)
            if script is not None:
                invocations.extend(_gh_invocations(script, _depth + 1))
            continue
        index = _skip_gh_global_options(shell_command, gh_index + 1)
        if index is None or index >= len(shell_command) or shell_command[index] != "pr":
            continue
        index = _skip_gh_global_options(shell_command, index + 1)
        if index is None or index >= len(shell_command):
            continue
        action = shell_command[index]
        if action == "new":
            action = "create"
        if action in {"create", "ready"}:
            invocations.append((action, shell_command[index + 1 :]))
    return invocations


def _syntactic_lifecycle_actions(command: object) -> set[str]:
    """Find lifecycle action syntax even behind an unsupported shell wrapper."""
    actions: set[str] = set()
    for shell_command in _shell_commands(command):
        for gh_index, token in enumerate(shell_command):
            if Path(token).name != "gh":
                continue
            index = _skip_gh_global_options(shell_command, gh_index + 1)
            if index is None or index >= len(shell_command) or shell_command[index] != "pr":
                continue
            index = _skip_gh_global_options(shell_command, index + 1)
            if index is None or index >= len(shell_command):
                continue
            action = shell_command[index]
            if action == "new":
                action = "create"
            if action in {"create", "ready"}:
                actions.add(action)
    return actions


def _has_dynamic_shell_values(command: object) -> bool:
    """Whether executed shell tokens depend on expansion this parser cannot resolve."""
    if not isinstance(command, str):
        return False
    source = _without_shell_comments(
        _without_line_continuations(_without_heredoc_bodies(command))
    )
    quote: str | None = None
    index = 0
    while index < len(source):
        char = source[index]
        if quote == "'":
            if char == "'":
                quote = None
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if char == "'" and quote is None:
            quote = "'"
            index += 1
            continue
        if char == '"':
            quote = None if quote == '"' else '"'
            index += 1
            continue
        if char in {"$", "`"}:
            return True
        index += 1
    return False


def _skip_gh_global_options(tokens: list[str], index: int) -> int | None:
    """Consume inherited options before a Cobra subcommand, or reject no-op flags."""
    while index < len(tokens):
        token = tokens[index]
        if token in _GH_GLOBAL_OPTIONS_WITH_VALUE:
            if index + 1 >= len(tokens):
                return None
            index += 2
            continue
        if any(
            token.startswith(f"{option}=")
            for option in _GH_GLOBAL_OPTIONS_WITH_VALUE
            if option.startswith("--")
        ) or (token.startswith("-R") and token != "-R"):
            index += 1
            continue
        if token in _GH_GLOBAL_OPTIONS_WITHOUT_VALUE:
            # Help/version terminate execution instead of selecting the later
            # lifecycle subcommand, wherever Cobra accepts their placement.
            return None
        return index
    return index


def _create_is_draft(arguments: list[str]) -> bool | None:
    """Return draft intent, or ``None`` when shell expansion can change it."""
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--":
            return False
        if token in _CREATE_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=")
            for option in _CREATE_OPTIONS_WITH_VALUE
            if option.startswith("--")
        ):
            index += 1
            continue
        if token in {"--draft", "-d"}:
            return True
        if token.startswith("--draft=") or token.startswith("-d="):
            value = token.split("=", 1)[1].strip().casefold()
            return value not in {"false", "0", "no", "off"}
        if token.startswith("-") and not token.startswith("--"):
            # Cobra/pflag walks a short-option cluster left to right. A boolean
            # `d` is draft wherever it is reached, but a value-taking option
            # consumes the rest of the token: `-dFbody.md` is draft while `-Fd`
            # gives `d` to `--body-file` and is ready.
            for short_flag in token[1:]:
                if short_flag == "d":
                    return True
                if short_flag in _CREATE_SHORT_OPTIONS_WITH_VALUE:
                    break
                if short_flag not in _CREATE_BOOLEAN_SHORT_FLAGS:
                    break
        if "$" in token or "`" in token:
            return None
        index += 1
    return False


def _create_is_dry_run(arguments: list[str]) -> bool:
    """Whether ``create`` only reports what it would do instead of creating."""
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--":
            return False
        if token in _CREATE_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=")
            for option in _CREATE_OPTIONS_WITH_VALUE
            if option.startswith("--")
        ):
            index += 1
            continue
        if token == "--dry-run":
            return True
        if token.startswith("--dry-run="):
            value = token.split("=", 1)[1].strip().casefold()
            return value not in {"false", "0", "no", "off"}
        index += 1
    return False


def _create_opens_browser(arguments: list[str]) -> bool:
    """Whether ``create`` only hands authoring off to a web browser."""
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--":
            return False
        if token in _CREATE_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=")
            for option in _CREATE_OPTIONS_WITH_VALUE
            if option.startswith("--")
        ):
            index += 1
            continue
        if token in {"--web", "-w"}:
            return True
        if token.startswith("--web=") or token.startswith("-w="):
            value = token.split("=", 1)[1].strip().casefold()
            return value not in {"false", "0", "no", "off"}
        if token.startswith("-") and not token.startswith("--"):
            for short_flag in token[1:]:
                if short_flag == "w":
                    return True
                if short_flag in _CREATE_SHORT_OPTIONS_WITH_VALUE:
                    break
                if short_flag not in _CREATE_BOOLEAN_SHORT_FLAGS:
                    break
        index += 1
    return False


def _create_can_complete(arguments: list[str]) -> bool:
    """Whether this CLI invocation itself can establish PR creation."""
    return not _create_is_dry_run(arguments) and not _create_opens_browser(arguments)


def _ready_is_undo(arguments: list[str]) -> bool:
    """Whether ``ready`` intentionally converts the target back to draft."""
    for token in arguments:
        if token == "--":
            return False
        if token == "--undo":
            return True
        if token.startswith("--undo="):
            value = token.split("=", 1)[1].strip().casefold()
            return value not in {"false", "0", "no", "off"}
    return False


def _without_existing_pr_diagnostics(response: str) -> str:
    """Remove failed-create diagnostics while preserving separate success URLs."""
    return _EXISTING_PR_ERROR.sub("", response)


def _existing_pr_diagnostic_count(response: str) -> int:
    """Count failed-create diagnostics in aggregate tool output."""
    return sum(1 for _match in _EXISTING_PR_ERROR.finditer(response))


def _response_identities(pattern: re.Pattern[str], response: str) -> set[tuple[str, str, int]]:
    """Return case-insensitive repository/PR identities captured by ``pattern``."""
    return {
        (
            match.group("owner").casefold(),
            match.group("repo").casefold(),
            int(match.group("number")),
        )
        for match in pattern.finditer(response)
    }


def _pr_lifecycle(command: object, response: str | None = None) -> str:
    """Return the evidenced lifecycle, or ``unknown`` for mixed create intent.

    Command text proves creation intent, including ``-d`` and inherited global
    ``gh`` flags. It does *not* prove that a later ready command executed: an
    ``||`` branch, failed intervening validation, or heredoc body may contain the
    same words. Only GitHub CLI's ready acknowledgement paired with a parsed ready
    invocation settles that transition. A draft-only create therefore preserves
    the intentional draft, while mixed create intent requires a live-state read
    before either mutating assertion.
    """
    invocations = _gh_invocations(command)
    create_arguments = [
        arguments for action, arguments in invocations if action == "create"
    ]
    real_creates = [arguments for arguments in create_arguments if _create_can_complete(arguments)]
    dry_run_creates = [
        arguments for arguments in create_arguments if _create_is_dry_run(arguments)
    ]
    browser_creates = [
        arguments for arguments in create_arguments if _create_opens_browser(arguments)
    ]
    ready_arguments = [
        arguments for action, arguments in invocations if action == "ready"
    ]
    normal_ready = [
        arguments for arguments in ready_arguments if not _ready_is_undo(arguments)
    ]
    undo_ready = [
        arguments for arguments in ready_arguments if _ready_is_undo(arguments)
    ]
    create_states = {
        _create_is_draft(arguments)
        for arguments in real_creates
    }
    if response is None and (real_creates or normal_ready):
        # No success output or PR identity is available. Fail loud, but never
        # choose a mutating correction from command intent alone.
        return "unknown"
    if (dry_run_creates or browser_creates) and (real_creates or normal_ready):
        # Aggregate output cannot say whether evidence came from a non-creating
        # handoff or the real invocation. Inspect live state first.
        return "unknown"
    if response is not None and real_creates and _existing_pr_diagnostic_count(response):
        # Output from failed and successful/fallback commands is aggregated.
        # A remaining URL cannot safely be assigned to one create invocation.
        return "unknown"
    if undo_ready and (real_creates or normal_ready):
        # Distinct ready/draft transitions in one aggregate response are not
        # safe grounds for a mutating assertion.
        return "unknown"
    if len(create_states) > 1:
        return "unknown"
    if real_creates and normal_ready:
        if len(real_creates) != 1 or len(normal_ready) != 1:
            return "unknown"
        create_ids = _response_identities(
            _PR_URL, _without_existing_pr_diagnostics(response)
        )
        ready_ids = _response_identities(_READY_ACK, response)
        if len(create_ids) == 1 and create_ids == ready_ids:
            return "ready"
        return "unknown"
    if create_states == {True}:
        return "draft"
    if create_states == {False} or normal_ready:
        return "ready"
    return "unknown"


def _lifecycle_instruction(
    command: object, engines_dir: str, response: str | None = None
) -> str:
    lifecycle = _pr_lifecycle(command, response)
    if lifecycle == "draft":
        return (
            "A draft pull request was just opened under the bounded material "
            "unfinished-work exception. Immediately run "
            f"`uv run {engines_dir}/pr_watch.py <PR#> --assert-draft`. "
            "Do not start review polling or the watch-and-fix loop yet. Finish and "
            "push the material work, complete the PR body, run `gh pr ready <PR#>`, "
            f"then run `uv run {engines_dir}/pr_watch.py <PR#> --assert-ready`. "
            "Only after that ready assertion passes may the watch-and-fix loop start. "
        )
    if lifecycle == "unknown":
        return (
            "A pull-request command produced ambiguous lifecycle evidence. Do not "
            "change its draft state from command text alone. First resolve the exact "
            "pull-request identity from authoritative forge state; if none exists, "
            "stop without changing any pull request. Then inspect "
            "`gh pr view <PR#> --json isDraft`; run "
            f"`uv run {engines_dir}/pr_watch.py <PR#> --assert-draft` only when "
            "that field is true, otherwise run "
            f"`uv run {engines_dir}/pr_watch.py <PR#> --assert-ready`. Start the "
            "watch-and-fix loop only after the ready assertion passes. "
        )
    return (
        "A pull request was just opened ready for review or marked ready. Immediately "
        f"run `uv run {engines_dir}/pr_watch.py <PR#> --assert-ready` before review "
        "polling, then start the watch-and-fix loop. "
    )


def build_reminder(
    runtime: str = _DEFAULT_RUNTIME,
    command: object = None,
    response: str | None = None,
) -> str:
    (
        bots,
        fallback_command,
        engines_dir,
        lenses,
        panel_source,
        lens_compute,
    ) = _load_review_config(runtime)
    bot_desc = _bot_description(bots)
    return (
        _lifecycle_instruction(command, engines_dir, response)
        + "Per the kit's \"PR follow-through\" policy (PRINCIPLES.md #5/#8), "
        "this lifecycle is MANDATORY; complete it in the current run without being "
        "asked. When it reaches review polling, invoke `/pr-watch` (or poll "
        f"`uv run {engines_dir}/pr_watch.py <PR#> --json`) and do NOT yield this turn "
        f"until CI is fully green AND every {bot_desc} finding is fixed or "
        "replied-to with a reason. Fix real findings, reply-with-reason to nitpicks "
        "you disagree with, `--mark-seen` each handled round, and keep polling (CI "
        "can take 20-30 min). "
        + _fallback_instruction(
            fallback_command, lenses, panel_source, engines_dir, lens_compute
        )
        + " Only stop early if you hit something that genuinely needs an "
        "operator decision."
    )


def _runtime_from_argv(argv: list[str]) -> str:
    """`--runtime <name>` or `--runtime=<name>`; `_DEFAULT_RUNTIME` when absent.

    An unknown name falls back to the default rather than rendering
    `review.fallback_commands.<typo>` as a missing key and advertising the generic
    default command — a typo in a hook registration would otherwise degrade the
    reminder silently, which is the failure class this hook exists to remove.
    """
    for i, arg in enumerate(argv):
        value = None
        if arg == "--runtime" and i + 1 < len(argv):
            value = argv[i + 1]
        elif arg.startswith("--runtime="):
            value = arg.split("=", 1)[1]
        if value:
            return value if value in _KNOWN_RUNTIMES else _DEFAULT_RUNTIME
    return _DEFAULT_RUNTIME


class _Unreadable(Exception):
    """The payload could not be walked in full, so nothing about it is settled."""


_MAX_DEPTH = 6


def _iter_strings(value: object, depth: int = 0):
    """Every string anywhere in a response payload, whatever shape it arrived in.

    Deliberately shape-agnostic. An earlier version read six hardcoded keys and
    fell back to `json.dumps` for anything else — and `json.dumps` escapes real
    newlines, so the line-anchored URL match below could never fire on a
    serialised payload. A genuine `gh pr create` under an unrecognised shape went
    SILENT. Codex's PostToolUse schema types `tool_response` as `true` — any
    value, no promised structure — so guessing key names was never verifiable.

    Depth-bounded, and exceeding the bound RAISES rather than truncating. That
    distinction is the whole point: truncating returns a shorter string, which
    reads downstream as "readable, and the evidence is not in it" — silence.
    A second review round proved that regression on the `ready` path, with a
    payload carrying shallow noise beside an acknowledgement nested too deep:
    the noise kept the response non-empty, the ack was dropped, and the run went
    quiet where the code this replaced would have fired.

    Values only, not keys — no runtime shape puts content in a key, and walking
    keys would let an arbitrary label masquerade as tool output.
    """
    if depth > _MAX_DEPTH:
        raise _Unreadable
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item, depth + 1)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_strings(item, depth + 1)


def _response_text(data: dict) -> str | None:
    """Everything the tool reported, flattened — or None when the payload cannot
    settle whether a PR was opened.

    None means "cannot settle it", and every such case fires: no strings at all,
    and now also a payload too deep to walk. A runtime that does not capture
    stderr renders `gh pr ready` indistinguishable from a command that printed
    nothing, and a missed reminder costs the follow-through this hook exists to
    guarantee while a spurious one costs a paragraph.
    """
    try:
        captured = "\n".join(_iter_strings(data.get("tool_response")))
    except (_Unreadable, RecursionError):
        return None
    return captured.strip() or None


def should_fire(command: object, response: str | None) -> bool:
    """Whether this Bash call actually opened or readied a PR.

    The command alone was the old gate and it mandated a watch loop for PRs that
    did not exist. Now it only selects candidates; the response decides.
    """
    if not isinstance(command, str):
        return False
    invocations = _gh_invocations(command)
    parsed_actions = {action for action, _arguments in invocations}
    real_creates = [
        arguments
        for action, arguments in invocations
        if action == "create" and _create_can_complete(arguments)
    ]
    normal_ready = [
        arguments
        for action, arguments in invocations
        if action == "ready" and not _ready_is_undo(arguments)
    ]
    if not real_creates and not normal_ready:
        if response is None:
            return False
        unparsed_actions = _syntactic_lifecycle_actions(command) - parsed_actions
        if "create" in unparsed_actions:
            diagnostic_count = _existing_pr_diagnostic_count(response)
            if diagnostic_count == 0 and _PR_URL.search(response):
                return True
        if "ready" in unparsed_actions and _READY_ACK.search(response):
            return True
        if _has_dynamic_shell_values(command):
            return bool(_PR_URL.search(response) or _READY_ACK.search(response))
        return False
    if response is None:
        return True  # nothing readable — fail loud

    # Each action is matched against ITS OWN evidence. Accepting either signal
    # for either action let a command that merely mentions `gh pr ready` fire on
    # any PR URL in its output, and vice versa — CodeRabbit found that.
    #
    # ANY, not ALL: `gh pr create --draft && gh pr ready` is one command with
    # both actions, and its response may carry only the URL if the runtime drops
    # stderr. Requiring every action's evidence would go silent on a PR that was
    # genuinely just opened, which is the failure this hook exists to prevent.
    if real_creates:
        diagnostic_count = _existing_pr_diagnostic_count(response)
        if diagnostic_count >= len(real_creates):
            # A failed create followed by `gh pr view` (or any other URL-producing
            # command) must not borrow that later URL as creation evidence.
            return False
        if _PR_URL.search(_without_existing_pr_diagnostics(response)):
            return True
    return bool(normal_ready and _READY_ACK.search(response))


def main() -> int:
    runtime = _runtime_from_argv(sys.argv[1:])
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError, RecursionError):
        # RecursionError is raised by `json.load` itself on deeply nested input,
        # before any of this module's code runs — so `_iter_strings`'s own depth
        # bound cannot help. Without it here a 200k-deep payload exits 1, which
        # this module's docstring promises never happens. Pre-existing; found by
        # a review lens that ran the real script rather than reading it, after a
        # a comment added on this PR implied the case was already handled.
        return 0  # malformed payload — never block the session

    if os.environ.get("JOB_NAME"):
        return 0  # cron/CI context — don't nag

    if not isinstance(data, dict):
        return 0

    tool_input = data.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    response = _response_text(data)
    if should_fire(command, response):
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": build_reminder(runtime, command, response),
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
