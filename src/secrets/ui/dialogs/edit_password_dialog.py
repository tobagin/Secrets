import gi
import os # Added for os.path.basename
import random

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gio
from ..widgets.color_paintable import ColorPaintable
from ...utils import DialogManager, UIConstants, AccessibilityHelper
from ..components.password_generator_popover import PasswordGeneratorPopover
from ...app_info import APP_ID
from ..widgets import ColorPicker, IconPicker

# Use SystemRandom for cryptographically secure random generation
_secure_random = random.SystemRandom()

@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/edit_password_dialog.ui')
class EditPasswordDialog(Adw.Window):
    __gtype_name__ = "EditPasswordDialog"

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
    color_row = Gtk.Template.Child()
    color_avatar = Gtk.Template.Child()
    color_select_button = Gtk.Template.Child()
    icon_row = Gtk.Template.Child()
    icon_avatar = Gtk.Template.Child()
    notes_view = Gtk.Template.Child()
    save_button = Gtk.Template.Child()

    # Define a signal that the dialog can emit when save is attempted
    # The signal will carry the old path, new path, new content, color, and icon.
    # This allows handling both content changes and path/name changes.
    sig_save_requested = GObject.Signal(name='save-requested', arg_types=[str, str, str, str, str])

    def __init__(self, password_path, password_content, transient_for_window, password_store=None, current_color=None, current_icon=None, **kwargs):
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.password_path = password_path
        self.initial_content = password_content
        self.password_store = password_store
        self.current_color = current_color or "#3584e4"  # Default blue
        self.current_icon = current_icon or "dialog-password-symbolic"  # Default password icon

        # Configure dialog title
        title = f"Edit: {os.path.basename(password_path)}"
        self.set_title(title)
        self.window_title.set_title(title)

        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, f"Edit password dialog for {os.path.basename(password_path)}")
        AccessibilityHelper.set_accessible_description(self, "Dialog for editing password entry content")

        # Initialize recovery codes list
        self.recovery_codes = []

        # Initialize color and icon
        self.selected_color = self.current_color
        self.selected_icon = self.current_icon

        # Create color paintable for avatar
        self.color_paintable = ColorPaintable(self.selected_color)

        # Icon options for passwords
        self.password_icons = [
            ("dialog-password-symbolic", "Password"),
            ("network-server-symbolic", "Server"),
            ("web-browser-symbolic", "Website"),
            ("mail-send-symbolic", "Email"),
            ("applications-games-symbolic", "Game"),
            ("preferences-system-symbolic", "System"),
            ("network-workgroup-symbolic", "Network"),
            ("document-edit-symbolic", "Document"),
            ("applications-multimedia-symbolic", "Media"),
            ("applications-development-symbolic", "Development"),
            ("user-info-symbolic", "Personal"),
            ("emblem-important-symbolic", "Important"),
        ]

        # Create string list for folders
        self.folder_model = Gtk.StringList()
        self.folder_row.set_model(self.folder_model)

        # Parse current path into folder and name
        current_folder, current_name = self._parse_path(self.password_path)

        # Populate folders
        self._populate_folders()

        # Set current folder selection
        self._set_current_folder(current_folder)

        # Set current name
        self.name_entry.set_text(current_name)

        # Parse the initial content to populate fields
        parsed_content = self._parse_password_content(self.initial_content)

        # Populate fields with parsed content
        self.password_entry.set_text(parsed_content.get('password', ''))
        self.username_entry.set_text(parsed_content.get('username', ''))
        self.url_entry.set_text(parsed_content.get('url', ''))
        self.totp_entry.set_text(parsed_content.get('totp', ''))

        # Set notes content
        notes_buffer = self.notes_view.get_buffer()
        notes_buffer.set_text(parsed_content.get('notes', ''))

        # Connect signals
        self.generate_button.connect("clicked", self.on_generate_password_clicked)
        self.add_recovery_button.connect("clicked", self.on_add_recovery_code_clicked)
        self.save_button.connect("clicked", self.on_save_clicked)

        # Connect color and icon signals
        self.color_select_button.connect("clicked", self.on_color_button_clicked)
        self.icon_row.connect("notify::selected", self.on_icon_changed)

        # Setup icon combo row
        self._setup_icon_combo()

        # Update avatars
        self._update_color_avatar()
        self._update_icon_avatar()

        # Connect to theme changes to update icon avatar
        style_manager = Adw.StyleManager.get_default()
        style_manager.connect("notify::dark", self._on_theme_changed)

        # Populate existing recovery codes and set expansion behavior
        recovery_codes = parsed_content.get('recovery_codes', [])
        self._populate_recovery_codes(recovery_codes)
        self._update_recovery_expansion(recovery_codes)

        # Set initial color and icon values (handled by setup methods)
        # Color and icon are set up in _setup_color_combo and _setup_icon_combo

        # Set up dialog behavior
        self._setup_dialog_behavior()

    def _update_recovery_expansion(self, recovery_codes):
        """Update recovery codes expander expansion behavior based on content."""
        has_codes = bool(recovery_codes)

        # If there are no recovery codes, disable expansion
        if not has_codes:
            self.recovery_expander.set_enable_expansion(False)
            self.recovery_expander.set_expanded(False)
        else:
            # If there are recovery codes, enable expansion and auto-expand
            self.recovery_expander.set_enable_expansion(True)
            self.recovery_expander.set_expanded(True)

    def _parse_password_content(self, content):
        """Parse password content into structured fields."""
        lines = content.splitlines()
        parsed = {
            'password': '',
            'username': '',
            'url': '',
            'totp': '',
            'recovery_codes': [],
            'notes': ''
        }

        if not lines:
            return parsed

        # First line is always the password
        parsed['password'] = lines[0]

        # Process remaining lines
        remaining_lines = lines[1:]
        notes_lines = []
        in_recovery_section = False

        for line in remaining_lines:
            line_stripped = line.strip()

            if not line_stripped:
                if not in_recovery_section:
                    notes_lines.append('')
                continue

            # Check for recovery codes section
            if line_stripped.lower() == "recovery codes:":
                in_recovery_section = True
                continue

            # If in recovery section, collect codes
            if in_recovery_section:
                if line_stripped.startswith('- '):
                    parsed['recovery_codes'].append(line_stripped[2:])
                    continue
                else:
                    # End of recovery section
                    in_recovery_section = False

            # Check for username patterns
            if line_stripped.lower().startswith(('username:', 'user:', 'login:')):
                if not parsed['username']:  # Take first username found
                    parsed['username'] = line_stripped.split(':', 1)[1].strip()
                continue

            # Check for TOTP patterns
            if line_stripped.lower().startswith('totp:'):
                if not parsed['totp']:  # Take first TOTP found
                    parsed['totp'] = line_stripped.split(':', 1)[1].strip()
                continue

            # Check for URL patterns
            if line_stripped.lower().startswith(('url:', 'website:')):
                if not parsed['url']:  # Take first URL found
                    parsed['url'] = line_stripped.split(':', 1)[1].strip()
                continue

            # Check for direct URL patterns (legacy format)
            if line_stripped.startswith(('http://', 'https://', 'www.')):
                if not parsed['url']:  # Take first URL found
                    parsed['url'] = line_stripped
                continue

            # Everything else goes to notes (if not in recovery section)
            if not in_recovery_section:
                notes_lines.append(line_stripped)

        # Join notes, removing empty lines at start/end
        notes = '\n'.join(notes_lines).strip()
        parsed['notes'] = notes

        return parsed

    def _parse_path(self, path):
        """Parse a path into folder and name components."""
        if '/' in path:
            parts = path.split('/')
            folder = '/'.join(parts[:-1])
            name = parts[-1]
        else:
            folder = "Root"
            name = path
        return folder, name

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

    def _set_current_folder(self, folder_path):
        """Set the current folder selection."""
        if not folder_path:
            folder_path = "Root"

        # Find and select the folder in the dropdown
        for i in range(self.folder_model.get_n_items()):
            item = self.folder_model.get_string(i)
            if item == folder_path:
                self.folder_row.set_selected(i)
                break

    def _get_new_path(self):
        """Construct the new path from folder and name."""
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

    def _setup_dialog_behavior(self):
        """Set up keyboard navigation and focus management."""
        # Set up keyboard navigation
        DialogManager.setup_dialog_keyboard_navigation(self)

        # Set up focus management - focus the password entry when dialog is shown
        DialogManager.ensure_dialog_focus(self, self.password_entry)

        # Center dialog on parent
        DialogManager.center_dialog_on_parent(self)

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

    def _setup_icon_combo(self):
        """Setup the icon combo row with available icons."""
        # Create a list store with icon names
        list_store = Gio.ListStore.new(Gtk.StringObject)
        for icon_name, display_name in self.password_icons:
            list_store.append(Gtk.StringObject.new(icon_name))

        self.icon_row.set_model(list_store)

        # Set up the factory to display icons instead of text
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_icon_item_setup)
        factory.connect("bind", self._on_icon_item_bind)
        self.icon_row.set_factory(factory)

        # Set current selection based on current icon
        current_index = 0
        for i, (icon_name, _) in enumerate(self.password_icons):
            if icon_name == self.current_icon:
                current_index = i
                break
        self.icon_row.set_selected(current_index)

    def on_color_button_clicked(self, button):
        """Handle color button click - show color chooser dialog."""
        color_dialog = Gtk.ColorChooserDialog()
        color_dialog.set_transient_for(self)
        color_dialog.set_modal(True)
        color_dialog.set_title("Choose Password Color")

        # Set current color
        from gi.repository import Gdk
        rgba = Gdk.RGBA()
        rgba.parse(self.selected_color)
        color_dialog.set_rgba(rgba)

        color_dialog.connect("response", self.on_color_dialog_response)
        color_dialog.present()

    def on_color_dialog_response(self, dialog, response_id):
        """Handle color dialog response."""
        if response_id == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            # Convert RGBA to hex
            self.selected_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
            self._update_color_avatar()
            self._update_save_button_state()
        dialog.destroy()

    def on_icon_changed(self, combo_row, pspec):
        """Handle icon selection changes."""
        selected_index = self.icon_row.get_selected()
        if selected_index < len(self.password_icons):
            self.selected_icon = self.password_icons[selected_index][0]
            self._update_icon_avatar()
            self._update_save_button_state()

    def _update_color_avatar(self):
        """Update the color avatar using custom paintable."""
        self.color_paintable.set_color(self.selected_color)
        self.color_avatar.set_custom_image(self.color_paintable)

    def _update_icon_avatar(self):
        """Update the icon avatar with transparent background."""
        # Create a transparent paintable with just the icon
        icon_paintable = ColorPaintable("transparent", self.selected_icon)
        self.icon_avatar.set_custom_image(icon_paintable)

    def _on_icon_item_setup(self, factory, list_item):
        """Setup the icon list item widget."""
        image = Gtk.Image()
        image.set_icon_size(Gtk.IconSize.INHERIT)
        image.set_pixel_size(16)  # Standard icon size
        list_item.set_child(image)

    def _on_icon_item_bind(self, factory, list_item):
        """Bind the icon to the list item."""
        string_object = list_item.get_item()
        icon_name = string_object.get_string()
        image = list_item.get_child()
        image.set_from_icon_name(icon_name)

    def _on_theme_changed(self, style_manager, param):
        """Handle theme changes to update icon avatar."""
        self._update_icon_avatar()

    def _update_save_button_state(self):
        """Update the save button state based on form validity."""
        # Check if required fields are filled
        name_text = self.name_entry.get_text().strip()
        password_text = self.password_entry.get_text().strip()

        # Enable save button if name and password are provided
        is_valid = bool(name_text and password_text)
        self.save_button.set_sensitive(is_valid)

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

    def on_save_clicked(self, widget):
        """Handle save button click."""
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

        # Get the new path
        new_path = self._get_new_path()

        # Construct the content in pass format
        content_lines = [password]  # Password is always first line

        if username:
            content_lines.append(f"username: {username}")

        if url:
            # Always save URL with url: prefix for consistency
            content_lines.append(f"url: {url}")

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

        new_content = "\n".join(content_lines)

        # Get selected color and icon
        selected_color = self.selected_color
        selected_icon = self.selected_icon

        # Emit the signal with old path, new path, new content, color, and icon
        self.emit("save-requested", self.password_path, new_path, new_content, selected_color, selected_icon)

if __name__ == '__main__': # For basic testing of the dialog itself
    # import os # Already at module level

    app = Adw.Application(application_id="com.example.testdialog")
    def on_activate(application):
        # Example data
        test_path = "Services/TestPassword"
        test_content = "this is the password\nline2\nline3"

        dialog = EditPasswordDialog(test_path, test_content, transient_for_window=None)

        def handle_save(dialog_instance, old_path, new_path, content, color, icon):
            print(f"Save requested for path: {old_path} -> {new_path}")
            print(f"New content:\n{content}")
            print(f"Color: {color}, Icon: {icon}")
            dialog_instance.close() # Close after handling

        dialog.connect('save-requested', handle_save)
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
