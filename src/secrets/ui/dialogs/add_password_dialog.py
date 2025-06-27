import gi
import os  # Added for consistency with edit dialog
import random

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ..components.password_generator_popover import PasswordGeneratorPopover
from ...utils import DialogManager, UIConstants, AccessibilityHelper
from ...app_info import APP_ID

# Use SystemRandom for cryptographically secure random generation
_secure_random = random.SystemRandom()

@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/add_password_dialog.ui')
class AddPasswordDialog(Adw.Window):
    __gtype_name__ = "AddPasswordDialog"

    # Template widgets
    window_title = Gtk.Template.Child()
    folder_row = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()
    generate_button = Gtk.Template.Child()
    username_entry = Gtk.Template.Child()
    url_entry = Gtk.Template.Child()
    totp_entry = Gtk.Template.Child()
    recovery_expander = Gtk.Template.Child()
    add_recovery_button = Gtk.Template.Child()
    recovery_codes_box = Gtk.Template.Child()
    notes_view = Gtk.Template.Child()
    save_button = Gtk.Template.Child()

    # Signal: add-requested (str: path, str: content)
    sig_add_requested = GObject.Signal(name='add-requested', arg_types=[str, str])

    def __init__(self, transient_for_window, suggested_folder_path="", password_store=None, **kwargs):
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.password_store = password_store
        self.suggested_folder_path = suggested_folder_path

        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, "Add new password dialog")
        AccessibilityHelper.set_accessible_description(self, "Dialog for creating a new password entry")

        # Initialize recovery codes list
        self.recovery_codes = []

        # Create string list for folders
        self.folder_model = Gtk.StringList()
        self.folder_row.set_model(self.folder_model)

        # Populate folders
        self._populate_folders()

        # Set initial folder selection
        if self.suggested_folder_path:
            self._set_initial_folder(self.suggested_folder_path)

        # Connect signals
        self.name_entry.connect("activate", self.on_name_entry_activated)
        self.name_entry.connect("notify::text", self.on_field_changed)
        self.password_entry.connect("notify::text", self.on_field_changed)
        self.generate_button.connect("clicked", self.on_generate_password_clicked)
        self.add_recovery_button.connect("clicked", self.on_add_recovery_code_clicked)
        self.save_button.connect("clicked", self.on_save_clicked)

        # Set up dialog behavior
        self._setup_dialog_behavior()

        # Initial button state check
        self._update_save_button_state()

        # Initialize recovery expansion behavior (no codes initially)
        self._update_recovery_expansion_state()

    def _update_recovery_expansion_state(self):
        """Update recovery codes expander expansion behavior based on current codes."""
        has_codes = bool(self.recovery_codes)

        # If there are no recovery codes, disable expansion and collapse
        if not has_codes:
            self.recovery_expander.set_enable_expansion(False)
            self.recovery_expander.set_expanded(False)
        else:
            # If there are recovery codes, enable expansion and auto-expand
            self.recovery_expander.set_enable_expansion(True)
            self.recovery_expander.set_expanded(True)

    def _setup_dialog_behavior(self):
        """Set up keyboard navigation and focus management."""
        # Set up keyboard navigation
        DialogManager.setup_dialog_keyboard_navigation(self)

        # Set up focus management - focus the name entry when dialog is shown
        DialogManager.ensure_dialog_focus(self, self.name_entry)

        # Center dialog on parent
        DialogManager.center_dialog_on_parent(self)

    def _populate_folders(self):
        """Populate the folder dropdown with available folders."""
        # Add "Root" option for passwords in the root directory
        self.folder_model.append("Root")

        # Add existing folders if password store is available
        if self.password_store:
            folders = self.password_store.list_folders()
            for folder in folders:
                # Only show top-level folders for now
                if '/' not in folder:
                    self.folder_model.append(folder)

    def _set_initial_folder(self, folder_path):
        """Set the initial folder selection."""
        folder_path = folder_path.strip().strip('/')
        if not folder_path:
            folder_path = "Root"

        # Find and select the folder in the dropdown
        for i in range(self.folder_model.get_n_items()):
            item = self.folder_model.get_string(i)
            if item == folder_path:
                self.folder_row.set_selected(i)
                break

    def _get_full_path(self):
        """Construct the full path from folder and name."""
        selected_index = self.folder_row.get_selected()
        if selected_index == Gtk.INVALID_LIST_POSITION:
            folder = "Root"
        else:
            folder = self.folder_model.get_string(selected_index)

        name = self.name_entry.get_text().strip()

        if folder == "Root":
            return name
        else:
            return f"{folder}/{name}" if name else folder

    def on_field_changed(self, entry, pspec):
        """Handle changes to required fields to update save button state."""
        self._update_save_button_state()

    def _update_save_button_state(self):
        """Update save button sensitivity based on required fields."""
        name = self.name_entry.get_text().strip()
        password = self.password_entry.get_text().strip()

        # Enable save button only if both name and password are provided
        can_save = bool(name and password)
        # Note: save_button is created later, so we need to check if it exists
        if hasattr(self, 'save_button'):
            self.save_button.set_sensitive(can_save)

    def on_generate_password_clicked(self, button):
        """Open password generator popover."""
        if not hasattr(self, 'generator_popover'):
            # Create the proper PasswordGeneratorPopover component
            self.generator_popover = PasswordGeneratorPopover()
            self.generator_popover.set_parent(button)
            self.generator_popover.connect('password-generated', self.on_password_generated)

            # Ensure the popover has proper size
            self.generator_popover.set_size_request(350, 450)

        # Show the popover
        self.generator_popover.popup()

    def on_password_generated(self, popover, password):
        """Handle generated password from popover."""
        self.password_entry.set_text(password)
        self._update_save_button_state()

    def _populate_recovery_codes(self, recovery_codes):
        """Populate existing recovery codes."""
        for code in recovery_codes:
            self.on_add_recovery_code_clicked(None, code)

    def on_add_recovery_code_clicked(self, button, initial_text=""):
        """Add a new recovery code entry."""
        recovery_row = Adw.EntryRow()
        recovery_row.set_title(f"Recovery Code {len(self.recovery_codes) + 1}")
        recovery_row.set_text(initial_text)

        # Add remove button
        remove_button = Gtk.Button()
        remove_button.set_icon_name("list-remove-symbolic")
        remove_button.set_tooltip_text("Remove Recovery Code")
        remove_button.add_css_class("flat")
        remove_button.connect("clicked", lambda btn: self.on_remove_recovery_code_clicked(recovery_row))
        recovery_row.add_suffix(remove_button)

        self.recovery_codes.append(recovery_row)
        self.recovery_codes_box.append(recovery_row)

        # Update expansion behavior when adding codes
        self._update_recovery_expansion_state()

    def on_remove_recovery_code_clicked(self, recovery_row):
        """Remove a recovery code entry."""
        if recovery_row in self.recovery_codes:
            self.recovery_codes.remove(recovery_row)
            self.recovery_codes_box.remove(recovery_row)

            # Update titles for remaining codes
            for i, row in enumerate(self.recovery_codes):
                row.set_title(f"Recovery Code {i + 1}")

            # Update expansion behavior when removing codes
            self._update_recovery_expansion_state()

    def on_name_entry_activated(self, entry_row):
        # Move focus to the password entry when Enter is pressed in name entry
        self.password_entry.grab_focus()

    def on_save_clicked(self, widget):
        """Handle save button click."""
        # Get the full path from folder and name
        path = self._get_full_path()
        password = self.password_entry.get_text().strip()
        username = self.username_entry.get_text().strip()
        url = self.url_entry.get_text().strip()
        totp = self.totp_entry.get_text().strip()

        # Get notes from TextView
        notes_buffer = self.notes_view.get_buffer()
        start_iter, end_iter = notes_buffer.get_bounds()
        notes = notes_buffer.get_text(start_iter, end_iter, True).strip()

        # Get recovery codes
        recovery_codes = []
        for recovery_row in self.recovery_codes:
            code = recovery_row.get_text().strip()
            if code:
                recovery_codes.append(code)

        if not self.name_entry.get_text().strip():
            print("Password name cannot be empty.")
            self.name_entry.grab_focus()
            return

        if not password:
            print("Password cannot be empty.")
            self.password_entry.grab_focus()
            return

        # Construct the content in pass format
        content_lines = [password]  # Password is always first line

        if username:
            content_lines.append(f"username: {username}")

        if url:
            content_lines.append(url)

        if totp:
            content_lines.append(f"totp: {totp}")

        if recovery_codes:
            content_lines.append("")  # Empty line before recovery codes
            content_lines.append("Recovery Codes:")
            for code in recovery_codes:
                content_lines.append(f"- {code}")

        if notes:
            content_lines.append("")  # Empty line before notes
            content_lines.append(notes)

        content = "\n".join(content_lines)
        self.emit("add-requested", path, content)

if __name__ == '__main__': # For basic testing of the dialog itself
    app = Adw.Application(application_id="com.example.testadddialog")
    def on_activate(application):
        # Example data
        dialog = AddPasswordDialog(transient_for_window=None, suggested_folder_path="Services/Email")

        def handle_add(dialog_instance, path, content):
            print(f"Add requested for path: {path}")
            print(f"Content:\n{content}")
            dialog_instance.close() # Close after handling

        dialog.connect('add-requested', handle_add)
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
