#!/usr/bin/env python3
"""PostToolUse hook: enforce PR state, then mandate the watch-fix loop.

Registered on BOTH runtimes, and told which one it is running under via
`--runtime claude|codex` (#301):

  - `.claude/settings.json` — `hooks.PostToolUse`, matcher `Bash`, plus an
    `if: "Bash(gh pr *)"` config-level pre-filter.
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

# The command is a NECESSARY condition, never a sufficient one (#302). It matches
# the phrase anywhere, so a command that merely quotes, echoes, greps for or
# documents it matches too — observed five times while wiring the Codex
# registration, once from the comment documenting this very behaviour and once
# from a review lens that had never heard of it. Anchoring to the start would
# miss the ordinary `cd x && <the command>` form.
#
# So the command decides whether to LOOK, and `tool_response` decides whether to
# fire. Both runtimes supply it on PostToolUse. The surface is wider under Codex,
# whose matcher filters the tool name only, so every Bash command reaches here.
_TRIGGER = re.compile(r"\bgh\s+pr\s+(create|ready)\b")
_SHELL_CONTROL_CHARS = frozenset(";&|()")

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
_PR_URL = re.compile(r"^\s*https://\S+/pull/\d+/?\s*$", re.MULTILINE)

# The optional backslash tolerates a runtime that hands us already-escaped text.
# It is NOT load-bearing for anything this module does: nothing serialises the
# response any more, because doing so was what broke `_PR_URL`'s line anchor.
_READY_ACK = re.compile(r'is (?:marked as|already) \\?"ready for review')

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


def _pr_lifecycle(command: object) -> str:
    """Return ``draft`` only for an actual draft create with no ready action.

    Tokenizing keeps a quoted PR body such as ``'run gh pr ready later'`` or
    ``'example: --draft'`` from changing the lifecycle. A compound command that
    creates draft and then marks ready has already completed the exception, so it
    takes the ready route.
    """
    if not isinstance(command, str):
        return "ready"
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except (TypeError, ValueError):
        return "ready"

    commands: list[list[str]] = [[]]
    for token in tokens:
        if token and set(token) <= _SHELL_CONTROL_CHARS:
            if commands[-1]:
                commands.append([])
            continue
        commands[-1].append(token)

    def invocation_index(shell_command: list[str], action: str) -> int | None:
        for candidate in (
            index
            for index in range(len(shell_command) - 2)
            if shell_command[index : index + 3] == ["gh", "pr", action]
        ):
            prefix = shell_command[:candidate]
            prefix_is_assignment = all(
                "=" in token and not token.startswith("=") for token in prefix
            )
            prefix_is_wrapper = prefix == ["command"] or (
                bool(prefix)
                and prefix[0] == "env"
                and all(
                    "=" in token and not token.startswith("=") for token in prefix[1:]
                )
            )
            if not prefix or prefix_is_assignment or prefix_is_wrapper:
                return candidate
        return None

    saw_ready = False
    saw_draft_create = False
    for shell_command in commands:
        if invocation_index(shell_command, "ready") is not None:
            saw_ready = True
            continue
        gh_index = invocation_index(shell_command, "create")
        if gh_index is None:
            continue
        for token in shell_command[gh_index + 3 :]:
            if token == "--draft":
                saw_draft_create = True
                break
            if token.startswith("--draft="):
                value = token.split("=", 1)[1].strip().casefold()
                if value not in {"false", "0", "no", "off"}:
                    saw_draft_create = True
                break
    return "draft" if saw_draft_create and not saw_ready else "ready"


def _lifecycle_instruction(command: object, engines_dir: str) -> str:
    if _pr_lifecycle(command) == "draft":
        return (
            "A draft pull request was just opened under the bounded material "
            "unfinished-work exception. Immediately run "
            f"`uv run {engines_dir}/pr_watch.py <PR#> --assert-draft`. "
            "Do not start review polling or the watch-and-fix loop yet. Finish and "
            "push the material work, complete the PR body, run `gh pr ready <PR#>`, "
            f"then run `uv run {engines_dir}/pr_watch.py <PR#> --assert-ready`. "
            "Only after that ready assertion passes may the watch-and-fix loop start. "
        )
    return (
        "A pull request was just opened ready for review or marked ready. Immediately "
        f"run `uv run {engines_dir}/pr_watch.py <PR#> --assert-ready` before review "
        "polling, then start the watch-and-fix loop. "
    )


def build_reminder(
    runtime: str = _DEFAULT_RUNTIME, command: object = None
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
        _lifecycle_instruction(command, engines_dir)
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
    actions = {match.group(1) for match in _TRIGGER.finditer(command)}
    if not actions:
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
    if "create" in actions and _PR_URL.search(response):
        return True
    return bool("ready" in actions and _READY_ACK.search(response))


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
    if should_fire(command, _response_text(data)):
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": build_reminder(runtime, command),
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
