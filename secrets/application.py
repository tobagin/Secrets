import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from .app_info import APP_ID, VERSION

# SecretsWindow is imported locally in methods where needed to avoid circular imports

class SecretsApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

    def do_startup(self):
        Adw.Application.do_startup(self)

        self.set_accels_for_action("app.quit", ["<Primary>q"])
        self.set_accels_for_action("app.about", ["<Primary>comma"])
        self.set_accels_for_action("app.preferences", ["<Primary>p"]) # Example

        self._make_action("quit", self.on_quit_action)
        self._make_action("about", self.on_about_action)
        self._make_action("preferences", self.on_preferences_action)
        self._make_action("git-pull", self.on_git_pull_action)
        self._make_action("git-push", self.on_git_push_action)

    def _make_action(self, name, callback_fn):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback_fn)
        self.add_action(action)

    def do_activate(self):
        from .window import SecretsWindow # Local import
        win = self.get_active_window()
        if not win:
            win = SecretsWindow(application=self)
        win.present()

    def on_about_action(self, action, param):
        from .window import SecretsWindow # Local import
        active_window = self.get_active_window()
        # Fallback if active_window is not the main one (e.g. a dialog is focused)
        if not isinstance(active_window, SecretsWindow) and self.get_windows():
             for w in self.get_windows():
                 if isinstance(w, SecretsWindow):
                     active_window = w
                     break

        about_dialog = Adw.AboutWindow(
            transient_for=active_window,
            application_name="Secrets",
            application_icon=APP_ID,
            developer_name="tobagin", # Replace with your actual name/handle
            version=VERSION,
            website="https://github.com/tobagin/secrets", # Replace with your actual project URL
            copyright="© 2023 tobagin", # Replace
            license_type=Gtk.License.MIT_X11 # Or your chosen license
        )
        about_dialog.present()

    def on_quit_action(self, action, param):
        self.quit()

    def on_preferences_action(self, action, param):
        active_window = self.get_active_window()
        if active_window and hasattr(active_window, 'toast_overlay'):
            active_window.toast_overlay.add_toast(Adw.Toast.new("Preferences not yet implemented."))
        else:
            print("Preferences action triggered. No active window with toast_overlay found.")

    def _call_window_method(self, method_name):
        from .window import SecretsWindow # Local import
        active_window = self.get_active_window()
        if isinstance(active_window, SecretsWindow) and hasattr(active_window, method_name):
            method_to_call = getattr(active_window, method_name)
            method_to_call(None) # Call with None as widget argument
        elif active_window:
            print(f"Active window does not support {method_name} or is not SecretsWindow.")
            if hasattr(active_window, 'toast_overlay'):
                 active_window.toast_overlay.add_toast(Adw.Toast.new(f"{method_name} action failed on window."))
        else:
            print(f"No active window to perform {method_name}.")


    def on_git_pull_action(self, action, param):
        self._call_window_method('on_git_pull_clicked')

    def on_git_push_action(self, action, param):
        self._call_window_method('on_git_push_clicked')

    def do_command_line(self, command_line):
        self.activate()
        return 0
