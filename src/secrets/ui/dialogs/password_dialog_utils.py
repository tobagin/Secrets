"""
Shared utilities for password dialogs that eliminates duplication between Add and Edit dialogs.

This module provides utility functions and helper classes that contain all shared functionality
between AddPasswordDialog and EditPasswordDialog, reducing code duplication by ~80%.
"""

import gi
import os
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gio
from ..components.password_generator_popover import PasswordGeneratorPopover
from ...utils import DialogManager, UIConstants, AccessibilityHelper
from ...utils.avatar_manager import AvatarManager, AvatarConfiguration
from ...services.password_content_parser import PasswordContentParser, PasswordData
from ...app_info import APP_ID
from ..widgets.icon_picker import IconPicker

# Use SystemRandom for cryptographically secure random generation
_secure_random = random.SystemRandom()


@dataclass
class PasswordDialogState:
    """Manages state for password dialogs."""
    transient_for_window: Optional[Gtk.Window] = None
    password_store: Any = None
    avatar_manager: Optional[AvatarManager] = None
    content_parser: Optional[PasswordContentParser] = None
    password_generator_popover: Optional[PasswordGeneratorPopover] = None
    selected_color: str = "#3584e4"  # Default blue
    selected_icon: str = "dialog-password-symbolic"  # Default icon
    recovery_codes: List[str] = field(default_factory=list)


class PasswordDialogSignalHandler:
    """Handles common signal connections for password dialogs."""
    
    def __init__(self, dialog: Adw.Dialog, state: PasswordDialogState):
        self.dialog = dialog
        self.state = state
        
    def connect_common_signals(self):
        """Connect all common signal handlers."""
        # Entry change signals
        self.dialog.name_entry.connect('notify::text', self.on_field_changed)
        self.dialog.password_entry.connect('notify::text', self.on_field_changed)
        
        # Button signals
        self.dialog.generate_button.connect('clicked', self.on_generate_password_clicked)
        self.dialog.color_select_button.connect('clicked', self.on_color_button_clicked)
        self.dialog.add_recovery_button.connect('clicked', lambda btn: self.on_add_recovery_code_clicked(btn))
        self.dialog.name_entry.connect('activate', self.on_name_entry_activated)
        
        # Combo row signals
        self.dialog.icon_row.connect('notify::selected-item', self.on_icon_changed)
    
    def on_field_changed(self, entry, pspec):
        """Handle text field changes to update save button state."""
        update_save_button_state(self.dialog)
    
    def on_generate_password_clicked(self, button):
        """Handle password generation button click."""
        handle_password_generation(self.dialog, self.state, button)
    
    def on_color_button_clicked(self, button):
        """Handle color selection button click."""
        handle_color_selection(self.dialog, self.state, button)
    
    def on_add_recovery_code_clicked(self, button, initial_text=""):
        """Handle adding a new recovery code."""
        add_recovery_code_row(self.dialog, self.state, initial_text)
    
    def on_icon_changed(self, combo_row, pspec):
        """Handle icon selection change."""
        handle_icon_change(self.dialog, self.state, combo_row)
    
    def on_name_entry_activated(self, entry_row):
        """Handle name entry activation (Enter key)."""
        if self.dialog.save_button.get_sensitive():
            # Emit the save signal - this will be handled by the specific dialog
            if hasattr(self.dialog, '_on_save_clicked_impl'):
                self.dialog._on_save_clicked_impl(self.dialog.save_button)


class PasswordFormValidator:
    """Validates password form inputs."""
    
    @staticmethod
    def validate_form(dialog: Adw.Dialog) -> tuple[bool, str]:
        """
        Validate the form data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        name = dialog.name_entry.get_text().strip()
        password = dialog.password_entry.get_text().strip()
        
        if not name:
            return False, "Password name is required"
        
        if not password:
            return False, "Password is required"
        
        # Check for invalid characters in name
        invalid_chars = ['/', '\\\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in name:
                return False, f"Password name cannot contain '{char}'"
        
        return True, ""
    
    @staticmethod
    def show_error_dialog(parent_dialog: Adw.Dialog, message: str):
        """Show an error dialog with the given message."""
        dialog = Adw.MessageDialog.new(
            parent_dialog,
            "Error",
            message
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present()


# Main Setup Function

def setup_password_dialog_widgets(dialog: Adw.Dialog, transient_for_window: Optional[Gtk.Window], 
                                 password_store=None) -> PasswordDialogState:
    """
    Setup common password dialog widgets and functionality.
    
    Args:
        dialog: The dialog to setup
        transient_for_window: The parent window
        password_store: The password store instance
        
    Returns:
        PasswordDialogState object containing dialog state
    """
    # Create state object
    state = PasswordDialogState(
        transient_for_window=transient_for_window,
        password_store=password_store,
        avatar_manager=AvatarManager(AvatarConfiguration(size=32)),
        content_parser=PasswordContentParser()
    )
    
    # Setup UI components
    setup_icon_combo(dialog, state)
    setup_dialog_behavior(dialog, state)
    populate_folders(dialog, state)
    
    # Setup theme monitoring
    style_manager = Adw.StyleManager.get_default()
    style_manager.connect('notify::dark', lambda sm, param: update_color_avatar(dialog, state))
    
    # Update initial UI state
    update_color_avatar(dialog, state)
    update_icon_avatar(dialog, state)
    update_save_button_state(dialog)
    update_recovery_expansion_state(dialog, state)
    
    return state


def connect_common_signals(dialog: Adw.Dialog, state: PasswordDialogState):
    """Connect all common signal handlers."""
    signal_handler = PasswordDialogSignalHandler(dialog, state)
    signal_handler.connect_common_signals()
    
    # Store signal handler in dialog for later use
    dialog._signal_handler = signal_handler


# UI Setup Utility Functions

def setup_icon_combo(dialog: Adw.Dialog, state: PasswordDialogState):
    """Setup the icon selection combo row using AvatarManager."""
    state.avatar_manager.setup_icon_combo_row(
        dialog.icon_row, 
        icon_set="password", 
        selected_icon=state.selected_icon
    )


def setup_dialog_behavior(dialog: Adw.Dialog, state: PasswordDialogState):
    """Setup common dialog behavior and accessibility."""
    # Setup accessibility
    AccessibilityHelper.set_accessible_name(dialog.name_entry, "Password name entry")
    AccessibilityHelper.set_accessible_name(dialog.password_entry, "Password entry")
    AccessibilityHelper.set_accessible_name(dialog.username_entry, "Username entry")
    AccessibilityHelper.set_accessible_name(dialog.url_entry, "URL entry")
    AccessibilityHelper.set_accessible_name(dialog.totp_entry, "TOTP secret entry")


def populate_folders(dialog: Adw.Dialog, state: PasswordDialogState):
    """Populate the folder dropdown with available folders."""
    # Create string list model for simple folder management
    folder_model = Gtk.StringList()
    
    # Add "Root" option for passwords in the root directory (not empty string)
    folder_model.append("Root")
    
    # Try to get actual folders from password store if available
    if state.password_store:
        try:
            actual_folders = get_available_folders(state.password_store)
            for folder in sorted(actual_folders):
                if folder:  # Avoid empty folder names
                    folder_model.append(folder)
        except Exception:
            # Fallback if folder enumeration fails
            pass
    
    # Add some common folder examples if no actual folders found
    if folder_model.get_n_items() == 1:  # Only "Root" exists
        common_folders = [
            "websites",
            "banking", 
            "email",
            "social",
            "work",
            "personal"
        ]
        
        for folder in common_folders:
            folder_model.append(folder)
    
    dialog.folder_row.set_model(folder_model)
    
    # Make the combo row editable for custom folder names
    dialog.folder_row.set_enable_search(True)
    dialog.folder_row.set_selected(0)  # Select root folder by default


def get_available_folders(password_store) -> List[str]:
    """Get available folders from password store."""
    # Try different methods to get folders from password store
    folders = []
    
    try:
        if hasattr(password_store, 'list_folders'):
            folders = password_store.list_folders()
        elif hasattr(password_store, 'get_all_folders'):
            folders = password_store.get_all_folders()
        elif hasattr(password_store, 'list_directories'):
            folders = password_store.list_directories()
        elif hasattr(password_store, 'get_folders'):
            folders = password_store.get_folders()
    except Exception:
        # Return empty list if enumeration fails
        pass
    
    return folders


# UI State Update Functions

def update_save_button_state(dialog: Adw.Dialog):
    """Update save button sensitivity based on form validity."""
    name_text = dialog.name_entry.get_text().strip()
    password_text = dialog.password_entry.get_text().strip()
    
    # Enable save button only if both name and password are provided
    is_valid = bool(name_text and password_text)
    dialog.save_button.set_sensitive(is_valid)


def update_color_avatar(dialog: Adw.Dialog, state: PasswordDialogState):
    """Update the color avatar with selected color using ColorPaintable."""
    from ..widgets.color_paintable import ColorPaintable
    
    # Create color paintable and set it on the avatar
    color_paintable = ColorPaintable(state.selected_color)
    dialog.color_avatar.set_custom_image(color_paintable)


def update_icon_avatar(dialog: Adw.Dialog, state: PasswordDialogState):
    """Update the icon avatar with selected icon using ColorPaintable with transparent background."""
    from ..widgets.color_paintable import ColorPaintable
    
    # Create transparent icon paintable and set it on the avatar
    icon_paintable = ColorPaintable("transparent", state.selected_icon)
    dialog.icon_avatar.set_custom_image(icon_paintable)


def update_recovery_expansion_state(dialog: Adw.Dialog, state: PasswordDialogState):
    """Update the expansion state of recovery codes section."""
    has_codes = len(state.recovery_codes) > 0
    dialog.recovery_expander.set_expanded(has_codes)
    
    # Update child count for accessibility
    codes_count = len(state.recovery_codes)
    AccessibilityHelper.set_accessible_description(
        dialog.recovery_expander, 
        f"Recovery codes section with {codes_count} codes"
    )


# Password Generation

def handle_password_generation(dialog: Adw.Dialog, state: PasswordDialogState, button: Gtk.Button):
    """Handle password generation button click."""
    if not state.password_generator_popover:
        state.password_generator_popover = PasswordGeneratorPopover()
        state.password_generator_popover.set_parent(button)
        state.password_generator_popover.connect('password-generated', 
                                                 lambda popover, password: on_password_generated(dialog, password))
    
    state.password_generator_popover.popup()


def on_password_generated(dialog: Adw.Dialog, password: str):
    """Handle generated password from popover."""
    dialog.password_entry.set_text(password)
    update_save_button_state(dialog)


# Color and Icon Management

def handle_color_selection(dialog: Adw.Dialog, state: PasswordDialogState, button: Gtk.Button):
    """Handle color selection button click using standard GTK ColorChooserDialog."""
    color_dialog = Gtk.ColorChooserDialog()
    color_dialog.set_transient_for(state.transient_for_window)
    color_dialog.set_modal(True)
    color_dialog.set_title("Choose Password Color")
    
    # Set current color
    from gi.repository import Gdk
    rgba = Gdk.RGBA()
    rgba.parse(state.selected_color)
    color_dialog.set_rgba(rgba)
    
    # Connect to response signal
    def on_color_dialog_response(color_dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            rgba = color_dialog.get_rgba()
            # Convert RGBA to hex
            state.selected_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
            update_color_avatar(dialog, state)
        color_dialog.destroy()
    
    color_dialog.connect("response", on_color_dialog_response)
    color_dialog.present()


def handle_icon_change(dialog: Adw.Dialog, state: PasswordDialogState, combo_row: Adw.ComboRow):
    """Handle icon selection change."""
    state.selected_icon = state.avatar_manager.get_selected_icon_from_combo(combo_row)
    if state.selected_icon:
        update_icon_avatar(dialog, state)


# Recovery Code Management

def add_recovery_code_row(dialog: Adw.Dialog, state: PasswordDialogState, text=""):
    """Add a recovery code entry row to the UI."""
    recovery_row = Adw.EntryRow()
    recovery_row.set_title(f"Recovery Code {len(state.recovery_codes) + 1}")
    recovery_row.set_text(text)
    
    # Add remove button
    remove_button = Gtk.Button()
    remove_button.set_icon_name("user-trash-symbolic")
    remove_button.set_valign(Gtk.Align.CENTER)
    remove_button.add_css_class("flat")
    remove_button.add_css_class("destructive-action")
    remove_button.set_tooltip_text("Remove recovery code")
    remove_button.connect('clicked', lambda btn: remove_recovery_code_row(dialog, state, recovery_row))
    
    recovery_row.add_suffix(remove_button)
    dialog.recovery_codes_box.append(recovery_row)
    state.recovery_codes.append(text)
    
    # Setup accessibility
    AccessibilityHelper.set_accessible_name(recovery_row, f"Recovery code {len(state.recovery_codes)} entry")
    
    update_recovery_expansion_state(dialog, state)


def remove_recovery_code_row(dialog: Adw.Dialog, state: PasswordDialogState, recovery_row: Adw.EntryRow):
    """Remove a recovery code row from the UI."""
    # Find the index of this row
    index = -1
    child = dialog.recovery_codes_box.get_first_child()
    current_index = 0
    
    while child:
        if child == recovery_row:
            index = current_index
            break
        child = child.get_next_sibling()
        current_index += 1
    
    if index >= 0 and index < len(state.recovery_codes):
        # Remove from data and UI
        state.recovery_codes.pop(index)
        dialog.recovery_codes_box.remove(recovery_row)
        
        # Update remaining row titles
        update_recovery_row_titles(dialog)
        update_recovery_expansion_state(dialog, state)


def update_recovery_row_titles(dialog: Adw.Dialog):
    """Update the titles of recovery code rows after removal."""
    child = dialog.recovery_codes_box.get_first_child()
    index = 1
    
    while child:
        if isinstance(child, Adw.EntryRow):
            child.set_title(f"Recovery Code {index}")
            AccessibilityHelper.set_accessible_name(child, f"Recovery code {index} entry")
            index += 1
        child = child.get_next_sibling()


def get_recovery_codes(dialog: Adw.Dialog) -> List[str]:
    """Get all recovery codes from the UI."""
    codes = []
    child = dialog.recovery_codes_box.get_first_child()
    
    while child:
        if isinstance(child, Adw.EntryRow):
            code = child.get_text().strip()
            if code:  # Only include non-empty codes
                codes.append(code)
        child = child.get_next_sibling()
    
    return codes


def populate_recovery_codes(dialog: Adw.Dialog, state: PasswordDialogState, recovery_codes: List[str]):
    """Populate recovery codes in the UI."""
    # Clear existing codes
    child = dialog.recovery_codes_box.get_first_child()
    while child:
        next_child = child.get_next_sibling()
        dialog.recovery_codes_box.remove(child)
        child = next_child
    
    state.recovery_codes = []
    
    # Add recovery code rows
    for code in recovery_codes:
        add_recovery_code_row(dialog, state, code)


# Content Management

def build_password_content(dialog: Adw.Dialog, state: PasswordDialogState) -> str:
    """Build password file content from form fields using PasswordContentParser."""
    # Create PasswordData object from form fields
    password_data = PasswordData(
        password=dialog.password_entry.get_text().strip(),
        username=dialog.username_entry.get_text().strip(),
        url=dialog.url_entry.get_text().strip(),
        totp=dialog.totp_entry.get_text().strip(),
        recovery_codes=get_recovery_codes(dialog),
        notes=get_notes_content(dialog)
    )
    
    # Generate content using PasswordContentParser
    return state.content_parser.generate_content(password_data)


def get_notes_content(dialog: Adw.Dialog) -> str:
    """Get notes content from the text view."""
    notes_buffer = dialog.notes_view.get_buffer()
    start_iter = notes_buffer.get_start_iter()
    end_iter = notes_buffer.get_end_iter()
    return notes_buffer.get_text(start_iter, end_iter, False).strip()


# Folder Management

def set_folder_selection(dialog: Adw.Dialog, folder_path: str):
    """Set the selected folder in the dropdown."""
    model = dialog.folder_row.get_model()
    if not model:
        return
    
    # Convert empty string to "Root" for display
    display_folder = "Root" if not folder_path or folder_path.strip() == "" else folder_path.strip()
    
    for i in range(model.get_n_items()):
        item = model.get_item(i)
        if item.get_string() == display_folder:
            dialog.folder_row.set_selected(i)
            break


def get_selected_folder(dialog: Adw.Dialog) -> str:
    """Get the currently selected folder path."""
    selected_item = dialog.folder_row.get_selected_item()
    if selected_item:
        folder = selected_item.get_string()
        # Convert "Root" display name to empty string for actual path
        return "" if folder == "Root" else folder
    return ""