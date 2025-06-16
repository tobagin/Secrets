"""
Password Details Controller - Manages the password details panel.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
import os
from typing import Optional

from ..managers import ToastManager, ClipboardManager
from ..models import PasswordEntry
from ..commands import CommandInvoker


class PasswordDetailsController:
    """Controls the password details panel and related operations."""
    
    def __init__(self,
                 password_store,
                 toast_manager: ToastManager,
                 clipboard_manager: ClipboardManager,
                 command_invoker: CommandInvoker,
                 app_state,
                 config_manager,
                 # UI elements
                 details_stack: Adw.ViewStack,
                 placeholder_page: Adw.StatusPage,
                 details_page_box: Gtk.Box,
                 path_row: Adw.ActionRow,
                 password_expander_row: Adw.ExpanderRow,
                 password_display_label: Gtk.Label,
                 show_hide_password_button: Gtk.ToggleButton,
                 copy_password_button_in_row: Gtk.Button,
                 username_row: Adw.ActionRow,
                 copy_username_button: Gtk.Button,
                 url_row: Adw.ActionRow,
                 open_url_button: Gtk.Button,
                 totp_row: Adw.ExpanderRow,
                 totp_code_label: Gtk.Label,
                 totp_timer_bar: Gtk.ProgressBar,
                 copy_totp_button: Gtk.Button,
                 recovery_codes_group: Adw.PreferencesGroup,
                 recovery_expander: Adw.ExpanderRow,
                 recovery_codes_box: Gtk.Box,
                 notes_display_label: Gtk.Label,
                 edit_button: Gtk.Button,
                 remove_button: Gtk.Button):
        
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.clipboard_manager = clipboard_manager
        self.command_invoker = command_invoker
        self.app_state = app_state
        self.config_manager = config_manager
        
        # UI elements
        self.details_stack = details_stack
        self.placeholder_page = placeholder_page
        self.details_page_box = details_page_box
        self.path_row = path_row
        self.password_expander_row = password_expander_row
        self.password_display_label = password_display_label
        self.show_hide_password_button = show_hide_password_button
        self.copy_password_button_in_row = copy_password_button_in_row
        self.username_row = username_row
        self.copy_username_button = copy_username_button
        self.url_row = url_row
        self.open_url_button = open_url_button
        self.totp_row = totp_row
        self.totp_code_label = totp_code_label
        self.totp_timer_bar = totp_timer_bar
        self.copy_totp_button = copy_totp_button
        self.recovery_codes_group = recovery_codes_group
        self.recovery_expander = recovery_expander
        self.recovery_codes_box = recovery_codes_box
        self.notes_display_label = notes_display_label
        self.edit_button = edit_button
        self.remove_button = remove_button
        
        # State
        self._password_visible = False
        self._current_password = None
        self._current_item = None
        self._current_totp_secret = None
        self._totp_timer_id = None
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.copy_password_button_in_row.connect("clicked", self._on_copy_password_clicked)
        self.show_hide_password_button.connect("toggled", self._on_show_hide_password_toggled)
        self.copy_username_button.connect("clicked", self._on_copy_username_clicked)
        self.open_url_button.connect("clicked", self._on_open_url_clicked)
        self.copy_totp_button.connect("clicked", self._on_copy_totp_clicked)
    
    def update_details(self, selected_item):
        """Update the details panel with the selected item."""
        self._current_item = selected_item

        if selected_item:
            # Handle both PasswordEntry and PasswordListItem objects
            if hasattr(selected_item, 'full_path'):
                full_path = selected_item.full_path
            else:
                full_path = selected_item.path
            is_folder = selected_item.is_folder

            self.details_stack.set_visible_child_name("details")

            if is_folder:
                self._display_folder_details(full_path)
            else:
                self._display_password_details(full_path)
        else:
            self._clear_details()
    
    def _display_folder_details(self, full_path):
        """Display details for a folder."""
        self.path_row.set_subtitle(full_path)
        self.password_expander_row.set_subtitle("N/A for folders")
        self._current_password = None
        self._update_password_display(False)
        self.username_row.set_subtitle("N/A for folders")
        self.url_row.set_subtitle("N/A for folders")
        self.notes_display_label.set_text("")
        
        # Update button sensitivity
        self.copy_password_button_in_row.set_sensitive(False)
        self.show_hide_password_button.set_sensitive(False)
        self.copy_username_button.set_sensitive(False)
        self.open_url_button.set_sensitive(False)
        self.edit_button.set_sensitive(False)  # Cannot edit a folder's "content"
        self.remove_button.set_sensitive(True)  # Allow deleting empty folders
    
    def _display_password_details(self, full_path):
        """Display details for a password entry."""
        # Get raw content and parse it ourselves for TOTP/recovery codes support
        success, content = self.password_store.get_password_content(full_path)

        if not success:
            self._display_error_details(full_path, content)
        else:
            # Parse content with enhanced parsing
            details = self._parse_password_content(content)
            details['full_content'] = content
            self._display_valid_password_details(full_path, details)
    
    def _display_error_details(self, full_path, error):
        """Display details when there's an error loading the password."""
        self.toast_manager.show_error(f"Error loading details: {error}")
        self.path_row.set_subtitle(full_path)
        self.password_expander_row.set_subtitle("Error")
        self._current_password = None
        self._update_password_display(False)
        self.username_row.set_subtitle("Error")
        self.url_row.set_subtitle("Error")
        self.notes_display_label.set_text("Error loading details.")
        
        # Update button sensitivity
        self.copy_password_button_in_row.set_sensitive(False)
        self.show_hide_password_button.set_sensitive(False)
        self.copy_username_button.set_sensitive(False)
        self.open_url_button.set_sensitive(False)
        # Allow edit/delete even if content parsing fails, as path is known
        self.edit_button.set_sensitive(True)
        self.remove_button.set_sensitive(True)
    
    def _display_valid_password_details(self, full_path, details):
        """Display details for a valid password entry."""
        self.path_row.set_subtitle(full_path)
        self._current_password = details.get('password')
        self._update_password_display(False)  # Init with password hidden

        username = details.get('username')
        self.username_row.set_subtitle(username if username else "Not set")
        self.username_row.set_visible(bool(username))
        self.copy_username_button.set_sensitive(bool(username))

        url = details.get('url')
        self.url_row.set_subtitle(url if url else "Not set")
        self.url_row.set_visible(bool(url))
        self.open_url_button.set_sensitive(bool(url))

        # Handle TOTP
        totp = details.get('totp')
        if totp:
            self._current_totp_secret = totp.strip()  # Remove leading/trailing whitespace
            self._totp_error_shown = False  # Reset error flag for new secret
            self.totp_row.set_visible(True)
            self.totp_row.set_enable_expansion(True)
            self.copy_totp_button.set_sensitive(True)
            self._start_totp_timer()
        else:
            self._current_totp_secret = None
            self.totp_row.set_visible(False)
            self.copy_totp_button.set_sensitive(False)
            self._stop_totp_timer()

        # Handle recovery codes
        recovery_codes = details.get('recovery_codes', [])
        if recovery_codes:
            self._display_recovery_codes(recovery_codes)
            self.recovery_codes_group.set_visible(True)
        else:
            self.recovery_codes_group.set_visible(False)

        notes_text = details.get('notes') if details.get('notes') else ""
        # Truncate very long notes to prevent GTK measurement warnings
        if len(notes_text) > 30:  # Extremely aggressive truncation
            notes_text = notes_text[:27] + "..."
        self.notes_display_label.set_text(notes_text)

        # Update button sensitivity
        self.copy_password_button_in_row.set_sensitive(bool(self._current_password))
        self.show_hide_password_button.set_sensitive(bool(self._current_password))
        self.edit_button.set_sensitive(True)
        self.remove_button.set_sensitive(True)
    
    def _clear_details(self):
        """Clear the details panel."""
        self.details_stack.set_visible_child_name("placeholder")
        self._current_password = None
        self._current_item = None

        # Clear all detail fields
        self.path_row.set_subtitle("")
        self._update_password_display(False)
        self.username_row.set_subtitle("")
        self.username_row.set_visible(False)
        self.url_row.set_subtitle("")
        self.url_row.set_visible(False)
        self.totp_row.set_visible(False)
        self._current_totp_secret = None
        self._stop_totp_timer()
        self.recovery_codes_group.set_visible(False)
        self._clear_recovery_codes()
        self.notes_display_label.set_text("")

        # Disable action buttons
        self.copy_password_button_in_row.set_sensitive(False)
        self.show_hide_password_button.set_sensitive(False)
        self.copy_username_button.set_sensitive(False)
        self.open_url_button.set_sensitive(False)
        self.copy_totp_button.set_sensitive(False)
        self.edit_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)
    
    def _update_password_display(self, show_password):
        """Update the password display based on visibility state."""
        self._password_visible = show_password
        
        if self._current_password and show_password:
            # Truncate very long passwords for display to prevent GTK measurement warnings
            display_password = self._current_password
            if len(display_password) > 10:  # Extremely aggressive truncation
                display_password = display_password[:7] + "..."
            self.password_display_label.set_text(display_password)
            self.password_expander_row.set_subtitle("Visible")
        else:
            if self._current_password:
                self.password_display_label.set_text("●●●●●●●●")
                self.password_expander_row.set_subtitle("Hidden")
            else:
                self.password_display_label.set_text("None")
            

        
        # Update button icon to match state
        icon_name = "eye-open-negative-filled-symbolic" if show_password else "eye-not-looking-symbolic"
        self.show_hide_password_button.set_icon_name(icon_name)
    
    def _on_show_hide_password_toggled(self, toggle_button):
        """Handle password visibility toggle."""
        show_password = toggle_button.get_active()
        self._update_password_display(show_password)
        
        # Auto-hide password after configured timeout if visible
        if show_password:
            config = self.config_manager.get_config()
            timeout = config.security.auto_hide_timeout_seconds
            GLib.timeout_add_seconds(timeout, self._auto_hide_password)
    
    def _auto_hide_password(self):
        """Automatically hide password after timeout if still visible."""
        if self._password_visible:
            self.show_hide_password_button.set_active(False)
            self._update_password_display(False)
            self.toast_manager.show_info("Password automatically hidden")
        return False  # Don't repeat the timeout
    
    def _on_copy_password_clicked(self, widget):
        """Handle copy password button click using command pattern."""
        if self._current_item and not self._current_item.is_folder:
            # Handle both PasswordEntry and PasswordListItem objects
            if hasattr(self._current_item, 'full_path'):
                path = self._current_item.full_path
            else:
                path = self._current_item.path

            # Create a PasswordEntry from the current selection
            entry = PasswordEntry(
                path=path,
                password=self._current_password,
                is_folder=False
            )
            self.app_state.set_selected_entry(entry)

            # Execute the copy command
            self.command_invoker.execute_command("copy_password")
        else:
            self.toast_manager.show_warning("No password selected to copy")
    
    def _on_copy_username_clicked(self, widget):
        """Handle copy username using command pattern."""
        if self._current_item and not self._current_item.is_folder:
            username = self.username_row.get_subtitle()

            # Handle both PasswordEntry and PasswordListItem objects
            if hasattr(self._current_item, 'full_path'):
                path = self._current_item.full_path
            else:
                path = self._current_item.path

            # Create a PasswordEntry with username
            entry = PasswordEntry(
                path=path,
                username=username if username not in ["Not set", "N/A for folders"] else None,
                is_folder=False
            )
            self.app_state.set_selected_entry(entry)

            # Execute the copy username command
            self.command_invoker.execute_command("copy_username")
        else:
            self.toast_manager.show_warning("No username to copy")
    
    def _on_open_url_clicked(self, widget):
        """Handle open URL using command pattern."""
        if self._current_item and not self._current_item.is_folder:
            url = self.url_row.get_subtitle()

            # Handle both PasswordEntry and PasswordListItem objects
            if hasattr(self._current_item, 'full_path'):
                path = self._current_item.full_path
            else:
                path = self._current_item.path

            # Create a PasswordEntry with URL
            entry = PasswordEntry(
                path=path,
                url=url if url not in ["Not set", "N/A for folders"] else None,
                is_folder=False
            )
            self.app_state.set_selected_entry(entry)

            # Execute the open URL command
            self.command_invoker.execute_command("open_url")
        else:
            self.toast_manager.show_warning("No valid URL to open")

    def _on_copy_totp_clicked(self, widget):
        """Handle copy TOTP button click."""
        if self._current_totp_secret:
            # Copy the currently displayed TOTP code
            current_code = self.totp_code_label.get_text().replace(' ', '')  # Remove space formatting
            if current_code and current_code.isdigit() and len(current_code) == 6:
                self.clipboard_manager.copy_text(current_code)
                self.toast_manager.show_success("TOTP code copied to clipboard")
            else:
                # Try to generate a fresh code if display is invalid
                try:
                    import pyotp
                    normalized_secret = self._normalize_totp_secret(self._current_totp_secret)
                    if normalized_secret:
                        totp = pyotp.TOTP(normalized_secret)
                        fresh_code = totp.now()
                        self.clipboard_manager.copy_text(fresh_code)
                        self.toast_manager.show_success("TOTP code copied to clipboard")
                    else:
                        self.toast_manager.show_warning("Invalid TOTP secret")
                except Exception as e:
                    self.toast_manager.show_error(f"Failed to generate TOTP code: {str(e)}")
        else:
            self.toast_manager.show_warning("No TOTP to copy")
    
    def toggle_password_visibility(self):
        """Toggle password visibility (for keyboard shortcuts)."""
        if self.show_hide_password_button.get_sensitive():
            current_state = self.show_hide_password_button.get_active()
            self.show_hide_password_button.set_active(not current_state)
    
    def get_current_item(self):
        """Get the currently displayed item."""
        return self._current_item

    def _parse_password_content(self, content):
        """Parse password content into structured fields."""
        lines = content.splitlines()
        parsed = {
            'password': '',
            'username': '',
            'url': '',
            'totp': '',
            'recovery_codes': [],
            'notes': ''
        }

        if not lines:
            return parsed

        # First line is always the password
        parsed['password'] = lines[0]

        # Process remaining lines
        remaining_lines = lines[1:]
        notes_lines = []
        in_recovery_section = False

        for line in remaining_lines:
            line_stripped = line.strip()

            if not line_stripped:
                if not in_recovery_section:
                    notes_lines.append('')
                continue

            # Check for recovery codes section
            if line_stripped.lower() in ['recovery codes:', 'recovery codes', 'backup codes:', 'backup codes']:
                in_recovery_section = True
                continue

            # If in recovery section, collect codes
            if in_recovery_section:
                # Look for codes (lines starting with -, *, or numbers)
                if line_stripped.startswith(('-', '*', '•')) or line_stripped[0].isdigit():
                    # Remove prefix and add to recovery codes
                    code = line_stripped.lstrip('-*•0123456789. ').strip()
                    if code:
                        parsed['recovery_codes'].append(code)
                    continue
                else:
                    # End of recovery section
                    in_recovery_section = False

            # Check for username patterns
            if line_stripped.lower().startswith(('username:', 'user:', 'login:')):
                if not parsed['username']:  # Take first username found
                    parsed['username'] = line_stripped.split(':', 1)[1].strip()
                continue

            # Check for TOTP patterns
            if line_stripped.lower().startswith('totp:'):
                if not parsed['totp']:  # Take first TOTP found
                    parsed['totp'] = line_stripped.split(':', 1)[1].strip()
                continue

            # Check for URL patterns (simple check)
            if line_stripped.startswith(('http://', 'https://', 'www.')):
                if not parsed['url']:  # Take first URL found
                    parsed['url'] = line_stripped
                continue

            # Everything else goes to notes (if not in recovery section)
            if not in_recovery_section:
                notes_lines.append(line_stripped)

        # Join notes, removing empty lines at start/end
        notes = '\n'.join(notes_lines).strip()
        parsed['notes'] = notes

        return parsed

    def _display_recovery_codes(self, recovery_codes):
        """Display recovery codes in the expander."""
        # Clear existing codes
        self._clear_recovery_codes()

        # Add new codes
        for code in recovery_codes:
            code_row = Adw.ActionRow()
            code_row.set_title(code)

            # Add copy button for each code
            copy_button = Gtk.Button()
            copy_button.set_icon_name("edit-copy-symbolic")
            copy_button.set_tooltip_text("Copy Recovery Code")
            copy_button.set_valign(Gtk.Align.CENTER)
            copy_button.add_css_class("flat")
            copy_button.connect("clicked", self._on_copy_recovery_code_clicked, code)

            code_row.add_suffix(copy_button)
            self.recovery_codes_box.append(code_row)

        # Enable expansion if codes are present
        self.recovery_expander.set_enable_expansion(len(recovery_codes) > 0)
        if recovery_codes:
            self.recovery_expander.set_subtitle(f"{len(recovery_codes)} backup codes")

    def _clear_recovery_codes(self):
        """Clear all recovery codes from the box."""
        # Remove all children from the recovery codes box
        child = self.recovery_codes_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.recovery_codes_box.remove(child)
            child = next_child

        # Disable expansion
        self.recovery_expander.set_enable_expansion(False)
        self.recovery_expander.set_subtitle("No backup codes")

    def _on_copy_recovery_code_clicked(self, button, code):
        """Handle copy recovery code button click."""
        self.clipboard_manager.copy_text(code)
        self.toast_manager.show_success("Recovery code copied to clipboard")

    def _validate_totp_secret(self, secret):
        """Validate TOTP secret without generating codes."""
        try:
            import pyotp
            normalized_secret = self._normalize_totp_secret(secret)
            if not normalized_secret:
                return False, "Empty or invalid secret format"

            # Try to create TOTP object (this validates the secret)
            totp = pyotp.TOTP(normalized_secret)
            # Try to generate a code to ensure it works
            totp.now()
            return True, "Valid"
        except ImportError:
            return False, "pyotp package required"
        except Exception as e:
            return False, str(e)

    def _start_totp_timer(self):
        """Start the TOTP timer and code generation."""
        if not self._current_totp_secret:
            return

        # Validate secret first
        is_valid, error_msg = self._validate_totp_secret(self._current_totp_secret)
        if not is_valid:
            # Show error in UI
            self.totp_code_label.set_text("Invalid")
            self.totp_timer_bar.set_fraction(0)
            self.totp_timer_bar.set_text("Error")
            self.toast_manager.show_error(f"TOTP validation failed: {error_msg}")
            return

        # Stop any existing timer
        self._stop_totp_timer()

        # Update immediately
        self._update_totp_display()

        # Start timer to update every second
        self._totp_timer_id = GLib.timeout_add(1000, self._update_totp_display)

    def _stop_totp_timer(self):
        """Stop the TOTP timer."""
        if self._totp_timer_id:
            GLib.source_remove(self._totp_timer_id)
            self._totp_timer_id = None

    def _normalize_totp_secret(self, secret):
        """Normalize TOTP secret to standard Base32 format."""
        if not secret:
            return None

        # Remove common separators and whitespace
        normalized = secret.upper().replace(' ', '').replace('-', '').replace('_', '')

        # Remove any non-Base32 characters (Base32 uses A-Z and 2-7)
        import re
        normalized = re.sub(r'[^A-Z2-7]', '', normalized)

        # Ensure proper padding (Base32 requires padding to multiple of 8)
        while len(normalized) % 8 != 0:
            normalized += '='

        return normalized if normalized else None

    def _update_totp_display(self):
        """Update the TOTP code and timer display."""
        if not self._current_totp_secret:
            return False  # Stop the timer

        try:
            import pyotp
            import time

            # Normalize the secret
            normalized_secret = self._normalize_totp_secret(self._current_totp_secret)
            if not normalized_secret:
                raise ValueError("Invalid TOTP secret format")

            # Generate current TOTP code
            totp = pyotp.TOTP(normalized_secret)
            current_code = totp.now()

            # Format code with space in middle (123 456)
            formatted_code = f"{current_code[:3]} {current_code[3:]}"
            self.totp_code_label.set_text(formatted_code)

            # Calculate time remaining in current 30-second window
            current_time = int(time.time())
            time_remaining = 30 - (current_time % 30)
            progress = time_remaining / 30.0

            # Update progress bar
            self.totp_timer_bar.set_fraction(progress)
            self.totp_timer_bar.set_text(f"{time_remaining}s")

            # Change color when time is running out
            if time_remaining <= 3:
                self.totp_timer_bar.add_css_class("error")
                self.totp_timer_bar.remove_css_class("warning")
            elif time_remaining <= 10:
                self.totp_timer_bar.add_css_class("warning")
                self.totp_timer_bar.remove_css_class("error")
            else:
                self.totp_timer_bar.remove_css_class("error")
                self.totp_timer_bar.remove_css_class("warning")

            return True  # Continue the timer

        except ImportError:
            self.totp_code_label.set_text("pyotp required")
            self.totp_timer_bar.set_fraction(0)
            self.totp_timer_bar.set_text("Missing pyotp")
            self.toast_manager.show_error("TOTP requires 'pyotp' package. Install with: pip install pyotp")
            return False  # Stop the timer
        except Exception as e:
            # More detailed error information
            error_msg = str(e)
            if "Incorrect padding" in error_msg:
                display_error = "Invalid format"
                toast_error = f"TOTP secret has invalid format. Please check the secret: {error_msg}"
            elif "Invalid base32" in error_msg.lower():
                display_error = "Invalid Base32"
                toast_error = f"TOTP secret contains invalid characters. Use only A-Z and 2-7: {error_msg}"
            else:
                display_error = "Invalid secret"
                toast_error = f"TOTP error: {error_msg}"

            self.totp_code_label.set_text(display_error)
            self.totp_timer_bar.set_fraction(0)
            self.totp_timer_bar.set_text("Error")

            # Show detailed error only once to avoid spam
            if not hasattr(self, '_totp_error_shown'):
                self.toast_manager.show_error(toast_error)
                self._totp_error_shown = True

            return False  # Stop the timer
