"""Engine failure types and their exit statuses."""

from __future__ import annotations


class SystemizeError(RuntimeError):
    """A hard stop: exit 1, one stderr line naming the failed check and remedy."""

    exit_code = 1


class UsageError(SystemizeError):
    """Rejected invocation syntax: exit 2, before any preflight."""

    exit_code = 2
