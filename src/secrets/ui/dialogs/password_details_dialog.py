"""Password details dialog for viewing password information."""

from gi.repository import Gtk, Adw, GObject, GLib
from typing import Optional
import logging

from ...models import PasswordEntry
from ...managers.clipboard_manager import ClipboardManager
from ...managers.toast_manager import ToastManager


@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/dialogs/password_details_dialog.ui')
class PasswordDetailsDialog(Adw.Dialog):
    """Dialog for viewing password details."""
    
    __gtype_name__ = 'PasswordDetailsDialog'
    
    # UI elements
    details_title = Gtk.Template.Child()
    
    # Password details
    password_entry_row = Gtk.Template.Child()
    copy_password_button = Gtk.Template.Child()
    
    username_row = Gtk.Template.Child()
    copy_username_button = Gtk.Template.Child()
    
    url_row = Gtk.Template.Child()
    open_url_button = Gtk.Template.Child()
    
    totp_group = Gtk.Template.Child()
    totp_row = Gtk.Template.Child()
    totp_code_label = Gtk.Template.Child()
    totp_timer_bar = Gtk.Template.Child()
    copy_totp_button = Gtk.Template.Child()
    
    recovery_codes_group = Gtk.Template.Child()
    recovery_expander = Gtk.Template.Child()
    recovery_codes_box = Gtk.Template.Child()
    
    notes_group = Gtk.Template.Child()
    notes_scrolled_window = Gtk.Template.Child()
    notes_display_label = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'edit-password': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'remove-password': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'visit-url': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, password_entry: PasswordEntry, **kwargs):
        super().__init__(**kwargs)
        
        self._password_entry = password_entry
        self._password_visible = False
        self._totp_timer_id = None
        self._clipboard_manager = None  # Set externally
        self._toast_manager = None  # Set externally
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the dialog UI with password entry data."""
        # Set title and subtitle
        if self.details_title:
            self.details_title.set_title("Password Details")
            self.details_title.set_subtitle(self._password_entry.name)
        
        # Set password
        if self._password_entry.password:
            self.password_entry_row.set_text(self._password_entry.password)
        
        # Set username - always show the row
        if self._password_entry.username:
            self.username_row.set_subtitle(self._password_entry.username)
        else:
            self.username_row.set_subtitle("(no username)")
        self.username_row.set_visible(True)
            
        # Set URL - always show the row
        if self._password_entry.url:
            self.url_row.set_subtitle(self._password_entry.url)
        else:
            self.url_row.set_subtitle("(no URL)")
        self.url_row.set_visible(True)
            
        # Set TOTP - show group if available
        if self._password_entry.totp:
            self._update_totp()
            self.totp_group.set_visible(True)
        else:
            self.totp_group.set_visible(False)
            
        # Set recovery codes - show if available
        if self._password_entry.recovery_codes:
            self._setup_recovery_codes()
            self.recovery_codes_group.set_visible(True)
        else:
            self.recovery_codes_group.set_visible(False)
            
        # Set notes - always show the group
        if self._password_entry.notes:
            self.notes_display_label.set_text(self._password_entry.notes)
        else:
            self.notes_display_label.set_text("(no notes)")
        self.notes_group.set_visible(True)
            
    def _update_totp(self):
        """Update TOTP display and progress with color changes."""
        if not self._password_entry.totp:
            return
            
        try:
            import pyotp
            import re
            
            # Normalize the TOTP secret (remove spaces, make uppercase)
            normalized_secret = re.sub(r'[^A-Z2-7]', '', self._password_entry.totp.upper())
            
            totp = pyotp.TOTP(normalized_secret)
            current_code = totp.now()
            
            # Format code as "000 000" and set as text
            formatted_code = f"{current_code[:3]} {current_code[3:]}"
            self.totp_code_label.set_text(formatted_code)
            
            # Update progress bar with color changes
            import time
            current_time = int(time.time())
            time_remaining = 30 - (current_time % 30)
            progress = time_remaining / 30.0
            
            self.totp_timer_bar.set_fraction(progress)
            self.totp_timer_bar.set_text(f"{time_remaining}s")
            
            # Change color based on time remaining using GTK style classes
            self.totp_timer_bar.remove_css_class("success")
            self.totp_timer_bar.remove_css_class("warning")
            self.totp_timer_bar.remove_css_class("error")
            
            if time_remaining <= 3:
                self.totp_timer_bar.add_css_class("error")      # Red
            elif time_remaining <= 10:
                self.totp_timer_bar.add_css_class("warning")    # Yellow
            else:
                self.totp_timer_bar.add_css_class("success")    # Blue/Green
            
            # Schedule next update
            if self._totp_timer_id:
                GLib.source_remove(self._totp_timer_id)
            self._totp_timer_id = GLib.timeout_add(1000, self._update_totp)
            
        except Exception as e:
            logging.error(f"Error updating TOTP: {e}")
            self.totp_timer_bar.set_text("Error")
            
    def _setup_recovery_codes(self):
        """Set up recovery codes display."""
        # Clear existing codes
        child = self.recovery_codes_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.recovery_codes_box.remove(child)
            child = next_child
            
        # Add recovery codes
        for code in self._password_entry.recovery_codes:
            code_row = Adw.ActionRow()
            code_row.set_title(code)
            
            # Add copy button
            copy_btn = Gtk.Button()
            copy_btn.set_icon_name("edit-copy-symbolic")
            copy_btn.set_tooltip_text("Copy Recovery Code")
            copy_btn.set_valign(Gtk.Align.CENTER)
            copy_btn.add_css_class("flat")
            copy_btn.connect("clicked", lambda btn, c=code: self._copy_recovery_code(c))
            
            code_row.add_suffix(copy_btn)
            self.recovery_codes_box.append(code_row)
            
    def _copy_recovery_code(self, code: str):
        """Copy a recovery code to clipboard."""
        if self._clipboard_manager:
            self._clipboard_manager.copy_text(code, "Recovery code")
            
    def _connect_signals(self):
        """Connect widget signals."""
        self.copy_password_button.connect("clicked", self._on_copy_password)
        self.copy_username_button.connect("clicked", self._on_copy_username)
        self.open_url_button.connect("clicked", self._on_open_url)
        self.copy_totp_button.connect("clicked", self._on_copy_totp)
        
    def _on_copy_password(self, button):
        """Handle copy password button click."""
        if self._password_entry.password and self._clipboard_manager:
            self._clipboard_manager.copy_text(self._password_entry.password, "Password")
                
    def _on_copy_username(self, button):
        """Handle copy username button click."""
        if self._password_entry.username and self._clipboard_manager:
            self._clipboard_manager.copy_text(self._password_entry.username, "Username")
                
    def _on_open_url(self, button):
        """Handle open URL button click."""
        if self._password_entry.url:
            self.emit("visit-url", self._password_entry.url)
            
    def _on_copy_totp(self, button):
        """Handle copy TOTP button click."""
        if self._password_entry.totp:
            try:
                import pyotp
                import re
                
                # Normalize the TOTP secret (remove spaces, make uppercase)
                normalized_secret = re.sub(r'[^A-Z2-7]', '', self._password_entry.totp.upper())
                
                totp = pyotp.TOTP(normalized_secret)
                current_code = totp.now()
                if self._clipboard_manager:
                    self._clipboard_manager.copy_text(current_code, "TOTP code")
            except Exception as e:
                logging.error(f"Error copying TOTP: {e}")
                if self._toast_manager:
                    self._toast_manager.show_error("Error copying TOTP code")
                    
    def set_toast_manager(self, toast_manager: ToastManager):
        """Set the toast manager for showing notifications."""
        self._toast_manager = toast_manager
    
    def set_clipboard_manager(self, clipboard_manager):
        """Set the clipboard manager for copy operations."""
        self._clipboard_manager = clipboard_manager
        
    def cleanup(self):
        """Clean up resources."""
        if self._totp_timer_id:
            GLib.source_remove(self._totp_timer_id)
            self._totp_timer_id = None