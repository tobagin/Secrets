"""
Password row widget for displaying individual passwords in the list.
"""

import gi
import os
import base64
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, GdkPixbuf, Gio
from .color_paintable import ColorPaintable
from ...managers.favicon_manager import get_favicon_manager
from ...app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/widgets/password_row.ui')
class PasswordRow(Adw.ActionRow):
    """Custom widget for displaying a password entry in the list."""
    
    __gtype_name__ = "PasswordRow"
    
    # Template widgets
    password_avatar = Gtk.Template.Child()
    action_button = Gtk.Template.Child()
    
    def __init__(self, password_entry=None, **kwargs):
        """
        Initialize the password row.
        
        Args:
            password_entry: The password entry data to display
        """
        super().__init__(**kwargs)
        self._password_entry = password_entry
        self._setup_signals()
        
        if password_entry:
            self.set_password_entry(password_entry)
    
    def _setup_signals(self):
        """Set up button signal connections."""
        self.action_button.connect('clicked', self._on_action_button_clicked)
    
    def set_password_entry(self, password_entry):
        """
        Set the password entry data for this row.
        
        Args:
            password_entry: The password entry data to display
        """
        self._password_entry = password_entry
        
        if password_entry:
            # Set the title to the password name
            self.set_title(password_entry.name)
            
            # Set subtitle based on available metadata
            subtitle_parts = []
            if hasattr(password_entry, 'username') and password_entry.username:
                subtitle_parts.append(f"User: {password_entry.username}")
            if hasattr(password_entry, 'url') and password_entry.url:
                subtitle_parts.append(f"URL: {password_entry.url}")
            
            if subtitle_parts:
                self.set_subtitle(" • ".join(subtitle_parts))
            else:
                self.set_subtitle(password_entry.path)
    
    def get_password_entry(self):
        """Get the password entry associated with this row."""
        return self._password_entry

    def set_avatar_color_and_icon(self, color, icon_name, url=None, favicon_data=None):
        """Set the avatar color and icon, with optional favicon for URLs or cached base64 data."""
        self._color = color
        self._icon_name = icon_name
        self._url = url

        # First check if we have cached favicon data (base64)
        if favicon_data:
            try:
                pixbuf = self._base64_to_pixbuf(favicon_data)
                if pixbuf:
                    self._on_favicon_loaded(pixbuf)
                    return
            except Exception as e:
                print(f"Error loading cached favicon data: {e}")
                # Continue to try downloading

        # If URL is provided and no cached favicon, try to download
        if url and url.strip():
            favicon_manager = get_favicon_manager()
            favicon_manager.get_favicon_pixbuf_async(url, self._on_favicon_loaded_with_cache)
        else:
            # Use color and icon paintable
            self._set_color_icon_paintable()

    def _on_favicon_loaded(self, pixbuf):
        """Handle favicon loading completion."""
        if pixbuf:
            # Create paintable with favicon only (no background color)
            paintable = ColorPaintable("transparent", favicon_pixbuf=pixbuf)
            self.password_avatar.set_custom_image(paintable)
        else:
            # Fallback to color and icon
            self._set_color_icon_paintable()

    def _on_favicon_loaded_with_cache(self, pixbuf):
        """Handle favicon loading completion and save to cache metadata."""
        if pixbuf:
            # Create paintable with favicon only (no background color)
            favicon_paintable = ColorPaintable("transparent", favicon_pixbuf=pixbuf)
            self.password_avatar.set_custom_image(favicon_paintable)

            # Save favicon as base64 data to metadata if we have a URL
            if self._url and hasattr(self, '_password_entry'):
                try:
                    favicon_data = self._pixbuf_to_base64(pixbuf)
                    if favicon_data:
                        print(f"💾 Saving favicon data to metadata for {self._password_entry} ({len(favicon_data)} chars)")
                        # Get password store and save favicon data
                        from ...password_store import PasswordStore
                        store = PasswordStore()
                        store.set_password_favicon(self._password_entry, favicon_data)
                    else:
                        print(f"❌ Failed to convert favicon to base64 for {self._password_entry}")
                except Exception as e:
                    print(f"❌ Error converting favicon to base64 for {self._password_entry}: {e}")
            else:
                print(f"❌ Cannot save favicon - missing URL or password entry for {getattr(self, '_password_entry', 'unknown')}")
        else:
            # Fallback to color and icon
            self._set_color_icon_paintable()

    def _set_color_icon_paintable(self):
        """Set avatar using color and icon paintable."""
        paintable = ColorPaintable(self._color, self._icon_name)
        self.password_avatar.set_custom_image(paintable)

    def _pixbuf_to_base64(self, pixbuf):
        """Convert a GdkPixbuf to base64 string."""
        try:
            # Save pixbuf to bytes
            success, buffer = pixbuf.save_to_bufferv("png", [], [])
            if success:
                # Encode to base64
                return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            print(f"Error converting pixbuf to base64: {e}")
        return None

    def _base64_to_pixbuf(self, base64_data):
        """Convert base64 string to GdkPixbuf."""
        try:
            # Decode base64
            image_data = base64.b64decode(base64_data)

            # Create GInputStream from bytes
            stream = Gio.MemoryInputStream.new_from_data(image_data)

            # Load pixbuf from stream
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream)
            return pixbuf
        except Exception as e:
            print(f"Error converting base64 to pixbuf: {e}")
        return None

    def set_avatar_favicon(self, favicon_path):
        """Set the avatar to use a favicon image (deprecated - use set_avatar_color_and_icon with url)."""
        try:
            from gi.repository import GdkPixbuf
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(favicon_path, 32, 32, True)
            paintable = ColorPaintable(self._color if hasattr(self, '_color') else "#9141ac", favicon_pixbuf=pixbuf)
            self.password_avatar.set_custom_image(paintable)
        except Exception as e:
            print(f"Error loading favicon {favicon_path}: {e}")
            # Fallback to color and icon
            self._set_color_icon_paintable()
    
    def _on_action_button_clicked(self, button):
        """Handle action button click - activates the row."""
        self.activate()
    
    def set_sensitive_actions(self, sensitive=True):
        """
        Set the sensitivity of action button.

        Args:
            sensitive: Whether the action button should be sensitive
        """
        self.action_button.set_sensitive(sensitive)
    
    def highlight_search_term(self, search_term):
        """
        Highlight search term in the row title and subtitle.
        
        Args:
            search_term: The term to highlight
        """
        if not search_term or not self._password_entry:
            return
        
        # Simple highlighting - in a real implementation you might want
        # to use markup for better highlighting
        title = self._password_entry.name
        if search_term.lower() in title.lower():
            # Add CSS class for highlighting
            self.add_css_class("search-highlight")
        else:
            self.remove_css_class("search-highlight")
