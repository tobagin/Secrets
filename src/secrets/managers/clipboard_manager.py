"""
Clipboard manager for handling clipboard operations with auto-clear functionality.
"""

from typing import Optional
from gi.repository import Gdk, GLib
from .toast_manager import ToastManager


class ClipboardManager:
    """Manages clipboard operations with auto-clear functionality."""

    def __init__(self, display: Gdk.Display, toast_manager: ToastManager, config_manager=None):
        self.clipboard = display.get_clipboard()
        self.toast_manager = toast_manager
        self.config_manager = config_manager
        self._clear_timeout_id: Optional[int] = None

    def copy_text(self, text: str, description: str = "Text", auto_clear: bool = False):
        """Copy text to clipboard with user feedback and optional auto-clear."""
        if not text:
            self.toast_manager.show_warning(f"No {description.lower()} to copy")
            return False

        try:
            self.clipboard.set(text)
            self.toast_manager.show_success(f"{description} copied to clipboard")

            # Set up auto-clear if requested
            if auto_clear and self.config_manager:
                self._setup_auto_clear(text)

            return True
        except Exception as e:
            self.toast_manager.show_error(f"Failed to copy {description.lower()}: {e}")
            return False

    def copy_password(self, password: str) -> bool:
        """Copy password to clipboard with auto-clear."""
        if not password:
            self.toast_manager.show_warning("No password to copy")
            return False
        return self.copy_text(password, "Password", auto_clear=True)

    def copy_username(self, username: str) -> bool:
        """Copy username to clipboard."""
        if not username:
            self.toast_manager.show_warning("No username to copy")
            return False
        return self.copy_text(username, "Username")

    def _setup_auto_clear(self, original_text: str):
        """Setup auto-clear timer for sensitive data."""
        # Cancel any existing timer
        if self._clear_timeout_id:
            GLib.source_remove(self._clear_timeout_id)

        # Get timeout from config
        timeout_seconds = 45  # Default
        if self.config_manager:
            config = self.config_manager.get_config()
            timeout_seconds = config.security.clear_clipboard_timeout

        # Set up new timer
        self._clear_timeout_id = GLib.timeout_add_seconds(
            timeout_seconds,
            self._auto_clear_callback,
            original_text
        )

    def _auto_clear_callback(self, original_text: str):
        """Auto-clear callback that only clears if clipboard still contains the original text."""
        try:
            # Use async read to avoid blocking
            def on_read_complete(clipboard, result):
                try:
                    current_text = clipboard.read_text_finish(result)
                    if current_text == original_text:
                        self.clipboard.set("")
                        self.toast_manager.show_info("Clipboard automatically cleared")
                except Exception:
                    # If we can't read clipboard, just clear it to be safe
                    try:
                        self.clipboard.set("")
                        self.toast_manager.show_info("Clipboard automatically cleared")
                    except Exception:
                        pass  # Ignore errors during auto-clear

            self.clipboard.read_text_async(None, on_read_complete)
        except Exception:
            # Fallback: just clear the clipboard
            try:
                self.clipboard.set("")
                self.toast_manager.show_info("Clipboard automatically cleared")
            except Exception:
                pass  # Ignore errors during auto-clear

        self._clear_timeout_id = None
        return False  # Don't repeat
