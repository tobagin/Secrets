import gi
import os # Added for os.path.basename

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject

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

        self.set_title(f"Edit: {os.path.basename(password_path)}")
        self.set_default_size(450, 400)

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_content(main_vbox)

        # Header Bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title=f"Edit: {os.path.basename(password_path)}"))

        save_button = Gtk.Button(label="_Save", use_underline=True)
        save_button.connect("clicked", self.on_save_clicked)
        save_button.get_style_context().add_class("suggested-action")
        header_bar.pack_end(save_button)

        cancel_button = Gtk.Button(label="_Cancel", use_underline=True)
        cancel_button.connect("clicked", self.on_cancel_clicked)
        header_bar.pack_start(cancel_button)

        main_vbox.append(header_bar)

        # Content Area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                              margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        main_vbox.append(content_box)
        content_box.set_vexpand(True)

        # Path Label (read-only for now)
        path_label_row = Adw.ActionRow(title="Path")
        path_label_row.set_subtitle(self.password_path)
        content_box.append(path_label_row)

        # Content TextView
        content_label = Gtk.Label(label="Content:", halign=Gtk.Align.START, margin_bottom=6)
        content_box.append(content_label)

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.get_buffer().set_text(self.initial_content)
        self.text_view.set_vexpand(True)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(self.text_view)
        scrolled_window.set_has_frame(True)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(200) # Ensure it has some decent height
        content_box.append(scrolled_window)


    def on_save_clicked(self, widget):
        buffer = self.text_view.get_buffer()
        start_iter, end_iter = buffer.get_bounds()
        new_content = buffer.get_text(start_iter, end_iter, True) # True for include_hidden_chars

        # Emit the signal with path and new content
        self.emit("save-requested", self.password_path, new_content)
        # The main window will listen to this signal, call PasswordStore, and then close this dialog.

    def on_cancel_clicked(self, widget):
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
