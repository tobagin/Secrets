import gi
import os # Added for os.path.basename

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from .ui_utils import DialogManager, UIConstants, AccessibilityHelper

class EditPasswordDialog(Adw.Window):
    __gtype_name__ = "EditPasswordDialog"

    # Define a signal that the dialog can emit when save is attempted
    # The signal will carry the password path and its new content.
    # Alternatively, the dialog can call a method on a delegate (e.g., the main window).
    # For now, let's use a signal.
    sig_save_requested = GObject.Signal(name='save-requested', arg_types=[str, str])

    def __init__(self, password_path, password_content, transient_for_window, **kwargs):
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.password_path = password_path
        self.initial_content = password_content

        # Configure dialog
        title = f"Edit: {os.path.basename(password_path)}"
        self.set_title(title)
        self.set_default_size(*UIConstants.MEDIUM_DIALOG)
        self.set_resizable(True)

        # Add dialog styling
        self.add_css_class("dialog")

        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, f"Edit password dialog for {os.path.basename(password_path)}")
        AccessibilityHelper.set_accessible_description(self, "Dialog for editing password entry content")

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_vbox)

        # Header Bar
        header_bar = Adw.HeaderBar()
        window_title = Adw.WindowTitle(title=f"Edit: {os.path.basename(password_path)}")
        window_title.set_subtitle("Password Entry")
        header_bar.set_title_widget(window_title)

        # Action buttons with improved styling
        save_button = Gtk.Button(label="_Save", use_underline=True)
        save_button.connect("clicked", self.on_save_clicked)
        save_button.add_css_class("suggested-action")
        save_button.set_tooltip_text("Save changes to password entry")
        AccessibilityHelper.set_accessible_name(save_button, "Save password changes")
        header_bar.pack_end(save_button)

        cancel_button = Gtk.Button(label="_Cancel", use_underline=True)
        cancel_button.connect("clicked", self.on_cancel_clicked)
        cancel_button.set_tooltip_text("Cancel editing and close dialog")
        AccessibilityHelper.set_accessible_name(cancel_button, "Cancel editing")
        header_bar.pack_start(cancel_button)

        main_vbox.append(header_bar)

        # Content Area with improved spacing
        content_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=UIConstants.MEDIUM_SPACING,
            margin_top=UIConstants.LARGE_MARGIN,
            margin_bottom=UIConstants.LARGE_MARGIN,
            margin_start=UIConstants.LARGE_MARGIN,
            margin_end=UIConstants.LARGE_MARGIN
        )
        main_vbox.append(content_box)
        content_box.set_vexpand(True)

        # Path information in a preferences group for better styling
        path_group = Adw.PreferencesGroup()
        path_group.set_title("Password Entry Information")
        content_box.append(path_group)

        path_row = Adw.ActionRow(title="Path")
        path_row.set_subtitle(self.password_path)
        path_row.add_css_class("property")
        AccessibilityHelper.set_accessible_name(path_row, f"Password path: {self.password_path}")
        path_group.add(path_row)

        # Content editing section
        content_group = Adw.PreferencesGroup()
        content_group.set_title("Content")
        content_group.set_description("Edit the password entry content below")
        content_box.append(content_group)

        # Text view with improved styling
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.get_buffer().set_text(self.initial_content)
        self.text_view.set_vexpand(True)
        self.text_view.add_css_class("password-field")
        AccessibilityHelper.set_accessible_name(self.text_view, "Password content editor")
        AccessibilityHelper.set_accessible_description(self.text_view, "Multi-line text editor for password entry content")

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(self.text_view)
        scrolled_window.set_has_frame(True)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(250)
        scrolled_window.set_vexpand(True)

        # Wrap in a clamp for better layout
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        clamp.set_child(scrolled_window)
        content_group.add(clamp)

        # Set up dialog behavior
        self._setup_dialog_behavior()

    def _setup_dialog_behavior(self):
        """Set up keyboard navigation and focus management."""
        # Set up keyboard navigation
        DialogManager.setup_dialog_keyboard_navigation(self)

        # Set up focus management - focus the text view when dialog is shown
        DialogManager.ensure_dialog_focus(self, self.text_view)

        # Center dialog on parent
        DialogManager.center_dialog_on_parent(self)

    def on_save_clicked(self, widget):
        """Handle save button click."""
        buffer = self.text_view.get_buffer()
        start_iter, end_iter = buffer.get_bounds()
        new_content = buffer.get_text(start_iter, end_iter, True) # True for include_hidden_chars

        # Emit the signal with path and new content
        self.emit("save-requested", self.password_path, new_content)
        # The main window will listen to this signal, call PasswordStore, and then close this dialog.

    def on_cancel_clicked(self, widget):
        """Handle cancel button click."""
        self.close()

if __name__ == '__main__': # For basic testing of the dialog itself
    # import os # Already at module level

    app = Adw.Application(application_id="com.example.testdialog")
    def on_activate(application):
        # Example data
        test_path = "Services/TestPassword"
        test_content = "this is the password\nline2\nline3"

        dialog = EditPasswordDialog(test_path, test_content, transient_for_window=None)

        def handle_save(dialog_instance, path, content):
            print(f"Save requested for path: {path}")
            print(f"New content:\n{content}")
            dialog_instance.close() # Close after handling

        dialog.connect('save-requested', handle_save)
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
