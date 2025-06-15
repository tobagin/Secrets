"""
GPG Setup Dialog for the Secrets application.
Provides a user-friendly interface for setting up GPG keys and password store.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from .utils import GPGSetupHelper, DialogManager, UIConstants, AccessibilityHelper, SystemSetupHelper


class GPGSetupDialog(Adw.Window):
    """Dialog to help users set up GPG and password store."""
    
    __gtype_name__ = "GPGSetupDialog"
    
    def __init__(self, parent_window=None, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Password Manager Setup")
        # Use a larger size for better layout
        self.set_default_size(800, 700)
        self.set_modal(True)
        self.set_resizable(True)

        if parent_window:
            self.set_transient_for(parent_window)

        # Add dialog styling
        self.add_css_class("dialog")

        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, "Password manager setup dialog")
        AccessibilityHelper.set_accessible_description(self, "Dialog for setting up GPG encryption and password store")

        self.setup_helper = GPGSetupHelper()
        self._build_ui()
        self._setup_dialog_behavior()
    
    def _build_ui(self):
        """Build the dialog UI."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Setup Password Manager"))
        main_box.append(header_bar)

        # Toast overlay for messages
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)

        # Content box - no scrolled window, direct content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(32)
        content_box.set_margin_bottom(32)
        content_box.set_margin_start(32)
        content_box.set_margin_end(32)
        content_box.set_vexpand(True)  # Allow vertical expansion
        self.toast_overlay.set_child(content_box)

        # Welcome section with icon and text
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        welcome_box.set_halign(Gtk.Align.CENTER)
        content_box.append(welcome_box)

        # Icon
        icon = Gtk.Image.new_from_icon_name("dialog-password-symbolic")
        icon.set_pixel_size(64)
        icon.add_css_class("accent")
        welcome_box.append(icon)

        # Title
        title_label = Gtk.Label(label="GPG Setup Required")
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.CENTER)
        welcome_box.append(title_label)

        # Description
        desc_label = Gtk.Label(label="GPG encrypts your passwords. Let's set up your encryption key.")
        desc_label.add_css_class("body")
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_wrap(True)
        desc_label.set_justify(Gtk.Justification.CENTER)
        welcome_box.append(desc_label)
        
        # Setup action section
        setup_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        setup_section.set_margin_top(32)
        setup_section.set_halign(Gtk.Align.CENTER)
        content_box.append(setup_section)

        # Setup description
        setup_desc = Gtk.Label(label="We'll automatically create your GPG key and set up the password store.")
        setup_desc.add_css_class("body")
        setup_desc.set_wrap(True)
        setup_desc.set_justify(Gtk.Justification.CENTER)
        setup_desc.set_halign(Gtk.Align.CENTER)
        setup_section.append(setup_desc)

        # Main setup button
        setup_button = Gtk.Button(label="Set Up Password Manager")
        setup_button.add_css_class("suggested-action")
        setup_button.add_css_class("pill")
        setup_button.set_size_request(200, 40)
        setup_button.connect("clicked", self._on_auto_setup_clicked)
        setup_section.append(setup_button)

        # Alternative action
        quit_button = Gtk.Button(label="Quit Application")
        quit_button.add_css_class("destructive-action")
        quit_button.connect("clicked", self._on_quit_clicked)
        setup_section.append(quit_button)
        
        # Information group
        info_group = Adw.PreferencesGroup()
        info_group.set_title("What You Need to Know")
        info_group.set_description("Understanding the components of your password manager")
        info_group.set_margin_top(24)
        content_box.append(info_group)

        # Info about GPG
        gpg_info_row = Adw.ActionRow()
        gpg_info_row.set_title("GPG (GNU Privacy Guard)")
        gpg_info_row.set_subtitle("Provides strong encryption for your passwords using public-key cryptography")
        gpg_info_row.set_icon_name("security-high-symbolic")
        info_group.add(gpg_info_row)

        # Info about password store
        pass_info_row = Adw.ActionRow()
        pass_info_row.set_title("Password Store")
        pass_info_row.set_subtitle("Organizes encrypted passwords in a directory structure with Git integration")
        pass_info_row.set_icon_name("folder-symbolic")
        info_group.add(pass_info_row)

        # Add some bottom spacing
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        content_box.append(spacer)
    
    def _on_auto_setup_clicked(self, button):
        """Handle automatic setup."""
        # Create a dialog to get user information
        self._show_auto_setup_dialog()

    def _on_quit_clicked(self, button):
        """Handle quit application."""
        # Get the application and quit
        app = self.get_root().get_application()
        if app:
            app.quit()
        else:
            self.close()
    
    def _show_auto_setup_dialog(self):
        """Show dialog for automatic setup."""
        from .utils import DialogManager

        dialog = DialogManager.create_message_dialog(
            parent=self,
            heading="Create Your GPG Key",
            body="Please provide your information to create a secure GPG key for password encryption:",
            dialog_type="question",
            default_size=(550, 450)
        )

        # Create form for user info with better spacing
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        form_box.set_margin_top(16)
        form_box.set_margin_bottom(16)

        # Name entry
        name_row = Adw.EntryRow(title="Full Name")
        name_row.set_text("")  # Empty by default
        name_row.set_show_apply_button(False)
        form_box.append(name_row)

        # Email entry
        email_row = Adw.EntryRow(title="Email Address")
        email_row.set_text("")  # Empty by default
        email_row.set_show_apply_button(False)
        form_box.append(email_row)

        # Passphrase option
        passphrase_row = Adw.PasswordEntryRow(title="Passphrase (optional)")
        passphrase_row.set_show_apply_button(False)
        form_box.append(passphrase_row)

        # Add help text
        help_label = Gtk.Label()
        help_label.set_markup("<small>The passphrase protects your GPG key. Leave empty for no passphrase.</small>")
        help_label.set_wrap(True)
        help_label.add_css_class("dim-label")
        form_box.append(help_label)
        
        # Add the form as extra child to the AlertDialog
        dialog.set_extra_child(form_box)

        # Add response buttons using the AlertDialog API
        DialogManager.add_dialog_response(dialog, "cancel", "_Cancel", "default")
        DialogManager.add_dialog_response(dialog, "create", "_Create Key", "suggested")

        # Set close response
        dialog.set_close_response("cancel")

        def on_auto_setup_response(_dialog, response_id):
            if response_id == "create":
                name = name_row.get_text().strip()
                email = email_row.get_text().strip()
                passphrase = passphrase_row.get_text().strip()

                if not name or not email:
                    self.toast_overlay.add_toast(Adw.Toast.new("Please fill in name and email"))
                    return

                if not self.setup_helper.validate_email(email):
                    self.toast_overlay.add_toast(Adw.Toast.new("Please enter a valid email address"))
                    return

                # Start GPG key creation
                self._create_gpg_key(name, email, passphrase)

        dialog.connect("response", on_auto_setup_response)

        # Ensure proper dialog behavior
        DialogManager.setup_dialog_keyboard_navigation(dialog)
        DialogManager.center_dialog_on_parent(dialog, self)

        dialog.present(self)
    
    def _create_gpg_key(self, name: str, email: str, passphrase: str):
        """Create GPG key with the provided information."""
        # Show progress
        self.toast_overlay.add_toast(Adw.Toast.new("Creating GPG key... This may take a moment."))
        
        # Use GLib.idle_add to run the key creation in the background
        def create_key():
            success, message = self.setup_helper.create_gpg_key_batch(name, email, passphrase)
            
            # Update UI on main thread
            GLib.idle_add(self._on_key_creation_complete, success, message, email)
        
        # Run in a separate thread (simplified for this example)
        import threading
        thread = threading.Thread(target=create_key)
        thread.daemon = True
        thread.start()
    
    def _on_key_creation_complete(self, success: bool, message: str, email: str):
        """Handle completion of GPG key creation."""
        if success:
            self.toast_overlay.add_toast(Adw.Toast.new("GPG key created successfully!"))
            # Now initialize password store
            self._initialize_password_store(email)
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Failed to create GPG key: {message}"))
    
    def _initialize_password_store(self, email: str):
        """Initialize the password store with the GPG key."""
        from .password_store import PasswordStore

        store = PasswordStore()

        # First ensure the store directory exists
        if not store.is_initialized:
            try:
                import os
                os.makedirs(store.store_dir, exist_ok=True)
            except Exception as e:
                self.toast_overlay.add_toast(Adw.Toast.new(f"Failed to create store directory: {e}"))
                return

        # Initialize the password store
        success, message = store.init_store(email)

        if success:
            self.toast_overlay.add_toast(Adw.Toast.new("Password store initialized successfully!"))
            self.toast_overlay.add_toast(Adw.Toast.new("Setup complete! You can now use the password manager."))
            # Close dialog and signal success
            GLib.timeout_add_seconds(3, self.close)
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Failed to initialize password store: {message}"))
    


    def _setup_dialog_behavior(self):
        """Set up keyboard navigation and focus management."""
        # Set up keyboard navigation
        DialogManager.setup_dialog_keyboard_navigation(self)

        # Center dialog on parent
        DialogManager.center_dialog_on_parent(self)
