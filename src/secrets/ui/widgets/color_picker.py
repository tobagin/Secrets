import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gdk
from ...app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/widgets/color_picker.ui')
class ColorPicker(Adw.Bin):
    """A color picker widget with predefined colors for folders and passwords."""
    
    __gtype_name__ = "ColorPicker"
    
    # Template widgets
    color_flow_box = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'color-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    # Predefined colors for folders and passwords
    COLORS = [
        "#3584e4",  # Blue
        "#33d17a",  # Green
        "#f6d32d",  # Yellow
        "#ff7800",  # Orange
        "#e01b24",  # Red
        "#9141ac",  # Purple
        "#986a44",  # Brown
        "#77767b",  # Gray
        "#2ec27e",  # Mint
        "#62a0ea",  # Light Blue
        "#f9f06b",  # Light Yellow
        "#ffbe6f",  # Light Orange
        "#f66151",  # Light Red
        "#dc8add",  # Light Purple
        "#c0bfbc",  # Light Gray
        "#26a269",  # Dark Green
    ]
    
    def __init__(self, selected_color=None, **kwargs):
        super().__init__(**kwargs)
        self.selected_color = selected_color or self.COLORS[0]
        self._setup_colors()
    
    def _setup_colors(self):
        """Setup the color selection flow box."""
        for color in self.COLORS:
            color_button = self._create_color_button(color)
            self.color_flow_box.append(color_button)
    
    def _create_color_button(self, color):
        """Create a color selection button."""
        button = Gtk.Button()
        button.set_size_request(40, 40)
        button.add_css_class("circular")
        
        # Create a colored box
        color_box = Gtk.Box()
        color_box.set_size_request(32, 32)
        color_box.add_css_class("color-swatch")
        
        # Set the background color using CSS
        css_provider = Gtk.CssProvider()
        css_data = f"""
        .color-swatch {{
            background-color: {color};
            border-radius: 16px;
        }}
        """
        css_provider.load_from_data(css_data.encode())
        
        # Apply CSS to the color box
        style_context = color_box.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        button.set_child(color_box)
        
        # Add selection indicator if this is the selected color
        if color == self.selected_color:
            button.add_css_class("suggested-action")
        
        # Connect click signal
        button.connect("clicked", self._on_color_clicked, color)
        
        return button
    
    def _on_color_clicked(self, button, color):
        """Handle color button click."""
        # Update selection
        self.selected_color = color
        
        # Update button styles
        self._update_selection_styles()
        
        # Emit signal
        self.emit('color-selected', color)
    
    def _update_selection_styles(self):
        """Update the visual selection styles."""
        # Remove suggested-action class from all buttons
        child = self.color_flow_box.get_first_child()
        while child:
            if isinstance(child, Gtk.Button):
                child.remove_css_class("suggested-action")
            child = child.get_next_sibling()
        
        # Add suggested-action class to selected button
        child = self.color_flow_box.get_first_child()
        color_index = 0
        while child and color_index < len(self.COLORS):
            if isinstance(child, Gtk.Button) and self.COLORS[color_index] == self.selected_color:
                child.add_css_class("suggested-action")
                break
            if isinstance(child, Gtk.Button):
                color_index += 1
            child = child.get_next_sibling()
    
    def get_selected_color(self):
        """Get the currently selected color."""
        return self.selected_color
    
    def set_selected_color(self, color):
        """Set the selected color."""
        if color in self.COLORS:
            self.selected_color = color
            self._update_selection_styles()


if __name__ == '__main__':
    # Test the color picker
    app = Adw.Application(application_id="com.example.testcolorpicker")
    
    def on_activate(application):
        window = Adw.ApplicationWindow(application=application)
        window.set_default_size(400, 300)
        
        color_picker = ColorPicker()
        color_picker.connect('color-selected', lambda picker, color: print(f"Selected color: {color}"))
        
        window.set_content(color_picker)
        window.present()
    
    app.connect("activate", on_activate)
    app.run([])
