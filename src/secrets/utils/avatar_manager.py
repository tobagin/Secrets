"""
AvatarManager utility for centralizing avatar, icon, and color management.

This utility eliminates duplication in avatar setup code that was scattered
across multiple dialog classes and UI components.
"""

import gi
from typing import Optional, List, Tuple, Union, Dict
from dataclasses import dataclass

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Pango", "1.0")

from gi.repository import Gtk, Adw, Gdk, GdkPixbuf, Pango
from ..ui.widgets.color_paintable import ColorPaintable


@dataclass
class AvatarConfiguration:
    """Configuration for avatar appearance."""
    size: int = 32
    fallback_icon: str = "dialog-password-symbolic"
    default_color: str = "#3584e4"  # Default blue
    use_rounded: bool = True


@dataclass
class IconInfo:
    """Information about an available icon."""
    name: str
    display_name: str
    category: str = "general"
    description: str = ""


class AvatarManager:
    """
    Centralized manager for avatar, icon, and color operations.
    
    This class provides a unified interface for:
    - Setting up color and icon avatars
    - Managing icon lists and selections
    - Handling color picker operations
    - Providing consistent avatar styling
    """
    
    # Default icon sets for different use cases (sorted by display name)
    PASSWORD_ICONS = sorted([
        # Security (4 icons)
        IconInfo("application-certificate-symbolic", "API Key", "security", "API keys/tokens"),
        IconInfo("io.github.tobagin.secrets-banking-symbolic", "Banking", "financial", "Banking/cards"),
        IconInfo("security-high-symbolic", "Certificate", "security", "Certificates/2FA"),
        IconInfo("io.github.tobagin.secrets-chat-symbolic", "Chat", "communication", "Messaging apps"),
        IconInfo("io.github.tobagin.secrets-cloud-symbolic", "Cloud", "web", "Cloud services"),
        IconInfo("io.github.tobagin.secrets-development-symbolic", "Development", "work", "Development tools"),
        IconInfo("text-x-generic-symbolic", "Document", "organization", "Documents/files"),
        IconInfo("mail-unread-symbolic", "Email", "communication", "Email accounts"),
        IconInfo("folder-symbolic", "Folder", "organization", "Folders/categories"),
        IconInfo("io.github.tobagin.secrets-gaming-symbolic", "Gaming", "entertainment", "Gaming"),
        IconInfo("emblem-important-symbolic", "Important", "organization", "Important/favorites"),
        IconInfo("web-browser-symbolic", "Internet", "web", "Online services"),
        IconInfo("multimedia-player-symbolic", "Media", "entertainment", "Streaming/media"),
        IconInfo("folder-music-symbolic", "Music", "entertainment", "Music services"),
        IconInfo("network-wireless-symbolic", "Network", "utilities", "Network devices"),
        IconInfo("io.github.tobagin.secrets-office-symbolic", "Office", "work", "Office/productivity"),
        IconInfo("dialog-password-symbolic", "Password", "security", "Generic password"),
        IconInfo("user-info-symbolic", "Personal", "personal", "Personal accounts"),
        IconInfo("system-lock-screen-symbolic", "Security", "security", "Security/encryption"),
        IconInfo("network-server-symbolic", "Server", "work", "Servers/hosting"),
        IconInfo("io.github.tobagin.secrets-shopping-symbolic", "Shopping", "financial", "Shopping/commerce"),
        IconInfo("system-users-symbolic", "Social", "communication", "Social media"),
        IconInfo("preferences-system-symbolic", "System", "utilities", "System/settings"),
        IconInfo("utilities-terminal-symbolic", "Terminal", "work", "SSH/command line"),
        IconInfo("io.github.tobagin.secrets-trading-symbolic", "Trading", "financial", "Trading/crypto"),
        IconInfo("applications-utilities-symbolic", "Utilities", "utilities", "Utilities/tools"),
        IconInfo("camera-video-symbolic", "Video", "entertainment", "Video/TV services"),
        IconInfo("io.github.tobagin.secrets-wallet-symbolic", "Wallet", "financial", "Digital wallets"),
        IconInfo("io.github.tobagin.secrets-website-symbolic", "Website", "web", "Websites"),
        IconInfo("system-file-manager-symbolic", "Work", "work", "Work accounts")
    ], key=lambda icon: icon.display_name)
    
    # Folder icons use the same comprehensive set as passwords (sorted by display name)
    FOLDER_ICONS = PASSWORD_ICONS
    
    # Default color palette
    DEFAULT_COLORS = [
        "#3584e4",  # Blue
        "#9141ac",  # Purple  
        "#ff6b6b",  # Red
        "#51cf66",  # Green
        "#ffd43b",  # Yellow
        "#fd7e14",  # Orange
        "#845ec2",  # Violet
        "#0ca678",  # Teal
        "#495057",  # Gray
        "#e03131",  # Dark Red
        "#1971c2",  # Dark Blue
        "#087f5b",  # Dark Green
    ]

    def __init__(self, config: Optional[AvatarConfiguration] = None):
        """Initialize the avatar manager with optional configuration."""
        self.config = config or AvatarConfiguration()
        self._color_picker = None
        self._icon_model_cache = {}

    def setup_color_avatar(self, avatar: Adw.Avatar, color: str, size: Optional[int] = None) -> None:
        """
        Setup a color avatar with the specified color.
        
        Args:
            avatar: The Adw.Avatar widget to configure
            color: Hex color string (e.g., "#ff6b6b")
            size: Optional size override
        """
        avatar_size = size or self.config.size
        paintable = ColorPaintable(color, avatar_size)
        avatar.set_custom_image(paintable)
        avatar.set_size(avatar_size)
        
        # Set accessibility information
        self._set_avatar_accessibility(avatar, f"Color avatar with {color}")

    def setup_icon_avatar(self, avatar: Adw.Avatar, icon_name: str, size: Optional[int] = None) -> None:
        """
        Setup an icon avatar with the specified icon.
        
        Args:
            avatar: The Adw.Avatar widget to configure
            icon_name: Icon name (e.g., "dialog-password-symbolic")
            size: Optional size override
        """
        avatar_size = size or self.config.size
        avatar.set_icon_name(icon_name)
        avatar.set_size(avatar_size)
        
        # Set accessibility information
        self._set_avatar_accessibility(avatar, f"Icon avatar with {icon_name}")

    def setup_text_avatar(self, avatar: Adw.Avatar, text: str, size: Optional[int] = None) -> None:
        """
        Setup a text avatar with initials or text.
        
        Args:
            avatar: The Adw.Avatar widget to configure
            text: Text to display (will extract initials)
            size: Optional size override
        """
        avatar_size = size or self.config.size
        avatar.set_text(text)
        avatar.set_size(avatar_size)
        
        # Set accessibility information
        self._set_avatar_accessibility(avatar, f"Text avatar with initials '{text}'")

    def create_icon_model(self, icon_set: str = "password") -> Gtk.ListStore:
        """
        Create a model for icon selection.
        
        Args:
            icon_set: Type of icons ("password", "folder", or "all")
            
        Returns:
            Gtk.ListStore with IconInfo objects
        """
        # Check cache first
        if icon_set in self._icon_model_cache:
            return self._icon_model_cache[icon_set]
        
        model = Gtk.ListStore.new([object])  # Store IconInfo objects
        
        # Select appropriate icon set
        if icon_set == "password":
            icons = self.PASSWORD_ICONS
        elif icon_set == "folder":
            icons = self.FOLDER_ICONS
        elif icon_set == "all":
            icons = self.PASSWORD_ICONS + self.FOLDER_ICONS
        else:
            icons = self.PASSWORD_ICONS  # Default fallback
        
        # Add icons to model
        for icon_info in icons:
            tree_iter = model.append()
            model.set_value(tree_iter, 0, icon_info)
        
        # Cache the model
        self._icon_model_cache[icon_set] = model
        return model

    def setup_icon_combo_row(self, combo_row: Adw.ComboRow, icon_set: str = "password", 
                           selected_icon: Optional[str] = None) -> None:
        """
        Setup a combo row for icon selection.
        
        Args:
            combo_row: The ComboRow to configure
            icon_set: Type of icons to display
            selected_icon: Initially selected icon name
        """
        # Create string list model instead of complex model for simpler binding
        model = Gtk.StringList()
        
        # Get appropriate icon set
        if icon_set == "password":
            icons = self.PASSWORD_ICONS
        elif icon_set == "folder":
            icons = self.FOLDER_ICONS
        elif icon_set == "all":
            icons = self.PASSWORD_ICONS + self.FOLDER_ICONS
        else:
            icons = self.PASSWORD_ICONS
        
        # Add icon names to model
        selected_index = 0
        for i, icon_info in enumerate(icons):
            model.append(icon_info.name)
            if selected_icon and icon_info.name == selected_icon:
                selected_index = i
        
        combo_row.set_model(model)
        
        # Setup custom factory for icon display
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._on_icon_item_setup)
        factory.connect('bind', self._on_icon_item_bind)
        combo_row.set_factory(factory)
        
        # Set initial selection
        combo_row.set_selected(selected_index)

    def get_selected_icon_from_combo(self, combo_row: Adw.ComboRow) -> Optional[str]:
        """
        Get the selected icon name from a combo row.
        
        Args:
            combo_row: The ComboRow to query
            
        Returns:
            Selected icon name or None
        """
        selected_item = combo_row.get_selected_item()
        if selected_item and hasattr(selected_item, 'get_string'):
            return selected_item.get_string()
        return None

    def create_color_picker_button(self, initial_color: str = None, 
                                 parent_window: Optional[Gtk.Window] = None) -> Gtk.Button:
        """
        Create a color picker button with preview.
        
        Args:
            initial_color: Initial color to display
            parent_window: Parent window for color picker dialog
            
        Returns:
            Configured color picker button
        """
        button = Gtk.Button()
        button.add_css_class("flat")
        
        # Set initial color
        color = initial_color or self.config.default_color
        self._update_color_button_preview(button, color)
        
        # Store color and parent for later use
        button.set_data("current_color", color)
        button.set_data("parent_window", parent_window)
        
        # Connect click handler
        button.connect('clicked', self._on_color_button_clicked)
        
        return button

    def get_color_from_button(self, button: Gtk.Button) -> str:
        """
        Get the current color from a color picker button.
        
        Args:
            button: The color picker button
            
        Returns:
            Current color as hex string
        """
        return button.get_data("current_color") or self.config.default_color

    def set_color_on_button(self, button: Gtk.Button, color: str) -> None:
        """
        Set the color on a color picker button.
        
        Args:
            button: The color picker button
            color: New color as hex string
        """
        button.set_data("current_color", color)
        self._update_color_button_preview(button, color)

    def get_icon_info(self, icon_name: str, icon_set: str = "password") -> Optional[IconInfo]:
        """
        Get information about a specific icon.
        
        Args:
            icon_name: Name of the icon
            icon_set: Icon set to search in
            
        Returns:
            IconInfo object or None if not found
        """
        # Select appropriate icon set
        if icon_set == "password":
            icons = self.PASSWORD_ICONS
        elif icon_set == "folder":
            icons = self.FOLDER_ICONS
        elif icon_set == "all":
            icons = self.PASSWORD_ICONS + self.FOLDER_ICONS
        else:
            icons = self.PASSWORD_ICONS
        
        # Find icon info
        for icon_info in icons:
            if icon_info.name == icon_name:
                return icon_info
        
        return None

    def get_default_color_for_type(self, item_type: str) -> str:
        """
        Get default color for different item types.
        
        Args:
            item_type: Type of item ("password", "folder", "important", etc.)
            
        Returns:
            Default color as hex string
        """
        color_map = {
            "password": "#9141ac",  # Purple
            "folder": "#fd7e14",    # Orange
            "important": "#e03131", # Red
            "secure": "#087f5b",    # Dark Green
            "personal": "#1971c2",  # Dark Blue
            "work": "#495057",      # Gray
            "social": "#51cf66",    # Green
            "financial": "#ffd43b", # Yellow
        }
        
        return color_map.get(item_type.lower(), self.config.default_color)

    def get_default_icon_for_type(self, item_type: str) -> str:
        """
        Get default icon for different item types.
        
        Args:
            item_type: Type of item ("password", "folder", etc.)
            
        Returns:
            Default icon name
        """
        icon_map = {
            "password": "dialog-password-symbolic",
            "folder": "folder-symbolic",
            "website": "io.github.tobagin.secrets-website-symbolic",
            "email": "mail-unread-symbolic",
            "social": "system-users-symbolic",
            "banking": "io.github.tobagin.secrets-banking-symbolic",
            "financial": "io.github.tobagin.secrets-wallet-symbolic",
            "gaming": "io.github.tobagin.secrets-gaming-symbolic",
            "work": "system-file-manager-symbolic",
            "development": "io.github.tobagin.secrets-development-symbolic",
            "server": "network-server-symbolic",
            "network": "network-wireless-symbolic",
            "document": "text-x-generic-symbolic",
            "system": "preferences-system-symbolic",
            "security": "system-lock-screen-symbolic",
            "api": "application-certificate-symbolic",
            "cloud": "io.github.tobagin.secrets-cloud-symbolic",
            "music": "folder-music-symbolic",
            "video": "camera-video-symbolic",
            "shopping": "io.github.tobagin.secrets-shopping-symbolic",
            "trading": "io.github.tobagin.secrets-trading-symbolic",
            "important": "emblem-important-symbolic",
            "chat": "io.github.tobagin.secrets-chat-symbolic",
            "office": "io.github.tobagin.secrets-office-symbolic"
        }
        
        return icon_map.get(item_type.lower(), self.config.fallback_icon)

    # Private methods

    def _set_avatar_accessibility(self, avatar: Adw.Avatar, description: str) -> None:
        """Set accessibility information for an avatar."""
        try:
            from ...utils import AccessibilityHelper
            AccessibilityHelper.set_accessible_description(avatar, description)
        except ImportError:
            # Fallback if AccessibilityHelper not available
            pass

    def _on_icon_item_setup(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        """Setup icon list item widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        icon = Gtk.Image()
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        
        label = Gtk.Label()
        label.set_xalign(0)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        
        box.append(icon)
        box.append(label)
        list_item.set_child(box)

    def _on_icon_item_bind(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        """Bind data to icon list item."""
        box = list_item.get_child()
        if not box:
            return
        
        icon = box.get_first_child()
        if not icon:
            return
            
        label = icon.get_next_sibling()
        if not label:
            return
        
        string_obj = list_item.get_item()
        icon_name = string_obj.get_string()
        
        # Set icon
        icon.set_from_icon_name(icon_name)
        
        # Set label with icon info if available
        icon_info = self.get_icon_info(icon_name, "all")
        if icon_info:
            label.set_text(icon_info.display_name)
            label.set_tooltip_text(icon_info.description)
        else:
            label.set_text(icon_name)

    def _on_color_button_clicked(self, button: Gtk.Button) -> None:
        """Handle color button click."""
        from ..widgets import ColorPicker  # Import here to avoid circular imports
        
        parent_window = button.get_data("parent_window")
        current_color = button.get_data("current_color") or self.config.default_color
        
        if not self._color_picker:
            self._color_picker = ColorPicker()
            if parent_window:
                self._color_picker.set_transient_for(parent_window)
        
        # Store reference to button for callback
        self._color_picker.set_data("target_button", button)
        self._color_picker.set_selected_color(current_color)
        self._color_picker.connect('response', self._on_color_picker_response)
        self._color_picker.present()

    def _on_color_picker_response(self, dialog: Gtk.Dialog, response_id: int) -> None:
        """Handle color picker dialog response."""
        if response_id == Gtk.ResponseType.OK:
            button = dialog.get_data("target_button")
            if button:
                new_color = dialog.get_selected_color()
                self.set_color_on_button(button, new_color)
                
                # Emit a custom signal on the button for listeners
                button.emit('notify::tooltip-text')  # Use existing signal as notification

    def _update_color_button_preview(self, button: Gtk.Button, color: str) -> None:
        """Update the color preview on a color picker button."""
        # Create a small color preview image
        try:
            paintable = ColorPaintable(color, 16)
            image = Gtk.Image.new_from_paintable(paintable)
            button.set_child(image)
            button.set_tooltip_text(f"Color: {color}")
        except Exception:
            # Fallback to text if color preview fails
            button.set_label("Color")
            button.set_tooltip_text(f"Color: {color}")


# Convenience functions for common operations

def setup_password_avatar(avatar: Adw.Avatar, color: str = "#9141ac", 
                         icon: str = "dialog-password-symbolic", size: int = 32) -> None:
    """
    Convenience function to setup a password avatar.
    
    Args:
        avatar: The avatar widget
        color: Avatar color
        icon: Avatar icon
        size: Avatar size
    """
    manager = AvatarManager(AvatarConfiguration(size=size))
    
    if color and color != "none":
        manager.setup_color_avatar(avatar, color, size)
    else:
        manager.setup_icon_avatar(avatar, icon, size)


def setup_folder_avatar(avatar: Adw.Avatar, color: str = "#fd7e14", 
                       icon: str = "folder-symbolic", size: int = 32) -> None:
    """
    Convenience function to setup a folder avatar.
    
    Args:
        avatar: The avatar widget  
        color: Avatar color
        icon: Avatar icon
        size: Avatar size
    """
    manager = AvatarManager(AvatarConfiguration(size=size))
    
    if color and color != "none":
        manager.setup_color_avatar(avatar, color, size)
    else:
        manager.setup_icon_avatar(avatar, icon, size)


def create_avatar_manager() -> AvatarManager:
    """Create a default avatar manager instance."""
    return AvatarManager()