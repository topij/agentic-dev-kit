"""Publish a text document by rename, so a failed write never destroys it.

``Path.write_text`` opens mode ``'w'``, which **truncates before the first byte
is written**. Any failure between that truncation and the flush — ENOSPC, EIO,
quota, a killed process — leaves the document empty or partial. Issue #164
measured a 26,807-byte living handoff going to 0 bytes while the caller printed
*"no changes applied"*.

This module writes the new content to a sibling temporary file, fsyncs it, and
only then ``os.replace``\\ s it over the target. The target either has its old
bytes or its new bytes; it never has a prefix of the new ones.

Staging and publishing are separate steps on purpose
----------------------------------------------------

:func:`stage_text` returns a :class:`StagedWrite` that has already done all the
expensive, failure-prone work — allocation, encoding, the actual disk write —
and left a single ``os.replace`` to perform. A caller updating **two** documents
that must move together can stage both, and only then publish both:

    plan = stage_text(plan_path, new_plan)
    history = stage_text(history_path, new_history)   # may still fail — nothing
    plan.commit()                                     # is published yet
    history.commit()

Every way a write can run out of space or hit an I/O error is now confined to
the staging phase, where aborting costs nothing and no document has been
touched. That is what makes a rollback affordable: a caller that needs one
stages it up front (see ``archive_plan_sessions.py``), so the recovery path is
an ``os.replace`` whose cost was paid while failing was still free — not a fresh
full-size write attempted on the disk that just refused one.

An earlier attempt at #164 (reverted from #160) wrote the first document, then
the second, then rewrote the first from memory to roll back. Under ENOSPC —
the failure class it was written for — that rollback needed *more* free space
than the write it was undoing, because the original is strictly larger than a
swept document. Staging inverts that ordering.

What it refuses to do
---------------------

Rename-based publishing is not a drop-in for ``write_text``: it replaces a
*directory entry*, so it silently ignores properties of the file that
``write_text`` respects. Rather than paper over the difference, each one is
either carried across or refused loudly, and never discovered after the fact:

* **Symlinks are followed, not replaced.** The target is resolved with
  ``os.path.realpath`` first and the temp is created beside the *resolved*
  file, so a symlinked document is written **through**. Replacing the link
  itself would leave the real document untouched while reporting success.
* **Mode, owner and group are carried** from the existing file onto the temp
  before the rename. Without this every publish resets a ``0600`` document to
  the temp's own permissions.
* **A read-only target is refused** (``AtomicWriteRefused``). ``os.replace``
  needs write permission on the *directory*, not on the file, so a ``0444``
  document would otherwise be replaceable — deleting the read-only bit and the
  guard it stands for. Refusing preserves exactly what ``write_text`` does
  today: ``PermissionError``, nothing written.
* **A hardlinked target is refused.** After a rename the other names for that
  inode keep the old content, so an alias silently stops tracking the document.
  There is no way to publish atomically *and* keep the alias, so the caller is
  told rather than one of the two being chosen for them.
* **Ownership that cannot be carried is refused**, rather than silently
  reassigning the document to whoever ran the tool.

Every one of these checks runs during staging, before anything is published.

Durability
----------

The temp is flushed and ``os.fsync``\\ ed before the rename, so the bytes are on
the medium before the directory entry points at them. The parent directory is
fsynced after the rename on a best-effort basis: it makes the rename itself
survive a power loss, but it happens *after* the replace has already succeeded,
so a failure there is not a failed write and is not reported as one. Directory
fsync is also not supported everywhere.

Debris
------

Temp files are named ``.<document>.<random>.devkit-tmp`` and removed on every
path this module controls, including exceptions. ``SIGKILL`` runs no handler,
so a hard kill can still leave one beside the document — which is why
``.gitignore`` carries ``*.devkit-tmp``. The name is randomised via
``tempfile.mkstemp`` (``O_EXCL``): a fixed name would let two concurrent runs
write each other's bytes, and would let a pre-existing symlink at that name
turn the write into an arbitrary-file clobber (CWE-59/CWE-377).
"""

from __future__ import annotations

import contextlib
import os
import stat as stat_module
import tempfile
from pathlib import Path

TEMP_SUFFIX = ".devkit-tmp"
"""Suffix for staged temp files. Mirrored by the ``*.devkit-tmp`` .gitignore rule."""


class AtomicWriteRefused(Exception):
    """The target cannot be published by rename without losing a property of it.

    Deliberately **not** an ``OSError``: these are conditions this module
    declines to handle, not failures of the underlying write, and a caller
    reporting "write failed" for one would be describing something that never
    happened. Callers catch both, and say which occurred.
    """


def _default_mode() -> int:
    """The mode ``write_text`` would create a new file with (``0o666`` & ~umask)."""
    umask = os.umask(0o022)
    os.umask(umask)
    return 0o666 & ~umask


class StagedWrite:
    """New content, fully written and fsynced, awaiting a single ``os.replace``.

    Created by :func:`stage_text`. Exactly one of :meth:`commit` or
    :meth:`abort` should be called; both are idempotent, so a ``finally: abort()``
    after a successful commit is safe and is the recommended shape.
    """

    def __init__(self, target: Path, temp: Path) -> None:
        self.target = target
        self.temp = temp
        self._done = False

    def commit(self) -> None:
        """Publish the staged content over the target. Atomic; no allocation."""
        if self._done:
            return
        os.replace(self.temp, self.target)
        self._done = True
        # After the replace, not before: this makes the *rename* durable. It is
        # best-effort by design — the write has already succeeded at this point,
        # so raising here would report a failure that did not occur, and some
        # filesystems and platforms do not support fsync on a directory at all.
        try:
            dir_fd = os.open(self.target.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            with contextlib.suppress(OSError):
                os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def abort(self) -> None:
        """Discard the staged content. Never touches the target."""
        if self._done:
            return
        self._done = True
        # OSError, not just FileNotFoundError. The documented shape is
        # `finally: abort()`, so anything raised here escapes from a `finally`
        # and replaces the caller's real outcome with a traceback — turning a
        # clean exit 2 into an exit 1, outside the exit-code contract its caller
        # publishes. A temp that cannot be removed is not something a caller can
        # act on, and leaving it is what `*.devkit-tmp` in .gitignore covers.
        with contextlib.suppress(OSError):
            self.temp.unlink()


def stage_text(
    path: str | os.PathLike[str],
    text: str,
    *,
    encoding: str = "utf-8",
    newline: str | None = None,
) -> StagedWrite:
    """Write ``text`` to a temp file beside ``path``, ready to be published.

    Does everything that can fail *except* the publish itself. Raises
    ``OSError`` if the content could not be written, or
    :class:`AtomicWriteRefused` if publishing by rename would lose a property of
    the existing document (see the module docstring). In both cases nothing has
    been published and no temp survives.

    ``newline`` is passed through to the underlying text stream, so a caller
    that has decided its documents are byte-preserving can pass ``""``.
    """
    target = Path(os.path.realpath(path))
    existing: os.stat_result | None = None
    with contextlib.suppress(FileNotFoundError):
        existing = target.lstat()

    if existing is not None:
        if existing.st_nlink > 1:
            raise AtomicWriteRefused(
                f"{target} has {existing.st_nlink} hard links; publishing by rename "
                "would leave the other name(s) pointing at the old content. "
                "Remove the extra link(s), or write this document some other way."
            )
        if not os.access(target, os.W_OK):
            raise AtomicWriteRefused(
                f"{target} is not writable. Refusing rather than replacing it by "
                "rename, which would succeed and delete the read-only bit."
            )

    fd, temp_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=TEMP_SUFFIX
    )
    temp = Path(temp_name)
    try:
        if existing is not None:
            os.fchmod(fd, stat_module.S_IMODE(existing.st_mode))
            if hasattr(os, "fchown") and (existing.st_uid, existing.st_gid) != (
                os.getuid(),
                os.getgid(),
            ):
                try:
                    os.fchown(fd, existing.st_uid, existing.st_gid)
                except OSError as exc:
                    raise AtomicWriteRefused(
                        f"cannot carry ownership of {target} "
                        f"(uid={existing.st_uid}, gid={existing.st_gid}) onto a "
                        f"replacement file ({exc}); refusing rather than silently "
                        "reassigning the document."
                    ) from exc
        else:
            os.fchmod(fd, _default_mode())

        # `open` on a file descriptor takes ownership of it, so the descriptor
        # must not also be closed by the handler below once this succeeds —
        # hence the reassignment before anything else can raise.
        with open(fd, "w", encoding=encoding, newline=newline) as handle:
            fd = -1
            handle.write(text)
            handle.flush()
            # Before the rename, not after: the bytes have to be on the medium
            # before a directory entry points at them, or a crash publishes a
            # name for content that was never written.
            os.fsync(handle.fileno())
    except BaseException:
        # BaseException, not Exception: a KeyboardInterrupt or SystemExit here
        # would otherwise leave a temp file next to the document, in the very
        # directory the caller's next step stages for commit.
        if fd != -1:
            os.close(fd)
        with contextlib.suppress(FileNotFoundError):
            temp.unlink()
        raise

    return StagedWrite(target, temp)


def atomic_write_text(
    path: str | os.PathLike[str],
    text: str,
    *,
    encoding: str = "utf-8",
    newline: str | None = None,
) -> None:
    """Stage and publish in one step — the single-document form of :func:`stage_text`."""
    staged = stage_text(path, text, encoding=encoding, newline=newline)
    try:
        staged.commit()
    finally:
        staged.abort()
