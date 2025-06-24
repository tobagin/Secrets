import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/add_folder_dialog.ui')
class AddFolderDialog(Adw.Window):
    """Dialog for creating new folders in the password store."""

    __gtype_name__ = "AddFolderDialog"

    # Template widgets
    create_button = Gtk.Template.Child()
    path_entry = Gtk.Template.Child()

    # Define custom signals
    __gsignals__ = {
        "folder-create-requested": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    def __init__(self, transient_for_window=None, suggested_parent_path="", **kwargs):
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.suggested_parent_path = suggested_parent_path
        self._setup_initial_state()

    def _setup_initial_state(self):
        """Setup initial state after template is loaded."""
        # Connect signals programmatically to ensure they work
        self.path_entry.connect("notify::text", self.on_path_changed)
        self.create_button.connect("clicked", self.on_create_clicked)

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

        # Emit the signal with the folder path
        self.emit("folder-create-requested", path)




if __name__ == '__main__':
    # Basic testing of the dialog
    app = Adw.Application(application_id="com.example.testaddfolderdialog")

    def on_activate(application):
        dialog = AddFolderDialog(transient_for_window=None, suggested_parent_path="websites")

        def handle_create(dialog_instance, folder_path):
            print(f"Create folder requested: {folder_path}")
            dialog_instance.close()

        dialog.connect('folder-create-requested', handle_create)
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
