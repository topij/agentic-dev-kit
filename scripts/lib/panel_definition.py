"""Pure renderer for the Claude fallback-panel agent definition.

Both ``panel_prompt.py`` and ``kit_doctor.py`` need the same expected bytes. Keeping
the renderer here lets the doctor compare an adopter-owned definition without
executing the adopter checkout's ``panel_prompt.py``: a diagnostic may inspect a
locally edited engine, but it must not run it merely to decide that it drifted.
"""

from __future__ import annotations

import json
import re

from kitconfig import get

AGENT_DEFINITION_RUNTIME = "claude"
LENS_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
CLAUDE_EFFORT_LEVELS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")


class LensDefinitionError(ValueError):
    """Configuration that cannot produce a faithful agent definition."""


def _compute_value(compute: dict, key: str, runtime: str) -> str | None:
    if key not in compute:
        return None
    value = compute.get(key)
    if not isinstance(value, str) or not value.strip() or not any(
        char.isalnum() for char in value
    ):
        raise LensDefinitionError(
            f"review.fallback_panel.lens_compute.{runtime}.{key} is {value!r}, which is "
            "not a usable value; omit the key to inherit, or set a real one"
        )
    return value.strip()


def render_agent_definition(config: dict, lens: str, runtime: str) -> str:
    """Render one configured Claude lens definition without reading or writing files."""
    if runtime != AGENT_DEFINITION_RUNTIME:
        raise LensDefinitionError(
            f"--agent-definition renders a {AGENT_DEFINITION_RUNTIME!r} agent definition; "
            f"runtime {runtime!r} carries lens compute on its launch argv, not in a "
            "definition file (see the doctrine's compute section)"
        )

    lenses = get(config, "review.fallback_panel.lenses", [])
    if not isinstance(lenses, list) or any(not isinstance(entry, dict) for entry in lenses):
        raise LensDefinitionError(
            "review.fallback_panel.lenses is not a list of maps, so no definition "
            "can be rendered"
        )
    roster = {
        entry["name"]: entry.get("focus", "")
        for entry in lenses
        if isinstance(entry.get("name"), str)
    }
    if lens not in roster:
        raise LensDefinitionError(
            f"lens {lens!r} is not in review.fallback_panel.lenses "
            f"({', '.join(sorted(roster)) or 'roster is empty'}). The doctrine requires "
            "lenses be drawn from the configured roster, not minted for the occasion."
        )
    if not LENS_NAME.match(lens):
        raise LensDefinitionError(
            f"lens name {lens!r} cannot be an agent definition: it becomes the file name, "
            "the frontmatter `name:`, and the subagent type, so it must match "
            f"{LENS_NAME.pattern}"
        )

    engines = get(config, "paths.engines", "scripts") or "scripts"
    compute = get(config, f"review.fallback_panel.lens_compute.{runtime}", {}) or {}
    if not isinstance(compute, dict):
        raise LensDefinitionError(
            f"review.fallback_panel.lens_compute.{runtime} is {compute!r}, not a map"
        )
    model = _compute_value(compute, "model", runtime)
    effort = _compute_value(compute, "effort", runtime)
    if effort is not None and effort not in CLAUDE_EFFORT_LEVELS:
        raise LensDefinitionError(
            f"review.fallback_panel.lens_compute.{runtime}.effort is {effort!r}; Claude Code "
            f"accepts {', '.join(CLAUDE_EFFORT_LEVELS)} and would run this lens at the "
            "cockpit's effort while logging the rejection only under --debug"
        )

    description = json.dumps(
        f"Fallback review panel lens {lens}: {roster[lens]}. Launch it only with a prompt "
        f"assembled by {engines}/panel_prompt.py; it is not a general-purpose agent.",
        ensure_ascii=False,
    )
    front = ["---", f"name: {lens}", f"description: {description}"]
    if model is not None:
        front.append(f"model: {json.dumps(model, ensure_ascii=False)}")
    if effort is not None:
        front.append(f"effort: {effort}")
    front.append("---")
    pinned = (
        "The frontmatter is what makes the configured compute mechanical: Claude Code\n"
        "applies its `model` and `effort` when the cockpit launches the agent named\n"
        f"`{lens}`. It lists this file at session start; a file written mid-session was\n"
        "not launchable in the turn it was written and appeared in the roster later, so\n"
        "count on it from the next session and treat an earlier listing as a bonus."
        if model is not None or effort is not None
        else "No `model` or `effort` is pinned here because\n"
        f"`review.fallback_panel.lens_compute.{runtime}` carries neither; the lens\n"
        "inherits the cockpit session's compute."
    )
    body = f"""
Generated from `config/dev-model.yaml` (`review.fallback_panel.lenses` and
`review.fallback_panel.lens_compute.{runtime}`) by
`{engines}/panel_prompt.py --lens {lens} --agent-definition`. Regenerate it after
changing either key; do not edit it by hand.

{pinned}

You are the **{lens}** lens of the fallback review panel
(`docs/agentic-dev-kit/fallback-review-panel.md`). You did NOT write the change under
review. Your launch prompt carries the contract, the revision, the diff, and your
focus; follow it exactly, and report what you reviewed before any finding.
"""
    return "\n".join(front) + "\n" + body
