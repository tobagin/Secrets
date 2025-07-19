"""
Password Generator Widget for embedding in dialogs.

This widget provides password generation functionality that can be embedded
in other dialogs, with a "Use Password" button instead of the standalone
dialog's "Regenerate" button.
"""

import gi
import random
import string

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...utils.password_strength import PasswordStrengthCalculator

# Use SystemRandom for cryptographically secure random generation
_secure_random = random.SystemRandom()


@Gtk.Template(resource_path="/io/github/tobagin/secrets/ui/components/password_generator_widget.ui")
class PasswordGeneratorWidget(Gtk.Box):
    """Widget for generating secure passwords with strength indication."""

    __gtype_name__ = "PasswordGeneratorWidget"

    # Template widgets
    password_entry = Gtk.Template.Child()
    regenerate_button = Gtk.Template.Child()
    strength_row = Gtk.Template.Child()
    strength_label = Gtk.Template.Child()
    length_row = Gtk.Template.Child()
    uppercase_row = Gtk.Template.Child()
    lowercase_row = Gtk.Template.Child()
    numbers_row = Gtk.Template.Child()
    symbols_row = Gtk.Template.Child()
    exclude_ambiguous_row = Gtk.Template.Child()
    use_password_button = Gtk.Template.Child()

    # Signal emitted when user wants to use the generated password
    __gsignals__ = {
        'password-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_signals()
        self._generate_password()  # Generate initial password
    
    def _setup_signals(self):
        """Setup signal connections for UI elements."""
        # Connect signals
        self.regenerate_button.connect("clicked", lambda x: self._generate_password())
        self.use_password_button.connect("clicked", self._on_use_password)
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
            self.emit('password-selected', password)
    
    def get_current_password(self):
        """Get the currently generated password."""
        return self.password_entry.get_text()
    
    def set_password(self, password):
        """Set a password and update strength indicator."""
        self.password_entry.set_text(password)
        self._update_strength_indicator(password)