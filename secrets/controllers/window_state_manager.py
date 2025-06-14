"""
Window State Manager - Manages window state, theme, and configuration.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from ..config import ConfigManager


class WindowStateManager:
    """Manages window state persistence and theme application."""
    
    def __init__(self, window: Adw.Window, config_manager: ConfigManager):
        self.window = window
        self.config_manager = config_manager
        
        # Apply initial settings
        self._apply_initial_settings()
        
        # Connect to window state change signals
        self._connect_signals()
    
    def _apply_initial_settings(self):
        """Apply initial settings from configuration."""
        from ..config import ThemeManager

        config = self.config_manager.get_config()

        # Apply theme
        theme_manager = ThemeManager(self.config_manager)
        theme_manager.apply_theme()

        # Apply window state if remember_window_state is enabled
        if config.ui.remember_window_state:
            self.window.set_default_size(config.ui.window_width, config.ui.window_height)
            if config.ui.window_maximized:
                self.window.maximize()
    
    def _connect_signals(self):
        """Connect to window state change signals to save state."""
        self.window.connect("notify::default-width", self._on_window_state_changed)
        self.window.connect("notify::default-height", self._on_window_state_changed)
        self.window.connect("notify::maximized", self._on_window_state_changed)
        self.window.connect("close-request", self._on_close_request)
    
    def _on_window_state_changed(self, window, param):
        """Save window state when it changes."""
        config = self.config_manager.get_config()
        if config.ui.remember_window_state:
            config.ui.window_width = self.window.get_width()
            config.ui.window_height = self.window.get_height()
            config.ui.window_maximized = self.window.is_maximized()
            self.config_manager.save_config(config)
    
    def _on_close_request(self, window):
        """Handle window close request and save final state."""
        config = self.config_manager.get_config()
        if config.ui.remember_window_state:
            config.ui.window_width = self.window.get_width()
            config.ui.window_height = self.window.get_height()
            config.ui.window_maximized = self.window.is_maximized()
            self.config_manager.save_config(config)
        return False  # Allow the window to close
    
    def apply_theme(self):
        """Apply the current theme."""
        from ..config import ThemeManager
        
        theme_manager = ThemeManager(self.config_manager)
        theme_manager.apply_theme()
    
    def save_current_state(self):
        """Manually save the current window state."""
        config = self.config_manager.get_config()
        if config.ui.remember_window_state:
            config.ui.window_width = self.window.get_width()
            config.ui.window_height = self.window.get_height()
            config.ui.window_maximized = self.window.is_maximized()
            self.config_manager.save_config(config)
    
    def restore_default_size(self):
        """Restore the window to its default size."""
        config = self.config_manager.get_config()
        self.window.set_default_size(config.ui.window_width, config.ui.window_height)
        
        if config.ui.window_maximized:
            self.window.maximize()
        else:
            self.window.unmaximize()
    
    def toggle_maximized(self):
        """Toggle the window maximized state."""
        if self.window.is_maximized():
            self.window.unmaximize()
        else:
            self.window.maximize()
    
    def get_window_info(self):
        """Get current window information."""
        return {
            'width': self.window.get_width(),
            'height': self.window.get_height(),
            'maximized': self.window.is_maximized(),
            'visible': self.window.get_visible()
        }
