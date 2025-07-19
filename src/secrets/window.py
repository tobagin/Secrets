import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GObject, Gio, Gdk, GLib # Added GLib
import os

from .password_store import PasswordStore
from .ui.dialogs import PasswordDialog, FolderDialog
from .app_info import APP_ID # Added to construct resource path programmatically
from .utils import DialogManager, UIConstants, AccessibilityHelper

# Import UI components
from .ui.components import HeaderBarComponent, PasswordListComponent, PasswordDetailsComponent

# Import new architecture components
from .models import PasswordEntry, PasswordListItem, AppState
from .managers import ToastManager, ClipboardManager, PasswordDisplayManager, SearchManager  # GitManager disabled for v0.8.6
from .services import PasswordService, ValidationService
from .commands import CommandInvoker, CopyPasswordCommand, CopyUsernameCommand, DeletePasswordCommand, OpenUrlCommand  # GitSyncCommand disabled for v0.8.6
from .config import ConfigManager, Constants
from .async_operations import AsyncPasswordOperations, TaskManager
from .error_handling import ErrorHandler, PasswordStoreError, ValidationError, UIError

# Import new controller components
from .controllers import (
    PasswordListController,
    PasswordDetailsController,
    SetupController,
    WindowStateManager,
    ActionController
)
from .controllers.dynamic_folder_controller import DynamicFolderController
from .security_manager import SecurityManager

# Git-related components disabled for v0.8.6
# from .ui.components.git_status_component import GitStatusComponent
# from .ui.dialogs.git_setup_dialog import GitSetupDialog
# from .ui.dialogs.git_status_dialog import GitStatusDialog

# Define a GObject for items in our ListView
class PasswordListItem(GObject.Object):
    __gtype_name__ = "PasswordListItem"

    name = GObject.Property(type=str)
    full_path = GObject.Property(type=str)
    is_folder = GObject.Property(type=bool, default=False)
    children_model = GObject.Property(type=Gio.ListStore) # For TreeListModel

    def __init__(self, name, full_path, is_folder, children_model=None):
        super().__init__()
        self.name = name
        self.full_path = full_path
        self.is_folder = is_folder
        # Initialize children_model if this item is a folder
        if is_folder and children_model is None:
            self.children_model = Gio.ListStore.new(PasswordListItem)
        elif children_model is not None: # Allow passing pre-filled model
            self.children_model = children_model

@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/main_window.ui')
class SecretsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SecretsWindow"

    # Template widgets (matching main_window.blp)
    toast_overlay = Gtk.Template.Child()
    main_toolbar = Gtk.Template.Child()
    main_header = Gtk.Template.Child()
    window_title = Gtk.Template.Child()
    search_toggle_button = Gtk.Template.Child()
    add_password_button = Gtk.Template.Child()
    add_folder_button = Gtk.Template.Child()
    git_pull_button = Gtk.Template.Child()
    git_push_button = Gtk.Template.Child()
    main_menu_button = Gtk.Template.Child()
    main_content = Gtk.Template.Child()
    search_clamp = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    password_list_scrolled = Gtk.Template.Child()
    password_list_box = Gtk.Template.Child()

    def __init__(self, config_manager=None, **kwargs):
        super().__init__(**kwargs)
        # In GTK4, stack page names are set in the UI file with the "name" property
        # No need to set them programmatically as they're already defined in the UI template

        # Initialize configuration and error handling
        self.config_manager = config_manager or ConfigManager()
        self.error_handler = ErrorHandler(self.config_manager)

        # Initialize application state
        self.app_state = AppState()

        # Initialize password store and service
        self.password_store = PasswordStore()
        self.password_service = PasswordService(self.password_store)

        # Initialize managers
        self.toast_manager = ToastManager(self.toast_overlay)
        self.clipboard_manager = ClipboardManager(self.get_display(), self.toast_manager, self.config_manager)

        # Initialize command system
        self.command_invoker = CommandInvoker()
        self._setup_commands()

        # Initialize async operations
        self.async_ops = AsyncPasswordOperations(self.password_service, self.toast_manager)
        self.task_manager = TaskManager(self.toast_manager)

        # Initialize security manager
        self.security_manager = SecurityManager(self.config_manager, self)
        self.security_manager.register_lock_callback(self._on_application_locked)
        self.security_manager.register_unlock_callback(self._on_application_unlocked)

        # Git manager and components disabled for v0.8.6
        # self.git_manager = GitManager(
        #     self.password_store.store_dir,
        #     self.config_manager,
        #     self.toast_manager
        # )
        # self.git_status_component = GitStatusComponent(self.git_manager)

        # Initialize basic controllers only (complex UI controllers disabled for simple layout)
        self._initialize_basic_controllers()

        # Connect basic UI signals
        self.search_toggle_button.connect("toggled", self.on_search_toggle_clicked)
        self.add_password_button.connect("clicked", self.on_add_password_button_clicked)
        self.add_folder_button.connect("clicked", self.on_add_folder_button_clicked)

        # Connect git buttons
        self.git_pull_button.connect("clicked", self.on_git_pull_clicked)
        self.git_push_button.connect("clicked", self.on_git_push_clicked)

        # Setup git functionality
        self._setup_git_functionality()

    def _setup_git_functionality(self):
        """Setup git functionality and status checking."""
        # Import git-related components
        try:
            from .managers import GitManager
            from .services import GitService
            
            # Initialize git manager
            self.git_manager = GitManager(
                self.password_store.store_dir,
                self.config_manager,
                self.toast_manager
            )
            
            # Check initial git status
            self._update_git_button_states()
            
        except ImportError:
            # Git functionality not available
            self.git_pull_button.set_sensitive(False)
            self.git_push_button.set_sensitive(False)
            self.git_pull_button.set_tooltip_text("Git functionality not available")
            self.git_push_button.set_tooltip_text("Git functionality not available")

        # Folder signals are handled by the DynamicFolderController

    def _initialize_basic_controllers(self):
        """Initialize basic controller components for simple layout."""
        # Window state manager
        self.window_state_manager = WindowStateManager(self, self.config_manager)

        # Setup controller
        self.setup_controller = SetupController(
            self.password_store,
            self.toast_manager,
            self.error_handler,
            self,
            on_setup_complete=self._on_setup_complete
        )

        # Dynamic folder controller - creates AdwExpanderRow and AdwActionRow dynamically
        self.folder_controller = DynamicFolderController(
            self.password_store,
            self.toast_manager,
            self.password_list_box,  # Use simple password list box
            self.search_entry,
            on_selection_changed=self._on_selection_changed
        )

        # Set up folder edit callback
        self.folder_controller.edit_folder_requested = self._on_edit_folder_requested

        # Set up add password to folder callback
        self.folder_controller.add_password_to_folder_requested = self._on_add_password_to_folder_requested

        # Connect folder deletion dialog handling
        self.folder_controller.delete_folder_requested = self._on_delete_folder_dialog_requested
        
        # Set up password action callbacks
        self.folder_controller.set_action_callbacks(
            copy_username=self._on_copy_username_requested,
            copy_password=self._on_copy_password_requested,
            copy_totp=self._on_copy_totp_requested,
            visit_url=self._on_visit_url_requested,
            edit_password=self._on_edit_password_requested,
            view_details=self._on_view_details_requested,
            remove_password=self._on_remove_password_requested
        )
        
        # Set up folder action callbacks
        self.folder_controller.add_subfolder_requested = self._on_add_subfolder_requested

        # Initialize ActionController for menu actions and keyboard shortcuts
        self.action_controller = ActionController(
            self,
            self.toast_manager,
            on_focus_search=self._on_focus_search,
            on_clear_search=self._on_clear_search,
            on_refresh=self._on_refresh,
            on_generate_password=self._on_generate_password,
            on_show_help=self._on_show_help_overlay,
            on_import_export=self._on_import_export
        )

        # Setup validation is now handled by the setup wizard before this window is shown
        # Just verify that setup is complete and load passwords
        # Use GLib.idle_add to ensure this happens after the window is fully initialized
        GLib.idle_add(self._verify_setup_and_load)

        # Start security monitoring after initialization
        GLib.idle_add(self.security_manager.start_security_monitoring)

    def _verify_setup_and_load(self):
        """Verify that setup is complete and load passwords."""
        is_valid, status = self.password_store.validate_complete_setup()

        if is_valid:
            # Setup is valid, load passwords
            self.folder_controller.load_passwords()
        else:
            # This shouldn't happen if setup wizard worked correctly
            self.toast_manager.show_error("Setup validation failed. Please restart the application.")

    def _on_setup_complete(self):
        """Called when setup is complete and valid."""
        self.folder_controller.load_passwords()

    def _on_selection_changed(self, selection_model, *args):
        """Handle selection changes from the folder controller."""
        # In simple layout, no details view to update
        pass

    def _setup_commands(self):
        """Setup the command system with all available commands."""
        # Copy commands
        copy_password_cmd = CopyPasswordCommand(
            self.password_service, self.toast_manager, self.app_state, self.clipboard_manager
        )
        copy_username_cmd = CopyUsernameCommand(
            self.password_service, self.toast_manager, self.app_state, self.clipboard_manager
        )

        # Delete command
        delete_cmd = DeletePasswordCommand(
            self.password_service, self.toast_manager, self.app_state, self,
            on_success_callback=lambda: self.folder_controller.load_passwords()
        )

        # URL command
        open_url_cmd = OpenUrlCommand(
            self.password_service, self.toast_manager, self.app_state
        )

        # Git commands disabled for v0.8.6
        # git_pull_cmd = GitSyncCommand(
        #     self.password_service, self.toast_manager, self.app_state, "pull",
        #     on_success_callback=lambda: self.folder_controller.load_passwords()
        # )
        # git_push_cmd = GitSyncCommand(
        #     self.password_service, self.toast_manager, self.app_state, "push"
        # )

        # Register commands
        self.command_invoker.register_command("copy_password", copy_password_cmd)
        self.command_invoker.register_command("copy_username", copy_username_cmd)
        self.command_invoker.register_command("delete_password", delete_cmd)
        self.command_invoker.register_command("open_url", open_url_cmd)
        # Git commands disabled for v0.8.6
        # self.command_invoker.register_command("git_pull", git_pull_cmd)
        # self.command_invoker.register_command("git_push", git_push_cmd)

    def on_git_pull_clicked(self, widget):
        """Handle git pull button click."""
        if not hasattr(self, 'git_manager'):
            self._show_git_setup_dialog()
            return
            
        # Check if Git is properly set up
        try:
            status = self.git_manager.get_status()
            if not status.is_repo or not status.has_remote:
                self._show_git_setup_dialog()
                return

            # Execute git pull
            self.toast_manager.show_info("Pulling changes from remote repository...")
            success, message = self.git_manager.pull()
            
            if success:
                self.toast_manager.show_success("Successfully pulled changes from remote")
                # Refresh password list to show any changes
                self.folder_controller.load_passwords()
            else:
                self.toast_manager.show_error(f"Git pull failed: {message}")
                
        except Exception as e:
            self.toast_manager.show_error(f"Error during git pull: {str(e)}")

    def on_git_push_clicked(self, widget):
        """Handle git push button click."""
        if not hasattr(self, 'git_manager'):
            self._show_git_setup_dialog()
            return
            
        # Check if Git is properly set up
        try:
            status = self.git_manager.get_status()
            if not status.is_repo or not status.has_remote:
                self._show_git_setup_dialog()
                return

            # Execute git push
            self.toast_manager.show_info("Pushing changes to remote repository...")
            success, message = self.git_manager.push()
            
            if success:
                self.toast_manager.show_success("Successfully pushed changes to remote")
            else:
                self.toast_manager.show_error(f"Git push failed: {message}")
                
        except Exception as e:
            self.toast_manager.show_error(f"Error during git push: {str(e)}")

    def on_add_folder_button_clicked(self, widget):
        """Handle add folder button click."""

        # Get suggested parent folder from current selection
        suggested_parent = ""
        selected_item_obj = self.folder_controller.get_selected_item()
        if selected_item_obj and selected_item_obj.is_folder:
            # If a folder is selected, suggest it as parent
            if hasattr(selected_item_obj, 'full_path'):
                suggested_parent = selected_item_obj.full_path
            else:
                suggested_parent = selected_item_obj.path

        dialog = FolderDialog(
            transient_for_window=self,
            suggested_parent_path=suggested_parent
        )
        dialog.connect("folder-create-requested", self.on_add_folder_dialog_create_requested)
        dialog.present()

    def _on_copy_username_requested(self, password_path):
        """Handle copy username request from password row."""
        success, content_or_error = self.password_store.get_password_content(password_path)
        if success:
            from .services.password_content_parser import parse_password_content
            password_data = parse_password_content(content_or_error)
            if password_data.username:
                self.clipboard_manager.copy_username(password_data.username)
            else:
                self.toast_manager.show_warning("No username found in this password entry")
        else:
            self.toast_manager.show_error(f"Error reading password: {content_or_error}")

    def _on_copy_password_requested(self, password_path):
        """Handle copy password request from password row."""
        success, content_or_error = self.password_store.get_password_content(password_path)
        if success:
            from .services.password_content_parser import parse_password_content
            password_data = parse_password_content(content_or_error)
            if password_data.password:
                self.clipboard_manager.copy_password(password_data.password)
            else:
                self.toast_manager.show_warning("No password found in this entry")
        else:
            self.toast_manager.show_error(f"Error reading password: {content_or_error}")

    def _on_copy_totp_requested(self, password_path):
        """Handle copy TOTP request from password row."""
        success, content_or_error = self.password_store.get_password_content(password_path)
        if success:
            from .services.password_content_parser import parse_password_content
            password_data = parse_password_content(content_or_error)
            
            if password_data.totp:
                try:
                    import pyotp
                    import re
                    
                    # Normalize the TOTP secret (remove spaces, make uppercase)
                    normalized_secret = re.sub(r'[^A-Z2-7]', '', password_data.totp.upper())
                    
                    totp = pyotp.TOTP(normalized_secret)
                    current_totp = totp.now()
                    self.clipboard_manager.copy_text(current_totp, "TOTP code")
                except Exception as e:
                    self.toast_manager.show_error(f"Error generating TOTP: {str(e)}")
            else:
                self.toast_manager.show_warning("No TOTP secret found in this password entry")
        else:
            self.toast_manager.show_error(f"Error reading password: {content_or_error}")

    def _on_visit_url_requested(self, url):
        """Handle visit URL request from password row."""
        try:
            import subprocess
            subprocess.run(['xdg-open', url], check=True)
            self.toast_manager.show_success(f"Opening {url}")
        except Exception as e:
            self.toast_manager.show_error(f"Error opening URL: {str(e)}")

    def _on_view_details_requested(self, password_path):
        """Handle view details request from password row."""
        # Get password content and parse it
        success, content_or_error = self.password_store.get_password_content(password_path)
        if not success:
            self.toast_manager.show_error(f"Error reading password: {content_or_error}")
            return
        
        # Parse the password content into a PasswordEntry
        from .services.password_content_parser import parse_password_content
        from .models import PasswordEntry
        
        password_data = parse_password_content(content_or_error)
        password_entry = PasswordEntry(
            path=password_path,
            password=password_data.password,
            username=password_data.username,
            url=password_data.url,
            notes=password_data.notes,
            totp=password_data.totp,
            recovery_codes=password_data.recovery_codes,
            is_folder=False
        )
        
        # Create and show the password details dialog
        from .ui.dialogs.password_details_dialog import PasswordDetailsDialog
        
        details_dialog = PasswordDetailsDialog(password_entry)
        details_dialog.set_clipboard_manager(self.clipboard_manager)
        details_dialog.set_toast_manager(self.toast_manager)
        
        # Connect signals
        details_dialog.connect("visit-url", self._on_visit_url_from_dialog)
        
        # Present the dialog
        details_dialog.present(self)

    def _on_visit_url_from_dialog(self, dialog, url):
        """Handle visit URL signal from password details dialog."""
        self._open_url(url)

    def _on_remove_password_requested(self, password_path):
        """Handle remove password request from password row."""
        from .utils import DialogManager, UIConstants
        
        dialog = DialogManager.create_message_dialog(
            parent=self,
            heading=f"Delete '{os.path.basename(password_path)}'?",
            body=f"Are you sure you want to permanently delete the password entry for '{password_path}'?",
            dialog_type="question",
            default_size=UIConstants.SMALL_DIALOG
        )

        # Add response buttons
        DialogManager.add_dialog_response(dialog, "cancel", "_Cancel", "default")
        DialogManager.add_dialog_response(dialog, "delete", "_Delete", "destructive")
        dialog.set_default_response("cancel")

        dialog.connect("response", self.on_delete_confirm_response, password_path)
        dialog.present(self)

    def _on_add_subfolder_requested(self, folder_path):
        """Handle add subfolder request from folder expander row."""
        dialog = FolderDialog(
            mode="add",
            transient_for_window=self,
            suggested_parent_path=folder_path
        )
        dialog.connect("folder-create-requested", self.on_add_folder_dialog_create_requested)
        dialog.present()

    def _on_edit_password_requested(self, password_path):
        """Handle edit password request from password row."""
        success, content_or_error = self.password_store.get_password_content(password_path)
        if success:
            current_content = content_or_error

            # Load current color and icon from metadata
            password_metadata = self.password_store.get_password_metadata(password_path)
            current_color = password_metadata["color"]
            current_icon = password_metadata["icon"]

            # Create and show the edit dialog
            dialog = PasswordDialog(
                mode="edit",
                password_path=password_path,
                password_content=current_content,
                transient_for=self,
                password_store=self.password_store,
                current_color=current_color,
                current_icon=current_icon
            )
            dialog.connect("password-edit-requested", self.on_edit_dialog_save_requested)
            dialog.present()
        else:
            # content_or_error is the error message here
            self.toast_manager.show_error(f"Error fetching content: {content_or_error}")

    def on_search_toggle_clicked(self, widget):
        """Handle search toggle button click."""
        is_active = widget.get_active()
        self.search_clamp.set_visible(is_active)
        if is_active:
            self.search_entry.grab_focus()
        else:
            self.search_entry.set_text("")  # Clear search when hiding

    def on_edit_button_clicked(self, widget):
        selected_item_obj = self.folder_controller.get_selected_item()
        if selected_item_obj:
            # Handle both PasswordEntry and PasswordListItem objects
            if hasattr(selected_item_obj, 'full_path'):
                password_path = selected_item_obj.full_path
            else:
                password_path = selected_item_obj.path
            is_folder_flag = selected_item_obj.is_folder

            if is_folder_flag:
                self.toast_manager.show_warning("Cannot edit a folder.")
                return

            success, content_or_error = self.password_store.get_password_content(password_path)
            if success:
                current_content = content_or_error

                # Load current color and icon from metadata
                password_metadata = self.password_store.get_password_metadata(password_path)
                current_color = password_metadata["color"]
                current_icon = password_metadata["icon"]

                # Create and show the edit dialog
                dialog = PasswordDialog(
                    mode="edit",
                    password_path=password_path,
                    password_content=current_content,
                    transient_for=self,
                    password_store=self.password_store,
                    current_color=current_color,
                    current_icon=current_icon
                )
                dialog.connect("password-edit-requested", self.on_edit_dialog_save_requested)
                dialog.present()
            else:
                # content_or_error is the error message here
                self.toast_manager.show_error(f"Error fetching content: {content_or_error}")
        else:
            self.toast_manager.show_warning("No item selected to edit.")

    def on_edit_dialog_save_requested(self, dialog, old_path, new_path, new_content, color, icon):
        # Handle both content changes and path changes
        if old_path != new_path:
            # Path changed - need to move/rename and update content
            # First, update the content at the old location
            content_success, content_message = self.password_store.insert_password(old_path, new_content, multiline=True, force=True)
            if content_success:
                # Then move to the new location (this preserves folder structure)
                move_success, move_message = self.password_store.move_password(old_path, new_path)
                if move_success:
                    # Update metadata for the moved password
                    self.password_store.rename_password_metadata(old_path, new_path)
                    self.password_store.set_password_metadata(new_path, color, icon)
                    self.toast_manager.show_success(f"Password moved from '{old_path}' to '{new_path}' and updated")
                    self.folder_controller.load_passwords()  # Refresh the entire list
                else:
                    self.toast_manager.show_error(f"Content updated but move failed: {move_message}")
                    self.folder_controller.load_passwords()
            else:
                self.toast_manager.show_error(f"Error updating content: {content_message}")
        else:
            # Path unchanged - just update content
            success, message = self.password_store.insert_password(new_path, new_content, multiline=True, force=True)
            if success:
                # Store color and icon metadata for the password
                self.password_store.set_password_metadata(new_path, color, icon)
                self.toast_manager.show_success(message)
                # Refresh the specific password display with new metadata
                self.folder_controller.refresh_password_display(new_path)
            else:
                self.toast_manager.show_error(f"Error saving: {message}")

        dialog.close() # Close the dialog after handling

    def on_remove_button_clicked(self, widget):
        selected_item_obj = self.folder_controller.get_selected_item()
        if selected_item_obj:
            # Handle both PasswordEntry and PasswordListItem objects
            if hasattr(selected_item_obj, 'full_path'):
                password_path = selected_item_obj.full_path
            else:
                password_path = selected_item_obj.path
            is_folder_flag = selected_item_obj.is_folder

            if is_folder_flag: # For now, only allow deleting password files via UI
                self.toast_manager.show_warning("Cannot delete a folder directly. Remove its contents first.")
                return

            dialog = DialogManager.create_message_dialog(
                parent=self,
                heading=f"Delete '{os.path.basename(password_path)}'?",
                body=f"Are you sure you want to permanently delete the password entry for '{password_path}'?",
                dialog_type="question",
                default_size=UIConstants.SMALL_DIALOG
            )

            # Add response buttons
            DialogManager.add_dialog_response(dialog, "cancel", "_Cancel", "default")
            DialogManager.add_dialog_response(dialog, "delete", "_Delete", "destructive")
            dialog.set_default_response("cancel")

            dialog.connect("response", self.on_delete_confirm_response, password_path)

            dialog.present(self)

    def on_delete_confirm_response(self, dialog, response_id, password_path):
        if response_id == "delete":
            success, message = self.password_store.delete_password(password_path)
            if success:
                self.toast_manager.show_success(message)
                self.folder_controller.load_passwords() # Refresh the list
            else:
                self.toast_manager.show_error(f"Error: {message}")
        dialog.close() # Ensure dialog is closed









    def _on_delete_folder_dialog_requested(self, dialog, folder_path, folder_name):
        """Handle folder deletion dialog request from folder controller."""
        # Present the dialog with this window as parent (for Adw.AlertDialog)
        dialog.present(self)

    def on_add_password_button_clicked(self, widget):
        suggested_path = ""
        selected_item_obj = self.folder_controller.get_selected_item()
        if selected_item_obj:
            # Handle both PasswordEntry and PasswordListItem objects
            if hasattr(selected_item_obj, 'full_path'):
                path = selected_item_obj.full_path
            else:
                path = selected_item_obj.path
            is_folder_flag = selected_item_obj.is_folder
            if is_folder_flag:
                suggested_path = path
            else:
                # If a file is selected, suggest its parent folder
                suggested_path = os.path.dirname(path) if os.path.dirname(path) else ""

        dialog = PasswordDialog(
            transient_for=self,
            suggested_folder=suggested_path,
            password_store=self.password_store
        )
        dialog.connect("password-create-requested", self.on_add_dialog_add_requested)
        dialog.present()

    def on_add_folder_dialog_create_requested(self, dialog, folder_path, color, icon):
        """Handle folder creation request from add folder dialog."""
        try:
            # Create the folder in the password store
            success, message = self.password_store.create_folder(folder_path)

            if success:
                # Store color and icon metadata for the folder
                self.password_store.set_folder_metadata(folder_path, color, icon)
                self.toast_manager.show_success(f"Folder '{folder_path}' created successfully")
                # Refresh the folder list to show the new folder
                self.folder_controller.load_passwords()
                dialog.close()
            else:
                self.toast_manager.show_error(f"Failed to create folder: {message}")

        except Exception as e:
            self.toast_manager.show_error(f"Error creating folder: {str(e)}")
            print(f"Error creating folder '{folder_path}': {e}")

    def _on_edit_folder_requested(self, folder_path, folder_name):
        """Handle edit folder request from folder controller."""

        # Load current color and icon from metadata
        folder_metadata = self.password_store.get_folder_metadata(folder_path)
        current_color = folder_metadata["color"]
        current_icon = folder_metadata["icon"]

        dialog = FolderDialog(
            mode="edit",
            folder_path=folder_path,
            current_color=current_color,
            current_icon=current_icon,
            transient_for_window=self
        )
        dialog.connect("folder-edit-requested", self.on_edit_folder_dialog_save_requested)
        dialog.present()

    def _on_add_password_to_folder_requested(self, folder_path):
        """Handle add password to folder request from folder controller."""

        dialog = PasswordDialog(
            transient_for=self,
            suggested_folder=folder_path,
            password_store=self.password_store
        )
        dialog.connect("password-create-requested", self.on_add_dialog_add_requested)
        dialog.present()

    def on_edit_folder_dialog_save_requested(self, dialog, old_path, new_path, color, icon):
        """Handle folder edit save request from edit folder dialog."""
        try:
            if old_path != new_path:
                # Folder path changed - need to rename the folder
                success, message = self.password_store.rename_folder(old_path, new_path)

                if success:
                    # Update metadata for the renamed folder
                    self.password_store.rename_folder_metadata(old_path, new_path)
                    self.password_store.set_folder_metadata(new_path, color, icon)
                    self.toast_manager.show_success(f"Folder renamed from '{old_path}' to '{new_path}'")
                    # Refresh the folder list to show the changes
                    self.folder_controller.load_passwords()
                    dialog.close()
                else:
                    self.toast_manager.show_error(f"Failed to rename folder: {message}")
            else:
                # Only color/icon changed
                self.password_store.set_folder_metadata(old_path, color, icon)
                self.toast_manager.show_success(f"Folder '{old_path}' appearance updated")
                # Refresh the folder list to show the changes
                self.folder_controller.load_passwords()
                dialog.close()

        except Exception as e:
            self.toast_manager.show_error(f"Error editing folder: {str(e)}")
            print(f"Error editing folder '{old_path}': {e}")

    def on_add_dialog_add_requested(self, dialog, path, content, color, icon):
        # Use force=False to prevent overwriting existing entries by mistake.
        # `pass insert` without -f will fail if the entry already exists.
        success, message = self.password_store.insert_password(path, content, multiline=True, force=False)

        if success:
            # Store color and icon metadata for the password
            self.password_store.set_password_metadata(path, color, icon)
            self.toast_manager.show_success(message)
            self.folder_controller.load_passwords() # Refresh the list
        else:
            # Check if the error message indicates it already exists
            if "already exists" in message.lower(): # Crude check, but often pass says this
                # More specific error for this case
                error_toast_msg = f"Error: '{path}' already exists. Choose a different name or path."
            else:
                error_toast_msg = f"Error adding password: {message}"
            self.toast_manager.show_error(error_toast_msg)

        # Only close dialog on success, or provide a way for user to correct path?
        # For now, let's close it always, user can re-open if path was bad.
        # A better UX might keep dialog open on "already exists" and highlight path field.
        dialog.close()

    def _on_generate_password(self, action=None, param=None):
        """Show password generator dialog."""
        from .ui.dialogs import PasswordGeneratorDialog

        generator_dialog = PasswordGeneratorDialog(transient_for=self)
        generator_dialog.connect("password-generated", self._on_password_generated)
        generator_dialog.present()

    def _on_password_generated(self, dialog, password):
        """Handle generated password from generator dialog."""
        # Copy to clipboard using proper method
        try:
            display = self.get_display()
            if display:
                clipboard = display.get_clipboard()
                clipboard.set(password)
                self.toast_manager.show_success("Generated password copied to clipboard")
        except Exception as e:
            print(f"Error copying generated password to clipboard: {e}")
            self.toast_manager.show_error("Failed to copy password to clipboard")

    def _on_show_help_overlay(self, action=None, param=None):
        """Show keyboard shortcuts help overlay."""
        from .shortcuts_window import ShortcutsWindow

        shortcuts_window = ShortcutsWindow(self)
        shortcuts_window.present()

    def _on_import_export(self, action=None, param=None):
        """Show import/export dialog."""
        from .ui.dialogs import ImportExportDialog

        import_export_dialog = ImportExportDialog(
            parent_window=self,
            password_store=self.password_store,
            toast_manager=self.toast_manager,
            refresh_callback=self._refresh_password_list_after_import
        )
        import_export_dialog.present()

    def _on_compliance_dashboard(self, action=None, param=None):
        """Show compliance dashboard dialog."""
        from .ui.dialogs import ComplianceDashboardDialog

        compliance_dashboard_dialog = ComplianceDashboardDialog(
            parent_window=self,
            config_manager=self.config_manager
        )
        compliance_dashboard_dialog.present()

    def _on_focus_search(self, action=None, param=None):
        """Focus the search entry."""
        if hasattr(self, 'search_entry') and self.search_entry:
            self.search_entry.grab_focus()

    def _on_clear_search(self, action=None, param=None):
        """Clear the search entry and show all items."""
        if hasattr(self, 'search_entry') and self.search_entry:
            self.search_entry.set_text("")
        if hasattr(self, 'folder_controller') and self.folder_controller:
            self.folder_controller.clear_search()

    def _on_refresh(self, action=None, param=None):
        """Refresh the password list."""
        if hasattr(self, 'folder_controller') and self.folder_controller:
            self.folder_controller.load_passwords()
            self.toast_manager.show_success("Password list refreshed")

    def _refresh_password_list_after_import(self):
        """Refresh the password list after import operations."""
        if hasattr(self, 'folder_controller'):
            self.folder_controller.load_passwords()


    def _on_application_locked(self):
        """Called when the application is locked."""
        # Disable UI interactions
        self.set_sensitive(False)

        # Clear sensitive data from UI (no details controller in simple layout)

        # Clear search
        self.search_entry.set_text("")

    def _on_application_unlocked(self):
        """Called when the application is unlocked."""
        # Re-enable UI interactions
        self.set_sensitive(True)

        # Reload passwords
        self.folder_controller.load_passwords()

    def close_request(self):
        """Handle window close request."""
        # Stop security monitoring
        if hasattr(self, 'security_manager'):
            self.security_manager.stop_security_monitoring()
        return super().close_request()

    def _update_git_button_states(self):
        """Update git button states based on git setup status."""
        try:
            if hasattr(self, 'git_manager'):
                status = self.git_manager.get_status()
                
                # Enable buttons only if git repo is set up with remote
                git_enabled = status.is_repo and status.has_remote
                
                self.git_pull_button.set_sensitive(git_enabled)
                self.git_push_button.set_sensitive(git_enabled)
                
                if git_enabled:
                    self.git_pull_button.set_tooltip_text("Pull changes from remote repository")
                    self.git_push_button.set_tooltip_text("Push changes to remote repository")
                else:
                    self.git_pull_button.set_tooltip_text("Git repository not configured")
                    self.git_push_button.set_tooltip_text("Git repository not configured")
            else:
                # Git manager not available
                self.git_pull_button.set_sensitive(False)
                self.git_push_button.set_sensitive(False)
                self.git_pull_button.set_tooltip_text("Click to setup Git repository")
                self.git_push_button.set_tooltip_text("Click to setup Git repository")
                
        except Exception as e:
            print(f"Error updating git button states: {e}")
            self.git_pull_button.set_sensitive(False)
            self.git_push_button.set_sensitive(False)
            self.git_pull_button.set_tooltip_text("Git error - click to setup")
            self.git_push_button.set_tooltip_text("Git error - click to setup")

    def _show_git_setup_dialog(self):
        """Show the Git setup dialog."""
        from .ui.dialogs.git_setup_dialog import GitSetupDialog
        
        dialog = GitSetupDialog(
            store_dir=self.password_store.store_dir,
            config_manager=self.config_manager,
            toast_manager=self.toast_manager,
            transient_for=self
        )
        dialog.connect("setup-completed", self._on_git_setup_completed)
        dialog.present()

    def _on_git_setup_completed(self, dialog):
        """Handle Git setup completion."""
        # Reinitialize git manager
        self._setup_git_functionality()
        self.toast_manager.show_success("Git repository setup completed")

    def _on_git_status_updated(self, status):
        """Handle Git status updates."""
        self._update_git_button_visibility()

        # Auto-push if configured and there are changes
        config = self.config_manager.get_config()
        if config.git.auto_push_on_changes and status.is_dirty:
            GLib.idle_add(self.git_manager.auto_push_on_changes)

    def _update_git_button_visibility(self):
        """Update Git button visibility based on Git setup status."""
        status = self.git_manager.get_status()

        # Show buttons only if Git is available and repository is set up
        git_available = self.git_manager.git_service.is_git_available()
        show_buttons = git_available and status.is_repo

        self.git_pull_button.set_visible(show_buttons)
        self.git_push_button.set_visible(show_buttons)

        # Show status indicator if Git is available
        self.git_status_button.set_visible(git_available)

        # Enable/disable based on remote availability
        if show_buttons:
            self.git_pull_button.set_sensitive(status.has_remote)
            self.git_push_button.set_sensitive(status.has_remote)

    def _periodic_git_status_update(self):
        """Periodic Git status update."""
        self.git_status_component.refresh_status()
        return True  # Continue the timeout

    # Git dialog methods disabled for v0.8.6
    # def _show_git_setup_dialog(self, widget=None):
    #     """Show the Git setup dialog."""
    #     dialog = GitSetupDialog(
    #         store_dir=self.password_store.store_dir,
    #         config_manager=self.config_manager,
    #         toast_manager=self.toast_manager,
    #         transient_for=self
    #     )
    #     dialog.connect("setup-completed", self._on_git_setup_completed)
    #     dialog.present()

    # def _on_git_setup_completed(self, dialog):
    #     """Handle Git setup completion."""
    #     self.git_status_component.refresh_status()
    #     self.toast_manager.show_success("Git repository setup completed")

    # def show_git_status_dialog(self, widget=None):
    #     """Show the Git status dialog."""
    #     dialog = GitStatusDialog(
    #         git_manager=self.git_manager,
    #         transient_for=self
    #     )
    #     dialog.present()

    # def on_git_status_button_clicked(self, widget):
    #     """Handle Git status button click."""
    #     self.show_git_status_dialog()

    # Git status indicator method disabled for v0.8.6
    # def _setup_git_status_indicator(self):
    #     """Set up the Git status indicator in the header."""
    #     # Get the git_status_indicator from the git_status_button
    #     self.git_status_indicator = self.git_status_button.get_child()

    #     if self.git_status_indicator:
    #         # Clear existing children
    #         child = self.git_status_indicator.get_first_child()
    #         while child:
    #             next_child = child.get_next_sibling()
    #             self.git_status_indicator.remove(child)
    #             child = next_child

    #         # Create status indicator widget
    #         status_widget = self.git_status_component.create_status_indicator()
    #         self.git_status_indicator.append(status_widget)
