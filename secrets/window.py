import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GObject, Gdk, GLib # Added GLib
import os

from .password_store import PasswordStore
from .ui.dialogs import EditPasswordDialog, MoveRenameDialog, AddPasswordDialog
from .app_info import APP_ID # Added to construct resource path programmatically
from .utils import DialogManager, UIConstants, AccessibilityHelper

# Import UI components
from .ui.components import HeaderBarComponent, PasswordListComponent, PasswordDetailsComponent

# Import new architecture components
from .models import PasswordEntry, PasswordListItem, AppState
from .managers import ToastManager, ClipboardManager, PasswordDisplayManager, SearchManager
from .services import PasswordService, ValidationService
from .commands import CommandInvoker, CopyPasswordCommand, CopyUsernameCommand, DeletePasswordCommand, OpenUrlCommand, GitSyncCommand
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

@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/main_window.ui')
class SecretsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SecretsWindow"

    # Define template children for UI elements defined in secrets.ui
    details_stack = Gtk.Template.Child()
    placeholder_page = Gtk.Template.Child() # Added: AdwStatusPage from UI
    details_page_box = Gtk.Template.Child() # Added: GtkBox from UI for details
    # selected_password_label = Gtk.Template.Child() # Replaced by path_row and specific labels
    path_row = Gtk.Template.Child()
    password_expander_row = Gtk.Template.Child()
    password_display_label = Gtk.Template.Child()
    show_hide_password_button = Gtk.Template.Child()
    copy_password_button_in_row = Gtk.Template.Child()
    username_row = Gtk.Template.Child()
    copy_username_button = Gtk.Template.Child()
    url_row = Gtk.Template.Child()
    open_url_button = Gtk.Template.Child()
    notes_display_label = Gtk.Template.Child()

    edit_button = Gtk.Template.Child()
    remove_button = Gtk.Template.Child()
    move_rename_button = Gtk.Template.Child()
    add_password_button = Gtk.Template.Child()
    git_pull_button = Gtk.Template.Child()
    git_push_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    treeview_scrolled_window = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # In GTK4, stack page names are set in the UI file with the "name" property
        # No need to set them programmatically as they're already defined in the UI template

        # Initialize configuration and error handling
        self.config_manager = ConfigManager()
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

        # Initialize controllers
        self._initialize_controllers()

        # Connect remaining signals for buttons that aren't handled by controllers
        self.edit_button.connect("clicked", self.on_edit_button_clicked)
        self.remove_button.connect("clicked", self.on_remove_button_clicked)
        self.move_rename_button.connect("clicked", self.on_move_rename_button_clicked)
        self.add_password_button.connect("clicked", self.on_add_password_button_clicked)
        self.git_pull_button.connect("clicked", self.on_git_pull_clicked)
        self.git_push_button.connect("clicked", self.on_git_push_clicked)

    def _initialize_controllers(self):
        """Initialize all controller components."""
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

        # Password list controller
        self.list_controller = PasswordListController(
            self.password_store,
            self.toast_manager,
            self.treeview_scrolled_window,
            self.search_entry,
            on_selection_changed=self._on_selection_changed
        )

        # Password details controller
        self.details_controller = PasswordDetailsController(
            self.password_store,
            self.toast_manager,
            self.clipboard_manager,
            self.command_invoker,
            self.app_state,
            self.config_manager,
            # UI elements
            self.details_stack,
            self.placeholder_page,
            self.details_page_box,
            self.path_row,
            self.password_expander_row,
            self.password_display_label,
            self.show_hide_password_button,
            self.copy_password_button_in_row,
            self.username_row,
            self.copy_username_button,
            self.url_row,
            self.open_url_button,
            self.notes_display_label,
            self.edit_button,
            self.remove_button,
            self.move_rename_button
        )

        # Action controller
        self.action_controller = ActionController(
            self,
            self.toast_manager,
            on_add_password=self.on_add_password_button_clicked,
            on_edit_password=self.on_edit_button_clicked,
            on_delete_password=self.on_remove_button_clicked,
            on_copy_password=self.details_controller._on_copy_password_clicked,
            on_copy_username=self.details_controller._on_copy_username_clicked,
            on_focus_search=self.list_controller.focus_search,
            on_clear_search=self.list_controller.clear_search,
            on_refresh=self.list_controller.load_passwords,
            on_toggle_password=self.details_controller.toggle_password_visibility,
            on_generate_password=self._on_generate_password,
            on_show_help=self._on_show_help_overlay,
            on_import_export=self._on_import_export
        )

        # Setup validation is now handled by the setup wizard before this window is shown
        # Just verify that setup is complete and load passwords
        self._verify_setup_and_load()

    def _verify_setup_and_load(self):
        """Verify that setup is complete and load passwords."""
        is_valid, status = self.password_store.validate_complete_setup()

        if is_valid:
            # Setup is valid, load passwords
            self.list_controller.load_passwords()
            self.toast_manager.show_info("Password manager is ready to use")
        else:
            # This shouldn't happen if setup wizard worked correctly
            self.toast_manager.show_error("Setup validation failed. Please restart the application.")

    def _on_setup_complete(self):
        """Called when setup is complete and valid."""
        self.list_controller.load_passwords()

    def _on_selection_changed(self, selection_model, param):
        """Handle selection changes from the list controller."""
        selected_item = self.list_controller.get_selected_item()
        self.details_controller.update_details(selected_item)

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
            on_success_callback=lambda: self.list_controller.load_passwords()
        )

        # URL command
        open_url_cmd = OpenUrlCommand(
            self.password_service, self.toast_manager, self.app_state
        )

        # Git commands
        git_pull_cmd = GitSyncCommand(
            self.password_service, self.toast_manager, self.app_state, "pull",
            on_success_callback=lambda: self.list_controller.load_passwords()
        )
        git_push_cmd = GitSyncCommand(
            self.password_service, self.toast_manager, self.app_state, "push"
        )

        # Register commands
        self.command_invoker.register_command("copy_password", copy_password_cmd)
        self.command_invoker.register_command("copy_username", copy_username_cmd)
        self.command_invoker.register_command("delete_password", delete_cmd)
        self.command_invoker.register_command("open_url", open_url_cmd)
        self.command_invoker.register_command("git_pull", git_pull_cmd)
        self.command_invoker.register_command("git_push", git_push_cmd)

    def on_git_pull_clicked(self, widget):
        """Handle git pull using command pattern."""
        self.command_invoker.execute_command("git_pull")

    def on_git_push_clicked(self, widget):
        """Handle git push using command pattern."""
        self.command_invoker.execute_command("git_push")

    def on_edit_button_clicked(self, widget):
        selected_item_obj = self.list_controller.get_selected_item()
        if selected_item_obj:
            password_path = selected_item_obj.full_path
            is_folder_flag = selected_item_obj.is_folder

            if is_folder_flag:
                self.toast_manager.show_warning("Cannot edit a folder.")
                return

            success, content_or_error = self.password_store.get_password_content(password_path)
            if success:
                current_content = content_or_error
                # Create and show the edit dialog
                dialog = EditPasswordDialog(
                    password_path=password_path,
                    password_content=current_content,
                    transient_for_window=self
                )
                dialog.connect("save-requested", self.on_edit_dialog_save_requested)
                dialog.present()
            else:
                # content_or_error is the error message here
                self.toast_manager.show_error(f"Error fetching content: {content_or_error}")
        else:
            self.toast_manager.show_warning("No item selected to edit.")

    def on_edit_dialog_save_requested(self, dialog, path, new_content):
        # This method will call self.password_store.insert_password()
        success, message = self.password_store.insert_password(path, new_content, multiline=True, force=True)
        # The 'force=True' is important for overwriting the existing password when editing.

        if success:
            self.toast_manager.show_success(message)
            # Refresh the details view to show updated content
            selected_item = self.list_controller.get_selected_item()
            if selected_item and selected_item.full_path == path:
                self.details_controller.update_details(selected_item)
        else:
            self.toast_manager.show_error(f"Error saving: {message}")

        dialog.close() # Close the dialog after handling

    def on_remove_button_clicked(self, widget):
        selected_item_obj = self.list_controller.get_selected_item()
        if selected_item_obj:
            password_path = selected_item_obj.full_path
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
            # Note: This code needs to be updated to use the new Adw.Dialog API
            # For now, keeping the old API calls as comments for reference
            # dialog.add_response("cancel", "_Cancel")
            # dialog.add_response("delete", "_Delete")
            # dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            # dialog.set_default_response("cancel")
            dialog.connect("response", self.on_delete_confirm_response, password_path) # Pass path to handler

            # Set up proper dialog behavior
            DialogManager.setup_dialog_keyboard_navigation(dialog)
            DialogManager.center_dialog_on_parent(dialog, self)

            dialog.present()

    def on_delete_confirm_response(self, dialog, response_id, password_path):
        if response_id == "delete":
            success, message = self.password_store.delete_password(password_path)
            if success:
                self.toast_manager.show_success(message)
                self.list_controller.load_passwords() # Refresh the list
                # Clear details view after deletion
                self.details_controller.update_details(None)
            else:
                self.toast_manager.show_error(f"Error: {message}")
        dialog.close() # Ensure dialog is closed







    def on_move_rename_button_clicked(self, widget):
        selected_item_obj = self.list_controller.get_selected_item()
        if selected_item_obj:
            current_path = selected_item_obj.full_path

            dialog = MoveRenameDialog(
                current_path=current_path,
                transient_for_window=self
            )
            dialog.connect("save-requested", self.on_move_rename_dialog_save_requested)
            dialog.present()
        else:
            self.toast_manager.show_warning("No item selected to move/rename.")

    def on_move_rename_dialog_save_requested(self, dialog, old_path, new_path):
        success, message = self.password_store.move_password(old_path, new_path)

        if success:
            self.toast_manager.show_success(message)
            self.list_controller.load_passwords() # Refresh the entire list as paths have changed
            # Clear details view after move/rename
            self.details_controller.update_details(None)
        else:
            self.toast_manager.show_error(f"Error: {message}")

        dialog.close()

    def on_add_password_button_clicked(self, widget):
        suggested_path = ""
        selected_item_obj = self.list_controller.get_selected_item()
        if selected_item_obj:
            path = selected_item_obj.full_path
            is_folder_flag = selected_item_obj.is_folder
            if is_folder_flag:
                suggested_path = path
            else:
                # If a file is selected, suggest its parent folder
                suggested_path = os.path.dirname(path) if os.path.dirname(path) else ""

        dialog = AddPasswordDialog(
            transient_for_window=self,
            suggested_folder_path=suggested_path
        )
        dialog.connect("add-requested", self.on_add_dialog_add_requested)
        dialog.present()

    def on_add_dialog_add_requested(self, dialog, path, content):
        # Use force=False to prevent overwriting existing entries by mistake.
        # `pass insert` without -f will fail if the entry already exists.
        success, message = self.password_store.insert_password(path, content, multiline=True, force=False)

        if success:
            self.toast_manager.show_success(message)
            self.list_controller.load_passwords() # Refresh the list
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

        generator_dialog = PasswordGeneratorDialog(parent_window=self)
        generator_dialog.connect("password-generated", self._on_password_generated)
        generator_dialog.present()

    def _on_password_generated(self, dialog, password):
        """Handle generated password from generator dialog."""
        # Copy to clipboard
        clipboard = self.get_clipboard()
        clipboard.set(password)
        self.toast_manager.show_success("Generated password copied to clipboard")

    def _on_show_help_overlay(self, action=None, param=None):
        """Show keyboard shortcuts help overlay."""
        from .shortcuts_window import ShortcutsWindow

        shortcuts_window = ShortcutsWindow(parent_window=self)
        shortcuts_window.present()

    def _on_import_export(self, action=None, param=None):
        """Show import/export dialog."""
        from .ui.dialogs import ImportExportDialog

        import_export_dialog = ImportExportDialog(
            parent_window=self,
            password_store=self.password_store,
            toast_manager=self.toast_manager
        )
        import_export_dialog.present()
