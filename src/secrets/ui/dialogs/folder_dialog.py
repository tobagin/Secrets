import gi
from typing import Optional

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ..widgets.color_paintable import ColorPaintable
from ...utils.avatar_manager import AvatarManager


@Gtk.Template(resource_path="/io/github/tobagin/secrets/ui/dialogs/folder_dialog.ui")
class FolderDialog(Adw.Window):
    """Unified dialog for creating and editing folders in the password store."""

    __gtype_name__ = "FolderDialog"

    # Template widgets
    window_title = Gtk.Template.Child()
    path_entry = Gtk.Template.Child()
    color_row = Gtk.Template.Child()
    color_avatar = Gtk.Template.Child()
    color_select_button = Gtk.Template.Child()
    icon_row = Gtk.Template.Child()
    icon_avatar = Gtk.Template.Child()
    primary_button = Gtk.Template.Child()

    # Define custom signals
    __gsignals__ = {
        "folder-create-requested": (GObject.SIGNAL_RUN_FIRST, None, (str, str, str)),
        "folder-edit-requested": (GObject.SIGNAL_RUN_FIRST, None, (str, str, str, str)),
    }

    def __init__(self, mode: str = "add", folder_path: str = "", current_color: Optional[str] = None, 
                 current_icon: Optional[str] = None, transient_for_window: Optional[Gtk.Window] = None, 
                 suggested_parent_path: str = "", **kwargs):
        """
        Initialize the folder dialog.
        
        Args:
            mode: "add" for creating new folders, "edit" for editing existing folders
            folder_path: For edit mode, the current folder path
            current_color: For edit mode, the current folder color
            current_icon: For edit mode, the current folder icon
            transient_for_window: Parent window
            suggested_parent_path: For add mode, suggested parent path
        """
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.mode = mode
        self.original_folder_path = folder_path if mode == "edit" else ""
        self.suggested_parent_path = suggested_parent_path
        
        # Initialize colors and icons
        self.current_color = current_color or "#fd7e14"  # Default orange for folders
        self.current_icon = current_icon or "folder-symbolic"  # Default folder icon
        self.selected_color = self.current_color
        self.selected_icon = self.current_icon

        # Create color paintable for avatar
        self.color_paintable = ColorPaintable(self.selected_color)

        # Initialize avatar manager for comprehensive icon selection
        self.avatar_manager = AvatarManager()
        
        self._setup_initial_state()

    def _setup_initial_state(self):
        """Setup initial state after template is loaded."""
        # Configure dialog based on mode
        if self.mode == "edit":
            title = "Edit Folder"
            description = f"Edit folder: {self.original_folder_path}"
            self.primary_button.set_label("Save")
            self.path_entry.set_text(self.original_folder_path)
        else:  # add mode
            title = "Create New Folder"
            description = "Create a new folder to organize your passwords"
            self.primary_button.set_label("Create")
            # Pre-fill with suggested parent path if provided
            if self.suggested_parent_path:
                if not self.suggested_parent_path.endswith('/'):
                    self.suggested_parent_path += '/'
                self.path_entry.set_text(self.suggested_parent_path)

        self.set_title(title)
        self.window_title.set_title(title)
        
        # Connect signals
        self.path_entry.connect("notify::text", self.on_path_changed)
        self.path_entry.connect("activate", self.on_path_activated)
        self.primary_button.connect("clicked", self.on_primary_button_clicked)
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

        # Focus the path entry
        self.path_entry.grab_focus()

        # Initial check for button state
        self._update_button_state()

    def _update_button_state(self):
        """Update the primary button state based on current text and changes."""
        path = self.path_entry.get_text().strip()

        if self.mode == "edit":
            # For edit mode, enable if path is not empty
            # Changes in color/icon are always allowed
            self.primary_button.set_sensitive(bool(path))
        else:
            # For add mode, enable if path is not empty
            self.primary_button.set_sensitive(bool(path))

    def on_path_changed(self, entry, pspec):
        """Handle path entry changes to enable/disable primary button."""
        self._update_button_state()

    def _setup_icon_combo(self):
        """Setup the icon combo row with available icons using AvatarManager."""
        # Use AvatarManager to setup icon selection with all available icons
        self.avatar_manager.setup_icon_combo_row(
            self.icon_row, 
            icon_set="folder",  # Uses the comprehensive icon set
            selected_icon=self.current_icon
        )

    def on_color_button_clicked(self, button):
        """Handle color button click - show color chooser dialog."""
        color_dialog = Gtk.ColorChooserDialog()
        color_dialog.set_transient_for(self)
        color_dialog.set_modal(True)
        color_dialog.set_title("Choose Folder Color")

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
            self._update_button_state()
        dialog.destroy()

    def on_icon_changed(self, combo_row, pspec):
        """Handle icon selection changes."""
        self.selected_icon = self.avatar_manager.get_selected_icon_from_combo(combo_row)
        if self.selected_icon:
            self._update_icon_avatar()
            self._update_button_state()

    def _update_color_avatar(self):
        """Update the color avatar using custom paintable."""
        self.color_paintable.set_color(self.selected_color)
        self.color_avatar.set_custom_image(self.color_paintable)

    def _update_icon_avatar(self):
        """Update the icon avatar with transparent background."""
        # Create a transparent paintable with just the icon
        icon_paintable = ColorPaintable("transparent", self.selected_icon)
        self.icon_avatar.set_custom_image(icon_paintable)

    def _on_theme_changed(self, style_manager, param):
        """Handle theme changes to update icon avatar."""
        self._update_icon_avatar()

    def on_path_activated(self, entry):
        """Handle Enter key in path entry."""
        if self.primary_button.get_sensitive():
            self.on_primary_button_clicked(None)

    def on_primary_button_clicked(self, widget):
        """Handle primary button click (Create or Save)."""
        path = self.path_entry.get_text().strip()

        if not path:
            # This shouldn't happen due to button sensitivity, but just in case
            self.path_entry.grab_focus()
            return

        # Clean the path (remove leading/trailing slashes)
        path = path.strip('/')

        if not path:
            # Path was only slashes
            self.path_entry.grab_focus()
            return

        # Get selected color and icon
        selected_color = self.selected_color
        selected_icon = self.selected_icon

        # Emit the appropriate signal based on mode
        if self.mode == "edit":
            # Emit edit signal with old path, new path, color, and icon
            self.emit("folder-edit-requested", self.original_folder_path, path, selected_color, selected_icon)
        else:
            # Emit create signal with path, color, and icon
            self.emit("folder-create-requested", path, selected_color, selected_icon)


if __name__ == '__main__':
    # Basic testing of the dialog
    app = Adw.Application(application_id="com.example.testfolderdialog")

    def on_activate(application):
        # Test add mode
        add_dialog = FolderDialog(
            mode="add",
            transient_for_window=None, 
            suggested_parent_path="websites"
        )

        def handle_create(dialog_instance, folder_path, color, icon):
            print(f"Create folder requested: {folder_path}, color: {color}, icon: {icon}")
            dialog_instance.close()
            
            # Test edit mode
            edit_dialog = FolderDialog(
                mode="edit",
                folder_path="websites/social",
                current_color="#33d17a",
                current_icon="system-users-symbolic",
                transient_for_window=None
            )
            
            def handle_edit(dialog_instance, old_path, new_path, color, icon):
                print(f"Edit folder requested: {old_path} -> {new_path}, color: {color}, icon: {icon}")
                dialog_instance.close()
                application.quit()
            
            edit_dialog.connect('folder-edit-requested', handle_edit)
            edit_dialog.present()

        add_dialog.connect('folder-create-requested', handle_create)
        add_dialog.present()

    app.connect("activate", on_activate)
    app.run([])