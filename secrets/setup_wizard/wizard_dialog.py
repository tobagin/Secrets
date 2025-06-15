"""
Main setup wizard dialog that coordinates between different pages.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, GObject
from ..app_info import APP_ID
from .dependencies_page import DependenciesPage


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/data/wizard_dialog.ui')
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
        self.dependencies_page.connect("install-pass-requested", self._on_install_pass_requested)
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

    def _on_install_pass_requested(self, _page):
        """Handle install pass request from dependencies page."""
        self._navigate_to_pass_install_page()

    def _on_create_directory_requested(self, _page):
        """Handle create directory request from dependencies page."""
        # This is handled directly in the dependencies page
        # We could show a toast here if needed
        self._show_toast("Password store directory created!")

    def _on_create_gpg_key_requested(self, _page):
        """Handle create GPG key request from dependencies page."""
        self._navigate_to_gpg_create_page()

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

    # Temporary page creation methods (to be extracted later)
    def _create_pass_install_page(self):
        """Create the pass installation page."""
        toolbar_view = Adw.ToolbarView()
        
        # Add header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label="Install Pass"))
        toolbar_view.add_top_bar(header_bar)
        
        # Create content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(18)
        content.set_margin_bottom(18)
        content.set_margin_start(18)
        content.set_margin_end(18)

        # Header
        header_label = Gtk.Label(label="Install Pass (Password Store)")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_margin_bottom(6)
        header_label.add_css_class("title-4")
        content.append(header_label)
        
        desc_label = Gtk.Label(label="Installing the pass password manager...")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_margin_bottom(12)
        desc_label.add_css_class("dim-label")
        content.append(desc_label)

        # Installation status row
        status_listbox = Gtk.ListBox()
        status_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        status_listbox.add_css_class("boxed-list")
        content.append(status_listbox)

        install_row = Adw.ActionRow()
        install_row.set_title("Installation Status")
        install_row.set_subtitle("Ready to install pass package")
        
        # Add an icon to show this is an installation process
        install_icon = Gtk.Image.new_from_icon_name("system-software-install-symbolic")
        install_row.add_prefix(install_icon)
        
        status_listbox.append(install_row)

        # Progress indicator
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(True)
        progress_bar.set_text("Ready to install")
        progress_bar.set_margin_top(12)
        content.append(progress_bar)

        # Install button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(24)
        content.append(button_box)

        install_button = Gtk.Button(label="Start Installation")
        install_button.add_css_class("suggested-action")
        install_button.connect("clicked", lambda b: self._show_toast("Installation not implemented yet"))
        button_box.append(install_button)

        toolbar_view.set_content(content)
        return toolbar_view

    def _create_gpg_create_page(self):
        """Create the GPG key creation page."""
        toolbar_view = Adw.ToolbarView()
        
        # Add header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label="Create GPG Key"))
        toolbar_view.add_top_bar(header_bar)
        
        # Create content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(18)
        content.set_margin_bottom(18)
        content.set_margin_start(18)
        content.set_margin_end(18)

        # Header
        header_label = Gtk.Label(label="Create GPG Key")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_margin_bottom(6)
        header_label.add_css_class("title-4")
        content.append(header_label)
        
        desc_label = Gtk.Label(label="Enter your information to create a new GPG key:")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_margin_bottom(12)
        desc_label.add_css_class("dim-label")
        content.append(desc_label)

        # Form container
        form_listbox = Gtk.ListBox()
        form_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        form_listbox.add_css_class("boxed-list")
        content.append(form_listbox)

        # Name entry
        name_row = Adw.EntryRow()
        name_row.set_title("Full Name")
        form_listbox.append(name_row)

        # Email entry
        email_row = Adw.EntryRow()
        email_row.set_title("Email Address")
        form_listbox.append(email_row)

        # Passphrase entry
        passphrase_row = Adw.PasswordEntryRow()
        passphrase_row.set_title("Passphrase (optional)")
        form_listbox.append(passphrase_row)

        # Create GPG Key button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(24)
        content.append(button_box)

        create_button = Gtk.Button(label="Create GPG Key")
        create_button.add_css_class("suggested-action")
        create_button.connect("clicked", lambda b: self._show_toast("GPG creation not implemented yet"))
        button_box.append(create_button)

        toolbar_view.set_content(content)
        return toolbar_view

    def _create_complete_page(self):
        """Create the completion page."""
        toolbar_view = Adw.ToolbarView()
        
        # Add header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label="Setup Complete"))
        toolbar_view.add_top_bar(header_bar)
        
        # Create content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(18)
        content.set_margin_bottom(18)
        content.set_margin_start(18)
        content.set_margin_end(18)

        # Success message
        success_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        success_box.set_halign(Gtk.Align.CENTER)
        success_box.set_valign(Gtk.Align.CENTER)
        content.append(success_box)

        # Success icon
        success_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
        success_icon.set_pixel_size(64)
        success_icon.add_css_class("success")
        success_box.append(success_icon)

        # Success title
        success_title = Gtk.Label(label="Setup Complete!")
        success_title.add_css_class("title-1")
        success_box.append(success_title)

        # Success description
        success_desc = Gtk.Label(label="Your password manager is now ready to use.")
        success_desc.add_css_class("dim-label")
        success_box.append(success_desc)

        # Start using button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(24)
        content.append(button_box)

        start_button = Gtk.Button(label="Start Using Secrets")
        start_button.add_css_class("suggested-action")
        start_button.connect("clicked", lambda b: self.emit("setup-complete"))
        button_box.append(start_button)

        toolbar_view.set_content(content)
        return toolbar_view
