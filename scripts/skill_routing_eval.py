#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check that each model-invoked kit skill's description carries the words people use (#1221).

A runtime decides whether to run ``pr-watch`` or ``wrap-up`` by reading the skill's
description. ``runtime_smoke.py`` proves a runtime *discovers* the skills; nothing
checked that a natural request would *reach* one, or that two descriptions do not
compete for the same request. A description edit could silently stop a workflow from
running on both runtimes at once.

This is the deterministic tier: a lexical approximation of routing, cheap enough for
``make test``. For each runtime it reads the description of every model-invoked skill
(the workflows not in ``runtime_adapters.EXPLICIT_INVOCATION_ONLY``) from the
committed adapter, and scores each case prompt against them with TF-IDF cosine over
lightly stemmed words. It fails when:

- a **positive** prompt does not rank its skill within ``top_k``;
- a **negative** prompt with an ``owner`` ranks the skill at or above that owner, or a
  negative prompt with no owner (a request no kit skill should take) scores the skill
  at or above ``unrelated_max_score``;
- two descriptions in one runtime have a cosine at or above ``collision_threshold``;
- a model-invoked skill has no case entry, or a case names a skill that is not one.

It cannot judge meaning. A failure usually means *fix the description*, not the case:
the description is missing the vocabulary a request uses, or is so broad it outranks
the right skill. Whether a real client then invokes the skill is the behavioural
question this tier does not answer.

The case file is ``docs/agentic-dev-kit/skill-routing/cases.json``; its ``settings``
block declares ``top_k``, ``unrelated_max_score`` and ``collision_threshold``, so a
threshold moves with the cases it was calibrated on.

    uv run <engine-dir>/skill_routing_eval.py [--root <repo>] [--cases <file>] [--json]

Exit 0: every check passed. Exit 1: a check failed (each failure is printed).
Exit 2: a case file, adapter or description could not be read.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import runtime_adapters  # noqa: E402
from kitconfig import repo_root  # noqa: E402

DEFAULT_CASES = "docs/agentic-dev-kit/skill-routing/cases.json"
ADAPTER_PATHS = {
    "claude": ".claude/skills/{slug}/SKILL.md",
    "codex": ".agents/skills/{slug}/SKILL.md",
}
SETTINGS = ("top_k", "unrelated_max_score", "collision_threshold")

# Function words carry no routing signal; with only a handful of descriptions in the
# corpus, IDF alone would not push them down far enough.
STOPWORDS = frozenset(
    (
        "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can", "could",
        "do", "does", "for", "from", "had", "has", "have", "how", "i", "if", "in",
        "into", "is", "it", "its", "me", "my", "no", "not", "of", "on", "or", "our",
        "so", "than", "that", "the", "their", "them", "then", "there", "these", "they",
        "this", "those", "to", "up", "us", "was", "we", "were", "what", "when", "where",
        "which", "while", "who", "why", "will", "with", "would", "you", "your", "yours",
    )
)


class EvalError(Exception):
    """An input could not be read; exit 2."""


def model_invoked_slugs() -> tuple[str, ...]:
    return tuple(s for s in runtime_adapters.WORKFLOW_SLUGS if s not in runtime_adapters.EXPLICIT_INVOCATION_ONLY)


def stem(word: str) -> str:
    """Strip a few English suffixes so `watching`, `watched` and `watch` meet.

    Deliberately crude: it only has to make the same word in two forms match, and a
    stem that is not a real word is harmless because both sides go through it.
    """
    for suffix in ("ations", "ation", "ings", "ing", "ers", "ies", "ied", "ed", "er", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            if suffix in ("ies", "ied"):
                word += "y"
            break
    return word


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("-", " "))
    return [stem(w) for w in words if w not in STOPWORDS and len(w) > 1]


@dataclass
class Model:
    """TF-IDF vectors for one runtime's descriptions."""

    idf: dict[str, float]
    vectors: dict[str, dict[str, float]]

    @classmethod
    def build(cls, descriptions: dict[str, str]) -> Model:
        docs = {slug: Counter(tokens(text)) for slug, text in descriptions.items()}
        n = len(docs)
        df = Counter(term for counts in docs.values() for term in counts)
        idf = {term: math.log((1 + n) / (1 + count)) + 1 for term, count in df.items()}
        return cls(idf, {slug: cls._weigh(counts, idf) for slug, counts in docs.items()})

    @staticmethod
    def _weigh(counts: Counter, idf: dict[str, float]) -> dict[str, float]:
        vec = {term: (1 + math.log(c)) * idf[term] for term, c in counts.items() if term in idf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {term: v / norm for term, v in vec.items()}

    def query(self, text: str) -> dict[str, float]:
        return self._weigh(Counter(tokens(text)), self.idf)

    @staticmethod
    def cosine(a: dict[str, float], b: dict[str, float]) -> float:
        return sum(v * b.get(term, 0.0) for term, v in a.items())

    def rank(self, text: str) -> list[tuple[str, float]]:
        q = self.query(text)
        scores = [(slug, self.cosine(q, vec)) for slug, vec in self.vectors.items()]
        # Ties break by slug so the printed order is reproducible. Whether a positive
        # case passes does not read this order: evaluate() counts every other skill
        # scoring at or above the target, so a tie counts against it either way.
        return sorted(scores, key=lambda item: (-item[1], item[0]))


@dataclass
class Result:
    failures: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)


def _frontmatter_description(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvalError(f"cannot read adapter {path}: {exc}") from exc
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise EvalError(f"{path} has no front matter")
    for line in match.group(1).splitlines():
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = json.loads(value) if value[0] == '"' else value[1:-1]
            if value:
                return value
    raise EvalError(f"{path} has no description")


def read_descriptions(root: Path, runtime: str) -> dict[str, str]:
    return {
        slug: _frontmatter_description(root / ADAPTER_PATHS[runtime].format(slug=slug))
        for slug in model_invoked_slugs()
    }


def read_cases(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvalError(f"cannot read case file {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("settings"), dict) or not isinstance(data.get("skills"), dict):
        raise EvalError(f"{path} must hold a 'settings' mapping and a 'skills' mapping")
    for key in SETTINGS:
        value = data["settings"].get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise EvalError(f"{path}: settings.{key} must be a number")
    slugs = set(model_invoked_slugs())
    for slug, entry in data["skills"].items():
        if not isinstance(entry, dict):
            raise EvalError(f"{path}: skills.{slug} must be a mapping")
        for kind in ("positive", "negative"):
            cases = entry.get(kind, [])
            if not isinstance(cases, list):
                raise EvalError(f"{path}: skills.{slug}.{kind} must be a list")
            for i, case in enumerate(cases):
                where = f"{path}: skills.{slug}.{kind}[{i}]"
                if not isinstance(case, dict) or not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
                    raise EvalError(f"{where} needs a non-empty 'prompt'")
                owner = case.get("owner")
                if owner is not None and (kind != "negative" or owner not in slugs or owner == slug):
                    raise EvalError(f"{where} has owner {owner!r}; an owner is another model-invoked skill, on a negative case")
    return data


def evaluate(root: Path, cases: dict) -> Result:
    settings = cases["settings"]
    top_k = int(settings["top_k"])
    unrelated_max = float(settings["unrelated_max_score"])
    collision = float(settings["collision_threshold"])
    slugs = model_invoked_slugs()
    result = Result()

    for slug in sorted(set(slugs) - set(cases["skills"])):
        result.failures.append(f"{slug}: no cases; every model-invoked skill needs positive and negative prompts")
    for slug in sorted(set(slugs) & set(cases["skills"])):
        entry = cases["skills"][slug]
        negatives = entry.get("negative", [])
        if not entry.get("positive"):
            result.failures.append(f"{slug}: no positive prompts")
        if not any("owner" in case for case in negatives):
            result.failures.append(f"{slug}: no negative prompt owned by another skill")
        if not any("owner" not in case for case in negatives):
            result.failures.append(f"{slug}: no negative prompt that no kit skill should take")
    for slug in sorted(set(cases["skills"]) - set(slugs)):
        result.failures.append(f"{slug}: has cases but is not a model-invoked skill")

    for runtime in ADAPTER_PATHS:
        model = Model.build(read_descriptions(root, runtime))
        names = sorted(model.vectors)
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                score = model.cosine(model.vectors[a], model.vectors[b])
                if score >= collision:
                    result.failures.append(
                        f"{runtime}: descriptions of {a} and {b} collide (cosine {score:.2f} >= {collision})"
                    )

        for slug in sorted(set(slugs) & set(cases["skills"])):
            entry = cases["skills"][slug]
            for case in entry.get("positive", []):
                ranking = model.rank(case["prompt"])
                target = dict(ranking)[slug]
                # Every other skill scoring at or above the target is ahead of it, so a
                # tie fails whichever slug sorts first; a prompt sharing no word with
                # the description (score 0) never passes.
                position = 1 + sum(1 for s, v in ranking if s != slug and v >= target)
                ok = position <= top_k and target > 0
                result.rows.append({"runtime": runtime, "skill": slug, "kind": "positive",
                                    "prompt": case["prompt"], "rank": position, "ok": ok})
                if not ok:
                    top = ", ".join(f"{s} {v:.2f}" for s, v in ranking[:3])
                    result.failures.append(
                        f"{runtime}: positive prompt for {slug} ranks it {position} (top_k {top_k}): "
                        f"{case['prompt']!r} -> {top}"
                    )
            for case in entry.get("negative", []):
                scores = dict(model.rank(case["prompt"]))
                owner = case.get("owner")
                if owner is not None:
                    ok = scores[owner] > scores[slug]
                    detail = f"{slug} {scores[slug]:.2f} vs owner {owner} {scores[owner]:.2f}"
                else:
                    ok = scores[slug] < unrelated_max
                    detail = f"{slug} {scores[slug]:.2f} >= unrelated_max_score {unrelated_max}"
                result.rows.append({"runtime": runtime, "skill": slug, "kind": "negative",
                                    "prompt": case["prompt"], "owner": owner, "ok": ok})
                if not ok:
                    result.failures.append(f"{runtime}: negative prompt for {slug} not rejected: {case['prompt']!r} ({detail})")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=None, help="repository whose adapters are scored (default: this one)")
    parser.add_argument("--cases", type=Path, default=None, help=f"case file (default: <root>/{DEFAULT_CASES})")
    parser.add_argument("--json", action="store_true", help="print every scored case as JSON")
    args = parser.parse_args(argv)
    root = (args.root or repo_root()).resolve()
    try:
        result = evaluate(root, read_cases(args.cases or root / DEFAULT_CASES))
    except EvalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"ok": not result.failures, "failures": result.failures, "cases": result.rows}, indent=2))
    else:
        passed = sum(row["ok"] for row in result.rows)
        for failure in result.failures:
            print(f"✗ {failure}")
        print(f"{passed}/{len(result.rows)} routing cases passed, {len(result.failures)} failure(s)")
    return 1 if result.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
