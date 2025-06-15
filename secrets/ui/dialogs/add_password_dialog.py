import gi
import os # For os.path.basename if needed, though not directly used here yet

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...utils import DialogManager, UIConstants, AccessibilityHelper

class AddPasswordDialog(Adw.Window):
    __gtype_name__ = "AddPasswordDialog"

    # Signal: add-requested (str: path, str: content)
    sig_add_requested = GObject.Signal(name='add-requested', arg_types=[str, str])

    def __init__(self, transient_for_window, suggested_folder_path="", **kwargs):
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.set_title("Add New Password")
        self.set_default_size(*UIConstants.MEDIUM_DIALOG)
        self.set_resizable(True)

        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, "Add new password dialog")
        AccessibilityHelper.set_accessible_description(self, "Dialog for creating a new password entry")

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_vbox)

        # Header Bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Add New Password"))

        save_button = Gtk.Button(label="_Save", use_underline=True)
        save_button.connect("clicked", self.on_save_clicked)
        header_bar.pack_end(save_button)

        cancel_button = Gtk.Button(label="_Cancel", use_underline=True)
        cancel_button.connect("clicked", self.on_cancel_clicked)
        header_bar.pack_start(cancel_button)

        main_vbox.append(header_bar)

        # Content Area using Adw.PreferencesPage for grouped rows
        page = Adw.PreferencesPage()
        main_vbox.append(page)

        group = Adw.PreferencesGroup()
        page.add(group)

        # New Password Path Entry
        self.path_entry = Adw.EntryRow()
        self.path_entry.set_title("Path")
        if suggested_folder_path and not suggested_folder_path.endswith('/'):
            suggested_folder_path += '/'
        self.path_entry.set_text(suggested_folder_path) # Pre-fill if a folder was selected
        self.path_entry.connect("activate", self.on_path_entry_activated) # Go to content on Enter
        group.add(self.path_entry)

        # Add a description row for the path format
        path_description = Adw.ActionRow()
        path_description.set_title("Examples: websites/github, email/gmail")
        group.add(path_description)

        # Content TextView (within its own group or just below)
        content_group = Adw.PreferencesGroup(title="Password Content")
        # content_group.set_description("The first line is typically the password itself. Subsequent lines can be notes or other data.")
        page.add(content_group)

        self.content_view = Gtk.TextView()
        self.content_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.content_view.set_vexpand(True) # Allow it to take vertical space

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(self.content_view)
        scrolled_window.set_has_frame(True)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(150)

        # Add ScrolledWindow to an Adw.ActionRow or directly if not using row styling here
        # For more space, we can add it directly to the page or a Box within the page.
        # Using a simple Box for the text view area for now.
        text_view_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=6)
        text_view_box.append(scrolled_window)
        content_group.add(text_view_box) # Add the box containing the scrolled window

        # Initial focus
        self.path_entry.grab_focus()

    def on_path_entry_activated(self, entry_row):
        # Move focus to the content view when Enter is pressed in path entry
        self.content_view.grab_focus()

    def on_save_clicked(self, widget):
        path = self.path_entry.get_text().strip()

        buffer = self.content_view.get_buffer()
        start_iter, end_iter = buffer.get_bounds()
        content = buffer.get_text(start_iter, end_iter, True) # True for include_hidden_chars

        if not path:
            # TODO: Show inline error or toast within dialog
            print("Path cannot be empty.")
            self.path_entry.grab_focus() # Focus back to path
            # Example of using a toast within this dialog if it had its own overlay
            # self.add_toast(Adw.Toast.new("Password path cannot be empty!"))
            return

        if not content.strip(): # Check if content (ignoring whitespace) is empty
            # TODO: Show inline error or toast
            print("Content cannot be empty.")
            self.content_view.grab_focus() # Focus to content
            return

        self.emit("add-requested", path, content)

    def on_cancel_clicked(self, widget):
        self.close()

if __name__ == '__main__': # For basic testing of the dialog itself
    app = Adw.Application(application_id="com.example.testadddialog")
    def on_activate(application):
        # Example data
        dialog = AddPasswordDialog(transient_for_window=None, suggested_folder_path="Services/Email")

        def handle_add(dialog_instance, path, content):
            print(f"Add requested for path: {path}")
            print(f"Content:\n{content}")
            dialog_instance.close() # Close after handling

        dialog.connect('add-requested', handle_add)
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
