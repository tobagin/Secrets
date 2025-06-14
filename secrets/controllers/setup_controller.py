"""
Setup Controller - Manages GPG and password store setup and validation.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from typing import Callable, Optional

from ..managers import ToastManager
from ..error_handling import ErrorHandler, PasswordStoreError


class SetupController:
    """Controls GPG and password store setup and validation."""
    
    def __init__(self,
                 password_store,
                 toast_manager: ToastManager,
                 error_handler: ErrorHandler,
                 parent_window: Adw.Window,
                 on_setup_complete: Optional[Callable] = None):
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.error_handler = error_handler
        self.parent_window = parent_window
        self.on_setup_complete = on_setup_complete
        
        self._gpg_setup_valid = False
    
    def validate_and_setup_store(self):
        """
        Comprehensive validation of pass, GPG, and password store configuration.
        Shows appropriate user messages and handles setup issues.
        This is now mandatory - users cannot continue without proper setup.
        """
        self._gpg_setup_valid = False

        # First, validate complete setup (pass + GPG + store)
        is_valid, status = self.password_store.validate_complete_setup()

        if not is_valid:
            # Check if we have missing dependencies that need installation
            missing_deps = status.get('missing_dependencies', [])

            if missing_deps:
                # Show dependency installation dialog
                self._show_dependency_setup_dialog(missing_deps)
                return
            else:
                # GPG/setup issue, show setup dialog
                error_msg = status.get('error_message', 'Unknown setup error')

                # Create a mandatory setup dialog using DialogManager for proper positioning
                from ..ui_utils import DialogManager

                dialog = DialogManager.create_message_dialog(
                    parent=self.parent_window,
                    heading="Password Manager Setup Required",
                    body=f"{error_msg}\n\nThe password manager requires proper setup to function. Would you like to set up now?",
                    dialog_type="question",
                    default_size=(450, 300)
                )

                # Add response buttons using the AlertDialog API
                DialogManager.add_dialog_response(dialog, "setup", "_Set Up Now", "suggested")
                DialogManager.add_dialog_response(dialog, "quit", "_Quit Application", "destructive")

                # Set close response (when dialog is closed without clicking a button)
                dialog.set_close_response("quit")

                def on_setup_error_response(_dialog, response_id):
                    if response_id == "quit":
                        self.parent_window.get_application().quit()
                    elif response_id == "setup":
                        # Show the comprehensive setup dialog
                        self._show_comprehensive_setup_dialog()

                dialog.connect("response", on_setup_error_response)

                # Ensure proper dialog behavior
                DialogManager.setup_dialog_keyboard_navigation(dialog)
                DialogManager.center_dialog_on_parent(dialog, self.parent_window)

                dialog.present(self.parent_window)
                return

        # GPG is valid, now check if store needs initialization
        if not self.password_store.is_initialized:
            if not self.password_store.ensure_store_initialized(parent_window=self.parent_window):
                # Store could not be initialized or user cancelled
                self.error_handler.handle_error(
                    PasswordStoreError("Password store initialization failed or was cancelled by the user."),
                    "store_init"
                )
                self.toast_manager.show_warning(
                    "Password store is not configured. Most features will be disabled."
                )
                return

        # Everything is set up correctly
        self._gpg_setup_valid = True
        self.toast_manager.show_info("Password manager is ready to use")
        
        if self.on_setup_complete:
            self.on_setup_complete()

    def _show_dependency_setup_dialog(self, missing_deps):
        """Show dialog to install missing dependencies (pass/GPG)."""
        from ..dependency_setup_dialog import DependencySetupDialog

        setup_dialog = DependencySetupDialog(parent_window=self.parent_window, missing_deps=missing_deps)
        setup_dialog.connect("dependencies-installed", self._on_dependencies_installed)
        setup_dialog.present()

    def _on_dependencies_installed(self, dialog):
        """Handle successful dependency installation."""
        # Re-validate setup after dependencies are installed
        GLib.timeout_add_seconds(1, self._revalidate_after_dependency_install)

    def _revalidate_after_dependency_install(self):
        """Re-validate setup after dependency installation."""
        is_valid, status = self.password_store.validate_complete_setup()

        if is_valid:
            self._gpg_setup_valid = True
            self.toast_manager.show_success("Dependencies installed successfully!")
            if self.on_setup_complete:
                self.on_setup_complete()
        elif status.get('missing_dependencies'):
            # Still missing dependencies
            self.toast_manager.show_error("Some dependencies are still missing")
            self._show_dependency_setup_dialog(status['missing_dependencies'])
        else:
            # Dependencies installed but need GPG/pass setup
            self.toast_manager.show_info("Dependencies installed. Now let's complete the setup.")
            self._show_comprehensive_setup_dialog()

        return False  # Don't repeat the timeout

    def _show_comprehensive_setup_dialog(self):
        """Show comprehensive setup dialog for GPG key creation and pass initialization."""
        from ..gpg_setup_dialog import GPGSetupDialog

        setup_dialog = GPGSetupDialog(parent_window=self.parent_window)
        setup_dialog.present()

        # Connect to dialog close to re-validate setup
        def on_setup_dialog_close(dialog):
            # Re-run validation after setup dialog closes
            GLib.timeout_add_seconds(1, self._revalidate_after_setup)

        setup_dialog.connect("close-request", on_setup_dialog_close)

    def _show_gpg_setup_dialog(self):
        """Show the GPG setup dialog to help users configure GPG."""
        from ..gpg_setup_dialog import GPGSetupDialog

        setup_dialog = GPGSetupDialog(parent_window=self.parent_window)
        setup_dialog.present()

        # Connect to dialog close to re-validate setup
        def on_setup_dialog_close(dialog):
            # Re-run validation after setup dialog closes
            GLib.timeout_add_seconds(1, self._revalidate_after_setup)

        setup_dialog.connect("close-request", on_setup_dialog_close)

    def _revalidate_after_setup(self):
        """Re-validate GPG setup after the setup dialog closes."""
        is_valid, status = self.password_store.validate_gpg_setup()

        if is_valid:
            self._gpg_setup_valid = True
            self.toast_manager.show_success("GPG setup completed successfully!")
            if self.on_setup_complete:
                self.on_setup_complete()
        else:
            self.toast_manager.show_warning("GPG setup still incomplete. Some features may not work.")

        return False  # Don't repeat the timeout

    @property
    def is_setup_valid(self):
        """Check if the setup is valid."""
        return self._gpg_setup_valid

    def force_revalidation(self):
        """Force a revalidation of the setup."""
        self.validate_and_setup_store()
