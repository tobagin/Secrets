"""
Action Controller - Manages window actions and keyboard shortcuts.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from typing import Callable, Optional, Dict, Any

from ..managers import ToastManager


class ActionController:
    """Controls window actions, keyboard shortcuts, and menu handling."""
    
    def __init__(self, 
                 window: Adw.Window,
                 toast_manager: ToastManager,
                 # Callback functions for various actions
                 on_add_password: Optional[Callable] = None,
                 on_edit_password: Optional[Callable] = None,
                 on_delete_password: Optional[Callable] = None,
                 on_copy_password: Optional[Callable] = None,
                 on_copy_username: Optional[Callable] = None,
                 on_focus_search: Optional[Callable] = None,
                 on_clear_search: Optional[Callable] = None,
                 on_refresh: Optional[Callable] = None,
                 on_toggle_password: Optional[Callable] = None,
                 on_generate_password: Optional[Callable] = None,
                 on_show_help: Optional[Callable] = None,
                 on_import_export: Optional[Callable] = None):
        
        self.window = window
        self.toast_manager = toast_manager
        
        # Store callback functions
        self.callbacks = {
            'add_password': on_add_password,
            'edit_password': on_edit_password,
            'delete_password': on_delete_password,
            'copy_password': on_copy_password,
            'copy_username': on_copy_username,
            'focus_search': on_focus_search,
            'clear_search': on_clear_search,
            'refresh': on_refresh,
            'toggle_password': on_toggle_password,
            'generate_password': on_generate_password,
            'show_help': on_show_help,
            'import_export': on_import_export
        }
        
        # Setup window actions
        self._setup_window_actions()
    
    def _setup_window_actions(self):
        """Setup window-specific actions for keyboard shortcuts."""
        actions = [
            ("add-password", self._on_add_password),
            ("edit-password", self._on_edit_password),
            ("delete-password", self._on_delete_password),
            ("copy-password", self._on_copy_password),
            ("copy-username", self._on_copy_username),
            ("focus-search", self._on_focus_search),
            ("clear-search", self._on_clear_search),
            ("refresh", self._on_refresh),
            ("toggle-password", self._on_toggle_password),
            ("generate-password", self._on_generate_password),
            ("show-help-overlay", self._on_show_help_overlay),
            ("import-export", self._on_import_export)
        ]
        
        for action_name, callback in actions:
            action = Gio.SimpleAction.new(action_name, None)
            action.connect("activate", callback)
            self.window.add_action(action)
    
    def _execute_callback(self, callback_name: str, *args, **kwargs):
        """Execute a callback if it exists."""
        callback = self.callbacks.get(callback_name)
        if callback:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.toast_manager.show_error(f"Action failed: {e}")
        else:
            self.toast_manager.show_warning(f"Action '{callback_name}' not available")
    
    def _on_add_password(self, action, param):
        """Handle add password action."""
        self._execute_callback('add_password')
    
    def _on_edit_password(self, action, param):
        """Handle edit password action."""
        self._execute_callback('edit_password')
    
    def _on_delete_password(self, action, param):
        """Handle delete password action."""
        self._execute_callback('delete_password')
    
    def _on_copy_password(self, action, param):
        """Handle copy password action."""
        self._execute_callback('copy_password')
    
    def _on_copy_username(self, action, param):
        """Handle copy username action."""
        self._execute_callback('copy_username')
    
    def _on_focus_search(self, action, param):
        """Handle focus search action."""
        self._execute_callback('focus_search')
    
    def _on_clear_search(self, action, param):
        """Handle clear search action."""
        self._execute_callback('clear_search')
    
    def _on_refresh(self, action, param):
        """Handle refresh action."""
        self._execute_callback('refresh')
    
    def _on_toggle_password(self, action, param):
        """Handle toggle password visibility action."""
        self._execute_callback('toggle_password')
    
    def _on_generate_password(self, action, param):
        """Handle generate password action."""
        self._execute_callback('generate_password')
    
    def _on_show_help_overlay(self, action, param):
        """Handle show help overlay action."""
        self._execute_callback('show_help')
    
    def _on_import_export(self, action, param):
        """Handle import/export action."""
        self._execute_callback('import_export')
    
    def update_callback(self, callback_name: str, callback: Callable):
        """Update a callback function."""
        if callback_name in self.callbacks:
            self.callbacks[callback_name] = callback
        else:
            raise ValueError(f"Unknown callback: {callback_name}")
    
    def enable_action(self, action_name: str, enabled: bool = True):
        """Enable or disable a specific action."""
        action = self.window.lookup_action(action_name)
        if action:
            action.set_enabled(enabled)
        else:
            print(f"Warning: Action '{action_name}' not found")
    
    def get_action(self, action_name: str) -> Optional[Gio.SimpleAction]:
        """Get a specific action by name."""
        return self.window.lookup_action(action_name)
    
    def trigger_action(self, action_name: str):
        """Programmatically trigger an action."""
        action = self.window.lookup_action(action_name)
        if action:
            action.activate(None)
        else:
            self.toast_manager.show_warning(f"Action '{action_name}' not found")
    
    def get_available_actions(self) -> list:
        """Get a list of all available action names."""
        return list(self.callbacks.keys())
    
    def set_action_enabled_state(self, states: Dict[str, bool]):
        """Set the enabled state for multiple actions at once."""
        for action_name, enabled in states.items():
            self.enable_action(action_name, enabled)
