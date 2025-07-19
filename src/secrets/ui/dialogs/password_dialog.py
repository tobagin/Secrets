"""
Unified PasswordDialog that combines add and edit functionality.

This dialog preserves the exact same design as the original add_password_dialog
while supporting both add and edit modes through a mode parameter.
"""

import gi
from typing import List, Optional

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...utils.password_strength import PasswordStrengthCalculator


@Gtk.Template(resource_path="/io/github/tobagin/secrets/ui/dialogs/password_dialog.ui")
class PasswordDialog(Adw.Window):
    """
    Unified dialog for adding and editing password entries.
    
    This dialog preserves the exact same design as the original add_password_dialog
    while supporting both add and edit modes through a mode parameter.
    """
    __gtype_name__ = "PasswordDialog"

    # Template children - these will be automatically populated by GTK
    window_title = Gtk.Template.Child()
    folder_row = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()
    generate_button = Gtk.Template.Child()
    strength_row = Gtk.Template.Child()
    strength_label = Gtk.Template.Child()
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

    # Custom signals
    __gsignals__ = {
        "password-create-requested": (GObject.SIGNAL_RUN_FIRST, None, (str, str, str, str)),
        "password-edit-requested": (GObject.SIGNAL_RUN_FIRST, None, (str, str, str, str, str)),
    }

    def __init__(self, mode: str = "add", password_path: str = "", password_content: str = "", 
                 current_color: Optional[str] = None, current_icon: Optional[str] = None,
                 suggested_folder: str = "", password_store=None, transient_for=None, **kwargs):
        """
        Initialize the password dialog.
        
        Args:
            mode: "add" for creating new passwords, "edit" for editing existing passwords
            password_path: For edit mode, the current password path
            password_content: For edit mode, the current password content
            current_color: For edit mode, the current password color
            current_icon: For edit mode, the current password icon
            suggested_folder: For add mode, suggested folder path
            password_store: Password store instance
            transient_for: Parent window
        """
        super().__init__(**kwargs)
        
        # Set transient parent if provided
        if transient_for:
            self.set_transient_for(transient_for)

        self.mode = mode
        self.password_path = password_path
        self.password_content = password_content
        self.suggested_folder = suggested_folder
        self.password_store = password_store

        # Initialize colors and icons
        self.current_color = current_color or "#3584e4"  # Default blue
        self.current_icon = current_icon or "dialog-password-symbolic"  # Default password icon
        self.selected_color = self.current_color
        self.selected_icon = self.current_icon
        
        # Setup the dialog after template is loaded
        self._setup_initial_state()

    def _setup_initial_state(self):
        """Setup initial state after template is loaded."""
        # Configure dialog based on mode
        if self.mode == "edit":
            title = "Edit Password"
            button_label = "Save"
            # Parse existing content for edit mode
            if self.password_content:
                self._populate_from_content()
        else:  # add mode
            title = "Create Password"
            button_label = "Create"
            # Set suggested folder for add mode
            if self.suggested_folder:
                self.folder_row.set_subtitle(self.suggested_folder)

        # Update UI elements
        self.set_title(title)
        if hasattr(self, 'window_title') and self.window_title:
            self.window_title.set_title(title)
        self.save_button.set_label(button_label)
        
        # Setup folder combobox with available folders
        self._setup_folder_combobox()
        
        # Setup icon combobox
        self._setup_icon_combobox()
        
        # Update color and icon avatars
        self._update_color_avatar()
        self._update_icon_avatar()

        # Connect signals
        self.name_entry.connect("notify::text", self.on_field_changed)
        self.password_entry.connect("notify::text", self.on_field_changed)
        self.password_entry.connect("notify::text", self.on_password_changed)
        self.generate_button.connect("clicked", self.on_generate_password_clicked)
        self.color_select_button.connect("clicked", self.on_color_button_clicked)
        self.add_recovery_button.connect("clicked", self.on_add_recovery_clicked)
        self.icon_row.connect("notify::selected", self.on_icon_changed)
        self.save_button.connect("clicked", self.on_save_clicked)

        # Focus appropriate field based on mode
        if self.mode == "edit":
            self.password_entry.grab_focus()
        else:
            self.name_entry.grab_focus()

    def _populate_from_content(self):
        """Populate dialog fields from existing password content."""
        try:
            # Extract password name from path
            if self.password_path:
                parts = self.password_path.split('/')
                password_name = parts[-1] if parts else ""
                folder_path = '/'.join(parts[:-1]) if len(parts) > 1 else ""
                
                self.name_entry.set_text(password_name)
                if folder_path:
                    self.folder_row.set_subtitle(folder_path)
            
            # Parse password content (simple format: first line is password, rest are key:value)
            if self.password_content:
                lines = self.password_content.strip().split('\n')
                if lines:
                    # First line is always the password
                    password = lines[0]
                    self.password_entry.set_text(password)
                    
                    # Parse additional fields
                    username = ""
                    url = ""
                    totp = ""
                    notes = ""
                    recovery_codes = []
                    
                    for line in lines[1:]:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip().lower()
                            value = value.strip()
                            
                            if key == 'username':
                                username = value
                            elif key == 'url':
                                url = value
                            elif key == 'totp':
                                totp = value
                            elif key.startswith('recovery_code'):
                                recovery_codes.append(value)
                            elif key == 'notes':
                                notes = value
                    
                    # Populate fields
                    if username:
                        self.username_entry.set_text(username)
                    if url:
                        self.url_entry.set_text(url)
                    if totp:
                        self.totp_entry.set_text(totp)
                    if recovery_codes:
                        for code in recovery_codes:
                            self._add_recovery_code_to_box(code)
                    if notes:
                        buffer = self.notes_view.get_buffer()
                        buffer.set_text(notes)
                
        except Exception as e:
            print(f"Error parsing password content: {e}")

    def _setup_folder_combobox(self):
        """Setup the folder combobox with available folders."""
        if not self.password_store:
            return
            
        # Get all folders from the password store
        folders = self.password_store.list_folders()
        
        # Create string list for the combo row
        string_list = Gtk.StringList()
        string_list.append("Root")  # Add root option
        
        for folder in sorted(folders):
            string_list.append(folder)
        
        # Set the model for the combo row
        self.folder_row.set_model(string_list)
        
        # Set default selection
        if self.suggested_folder:
            # Find and select the suggested folder
            for i in range(string_list.get_n_items()):
                if string_list.get_string(i) == self.suggested_folder:
                    self.folder_row.set_selected(i)
                    break
        else:
            self.folder_row.set_selected(0)  # Select "Root"
    
    def _setup_icon_combobox(self):
        """Setup the icon combobox with available icons."""
        from ...utils.avatar_manager import AvatarManager
        
        # Initialize avatar manager if not already done
        if not hasattr(self, 'avatar_manager'):
            self.avatar_manager = AvatarManager()
        
        # Setup icon combo with comprehensive icon set
        self.avatar_manager.setup_icon_combo_row(
            self.icon_row,
            icon_set="password",  # Use password-specific icons
            selected_icon=self.current_icon
        )
        
    def _update_color_avatar(self):
        """Update the color avatar."""
        from ..widgets.color_paintable import ColorPaintable
        
        # Create color paintable
        color_paintable = ColorPaintable(self.selected_color)
        self.color_avatar.set_custom_image(color_paintable)
        
    def _update_icon_avatar(self):
        """Update the icon avatar."""
        from ..widgets.color_paintable import ColorPaintable
        
        # Create transparent paintable with icon
        icon_paintable = ColorPaintable("transparent", self.selected_icon)
        self.icon_avatar.set_custom_image(icon_paintable)
    
    def _add_recovery_code_to_box(self, code: str):
        """Add a recovery code to the recovery codes box."""
        # Count existing recovery codes
        code_count = 0
        child = self.recovery_codes_box.get_first_child()
        while child:
            if isinstance(child, Adw.EntryRow):
                code_count += 1
            child = child.get_next_sibling()
        
        # Create entry row for the recovery code
        entry_row = Adw.EntryRow()
        entry_row.set_title(f"Recovery Code {code_count + 1}")
        entry_row.set_text(code)
        
        # Add remove button
        remove_button = Gtk.Button()
        remove_button.set_icon_name("list-remove-symbolic")
        remove_button.add_css_class("flat")
        remove_button.connect("clicked", lambda btn: self._remove_recovery_code(entry_row))
        entry_row.add_suffix(remove_button)
        
        # Add to box
        self.recovery_codes_box.append(entry_row)
        
        # Enable expansion if we have codes
        self.recovery_expander.set_enable_expansion(True)

    def on_field_changed(self, entry, pspec):
        """Handle text field changes."""
        # Enable save button if both name and password are filled
        name_text = self.name_entry.get_text().strip()
        password_text = self.password_entry.get_text()
        self.save_button.set_sensitive(bool(name_text and password_text))

    def on_password_changed(self, entry, pspec):
        """Handle password field changes to update strength indicator."""
        password = self.password_entry.get_text()
        self._update_password_strength(password)

    def _update_password_strength(self, password):
        """Update the password strength indicator."""
        if not password:
            self.strength_label.set_text("Enter password")
            self.strength_label.remove_css_class("error")
            self.strength_label.remove_css_class("warning")
            self.strength_label.remove_css_class("accent")
            self.strength_label.remove_css_class("success")
            self.strength_label.add_css_class("dim-label")
            return

        # Calculate strength using the advanced calculator
        score, strength_text = PasswordStrengthCalculator.calculate_strength(password, False)
        
        self.strength_label.set_text(strength_text)
        
        # Update CSS classes based on strength (0-4 scale)
        self.strength_label.remove_css_class("error")
        self.strength_label.remove_css_class("warning") 
        self.strength_label.remove_css_class("accent")
        self.strength_label.remove_css_class("success")
        self.strength_label.remove_css_class("dim-label")
        
        if score <= 0:  # Very Weak
            css_class = "error"
        elif score == 1:  # Weak
            css_class = "error"
        elif score == 2:  # Fair
            css_class = "warning"
        elif score == 3:  # Good
            css_class = "accent"
        else:  # Strong (4)
            css_class = "success"
            
        self.strength_label.add_css_class(css_class)

    def on_generate_password_clicked(self, button):
        """Handle password generation button click."""
        # Import here to avoid circular imports
        from .password_generator_dialog import PasswordGeneratorDialog
        
        # Create and show password generator dialog with from_dialog=True
        generator_dialog = PasswordGeneratorDialog(transient_for=self, from_dialog=True)
        generator_dialog.connect('password-generated', self._on_password_generated)
        generator_dialog.present()

    def _on_password_generated(self, dialog, password):
        """Handle password generated from dialog."""
        self.password_entry.set_text(password)
        self._update_password_strength(password)
        dialog.close()

    def on_color_button_clicked(self, button):
        """Handle color selection button click."""
        color_dialog = Gtk.ColorChooserDialog()
        color_dialog.set_transient_for(self)
        color_dialog.set_modal(True)
        color_dialog.set_title("Choose Password Color")

        # Set current color
        from gi.repository import Gdk
        rgba = Gdk.RGBA()
        rgba.parse(self.selected_color)
        color_dialog.set_rgba(rgba)

        color_dialog.connect("response", self._on_color_dialog_response)
        color_dialog.present()
        
    def _on_color_dialog_response(self, dialog, response_id):
        """Handle color dialog response."""
        if response_id == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            # Convert RGBA to hex
            self.selected_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
            self._update_color_avatar()
        dialog.destroy()
        
    def on_icon_changed(self, combo_row, pspec):
        """Handle icon selection changes."""
        if hasattr(self, 'avatar_manager'):
            self.selected_icon = self.avatar_manager.get_selected_icon_from_combo(combo_row)
            if self.selected_icon:
                self._update_icon_avatar()
                
    def on_add_recovery_clicked(self, button):
        """Handle add recovery code button click."""
        # Add empty recovery code entry
        self._add_recovery_code_to_box("")
        
    def _remove_recovery_code(self, entry_row):
        """Remove a recovery code entry."""
        self.recovery_codes_box.remove(entry_row)
        
        # Disable expansion if no codes remain
        if not self.recovery_codes_box.get_first_child():
            self.recovery_expander.set_enable_expansion(False)

    def on_save_clicked(self, button):
        """Handle save button click."""
        # Get form data
        # Get selected folder from combo
        selected_index = self.folder_row.get_selected()
        if selected_index != Gtk.INVALID_LIST_POSITION:
            model = self.folder_row.get_model()
            if model and selected_index < model.get_n_items():
                folder = model.get_string(selected_index)
                if folder == "Root":
                    folder = ""
            else:
                folder = ""
        else:
            folder = ""
            
        name = self.name_entry.get_text().strip()
        password = self.password_entry.get_text()
        username = self.username_entry.get_text().strip()
        url = self.url_entry.get_text().strip()
        totp = self.totp_entry.get_text().strip()
        
        # Get notes
        buffer = self.notes_view.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        notes = buffer.get_text(start_iter, end_iter, False).strip()
        
        # Get recovery codes
        recovery_codes = []
        child = self.recovery_codes_box.get_first_child()
        while child:
            if isinstance(child, Adw.EntryRow):
                code = child.get_text().strip()
                if code:
                    recovery_codes.append(code)
            child = child.get_next_sibling()

        # Build full path
        if folder:
            full_path = f"{folder}/{name}"
        else:
            full_path = name

        # Build password content - simple format for now
        content_lines = [password]
        if username:
            content_lines.append(f"username: {username}")
        if url:
            content_lines.append(f"url: {url}")
        if totp:
            content_lines.append(f"totp: {totp}")
        if recovery_codes:
            for i, code in enumerate(recovery_codes):
                content_lines.append(f"recovery_code_{i+1}: {code}")
        if notes:
            content_lines.append(f"notes: {notes}")
        content = "\n".join(content_lines)
        
        # Get color and icon
        color = self.selected_color
        icon = self.selected_icon

        # Emit appropriate signal based on mode
        if self.mode == "edit":
            self.emit("password-edit-requested", self.password_path, full_path, content, color, icon)
        else:
            self.emit("password-create-requested", full_path, content, color, icon)


if __name__ == '__main__':
    # Basic testing of the dialog
    app = Adw.Application(application_id="com.example.testpassworddialog")

    def on_activate(application):
        # Test add mode
        add_dialog = PasswordDialog(
            mode="add",
            suggested_folder="websites",
            transient_for=None
        )

        def handle_create(dialog_instance, path, content, color, icon):
            print(f"Create password requested: {path}, color: {color}, icon: {icon}")
            dialog_instance.close()
            
            # Test edit mode
            edit_dialog = PasswordDialog(
                mode="edit",
                password_path="websites/example.com",
                password_content="mypassword123\nusername: john@example.com\nurl: https://example.com",
                current_color="#33d17a",
                current_icon="web-browser-symbolic",
                transient_for=None
            )
            
            def handle_edit(dialog_instance, old_path, new_path, content, color, icon):
                print(f"Edit password requested: {old_path} -> {new_path}, color: {color}, icon: {icon}")
                dialog_instance.close()
                application.quit()
            
            edit_dialog.connect('password-edit-requested', handle_edit)
            edit_dialog.present()

        add_dialog.connect('password-create-requested', handle_create)
        add_dialog.present()

    app.connect("activate", on_activate)
    app.run([])