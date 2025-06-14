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
                 notes_display_label: Gtk.Label,
                 edit_button: Gtk.Button,
                 remove_button: Gtk.Button,
                 move_rename_button: Gtk.Button):
        
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
        self.notes_display_label = notes_display_label
        self.edit_button = edit_button
        self.remove_button = remove_button
        self.move_rename_button = move_rename_button
        
        # State
        self._password_visible = False
        self._current_password = None
        self._current_item = None
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.copy_password_button_in_row.connect("clicked", self._on_copy_password_clicked)
        self.show_hide_password_button.connect("toggled", self._on_show_hide_password_toggled)
        self.copy_username_button.connect("clicked", self._on_copy_username_clicked)
        self.open_url_button.connect("clicked", self._on_open_url_clicked)
    
    def update_details(self, selected_item):
        """Update the details panel with the selected item."""
        self._current_item = selected_item
        
        if selected_item:
            full_path = selected_item.full_path
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
        self.move_rename_button.set_sensitive(True)
    
    def _display_password_details(self, full_path):
        """Display details for a password entry."""
        details = self.password_store.get_parsed_password_details(full_path)
        
        if 'error' in details:
            self._display_error_details(full_path, details['error'])
        else:
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
        # Allow edit/delete/move even if content parsing fails, as path is known
        self.edit_button.set_sensitive(True)
        self.remove_button.set_sensitive(True)
        self.move_rename_button.set_sensitive(True)
    
    def _display_valid_password_details(self, full_path, details):
        """Display details for a valid password entry."""
        self.path_row.set_subtitle(full_path)
        self._current_password = details.get('password')
        self._update_password_display(False)  # Init with password hidden
        
        username = details.get('username')
        self.username_row.set_subtitle(username if username else "Not set")
        self.copy_username_button.set_sensitive(bool(username))
        
        url = details.get('url')
        self.url_row.set_subtitle(url if url else "Not set")
        self.open_url_button.set_sensitive(bool(url))
        
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
        self.move_rename_button.set_sensitive(True)
    
    def _clear_details(self):
        """Clear the details panel."""
        self.details_stack.set_visible_child_name("placeholder")
        self._current_password = None
        self._current_item = None
        
        # Clear all detail fields
        self.path_row.set_subtitle("")
        self._update_password_display(False)
        self.username_row.set_subtitle("")
        self.url_row.set_subtitle("")
        self.notes_display_label.set_text("")
        
        # Disable action buttons
        self.copy_password_button_in_row.set_sensitive(False)
        self.show_hide_password_button.set_sensitive(False)
        self.copy_username_button.set_sensitive(False)
        self.open_url_button.set_sensitive(False)
        self.edit_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)
        self.move_rename_button.set_sensitive(False)
    
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
            # Add a CSS class to highlight that password is visible
            self.password_expander_row.add_css_class("password-visible")
        else:
            if self._current_password:
                self.password_display_label.set_text("●●●●●●●●")
                self.password_expander_row.set_subtitle("Hidden")
            else:
                self.password_display_label.set_text("None")
            
            # Remove the highlight class
            self.password_expander_row.remove_css_class("password-visible")
        
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
            # Create a PasswordEntry from the current selection
            entry = PasswordEntry(
                path=self._current_item.full_path,
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
            
            # Create a PasswordEntry with username
            entry = PasswordEntry(
                path=self._current_item.full_path,
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
            
            # Create a PasswordEntry with URL
            entry = PasswordEntry(
                path=self._current_item.full_path,
                url=url if url not in ["Not set", "N/A for folders"] else None,
                is_folder=False
            )
            self.app_state.set_selected_entry(entry)
            
            # Execute the open URL command
            self.command_invoker.execute_command("open_url")
        else:
            self.toast_manager.show_warning("No valid URL to open")
    
    def toggle_password_visibility(self):
        """Toggle password visibility (for keyboard shortcuts)."""
        if self.show_hide_password_button.get_sensitive():
            current_state = self.show_hide_password_button.get_active()
            self.show_hide_password_button.set_active(not current_state)
    
    def get_current_item(self):
        """Get the currently displayed item."""
        return self._current_item
