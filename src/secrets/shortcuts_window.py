import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from secrets.app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/shortcuts_window.ui')
class ShortcutsWindow(Adw.Window):
    """Keyboard shortcuts help window."""

    __gtype_name__ = "ShortcutsWindow"

    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)

        self.set_transient_for(parent_window)
