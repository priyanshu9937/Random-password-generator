"""Shared application helpers."""

import pyperclip


class ClipboardError(RuntimeError):
    """Raised when the system clipboard cannot be accessed."""


def copy_to_clipboard(value: str) -> None:
    """Copy text to the system clipboard without suppressing failures."""
    try:
        pyperclip.copy(value)
    except (pyperclip.PyperclipException, OSError) as error:
        raise ClipboardError(
            "The clipboard is unavailable. Check your desktop clipboard support."
        ) from error
