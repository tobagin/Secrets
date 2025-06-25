import gi
import random
import string

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject

# Use SystemRandom for cryptographically secure random generation
_secure_random = random.SystemRandom()


class PasswordGeneratorDialog(Adw.Window):
    """Dialog for generating secure passwords."""
    
    __gtype_name__ = "PasswordGeneratorDialog"
    
    # Signal emitted when a password is generated and accepted
    __gsignals__ = {
        'password-generated': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_title("Generate Password")
        self.set_default_size(500, 400)
        
        self._setup_ui()
        self._generate_password()  # Generate initial password
    
    def _setup_ui(self):
        """Setup the password generator UI."""
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(content_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Generate Password"))
        content_box.append(header_bar)
        
        # Generated password display
        password_group = Adw.PreferencesGroup()
        password_group.set_title("Generated Password")
        content_box.append(password_group)
        
        # Password display row
        self.password_row = Adw.ActionRow()
        self.password_row.set_title("Password")
        
        # Password entry (read-only)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_editable(False)
        self.password_entry.set_hexpand(True)
        
        # Copy button
        copy_button = Gtk.Button()
        copy_button.set_icon_name("edit-copy-symbolic")
        copy_button.set_tooltip_text("Copy to Clipboard")
        copy_button.connect("clicked", self._on_copy_password)
        
        # Regenerate button
        regenerate_button = Gtk.Button()
        regenerate_button.set_icon_name("view-refresh-symbolic")
        regenerate_button.set_tooltip_text("Generate New Password")
        regenerate_button.connect("clicked", lambda x: self._generate_password())
        
        # Password controls box
        password_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        password_controls.append(self.password_entry)
        password_controls.append(copy_button)
        password_controls.append(regenerate_button)
        
        self.password_row.add_suffix(password_controls)
        password_group.add(self.password_row)
        
        # Options group
        options_group = Adw.PreferencesGroup()
        options_group.set_title("Options")
        content_box.append(options_group)
        
        # Length setting
        self.length_row = Adw.SpinRow()
        self.length_row.set_title("Length")
        self.length_row.set_subtitle("Number of characters in the password")
        length_adjustment = Gtk.Adjustment(value=16, lower=4, upper=128, step_increment=1)
        self.length_row.set_adjustment(length_adjustment)
        self.length_row.connect("notify::value", lambda x, y: self._generate_password())
        options_group.add(self.length_row)
        
        # Character set options
        charset_group = Adw.PreferencesGroup()
        charset_group.set_title("Character Sets")
        content_box.append(charset_group)
        
        # Uppercase letters
        self.uppercase_row = Adw.SwitchRow()
        self.uppercase_row.set_title("Uppercase Letters")
        self.uppercase_row.set_subtitle("A-Z")
        self.uppercase_row.set_active(True)
        self.uppercase_row.connect("notify::active", lambda x, y: self._generate_password())
        charset_group.add(self.uppercase_row)
        
        # Lowercase letters
        self.lowercase_row = Adw.SwitchRow()
        self.lowercase_row.set_title("Lowercase Letters")
        self.lowercase_row.set_subtitle("a-z")
        self.lowercase_row.set_active(True)
        self.lowercase_row.connect("notify::active", lambda x, y: self._generate_password())
        charset_group.add(self.lowercase_row)
        
        # Numbers
        self.numbers_row = Adw.SwitchRow()
        self.numbers_row.set_title("Numbers")
        self.numbers_row.set_subtitle("0-9")
        self.numbers_row.set_active(True)
        self.numbers_row.connect("notify::active", lambda x, y: self._generate_password())
        charset_group.add(self.numbers_row)
        
        # Symbols
        self.symbols_row = Adw.SwitchRow()
        self.symbols_row.set_title("Symbols")
        self.symbols_row.set_subtitle("!@#$%^&*()_+-=[]{}|;:,.<>?")
        self.symbols_row.set_active(True)
        self.symbols_row.connect("notify::active", lambda x, y: self._generate_password())
        charset_group.add(self.symbols_row)
        
        # Exclude ambiguous characters
        self.exclude_ambiguous_row = Adw.SwitchRow()
        self.exclude_ambiguous_row.set_title("Exclude Ambiguous Characters")
        self.exclude_ambiguous_row.set_subtitle("Exclude 0, O, l, 1, I")
        self.exclude_ambiguous_row.set_active(False)
        self.exclude_ambiguous_row.connect("notify::active", lambda x, y: self._generate_password())
        charset_group.add(self.exclude_ambiguous_row)
        
        # Password strength indicator
        strength_group = Adw.PreferencesGroup()
        strength_group.set_title("Strength")
        content_box.append(strength_group)
        
        self.strength_row = Adw.ActionRow()
        self.strength_row.set_title("Password Strength")
        
        self.strength_label = Gtk.Label()
        self.strength_row.add_suffix(self.strength_label)

        strength_group.add(self.strength_row)

        # Bottom HeaderBar with action button
        bottom_header_bar = Adw.HeaderBar()
        bottom_header_bar.set_show_end_title_buttons(False)

        self.use_button = Gtk.Button(label="Use Password")
        self.use_button.add_css_class("suggested-action")
        self.use_button.connect("clicked", self._on_use_password)
        bottom_header_bar.set_title_widget(self.use_button)

        content_box.append(bottom_header_bar)
    
    def _generate_password(self):
        """Generate a new password based on current settings."""
        length = int(self.length_row.get_value())
        
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
        clipboard = self.get_clipboard()
        clipboard.set(password)
        
        # Show toast notification (if parent has toast overlay)
        if hasattr(self.get_transient_for(), 'toast_overlay'):
            toast = Adw.Toast.new("Password copied to clipboard")
            self.get_transient_for().toast_overlay.add_toast(toast)
    
    def _on_use_password(self, button):
        """Emit signal with generated password and close dialog."""
        password = self.password_entry.get_text()
        self.emit('password-generated', password)
        self.close()
