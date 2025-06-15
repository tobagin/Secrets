"""
Password details component for the main window.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...app_info import APP_ID


class PasswordDetailsComponent(GObject.Object):
    """
    Component that manages the password details display.
    """
    
    def __init__(self, details_stack, placeholder_page, details_page_box, 
                 path_row, password_expander_row, password_display_label,
                 show_hide_button, copy_password_button, username_row,
                 copy_username_button, url_row, open_url_button,
                 notes_display_label, action_buttons):
        """
        Initialize the password details component.
        
        Args:
            details_stack: The main stack widget
            placeholder_page: The placeholder page
            details_page_box: The details page container
            path_row: The path display row
            password_expander_row: The password expander row
            password_display_label: The password display label
            show_hide_button: The show/hide password button
            copy_password_button: The copy password button
            username_row: The username display row
            copy_username_button: The copy username button
            url_row: The URL display row
            open_url_button: The open URL button
            notes_display_label: The notes display label
            action_buttons: Dictionary of action buttons
        """
        super().__init__()
        self.details_stack = details_stack
        self.placeholder_page = placeholder_page
        self.details_page_box = details_page_box
        self.path_row = path_row
        self.password_expander_row = password_expander_row
        self.password_display_label = password_display_label
        self.show_hide_button = show_hide_button
        self.copy_password_button = copy_password_button
        self.username_row = username_row
        self.copy_username_button = copy_username_button
        self.url_row = url_row
        self.open_url_button = open_url_button
        self.notes_display_label = notes_display_label
        self.action_buttons = action_buttons
        
        # State tracking
        self.password_visible = False
        self.current_password = ""
        
    def connect_signals(self, signal_handlers):
        """
        Connect signals to their handlers.
        
        Args:
            signal_handlers: Dictionary mapping signal names to handler functions
        """
        if self.show_hide_button and 'toggle_password' in signal_handlers:
            self.show_hide_button.connect("toggled", signal_handlers['toggle_password'])
            
        if self.copy_password_button and 'copy_password' in signal_handlers:
            self.copy_password_button.connect("clicked", signal_handlers['copy_password'])
            
        if self.copy_username_button and 'copy_username' in signal_handlers:
            self.copy_username_button.connect("clicked", signal_handlers['copy_username'])
            
        if self.open_url_button and 'open_url' in signal_handlers:
            self.open_url_button.connect("clicked", signal_handlers['open_url'])
            
        # Connect action button signals
        for button_name, handler_name in [
            ('edit_button', 'edit_password'),
            ('move_rename_button', 'move_rename_password'),
            ('remove_button', 'remove_password')
        ]:
            button = self.action_buttons.get(button_name)
            if button and handler_name in signal_handlers:
                button.connect("clicked", signal_handlers[handler_name])
    
    def show_placeholder(self):
        """Show the placeholder page."""
        self.details_stack.set_visible_child_name("placeholder")
        self._set_action_buttons_sensitivity(False)
    
    def show_details(self):
        """Show the details page."""
        self.details_stack.set_visible_child_name("details")
        self._set_action_buttons_sensitivity(True)
    
    def update_path(self, path):
        """
        Update the path display.
        
        Args:
            path: The password path
        """
        if self.path_row:
            self.path_row.set_subtitle(path or "")
    
    def update_password(self, password, visible=False):
        """
        Update the password display.
        
        Args:
            password: The password text
            visible: Whether to show the password
        """
        self.current_password = password or ""
        self.password_visible = visible
        
        if self.password_display_label:
            if visible and password:
                self.password_display_label.set_text(password)
            else:
                self.password_display_label.set_text("●●●●●●●●")
        
        if self.show_hide_button:
            self.show_hide_button.set_active(visible)
            icon_name = "view-conceal-symbolic" if visible else "view-reveal-symbolic"
            self.show_hide_button.set_icon_name(icon_name)
    
    def toggle_password_visibility(self):
        """Toggle password visibility."""
        self.update_password(self.current_password, not self.password_visible)
    
    def update_username(self, username):
        """
        Update the username display.
        
        Args:
            username: The username text
        """
        if self.username_row:
            self.username_row.set_subtitle(username or "")
            self.username_row.set_visible(bool(username))
    
    def update_url(self, url):
        """
        Update the URL display.
        
        Args:
            url: The URL text
        """
        if self.url_row:
            self.url_row.set_subtitle(url or "")
            self.url_row.set_visible(bool(url))
    
    def update_notes(self, notes):
        """
        Update the notes display.
        
        Args:
            notes: The notes text
        """
        if self.notes_display_label:
            self.notes_display_label.set_text(notes or "")
            # Show/hide the notes section based on content
            notes_group = self.notes_display_label.get_parent()
            while notes_group and not isinstance(notes_group, Adw.PreferencesGroup):
                notes_group = notes_group.get_parent()
            if notes_group:
                notes_group.set_visible(bool(notes))
    
    def _set_action_buttons_sensitivity(self, sensitive):
        """
        Set the sensitivity of action buttons.
        
        Args:
            sensitive: Whether buttons should be sensitive
        """
        for button in self.action_buttons.values():
            if button:
                button.set_sensitive(sensitive)
    
    def clear_details(self):
        """Clear all details and show placeholder."""
        self.update_path("")
        self.update_password("", False)
        self.update_username("")
        self.update_url("")
        self.update_notes("")
        self.show_placeholder()
