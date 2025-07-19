import gi
import random
import string

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject

from secrets.app_info import APP_ID
from ...utils.password_strength import PasswordStrengthCalculator

# Use SystemRandom for cryptographically secure random generation
_secure_random = random.SystemRandom()


@Gtk.Template(resource_path="/io/github/tobagin/secrets/ui/dialogs/password_generator_dialog.ui")
class PasswordGeneratorDialog(Adw.Window):
    """Dialog for generating secure passwords."""

    __gtype_name__ = "PasswordGeneratorDialog"

    # Template widgets
    password_entry = Gtk.Template.Child()
    password_copy_button = Gtk.Template.Child()
    regenerate_button = Gtk.Template.Child()
    length_row = Gtk.Template.Child()
    uppercase_row = Gtk.Template.Child()
    lowercase_row = Gtk.Template.Child()
    numbers_row = Gtk.Template.Child()
    symbols_row = Gtk.Template.Child()
    exclude_ambiguous_row = Gtk.Template.Child()
    strength_label = Gtk.Template.Child()

    # Signal emitted when a password is generated and accepted
    __gsignals__ = {
        'password-generated': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }

    def __init__(self, transient_for=None, from_dialog=False, **kwargs):
        super().__init__(modal=True, transient_for=transient_for, **kwargs)
        
        self.from_dialog = from_dialog
        self._setup_ui_for_context()
        self._setup_signals()
        self._generate_password()  # Generate initial password
    
    def _setup_ui_for_context(self):
        """Setup UI based on how dialog was opened."""
        if self.from_dialog:
            # When opened from add/edit dialog: Use button replaces Regenerate, Copy becomes Regenerate (icon only)
            self.regenerate_button.set_label("Use Password")
            self.password_copy_button.set_label("")  # Icon only
            self.password_copy_button.set_icon_name("view-refresh-symbolic")
            self.password_copy_button.set_tooltip_text("Regenerate Password")
        # When opened from menu: keep default layout (Copy + Regenerate)
    
    def _setup_signals(self):
        """Setup signal connections for UI elements."""
        # Connect signals based on context
        if self.from_dialog:
            # When from dialog: copy button becomes regenerate, regenerate button becomes use
            self.password_copy_button.connect("clicked", lambda x: self._generate_password())
            self.regenerate_button.connect("clicked", self._on_use_password)
        else:
            # When from menu: normal behavior
            self.password_copy_button.connect("clicked", self._on_copy_password)
            self.regenerate_button.connect("clicked", lambda x: self._generate_password())
        self.length_row.connect("notify::value", lambda x, y: self._generate_password())
        self.uppercase_row.connect("notify::active", lambda x, y: self._generate_password())
        self.lowercase_row.connect("notify::active", lambda x, y: self._generate_password())
        self.numbers_row.connect("notify::active", lambda x, y: self._generate_password())
        self.symbols_row.connect("notify::active", lambda x, y: self._generate_password())
        self.exclude_ambiguous_row.connect("notify::active", lambda x, y: self._generate_password())
    
    def _generate_password(self):
        """Generate a new password based on current settings."""
        length = int(self.length_row.get_value())

        # Ensure minimum length (fallback if adjustment isn't working)
        if length < 4:
            length = 16
            self.length_row.set_value(16)

        # Build character set
        charset = ""

        if self.uppercase_row.get_active():
            charset += string.ascii_uppercase

        if self.lowercase_row.get_active():
            charset += string.ascii_lowercase

        if self.numbers_row.get_active():
            charset += string.digits

        if self.symbols_row.get_active():
            charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Exclude ambiguous characters if requested
        if self.exclude_ambiguous_row.get_active():
            ambiguous = "0Ol1I"
            charset = "".join(c for c in charset if c not in ambiguous)

        # Ensure we have at least some characters
        if not charset:
            charset = string.ascii_letters + string.digits

        # Generate password using cryptographically secure random
        password = "".join(_secure_random.choice(charset) for _ in range(length))

        self.password_entry.set_text(password)
        self._update_strength_indicator(password)
    
    def _update_strength_indicator(self, password):
        """Update the password strength indicator."""
        exclude_ambiguous = self.exclude_ambiguous_row.get_active()
        score, strength_text = PasswordStrengthCalculator.calculate_strength(
            password, exclude_ambiguous
        )
        
        self.strength_label.set_text(strength_text)
        
        # Update CSS classes based on strength (0-4 scale)
        self.strength_label.remove_css_class("error")
        self.strength_label.remove_css_class("warning") 
        self.strength_label.remove_css_class("accent")
        self.strength_label.remove_css_class("success")
        
        if score <= 0:  # Very Weak
            css_class = "error"
        elif score == 1:  # Weak
            css_class = "error"
        elif score == 2:  # Fair
            css_class = "warning"
        elif score == 3:  # Good
            css_class = "accent"
        else:  # Strong (4)
            css_class = "success"
            
        self.strength_label.add_css_class(css_class)
    
    def _on_use_password(self, button):
        """Handle use password button click."""
        password = self.password_entry.get_text()
        if password:
            self.emit('password-generated', password)
    
    def _on_copy_password(self, button):
        """Copy password to clipboard."""
        password = self.password_entry.get_text()
        if not password:
            return

        try:
            # Get the display and clipboard properly
            display = self.get_display()
            if display:
                clipboard = display.get_clipboard()
                clipboard.set(password)

                # Show toast notification if possible
                parent = self.get_transient_for()
                while parent and not hasattr(parent, 'toast_overlay'):
                    parent = parent.get_parent()

                if parent and hasattr(parent, 'toast_overlay'):
                    toast = Adw.Toast.new("Password copied to clipboard")
                    parent.toast_overlay.add_toast(toast)
        except Exception as e:
            # Try to show error toast if possible
            parent = self.get_transient_for()
            while parent and not hasattr(parent, 'toast_overlay'):
                parent = parent.get_parent()

            if parent and hasattr(parent, 'toast_overlay'):
                toast = Adw.Toast.new("Failed to copy password")
                parent.toast_overlay.add_toast(toast)
