import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio # Gio might be needed for actions/menus

# The resource path should match how it's defined in the GResource XML
# and how Meson compiles and installs it.
@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/secrets.ui')
class SecretsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SecretsWindow"

    # Define template children if you need to access them directly in code
    # Example:
    # main_content_box = Gtk.Template.Child()
    # add_button = Gtk.Template.Child()
    # edit_button = Gtk.Template.Child()
    # remove_button = Gtk.Template.Child()
    # toast_overlay = Gtk.Template.Child() # If you need to add toasts

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # The Gtk.Template decorator handles loading the UI definition.
        # Default size, title, and content are now set from secrets.ui.

    # Example of a template callback if you defined a signal handler in the UI file
    # @Gtk.Template.Callback()
    # def on_add_button_clicked(self, widget):
    #     print("Add button was clicked!")
    #     # Example: Show a toast
    #     # self.toast_overlay.add_toast(Adw.Toast.new("Add action triggered!"))

    # Add other methods for your window logic here
