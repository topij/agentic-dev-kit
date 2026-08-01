#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Assemble a fallback-review-panel launch prompt instead of hand-authoring it.

``docs/agentic-dev-kit/fallback-review-panel.md`` specifies what every lens must be
told: the numbered contract, the lens's ``focus`` from config, the repo/branch/sha
under review, and how the base was established. **Nothing rendered that.** Every
prompt was hand-written from the doctrine, once per lens per round, and #214 records
what it cost — an omitted contract item is invisible (a lens cannot report the absence
of an instruction it never received), and asserted-but-wrong provenance sends a lens
looking for things that are not there.

Three properties, each earned by a real failure:

1. **The contract is quoted, never restated.** This script parses it out of the
   doctrine at run time. A second copy would drift, which is the argument the doctrine
   already makes about lens briefs ("Restating the briefs here would give the kit two
   copies to drift apart") applied to itself. Change the doctrine, the prompt changes.
2. **The base cannot be stale, because it is not an input.** It is resolved from the
   *remote* every run. A stale base yields a large, non-empty, entirely plausible wrong
   diff that satisfies every other check the doctrine prescribes — so this refuses to
   emit rather than emit a prompt naming one.
3. **Same inputs, same prompt.** A round's framing differences are then deliberate
   additions passed via ``--carry-forward``, not variance in what the contract
   delivered. Measured on PR #218: what moved finding-yield across five rounds was
   what the prompt aimed lenses at, not how big the pass was — and that carry-forward
   had no home except an author remembering to type it.

This assembles the prompt. It does not launch lenses, build worktrees, or read reports:
``--lenses`` staying self-reported is #32, and this is what a real check would build on.

Usage:
    uv run scripts/panel_prompt.py --lens adversarial --head <sha>
    uv run scripts/panel_prompt.py --lens correctness --head <sha> \\
        --scratch /tmp/panel --pr 218 --carry-forward "Rounds 1-3 found everything in
        the author's claims and nothing in the changed content. Invert that."

Exits 2 on any condition that would produce a misleading prompt.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import get, load_config, repo_root  # noqa: E402

REPO_ROOT = repo_root(Path(__file__).resolve())
DOCTRINE = "docs/agentic-dev-kit/fallback-review-panel.md"
CONTRACT_HEADING = "## The contract every lens gets"

# A contract item opens as `N. **Name.**` at the top level of the list. Sub-bullets
# and continuation lines are indented, so anchoring to column 0 is what keeps the
# item count honest.
_ITEM = re.compile(r"^(\d+)\.\s+\*\*(.+?)\.?\*\*", re.MULTILINE)

# The heading must be a real level-two heading on its own line. A plain substring
# search also matches `### The contract every lens gets` (at offset 1) and any prose
# quoting the phrase mid-line — so it would happily slice a "contract" out of a
# subsection or a sentence and emit it as the contract.
_HEADING = re.compile(rf"^{re.escape(CONTRACT_HEADING)}\s*$", re.MULTILINE)
# Any level-two heading, to bound the section without matching `###` sub-headings.
_NEXT_H2 = re.compile(r"^## ", re.MULTILINE)


class PromptError(Exception):
    """A condition that would make the emitted prompt misleading."""


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise PromptError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def contract(doctrine_path: Path) -> tuple[str, list[str]]:
    """Return the contract section verbatim, plus the parsed item names.

    Verbatim is deliberate: rendering the section as-is means no sub-requirement can
    be dropped in transit. The parsed names are for the *cockpit* to eyeball against
    the doctrine — the count is the thing #214 says is currently invisible.
    """
    text = doctrine_path.read_text()
    opening = _HEADING.search(text)
    if opening is None:
        raise PromptError(
            f"{doctrine_path}: no {CONTRACT_HEADING!r} heading — the doctrine moved or "
            "was renamed, and this script must not guess at a substitute"
        )
    body_start = opening.end()
    following = _NEXT_H2.search(text, body_start)
    section = text[body_start : following.start() if following else len(text)].strip("\n")

    names = [m.group(2) for m in _ITEM.finditer(section)]
    if not names:
        raise PromptError(
            f"{doctrine_path}: parsed 0 contract items from {CONTRACT_HEADING!r}. The "
            "list format changed; refusing to emit a prompt carrying no contract."
        )
    return section, names


def resolve_base(root: Path, branch: str, remote: str = "origin") -> str:
    """Resolve the base from the REMOTE. Never an input, so it cannot be stale."""
    out = _git(root, "ls-remote", remote, f"refs/heads/{branch}")
    if not out:
        raise PromptError(
            f"{remote} has no refs/heads/{branch} — cannot establish base currency "
            "against the remote, and an ancestry check does not substitute (a stale "
            "base is still an ancestor)."
        )
    return out.split()[0]


def _require_commit(root: Path, rev: str) -> str:
    try:
        return _git(root, "rev-parse", "--verify", f"{rev}^{{commit}}")
    except PromptError as exc:
        raise PromptError(f"{rev} is not a commit in this repo: {exc}") from exc


def render(
    *,
    lens: str,
    focus: str,
    head: str,
    base: str,
    diffstat: str,
    contract_text: str,
    item_names: list[str],
    repo_slug: str,
    branch: str,
    compute: dict,
    scratch: str | None,
    pr: int | None,
    carry_forward: str | None,
    verify_command: str | None,
    base_from_remote: bool,
) -> str:
    compute_line = ""
    if compute:
        parts = [f"{k} {v}" for k, v in sorted(compute.items()) if v]
        if parts:
            compute_line = f"\nRun at: {', '.join(parts)}.\n"

    tree = (
        f"- **A detached worktree at that sha has been built for you at:**\n  `{scratch}`\n"
        if scratch
        else "- **No worktree was provided.** Obtain the revision into a copy you made; "
        "do not write into any tree you were handed.\n"
    )
    pr_line = f"- **PR:** #{pr}\n" if pr else ""
    carry = (
        f"\n## What prior rounds have and have not covered\n\n{carry_forward.strip()}\n"
        if carry_forward
        else ""
    )
    # The base label must match the path actually taken. Saying "resolved from the
    # remote" over an author-supplied base would assert the one property this script
    # exists to guarantee, on the one path where it does not hold.
    base_provenance = (
        "resolved from the remote at assembly time, not supplied by the author"
        if base_from_remote
        else "**supplied by the author via --base, NOT resolved from the remote.** "
        "Establish its currency yourself; a stale base yields a large, plausible, "
        "wrong diff"
    )
    # No config key holds the verification command, so it is passed in or omitted —
    # never guessed. A wrong one sends a lens down the exact "tests cannot run here"
    # path this kit's own CLAUDE.md exists to prevent.
    verify = (
        f"\n`{verify_command}` is this repo's verification command. A different probe "
        "failing is not\nevidence that tests cannot run here.\n"
        if verify_command
        else ""
    )

    return f"""You are an independent review lens. You did NOT write this code.
{compute_line}
## Your lens focus

**{lens}** — {focus}

## What you are reviewing

- **Repo:** {repo_slug}
- **Branch:** {branch}
{pr_line}- **Head sha under review:** `{head}`
- **Base:** `{base}` — {base_provenance}
{tree}
Diff against the named sha, not `HEAD`:

```sh
git diff {base}...{head}
git show {head}:<path>
```

Diffstat at assembly time: {diffstat}
{verify}
Name the command that established any claim you make.
{carry}
## The contract every lens gets

{contract_text}

---

The contract above is quoted verbatim from `{DOCTRINE}` and carries \
{len(item_names)} items: {", ".join(item_names)}.

If you cannot show a non-empty diff at the named sha, you have NOT reviewed anything —
say so rather than reporting a clean pass. Report findings ordered most-severe first.
If you find nothing, say precisely what you executed, so a zero-finding result is
readable as a result rather than as an unexecuted pass.
"""


def build(args: argparse.Namespace) -> str:
    # The repo under review is a parameter, not a module constant, so the engine can
    # be pointed at a checkout other than its own — and so its own tests can build a
    # fixture repo rather than depending on this one's history. `kit_doctor.py` takes
    # `--root` for the same reason. CI checks out shallow, which is what surfaced it:
    # a helper reading `git log` found one commit, and the engine correctly refused
    # the resulting empty diff.
    root = (args.root or REPO_ROOT).resolve()
    config = load_config(root / "config" / "dev-model.yaml")

    lenses = get(config, "review.fallback_panel.lenses", [])
    roster = {entry["name"]: entry.get("focus", "") for entry in lenses if "name" in entry}
    if args.lens not in roster:
        raise PromptError(
            f"lens {args.lens!r} is not in review.fallback_panel.lenses "
            f"({', '.join(sorted(roster)) or 'roster is empty'}). The doctrine requires "
            "lenses be drawn from the configured roster, not minted for the occasion."
        )

    branch = args.branch or _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    base_branch = args.base_branch or get(config, "vcs.protected_branch", "main")
    base_from_remote = args.base is None
    base = args.base or resolve_base(root, base_branch)
    head = _require_commit(root, args.head)
    base = _require_commit(root, base)

    diffstat = _git(root, "diff", "--shortstat", f"{base}...{head}")
    if not diffstat:
        raise PromptError(
            f"diff {base}...{head} is empty. A lens handed an empty diff reports a clean "
            "pass over nothing, which the doctrine names as the worst failure available "
            "to a review mechanism. Refusing to emit."
        )

    section, names = contract(root / DOCTRINE)

    remote_url = _git(root, "config", "--get", "remote.origin.url")
    slug = re.sub(r"^.*[:/]([^/]+/[^/]+?)(?:\.git)?$", r"\1", remote_url) or remote_url

    return render(
        lens=args.lens,
        focus=roster[args.lens],
        head=head,
        base=base,
        diffstat=diffstat,
        contract_text=section,
        item_names=names,
        repo_slug=slug,
        branch=branch,
        compute=get(config, f"review.fallback_panel.lens_compute.{args.runtime}", {}) or {},
        scratch=args.scratch,
        pr=args.pr,
        carry_forward=args.carry_forward,
        verify_command=args.verify_command,
        base_from_remote=base_from_remote,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble a fallback-review-panel launch prompt from the doctrine."
    )
    parser.add_argument("--root", type=Path, default=None, help="repo under review (default: this one)")
    parser.add_argument("--lens", required=True, help="lens name; must be in the configured roster")
    parser.add_argument("--head", required=True, help="head sha under review")
    parser.add_argument("--base", default=None, help="override the remote-resolved base (discouraged)")
    parser.add_argument("--base-branch", default=None, help="branch to resolve the base from")
    parser.add_argument("--branch", default=None, help="branch under review (default: current)")
    parser.add_argument("--scratch", default=None, help="worktree path to name in the prompt")
    parser.add_argument("--pr", type=int, default=None, help="PR number, for the lens's context")
    parser.add_argument("--runtime", default="claude", help="lens_compute.<runtime> key to render")
    parser.add_argument(
        "--carry-forward",
        default=None,
        help="what prior rounds covered — the round-to-round aim that has no other home",
    )
    parser.add_argument(
        "--verify-command",
        default=None,
        help="this repo's verification command (e.g. 'make test'); omitted if unset, never guessed",
    )
    args = parser.parse_args(argv)

    try:
        sys.stdout.write(build(args))
    except PromptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
