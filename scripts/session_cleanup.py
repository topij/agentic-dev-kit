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

Completed payloads are discarded by default: a seal may retain nothing, and each
retained item carries an exception (task, next action, deletion condition).
`retire-evidence` deletes retained bytes no unfinished task needs and leaves a
tombstone, so availability reads present, retiring, retired or missing.
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

SCHEMA = "devkit-cleanup-session/2"
# Schema 1 bound (st_dev, st_ino), which macOS renumbers across reboots (#1253).
# It still loads on that pair; a renumber's approved `reconcile` rebinds it to
# stable_identity and schema 2.
LEGACY_SCHEMA = "devkit-cleanup-session/1"
LIMIT = 1024 * 1024
KINDS = {"report", "finding", "verification", "compute", "source", "asset", "receipt"}
# A retained item is an exception to discard-by-default (#1256, #1315): it names
# the unfinished task that needs it, the next action, and when it may be deleted.
EXCEPTION_FIELDS = ("task", "next_action", "delete_when")


def canonical(path: Path) -> Path:
    if (not path.is_absolute() or str(path) != os.path.realpath(path)
            or any(ord(c) < 32 or c == "\\" for c in str(path))):
        raise sweep.ConfigError(f"path must be absolute and have no symlink aliases: {path}")
    return path


def git(repo: Path, *args: str, timeout: int = 30) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], env=env,
                            capture_output=True, text=True, timeout=timeout)
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
    try:
        value = json.loads(read_bytes(path))
    except RecursionError as exc:
        raise sweep.ConfigError(f"JSON nesting exceeds the reader's limit: {path}") from exc
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
        changed = self.differences(record, token)
        if changed:
            hint = ""
            if all(item.startswith("device ") for item in changed):
                hint = ("; only the device number differs, which a reboot or remount can renumber: "
                        f"preview `session_cleanup.py reconcile {token}`")
            raise sweep.ConfigError("session repository identity or cleanup policy changed: "
                                    + "; ".join(changed) + hint)
        self.check_journal(record)
        return record

    def differences(self, record: dict, token: str) -> list[str]:
        """Each bound field that no longer matches, with its stored and current value.

        A schema 1 record is compared in its own terms, (st_dev, st_ino), exactly
        as before #1253, and loads while that pair matches; it is never
        accepted on inode and path alone. Only a "device" difference is ever reported
        with the `device ` prefix reconcile accepts: a different volume UUID, or
        a change between the "volume" and "device" kinds, is another volume.
        """
        found = []
        legacy = record.get("schema") == LEGACY_SCHEMA
        if record.get("schema") not in (SCHEMA, LEGACY_SCHEMA):
            found.append(f"schema (stored {record.get('schema')!r}, current {SCHEMA!r})")
        if record.get("id") != token:
            found.append(f"id (stored {record.get('id')!r}, current {token!r})")
        stored = record.get("common_identity")
        current = list(sweep._identity(str(self.common))) if legacy else sweep.stable_identity(str(self.common))
        if not sweep.valid_identity(stored, legacy=legacy):
            found.append(f"common identity (stored {stored!r}, current {current})")
        elif not legacy and stored[0] != current[0]:
            found.append(f"identity kind (stored {stored[0]!r}, current {current[0]!r})")
        else:
            names = ("device", "inode") if legacy else (stored[0], "inode")
            found += [f"{name} (stored {old}, current {new})"
                      for name, old, new in zip(names, stored[-2:], current[-2:], strict=True)
                      if old != new]
        try:
            before = self.retirement_policy(record.get("policy", {}))
        except sweep.ConfigError:
            return [*found, "policy (stored value is not a mapping)"]
        after = self.retirement_policy(self.policy)
        for key in sorted(set(before) | set(after)):
            if key not in before or key not in after or before[key] != after[key]:
                show = [json.dumps(side[key]) if key in side else "absent" for side in (before, after)]
                found.append(f"policy {key} (stored {show[0]}, current {show[1]})")
        return found

    @staticmethod
    def check_journal(record: dict) -> None:
        if any(r["status"] == "removing" and not (r.get("approval") or record["approval"])
               for r in record["rounds"]):
            raise sweep.ConfigError("interrupted removal lacks its durable approval")

    def reconcile_plan(self, token: str) -> tuple[dict, dict]:
        """Preview rebinding an inventory whose only changed binding is its device number.

        macOS renumbers st_dev across reboots, so a record bound to the device
        number (schema 1, or a schema 2 record bound to the "device" kind) can
        never load again. Reconcile accepts that one difference and nothing
        else: schema, id, inode and policy (which carries the canonical common
        dir) must still match. It rebinds to ``stable_identity`` and schema 2,
        and retires no data. Every recorded round and worktree path must be
        absent and no worktree still registered with Git; a present one refuses,
        because its own recorded identity carries the old device too and
        nothing here can re-verify it. Only FileNotFoundError counts as absent:
        any other error inspecting a path refuses reconcile rather than reading
        as gone. An unmounted root also reads as absent; marking its round
        removed deletes nothing, and a returning directory is no longer managed
        here.
        """
        record = read_json(self.location(token) / "session.json")
        changed = self.differences(record, token)
        if not all(item.startswith("device ") for item in changed):
            raise sweep.ConfigError("reconcile rebinds only a changed device number; other bound "
                                    "fields differ: " + "; ".join(changed))
        # Only once every bound field but the device is trusted (#1263).
        self.check_journal(record)
        if not changed:
            raise sweep.ConfigError("inventory loads unchanged; there is nothing to reconcile")
        present = []
        for path in ([r["receipt"]["path"] for r in record["rounds"]]
                     + [w["path"] for w in record["worktrees"]]):
            try:
                os.lstat(canonical(Path(path)))
            except FileNotFoundError:
                continue
            present.append(path)
        registered = sweep.registered_worktrees(self.settings.repos)
        present += [w["path"] for w in record["worktrees"]
                    if w["path"] in registered and w["path"] not in present]
        if present:
            raise sweep.ConfigError("reconcile requires every recorded round and worktree to be absent "
                                    "and unregistered; still present: " + ", ".join(present))
        plan = {"session": token, "differences": changed,
                "schema": {"stored": record["schema"], "current": SCHEMA},
                "common_identity": {"stored": record["common_identity"],
                                    "current": sweep.stable_identity(str(self.common))},
                "rounds_marked_removed": [r["receipt"]["id"] for r in record["rounds"]
                                          if r["status"] != "removed"],
                # An unsealed round retained no evidence; the approver sees which.
                "rounds_without_seal": [r["receipt"]["id"] for r in record["rounds"]
                                        if r["status"] != "removed" and r.get("seal") is None
                                        and record["seal"] is None],
                "absent_worktrees": [w["path"] for w in record["worktrees"]]}
        plan["approval_token"] = digest({"record": record, "plan": plan})
        return record, plan

    def reconcile(self, token: str, approval: str) -> dict:
        record, plan = self.reconcile_plan(token)
        if approval != plan["approval_token"]:
            raise sweep.ConfigError("approval does not match this exact inventory and reconcile plan")
        for entry in record["rounds"]:
            if entry["status"] != "removed":
                entry["status"] = "removed"
                entry["reconciled"] = approval
        history = record.get("reconciled", [])
        if not isinstance(history, list):
            raise sweep.ConfigError("recorded reconcile history must be a list")
        record["reconciled"] = [*history, {"schema": plan["schema"],
                                           "common_identity": plan["common_identity"],
                                           "approval": approval}]
        record["schema"] = SCHEMA
        record["common_identity"] = plan["common_identity"]["current"]
        record["complete"] = True  # every recorded path was just verified absent
        self.save(record)
        self.load(token)
        return {**plan, "applied": True}

    @staticmethod
    def retirement_policy(policy: dict) -> dict:
        if not isinstance(policy, dict):
            raise sweep.ConfigError("session policy must be a mapping")
        # Only grace_seconds is irrelevant: registered retirement always uses
        # grace zero. Roots, dependency repositories, registry and common dir
        # still bind authority; unknown future keys also remain bound. Preserve
        # the original policy in the record/token for audit and retry stability.
        return {key: value for key, value in policy.items() if key != "grace_seconds"}

    @staticmethod
    def evidence_items(record: dict) -> list[tuple[dict | None, dict]]:
        """Every retained item with the round that sealed it (None: the inventory seal)."""
        found = [(None, item) for item in (record["seal"] or {}).get("retained", [])]
        for entry in record["rounds"]:
            found += [(entry, item) for item in (entry.get("seal") or {}).get("retained", [])]
        return found

    def evidence_summary(self, record: dict) -> dict:
        """Availability of retained evidence: present, retiring, retired or missing.

        `items` counts index entries; `bytes` counts each stored file once, since
        items with the same content share one file. Missing means absent without
        a tombstone, which nothing here authorized; it is never reported as
        retired. `exceptions` counts items that carry a retention exception.
        `held` is the present evidence of an inventory with a round marked
        `unverified`, with the marks' reasons. Some of it may also be kept for
        another reason; `reasons` stays until a verified removal clears a mark.
        """
        states: dict[str, dict] = {state: {"items": 0, "files": {}}
                                   for state in ("present", "retiring", "retired", "missing")}
        exceptions = 0
        for _, item in self.evidence_items(record):
            present = os.path.lexists(item["retained"])
            if item.get("retired") is not None:
                state = "retiring" if present else "retired"
            else:
                state = "present" if present else "missing"
            states[state]["items"] += 1
            states[state]["files"][item["sha256"]] = item["size"]
            exceptions += item.get("exception") is not None
        # A file still on disk is counted under present; a tombstone that
        # shares it is reported as retiring without counting its bytes twice.
        states["retiring"]["files"] = {k: v for k, v in states["retiring"]["files"].items()
                                       if k not in states["present"]["files"]}
        summary = {state: {"items": value["items"], "bytes": sum(value["files"].values())}
                   for state, value in states.items()}
        summary["exceptions"] = exceptions
        marks = self.unverified_marks(record)
        summary["held"] = {**(summary["present"] if marks else {"items": 0, "bytes": 0}),
                           "reasons": marks}
        return summary

    @staticmethod
    def unverified_marks(record: dict) -> list[str]:
        """Reasons of rounds recorded removed without a verified removal (#1278)."""
        return [f"{r['receipt']['id']}: {r['unverified']}" for r in record["rounds"] if r.get("unverified")]

    def retirement_plan(self, token: str, include: list[str]) -> tuple[dict, dict]:
        """Preview deleting retained evidence that no unfinished task needs (#1256, #1315).

        Default discard: an item without a retention exception is eligible once
        the round that sealed it is removed, or, for the inventory seal, once the
        inventory is complete. An item with an exception, and a `source` item
        sealed before exceptions existed (it may be the only copy of
        uncommitted work), stays kept unless its bytes are named by sha256 in
        `include`, the caller's assertion that the deletion condition of every
        item holding those bytes holds. While any round of the inventory is
        marked `unverified` (recorded removed while its data may still exist
        elsewhere), every item of the inventory, whichever seal holds it, is
        kept the same way. Bytes shared with a kept item, and an item a kept
        item requires, stay. Tombstones keep hash, size, kind,
        source and exception, so retired reads differently from missing.
        Evidence in other inventories is a separate copy and is untouched.
        """
        record = self.load(token)
        if any(r["status"] == "removing" for r in record["rounds"]):
            raise sweep.ConfigError("a round's retirement was interrupted; resume it before retiring evidence")
        evidence = self.location(token) / "evidence"
        unknown = set(include) - {item["sha256"] for _, item in self.evidence_items(record)}
        if unknown:
            raise sweep.ConfigError("--include names no retained item: " + ", ".join(sorted(unknown)))
        retire, kept, missing = [], [], []
        # Inventory-wide, because an item's source need not lie under the round
        # it came from, and the inventory seal holds items from every round.
        marks = self.unverified_marks(record)
        held = (f"a round of this inventory was recorded removed without a verified removal "
                f"({'; '.join(marks)}); name its bytes with --include once that round's data is "
                "confirmed gone") if marks else None
        for owner, item in self.evidence_items(record):
            view = {k: item.get(k) for k in ("sha256", "size", "kind", "source", "requires",
                                             "retained", "exception")}
            view["sealed_by"] = "inventory" if owner is None else owner["receipt"]["id"]
            path = canonical(Path(item["retained"]))
            if path != evidence / item["sha256"]:
                raise sweep.ConfigError("retained evidence path escaped its session")
            present = os.path.lexists(path)
            if item.get("retired") is not None and not present:
                continue
            reason = None
            if not present:
                missing.append(view)
                continue
            info = os.lstat(path)
            if not stat.S_ISREG(info.st_mode) or info.st_size != item["size"]:
                reason = "retained file size or type changed; inspect before retiring"
            elif item.get("retired") is not None:
                # An approved retirement was interrupted after its tombstone.
                # Only retire_evidence writes `retired`; a seal stores no such
                # key from a manifest.
                pass
            elif owner is None and not record["complete"]:
                reason = "inventory is not complete; retire its paths first"
            elif owner is not None and (owner["status"] != "removed"
                                        or os.path.lexists(owner["receipt"]["path"])):
                reason = "its round is not retired"
            elif held and item["sha256"] not in include:
                reason = held
                if item.get("exception") is not None:
                    reason += "; retention exception until: " + item["exception"]["delete_when"]
            elif item.get("exception") is not None and item["sha256"] not in include:
                reason = "retention exception until: " + item["exception"]["delete_when"]
            elif item.get("kind") == "source" and item["sha256"] not in include:
                reason = ("source evidence without a recorded exception may be the only copy of "
                          "uncommitted work; check it, then name it with --include")
            (kept if reason else retire).append({**view, "reason": reason} if reason else view)
        # One evidence directory serves the inventory seal and every round seal,
        # so the same bytes can back two items, and a kept item's `requires`
        # names items in its own seal. Keep both, until nothing more moves.
        moved = True
        while moved:
            moved = False
            needed = {v["sha256"] for v in kept}
            required = {(v["sealed_by"], r) for v in kept for r in v.get("requires") or []}
            for view in list(retire):
                if view["sha256"] in needed:
                    reason = "shares retained bytes with a kept item"
                elif (view["sealed_by"], view["source"]) in required:
                    reason = "required by a kept item"
                else:
                    continue
                retire.remove(view)
                kept.append({**view, "reason": reason})
                moved = True
        files = {v["sha256"]: v["size"] for v in retire}
        summary = self.evidence_summary(record)
        before = summary["present"]["bytes"] + summary["retiring"]["bytes"]
        plan = {"session": token, "retire": retire, "kept": kept, "missing": missing,
                "active_users": active_users([str(evidence / sha) for sha in files], record["pids"]),
                "evidence_summary": summary,
                "bytes": {"present_before": before, "removed": sum(files.values()),
                          "present_after": before - sum(files.values()),
                          "net_change": -sum(files.values())}}
        plan["approval_token"] = digest({"record": record, "plan": plan})
        return record, plan

    def retire_evidence(self, token: str, approval: str, include: list[str]) -> dict:
        record, plan = self.retirement_plan(token, include)
        if approval != plan["approval_token"]:
            raise sweep.ConfigError("approval does not match this exact inventory and retirement plan")
        if plan["active_users"]:
            raise sweep.ConfigError("retained evidence has an active user: " + "; ".join(plan["active_users"]))
        chosen = {(v["sealed_by"], v["sha256"], v["source"]) for v in plan["retire"]}
        for owner, item in self.evidence_items(record):
            key = ("inventory" if owner is None else owner["receipt"]["id"], item["sha256"], item["source"])
            if key in chosen:
                item["retired"] = {"approval": approval}
        if not plan["retire"]:
            return {**plan, "applied": True}  # nothing to delete: nothing written
        self.save(record)  # tombstones first: an interruption leaves "retiring", never "missing"
        evidence = self.location(token) / "evidence"
        for sha in sorted({v["sha256"] for v in plan["retire"]}):
            with contextlib.suppress(FileNotFoundError):
                os.unlink(evidence / sha)
        directory = os.open(evidence, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return {**plan, "applied": True, "evidence_summary": self.evidence_summary(self.load(token))}

    def inventories(self) -> list[dict]:
        result = []
        for path in sorted(self.directory.glob("*/session.json")):
            try:
                loaded = self.load(path.parent.name)
                result.append({**loaded, "evidence_summary": self.evidence_summary(loaded)})
            except (OSError, ValueError, KeyError, TypeError, sweep.ConfigError) as exc:
                result.append({"id": path.parent.name, "path": str(path),
                               "unavailable": str(exc)})
        return result

    def save(self, record: dict) -> None:
        publish(self.location(record["id"]) / "session.json", record)

    def start(self) -> dict:
        token = uuid.uuid4().hex
        self.location(token).mkdir(mode=0o700)
        record = {"schema": SCHEMA, "id": token, "policy": self.policy,
                  "common_identity": sweep.stable_identity(str(self.common)),
                  "origin": str(self.repo), "head": git(self.repo, "rev-parse", "HEAD"),
                  "rounds": [], "worktrees": [], "pids": [], "seal": None,
                  "approval": None, "complete": False}
        self.save(record)
        return record

    def require_open(self, record: dict) -> None:
        if record["seal"] is not None or record["approval"] is not None:
            raise sweep.ConfigError("session inventory is sealed; start a new session for new work")

    def allocate(self, record: dict, root: str, head: str, keep_previous: str | None = None) -> dict:
        self.require_open(record)
        canonical(Path(root))
        # A new round waits for every earlier one to be retired (`--round`), so
        # a long review loop does not hold each round's trees until the end.
        # Round statuses: "removed" is retired; "allocated" refuses unless the
        # caller records a keep reason, and a kept round still retires with the
        # inventory; "removing" is an interrupted retirement and always refuses,
        # because only resuming it is safe, and a keep reason does not exempt it.
        # An allocated round whose path is already gone still refuses: its
        # retirement records it removed cheaply.
        if any(r["status"] == "removing" for r in record["rounds"]):
            raise sweep.ConfigError("an earlier round's retirement was interrupted; resume it with "
                                    "preview/apply --round before allocating another")
        pending = [r for r in record["rounds"] if r["status"] != "removed" and not r.get("kept")]
        if pending and not (keep_previous and keep_previous.strip()):
            ids = ", ".join(r["receipt"]["id"] for r in pending)
            raise sweep.ConfigError(f"earlier round {ids} is not retired; retire it with seal, preview "
                                    "and apply --round, or pass --keep-previous <reason>")
        for entry in pending:
            entry["kept"] = keep_previous.strip()
        receipt = sweep.create_review_round(root, head, self.settings, self.repo)
        record["rounds"].append({"receipt": receipt, "namespace": str(self.repo), "status": "allocated"})
        record["complete"] = False
        self.save(record)  # No reviewer starts until this durable publication returns.
        return receipt

    def round_entry(self, record: dict, round_id: str) -> dict:
        matches = [r for r in record["rounds"] if r["receipt"]["id"] == round_id]
        if len(matches) != 1:
            raise sweep.ConfigError("round must be a receipt id allocated in this inventory")
        return matches[0]

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
        record["worktrees"].append({"path": str(path), "identity": sweep.stable_identity(str(path)),
                                    "head": git(path, "rev-parse", "HEAD"), "runtime": runtime,
                                    "branch": git(path, "rev-parse", "--abbrev-ref", "HEAD")})
        record["complete"] = False
        self.save(record)

    def track_process(self, record: dict, pid: int) -> None:
        self.require_open(record)
        # A round persists its approval only when its removal is journalled,
        # and a resume must present that same token, which binds the registered
        # writers. So the writer list freezes only while a round is "removing".
        # "allocated" persists no approval, even after an apply stopped on an
        # active user or a refusal: its next preview simply issues a new token.
        # "removed" is done.
        for entry in record["rounds"]:
            if entry["status"] == "removing":
                raise sweep.ConfigError(f"round {entry['receipt']['id']} has an interrupted retirement; "
                                        "resume it with apply --round before registering writers")
        if pid <= 1:
            raise sweep.ConfigError("invalid process id")
        os.kill(pid, 0)
        if pid not in record["pids"]:
            record["pids"].append(pid)
        self.save(record)

    def seal(self, record: dict, manifest: dict) -> dict:
        self.require_open(record)
        record["seal"] = self.retain(record, manifest, record["rounds"])
        self.save(record)
        return record["seal"]

    def seal_round(self, record: dict, round_id: str, manifest: dict) -> dict:
        # Retains one round's evidence without sealing the inventory, so later
        # rounds can still be allocated into it. One seal per round.
        self.require_open(record)
        entry = self.round_entry(record, round_id)
        if entry["status"] != "allocated" or entry.get("seal") is not None:
            raise sweep.ConfigError("round is already sealed or retiring")
        entry["seal"] = self.retain(record, manifest, [entry])
        self.save(record)
        return entry["seal"]

    def retain(self, record: dict, manifest: dict, rounds: list[dict]) -> dict:
        if manifest.get("evidence_complete") is not True:
            raise sweep.ConfigError("manifest must attest the complete required evidence closure")
        items = manifest.get("retain")
        if not isinstance(items, list):
            raise sweep.ConfigError("retain must be a list of excepted evidence (it may be empty)")
        discarded = manifest.get("discard", [])
        if not isinstance(discarded, list):
            raise sweep.ConfigError("discard must be a list")

        def normal(value: object) -> str:
            # Paths are compared after normalisation, so `a/./b` or a trailing
            # slash cannot slip one path past a uniqueness or overlap check.
            if not isinstance(value, str):
                raise sweep.ConfigError("evidence paths must be absolute path strings")
            return str(canonical(Path(value)))

        # A discard entry is a declaration: the engine records it and does not
        # check that the path exists or that the reason is true.
        discards = []
        for item in discarded:
            if (not isinstance(item, dict) or not isinstance(item.get("reason"), str)
                    or not item["reason"].strip() or not isinstance(item.get("source"), str)):
                raise sweep.ConfigError("each discard entry needs a source and a reason, "
                                        "such as where its result is recorded")
            discards.append({"source": normal(item["source"]), "reason": item["reason"]})
        if not items and not discards:
            # Discard is the normal completion path, but it is still declared:
            # an empty seal must say where the results went.
            raise sweep.ConfigError("an empty retain needs at least one discard entry saying "
                                    "where the results are recorded")
        # Validate every item (and, below, hash every source) before copying
        # any bytes, so a validation refusal copies nothing. A failure during a
        # copy can still leave a file no index names; there is no rollback.
        planned = []
        for item in items:
            if not isinstance(item, dict):
                raise sweep.ConfigError("each evidence item must be an object")
            if item.get("kind") not in KINDS or not isinstance(item.get("requires"), list):
                raise sweep.ConfigError("each evidence item needs a supported kind and requires list")
            exception = item.get("exception")
            if (not isinstance(exception, dict) or set(exception) != set(EXCEPTION_FIELDS)
                    or any(not isinstance(exception[k], str) or not exception[k].strip()
                           for k in EXCEPTION_FIELDS)):
                raise sweep.ConfigError("retained evidence needs an exception naming its unfinished task, "
                                        "next action and deletion condition (task, next_action, "
                                        "delete_when); discard it otherwise")
            # Only these keys are stored from the manifest. Engine state such
            # as a `retired` tombstone can never arrive through a manifest.
            planned.append({"source": normal(item.get("source")), "kind": item["kind"],
                            "requires": [normal(r) for r in item["requires"]],
                            "exception": {k: exception[k] for k in EXCEPTION_FIELDS}})
        sources = {item["source"] for item in planned}
        if len(sources) != len(planned):
            raise sweep.ConfigError("evidence sources must be unique")
        if any(required not in sources for item in planned for required in item["requires"]):
            raise sweep.ConfigError("required evidence dependency is missing from retain")
        if sources & {item["source"] for item in discards}:
            raise sweep.ConfigError("a source cannot be both retained and discarded")
        retired = manifest.get("retire", [])
        if not isinstance(retired, list):
            raise sweep.ConfigError("retire must enumerate diagnostics")
        for item in retired:
            if (not isinstance(item, dict) or not isinstance(item.get("reason"), str)
                    or not item["reason"].strip() or not isinstance(item.get("replaced_by"), list)
                    or not item["replaced_by"]
                    or any(normal(p) not in sources for p in item["replaced_by"])):
                raise sweep.ConfigError("retired diagnostics need a reason and retained replacements")
            path = canonical(Path(normal(item.get("source"))))
            if str(path) in sources or not any(path.is_relative_to(r["receipt"]["path"]) for r in rounds):
                raise sweep.ConfigError("retired diagnostics must be unretained files in an owned round")
        for item in planned:
            hash_file(Path(item["source"]))  # every source readable before any copy
        retained, copied = [], 0
        if planned:
            target = self.location(record["id"]) / "evidence"
            target.mkdir(mode=0o700, exist_ok=True)
            canonical(target)
            for item in planned:
                # Streaming preserves large authoritative assets without trusting
                # their filenames. Non-regular files, aliases and unreadable inputs
                # are refused; there is no generic recursive evidence copy.
                data_hash, size, wrote = copy_evidence(Path(item["source"]), target)
                copied += size if wrote else 0
                retained.append({**item, "sha256": data_hash, "size": size,
                                 "retained": str(target / data_hash)})
        return {"retained": retained, "retired": retired, "discarded": discards,
                "evidence_complete": True,
                # Bytes the retained items name (shared content counted per
                # item), and bytes this seal newly wrote to disk.
                "bytes": {"retained": sum(r["size"] for r in retained), "copied": copied}}

    def verify_evidence(self, record: dict) -> None:
        self.verify_seal(record, record["seal"])

    def verify_seal(self, record: dict, seal: dict | None) -> None:
        if seal is None:
            raise sweep.ConfigError("seal required evidence before cleanup")
        for item in seal["retained"]:
            path = canonical(Path(item["retained"]))
            if path != self.location(record["id"]) / "evidence" / item["sha256"]:
                raise sweep.ConfigError("retained evidence path escaped its session")
            # A tombstoned item was retired through retire-evidence: its bytes
            # are gone by approval. Inputs sharing this skip's shape (a
            # `retired` key and an absent path): an approved retirement, which
            # skips; a tombstone hand-written into session.json, which skips too,
            # since the registry is no boundary against same-user writes. Present
            # bytes under a tombstone (an interrupted apply) are still checked, so
            # a replacement never passes; an absent item with no tombstone is
            # missing and refuses.
            if item.get("retired") is not None and not os.path.lexists(path):
                continue
            if not os.path.lexists(path):
                raise sweep.ConfigError(f"retained evidence is missing and has no retirement tombstone: {path}")
            if hash_file(path) != (item["sha256"], item["size"]):
                raise sweep.ConfigError(f"retained evidence changed: {path}")

    def worktree_reason(self, worktree: dict) -> str | None:
        path = canonical(Path(worktree["path"]))
        if sweep.bound_identity(worktree["identity"], str(path)) is None:
            return "worktree identity changed"
        if git(path, "rev-parse", "HEAD") != worktree["head"]:
            return "worktree head changed; inventory is stale"
        if git(path, "rev-parse", "--path-format=absolute", "--git-common-dir") != str(self.common):
            return "worktree belongs to a different repository"
        worktrees = sweep.registered_worktrees(self.settings.repos)
        if str(path) not in worktrees:
            return "worktree is not registered"
        # Read stores BEFORE excluding the retiring checkout from self-protection.
        # Only this exact registered, identity/head/common-dir matched checkout
        # is exempt. Parent registrations other than the primary checkout (see
        # below), child/sibling registrations, other repositories and bare
        # configured repositories remain; missing/unreadable metadata still
        # fails closed in repository_stores. No fixture exemption is used here.
        stores = sweep.repository_stores(worktrees)
        others = [p for p in worktrees if p != str(path)]
        # A task worktree nested under the primary checkout, where Claude Code's
        # worktree tool puts it (<primary>/.claude/worktrees/<name>), is not kept
        # merely because the primary checkout holds it (#1307). Removing it
        # deletes only its own directory, and the primary checkout is exempt only
        # as its ancestor: a path that is or holds the primary still overlaps it.
        # Inputs sharing this exemption's shape (a path under the primary
        # checkout) and each one's result:
        # - a registered linked worktree of this repository tracked by this
        #   inventory: eligible, subject to every other check here.
        # - an untracked or ignored plain directory: never reaches here;
        #   track_worktree and the registration check above refuse it.
        # - a submodule checkout: its common dir differs, refused above.
        # - a registered worktree of this repository that this inventory did not
        #   track: never examined; only tracked worktrees reach this method.
        # - a path the primary checkout's index tracks (its files, or a gitlink
        #   for an embedded repository): kept below.
        # - a worktree nested under another registered worktree that is itself
        #   under the primary, or one holding a registered worktree: kept, since
        #   only the primary is dropped from the overlap list.
        # - a path held by the primary only by filesystem identity, not by its
        #   string (a case variant, an alias): kept, since no relative path into
        #   the primary's index can be trusted for it.
        # - a worktree under another configured repository's primary: refused
        #   above for its common dir; that primary is never dropped.
        primary = str(self.primary)
        if str(path).startswith(primary + os.sep) and sweep._holds(str(path), primary) is False:
            relative = os.path.relpath(path, primary)
            try:
                tracked = git(self.primary, "ls-files", "-z", "--", f":(literal,icase){relative}")
            except sweep.ConfigError as exc:
                return f"cannot read what the primary checkout tracks at the worktree's path: {exc}"
            if tracked:
                return "the primary checkout tracks content at the worktree's path"
            others = [p for p in others if p != primary]
        roots = [sweep.expand_root(raw, root=namespace)
                 for raw in self.settings.roots
                 for namespace in {self.primary, self.repo, path}]
        reason = (sweep.live_worktree_reason(str(path), others)
                  or sweep.repository_store_reason(str(path), stores)
                  or sweep.configured_root_reason(str(path), roots))
        if reason:
            return reason
        flags = git(path, "ls-files", "-v", "-z").split("\0")
        if any(item and (item[0].islower() or item[0] == "S") for item in flags):
            return "worktree index hides changes with assume-unchanged or skip-worktree; inspect and clear those flags"
        if git(path, "status", "--porcelain", "--untracked-files=all"):
            return "worktree has uncommitted or untracked content"
        # Git remove and native archive can discard ignored files. Require the
        # caller to retain/move those explicitly, including ignored caches; a
        # seal assertion alone does not distinguish a cache from unique data.
        if git(path, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"):
            return "worktree has ignored content; retain or move it before retirement"
        # Only shared branches, tags and remote-tracking refs establish retention.
        # refs/bisect, refs/worktree and refs/rewritten can belong to this checkout
        # and disappear with it. Other namespaces (including shared stash/notes
        # and custom refs) are conservatively insufficient; create a branch/tag.
        if worktree["runtime"] == "git" and not git(path, "for-each-ref", "--contains", worktree["head"], "--format=%(refname)", "refs/heads", "refs/tags", "refs/remotes"):
            return "worktree head has no containing shared branch, tag or remote ref; preserve the commit before retirement"
        if Path.cwd().resolve().is_relative_to(path):
            return "invoke cleanup from outside the worktree"
        return None

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
                try:
                    reason = self.worktree_reason(worktree)
                except subprocess.TimeoutExpired as exc:
                    reason = f"worktree inspection timed out: {exc}"
                if reason:
                    action = "kept"
            outcomes.append({"path": str(path), "action": action, "reason": reason})
        outcomes += [self.round_outcome(entry) for entry in record["rounds"]]
        measure(outcomes, record["id"])
        return {"session": record["id"], "paths": outcomes, "active_users": active,
                "evidence": record["seal"], "evidence_summary": self.evidence_summary(record),
                "approval_token": digest({"policy": record["policy"],
                    "rounds": [{"receipt": r["receipt"], "namespace": r["namespace"]}
                               for r in record["rounds"]],
                    "worktrees": record["worktrees"], "pids": record["pids"], "seal": record["seal"]})}

    def round_outcome(self, entry: dict) -> dict:
        receipt = entry["receipt"]
        # A round already recorded removed whose path is gone has nothing left
        # to act on, so its root is not re-validated: reconcile leaves the old
        # device number in root_identity, and a wiped temp root may be absent
        # or recreated. Every other shape keeps every check below when its path
        # is present: a removed round whose path returned, and an allocated or
        # removing round. An allocated or removing round whose path is gone
        # takes the #1278 block below.
        if entry["status"] == "removed" and not os.path.lexists(receipt["path"]):
            return {"path": receipt["path"], "action": "absent", "reason": None}
        # Reconcile marked this round removed while its path was absent, and its
        # receipt still names the old device. The path is back (a remounted
        # scratch volume, say); it is no longer managed here, so report it kept
        # rather than refuse the whole inventory (#1263). Only reconcile sets
        # "reconciled", and only on a round it marks removed; retire_round makes
        # no removal attempt for such a round.
        if entry.get("reconciled"):
            return {"path": receipt["path"], "action": "kept",
                    "reason": "round was marked removed by reconcile and its path reappeared; "
                              "inspect and remove it by hand"}
        # A round whose path is gone has nothing left to delete here, so a
        # scratch root that is gone too, or whose identity no longer matches,
        # must not wedge the inventory (#1278). Inputs of this shape (round not
        # yet removed, round path absent) and each one's result:
        # - root absent (removed by hand, or its volume unmounted): absent,
        #   marked unverified.
        # - root present, identity no longer matching (recreated, for example
        #   by another session's allocate in the shared root, or moved aside):
        #   absent, marked unverified.
        # - root present with its identity unchanged: absent, as before, with no
        #   mark (a round moved aside inside that root also reads so, as at the
        #   base).
        # - root not a configured expanded root, or present but refused for any
        #   other reason (a symlink, inside a registered worktree, the system
        #   temp directory): refuses, as before.
        # - any error other than FileNotFoundError on the round path or the root
        #   (permission, an ancestor replaced by a file): refuses, never absent.
        # "Unverified" means the round's data may still exist elsewhere (a moved
        # root, an unmounted volume). Nothing is deleted; retire_round records
        # the mark, and retirement_plan keeps such a round's evidence unless its
        # bytes are named with --include, inventory-wide. A round recorded
        # removed by apply whose path later returns gets every check again: the
        # same allocation is eligible for an approved removal, whose sweeper
        # removal clears the mark; a replacement refuses. Re-running apply on
        # a round whose path is still gone never clears it. Reconcile-marked rounds instead
        # read kept, above.
        # A present round path keeps every check below, root identity included.
        round_gone = _absent(receipt["path"])
        if round_gone:
            # The same expansion and membership check _round_root starts with;
            # it runs here because an absent root never reaches _round_root.
            roots = [sweep.expand_root(raw, root=Path(entry["namespace"])).rstrip("/") or "/"
                     for raw in self.settings.roots]
            if receipt["root"] not in roots:
                raise sweep.ConfigError("review round root is not an expanded scratch.roots entry")
            if _absent(receipt["root"]):
                return {"path": receipt["path"], "action": "absent", "unverified": True,
                        "reason": "round and its scratch root are both gone"}
        sweep._round_root(receipt["root"], self.settings, Path(entry["namespace"]))
        if sweep.bound_identity(receipt["root_identity"], receipt["root"]) is None:
            if round_gone:
                return {"path": receipt["path"], "action": "absent", "unverified": True,
                        "reason": "round is gone and its scratch root's identity no longer matches"}
            legacy = sweep.valid_identity(receipt["root_identity"], legacy=True)
            current = list(sweep._identity(receipt["root"])) if legacy else sweep.stable_identity(receipt["root"])
            raise sweep.ConfigError(f"allocation root identity changed (stored {receipt['root_identity']}, "
                                    f"current {current})")
        if not os.path.lexists(receipt["path"]):
            # Absence is an idempotent result, not permission to delete a
            # replacement. If a path reappears its allocation identity must
            # still match before the existing sweeper may touch it.
            return {"path": receipt["path"], "action": "absent", "reason": None}
        try:
            result = sweep.finish_review_round(receipt, self.settings, Path(entry["namespace"]),
                                               resuming=entry["status"] == "removing")
        except FileNotFoundError as exc:
            # Let the sweeper validate directory identity first. Only its
            # missing-marker diagnostic is translated; no guard is bypassed.
            if exc.filename != str(Path(receipt["path"]) / sweep.ROUND_MARKER):
                raise
            raise sweep.ConfigError("round marker missing without an approved removal journal") from exc
        return {"path": result.path, "action": result.action, "reason": result.reason}

    def preview_round(self, record: dict, round_id: str) -> dict:
        entry = self.round_entry(record, round_id)
        self.verify_seal(record, entry.get("seal"))
        active = active_users([entry["receipt"]["path"]], record["pids"])
        outcomes = [self.round_outcome(entry)]
        measure(outcomes, record["id"])
        # The token binds this round's receipt and seal plus the inventory's
        # registered writers, never the other rounds, which stay unaffected.
        return {"session": record["id"], "round": round_id, "paths": outcomes,
                "active_users": active, "evidence": entry["seal"], "evidence_summary": self.evidence_summary(record),
                "approval_token": digest({"policy": record["policy"], "round": {
                    "receipt": entry["receipt"], "namespace": entry["namespace"]},
                    "pids": record["pids"], "seal": entry["seal"]})}

    def apply_round(self, record: dict, round_id: str, approval: str, processes_finished: bool) -> dict:
        if not processes_finished:
            raise sweep.ConfigError("apply requires explicit completion of all writers and descendants")
        entry = self.round_entry(record, round_id)
        preview = self.preview_round(record, round_id)
        if approval != preview["approval_token"]:
            raise sweep.ConfigError("approval does not match this exact round and evidence seal")
        if entry["status"] == "removing" and entry.get("approval") != approval:
            raise sweep.ConfigError("round has a different persisted approval")
        preview["processes_finished_attestation"] = True
        result = preview["paths"][0]
        if preview["active_users"]:
            entry["last_result"] = {**preview, "complete": False}
            self.save(record)
            return entry["last_result"]
        self.retire_round(record, entry, result, lambda: self.verify_seal(record, entry["seal"]), approval)
        entry["last_result"] = {**preview, "complete": result["action"] in {"removed", "absent"}}
        # A reconciled round whose path reappeared stays "removed" but is not
        # gone, matching apply's path-based verdict for the same state.
        record["complete"] = (not record["worktrees"]
                              and all(r["status"] == "removed" for r in record["rounds"])
                              and not any(r.get("reconciled") and os.path.lexists(r["receipt"]["path"])
                                          for r in record["rounds"]))
        self.save(record)
        return entry["last_result"]

    def retire_round(self, record: dict, entry: dict, result: dict, verify, approval: str | None = None) -> None:
        if result["action"] in {"eligible", "kept"} and not entry.get("reconciled"):
            try:
                verify()
                if active_users([entry["receipt"]["path"]], record["pids"]):
                    raise sweep.ConfigError("round acquired an active user")
                # Publish intent only after the sweeper's final guards. A
                # retry may lack the marker if interruption struck rmtree;
                # durable approval, root and directory identities remain bound.
                def journal_removal(current=entry):
                    current["status"] = "removing"
                    if approval is not None:
                        current["approval"] = approval  # the round's resume authority
                    self.save(record)

                outcome = sweep.finish_review_round(entry["receipt"], self.settings,
                    Path(entry["namespace"]), apply=True, reviewers_finished=True,
                    resuming=entry["status"] == "removing", before_remove=journal_removal)
                result.update(action=outcome.action, reason=outcome.reason)
            except (OSError, sweep.ConfigError, sweep.Refused) as exc:
                result.update(action="kept", reason=str(exc))
        verify()
        if result["action"] in {"removed", "absent"} and os.path.lexists(result["path"]):
            result.update(action="kept", reason="path exists after retirement; inspect before retrying")
        if result["action"] in {"removed", "absent"}:
            entry["status"] = "removed"
            if result.get("unverified"):
                entry["unverified"] = result["reason"]
            elif result["action"] == "removed":
                # Only the sweeper's own removal, after every check, verifies
                # that the round's data is gone. An `absent` never clears the
                # mark: for a round already removed it is a no-op re-observation
                # of the same missing path, not a verification.
                entry.pop("unverified", None)
        self.save(record)

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
                # Git's refusal is supplementary: it can discard ignored object
                # stores. Refresh our content and dependency checks before Git.
                # Never use --force or the scratch deletion primitive here.
                try:
                    self.verify_evidence(record)
                    reason = self.worktree_reason(worktree)
                    if reason:
                        raise sweep.ConfigError(reason)
                    if active_users([worktree["path"]], record["pids"]):
                        raise sweep.ConfigError("worktree acquired an active user")
                    git(self.repo, "worktree", "remove", worktree["path"], timeout=300)
                except (OSError, sweep.ConfigError, subprocess.TimeoutExpired) as exc:
                    result.update(action="kept", reason=str(exc))
                else:
                    result.update(action="removed", reason=None)
        offset = len(record["worktrees"])
        for entry, result in zip(record["rounds"], preview["paths"][offset:], strict=True):
            self.retire_round(record, entry, result, lambda: self.verify_evidence(record))
        self.verify_evidence(record)
        for result in preview["paths"]:
            if result["action"] in {"removed", "absent"} and os.path.lexists(result["path"]):
                result.update(action="kept", reason="path exists after retirement; inspect before retrying")
        record["complete"] = all(p["action"] in {"removed", "absent"} for p in preview["paths"])
        record["last_result"] = {**preview, "complete": record["complete"]}
        self.save(record)
        return record["last_result"]


def _absent(path: str) -> bool:
    """True only when the path does not exist; any other inspection error raises."""
    try:
        os.lstat(path)
    except FileNotFoundError:
        return True
    return False


def measure(outcomes: list[dict], owner: str) -> None:
    for item in outcomes:
        item["owner"] = owner
        item["bytes"] = None
        if item["action"] == "absent":
            item["bytes"] = 0
        elif item["action"] in {"eligible", "remove-worktree", "archive-with-runtime"}:
            measurement = sweep.scan(item["path"], os.lstat(item["path"]))
            if not measurement.problems:
                item["bytes"] = measurement.size


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


def copy_evidence(source: Path, target: Path) -> tuple[str, int, bool]:
    expected, size = hash_file(source)
    destination = target / expected
    if destination.exists():
        if hash_file(destination) != (expected, size):
            raise sweep.ConfigError("existing retained evidence is corrupt")
        return expected, size, False
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
    return expected, size, True


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
    for action in ("allocate", "track-worktree", "track-process", "seal", "preview", "apply", "reconcile",
                   "retire-evidence"):
        command = sub.add_parser(action)
        command.add_argument("session")
        if action == "allocate":
            command.add_argument("--root", required=True)
            command.add_argument("--head", required=True)
            command.add_argument("--keep-previous", metavar="REASON",
                                 help="allocate while earlier rounds stay unretired; they retire with the inventory")
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
        elif action == "reconcile":
            command.add_argument("--approve", metavar="APPROVAL_TOKEN",
                                 help="apply the previewed plan; without it, only preview")
        elif action == "retire-evidence":
            command.add_argument("--approve", metavar="APPROVAL_TOKEN",
                                 help="delete the previewed evidence; without it, only preview")
            command.add_argument("--include", metavar="SHA256", action="append", default=[],
                                 help="also retire these bytes when an exception or the source rule keeps "
                                      "them; asserts the deletion condition of every item holding them")
        if action in ("seal", "preview", "apply"):
            command.add_argument("--round", metavar="RECEIPT_ID",
                                 help="act on one allocated round without sealing the inventory")
    args = parser.parse_args(argv)
    try:
        repo = repo_root(Path.cwd())
        registry = Registry(repo, args.config or repo / "config/dev-model.yaml")
        if args.action == "list":
            result = registry.inventories()
        else:
            with registry.lock():
                if args.action == "retire-evidence":
                    result = (registry.retire_evidence(args.session, args.approve, args.include)
                              if args.approve is not None
                              else registry.retirement_plan(args.session, args.include)[1])
                    print(json.dumps(result, indent=2))
                    return 0
                if args.action == "reconcile":
                    result = (registry.reconcile(args.session, args.approve) if args.approve is not None
                              else registry.reconcile_plan(args.session)[1])
                    print(json.dumps(result, indent=2))
                    return 0
                record = registry.start() if args.action == "start" else registry.load(args.session)
                result = record
                if args.action == "allocate":
                    result = registry.allocate(record, args.root, args.head, args.keep_previous)
                elif args.action == "seal" and args.round is not None:
                    result = registry.seal_round(record, args.round, read_json(args.manifest))
                elif args.action == "preview" and args.round is not None:
                    result = registry.preview_round(record, args.round)
                elif args.action == "apply" and args.round is not None:
                    result = registry.apply_round(record, args.round, args.approve, args.processes_finished)
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
