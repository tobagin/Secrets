import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gio
from ..widgets.color_paintable import ColorPaintable
from ...app_info import APP_ID
from ..widgets import ColorPicker, IconPicker


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/add_folder_dialog.ui')
class AddFolderDialog(Adw.Window):
    """Dialog for creating new folders in the password store."""

    __gtype_name__ = "AddFolderDialog"

    # Template widgets
    create_button = Gtk.Template.Child()
    path_entry = Gtk.Template.Child()
    color_row = Gtk.Template.Child()
    color_avatar = Gtk.Template.Child()
    color_select_button = Gtk.Template.Child()
    icon_row = Gtk.Template.Child()
    icon_avatar = Gtk.Template.Child()

    # Define custom signals
    __gsignals__ = {
        "folder-create-requested": (GObject.SIGNAL_RUN_FIRST, None, (str, str, str)),
    }

    def __init__(self, transient_for_window=None, suggested_parent_path="", **kwargs):
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.suggested_parent_path = suggested_parent_path

        # Initialize color and icon
        self.selected_color = "#3584e4"  # Default blue
        self.selected_icon = "folder-symbolic"  # Default folder icon

        # Create color paintable for avatar
        self.color_paintable = ColorPaintable(self.selected_color, self.selected_icon)

        # Icon options for folders
        self.folder_icons = [
            ("folder-symbolic", "Folder"),
            ("folder-documents-symbolic", "Documents"),
            ("folder-download-symbolic", "Downloads"),
            ("folder-music-symbolic", "Music"),
            ("folder-pictures-symbolic", "Pictures"),
            ("folder-videos-symbolic", "Videos"),
            ("folder-publicshare-symbolic", "Public"),
            ("user-home-symbolic", "Home"),
            ("applications-games-symbolic", "Games"),
            ("preferences-system-symbolic", "System"),
            ("network-workgroup-symbolic", "Network"),
            ("folder-remote-symbolic", "Remote"),
        ]

        self._setup_initial_state()

    def _setup_initial_state(self):
        """Setup initial state after template is loaded."""
        # Connect signals programmatically to ensure they work
        self.path_entry.connect("notify::text", self.on_path_changed)
        self.create_button.connect("clicked", self.on_create_clicked)

        # Connect color button and icon row signals
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

        # Pre-fill with suggested parent path if provided
        if self.suggested_parent_path:
            if not self.suggested_parent_path.endswith('/'):
                self.suggested_parent_path += '/'
            self.path_entry.set_text(self.suggested_parent_path)

        # Focus the path entry
        self.path_entry.grab_focus()

        # Initial check for button state
        self._update_button_state()

    def _update_button_state(self):
        """Update the create button state based on current text."""
        path = self.path_entry.get_text().strip()
        self.create_button.set_sensitive(bool(path))

    def on_path_changed(self, entry, pspec):
        """Handle path entry changes to enable/disable create button."""
        self._update_button_state()

    def _setup_icon_combo(self):
        """Setup the icon combo row with available icons."""
        # Create a list store with icon names
        list_store = Gio.ListStore.new(Gtk.StringObject)
        for icon_name, display_name in self.folder_icons:
            list_store.append(Gtk.StringObject.new(icon_name))

        self.icon_row.set_model(list_store)

        # Set up the factory to display icons instead of text
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_icon_item_setup)
        factory.connect("bind", self._on_icon_item_bind)
        self.icon_row.set_factory(factory)

        # Set default selection (first item - folder-symbolic)
        self.icon_row.set_selected(0)

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
        dialog.destroy()

    def on_icon_changed(self, combo_row, pspec):
        """Handle icon selection changes."""
        selected_index = self.icon_row.get_selected()
        if selected_index < len(self.folder_icons):
            self.selected_icon = self.folder_icons[selected_index][0]
            self._update_icon_avatar()

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

    def on_path_activated(self, entry):
        """Handle Enter key in path entry."""
        if self.create_button.get_sensitive():
            self.on_create_clicked(None)

    def on_create_clicked(self, widget):
        """Handle create button click."""
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

        # Emit the signal with the folder path, color, and icon
        self.emit("folder-create-requested", path, selected_color, selected_icon)




if __name__ == '__main__':
    # Basic testing of the dialog
    app = Adw.Application(application_id="com.example.testaddfolderdialog")

    def on_activate(application):
        dialog = AddFolderDialog(transient_for_window=None, suggested_parent_path="websites")

        def handle_create(dialog_instance, folder_path, color, icon):
            print(f"Create folder requested: {folder_path}, color: {color}, icon: {icon}")
            dialog_instance.close()

        dialog.connect('folder-create-requested', handle_create)
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
