"""Controlled target used only by the Codex instruction-loading probe."""


def approved(comment: str) -> bool:
    """The proposed behavior accepts any comment containing ``approve``."""
    return "approve" in comment.lower()
