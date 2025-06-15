"""
Command pattern implementation for application actions.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from gi.repository import Adw, Gtk
from .models import PasswordEntry, AppState
from .services import PasswordService, ValidationService
from .managers import ToastManager, ClipboardManager


class Command(ABC):
    """Base command interface."""
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True if successful."""
        pass
    
    @abstractmethod
    def can_execute(self) -> bool:
        """Check if the command can be executed."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get command description for logging/debugging."""
        pass


class PasswordCommand(Command):
    """Base class for password-related commands."""
    
    def __init__(self, 
                 password_service: PasswordService,
                 toast_manager: ToastManager,
                 app_state: AppState):
        self.password_service = password_service
        self.toast_manager = toast_manager
        self.app_state = app_state


class CopyPasswordCommand(PasswordCommand):
    """Command to copy password to clipboard."""
    
    def __init__(self, 
                 password_service: PasswordService,
                 toast_manager: ToastManager,
                 app_state: AppState,
                 clipboard_manager: ClipboardManager):
        super().__init__(password_service, toast_manager, app_state)
        self.clipboard_manager = clipboard_manager
    
    def can_execute(self) -> bool:
        entry = self.app_state.selected_entry
        return entry is not None and not entry.is_folder and entry.password is not None
    
    def execute(self) -> bool:
        if not self.can_execute():
            self.toast_manager.show_warning("No password selected to copy")
            return False
        
        entry = self.app_state.selected_entry
        if entry.password:
            return self.clipboard_manager.copy_password(entry.password)
        else:
            # Fallback to pass -c command
            success, message = self.password_service.copy_password_to_clipboard(entry.path)
            if success:
                self.toast_manager.show_success(message)
            else:
                self.toast_manager.show_error(message)
            return success
    
    @property
    def description(self) -> str:
        return "Copy password to clipboard"


class CopyUsernameCommand(PasswordCommand):
    """Command to copy username to clipboard."""
    
    def __init__(self, 
                 password_service: PasswordService,
                 toast_manager: ToastManager,
                 app_state: AppState,
                 clipboard_manager: ClipboardManager):
        super().__init__(password_service, toast_manager, app_state)
        self.clipboard_manager = clipboard_manager
    
    def can_execute(self) -> bool:
        entry = self.app_state.selected_entry
        return (entry is not None and 
                not entry.is_folder and 
                entry.username is not None and 
                entry.username.strip() != "")
    
    def execute(self) -> bool:
        if not self.can_execute():
            self.toast_manager.show_warning("No username to copy")
            return False
        
        return self.clipboard_manager.copy_username(self.app_state.selected_entry.username)
    
    @property
    def description(self) -> str:
        return "Copy username to clipboard"


class DeletePasswordCommand(PasswordCommand):
    """Command to delete a password entry."""
    
    def __init__(self, 
                 password_service: PasswordService,
                 toast_manager: ToastManager,
                 app_state: AppState,
                 parent_window: Adw.Window,
                 on_success_callback: callable = None):
        super().__init__(password_service, toast_manager, app_state)
        self.parent_window = parent_window
        self.on_success_callback = on_success_callback
    
    def can_execute(self) -> bool:
        entry = self.app_state.selected_entry
        return entry is not None and not entry.is_folder
    
    def execute(self) -> bool:
        if not self.can_execute():
            self.toast_manager.show_warning("No password selected to delete")
            return False
        
        entry = self.app_state.selected_entry
        
        # Import DialogManager for consistent dialog creation
        from ..utils.ui_utils import DialogManager, UIConstants

        # Show confirmation dialog
        dialog = DialogManager.create_message_dialog(
            parent=self.parent_window,
            heading=f"Delete '{entry.name}'?",
            body=f"Are you sure you want to permanently delete the password entry for '{entry.path}'?",
            dialog_type="question",
            default_size=UIConstants.SMALL_DIALOG
        )

        # Add response buttons
        DialogManager.add_dialog_response(dialog, "cancel", "_Cancel", "default")
        DialogManager.add_dialog_response(dialog, "delete", "_Delete", "destructive")
        dialog.set_default_response("cancel")

        def on_response(dialog, response_id):
            if response_id == "delete":
                success, message = self.password_service.delete_entry(entry.path)
                if success:
                    self.toast_manager.show_success(message)
                    self.app_state.clear_selection()
                    if self.on_success_callback:
                        self.on_success_callback()
                else:
                    self.toast_manager.show_error(message)
            dialog.close()

        dialog.connect("response", on_response)
        dialog.present(self.parent_window)
        return True  # Command was initiated successfully
    
    @property
    def description(self) -> str:
        return "Delete password entry"


class OpenUrlCommand(PasswordCommand):
    """Command to open URL in browser."""
    
    def can_execute(self) -> bool:
        entry = self.app_state.selected_entry
        return (entry is not None and 
                not entry.is_folder and 
                entry.url is not None and 
                self._is_valid_url(entry.url))
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        if not url or url in ["Not set", "N/A for folders"]:
            return False
        return (url.startswith("http://") or 
                url.startswith("https://") or 
                url.startswith("www."))
    
    def execute(self) -> bool:
        if not self.can_execute():
            self.toast_manager.show_warning("No valid URL to open")
            return False
        
        entry = self.app_state.selected_entry
        url = entry.url
        
        try:
            actual_url = url
            if url.startswith("www."):
                actual_url = "http://" + url
            
            Gtk.show_uri(None, actual_url, 0)  # 0 instead of Gdk.CURRENT_TIME
            self.toast_manager.show_success(f"Opening URL: {actual_url}")
            return True
        except Exception as e:
            self.toast_manager.show_error(f"Failed to open URL: {e}")
            return False
    
    @property
    def description(self) -> str:
        return "Open URL in browser"


class GitSyncCommand(PasswordCommand):
    """Command for Git operations."""
    
    def __init__(self, 
                 password_service: PasswordService,
                 toast_manager: ToastManager,
                 app_state: AppState,
                 operation: str,  # "pull" or "push"
                 on_success_callback: callable = None):
        super().__init__(password_service, toast_manager, app_state)
        self.operation = operation
        self.on_success_callback = on_success_callback
    
    def can_execute(self) -> bool:
        return self.password_service.is_initialized()
    
    def execute(self) -> bool:
        if not self.can_execute():
            self.toast_manager.show_error("Password store not initialized")
            return False
        
        self.toast_manager.show_info(f"Git {self.operation} in progress...")
        
        if self.operation == "pull":
            success, message = self.password_service.sync_pull()
        elif self.operation == "push":
            success, message = self.password_service.sync_push()
        else:
            self.toast_manager.show_error(f"Unknown git operation: {self.operation}")
            return False
        
        if success:
            self.toast_manager.show_success(f"Git {self.operation} successful: {message}")
            if self.on_success_callback:
                self.on_success_callback()
        else:
            self.toast_manager.show_error(f"Git {self.operation} failed: {message}")
        
        return success
    
    @property
    def description(self) -> str:
        return f"Git {self.operation}"


class CommandInvoker:
    """Manages and executes commands."""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._history: list = []
    
    def register_command(self, name: str, command: Command):
        """Register a command with a name."""
        self._commands[name] = command
    
    def execute_command(self, name: str) -> bool:
        """Execute a command by name."""
        if name not in self._commands:
            print(f"Command '{name}' not found")
            return False
        
        command = self._commands[name]
        if not command.can_execute():
            print(f"Command '{name}' cannot be executed")
            return False
        
        success = command.execute()
        self._history.append((name, success))
        return success
    
    def can_execute_command(self, name: str) -> bool:
        """Check if a command can be executed."""
        if name not in self._commands:
            return False
        return self._commands[name].can_execute()
    
    def get_command_description(self, name: str) -> str:
        """Get command description."""
        if name not in self._commands:
            return "Unknown command"
        return self._commands[name].description
