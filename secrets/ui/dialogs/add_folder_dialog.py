import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/add_folder_dialog.ui')
class AddFolderDialog(Adw.Dialog):
    """Dialog for creating new folders in the password store."""

    __gtype_name__ = "AddFolderDialog"

    # Template widgets
    cancel_button = Gtk.Template.Child()
    create_button = Gtk.Template.Child()
    path_entry = Gtk.Template.Child()

    # Define custom signals
    __gsignals__ = {
        "folder-create-requested": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    def __init__(self, transient_for_window=None, suggested_parent_path="", **kwargs):
        super().__init__(**kwargs)

        # AdwDialog doesn't have set_transient_for, but we can present it on the parent
        self.transient_for_window = transient_for_window
        self.suggested_parent_path = suggested_parent_path
        self._setup_initial_state()

    def present(self):
        """Present the dialog, optionally with a parent window."""
        if self.transient_for_window:
            super().present(self.transient_for_window)
        else:
            super().present()

    def _setup_initial_state(self):
        """Setup initial state after template is loaded."""
        # Pre-fill with suggested parent path if provided
        if self.suggested_parent_path:
            if not self.suggested_parent_path.endswith('/'):
                self.suggested_parent_path += '/'
            self.path_entry.set_text(self.suggested_parent_path)

        # Focus the path entry
        self.path_entry.grab_focus()

    def on_path_changed(self, entry):
        """Handle path entry changes to enable/disable create button."""
        path = entry.get_text().strip()
        self.create_button.set_sensitive(bool(path))

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

    def on_cancel_clicked(self, widget):
        """Handle cancel button click."""
        self.close()


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
