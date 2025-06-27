import gi
import random
import string

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject

from secrets.app_info import APP_ID

# Use SystemRandom for cryptographically secure random generation
_secure_random = random.SystemRandom()


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/password_generator_dialog.ui')
class PasswordGeneratorDialog(Adw.Window):
    """Dialog for generating secure passwords."""

    __gtype_name__ = "PasswordGeneratorDialog"

    # Template widgets
    password_entry = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()
    regenerate_button = Gtk.Template.Child()
    length_row = Gtk.Template.Child()
    uppercase_row = Gtk.Template.Child()
    lowercase_row = Gtk.Template.Child()
    numbers_row = Gtk.Template.Child()
    symbols_row = Gtk.Template.Child()
    exclude_ambiguous_row = Gtk.Template.Child()
    strength_label = Gtk.Template.Child()
    use_button = Gtk.Template.Child()

    # Signal emitted when a password is generated and accepted
    __gsignals__ = {
        'password-generated': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }

    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)

        self.set_transient_for(parent_window)
        self.set_modal(True)

        self._setup_signals()
        self._generate_password()  # Generate initial password
    
    def _setup_signals(self):
        """Setup signal connections for UI elements."""
        # Connect signals
        self.copy_button.connect("clicked", self._on_copy_password)
        self.regenerate_button.connect("clicked", lambda x: self._generate_password())
        self.length_row.connect("notify::value", lambda x, y: self._generate_password())
        self.uppercase_row.connect("notify::active", lambda x, y: self._generate_password())
        self.lowercase_row.connect("notify::active", lambda x, y: self._generate_password())
        self.numbers_row.connect("notify::active", lambda x, y: self._generate_password())
        self.symbols_row.connect("notify::active", lambda x, y: self._generate_password())
        self.exclude_ambiguous_row.connect("notify::active", lambda x, y: self._generate_password())
        self.use_button.connect("clicked", self._on_use_password)
    
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
        score = self._calculate_strength(password)
        
        if score < 30:
            strength_text = "Weak"
            css_class = "error"
        elif score < 60:
            strength_text = "Fair"
            css_class = "warning"
        elif score < 80:
            strength_text = "Good"
            css_class = "accent"
        else:
            strength_text = "Strong"
            css_class = "success"
        
        self.strength_label.set_text(strength_text)
        
        # Remove old CSS classes and add new one
        # CSS styling will be handled in UI files
    
    def _calculate_strength(self, password):
        """Calculate password strength score (0-100)."""
        score = 0
        
        # Length bonus
        score += min(len(password) * 2, 25)
        
        # Character variety bonus
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        variety_count = sum([has_lower, has_upper, has_digit, has_symbol])
        score += variety_count * 15
        
        # Entropy bonus (simplified)
        unique_chars = len(set(password))
        score += min(unique_chars * 2, 20)
        
        return min(score, 100)
    
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
                clipboard.set_text(password)

                # Show toast notification if possible
                parent = self.get_transient_for()
                while parent and not hasattr(parent, 'toast_overlay'):
                    parent = parent.get_parent()

                if parent and hasattr(parent, 'toast_overlay'):
                    toast = Adw.Toast.new("Password copied to clipboard")
                    parent.toast_overlay.add_toast(toast)
        except Exception as e:
            print(f"Error copying password to clipboard: {e}")
            # Try to show error toast if possible
            parent = self.get_transient_for()
            while parent and not hasattr(parent, 'toast_overlay'):
                parent = parent.get_parent()

            if parent and hasattr(parent, 'toast_overlay'):
                toast = Adw.Toast.new("Failed to copy password")
                parent.toast_overlay.add_toast(toast)
    
    def _on_use_password(self, button):
        """Emit signal with generated password and close dialog."""
        password = self.password_entry.get_text()
        self.emit('password-generated', password)
        self.close()
