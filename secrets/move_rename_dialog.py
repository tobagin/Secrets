import gi
import os # For os.path.basename

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from .ui_utils import DialogManager, UIConstants, AccessibilityHelper

class MoveRenameDialog(Adw.Window):
    __gtype_name__ = "MoveRenameDialog"

    # Signal: save-requested (str: old_path, str: new_path)
    sig_save_requested = GObject.Signal(name='save-requested', arg_types=[str, str])

    def __init__(self, current_path, transient_for_window, **kwargs):
        super().__init__(modal=True, transient_for=transient_for_window, **kwargs)

        self.old_path = current_path

        title = f"Move/Rename: {os.path.basename(current_path)}"
        self.set_title(title)
        self.set_default_size(*UIConstants.SMALL_DIALOG)
        self.set_resizable(True)

        # Add dialog styling
        self.add_css_class("dialog")

        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, f"Move or rename dialog for {os.path.basename(current_path)}")
        AccessibilityHelper.set_accessible_description(self, "Dialog for moving or renaming a password entry")

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_vbox)

        # Header Bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Move/Rename Entry"))

        save_button = Gtk.Button(label="_Save", use_underline=True)
        save_button.connect("clicked", self.on_save_clicked)
        save_button.add_css_class("suggested-action")
        header_bar.pack_end(save_button)

        cancel_button = Gtk.Button(label="_Cancel", use_underline=True)
        cancel_button.connect("clicked", self.on_cancel_clicked)
        header_bar.pack_start(cancel_button)

        main_vbox.append(header_bar)

        # Content Area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                              margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        main_vbox.append(content_box)
        content_box.set_vexpand(True) # Allow content to expand if needed

        # Current Path (read-only for reference)
        current_path_row = Adw.ActionRow(title="Current Path")
        current_path_row.set_subtitle(self.old_path)
        content_box.append(current_path_row)

        # New Path Entry
        self.new_path_entry = Adw.EntryRow(title="New Path")
        self.new_path_entry.set_text(self.old_path) # Pre-fill with old path for editing
        self.new_path_entry.connect("activate", self.on_save_clicked) # Allow Enter to save
        content_box.append(self.new_path_entry)

        # Request focus on the entry
        self.new_path_entry.grab_focus()


    def on_save_clicked(self, widget):
        new_path = self.new_path_entry.get_text().strip()
        if not new_path:
            # Optionally show an error in the dialog itself or rely on main window toast
            print("New path cannot be empty.") # Simple feedback for now
            # Could use Adw.ToastOverlay within the dialog if complex validation needed here
            return

        if new_path == self.old_path:
            # No change, just close or inform user
            self.close()
            return

        self.emit("save-requested", self.old_path, new_path)

    def on_cancel_clicked(self, widget):
        self.close()

if __name__ == '__main__': # For basic testing of the dialog itself
    app = Adw.Application(application_id="com.example.testmoverenamedialog")
    def on_activate(application):
        test_path = "Services/OldName"

        dialog = MoveRenameDialog(test_path, transient_for_window=None)

        def handle_save(dialog_instance, old_p, new_p):
            print(f"Save requested to move/rename from: {old_p} to: {new_p}")
            dialog_instance.close()

        dialog.connect('save-requested', handle_save)
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
