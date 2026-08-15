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

Four properties, each earned by a real failure:

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
4. **One channel per kind of framing.** ``--carry-forward`` carries what prior rounds
   *covered*; ``--delta-draws`` carries the author's own classification of the change,
   which the doctrine hands to a **delta lens only**, precisely so it can be disputed.
   Sharing one flag between the two is how a full panel came to be handed its author's
   draws — the anchoring **No framing** exists to keep out of a full panel.

This assembles the prompt. It does not launch lenses, build worktrees, or read reports:
``--lenses`` staying self-reported is #32, and this is what a real check would build on.

Usage:
    uv run scripts/panel_prompt.py --lens adversarial --head <sha>
    uv run scripts/panel_prompt.py --lens correctness --head <sha> \\
        --scratch /tmp/panel --pr 218 --carry-forward "Rounds 1-3 found everything in
        the author's claims and nothing in the changed content. Invert that."

A delta pass — and only a delta pass — adds the author's stated draws for the lens
to dispute, as a continuation of either form above::

        --delta-draws "Prose class: record prose (a handoff block, nothing reads it).
        Safety-critical: not under safety-critical-changes.md."

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

    matches = list(_ITEM.finditer(section))
    names = [m.group(2) for m in matches]
    if not names:
        raise PromptError(
            f"{doctrine_path}: parsed 0 contract items from {CONTRACT_HEADING!r}. The "
            "list format changed; refusing to emit a prompt carrying no contract."
        )
    # The rendered "carries N items" line is only assurance if N describes a sound
    # list. A renumbering slip leaves the count intact while the doctrine reads
    # wrong, so the ordinals are checked rather than merely counted.
    ordinals = [int(m.group(1)) for m in matches]
    if ordinals != list(range(1, len(ordinals) + 1)):
        raise PromptError(
            f"{doctrine_path}: contract items are numbered {ordinals}, not 1..{len(ordinals)}. "
            "A renumbering slip leaves the item count unchanged, so the count alone would "
            "have reported false assurance. Refusing to emit."
        )
    return section, names


def resolve_base(root: Path, branch: str, remote: str = "origin") -> str:
    """Resolve the base from the REMOTE. Never an input, so it cannot be stale.

    ``git ls-remote`` takes a *pattern*, not a name. A ``base_branch`` carrying glob
    metacharacters — reachable from a mistyped ``--base-branch`` or a
    ``vcs.protected_branch`` written prose-style as ``release/*`` — matches several
    refs, and taking the first silently picks a base nobody chose. Requiring exactly
    one match is what keeps "resolved from the remote" worth saying.
    """
    out = _git(root, "ls-remote", remote, f"refs/heads/{branch}")
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        raise PromptError(
            f"{remote} has no refs/heads/{branch} — cannot establish base currency "
            "against the remote, and an ancestry check does not substitute (a stale "
            "base is still an ancestor)."
        )
    if len(lines) > 1:
        matched = ", ".join(sorted(ln.split()[-1] for ln in lines))
        raise PromptError(
            f"{branch!r} matched {len(lines)} refs on {remote} ({matched}). "
            "`git ls-remote` takes a pattern, so a base branch containing a glob "
            "resolves ambiguously and the first match would be chosen silently. "
            "Name one branch."
        )
    return lines[0].split()[0]


def resolve_branch(root: Path, override: str | None, head: str) -> str:
    """Name the branch under review, or refuse. Never guess it from the checkout.

    Two ways the checkout lies about this, and refusing only the first is not
    enough — an earlier version of this function did exactly that:

    - **Detached**: ``rev-parse --abbrev-ref HEAD`` returns the literal ``HEAD``,
      and rendering it produces ``**Branch:** HEAD`` at exit 0.
    - **On some other branch**: this repo's own ``dev_session.sh`` builds lanes with
      ``git worktree add -b``, so a review tree can sit on a throwaway lane branch.
      That renders a real-looking branch name that is not the branch under review —
      strictly worse than ``HEAD``, which at least reads as a placeholder. The
      doctrine's own **No writes in the tree you were given** names this pattern.

    The checkable property is the same in both cases: an auto-detected branch is
    only the branch under review if **its tip is the head being reviewed**. Anything
    else is a guess, so it asks for ``--branch`` instead of guessing.
    """
    if override is not None:
        # The escape hatch must not admit the value it exists to refuse. git forbids a
        # branch literally named HEAD, so nothing valid is rejected here — and without
        # this, `--branch HEAD` reproduces the exact lie the ambient path refuses.
        if override == "HEAD":
            raise PromptError(
                "--branch HEAD names a placeholder, not a branch, and reproduces exactly "
                "the render this function refuses on the ambient path. git does not allow "
                "a branch by that name; pass the real one."
            )
        return override
    name = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if name == "HEAD":
        raise PromptError(
            "this checkout is detached, so the branch under review cannot be observed "
            "— `git rev-parse --abbrev-ref HEAD` returns the literal 'HEAD'. Pass "
            "--branch explicitly. Emitting 'Branch: HEAD' would name a placeholder as "
            "if it were the branch."
        )
    tip = _git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    if tip != head:
        raise PromptError(
            f"this checkout is on branch {name!r}, whose tip is {tip[:12]}, but the head "
            f"under review is {head[:12]}. That branch is not the one under review — a "
            "worktree built with `git worktree add -b` sits on its own lane branch, and "
            "rendering it would name a real-looking branch that is the wrong one. Pass "
            "--branch explicitly."
        )
    return name


def _override(flag: str, value: str | None) -> str | None:
    """Validate one optional string override: passed-but-empty is an error.

    Every optional flag here goes through this, and that is the point. Three
    successive review rounds each found the same defect in a *different* flag,
    because each was fixed as an instance: ``if x:`` treats an empty string — which
    a shell interpolating an unset variable produces routinely — as "not passed",
    so the caller's intent is discarded silently. Fixing them one at a time is how
    the fourth one survives.
    """
    if value is None:
        return None
    if not value.strip():
        raise PromptError(
            f"{flag} was passed but empty. An empty override is not the same as an "
            "omitted one, and silently falling back would discard what you asked for."
        )
    return value.strip()


def _repo_slug(remote_url: str) -> str:
    """`git@host:a/b.git` and `https://host/a/b/c.git` -> `a/b`, `a/b/c`.

    Keeping every path segment matters for forges with nested namespaces (GitLab
    subgroups, Bitbucket projects): taking only the last two silently renders a
    wrong-but-plausible repo for them.
    """
    url = remote_url.strip().removesuffix(".git")
    # A local remote has no org/repo to render. Splitting a filesystem path yields
    # something that reads exactly like `org/repo` but is a mangled path — the
    # wrong-but-plausible shape this function exists to avoid. This kit's own tests
    # set a local-path origin, so it is not a hypothetical input.
    if url.startswith(("file://", "/", "./", "../")) or (
        "://" not in url and ":" not in url and "/" in url
    ):
        return remote_url
    if "://" in url:
        url = url.split("://", 1)[1]
        path = url.split("/", 1)[1] if "/" in url else url
    elif ":" in url:  # scp-like: git@host:path
        path = url.split(":", 1)[1]
    else:
        path = url
    slug = path.strip("/")
    # A URL with no path at all leaves the host in `path`; rendering that as the
    # repo is wrong-but-plausible, so fall back to the raw URL, which reads as odd.
    return slug if "/" in slug else remote_url


def _require_base_object(root: Path, base: str, base_branch: str, from_remote: bool) -> str:
    """Validate the base locally, distinguishing "not fetched" from "not a commit".

    ``resolve_base`` reads the sha from the remote with ``ls-remote``, which transfers
    no objects. A shallow or single-branch clone — ``git clone --depth 1``, and what
    ``actions/checkout`` does by default — then has the feature branch's history but
    not the base's, so validating it locally fails on a base that is *provably
    current*. The refusal was right to happen and its message was wrong: it read as
    staleness or corruption and named no remedy, so the engine rejected an entirely
    legitimate invocation with no way out.
    """
    try:
        return _git(root, "rev-parse", "--verify", f"{base}^{{commit}}")
    except PromptError:
        pass
    if _run_ok(root, "cat-file", "-e", base):
        raise PromptError(f"{base} exists but is not a commit")
    if from_remote:
        # Earned: the sha was read off the remote's ref tip moments ago.
        raise PromptError(
            f"the base {base} was resolved from the remote as the tip of {base_branch!r}, "
            "but its object is not in this clone. That is a shallow or single-branch "
            "checkout, not a stale or wrong base — the sha is current. Fetch it and "
            f"retry:\n    git fetch origin {base_branch}\n(or `git fetch --unshallow`). "
            "Refusing rather than diffing against a base this repo cannot read."
        )
    # NOT earned: nothing verified an author-supplied base, so asserting it is current
    # would tell someone who fat-fingered --base to run a fetch that cannot help. The
    # render already says an author-supplied base is unverified; the refusal must agree.
    raise PromptError(
        f"the base {base} was supplied via --base, and no object by that name is in "
        "this repo. It may be a typo, or it may be a real commit this clone has not "
        f"fetched — nothing here has verified which. If you meant the tip of "
        f"{base_branch!r}, omit --base and it will be resolved from the remote; if you "
        f"meant this sha, fetch it first."
    )


def _run_ok(root: Path, *args: str) -> bool:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    ).returncode == 0


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
    runtime: str = "claude",
    scratch: str | None = None,
    pr: int | None,
    carry_forward: str | None,
    verify_command: str | None,
    base_from_remote: bool,
    branch_from_checkout: bool = True,
    # Defaulted, and the direction is what earns the default: a caller that forgets
    # this parameter emits a FULL-panel prompt carrying no draws, which is the safe
    # render. No omission here can silently add author framing — passing the flag on
    # a full panel still can, which nothing here is able to detect (see the render).
    delta_draws: str | None = None,
) -> str:
    # An unconfigured runtime legitimately means "inherit the cockpit's compute"
    # (the doctrine says so), but a TYPO looks identical. Saying which runtime was
    # asked for makes the two distinguishable at the point a reader can act on it.
    parts = [f"{k} {v}" for k, v in sorted(compute.items()) if v] if compute else []
    compute_line = (
        f"\nRun at: {', '.join(parts)}.\n"
        if parts
        else f"\nNo compute configured for runtime {runtime!r}; inherit the cockpit's.\n"
    )

    tree = (
        f"- **A detached worktree at that sha has been built for you at:**\n  `{scratch}`\n"
        if scratch is not None
        else "- **No worktree was provided.** Obtain the revision into a copy you made; "
        "do not write into any tree you were handed.\n"
    )
    # #469: the doctrine's Scratch namespace item (quoted in full below) already told a
    # lens to reach its own mutation-test copy by a fresh path, never rm -rf — and every
    # round of #459's panel still had a lens hit the sandbox's rm -rf refusal first. The
    # wording was never wrong; the carrier was. A lens meets the refusal before it reaches
    # item 9 of a 13-item contract quoted at the end of this prompt, so the operative
    # sentence is repeated here too, right where a lens is already thinking about a copy
    # of its own. This is a restatement, not a duplicate rule: it says nothing the item
    # below does not, so nothing here can drift out of agreement with the doctrine's own
    # wording without both copies being read side by side and noticed — the same bet the
    # "do not write into any tree you were handed" line above already makes for item 7.
    tree += (
        "- **If you also make a scratch copy of your own** (for mutation testing, say),"
        " reach it by a **fresh path**, namespaced by lens and revision — never by"
        " removing and recreating one. A sandbox refusing `rm -rf` is refusing the wrong"
        " route, not blocking you: the fresh path was already correct. The **Scratch"
        " namespace** item in the contract below has the full reasoning.\n"
    )
    pr_line = "" if pr is None else f"- **PR:** #{pr}\n"
    # The scope sentence is the half that could not be enforced. Nothing can inspect
    # free prose and tell "rounds 1-3 covered the guards" from "I judge this record
    # prose": a classifier over an author's own wording fails open on exactly the
    # wording that matters, and shipping one would license the belief that the channel
    # is policed. So the boundary is stated to the party that CAN check it — telling
    # the lens what this section is for turns author framing arriving here from
    # invisible into a reportable finding, the only defence a free-text field admits.
    carry = (
        f"\n## What prior rounds have and have not covered\n\n{carry_forward.strip()}\n"
        "\nThis section carries only what prior rounds *covered*. It is not the author's\n"
        "view of what this change is for, what is risky, or how it should be classified.\n"
        "If it reads that way, report that as a finding — the contract's **No framing**\n"
        "forbids it, and it is not something this pass is entitled to hand you.\n"
        if carry_forward is not None and carry_forward.strip()
        else ""
    )
    # A delta pass is the doctrine's ONE sanctioned exception to **No framing**: the
    # delta lens is handed the author's stated draws — the prose class and the
    # safety-critical boundary — precisely in order to dispute them. It gets its own
    # flag rather than sharing `--carry-forward` because the two were confused in
    # practice: draws typed into `--carry-forward` reached FULL-panel prompts, which
    # the doctrine says carry none of this ("Full-panel lens prompts are untouched by
    # all of this").
    #
    # Restated here rather than quoted from the doctrine, unlike the contract section:
    # the delta-pass rules sit mid-paragraph under "Re-running, and when to stop" with
    # no heading to anchor a slice on, and a substring anchor is exactly the fragility
    # `_HEADING` refuses. The cost is a second copy that can drift, so the doctrine
    # names this flag beside the rule — the two are found together.
    draws = (
        "\n## The author's stated draws — dispute them\n\n"
        "This is a **delta pass** — asserted by whoever assembled this prompt, not\n"
        "observed here. What follows is the author's own classification of\n"
        "this change, handed to you because disputing it is your first duty here. It is\n"
        "the one anchoring this panel accepts on purpose, and it is confined to a delta\n"
        "pass: a full panel's prompt carries no draw at all.\n\n"
        f"{delta_draws.strip()}\n\n"
        "End your report with **one verdict line per draw**: name the draw, then\n"
        "`confirmed` or `disputed`, with your reason. Confirm a draw only if you checked\n"
        'it yourself — "confirmed" means every draw is confirmed. A dispute moves the\n'
        "round toward more review, never less, so raising one costs you nothing.\n"
        if delta_draws is not None and delta_draws.strip()
        else ""
    )
    # The base label must match the path actually taken. Saying "resolved from the
    # remote" over an author-supplied base would assert the one property this script
    # exists to guarantee, on the one path where it does not hold.
    # An overridden branch is asserted by the caller, not observed. Every neighbouring
    # fact in this prompt is git-verified, so saying nothing would render an assertion
    # with the same confidence as a measurement.
    branch_provenance = (
        ""
        if branch_from_checkout
        else " — **supplied via --branch, not verified against this checkout**"
    )
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
        if verify_command is not None and verify_command.strip()
        else ""
    )

    return f"""You are an independent review lens. You did NOT write this code.
{compute_line}
## Your lens focus

**{lens}** — {focus}

## What you are reviewing

- **Repo:** {repo_slug}
- **Branch:** {branch}{branch_provenance}
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
{carry}{draws}
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
    o_root = _override("--root", args.root)
    root = (Path(o_root) if o_root else REPO_ROOT).resolve()
    # One validator, every optional override. See _override for why this is not
    # done per-flag.
    o_branch = _override("--branch", args.branch)
    o_base = _override("--base", args.base)
    o_base_branch = _override("--base-branch", args.base_branch)
    o_scratch = _override("--scratch", args.scratch)
    o_carry = _override("--carry-forward", args.carry_forward)
    o_draws = _override("--delta-draws", args.delta_draws)
    o_verify = _override("--verify-command", args.verify_command)
    o_runtime = _override("--runtime", args.runtime) or "claude"
    # --head and --lens are required=True, so argparse guarantees presence but not
    # content; an empty value otherwise reaches git as a blank revision.
    _override("--head", args.head)
    _override("--lens", args.lens)
    config = load_config(root / "config" / "dev-model.yaml")

    lenses = get(config, "review.fallback_panel.lenses", [])
    roster = {entry["name"]: entry.get("focus", "") for entry in lenses if "name" in entry}
    if args.lens not in roster:
        raise PromptError(
            f"lens {args.lens!r} is not in review.fallback_panel.lenses "
            f"({', '.join(sorted(roster)) or 'roster is empty'}). The doctrine requires "
            "lenses be drawn from the configured roster, not minted for the occasion."
        )

    head = _require_commit(root, args.head)
    branch = resolve_branch(root, o_branch, head)
    base_branch = o_base_branch or get(config, "vcs.protected_branch", "main")
    # These two must agree, or the provenance label describes the wrong path.
    base_from_remote = o_base is None
    base = o_base if o_base is not None else resolve_base(root, base_branch)
    base = _require_base_object(root, base, base_branch, base_from_remote)

    diffstat = _git(root, "diff", "--shortstat", f"{base}...{head}")
    if not diffstat:
        raise PromptError(
            f"diff {base}...{head} is empty. A lens handed an empty diff reports a clean "
            "pass over nothing, which the doctrine names as the worst failure available "
            "to a review mechanism. Refusing to emit."
        )

    section, names = contract(root / DOCTRINE)

    slug = _repo_slug(_git(root, "config", "--get", "remote.origin.url"))

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
        compute=get(config, f"review.fallback_panel.lens_compute.{o_runtime}", {}) or {},
        runtime=o_runtime,
        scratch=o_scratch,
        pr=args.pr,
        carry_forward=o_carry,
        delta_draws=o_draws,
        verify_command=o_verify,
        base_from_remote=base_from_remote,
        branch_from_checkout=o_branch is None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble a fallback-review-panel launch prompt from the doctrine."
    )
    # NOT `type=Path`: argparse would coerce "" to PosixPath(".") — truthy — so the
    # `or REPO_ROOT` fallback silently never fires and the review retargets at cwd.
    # The string is validated first, then converted.
    parser.add_argument("--root", default=None, help="repo under review (default: this one)")
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
        help="what prior rounds COVERED — the round-to-round aim that has no other home. "
        "Never the author's draws or risk assessment: those go to --delta-draws, and a "
        "full panel's prompt carries neither",
    )
    parser.add_argument(
        "--delta-draws",
        default=None,
        help="DELTA PASS ONLY: the author's stated draws (prose class, safety-critical "
        "boundary) for the lens to dispute, ending its report with one verdict line per "
        "draw. Omit for a full panel — this is the doctrine's one exception to No framing",
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
