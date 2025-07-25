"""Password entry row widget for the new single-window design."""

import gi
import os
import base64
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, GdkPixbuf, Gio
from .color_paintable import ColorPaintable
from ...managers.favicon_manager import get_favicon_manager
from ...app_info import APP_ID


@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/widgets/password_entry_row.ui')
class PasswordEntryRow(Adw.ActionRow):
    """A simple password entry row with basic action functionality."""
    
    __gtype_name__ = 'PasswordEntryRow'
    
    # UI elements
    password_avatar = Gtk.Template.Child()
    action_buttons = Gtk.Template.Child()
    copy_username_button = Gtk.Template.Child()
    copy_password_button = Gtk.Template.Child()
    copy_totp_button = Gtk.Template.Child()
    visit_url_button = Gtk.Template.Child()
    edit_password_button = Gtk.Template.Child()
    view_details_button = Gtk.Template.Child()
    remove_password_button = Gtk.Template.Child()
    
    # Signals for action buttons
    __gsignals__ = {
        'copy-username': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'copy-password': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'copy-totp': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'visit-url': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'edit-password': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'view-details': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'remove-password': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, password_entry=None, **kwargs):
        """Initialize the password row."""
        super().__init__(**kwargs)
        self._password_entry = password_entry
        self._toast_manager = None
        self._clipboard_manager = None
        self._lazy_url_loader = None
        self._lazy_url_loader_args = None
        self._url_loaded = False
        self._content_checked = False
        self._setup_signals()
        
        if password_entry:
            self.set_password_entry(password_entry)
            self._update_button_visibility()
    
    def _setup_signals(self):
        """Set up button signal connections."""
        self.copy_username_button.connect('clicked', self._on_copy_username_clicked)
        self.copy_password_button.connect('clicked', self._on_copy_password_clicked)
        self.copy_totp_button.connect('clicked', self._on_copy_totp_clicked)
        self.visit_url_button.connect('clicked', self._on_visit_url_clicked)
        self.edit_password_button.connect('clicked', self._on_edit_password_clicked)
        self.view_details_button.connect('clicked', self._on_view_details_clicked)
        self.remove_password_button.connect('clicked', self._on_remove_password_clicked)
        self.connect("activate", self._on_row_activated)
    
    def set_password_entry(self, password_entry):
        """Set the password entry data for this row."""
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
                # Continue to try downloading if cached data fails
                pass

        # If URL is provided and no cached favicon, try to download
        if url and url.strip():
            favicon_manager = get_favicon_manager()
            favicon_manager.get_favicon_pixbuf_async(url, self._on_favicon_loaded_with_cache)
        else:
            # Use color and icon paintable
            self._set_color_icon_paintable()
    
    def set_lazy_url_loader(self, loader_func, *args):
        """Set a lazy URL loader function that will be called when the URL is needed."""
        self._lazy_url_loader = loader_func
        self._lazy_url_loader_args = args
        self._url_loaded = False
    
    def _load_url_if_needed(self):
        """Load URL lazily if not already loaded."""
        if not self._url_loaded and self._lazy_url_loader:
            try:
                url = self._lazy_url_loader(*self._lazy_url_loader_args)
                if url:
                    self._url = url
                    # Try to load favicon with the new URL
                    favicon_manager = get_favicon_manager()
                    favicon_manager.get_favicon_pixbuf_async(url, self._on_favicon_loaded_with_cache)
                self._url_loaded = True
            except Exception as e:
                # Silently handle URL loading errors
                self._url_loaded = True
    
    def _check_content_if_needed(self):
        """Check password content lazily for TOTP and URL button visibility."""
        if self._content_checked or not self._password_entry:
            return
        
        # Get password path for content checking
        password_path = self._password_entry.path if hasattr(self._password_entry, 'path') else str(self._password_entry)
        
        def check_content_background():
            try:
                # Import password store to check content
                from ...password_store import PasswordStore
                store = PasswordStore()
                success, content = store.get_password_content(password_path)
                
                if success:
                    lines = content.split('\n')
                    has_totp = False
                    has_url = False
                    
                    for line in lines:
                        line = line.strip().lower()
                        if line.startswith('totp:') or line.startswith('otp:'):
                            has_totp = True
                        if (line.startswith('url:') or line.startswith('website:') or 
                            line.startswith('http://') or line.startswith('https://')):
                            has_url = True
                    
                    # Update UI on main thread
                    from gi.repository import GLib
                    GLib.idle_add(self._update_advanced_buttons, has_totp, has_url)
                    
            except Exception as e:
                # Silently handle content loading errors
                pass
        
        # Load content in background thread
        import threading
        threading.Thread(target=check_content_background, daemon=True).start()
        self._content_checked = True
    
    def _update_advanced_buttons(self, has_totp, has_url):
        """Update advanced button visibility based on content analysis."""
        self.copy_totp_button.set_visible(has_totp)
        self.visit_url_button.set_visible(has_url)
        return False  # Don't repeat this idle call

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
                        # Get password store and save favicon data
                        from ...password_store import PasswordStore
                        store = PasswordStore()
                        store.set_password_favicon(self._password_entry, favicon_data)
                except Exception as e:
                    # Silently handle favicon conversion errors
                    pass
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
            # Silently handle pixbuf conversion errors
            pass
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
            # Silently handle base64 conversion errors
            pass
        return None
    
    def _on_copy_username_clicked(self, button):
        """Handle copy username button click."""
        self.emit("copy-username")
        
    def _on_copy_password_clicked(self, button):
        """Handle copy password button click."""
        self.emit("copy-password")
        
    def _on_copy_totp_clicked(self, button):
        """Handle copy TOTP button click."""
        # Ensure content is checked before copying TOTP
        self._check_content_if_needed()
        self.emit("copy-totp")
        
    def _on_visit_url_clicked(self, button):
        """Handle visit URL button click."""
        # Load URL lazily if needed
        self._load_url_if_needed()
        
        if self._url:
            self.emit("visit-url", self._url)
        elif self._password_entry:
            # Try to get URL from password entry if available
            if hasattr(self._password_entry, 'url') and self._password_entry.url:
                self.emit("visit-url", self._password_entry.url)
        
    def _on_edit_password_clicked(self, button):
        """Handle edit password button click."""
        if self._password_entry:
            path = self._password_entry.path if hasattr(self._password_entry, 'path') else str(self._password_entry)
            self.emit("edit-password", path)
        
    def _on_view_details_clicked(self, button):
        """Handle view details button click."""
        if self._password_entry:
            path = self._password_entry.path if hasattr(self._password_entry, 'path') else str(self._password_entry)
            self.emit("view-details", path)
        
    def _on_remove_password_clicked(self, button):
        """Handle remove password button click."""
        if self._password_entry:
            path = self._password_entry.path if hasattr(self._password_entry, 'path') else str(self._password_entry)
            self.emit("remove-password", path)
        
    def _on_row_activated(self, row):
        """Handle row activation - ActionRow already emits 'activated' signal."""
        # Check content if user specifically clicks on this row (indicates interest)
        if self.get_visible() and not self._content_checked:
            self._check_content_if_needed()
        # The ActionRow will automatically emit the 'activated' signal
    
    def set_sensitive_actions(self, sensitive=True):
        """Set the sensitivity of action buttons."""
        self.copy_username_button.set_sensitive(sensitive)
        self.copy_password_button.set_sensitive(sensitive)
        self.copy_totp_button.set_sensitive(sensitive)
        self.visit_url_button.set_sensitive(sensitive)
        self.edit_password_button.set_sensitive(sensitive)
        self.view_details_button.set_sensitive(sensitive)
        self.remove_password_button.set_sensitive(sensitive)
    
    def set_toast_manager(self, toast_manager):
        """Set the toast manager for showing notifications."""
        self._toast_manager = toast_manager
    
    def set_clipboard_manager(self, clipboard_manager):
        """Set the clipboard manager for copying content."""
        self._clipboard_manager = clipboard_manager
    
    def _update_button_visibility(self):
        """Update button visibility based on available data (lazy loading)."""
        if not self._password_entry:
            return
        
        # Start with conservative defaults - show basic buttons, hide advanced ones
        self.copy_username_button.set_visible(True)
        self.copy_password_button.set_visible(True)
        self.copy_totp_button.set_visible(False)  # Hidden until we check content
        self.visit_url_button.set_visible(False)  # Hidden until we check content
        self.edit_password_button.set_visible(True)
        self.view_details_button.set_visible(True)
        self.remove_password_button.set_visible(True)
        
        # Mark that we need to check content lazily
        self._content_checked = False
        
        # Content will be processed in bulk by the controller to avoid multiple passphrase prompts
        # Individual password rows no longer need to check content automatically
    
    def check_visibility_and_load_content(self):
        """Check if row is visible and load content if needed. Called when row becomes visible."""
        # This can be called by the parent controller when the row becomes visible
        if self.get_visible():
            if not self._content_checked:
                self._check_content_if_needed()
            # Also load favicon when row becomes visible (viewport-based loading)
            if not self._url_loaded and self._lazy_url_loader:
                # Add a small delay to avoid overwhelming the graphics system
                GLib.timeout_add(100, self._trigger_favicon_loading)
    
    def _trigger_lazy_content_check(self):
        """Trigger lazy content checking after a short delay to avoid blocking startup."""
        if not self._content_checked:
            self._check_content_if_needed()
        return False  # Don't repeat the timeout=
    
    def _should_load_favicon_eagerly(self):
        """Determine if this password should load its favicon eagerly to avoid memory issues."""
        if not self._password_entry or not hasattr(self._password_entry, 'path'):
            return False
        
        path_lower = str(self._password_entry.path).lower()
        
        # Load favicons eagerly for commonly used services
        priority_domains = ['google', 'microsoft', 'amazon', 'github', 'facebook', 'twitter', 
                           'apple', 'dropbox', 'netflix', 'youtube', 'gmail', 'outlook',
                           'paypal', 'linkedin', 'instagram', 'reddit', 'discord', 'slack']
        
        # Only load favicon eagerly if it's a well-known service or has cached favicon data
        return any(domain in path_lower for domain in priority_domains)
    
    def _trigger_favicon_loading(self):
        """Trigger favicon loading for better visual experience."""
        if not self._url_loaded and self._lazy_url_loader:
            self._load_url_if_needed()
        return False  # Don't repeat the timeout
    
    def set_bulk_processing_results(self, has_totp, has_url):
        """Set the results from bulk content processing."""
        self._update_advanced_buttons(has_totp, has_url)
        self._content_checked = True  # Mark as processed=
