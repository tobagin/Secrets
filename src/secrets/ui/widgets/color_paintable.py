import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gsk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, Gsk, Adw, GObject, Graphene, GdkPixbuf
import math


class ColorPaintable(GObject.Object, Gdk.Paintable):
    """A custom paintable that renders a solid color with optional icon or favicon for AdwAvatar."""

    __gtype_name__ = "ColorPaintable"

    def __init__(self, color="#9141ac", icon_name=None, favicon_pixbuf=None):
        super().__init__()
        self._color = color
        self._rgba = Gdk.RGBA()
        self._rgba.parse(color)
        self._icon_name = icon_name
        self._favicon_pixbuf = favicon_pixbuf
        self._icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

    def set_color(self, color):
        """Set the color and invalidate the paintable."""
        self._color = color
        if color.lower() == "transparent":
            self._rgba.red = 0.0
            self._rgba.green = 0.0
            self._rgba.blue = 0.0
            self._rgba.alpha = 0.0
        else:
            self._rgba.parse(color)
        self.invalidate_contents()

    def get_color(self):
        """Get the current color."""
        return self._color

    def set_icon(self, icon_name):
        """Set the icon name and invalidate the paintable."""
        self._icon_name = icon_name
        self._favicon_pixbuf = None  # Clear favicon when setting icon
        self.invalidate_contents()

    def get_icon(self):
        """Get the current icon name."""
        return self._icon_name

    def set_favicon(self, pixbuf):
        """Set the favicon pixbuf and invalidate the paintable."""
        self._favicon_pixbuf = pixbuf
        self._icon_name = None  # Clear icon when setting favicon
        self.invalidate_contents()

    def get_favicon(self):
        """Get the current favicon pixbuf."""
        return self._favicon_pixbuf
        
    def do_snapshot(self, snapshot, width, height):
        """Render the color background with optional icon or favicon."""
        # If favicon is available, render only the favicon (no background)
        if self._favicon_pixbuf:
            self._render_favicon_only(snapshot, width, height)
        else:
            # Render background color and icon
            rect = Graphene.Rect()
            rect.init(0, 0, width, height)

            # Append background color (skip if transparent)
            if self._color.lower() != "transparent":
                snapshot.append_color(self._rgba, rect)

            # Render icon if available
            if self._icon_name:
                self._render_icon(snapshot, width, height)

    def _render_favicon_only(self, snapshot, width, height):
        """Render the favicon pixbuf with automatic background for dark icons."""
        if not self._favicon_pixbuf:
            return

        # Check if favicon is dark and needs a white background
        needs_white_background = self._favicon_needs_white_background()

        # If dark favicon detected, render white background
        if needs_white_background:
            rect = Graphene.Rect()
            rect.init(0, 0, width, height)
            white_rgba = Gdk.RGBA()
            white_rgba.red = 1.0
            white_rgba.green = 1.0
            white_rgba.blue = 1.0
            white_rgba.alpha = 1.0
            snapshot.append_color(white_rgba, rect)

        # Get original favicon dimensions
        favicon_width = self._favicon_pixbuf.get_width()
        favicon_height = self._favicon_pixbuf.get_height()

        # Calculate scaling to fit within avatar while maintaining aspect ratio
        scale_x = width / favicon_width
        scale_y = height / favicon_height
        scale = min(scale_x, scale_y)

        # Calculate final size and position
        final_width = favicon_width * scale
        final_height = favicon_height * scale
        x = (width - final_width) / 2
        y = (height - final_height) / 2

        # Create a texture from the pixbuf
        texture = Gdk.Texture.new_for_pixbuf(self._favicon_pixbuf)

        # Create a rectangle for the favicon
        rect = Graphene.Rect()
        rect.init(x, y, final_width, final_height)

        # Render the favicon texture
        snapshot.append_texture(texture, rect)

    def _favicon_needs_white_background(self):
        """Check if favicon is dark and needs a white background for visibility."""
        if not self._favicon_pixbuf:
            return False

        # Get pixbuf properties
        width = self._favicon_pixbuf.get_width()
        height = self._favicon_pixbuf.get_height()
        n_channels = self._favicon_pixbuf.get_n_channels()
        has_alpha = self._favicon_pixbuf.get_has_alpha()
        
        # Get pixel data
        pixels = self._favicon_pixbuf.get_pixels()
        
        # Sample pixels for analysis (sample every 4th pixel for performance)
        sample_size = min(100, width * height // 16)  # Sample up to 100 pixels
        step = max(1, (width * height) // sample_size)
        
        total_luminance = 0
        transparent_pixels = 0
        sampled_pixels = 0
        
        for y in range(0, height, max(1, step // width)):
            for x in range(0, width, max(1, step % width) or 1):
                if sampled_pixels >= sample_size:
                    break
                
                # Calculate pixel offset
                offset = (y * width + x) * n_channels
                
                if offset + 2 >= len(pixels):
                    continue
                
                # Get RGB values
                r = pixels[offset] / 255.0
                g = pixels[offset + 1] / 255.0
                b = pixels[offset + 2] / 255.0
                
                # Check alpha if present
                if has_alpha and n_channels >= 4:
                    alpha = pixels[offset + 3] / 255.0
                    if alpha < 0.1:  # Nearly transparent
                        transparent_pixels += 1
                        sampled_pixels += 1
                        continue
                
                # Calculate luminance using standard formula
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                total_luminance += luminance
                sampled_pixels += 1
                
            if sampled_pixels >= sample_size:
                break
        
        if sampled_pixels == 0:
            return False  # No valid pixels to analyze
        
        # Calculate average luminance of non-transparent pixels
        opaque_pixels = sampled_pixels - transparent_pixels
        if opaque_pixels == 0:
            return False  # All pixels are transparent
        
        avg_luminance = total_luminance / opaque_pixels
        
        # If more than 70% of pixels are transparent, it's likely a simple icon that needs background
        transparency_ratio = transparent_pixels / sampled_pixels
        if transparency_ratio > 0.7:
            return True
        
        # If average luminance is below 0.4, consider it dark and needing white background
        # This threshold works well for GitHub and other dark icons
        return avg_luminance < 0.4

    def _render_favicon(self, snapshot, width, height):
        """Render the favicon pixbuf centered on the background (legacy method)."""
        if not self._favicon_pixbuf:
            return

        # Calculate size and position to center the favicon
        # Use minimum 16px for crisp rendering, 25% smaller than before
        favicon_size = max(16, min(width, height) * 0.375)  # 37.5% of avatar size
        pixbuf_width = self._favicon_pixbuf.get_width()
        pixbuf_height = self._favicon_pixbuf.get_height()

        # Scale the pixbuf to fit
        if pixbuf_width > favicon_size or pixbuf_height > favicon_size:
            scale = min(favicon_size / pixbuf_width, favicon_size / pixbuf_height)
            new_width = int(pixbuf_width * scale)
            new_height = int(pixbuf_height * scale)
            scaled_pixbuf = self._favicon_pixbuf.scale_simple(
                new_width, new_height, GdkPixbuf.InterpType.BILINEAR
            )
        else:
            scaled_pixbuf = self._favicon_pixbuf
            new_width = pixbuf_width
            new_height = pixbuf_height

        # Center the favicon
        x = (width - new_width) / 2
        y = (height - new_height) / 2

        # Create texture from pixbuf and render
        texture = Gdk.Texture.new_for_pixbuf(scaled_pixbuf)
        favicon_rect = Graphene.Rect()
        favicon_rect.init(x, y, new_width, new_height)
        snapshot.append_texture(texture, favicon_rect)

    def _render_icon(self, snapshot, width, height):
        """Render the icon centered on the background with appropriate color."""
        if not self._icon_name:
            return

        # Calculate icon size (37.5% of avatar size - 25% smaller than before)
        # Use minimum 16px for crisp rendering, but scale down for display
        base_size = int(min(width, height) * 0.375)
        icon_size = max(16, base_size)

        # Get icon color based on background luminance
        icon_color = self._get_icon_color()

        try:
            # Load the icon
            icon_info = self._icon_theme.lookup_icon(
                self._icon_name,
                None,  # fallbacks
                icon_size,
                1,  # scale
                Gtk.TextDirection.NONE,
                Gtk.IconLookupFlags.FORCE_SYMBOLIC
            )

            if icon_info:
                # Center the icon
                x = (width - icon_size) / 2
                y = (height - icon_size) / 2

                # Save the current state
                snapshot.save()

                # Translate to center position
                snapshot.translate(Graphene.Point().init(x, y))

                # Render the symbolic icon with the calculated color
                icon_info.snapshot_symbolic(snapshot, icon_size, icon_size, [icon_color])

                # Restore the state
                snapshot.restore()

        except Exception as e:
            # Fallback: render a simple circle when icon loading fails
            self._render_fallback_icon(snapshot, width, height)

    def _render_fallback_icon(self, snapshot, width, height):
        """Render a simple fallback icon when the main icon fails."""
        icon_size = int(min(width, height) * 0.4)
        x = (width - icon_size) / 2
        y = (height - icon_size) / 2

        # Draw a simple circle as fallback
        icon_color = self._get_icon_color()
        rect = Graphene.Rect()
        rect.init(x, y, icon_size, icon_size)
        snapshot.append_color(icon_color, rect)

    def _get_icon_color(self):
        """Get appropriate icon color based on background luminance and theme."""
        icon_rgba = Gdk.RGBA()

        # For transparent backgrounds, adapt to current theme
        if self._color.lower() == "transparent" or self._rgba.alpha < 0.1:
            # Check if we're in dark mode by looking at the default style context
            style_manager = Adw.StyleManager.get_default()
            is_dark = style_manager.get_dark()

            if is_dark:
                # Dark theme - use light icon
                icon_rgba.red = 0.9
                icon_rgba.green = 0.9
                icon_rgba.blue = 0.9
                icon_rgba.alpha = 1.0
            else:
                # Light theme - use dark icon
                icon_rgba.red = 0.18  # #2e3436 in RGB
                icon_rgba.green = 0.20
                icon_rgba.blue = 0.21
                icon_rgba.alpha = 1.0
            return icon_rgba

        # Calculate luminance of background color using proper formula
        luminance = (0.2126 * self._rgba.red + 0.7152 * self._rgba.green + 0.0722 * self._rgba.blue)

        # Use white icon on dark backgrounds, dark icon on light backgrounds
        if luminance < 0.5:
            # Dark background - use white icon
            icon_rgba.red = 1.0
            icon_rgba.green = 1.0
            icon_rgba.blue = 1.0
            icon_rgba.alpha = 1.0
        else:
            # Light background - use dark icon
            icon_rgba.red = 0.18  # #2e3436 in RGB
            icon_rgba.green = 0.20
            icon_rgba.blue = 0.21
            icon_rgba.alpha = 1.0

        return icon_rgba
        
    def do_get_intrinsic_width(self):
        """Return the intrinsic width (32px - standard avatar size)."""
        return 32

    def do_get_intrinsic_height(self):
        """Return the intrinsic height (32px - standard avatar size)."""
        return 32
        
    def do_get_intrinsic_aspect_ratio(self):
        """Return the aspect ratio (1:1 for square)."""
        return 1.0


# Register the type
GObject.type_register(ColorPaintable)
