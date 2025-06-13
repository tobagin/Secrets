import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw
from .window import SecretsWindow
from .app_info import APP_ID

class SecretsApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id=APP_ID, **kwargs)
        # self.connect('activate', self.on_activate) # Using do_activate vfunc

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = SecretsWindow(application=self)
        win.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        # Basic setup can go here later
