#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Retain session evidence and retire registered rounds through sweep_scratch.

The registry is shared Git metadata, outside disposable linked worktrees. Only
this engine's allocation operation adds root authority; importing an arbitrary
receipt is deliberately unsupported. Callers attest completion of all writers and
declare the evidence closure. OS probes supplement, rather than replace, those
attestations. This is not a security boundary against concurrent same-user writes.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import sweep_scratch as sweep

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import get, load_config, repo_root  # noqa: E402

SCHEMA = "devkit-cleanup-session/1"
LIMIT = 1024 * 1024
KINDS = {"report", "finding", "verification", "compute", "source", "asset", "receipt"}


def canonical(path: Path) -> Path:
    if (not path.is_absolute() or str(path) != os.path.realpath(path)
            or any(ord(c) < 32 or c == "\\" for c in str(path))):
        raise sweep.ConfigError(f"path must be absolute and have no symlink aliases: {path}")
    return path


def git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], env=env,
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise sweep.ConfigError(f"Git identity unavailable: {result.stderr.strip()}")
    return result.stdout.removesuffix("\n")


def read_bytes(path: Path, limit: int = LIMIT) -> bytes:
    canonical(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
            raise sweep.ConfigError(f"expected bounded, unaliased regular file: {path}")
        data = os.read(fd, limit + 1)
        if len(data) > limit:
            raise sweep.ConfigError(f"file grew beyond read limit: {path}")
        return data
    finally:
        os.close(fd)


def read_json(path: Path) -> dict:
    value = json.loads(read_bytes(path))
    if not isinstance(value, dict):
        raise sweep.ConfigError(f"expected JSON object: {path}")
    return value


def publish(path: Path, value: dict) -> None:
    canonical(path.parent)
    encoded = json.dumps(value, sort_keys=True, indent=2) + "\n"
    if len(encoded.encode()) > LIMIT:
        raise sweep.ConfigError("registry record exceeds its bounded read size")
    if os.path.lexists(path):
        read_bytes(path)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Registry:
    def __init__(self, repo: Path, config_path: Path):
        self.repo = canonical(repo)
        if Path(git(repo, "rev-parse", "--show-toplevel")) != repo:
            raise sweep.ConfigError("run from the exact repository root")
        self.common = canonical(Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")))
        self.config = load_config(config_path)
        name = get(self.config, "scratch.session_registry", None)
        if not isinstance(name, str) or re.fullmatch(r"[a-z][a-z0-9-]*", name) is None:
            raise sweep.ConfigError("configure scratch.session_registry as a simple directory name")
        self.directory = canonical(self.common / "devkit" / name)
        # Relative dependency repositories are anchored to the primary checkout,
        # not the task tree that may disappear. Separate Git directories are
        # allowed only when Git's worktree inventory supplies that primary path.
        listing = git(repo, "worktree", "list", "--porcelain", "-z")
        primary = listing.split("\0", 1)[0]
        if not primary.startswith("worktree "):
            raise sweep.ConfigError("primary worktree identity unavailable")
        self.primary = canonical(Path(primary.removeprefix("worktree ")))
        self.settings = sweep.load_settings(config_path, root=self.primary)
        self.policy = {"roots": self.settings.roots, "repos": [str(p) for p in self.settings.repos],
                       "grace_seconds": self.settings.grace_seconds,
                       "registry": name, "common": str(self.common)}

    @contextlib.contextmanager
    def lock(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        canonical(self.directory)
        fd = os.open(self.directory / "lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_nlink != 1:
                raise sweep.ConfigError("invalid registry lock")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    def location(self, token: str) -> Path:
        if re.fullmatch(r"[a-f0-9]{32}", token) is None:
            raise sweep.ConfigError("session must be the returned identifier")
        return canonical(self.directory / token)

    def load(self, token: str) -> dict:
        record = read_json(self.location(token) / "session.json")
        if (record.get("schema") != SCHEMA or record.get("id") != token
                or record.get("common_identity") != list(sweep._identity(str(self.common)))
                or record.get("policy") != self.policy):
            raise sweep.ConfigError("session repository identity or cleanup policy changed")
        if any(r["status"] == "removing" for r in record["rounds"]) and not record["approval"]:
            raise sweep.ConfigError("interrupted removal lacks its durable approval")
        return record

    def save(self, record: dict) -> None:
        publish(self.location(record["id"]) / "session.json", record)

    def start(self) -> dict:
        token = uuid.uuid4().hex
        self.location(token).mkdir(mode=0o700)
        record = {"schema": SCHEMA, "id": token, "policy": self.policy,
                  "common_identity": list(sweep._identity(str(self.common))),
                  "origin": str(self.repo), "head": git(self.repo, "rev-parse", "HEAD"),
                  "rounds": [], "worktrees": [], "pids": [], "seal": None,
                  "approval": None, "complete": False}
        self.save(record)
        return record

    def require_open(self, record: dict) -> None:
        if record["seal"] is not None or record["approval"] is not None:
            raise sweep.ConfigError("session inventory is sealed; start a new session for new work")

    def allocate(self, record: dict, root: str, head: str) -> dict:
        self.require_open(record)
        canonical(Path(root))
        receipt = sweep.create_review_round(root, head, self.settings, self.repo)
        record["rounds"].append({"receipt": receipt, "namespace": str(self.repo), "status": "allocated"})
        self.save(record)  # No reviewer starts until this durable publication returns.
        return receipt

    def track_worktree(self, record: dict, path: Path, runtime: str) -> None:
        self.require_open(record)
        canonical(path)
        if path == self.primary or path == self.common:
            raise sweep.ConfigError("the primary checkout cannot be retired")
        if git(path, "rev-parse", "--path-format=absolute", "--git-common-dir") != str(self.common):
            raise sweep.ConfigError("worktree belongs to a different repository")
        if str(path) not in sweep.registered_worktrees(self.settings.repos):
            raise sweep.ConfigError("worktree is not registered")
        if any(w["path"] == str(path) for w in record["worktrees"]):
            raise sweep.ConfigError("worktree already tracked")
        record["worktrees"].append({"path": str(path), "identity": list(sweep._identity(str(path))),
                                    "head": git(path, "rev-parse", "HEAD"), "runtime": runtime,
                                    "branch": git(path, "rev-parse", "--abbrev-ref", "HEAD")})
        self.save(record)

    def track_process(self, record: dict, pid: int) -> None:
        self.require_open(record)
        if pid <= 1:
            raise sweep.ConfigError("invalid process id")
        os.kill(pid, 0)
        if pid not in record["pids"]:
            record["pids"].append(pid)
        self.save(record)

    def seal(self, record: dict, manifest: dict) -> dict:
        self.require_open(record)
        if manifest.get("evidence_complete") is not True:
            raise sweep.ConfigError("manifest must attest the complete required evidence closure")
        items = manifest.get("retain")
        if not isinstance(items, list) or not items:
            raise sweep.ConfigError("retain must enumerate required evidence")
        sources = {item.get("source") for item in items if isinstance(item, dict)}
        if len(sources) != len(items):
            raise sweep.ConfigError("evidence sources must be unique")
        target = self.location(record["id"]) / "evidence"
        target.mkdir(mode=0o700, exist_ok=True)
        canonical(target)
        retained = []
        for item in items:
            if item.get("kind") not in KINDS or not isinstance(item.get("requires"), list):
                raise sweep.ConfigError("each evidence item needs a supported kind and requires list")
            if any(required not in sources for required in item["requires"]):
                raise sweep.ConfigError("required evidence dependency is missing from retain")
            source = canonical(Path(item["source"]))
            # Streaming preserves large authoritative assets without trusting
            # their filenames. Non-regular files, aliases and unreadable inputs
            # are refused; there is no generic recursive evidence copy.
            data_hash, size = copy_evidence(source, target)
            retained.append({**item, "sha256": data_hash, "size": size,
                             "retained": str(target / data_hash)})
        retired = manifest.get("retire", [])
        if not isinstance(retired, list):
            raise sweep.ConfigError("retire must enumerate diagnostics")
        for item in retired:
            if (not isinstance(item, dict) or not isinstance(item.get("reason"), str)
                    or not item["reason"].strip() or not item.get("replaced_by")
                    or any(p not in sources for p in item["replaced_by"])):
                raise sweep.ConfigError("retired diagnostics need a reason and retained replacements")
            path = canonical(Path(item["source"]))
            if str(path) in sources or not any(path.is_relative_to(r["receipt"]["path"]) for r in record["rounds"]):
                raise sweep.ConfigError("retired diagnostics must be unretained files in an owned round")
        record["seal"] = {"retained": retained, "retired": retired,
                          "evidence_complete": True}
        self.save(record)
        return record["seal"]

    def verify_evidence(self, record: dict) -> None:
        if record["seal"] is None:
            raise sweep.ConfigError("seal required evidence before cleanup")
        for item in record["seal"]["retained"]:
            path = canonical(Path(item["retained"]))
            if path != self.location(record["id"]) / "evidence" / item["sha256"]:
                raise sweep.ConfigError("retained evidence path escaped its session")
            if hash_file(path) != (item["sha256"], item["size"]):
                raise sweep.ConfigError(f"retained evidence changed: {path}")

    def preview(self, record: dict) -> dict:
        self.verify_evidence(record)
        outcomes = []
        paths = [r["receipt"]["path"] for r in record["rounds"]]
        paths += [w["path"] for w in record["worktrees"]]
        active = active_users(paths, record["pids"])
        for worktree in record["worktrees"]:
            path = Path(worktree["path"])
            reason = None
            action = "archive-with-runtime" if worktree["runtime"] == "codex" else "remove-worktree"
            if not os.path.lexists(path):
                action = "absent"
                if str(path) in sweep.registered_worktrees(self.settings.repos):
                    action, reason = "kept", "absent path still registered with Git"
            else:
                canonical(path)
                if list(sweep._identity(str(path))) != worktree["identity"]:
                    action, reason = "kept", "worktree identity changed"
                elif git(path, "rev-parse", "HEAD") != worktree["head"]:
                    action, reason = "kept", "worktree head changed; inventory is stale"
                elif git(path, "status", "--porcelain", "--untracked-files=all"):
                    action, reason = "kept", "worktree has uncommitted or untracked content"
                elif Path.cwd().resolve().is_relative_to(path):
                    action, reason = "kept", "invoke cleanup from outside the worktree"
            outcomes.append({"path": str(path), "action": action, "reason": reason})
        for entry in record["rounds"]:
            receipt = entry["receipt"]
            sweep._round_root(receipt["root"], self.settings, Path(entry["namespace"]))
            if list(sweep._identity(receipt["root"])) != receipt["root_identity"]:
                raise sweep.ConfigError("allocation root identity changed")
            if not os.path.lexists(receipt["path"]):
                # Absence is an idempotent result, not permission to delete a
                # replacement. If a path reappears its allocation identity must
                # still match before the existing sweeper may touch it.
                outcomes.append({"path": receipt["path"], "action": "absent", "reason": None})
                continue
            result = sweep.finish_review_round(receipt, self.settings, Path(entry["namespace"]),
                                               resuming=entry["status"] == "removing")
            outcomes.append({"path": result.path, "action": result.action, "reason": result.reason})
        for item in outcomes:
            item["owner"] = record["id"]
            item["bytes"] = None
            if item["action"] == "absent":
                item["bytes"] = 0
            elif item["action"] in {"eligible", "remove-worktree", "archive-with-runtime"}:
                measurement = sweep.scan(item["path"], os.lstat(item["path"]))
                if not measurement.problems:
                    item["bytes"] = measurement.size
        return {"session": record["id"], "paths": outcomes, "active_users": active,
                "evidence": record["seal"], "approval_token": digest({"policy": record["policy"],
                    "rounds": [{"receipt": r["receipt"], "namespace": r["namespace"]}
                               for r in record["rounds"]],
                    "worktrees": record["worktrees"], "pids": record["pids"], "seal": record["seal"]})}

    def apply(self, record: dict, approval: str, processes_finished: bool) -> dict:
        if not processes_finished:
            raise sweep.ConfigError("apply requires explicit completion of all writers and descendants")
        preview = self.preview(record)
        if approval != preview["approval_token"]:
            raise sweep.ConfigError("approval does not match this exact inventory and evidence seal")
        if record["approval"] not in (None, approval):
            raise sweep.ConfigError("session has a different persisted approval")
        record["approval"] = approval
        self.save(record)
        preview["processes_finished_attestation"] = True
        if preview["active_users"]:
            record["complete"] = False
            record["last_result"] = {**preview, "complete": False}
            self.save(record)
            return record["last_result"]
        for worktree, result in zip(record["worktrees"], preview["paths"], strict=False):
            if result["action"] == "remove-worktree":
                # Git refuses locked, dirty and nested-repository trees. Never
                # use --force or delete a worktree using the scratch primitive.
                try:
                    self.verify_evidence(record)
                    path = canonical(Path(worktree["path"]))
                    if (list(sweep._identity(str(path))) != worktree["identity"]
                            or git(path, "rev-parse", "HEAD") != worktree["head"]
                            or git(path, "status", "--porcelain", "--untracked-files=all")):
                        raise sweep.ConfigError("worktree changed after preview")
                    if active_users([worktree["path"]], record["pids"]):
                        raise sweep.ConfigError("worktree acquired an active user")
                    git(self.repo, "worktree", "remove", worktree["path"])
                except (OSError, sweep.ConfigError) as exc:
                    result.update(action="kept", reason=str(exc))
                else:
                    result.update(action="removed", reason=None)
        offset = len(record["worktrees"])
        for entry, result in zip(record["rounds"], preview["paths"][offset:], strict=True):
            if result["action"] not in {"eligible", "kept"}:
                continue
            try:
                self.verify_evidence(record)
                if active_users([entry["receipt"]["path"]], record["pids"]):
                    raise sweep.ConfigError("round acquired an active user")
                # Publish intent only after the sweeper's final guards. A
                # retry may lack the marker if interruption struck rmtree;
                # durable approval, root and directory identities remain bound.
                def journal_removal(current=entry):
                    current["status"] = "removing"
                    self.save(record)

                outcome = sweep.finish_review_round(entry["receipt"], self.settings,
                    Path(entry["namespace"]), apply=True, reviewers_finished=True,
                    resuming=entry["status"] == "removing", before_remove=journal_removal)
                result.update(action=outcome.action, reason=outcome.reason)
            except (OSError, sweep.ConfigError, sweep.Refused) as exc:
                result.update(action="kept", reason=str(exc))
            self.save(record)
        self.verify_evidence(record)
        for result in preview["paths"]:
            if result["action"] in {"removed", "absent"} and os.path.lexists(result["path"]):
                result.update(action="kept", reason="path exists after retirement; inspect before retrying")
        record["complete"] = all(p["action"] in {"removed", "absent"} for p in preview["paths"])
        record["last_result"] = {**preview, "complete": record["complete"]}
        self.save(record)
        return record["last_result"]


def hash_file(path: Path) -> tuple[str, int]:
    canonical(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise sweep.ConfigError(f"evidence must be an unaliased regular file: {path}")
        value, size = hashlib.sha256(), 0
        while chunk := os.read(fd, min(LIMIT, before.st_size + 1 - size)):
            value.update(chunk)
            size += len(chunk)
        after = os.fstat(fd)
        if size != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise sweep.ConfigError(f"evidence changed while being read: {path}")
        return value.hexdigest(), size
    finally:
        os.close(fd)


def copy_evidence(source: Path, target: Path) -> tuple[str, int]:
    expected, size = hash_file(source)
    destination = target / expected
    if destination.exists():
        if hash_file(destination) != (expected, size):
            raise sweep.ConfigError("existing retained evidence is corrupt")
        return expected, size
    fd, name = tempfile.mkstemp(prefix=".evidence-", dir=target)
    try:
        with os.fdopen(fd, "wb") as output:
            source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            try:
                if not stat.S_ISREG(os.fstat(source_fd).st_mode):
                    raise sweep.ConfigError("source changed its file type")
                remaining = size + 1
                while remaining and (chunk := os.read(source_fd, min(LIMIT, remaining))):
                    output.write(chunk)
                    remaining -= len(chunk)
                output.flush()
                os.fsync(output.fileno())
            finally:
                os.close(source_fd)
        if hash_file(Path(name)) != (expected, size):
            raise sweep.ConfigError("source changed during evidence retention")
        os.link(name, destination)  # no replacement publication
    finally:
        os.unlink(name)
    directory = os.open(target, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return expected, size


def active_users(paths: list[str], pids: list[int]) -> list[str]:
    """Bounded local observation; an unavailable/partial probe blocks cleanup.

    Registered PIDs remain blockers even after reuse. The explicit completion
    attestation covers escaped descendants and access outside the local user's
    visible process/file table. No process is killed by this workflow.
    """
    found = []
    for pid in pids:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError:
            found.append(f"process {pid} is inaccessible")
        else:
            found.append(f"process {pid} exists")
    existing = [p for p in paths if os.path.lexists(p)]
    if not existing:
        return found
    try:
        with tempfile.TemporaryFile() as output:
            result = subprocess.run(["lsof", "-n", "-P", "-Fpn"], stdout=output,
                                    stderr=subprocess.PIPE, timeout=30)
            output.seek(0)
            raw = output.read(64 * LIMIT + 1)
        if result.returncode or result.stderr or len(raw) > 64 * LIMIT:
            return found + ["open-file observation unavailable or incomplete"]
        pid = "unknown"
        for line in raw.decode(errors="strict").splitlines():
            if line.startswith("p"):
                pid = line[1:]
            elif line.startswith("n"):
                name = line[1:]
                if any(name == path or name.startswith(path + os.sep) for path in existing):
                    found.append(f"process {pid} uses {name}")
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        found.append(f"open-file observation unavailable: {exc}")
    return sorted(set(found))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("start")
    sub.add_parser("list")
    for action in ("allocate", "track-worktree", "track-process", "seal", "preview", "apply"):
        command = sub.add_parser(action)
        command.add_argument("session")
        if action == "allocate":
            command.add_argument("--root", required=True)
            command.add_argument("--head", required=True)
        elif action == "track-worktree":
            command.add_argument("path", type=Path)
            command.add_argument("--runtime", choices=("git", "codex"), required=True)
        elif action == "track-process":
            command.add_argument("--pid", type=int, required=True)
        elif action == "seal":
            command.add_argument("manifest", type=Path)
        elif action == "apply":
            command.add_argument("--approve", required=True)
            command.add_argument("--processes-finished", action="store_true")
    args = parser.parse_args(argv)
    try:
        repo = repo_root(Path.cwd())
        registry = Registry(repo, args.config or repo / "config/dev-model.yaml")
        if args.action == "list":
            result = [registry.load(p.parent.name) for p in sorted(registry.directory.glob("*/session.json"))]
        else:
            with registry.lock():
                record = registry.start() if args.action == "start" else registry.load(args.session)
                result = record
                if args.action == "allocate":
                    result = registry.allocate(record, args.root, args.head)
                elif args.action == "track-worktree":
                    registry.track_worktree(record, args.path, args.runtime)
                elif args.action == "track-process":
                    registry.track_process(record, args.pid)
                elif args.action == "seal":
                    result = registry.seal(record, read_json(args.manifest))
                elif args.action == "preview":
                    result = registry.preview(record)
                elif args.action == "apply":
                    result = registry.apply(record, args.approve, args.processes_finished)
        print(json.dumps(result, indent=2))
        return 1 if isinstance(result, dict) and args.action == "apply" and not result["complete"] else 0
    except (OSError, ValueError, KeyError, TypeError, sweep.ConfigError, sweep.Refused, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
