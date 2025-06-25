import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class ShortcutsWindow(Adw.Window):
    """Keyboard shortcuts help window."""

    __gtype_name__ = "ShortcutsWindow"

    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)

        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_title("Keyboard Shortcuts")
        self.set_default_size(600, 700)

        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Setup the shortcuts window content."""
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(content_box)

        # Header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Keyboard Shortcuts"))

        header_bar.pack_end(close_button)

        content_box.append(header_bar)

        # Scrolled window for shortcuts
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        content_box.append(scrolled)

        # Main shortcuts box
        shortcuts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        shortcuts_box.set_margin_top(12)
        shortcuts_box.set_margin_bottom(12)
        shortcuts_box.set_margin_start(12)
        shortcuts_box.set_margin_end(12)
        scrolled.set_child(shortcuts_box)
        
        # Application group
        app_group = Adw.PreferencesGroup()
        app_group.set_title("Application")
        shortcuts_box.append(app_group)

        self._add_shortcut_row(app_group, "Quit", "Ctrl+Q")
        self._add_shortcut_row(app_group, "Preferences", "Ctrl+,")
        self._add_shortcut_row(app_group, "About", "Ctrl+?")

        # Password management group
        password_group = Adw.PreferencesGroup()
        password_group.set_title("Password Management")
        shortcuts_box.append(password_group)

        self._add_shortcut_row(password_group, "Add New Password", "Ctrl+N")
        self._add_shortcut_row(password_group, "Edit Selected Password", "Ctrl+E")
        self._add_shortcut_row(password_group, "Delete Selected Password", "Delete")
        self._add_shortcut_row(password_group, "Copy Password", "Ctrl+C")
        self._add_shortcut_row(password_group, "Copy Username", "Ctrl+Shift+C")

        # Navigation group
        nav_group = Adw.PreferencesGroup()
        nav_group.set_title("Navigation")
        shortcuts_box.append(nav_group)

        self._add_shortcut_row(nav_group, "Focus Search", "Ctrl+F")
        self._add_shortcut_row(nav_group, "Clear Search", "Escape")
        self._add_shortcut_row(nav_group, "Refresh Password List", "F5")

        # Git group
        #git_group = Adw.PreferencesGroup()
        #git_group.set_title("Git Operations")
        #shortcuts_box.append(git_group)

        #self._add_shortcut_row(git_group, "Git Pull", "Ctrl+Shift+P")
        #self._add_shortcut_row(git_group, "Git Push", "Ctrl+Shift+U")
        #self._add_shortcut_row(git_group, "Git Status", "Ctrl+Shift+S")
        #self._add_shortcut_row(git_group, "Git Setup", "Ctrl+Shift+G")

        # View group
        view_group = Adw.PreferencesGroup()
        view_group.set_title("View")
        shortcuts_box.append(view_group)

        self._add_shortcut_row(view_group, "Toggle Password Visibility", "Ctrl+H")
        self._add_shortcut_row(view_group, "Generate Password", "Ctrl+G")

    def _add_shortcut_row(self, group, title, shortcut):
        """Add a shortcut row to a group."""
        row = Adw.ActionRow()
        row.set_title(title)

        # Create shortcut label
        shortcut_label = Gtk.Label(label=shortcut)
        shortcut_label.set_valign(Gtk.Align.CENTER)

        row.add_suffix(shortcut_label)
        group.add(row)
