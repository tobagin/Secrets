"""
Password display manager for handling password visibility and auto-hide functionality.
"""

from typing import Optional
from gi.repository import Gtk, Adw, GLib
from .toast_manager import ToastManager


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
