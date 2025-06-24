"""
Header bar component for the main window.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...app_info import APP_ID


class HeaderBarComponent(GObject.Object):
    """
    Component that manages the header bar functionality.
    """
    
    def __init__(self, header_bar, buttons_dict, menu_button):
        """
        Initialize the header bar component.
        
        Args:
            header_bar: The AdwHeaderBar widget
            buttons_dict: Dictionary of button widgets
            menu_button: The main menu button
        """
        super().__init__()
        self.header_bar = header_bar
        self.buttons = buttons_dict
        self.menu_button = menu_button
        
        # Store button references for easy access
        self.add_password_button = buttons_dict.get('add_password_button')
        self.git_pull_button = buttons_dict.get('git_pull_button')
        self.git_push_button = buttons_dict.get('git_push_button')
        
    def connect_signals(self, signal_handlers):
        """
        Connect signals to their handlers.
        
        Args:
            signal_handlers: Dictionary mapping signal names to handler functions
        """
        if self.add_password_button and 'add_password' in signal_handlers:
            self.add_password_button.connect("clicked", signal_handlers['add_password'])
            
        if self.git_pull_button and 'git_pull' in signal_handlers:
            self.git_pull_button.connect("clicked", signal_handlers['git_pull'])
            
        if self.git_push_button and 'git_push' in signal_handlers:
            self.git_push_button.connect("clicked", signal_handlers['git_push'])
    
    def set_button_sensitivity(self, button_name, sensitive):
        """
        Set the sensitivity of a specific button.
        
        Args:
            button_name: Name of the button
            sensitive: Whether the button should be sensitive
        """
        button = self.buttons.get(button_name)
        if button:
            button.set_sensitive(sensitive)
    
    def set_git_buttons_sensitivity(self, sensitive):
        """
        Set the sensitivity of git-related buttons.
        
        Args:
            sensitive: Whether the buttons should be sensitive
        """
        self.set_button_sensitivity('git_pull_button', sensitive)
        self.set_button_sensitivity('git_push_button', sensitive)
    
    def update_title(self, title, subtitle=None):
        """
        Update the header bar title.
        
        Args:
            title: Main title text
            subtitle: Optional subtitle text
        """
        title_widget = self.header_bar.get_title_widget()
        if isinstance(title_widget, Adw.WindowTitle):
            title_widget.set_title(title)
            if subtitle:
                title_widget.set_subtitle(subtitle)
