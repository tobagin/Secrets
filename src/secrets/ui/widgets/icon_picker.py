import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/widgets/icon_picker.ui')
class IconPicker(Adw.Bin):
    """An icon picker widget with predefined icons for folders and passwords."""
    
    __gtype_name__ = "IconPicker"
    
    # Template widgets
    icon_flow_box = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'icon-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    # Predefined icons organized by category
    ICONS = [
        # General/Default
        "folder-symbolic",
        "dialog-password-symbolic",
        "document-properties-symbolic",
        "preferences-system-symbolic",
        
        # Technology/Web
        "network-wired-symbolic",
        "network-wireless-symbolic",
        "computer-symbolic",
        "phone-symbolic",
        
        # Communication
        "mail-send-symbolic",
        "user-info-symbolic",
        "system-users-symbolic",
        "avatar-default-symbolic",
        
        # Security
        "security-high-symbolic",
        "changes-prevent-symbolic",
        "channel-secure-symbolic",
        "key-symbolic",
        
        # Finance/Shopping
        "emblem-money-symbolic",
        "shopping-cart-symbolic",
        "credit-card-symbolic",
        "bank-symbolic",
    ]
    
    def __init__(self, selected_icon=None, **kwargs):
        super().__init__(**kwargs)
        self.selected_icon = selected_icon or self.ICONS[0]
        self._setup_icons()
    
    def _setup_icons(self):
        """Setup the icon selection flow box."""
        for icon_name in self.ICONS:
            icon_button = self._create_icon_button(icon_name)
            self.icon_flow_box.append(icon_button)
    
    def _create_icon_button(self, icon_name):
        """Create an icon selection button."""
        button = Gtk.Button()
        button.set_size_request(48, 48)
        button.add_css_class("circular")
        
        # Create icon
        icon = Gtk.Image()
        icon.set_from_icon_name(icon_name)
        icon.set_icon_size(Gtk.IconSize.LARGE)
        
        button.set_child(icon)
        
        # Add selection indicator if this is the selected icon
        if icon_name == self.selected_icon:
            button.add_css_class("suggested-action")
        
        # Connect click signal
        button.connect("clicked", self._on_icon_clicked, icon_name)
        
        return button
    
    def _on_icon_clicked(self, button, icon_name):
        """Handle icon button click."""
        # Update selection
        self.selected_icon = icon_name
        
        # Update button styles
        self._update_selection_styles()
        
        # Emit signal
        self.emit('icon-selected', icon_name)
    
    def _update_selection_styles(self):
        """Update the visual selection styles."""
        # Remove suggested-action class from all buttons
        child = self.icon_flow_box.get_first_child()
        while child:
            if isinstance(child, Gtk.Button):
                child.remove_css_class("suggested-action")
            child = child.get_next_sibling()
        
        # Add suggested-action class to selected button
        child = self.icon_flow_box.get_first_child()
        icon_index = 0
        while child and icon_index < len(self.ICONS):
            if isinstance(child, Gtk.Button) and self.ICONS[icon_index] == self.selected_icon:
                child.add_css_class("suggested-action")
                break
            if isinstance(child, Gtk.Button):
                icon_index += 1
            child = child.get_next_sibling()
    
    def get_selected_icon(self):
        """Get the currently selected icon."""
        return self.selected_icon
    
    def set_selected_icon(self, icon_name):
        """Set the selected icon."""
        if icon_name in self.ICONS:
            self.selected_icon = icon_name
            self._update_selection_styles()


if __name__ == '__main__':
    # Test the icon picker
    app = Adw.Application(application_id="com.example.testiconpicker")
    
    def on_activate(application):
        window = Adw.ApplicationWindow(application=application)
        window.set_default_size(400, 300)
        
        icon_picker = IconPicker()
        icon_picker.connect('icon-selected', lambda picker, icon: print(f"Selected icon: {icon}"))
        
        window.set_content(icon_picker)
        window.present()
    
    app.connect("activate", on_activate)
    app.run([])
