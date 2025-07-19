"""
WindowController - Handles window-level coordination and controller management.

This controller manages the initialization and coordination of various subsystem controllers,
setup orchestration, and command system setup. It extracts these responsibilities from
the main SecretsWindow class to improve maintainability and separation of concerns.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GObject
from typing import Optional, TYPE_CHECKING

from ..commands import CommandInvoker, CopyPasswordCommand, CopyUsernameCommand, DeletePasswordCommand, OpenUrlCommand
from ..controllers import (
    PasswordListController,
    SetupController,
    WindowStateManager,
    ActionController
)
from ..controllers.dynamic_folder_controller import DynamicFolderController
from ..managers import ToastManager, ClipboardManager, PasswordDisplayManager, SearchManager
from ..services import PasswordService, ValidationService
from ..async_operations import AsyncPasswordOperations, TaskManager
from ..error_handling import ErrorHandler, PasswordStoreError, ValidationError, UIError
from ..logging_system import get_logger, LogCategory

if TYPE_CHECKING:
    from ..window import SecretsWindow

logger = get_logger(LogCategory.UI)


class WindowController:
    """Controller for window-level coordination and controller management."""
    
    def __init__(self, window: 'SecretsWindow'):
        """Initialize the window controller.
        
        Args:
            window: The main SecretsWindow instance
        """
        self.window = window
        self.logger = logger
        
        # Controller instances
        self.password_list_controller: Optional[PasswordListController] = None
        self.setup_controller: Optional[SetupController] = None
        self.window_state_manager: Optional[WindowStateManager] = None
        self.action_controller: Optional[ActionController] = None
        self.dynamic_folder_controller: Optional[DynamicFolderController] = None
        
        # Managers
        self.toast_manager: Optional[ToastManager] = None
        self.clipboard_manager: Optional[ClipboardManager] = None
        self.password_display_manager: Optional[PasswordDisplayManager] = None
        self.search_manager: Optional[SearchManager] = None
        
        # Services
        self.password_service: Optional[PasswordService] = None
        self.validation_service: Optional[ValidationService] = None
        
        # Operations
        self.async_operations: Optional[AsyncPasswordOperations] = None
        self.task_manager: Optional[TaskManager] = None
        
        # Command system
        self.command_invoker: Optional[CommandInvoker] = None
        
        # Error handler
        self.error_handler: Optional[ErrorHandler] = None
        
        self._initialized = False
    
    def initialize_controllers(self):
        """Initialize all controllers and managers."""
        if self._initialized:
            self.logger.warning("WindowController already initialized")
            return
            
        try:
            self.logger.info("Initializing window controller and subsystems")
            
            # Initialize error handler first
            self._initialize_error_handler()
            
            # Initialize services
            self._initialize_services()
            
            # Initialize managers
            self._initialize_managers()
            
            # Initialize operations
            self._initialize_operations()
            
            # Initialize command system (before controllers that need it)
            self._initialize_command_system()
            
            # Initialize controllers
            self._initialize_core_controllers()
            
            # Setup controller relationships
            self._setup_controller_relationships()
            
            self._initialized = True
            self.logger.info("Window controller initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize controllers: {e}")
            if self.error_handler:
                self.error_handler.handle_error(
                    UIError(f"Controller initialization failed: {e}")
                )
            raise
    
    def _initialize_error_handler(self):
        """Initialize the error handler."""
        self.error_handler = ErrorHandler(self.window)
    
    def _initialize_services(self):
        """Initialize core services."""
        # Store reference to password store for backward compatibility
        self.password_store = self.window.password_store
        
        # Initialize password service
        self.password_service = PasswordService(
            password_store=self.password_store
        )
        
        # Initialize validation service
        self.validation_service = ValidationService()
    
    def _initialize_managers(self):
        """Initialize manager components."""
        # Initialize toast manager
        self.toast_manager = ToastManager(self.window.toast_overlay)
        
        # Initialize clipboard manager
        self.clipboard_manager = ClipboardManager(
            display=self.window.get_display(),
            toast_manager=self.toast_manager,
            config_manager=self.window.config_manager
        )
        
        # Initialize password display manager (if components are available)
        self.password_display_manager = None
        if hasattr(self.window, 'password_details_component'):
            self.password_display_manager = PasswordDisplayManager(
                self.window.password_details_component
            )
        
        # Initialize search manager  
        self.search_manager = SearchManager(
            search_entry=self.window.search_entry,
            password_store=self.window.password_store,
            toast_manager=self.toast_manager,
            on_search_results=self._on_search_results
        )
    
    def _initialize_operations(self):
        """Initialize async operations and task management."""
        self.task_manager = TaskManager(self.toast_manager)
        self.async_operations = AsyncPasswordOperations(
            password_service=self.password_service,
            toast_manager=self.toast_manager
        )
    
    def _initialize_core_controllers(self):
        """Initialize core controller components."""
        # Initialize window state manager
        self.window_state_manager = WindowStateManager(
            window=self.window,
            config_manager=self.window.config_manager
        )
        
        # Initialize setup controller
        self.setup_controller = SetupController(
            password_store=self.password_store,
            toast_manager=self.toast_manager,
            error_handler=self.error_handler,
            parent_window=self.window,
            on_setup_complete=self._on_setup_complete
        )
        
        # Initialize action controller
        self.action_controller = ActionController(
            window=self.window,
            toast_manager=self.toast_manager
        )
        
        # Initialize password list controller
        self.password_list_controller = PasswordListController(
            password_store=self.password_store,
            toast_manager=self.toast_manager,
            treeview_scrolled_window=self.window.password_list_scrolled,
            search_entry=self.window.search_entry
        )
        
        
        # Initialize dynamic folder controller
        self.dynamic_folder_controller = DynamicFolderController(
            password_store=self.window.password_store,
            toast_manager=self.toast_manager,
            folders_listbox=self.window.password_list_box,
            search_entry=self.window.search_entry,
            on_selection_changed=self.window._on_selection_changed,
            parent_window=self.window
        )
    
    def _initialize_command_system(self):
        """Initialize the command system and register commands."""
        self.command_invoker = CommandInvoker()
        
        # Register common commands
        self.command_invoker.register_command(
            'copy_password',
            lambda path: CopyPasswordCommand(
                path=path,
                password_service=self.password_service,
                clipboard_manager=self.clipboard_manager,
                toast_manager=self.toast_manager
            )
        )
        
        self.command_invoker.register_command(
            'copy_username',
            lambda path: CopyUsernameCommand(
                path=path,
                password_service=self.password_service,
                clipboard_manager=self.clipboard_manager,
                toast_manager=self.toast_manager
            )
        )
        
        self.command_invoker.register_command(
            'delete_password',
            lambda path: DeletePasswordCommand(
                path=path,
                password_service=self.password_service,
                toast_manager=self.toast_manager,
                on_success=self._refresh_password_list
            )
        )
        
        self.command_invoker.register_command(
            'open_url',
            lambda url: OpenUrlCommand(
                url=url,
                toast_manager=self.toast_manager
            )
        )
    
    def _setup_controller_relationships(self):
        """Setup relationships and dependencies between controllers."""
        
        # Update action controller callbacks to connect to other controllers
        if self.action_controller and self.password_list_controller:
            # Update callbacks to connect controllers through the action controller
            self.action_controller.update_callback('focus_search', 
                lambda: getattr(self.window, '_focus_search_blueprint', lambda: None)())
            self.action_controller.update_callback('clear_search', 
                lambda: getattr(self.window, '_clear_search_blueprint', lambda: None)())
            self.action_controller.update_callback('refresh', 
                lambda: getattr(self.window, '_load_passwords_controller', lambda: None)())
        
        # Setup dynamic folder controller callbacks
        if self.dynamic_folder_controller:
            # Set up action callbacks for password actions
            self.dynamic_folder_controller.set_action_callbacks(
                copy_username=self.window._on_copy_username_signal,
                copy_password=self.window._on_copy_password_signal,
                copy_totp=self.window._on_copy_totp_signal,
                visit_url=self.window._on_visit_url_signal,
                edit_password=self.window._on_edit_password_signal_from_path,
                view_details=self.window._on_view_details_signal_from_path,
                remove_password=self.window._on_remove_password_signal_from_path
            )
            
            # Set up folder controller callbacks for folder operations
            self.dynamic_folder_controller.add_password_to_folder_requested = self.window._on_add_password_to_folder_requested
            self.dynamic_folder_controller.add_subfolder_requested = self.window._on_add_subfolder_requested
            self.dynamic_folder_controller.edit_folder_requested = self.window._on_edit_folder_requested
            self.dynamic_folder_controller.delete_folder_requested = self.window._on_delete_folder_dialog_requested
    
    def verify_setup_and_load(self):
        """Verify setup completion and load initial data."""
        if not self._initialized:
            raise RuntimeError("WindowController must be initialized before verifying setup")
        
        try:
            self.logger.info("Verifying setup and loading initial data")
            
            # Check if setup is valid
            if self.setup_controller and not self.setup_controller.is_setup_valid:
                self.logger.info("Setup required, validating setup")
                self.setup_controller.validate_and_setup_store()
                return
            
            # Setup is complete, load passwords
            self._on_setup_complete()
            
        except Exception as e:
            self.logger.error(f"Setup verification failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(
                    UIError(f"Setup verification failed: {e}")
                )
    
    def _on_setup_complete(self):
        """Handle setup completion and load passwords."""
        try:
            self.logger.info("Setup complete, loading passwords")
            
            # Load passwords using the dynamic folder controller (main password display)
            if self.dynamic_folder_controller:
                self.dynamic_folder_controller.load_passwords()
            
            # Update window state (method may not exist)
            if self.window_state_manager and hasattr(self.window_state_manager, 'on_passwords_loaded'):
                self.window_state_manager.on_passwords_loaded()
            
            self.logger.info("Password loading completed")
            
        except Exception as e:
            self.logger.error(f"Failed to load passwords after setup: {e}")
            if self.error_handler:
                self.error_handler.handle_error(
                    PasswordStoreError(f"Failed to load passwords: {e}")
                )
    
    def _refresh_password_list(self):
        """Refresh the password list after changes."""
        if self.dynamic_folder_controller:
            self.dynamic_folder_controller.load_passwords()
    
    def _on_search_results(self, search_result):
        """Handle search results from SearchManager."""
        # For now, delegate to the window's search handling
        # This could be improved with better controller integration
        if hasattr(self.window, '_on_search_results'):
            self.window._on_search_results(search_result)
    
    def execute_command(self, command_name: str, *args, **kwargs):
        """Execute a command through the command system.
        
        Args:
            command_name: Name of the command to execute
            *args: Command arguments
            **kwargs: Command keyword arguments
        """
        if not self.command_invoker:
            raise RuntimeError("Command system not initialized")
        
        try:
            command = self.command_invoker.create_command(command_name, *args, **kwargs)
            self.command_invoker.execute(command)
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(
                    UIError(f"Command '{command_name}' failed: {e}")
                )
    
    def shutdown(self):
        """Cleanup resources and shutdown controllers."""
        self.logger.info("Shutting down window controller")
        
        try:
            # Shutdown task manager
            if self.task_manager:
                self.task_manager.shutdown()
            
            # Cleanup controllers
            controllers = [
                self.password_list_controller,
                self.setup_controller,
                self.window_state_manager,
                self.action_controller,
                self.dynamic_folder_controller
            ]
            
            for controller in controllers:
                if controller and hasattr(controller, 'cleanup'):
                    try:
                        controller.cleanup()
                    except Exception as e:
                        self.logger.warning(f"Error cleaning up controller {type(controller).__name__}: {e}")
            
            self._initialized = False
            self.logger.info("Window controller shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during window controller shutdown: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if the controller is initialized."""
        return self._initialized