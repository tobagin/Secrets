"""
Manager classes for handling specific UI components and operations.
"""
from typing import Optional, Callable, List
from gi.repository import Gtk, Adw, Gdk, GLib, Gio
from .models import PasswordEntry, PasswordListItem, SearchResult, AppState


class ToastManager:
    """Manages toast notifications throughout the application."""
    
    def __init__(self, toast_overlay: Adw.ToastOverlay):
        self.toast_overlay = toast_overlay
    
    def show_info(self, message: str):
        """Show an informational toast."""
        self.toast_overlay.add_toast(Adw.Toast.new(message))
    
    def show_success(self, message: str):
        """Show a success toast."""
        toast = Adw.Toast.new(message)
        self.toast_overlay.add_toast(toast)
    
    def show_error(self, message: str):
        """Show an error toast."""
        toast = Adw.Toast.new(f"Error: {message}")
        self.toast_overlay.add_toast(toast)
    
    def show_warning(self, message: str):
        """Show a warning toast."""
        toast = Adw.Toast.new(f"Warning: {message}")
        self.toast_overlay.add_toast(toast)


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
            self.clipboard.set_text(text)
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
        return self.copy_text(password, "Password", auto_clear=True)

    def copy_username(self, username: str) -> bool:
        """Copy username to clipboard."""
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
            # Check if clipboard still contains our text
            current_text = self.clipboard.read_text()
            if current_text == original_text:
                self.clipboard.set_text("")
                self.toast_manager.show_info("Clipboard automatically cleared")
        except Exception:
            # If we can't read clipboard, just clear it to be safe
            try:
                self.clipboard.set_text("")
                self.toast_manager.show_info("Clipboard automatically cleared")
            except Exception:
                pass  # Ignore errors during auto-clear

        self._clear_timeout_id = None
        return False  # Don't repeat


class PasswordDisplayManager:
    """Manages password visibility and auto-hide functionality."""
    
    def __init__(self, 
                 password_label: Gtk.Label,
                 toggle_button: Gtk.ToggleButton,
                 expander_row: Adw.ExpanderRow,
                 toast_manager: ToastManager):
        self.password_label = password_label
        self.toggle_button = toggle_button
        self.expander_row = expander_row
        self.toast_manager = toast_manager
        
        self._current_password: Optional[str] = None
        self._visible = False
        self._auto_hide_timeout_id: Optional[int] = None
        
        # Connect signals
        self.toggle_button.connect("toggled", self._on_toggle_clicked)
    
    def set_password(self, password: Optional[str]):
        """Set the current password."""
        self._current_password = password
        self._update_display()
    
    def _update_display(self):
        """Update the password display based on current state."""
        if not self._current_password:
            self.password_label.set_text("No password available")
            self.expander_row.set_subtitle("N/A")
            self.toggle_button.set_sensitive(False)
            return
        
        self.toggle_button.set_sensitive(True)
        
        if self._visible:
            self.password_label.set_text(self._current_password)
            self.expander_row.set_subtitle("Visible")
            self.toggle_button.set_icon_name("eye-open-negative-filled-symbolic")
            self._start_auto_hide_timer()
        else:
            self.password_label.set_text("●●●●●●●●")
            self.expander_row.set_subtitle("Hidden")
            self.toggle_button.set_icon_name("eye-not-looking-symbolic")
            self._cancel_auto_hide_timer()
    
    def _on_toggle_clicked(self, toggle_button):
        """Handle toggle button clicks."""
        self._visible = toggle_button.get_active()
        self._update_display()
    
    def _start_auto_hide_timer(self):
        """Start the auto-hide timer."""
        self._cancel_auto_hide_timer()
        self._auto_hide_timeout_id = GLib.timeout_add_seconds(30, self._auto_hide_callback)
    
    def _cancel_auto_hide_timer(self):
        """Cancel the auto-hide timer."""
        if self._auto_hide_timeout_id:
            GLib.source_remove(self._auto_hide_timeout_id)
            self._auto_hide_timeout_id = None
    
    def _auto_hide_callback(self):
        """Auto-hide callback."""
        if self._visible:
            self.toggle_button.set_active(False)
            self._visible = False
            self._update_display()
            self.toast_manager.show_info("Password automatically hidden")
        return False  # Don't repeat
    
    def hide_password(self):
        """Programmatically hide the password."""
        if self._visible:
            self.toggle_button.set_active(False)
            self._visible = False
            self._update_display()


class SearchManager:
    """Manages search functionality."""
    
    def __init__(self, 
                 search_entry: Gtk.SearchEntry,
                 password_store,
                 toast_manager: ToastManager,
                 on_search_results: Callable[[SearchResult], None]):
        self.search_entry = search_entry
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.on_search_results = on_search_results
        
        # Connect signals
        self.search_entry.connect("search-changed", self._on_search_changed)
    
    def _on_search_changed(self, search_entry):
        """Handle search entry changes."""
        query = search_entry.get_text().strip()
        
        if not query:
            # Empty query - show all passwords
            self.on_search_results(SearchResult("", [], 0))
            return
        
        try:
            success, result = self.password_store.search_passwords(query)
            
            if success:
                entries = []
                if result:
                    for path_str in sorted(result):
                        entry = PasswordEntry(path=path_str, is_folder=False)
                        entries.append(entry)
                
                search_result = SearchResult(query, entries, len(entries))
                self.on_search_results(search_result)
                self.toast_manager.show_info(search_result.get_summary())
            else:
                # Error occurred
                self.toast_manager.show_error(f"Search failed: {result}")
                self.on_search_results(SearchResult(query, [], 0))
                
        except Exception as e:
            self.toast_manager.show_error(f"Search error: {e}")
            self.on_search_results(SearchResult(query, [], 0))
