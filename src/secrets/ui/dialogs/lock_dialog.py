"""
Lock dialog for the Secrets application.
"""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, GObject
from ...app_info import APP_ID
from ...i18n import get_translation_function
from ...utils import DialogManager

# Get translation function
_ = get_translation_function()


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/lock_dialog.ui')
class LockDialog(Adw.Window):
    """Dialog shown when the application is locked."""
    
    __gtype_name__ = "LockDialog"
    
    # Template widgets
    password_entry = Gtk.Template.Child()
    error_label = Gtk.Template.Child()
    lockout_label = Gtk.Template.Child()
    unlock_button = Gtk.Template.Child()
    
    def __init__(self, parent_window, security_manager, **kwargs):
        super().__init__(**kwargs)
        
        self.set_transient_for(parent_window)
        
        self.security_manager = security_manager
        self._setup_dialog_behavior()
        
        # Update lockout status periodically
        self._update_lockout_status()
        self._lockout_update_id = GLib.timeout_add_seconds(1, self._update_lockout_status)
        
    def _setup_dialog_behavior(self):
        """Set up dialog behavior and keyboard shortcuts."""
        # Set up keyboard navigation
        DialogManager.setup_dialog_keyboard_navigation(self)
        
        # Center dialog on parent
        DialogManager.center_dialog_on_parent(self)
        
        # Focus password entry
        self.password_entry.grab_focus()
        
        # Handle window close attempts
        self.connect("close-request", self._on_close_request)
        
    @Gtk.Template.Callback()
    def _on_unlock_clicked(self, widget=None):
        """Handle unlock button click."""
        if self.security_manager.is_in_lockout():
            self._show_lockout_error()
            return
            
        password = self.password_entry.get_text()
        
        if not password:
            self._show_error(_("Please enter your master password"))
            return
            
        # Attempt to unlock
        success = self.security_manager.unlock_application(password)
        
        if success:
            # Clear password and close dialog
            self.password_entry.set_text("")
            self._cleanup()
            self.close()
        else:
            # Show error and clear password
            self.password_entry.set_text("")
            
            if self.security_manager.is_in_lockout():
                self._show_lockout_error()
            else:
                attempts_left = (self.security_manager.config_manager.get_config().security.max_failed_unlock_attempts - 
                               self.security_manager._failed_unlock_attempts)
                if attempts_left > 0:
                    self._show_error(_("Incorrect password. {} attempts remaining.").format(attempts_left))
                else:
                    self._show_error(_("Too many failed attempts"))
                    
    @Gtk.Template.Callback()
    def _on_quit_clicked(self, widget):
        """Handle quit button click."""
        # Show confirmation dialog
        dialog = Adw.AlertDialog()
        dialog.set_heading(_("Quit Application?"))
        dialog.set_body(_("Are you sure you want to quit? Any unsaved changes will be lost."))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("quit", _("Quit"))
        dialog.set_response_appearance("quit", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        dialog.connect("response", self._on_quit_confirmed)
        dialog.present(self)
        
    def _on_quit_confirmed(self, dialog, response):
        """Handle quit confirmation."""
        if response == "quit":
            # Get the application and quit
            app = self.get_application()
            if app:
                app.quit()
            else:
                # Fallback: exit the process
                import sys
                sys.exit(0)
                
    def _on_close_request(self, widget):
        """Handle window close request."""
        # Prevent closing without unlocking
        return True  # Block the close
        
    def _show_error(self, message: str):
        """Show error message."""
        self.error_label.set_text(message)
        self.error_label.set_visible(True)
        
        # Hide error after 5 seconds
        GLib.timeout_add_seconds(5, lambda: self.error_label.set_visible(False))
        
    def _show_lockout_error(self):
        """Show lockout error message."""
        remaining = self.security_manager.get_lockout_remaining_seconds()
        minutes = remaining // 60
        seconds = remaining % 60
        
        if minutes > 0:
            message = _("Too many failed attempts. Try again in {} minutes and {} seconds.").format(minutes, seconds)
        else:
            message = _("Too many failed attempts. Try again in {} seconds.").format(seconds)
            
        self._show_error(message)
        
    def _update_lockout_status(self) -> bool:
        """Update lockout status display."""
        if self.security_manager.is_in_lockout():
            remaining = self.security_manager.get_lockout_remaining_seconds()
            minutes = remaining // 60
            seconds = remaining % 60
            
            if minutes > 0:
                text = _("Locked out for {} minutes and {} seconds").format(minutes, seconds)
            else:
                text = _("Locked out for {} seconds").format(seconds)
                
            self.lockout_label.set_text(text)
            self.lockout_label.set_visible(True)
            self.unlock_button.set_sensitive(False)
            self.password_entry.set_sensitive(False)
        else:
            self.lockout_label.set_visible(False)
            self.unlock_button.set_sensitive(True)
            self.password_entry.set_sensitive(True)
            
        return True  # Continue updating
        
    def _cleanup(self):
        """Cleanup resources."""
        if hasattr(self, '_lockout_update_id') and self._lockout_update_id:
            GLib.source_remove(self._lockout_update_id)
            self._lockout_update_id = None