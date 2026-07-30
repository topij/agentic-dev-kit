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
  guard it stands for. The *outcome* matches ``write_text`` (nothing written),
  but the exception does **not**: ``AtomicWriteRefused`` is not an ``OSError``,
  so a caller porting from ``write_text`` on the strength of this bullet and
  catching ``OSError`` alone would get an uncaught traceback where it used to
  get a handled ``PermissionError``. Catch both.
* **A non-writable parent directory is refused too**, and this is a capability
  ``write_text`` had that publishing by rename cannot: it writes the file, while
  a rename needs to create an entry in the directory. A document that is
  writable inside a ``0555`` directory could be swept before and cannot now.
  It surfaces as an ordinary ``OSError`` from the temp creation.
* **A hardlinked target is refused.** After a rename the other names for that
  inode keep the old content, so an alias silently stops tracking the document.
  There is no way to publish atomically *and* keep the alias, so the caller is
  told rather than one of the two being chosen for them.
* **Ownership that cannot be carried is refused**, rather than silently
  reassigning the document to whoever ran the tool.

* **A non-regular target is refused** — FIFO, socket, device. A rename replaces
  such a file with a regular one where ``write_text`` would have written
  *through* it.

Every one of these checks runs during staging, before anything is published.

**Two limits of those checks, stated rather than left to be discovered:**

* The read-only test is ``os.access(target, os.W_OK)``, which consults the
  **real** uid/gid and returns true for **root whatever the mode**. Running as
  root — routine in devcontainers — the ``0444`` refusal does not fire and the
  rename removes the read-only bit. ``write_text`` as root would also have
  written the file, so this is not a regression; it is a guard that does not
  guard for that user, which is a different thing from one that does.
* ``_default_mode()`` reads the umask by setting and restoring it, a
  process-global side effect. It runs only when the target does not exist, so
  the sweep never reaches it, but a threaded caller creating a new file races
  it.

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

Temp files are named ``.<document>.<random>.devkit-tmp`` and every path this
module controls *attempts* to remove them, exceptions included. Two routes still
leave one behind, which is why ``.gitignore`` carries ``*.devkit-tmp``:
``SIGKILL`` runs no handler at all, and an ``unlink`` that itself fails is
deliberately swallowed rather than allowed to escape a caller's ``finally``
(see :meth:`StagedWrite.abort`) — so a directory that has become unwritable
leaves the debris it also caused. The name is randomised via
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
from typing import Literal

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
        self._settled = False

    def publish_state(self) -> Literal["published", "pending", "unknown"]:
        """``"published"``, ``"pending"`` or ``"unknown"`` — **observed, not remembered**.

        ``os.replace`` removes the temp, so the temp's absence is the best
        available evidence that the rename happened. A stored flag is not good
        enough: an interrupt can land between ``os.replace`` returning and the
        assignment that records it, leaving a flag that says "not published" for
        a document that was. A caller choosing whether to roll back has to read
        the filesystem, or it will roll back a completed move and put the
        content in both documents.

        Two honesty caveats, both from review, because an earlier version of
        this returned a plain bool documented as "the fact":

        * It is **evidence, not the fact**. Anything else that removes the temp
          — a tmp reaper, an operator, another tool — reads as published. So the
          caller must not turn a positive reading into an unqualified all-clear.
        * It can be **indeterminate**. ``Path.exists()`` propagates ``EACCES``
          rather than swallowing it, so a parent directory that becomes
          unsearchable mid-run made this *raise* — from inside an exception
          handler, which replaced the real exception, skipped the rollback and
          let the cleanup delete it. Hence ``"unknown"`` rather than a guess.

        **This method must never raise**, and ``except OSError`` was not enough
        to achieve that. ``Path.exists()`` calls ``os.stat``, a blocking
        syscall, and every caller is a failure handler — so an interrupt landing
        here escapes the handler, skips the recovery it was about to run, and
        the caller's cleanup then deletes the copy staged for it. Measured at
        both of this kit's call sites: swept blocks in neither document, nothing
        on stderr. Same reasoning, and the same trade, as
        :meth:`_fsync_parent` — swallowing a second interrupt is the lesser
        harm.

        Only meaningful before :meth:`abort`, which also removes the temp.
        """
        try:
            return "pending" if self.temp.exists() else "published"
        except BaseException:  # noqa: BLE001 — see the docstring; this cannot raise
            return "unknown"

    def commit(self) -> None:
        """Publish the staged content over the target. Atomic; no allocation.

        Raises only if the *publish* itself failed. Once ``os.replace`` returns,
        nothing this method does afterwards can raise — see :meth:`_fsync_parent`.
        """
        if self._settled:
            return
        os.replace(self.temp, self.target)
        self._settled = True
        self._fsync_parent()

    def _fsync_parent(self) -> None:
        """Make the rename durable. **Nothing here may raise. Ever.**

        This runs after ``os.replace`` has already succeeded, so an exception
        escaping it would be reported by the caller as a failed write over a
        document that was in fact published — the false all-clear that #164
        exists to eliminate, reintroduced one call later.

        Two review rounds landed here, and the second is why the handler catches
        ``BaseException`` rather than ``OSError``:

        * A first version guarded ``os.open`` and suppressed ``os.fsync`` but
          left the descriptor teardown in a bare ``finally``. That syscall
          returns EIO on NFS, and injecting it there produced exactly the
          original bug: handoff swept, history untouched, staged rollback
          discarded, ``no changes applied`` on stderr.
        * Narrowing to ``OSError`` still left the realistic case open. ``os.open``
          and ``os.fsync`` on a directory are *blocking* syscalls — the likeliest
          landing spot for an interactive Ctrl-C, and this tool's caller is
          interactive. An escaping ``KeyboardInterrupt`` here reached the
          caller's cleanup and unlinked the staged rollback, losing the swept
          blocks with no message at all.

        Swallowing an interrupt is the lesser harm: the window is microseconds,
        the document is already correct, and a second Ctrl-C still works.
        Directory fsync is also simply unsupported on some platforms.
        """
        dir_fd = None
        try:
            dir_fd = os.open(self.target.parent, os.O_RDONLY)
            os.fsync(dir_fd)
        except BaseException:  # noqa: BLE001 — see the docstring; this cannot raise
            pass
        finally:
            if dir_fd is not None:
                with contextlib.suppress(OSError):
                    os.close(dir_fd)

    def abort(self) -> None:
        """Discard the staged content. Never touches the target."""
        if self._settled:
            return
        self._settled = True
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
        if not stat_module.S_ISREG(existing.st_mode):
            # Named before the hardlink check, which every directory trips
            # (`.` and `..` give nlink >= 2) — so a directory used to be
            # diagnosed as a hardlink problem and told to remove links.
            # Widened from directories to every non-regular file: a rename over
            # a FIFO, socket or device REPLACES it with a regular file, where
            # `write_text` would have written through it. Measured on a FIFO.
            kind = "a directory" if stat_module.S_ISDIR(existing.st_mode) else "not a regular file"
            raise AtomicWriteRefused(
                f"{target} is {kind}. Publishing by rename would replace it with "
                "a regular file rather than writing through it."
            )
        if existing.st_nlink > 1:
            raise AtomicWriteRefused(
                f"{target} has {existing.st_nlink} hard links; publishing by rename "
                "would leave the other name(s) pointing at the old content. "
                "Remove the extra link(s), or write this document some other way."
            )
        if not os.access(target, os.W_OK):
            # `os.access` reports "cannot write", not "the mode bits forbid it":
            # a read-only MOUNT (EROFS) and a symlink loop (ELOOP) land here too,
            # for which "check the permissions" is the wrong remedy. So the
            # message states what was observed and offers the read-only case as
            # the likely reading rather than the diagnosis.
            raise AtomicWriteRefused(
                f"{target} is not writable by this process — most often a "
                "read-only file, but a read-only mount or an unresolvable path "
                "reports the same way. Refusing rather than replacing it by "
                "rename, which for the read-only-file case would succeed and "
                "delete the read-only bit."
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

        # `open` on a descriptor takes ownership of it — and closes it even when
        # it FAILS (a bad `encoding` or `newline` raises LookupError/ValueError
        # after the descriptor is gone). So `fd` is retired either way, before
        # the handler can double-close it. A double close raised EBADF from the
        # cleanup path, which both replaced the real exception with a bogus
        # "Bad file descriptor" and aborted the handler before `temp.unlink()`,
        # leaking the temp this module promises to remove — and closing a stale
        # descriptor number is the classic route to closing an unrelated file.
        try:
            handle = open(fd, "w", encoding=encoding, newline=newline)  # noqa: SIM115
        finally:
            # Unconditionally, and before the `with` below: `open` owns the
            # descriptor on success AND has already closed it on failure, so in
            # neither case may the handler close it again.
            fd = -1
        with handle:
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
            with contextlib.suppress(OSError):
                os.close(fd)
        # OSError, not just FileNotFoundError, for the same reason `abort` uses
        # it: this runs while an exception is already propagating, and raising
        # here would replace the real cause with a cleanup failure.
        with contextlib.suppress(OSError):
            temp.unlink()
        raise

    return StagedWrite(target, temp)
