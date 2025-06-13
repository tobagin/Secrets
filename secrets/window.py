import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GObject # Added GObject for custom TreeStore columns
import os # For path manipulation in list_passwords if needed, though logic is in PasswordStore

from .password_store import PasswordStore

@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/secrets.ui')
class SecretsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SecretsWindow"

    # Define template children for UI elements defined in secrets.ui
    details_stack = Gtk.Template.Child()
    selected_password_label = Gtk.Template.Child()
    copy_password_button = Gtk.Template.Child()
    git_pull_button = Gtk.Template.Child()
    git_push_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    treeview_scrolled_window = Gtk.Template.Child() # ScrolledWindow for TreeView

    # We'll create the TreeView and its TreeStore programmatically
    # Gtk.TreeView itself is not easily templated if columns/renderers are complex.

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.password_store = PasswordStore() # Instantiate the password store

        self._build_treeview() # Create and set up the TreeView
        self._load_passwords() # Load passwords into the TreeView

        # Set initial state for details view
        self.details_stack.set_visible_child_name("placeholder")
        self.copy_password_button.set_sensitive(False)

        # Connect signals for buttons
        self.copy_password_button.connect("clicked", self.on_copy_password_clicked)
        self.git_pull_button.connect("clicked", self.on_git_pull_clicked)
        self.git_push_button.connect("clicked", self.on_git_push_clicked)

    def _build_treeview(self):
        # TreeStore: 0: display_name (str), 1: full_path (str), 2: is_folder (bool)
        self.tree_store = Gtk.TreeStore(str, str, bool)

        self.treeview = Gtk.TreeView(model=self.tree_store)
        self.treeview.set_headers_visible(False) # Simple list, no headers

        # Column for password/folder name
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Name", renderer_text, text=0)
        self.treeview.append_column(column_text)

        # Icon for folders (optional, could add another column with CellRendererPixbuf)
        # For simplicity, we'll rely on naming or visual cues from selection for now.

        selection = self.treeview.get_selection()
        selection.connect("changed", self.on_treeview_selection_changed)

        self.treeview_scrolled_window.set_child(self.treeview)


    def _load_passwords(self):
        self.tree_store.clear()
        raw_password_list = self.password_store.list_passwords() # This is a flat list of paths

        # Process the flat list into a hierarchical structure for TreeStore
        # This basic version adds all items at the root.
        # A more advanced version would parse paths like "Folder/Subfolder/Password"
        # and create parent iterators accordingly.

        # Simple hierarchical population (assumes paths like 'folder/password')
        # This needs a more robust parser for arbitrary depth.
        # For now, let's build a temporary dict structure.

        # root_nodes = {} # To store iterators for top-level folders/passwords
        # for path_str in raw_password_list:
        #     parts = path_str.split('/')
        #     current_level_nodes = root_nodes
        #     parent_iter = None
        #
        #     for i, part_name in enumerate(parts):
        #         is_last_part = (i == len(parts) - 1)
        #
        #         # Create a unique key for the current node in its level
        #         node_key = '/'.join(parts[:i+1])
        #
        #         if node_key not in current_level_nodes:
        #             # Item name, full_path_str, is_folder
        #             # For folders, full_path_str is the folder path itself.
        #             # For files (passwords), full_path_str is the password path.
        #             is_folder = not is_last_part
        #
        #             # For TreeStore: display_name, full_path_for_action, is_folder_bool
        #             # If it's a folder, full_path_for_action is its own path (used to identify it)
        #             # If it's a password, full_path_for_action is the password path.
        #
        #             # We need to determine if an entry is a folder or a file path
        #             # The current list_passwords only returns password files.
        #             # We need to enhance list_passwords to also return folders, or infer them.
        #
        #             # For now, let's assume list_passwords gives only actual password files.
        #             # We'll create folder nodes on the fly.
        #             # This is a simplified approach. A real implementation would be more robust.
        #
        #             # Temporary simplified approach: add all as root items
        #             # This does not build a visual hierarchy in the TreeView yet.
        #             # We will improve this later.
        #
        #             # display_name, full_path, is_folder
        #             self.tree_store.append(parent_iter, [part_name, path_str, False]) # All are files for now
        #             # current_level_nodes[node_key] = new_iter # Store iter for future children
        #             # parent_iter = new_iter
        #         else:
        #             parent_iter = current_level_nodes[node_key]

        # A more correct population for hierarchical data:
        iters = {} # To store iterators for folders: 'folder_path' -> iter
        for path_str in sorted(raw_password_list):
            parts = path_str.split(os.sep)
            current_path_slug = ""
            parent_iter = None
            for i, part_name in enumerate(parts):
                if current_path_slug == "":
                    current_path_slug = part_name
                else:
                    current_path_slug = os.path.join(current_path_slug, part_name)

                is_password_file = (i == len(parts) - 1)

                if current_path_slug not in iters:
                    # display_name, full_path_for_action, is_folder_bool
                    # For folders, full_path_for_action is the folder path.
                    # For passwords, full_path_for_action is the password path (what `pass` expects).
                    display_name = part_name
                    action_path = current_path_slug
                    is_folder = not is_password_file

                    new_iter = self.tree_store.append(parent_iter, [display_name, action_path, is_folder])
                    iters[current_path_slug] = new_iter
                    parent_iter = new_iter
                else:
                    parent_iter = iters[current_path_slug]

        # Expand first level by default (optional)
        # root_iter = self.tree_store.get_iter_first()
        # if root_iter:
        #     self.treeview.expand_row(self.tree_store.get_path(root_iter), False)


    def on_treeview_selection_changed(self, selection):
        model, tree_iter = selection.get_selected()
        if tree_iter is not None:
            full_path = model.get_value(tree_iter, 1) # column 1: full_path
            is_folder = model.get_value(tree_iter, 2) # column 2: is_folder

            self.selected_password_label.set_text(full_path) # Show full path for now
            self.details_stack.set_visible_child_name("details")

            if is_folder:
                self.copy_password_button.set_sensitive(False)
            else: # It's a password file
                self.copy_password_button.set_sensitive(True)
        else:
            self.details_stack.set_visible_child_name("placeholder")
            self.copy_password_button.set_sensitive(False)

    def on_copy_password_clicked(self, widget):
        model, tree_iter = self.treeview.get_selection().get_selected()
        if tree_iter is not None:
            password_path = model.get_value(tree_iter, 1)
            is_folder = model.get_value(tree_iter, 2)

            if not is_folder:
                success, message = self.password_store.copy_password(password_path)
                if success:
                    toast_message = f"Copied '{os.path.basename(password_path)}' to clipboard."
                    self.toast_overlay.add_toast(Adw.Toast.new(toast_message))
                else:
                    self.toast_overlay.add_toast(Adw.Toast.new(f"Error: {message}"))
            else:
                self.toast_overlay.add_toast(Adw.Toast.new("Cannot copy a folder."))


    def on_git_pull_clicked(self, widget):
        self.toast_overlay.add_toast(Adw.Toast.new("Pulling changes from remote..."))
        success, message = self.password_store.git_pull()
        if success:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Git pull successful! {message}"))
            self._load_passwords() # Refresh list after pull
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Git pull failed: {message}"))

    def on_git_push_clicked(self, widget):
        self.toast_overlay.add_toast(Adw.Toast.new("Pushing changes to remote..."))
        success, message = self.password_store.git_push()
        if success:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Git push successful! {message}"))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Git push failed: {message}"))
