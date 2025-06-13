import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GObject # Added GObject for custom TreeStore columns
import os # For path manipulation in list_passwords if needed, though logic is in PasswordStore

from .password_store import PasswordStore
from .edit_dialog import EditPasswordDialog
from .move_rename_dialog import MoveRenameDialog
from .add_password_dialog import AddPasswordDialog # Added

@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/secrets.ui')
class SecretsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SecretsWindow"

    # Define template children for UI elements defined in secrets.ui
    details_stack = Gtk.Template.Child()
    selected_password_label = Gtk.Template.Child()
    copy_password_button = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()
    remove_button = Gtk.Template.Child()
    move_rename_button = Gtk.Template.Child()
    add_password_button = Gtk.Template.Child() # Added
    git_pull_button = Gtk.Template.Child()
    git_push_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    treeview_scrolled_window = Gtk.Template.Child() # ScrolledWindow for TreeView
    search_entry = Gtk.Template.Child()

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
        self.edit_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)
        self.move_rename_button.set_sensitive(False) # Added

        # Connect signals for buttons
        self.copy_password_button.connect("clicked", self.on_copy_password_clicked)
        self.edit_button.connect("clicked", self.on_edit_button_clicked)
        self.remove_button.connect("clicked", self.on_remove_button_clicked)
        self.move_rename_button.connect("clicked", self.on_move_rename_button_clicked)
        self.add_password_button.connect("clicked", self.on_add_password_button_clicked) # Added
        self.git_pull_button.connect("clicked", self.on_git_pull_clicked)
        self.git_push_button.connect("clicked", self.on_git_push_clicked)
        self.search_entry.connect("search-changed", self.on_search_entry_changed)

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

            self.selected_password_label.set_text(os.path.basename(full_path)) # Show just name, not full path
            self.details_stack.set_visible_child_name("details")

            if is_folder:
                self.copy_password_button.set_sensitive(False)
                self.edit_button.set_sensitive(False)
                self.remove_button.set_sensitive(False)
                # self.move_rename_button.set_sensitive(True) # Allow moving folders
            else: # It's a password file
                self.copy_password_button.set_sensitive(True)
                self.edit_button.set_sensitive(True)
                self.remove_button.set_sensitive(True)
            self.move_rename_button.set_sensitive(True) # Enable if any item (file or folder) is selected
        else:
            self.details_stack.set_visible_child_name("placeholder")
            self.copy_password_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)
            self.move_rename_button.set_sensitive(False)

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

    def on_edit_button_clicked(self, widget):
        model, tree_iter = self.treeview.get_selection().get_selected()
        if tree_iter is not None:
            password_path = model.get_value(tree_iter, 1) # full_path
            is_folder = model.get_value(tree_iter, 2)

            if is_folder:
                self.toast_overlay.add_toast(Adw.Toast.new("Cannot edit a folder."))
                return

            success, content_or_error = self.password_store.get_password_content(password_path)
            if success:
                current_content = content_or_error
                # Create and show the edit dialog
                dialog = EditPasswordDialog(
                    password_path=password_path,
                    password_content=current_content,
                    transient_for_window=self
                )
                dialog.connect("save-requested", self.on_edit_dialog_save_requested)
                dialog.present()
            else:
                # content_or_error is the error message here
                self.toast_overlay.add_toast(Adw.Toast.new(f"Error fetching content: {content_or_error}"))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("No item selected to edit."))

    def on_edit_dialog_save_requested(self, dialog, path, new_content):
        # This method will call self.password_store.insert_password()
        success, message = self.password_store.insert_password(path, new_content, multiline=True, force=True)
        # The 'force=True' is important for overwriting the existing password when editing.

        if success:
            self.toast_overlay.add_toast(Adw.Toast.new(message))
            # If content displayed in the main list changes (e.g. first line summary),
            # you might need to update the TreeStore item or reload.
            # For now, assuming edit doesn't change its representation in the list.
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Error saving: {message}"))

        dialog.close() # Close the dialog after handling

    def on_remove_button_clicked(self, widget):
        model, tree_iter = self.treeview.get_selection().get_selected()
        if tree_iter is not None:
            password_path = model.get_value(tree_iter, 1) # full_path
            is_folder = model.get_value(tree_iter, 2) # is_folder

            if is_folder:
                self.toast_overlay.add_toast(Adw.Toast.new("Cannot delete a folder directly. Remove its contents first."))
                return

            dialog = Adw.MessageDialog(
                heading=f"Delete '{os.path.basename(password_path)}'?",
                body=f"Are you sure you want to permanently delete the password entry for '{password_path}'?",
                transient_for=self,
                modal=True
            )
            dialog.add_response("cancel", "_Cancel")
            dialog.add_response("delete", "_Delete")
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            dialog.connect("response", self.on_delete_confirm_response, password_path) # Pass path to handler
            dialog.present()

    def on_delete_confirm_response(self, dialog, response_id, password_path):
        if response_id == "delete":
            success, message = self.password_store.delete_password(password_path)
            if success:
                self.toast_overlay.add_toast(Adw.Toast.new(message))
                self._load_passwords() # Refresh the list
                # After deletion, selection will be lost, on_treeview_selection_changed should handle UI update
                # Or explicitly set details_stack to placeholder here:
                self.details_stack.set_visible_child_name("placeholder")
                self.copy_password_button.set_sensitive(False)
                self.edit_button.set_sensitive(False) # Also disable edit button
                self.remove_button.set_sensitive(False) # And remove button itself
            else:
                self.toast_overlay.add_toast(Adw.Toast.new(f"Error: {message}"))
        dialog.close() # Ensure dialog is closed

    def on_search_entry_changed(self, search_entry):
        query = search_entry.get_text().strip()

        if not query:
            # If query is empty, reload the full hierarchical list
            self._load_passwords()
            return

        # If there's a query, perform search
        success, result = self.password_store.search_passwords(query)

        self.tree_store.clear() # Clear existing items

        if success:
            if result: # If there are matching paths
                for path_str in sorted(result): # `result` is a list of paths from `pass grep`
                    # For search results, we display them as a flat list.
                    # display_name, full_path_for_action, is_folder_bool
                    # We might not easily know if a grep result path itself is a folder
                    # without further checks. `pass grep` usually returns paths to files.
                    # Assuming results from `pass grep` are actual password entries (not folders).
                    display_name = os.path.basename(path_str)
                    # Or, to give more context for search results:
                    # display_name = path_str

                    self.tree_store.append(None, [path_str, path_str, False]) # Display full path as name
            else: # No results found
                # Optionally, show a "No results found" in the TreeView area or a toast
                # For now, an empty tree indicates no results.
                # You could add a root item: self.tree_store.append(None, ["No results found.", "", True])
                pass
        else:
            # result contains the error message
            self.toast_overlay.add_toast(Adw.Toast.new(f"Search error: {result}"))
            # Optionally, restore full list on error:
            # self._load_passwords()

    def on_move_rename_button_clicked(self, widget):
        model, tree_iter = self.treeview.get_selection().get_selected()
        if tree_iter is not None:
            current_path = model.get_value(tree_iter, 1) # full_path

            dialog = MoveRenameDialog(
                current_path=current_path,
                transient_for_window=self
            )
            dialog.connect("save-requested", self.on_move_rename_dialog_save_requested)
            dialog.present()
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("No item selected to move/rename."))

    def on_move_rename_dialog_save_requested(self, dialog, old_path, new_path):
        success, message = self.password_store.move_password(old_path, new_path)

        if success:
            self.toast_overlay.add_toast(Adw.Toast.new(message))
            self._load_passwords() # Refresh the entire list as paths have changed
            # Selection will be lost, on_treeview_selection_changed will handle UI reset
            self.details_stack.set_visible_child_name("placeholder") # Explicitly reset view
            self.copy_password_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)
            self.move_rename_button.set_sensitive(False)
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Error: {message}"))

        dialog.close()

    def on_add_password_button_clicked(self, widget):
        suggested_path = ""
        model, tree_iter = self.treeview.get_selection().get_selected()
        if tree_iter is not None:
            path = model.get_value(tree_iter, 1) # full_path
            is_folder = model.get_value(tree_iter, 2) # is_folder
            if is_folder:
                suggested_path = path # Pass the folder path as suggestion
            else:
                # If a file is selected, suggest its parent folder
                suggested_path = os.path.dirname(path) if os.path.dirname(path) else ""

        dialog = AddPasswordDialog(
            transient_for_window=self,
            suggested_folder_path=suggested_path
        )
        dialog.connect("add-requested", self.on_add_dialog_add_requested)
        dialog.present()

    def on_add_dialog_add_requested(self, dialog, path, content):
        # Use force=False to prevent overwriting existing entries by mistake.
        # `pass insert` without -f will fail if the entry already exists.
        success, message = self.password_store.insert_password(path, content, multiline=True, force=False)

        if success:
            self.toast_overlay.add_toast(Adw.Toast.new(message))
            self._load_passwords() # Refresh the list
        else:
            # Check if the error message indicates it already exists
            if "already exists" in message.lower(): # Crude check, but often pass says this
                # More specific error for this case
                error_toast_msg = f"Error: '{path}' already exists. Choose a different name or path."
            else:
                error_toast_msg = f"Error adding password: {message}"
            self.toast_overlay.add_toast(Adw.Toast.new(error_toast_msg))

        # Only close dialog on success, or provide a way for user to correct path?
        # For now, let's close it always, user can re-open if path was bad.
        # A better UX might keep dialog open on "already exists" and highlight path field.
        dialog.close()
