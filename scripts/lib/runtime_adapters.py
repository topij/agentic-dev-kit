"""Render and classify the kit's adopter-owned runtime adapters.

Adapters do not belong in ``KIT_OWNED``: an adopter may legitimately keep a
same-named command or skill of its own.  Their *kit* form is nevertheless
derivable.  This module is the one renderer for that form and the comparison
used by ``kit_doctor --adapter-report``.

The comparison is intentionally informational.  A byte match means the file is
generated kit glue and may be refreshed; a mismatch means the adopter owns the
file and it must be reported and left alone.  It never turns an adapter into a
drift-gate failure.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

CURRENT_TEMPLATE_VERSION = 2

_DISPLAY_NAMES = {
    "adopt": "Adopt",
    "parallel": "Parallel Development",
    "post-merge-systemize": "Post-Merge Systemize",
    "pr-watch": "PR Watch",
    "session-start": "Session Start",
    "triage-friction-log": "Triage Friction Log",
    "upgrade": "Upgrade",
    "wrap-up": "Wrap Up",
}

_ARGUMENT_HINTS = {
    "parallel": "[list|plan|new|pr-watch|merge|rm|path] [args...]",
    "post-merge-systemize": "[backfill] [test]",
    "pr-watch": "[pr-number]",
    "triage-friction-log": "[resume|new|recover|test]",
}

_CURRENT_CONTEXTS = {
    "claude": {
        "adopt": """Treat `$ARGUMENTS` as additional adoption context (for example, a target repo path or
constraints on what may be installed). Resolve all configured paths from the repository
root and `config/dev-model.yaml`.""",
        "parallel": """Treat `$ARGUMENTS` as the requested parallel-development action and arguments.
Resolve the engine path from the repository root.""",
        "post-merge-systemize": """Treat `$ARGUMENTS` as entry-point keywords. Resolve configured paths from the repository
root and merged configuration defined by the shared workflow. This runtime's
repository-instruction layer is `CLAUDE.md` and `.claude/rules/`. Translate the
configured analysis tier only when the current launcher exposes that control; otherwise
treat it as guidance and do not claim that the model or effort changed.""",
        "pr-watch": """Treat `$ARGUMENTS` as the optional PR number or additional watch context. Resolve
the engine path from the repository root.

When the fallback review panel runs here, launch each lens as the agent named after
it (`.claude/agents/<lens>.md`, rendered from `review.fallback_panel.lens_compute.claude`
by `<engine-dir>/panel_prompt.py --lens <lens> --agent-definition`): its frontmatter is what
applies the configured `model` and `effort`, since the delegation tool itself has no
effort parameter. A definition added after this session started was not launchable in
the turn it was written and appeared in the roster later; count on it from the next
session.""",
        "session-start": """Treat `$ARGUMENTS` as additional session context. Resolve all configured paths from
the repository root and merged configuration defined by the shared workflow.""",
        "triage-friction-log": """Treat `$ARGUMENTS` as the entry point. Resolve configured paths from the repository root
and merged configuration defined by the shared workflow; translate only runtime-native
invocation and available mechanisms.""",
        "upgrade": """**Its Step 0 clones the kit. Re-read the workflow from that clone before Step 2, and
follow the clone's copy for the rest of the run.** The workflow's own early steps execute
from whatever copy is on disk here, and it is replaced only in Step 4 — so an installed
copy that is behind the kit drives the entire upgrade before anything refreshes it, and
the paragraph telling you to check for that is inside the copy you do not have yet. That
is why the instruction is here instead: this adapter is the one surface read before any
of it. A workflow doc is kit-owned, so a local edit to it is a kit bug to report rather
than a patch to carry forward.

Treat `$ARGUMENTS` as additional upgrade context. Resolve all configured paths from the
repository root and `config/dev-model.yaml`.""",
        "wrap-up": """Treat `$ARGUMENTS` as additional wrap-up context. Resolve all configured paths from
the repository root and merged configuration defined by the shared workflow.""",
    },
    "codex": {
        "adopt": """Treat the user's request as additional adoption context. Resolve configured paths from
the repository root and merged configuration when one exists; translate only
runtime-native invocation and available mechanisms.""",
        "parallel": """Treat the user's request as the parallel-development action and context. Resolve the
configured engine path from the repository root; translate only runtime-native lane,
isolation, and delegation mechanisms.""",
        "post-merge-systemize": """Treat the user's argument as entry-point keywords. Resolve configured paths from the
repository root and merged configuration defined by the shared workflow; translate only
runtime-native invocation and available mechanisms. This runtime's repository-instruction
layer is `AGENTS.md`. Translate the configured analysis tier only when the current
launcher exposes that control; otherwise treat it as guidance and do not claim that the
model or effort changed.""",
        "pr-watch": """Treat the user's request as the optional PR number or additional watch context. Resolve
the configured engine path from the repository root.

When the fallback panel runs, use one isolated fresh-context reviewer per configured
lens. Carry `review.fallback_panel.lens_compute.codex` on the `codex exec` argv as
`-c model_reasoning_effort=<effort>` and, when configured, `-m <model>`; read the
applied values back from the rollout. Translate only runtime-native reviewer isolation
and available mechanisms, and never treat an unavailable reviewer as a waiver.""",
        "session-start": """Treat the user's request as additional session context. Resolve all configured paths
from the repository root and merged configuration defined by the shared workflow;
translate only runtime-native invocation and available mechanisms.""",
        "triage-friction-log": """Treat the user's argument as the entry point. Resolve configured paths from the
repository root and merged configuration defined by the shared workflow; translate only
runtime-native invocation and available mechanisms.""",
        "upgrade": """The workflow's Step 0 clones the kit. Re-read the workflow from that clone before
Step 2, and follow the clone's copy for the rest of the run. Its early steps execute from
whatever copy is installed in the adopter and it is replaced only in Step 4, so this
bootstrap instruction must remain in the adapter that is read first. A local edit to the
shared workflow is a kit bug to report rather than a patch to carry forward.

Treat the user's request as additional upgrade context. Resolve configured paths from
the repository root and merged configuration; translate only runtime-native invocation
and available mechanisms.""",
        "wrap-up": """Treat the current conversation and repository diff as session context. Resolve all
configured paths from the repository root and merged configuration defined by the
shared workflow; translate only runtime-native invocation and available mechanisms.""",
    },
}

# The Codex bindings below were the shipped form immediately before the shared
# renderer.  Keep this one historical generation executable: an adopter that
# still has these exact generated bytes must be identified as a stale kit
# adapter and refreshed, not mistaken for adopter-authored policy.  Earlier
# thick forks are deliberately not listed; their authored behavior is exactly
# what the comparison must preserve.
_LEGACY_CODEX_BODIES = {
    "adopt": """# Adopt

1. Work from the repository root of the repo being adopted into.
2. Read `config/dev-model.yaml` if one exists, and resolve configured paths from it. Its
   absence is itself a signal the workflow handles — do not invent one.
3. Read `{workflow_path}` completely.
4. Follow that workflow. It is a judgment pass, not a copy: inspect what the repo already
   has, propose an install plan, and get the operator's confirmation before writing.
5. Never clobber an existing file. The workflow's final step hands the operator
   `./init.sh --no-clobber`; run nothing that renders over a file the operator has not
   agreed to lose.
6. Use the current runtime's review and commit mechanisms; require user authorization for
   external mutations not already requested.
""",
    "parallel": """# Parallel Development

1. Work from the repository root.
2. Read `config/dev-model.yaml` and `{workflow_path}` completely.
3. Follow the requested action. With no action, show the read-only lane board.
4. Resolve engine paths from the repository root; support both `scripts/dev_session.sh` and a namespaced adopted path such as `scripts/devkit/dev_session.sh`.
5. Use the current runtime's supported parallel-task mechanism. Do not assume peer messaging, model selection, background execution, or automatic terminal launch unless the runtime exposes it.
6. Preserve the cockpit/lane ownership boundary and require disjoint source-file footprints before launch.
7. For behavioral changes to lane safety, read and apply `docs/agentic-dev-kit/safety-critical-changes.md`.
""",
    "pr-watch": """# PR Watch

1. Work from the repository root.
2. Read `config/dev-model.yaml` and `{workflow_path}` completely.
3. Follow the workflow for the PR number in the user's request, or the current branch's PR when none is supplied.
4. Resolve the engine path from the repository root; support both `scripts/pr_watch.py` and a namespaced adopted path such as `scripts/devkit/pr_watch.py`.
5. When a bot is unavailable, run the `review.fallback_panel` pass — one isolated, fresh-context reviewer per lens, per `docs/agentic-dev-kit/fallback-review-panel.md`. Give each lens the compute in `review.fallback_panel.lens_compute.codex` on the `codex exec` argv — `-c model_reasoning_effort=<effort>` and, when set, `-m <model>`; either key may be absent, and an absent key means the lens inherits the user's Codex config. The `Run at:` line in the prompt enforces nothing; the argv does, and the rollout's `turn_context` reads it back. Fall back to `review.fallback_commands` only if the runtime cannot isolate a reviewer, and record that as one lens, never as the configured `review.fallback_panel.receipt_source`. Never treat an unavailable review bot as a review waiver.
6. For safety-critical changes, also read and apply `docs/agentic-dev-kit/safety-critical-changes.md` before recommending merge.
""",
    "upgrade": """# Upgrade

1. Work from the repository root of the repo being upgraded.
2. Read `config/dev-model.yaml` and resolve configured paths from it. If there is none,
   the workflow's Step 0 says to stop and adopt instead — follow that rather than guessing
   a config into existence.
3. Read `{workflow_path}` completely.
4. That workflow's Step 0 clones the kit. **Re-read the workflow from that clone before
   Step 2, and follow the clone's copy for the rest of the run.** Its early steps execute
   from whatever copy is on disk in this repo, and it is replaced only in Step 4 — so an
   installed copy that is behind the kit drives the entire upgrade before anything
   refreshes it, and the paragraph telling you to check for that is inside the copy you do
   not have yet. This adapter is the one surface read before any of it, which is why the
   instruction is here. A workflow doc is kit-owned, so a local edit to it is a kit bug to
   report rather than a patch to carry forward.
5. Follow that workflow in order. Steps 0 and 1 are read-only; everything from Step 2
   mutates the repo and must happen on a branch.
6. Do not batch-replace kit-owned files because most of them are `unchanged` — the
   `differs` entries are where the risk is, and each is a decision the workflow specifies.
7. Use the current runtime's review and commit mechanisms; require user authorization for
   external mutations not already requested.
""",
}


@dataclass(frozen=True)
class AdapterStatus:
    runtime: str
    slug: str
    path: str
    state: str
    detail: str


def _yaml_scalar(value: str) -> str:
    if not value or "\n" in value or re.search(r"(^[!&*{}\[\],#|>@`'\"]|:\s|\s#)", value):
        return json.dumps(value, ensure_ascii=False)
    return value


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("adapter has no YAML front matter")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("adapter front matter is not closed")
    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        key, separator, raw = line.partition(":")
        if not separator or not key or key in fields:
            raise ValueError(f"unsupported adapter front-matter line: {line!r}")
        value = raw.strip()
        if value.startswith('"'):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid quoted adapter metadata for {key}") from exc
            if not isinstance(parsed, str):
                raise ValueError(f"adapter metadata {key} is not a string")
            value = parsed
        fields[key] = value
    return fields


def render_adapter(
    runtime: str,
    slug: str,
    description: str,
    workflow_path: str,
    *,
    template_version: int = CURRENT_TEMPLATE_VERSION,
) -> str:
    """Render one complete adapter from its declared inputs."""

    if runtime not in _CURRENT_CONTEXTS:
        raise ValueError(f"unsupported runtime: {runtime}")
    if slug not in _CURRENT_CONTEXTS[runtime]:
        raise ValueError(f"unsupported workflow slug for {runtime}: {slug}")
    expected_path = f"docs/agentic-dev-kit/workflows/{slug}.md"
    if workflow_path != expected_path:
        raise ValueError(f"workflow path for {slug} must be {expected_path}")
    if not description.strip() or "\n" in description:
        raise ValueError("adapter description must be a non-empty single line")

    if runtime == "claude":
        frontmatter = ["---", f"description: {_yaml_scalar(description)}"]
        if slug in _ARGUMENT_HINTS:
            frontmatter.append(f"argument-hint: {json.dumps(_ARGUMENT_HINTS[slug])}")
    else:
        frontmatter = [
            "---",
            f"name: {slug}",
            f"description: {_yaml_scalar(description)}",
        ]
    frontmatter.extend(["---", ""])

    if template_version == 1 and runtime == "codex" and slug in _LEGACY_CODEX_BODIES:
        body = _LEGACY_CODEX_BODIES[slug].format(workflow_path=workflow_path)
    elif template_version == CURRENT_TEMPLATE_VERSION:
        heading = f"# {_DISPLAY_NAMES[slug]}\n\n" if runtime == "codex" else ""
        context = _CURRENT_CONTEXTS[runtime][slug]
        body = (
            f"{heading}Read `{workflow_path}` completely and follow it.\n\n"
            f"{context}\n"
        )
    elif template_version == 1:
        # Every unlisted binding kept the same rendered body across the template
        # transition, so the current renderer is also its historical renderer.
        heading = f"# {_DISPLAY_NAMES[slug]}\n\n" if runtime == "codex" else ""
        context = _CURRENT_CONTEXTS[runtime][slug]
        body = (
            f"{heading}Read `{workflow_path}` completely and follow it.\n\n"
            f"{context}\n"
        )
    else:
        raise ValueError(f"unsupported adapter template version: {template_version}")
    return "\n".join(frontmatter) + "\n" + body


def _adapter_path(runtime: str, slug: str) -> str:
    if runtime == "claude":
        return f".claude/commands/{slug}.md"
    return f".agents/skills/{slug}/SKILL.md"


def _unsafe_adopter_path(root: Path, rel: str) -> str | None:
    """Describe a path shape that an upgrade must preserve rather than write through."""

    current = root
    parts = Path(rel).parts
    for index, part in enumerate(parts):
        current /= part
        if current.is_symlink():
            return f"symlink at {Path(*parts[: index + 1])}; preserve and inspect manually"
        if not current.exists():
            continue
        if index < len(parts) - 1 and not current.is_dir():
            return f"non-directory ancestor at {Path(*parts[: index + 1])}; preserve manually"
        if index == len(parts) - 1:
            if not current.is_file():
                return "non-regular adapter path; preserve and inspect manually"
            try:
                if current.stat().st_nlink != 1:
                    return "multiply-linked adapter path; preserve and inspect manually"
            except OSError as exc:
                return f"cannot inspect adapter path: {exc}"
    return None


def compare_adapters(source_root: Path, adopter_root: Path) -> list[AdapterStatus]:
    """Compare an adopter against adapters rendered from a source kit checkout."""

    statuses: list[AdapterStatus] = []
    for runtime, contexts in _CURRENT_CONTEXTS.items():
        for slug in contexts:
            rel = _adapter_path(runtime, slug)
            source_path = source_root / rel
            try:
                source_text = source_path.read_text(encoding="utf-8")
                metadata = _frontmatter(source_text)
            except (OSError, UnicodeError, ValueError) as exc:
                raise ValueError(f"cannot read source adapter {rel}: {exc}") from exc
            description = metadata.get("description", "")
            if runtime == "codex" and metadata.get("name") != slug:
                raise ValueError(f"source adapter {rel} declares the wrong name")
            workflow_path = f"docs/agentic-dev-kit/workflows/{slug}.md"
            if not (source_root / workflow_path).is_file():
                raise ValueError(f"source adapter {rel} has no shared workflow {workflow_path}")
            current = render_adapter(runtime, slug, description, workflow_path)
            if source_text != current:
                raise ValueError(
                    f"source adapter {rel} does not equal the current rendered form"
                )

            adopter_path = adopter_root / rel
            unsafe_path = _unsafe_adopter_path(adopter_root, rel)
            if unsafe_path is not None:
                statuses.append(
                    AdapterStatus(runtime, slug, rel, "adopter-owned", unsafe_path)
                )
                continue
            if not adopter_path.is_file():
                statuses.append(
                    AdapterStatus(runtime, slug, rel, "missing", "install the rendered adapter")
                )
                continue
            try:
                adopter_text = adopter_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                statuses.append(
                    AdapterStatus(runtime, slug, rel, "adopter-owned", f"unreadable: {exc}")
                )
                continue
            if adopter_text == current:
                statuses.append(
                    AdapterStatus(runtime, slug, rel, "kit-current", "matches rendered form")
                )
                continue
            legacy = render_adapter(
                runtime,
                slug,
                description,
                workflow_path,
                template_version=1,
            )
            if legacy != current and adopter_text == legacy:
                statuses.append(
                    AdapterStatus(
                        runtime,
                        slug,
                        rel,
                        "kit-stale",
                        "matches an earlier rendered form; refresh freely",
                    )
                )
                continue
            statuses.append(
                AdapterStatus(
                    runtime,
                    slug,
                    rel,
                    "adopter-owned",
                    "does not match a rendered kit form; report and leave unchanged",
                )
            )
    return statuses


def render_adapter_report(statuses: list[AdapterStatus]) -> str:
    lines = [
        "runtime adapters — rendered comparison (informational; never a drift gate)",
        "",
    ]
    symbols = {
        "kit-current": "✓",
        "kit-stale": "↻",
        "adopter-owned": "!",
        "missing": "+",
    }
    for runtime in ("claude", "codex"):
        lines.append(f"  {runtime}:")
        for status in statuses:
            if status.runtime == runtime:
                lines.append(
                    f"    {symbols[status.state]} {status.path}: {status.state} — {status.detail}"
                )
    return "\n".join(lines)


def report_json(statuses: list[AdapterStatus]) -> list[dict[str, str]]:
    return [
        {
            "runtime": status.runtime,
            "slug": status.slug,
            "path": status.path,
            "state": status.state,
            "detail": status.detail,
        }
        for status in statuses
    ]
