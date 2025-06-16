"""
Main setup wizard dialog that coordinates between different pages.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, GObject
from ..app_info import APP_ID
from .dependencies_page import DependenciesPage
from .create_gpg_page import CreateGpgPage
from .setup_complete_page import SetupCompletePage


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/setup/wizard_dialog.ui')
class SetupWizard(Adw.Dialog):
    """
    Main setup wizard dialog that coordinates the setup process.

    Signals:
        setup-complete: Emitted when setup is successfully completed
    """

    __gtype_name__ = "SetupWizard"

    __gsignals__ = {
        'setup-complete': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    # Template widgets
    toast_overlay = Gtk.Template.Child()
    navigation_view = Gtk.Template.Child()

    def __init__(self, parent_window=None, **kwargs):
        super().__init__(**kwargs)

        # Store parent window reference
        self.parent_window = parent_window

        # Connect dialog signals
        self.connect("closed", self._on_dialog_closed)
        self.connect("close-attempt", self._on_close_attempt)

        # Initialize the wizard
        self._setup_wizard()

    def _setup_wizard(self):
        """Set up the wizard by creating and adding the initial page."""
        # Create and add the dependencies page
        self.dependencies_page = DependenciesPage()
        self._connect_dependencies_signals()
        self.navigation_view.push(self.dependencies_page)

    def _connect_dependencies_signals(self):
        """Connect signals from the dependencies page."""
        self.dependencies_page.connect("continue-requested", self._on_dependencies_continue)
        self.dependencies_page.connect("create-directory-requested", self._on_create_directory_requested)
        self.dependencies_page.connect("create-gpg-key-requested", self._on_create_gpg_key_requested)

    # Navigation methods
    def _navigate_to_pass_install_page(self):
        """Navigate to the pass installation page."""
        # Create and push the pass installation page programmatically
        page = self._create_pass_install_page()
        nav_page = Adw.NavigationPage(child=page, title="Install Pass")
        nav_page.set_tag("pass-install")
        self.navigation_view.push(nav_page)

    def _navigate_to_gpg_create_page(self):
        """Navigate to the GPG creation page."""
        # Create and push the GPG creation page programmatically
        page = self._create_gpg_create_page()
        nav_page = Adw.NavigationPage(child=page, title="Create GPG Key")
        nav_page.set_tag("gpg-create")
        self.navigation_view.push(nav_page)

    def _navigate_to_complete_page(self):
        """Navigate to the completion page."""
        # Create and push the completion page programmatically
        page = self._create_complete_page()
        nav_page = Adw.NavigationPage(child=page, title="Setup Complete")
        nav_page.set_tag("complete")
        self.navigation_view.push(nav_page)

    # Event handlers from dependencies page
    def _on_dependencies_continue(self, _page):
        """Handle continue request from dependencies page."""
        # For now, go directly to completion page
        # In a full implementation, this might go to store initialization
        self._navigate_to_complete_page()



    def _on_create_directory_requested(self, _page):
        """Handle create directory request from dependencies page."""
        # This is handled directly in the dependencies page
        # We could show a toast here if needed
        self._show_toast("Password store directory created!")

    def _on_create_gpg_key_requested(self, _page):
        """Handle create GPG key request from dependencies page."""
        self._navigate_to_gpg_create_page()



    def _navigate_to_gpg_create_page(self):
        """Navigate to the GPG key creation page."""
        gpg_page = CreateGpgPage()
        gpg_page.connect('gpg-created', self._on_gpg_created)
        gpg_page.connect('creation-cancelled', self._on_creation_cancelled)
        self.navigation_view.push(gpg_page)

    def _navigate_to_complete_page(self):
        """Navigate to the completion page."""
        complete_page = SetupCompletePage()
        complete_page.connect('close-wizard', self._on_close_wizard)
        self.navigation_view.push(complete_page)

    # New signal handlers for the separate page classes
    def _on_installation_complete(self, _page):
        """Handle installation completion."""
        self._show_toast("Pass and GPG installed successfully!")
        # Navigate back to dependencies page and refresh
        self.navigation_view.pop()
        # Add a small delay to allow system to update before rechecking
        if hasattr(self.dependencies_page, 'recheck_dependencies'):
            GLib.timeout_add_seconds(1, lambda: (self.dependencies_page.recheck_dependencies(), False)[1])

    def _on_installation_cancelled(self, _page):
        """Handle installation cancellation."""
        self.navigation_view.pop()

    def _on_gpg_created(self, _page, gpg_id):
        """Handle GPG key creation."""
        self._show_toast(f"GPG key created successfully! ID: {gpg_id}")

        # Store the GPG key ID in the dependencies page for later use
        if hasattr(self.dependencies_page, 'set_created_gpg_key_id'):
            self.dependencies_page.set_created_gpg_key_id(gpg_id)

        # Navigate back to dependencies page and refresh
        self.navigation_view.pop()
        # Add a small delay to allow system to update before rechecking
        if hasattr(self.dependencies_page, 'recheck_dependencies'):
            GLib.timeout_add_seconds(1, lambda: (self.dependencies_page.recheck_dependencies(), False)[1])

    def _on_creation_cancelled(self, _page):
        """Handle GPG creation cancellation."""
        self.navigation_view.pop()

    def _on_close_wizard(self, _page):
        """Handle wizard close request."""
        self.close()

    # Dialog event handlers
    def _on_close_attempt(self, _dialog):
        """Handle close attempt - allow closing and quit application."""
        return False

    def _on_dialog_closed(self, _dialog):
        """Handle dialog closed - quit application when dialog is closed."""
        app = self.parent_window.get_application()
        if app:
            app.quit()

    # Utility methods
    def _show_toast(self, message):
        """Show a toast notification."""
        toast = Adw.Toast.new(message)
        self.toast_overlay.add_toast(toast)








