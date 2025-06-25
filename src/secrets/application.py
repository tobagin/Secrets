import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, Gdk
from .app_info import APP_ID, VERSION

# SecretsWindow is imported locally in methods where needed to avoid circular imports

class SecretsApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Load CSS styles
        self._load_css()

        self.set_accels_for_action("app.quit", ["<Primary>q"])
        self.set_accels_for_action("app.about", ["<Primary>question"])
        self.set_accels_for_action("app.preferences", ["<Primary>comma"])
        # Git keyboard shortcuts disabled for v0.8.6
        # self.set_accels_for_action("app.git-pull", ["<Primary><Shift>p"])
        # self.set_accels_for_action("app.git-push", ["<Primary><Shift>u"])
        # self.set_accels_for_action("app.git-status", ["<Primary><Shift>s"])
        # self.set_accels_for_action("app.git-setup", ["<Primary><Shift>g"])

        # Window-specific shortcuts
        self.set_accels_for_action("win.add-password", ["<Primary>n"])
        self.set_accels_for_action("win.edit-password", ["<Primary>e"])
        self.set_accels_for_action("win.delete-password", ["Delete"])
        self.set_accels_for_action("win.copy-password", ["<Primary>c"])
        self.set_accels_for_action("win.copy-username", ["<Primary><Shift>c"])
        self.set_accels_for_action("win.focus-search", ["<Primary>f"])
        self.set_accels_for_action("win.clear-search", ["Escape"])
        self.set_accels_for_action("win.refresh", ["F5"])
        self.set_accels_for_action("win.toggle-password", ["<Primary>h"])
        self.set_accels_for_action("win.generate-password", ["<Primary>g"])
        self.set_accels_for_action("win.show-help-overlay", ["<Primary>question", "F1"])
        self.set_accels_for_action("win.import-export", ["<Primary><Shift>i"])

        self._make_action("quit", self.on_quit_action)
        self._make_action("about", self.on_about_action)
        self._make_action("preferences", self.on_preferences_action)
        # Git actions disabled for v0.8.6
        # self._make_action("git-pull", self.on_git_pull_action)
        # self._make_action("git-push", self.on_git_push_action)
        # self._make_action("git-status", self.on_git_status_action)
        # self._make_action("git-setup", self.on_git_setup_action)

    def _load_css(self):
        """Load CSS styles for the application."""
        try:
            css_provider = Gtk.CssProvider()
            css_path = "/io/github/tobagin/secrets/ui/style.css"
            css_provider.load_from_resource(css_path)

            display = Gdk.Display.get_default()
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Failed to load CSS: {e}")

    def _make_action(self, name, callback_fn):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback_fn)
        self.add_action(action)

    def do_activate(self):
        """Activate the application - check setup first, then show appropriate window."""
        win = self.get_active_window()
        if not win:
            # Check if setup is needed before showing main window
            if self._needs_setup():
                self._show_setup_wizard()
            else:
                self._show_main_window()
        else:
            win.present()

    def _needs_setup(self):
        """Check if the application needs setup (pass/GPG/store)."""
        # Simple check without full validation to avoid hanging
        import os
        import shutil
        import subprocess

        # Check if pass is installed
        if not shutil.which('pass'):
            return True

        # Check if GPG is installed
        if not shutil.which('gpg'):
            return True

        # Check if password store directory exists
        store_dir = os.path.expanduser("~/.password-store")
        if not os.path.exists(store_dir):
            return True

        # Check if .gpg-id file exists
        gpg_id_file = os.path.join(store_dir, ".gpg-id")
        if not os.path.exists(gpg_id_file):
            return True

        # Check if there are any GPG secret keys
        try:
            result = subprocess.run(['gpg', '--batch', '--list-secret-keys', '--with-colons'],
                                  capture_output=True, text=True, timeout=3)
            has_gpg_keys = result.returncode == 0 and result.stdout.strip()
            if not has_gpg_keys:
                return True
        except:
            # If we can't check GPG keys, assume setup is needed
            return True

        # All checks passed, setup is complete
        return False

    def _show_setup_wizard(self):
        """Show the setup wizard dialog over the main window."""
        from .window import SecretsWindow
        from .setup_wizard import SetupWizard

        # Create the main window first (but don't show it yet)
        main_window = SecretsWindow(application=self)

        # Create and show the setup wizard as a dialog over the main window
        setup_wizard = SetupWizard(parent_window=main_window)
        setup_wizard.connect("closed", self._on_wizard_closed)
        setup_wizard.connect("setup-complete", self._on_setup_complete)

        # Present the main window first, then the setup wizard
        main_window.present()
        setup_wizard.present(main_window)

    def _show_main_window(self):
        """Show the main application window."""
        from .window import SecretsWindow

        win = SecretsWindow(application=self)
        win.present()

    def _on_setup_complete(self, setup_wizard):
        """Called when setup is successfully completed."""
        print("DEBUG: _on_setup_complete called in application")

        # Main window is already shown, just trigger the setup completion
        main_window = setup_wizard.parent_window
        if hasattr(main_window, '_verify_setup_and_load'):
            print("DEBUG: Calling _verify_setup_and_load on main window")
            main_window._verify_setup_and_load()
        else:
            print("DEBUG: Main window does not have _verify_setup_and_load method")

    def _on_wizard_closed(self, setup_wizard):
        """Called when setup wizard is closed."""
        # If setup was completed, _on_setup_complete already handled it
        # If setup was not completed, the wizard will quit the application
        pass

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
            license_type=Gtk.License.GPL_3_0 # Or your chosen license
        )
        about_dialog.present()

    def on_quit_action(self, action, param):
        self.quit()

    def on_preferences_action(self, action, param):
        from .ui.dialogs import PreferencesDialog
        from .window import SecretsWindow

        active_window = self.get_active_window()
        if isinstance(active_window, SecretsWindow):
            preferences_dialog = PreferencesDialog(
                parent_window=active_window,
                config_manager=active_window.config_manager
            )
            preferences_dialog.present()
        else:
            print("Preferences action triggered. No active SecretsWindow found.")

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


    # Git action handlers disabled for v0.8.6
    # def on_git_pull_action(self, action, param):
    #     self._call_window_method('on_git_pull_clicked')

    # def on_git_push_action(self, action, param):
    #     self._call_window_method('on_git_push_clicked')

    # def on_git_status_action(self, action, param):
    #     self._call_window_method('show_git_status_dialog')

    # def on_git_setup_action(self, action, param):
    #     self._call_window_method('_show_git_setup_dialog')

    def do_command_line(self, command_line):
        self.activate()
        return 0
