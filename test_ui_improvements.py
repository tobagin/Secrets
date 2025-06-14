#!/usr/bin/env python3
"""
Test script to verify UI improvements are working correctly.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
import sys
import os

# Add the secrets module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secrets'))

from secrets.ui_utils import DialogManager, UIConstants, AccessibilityHelper
from secrets.edit_dialog import EditPasswordDialog
from secrets.add_password_dialog import AddPasswordDialog
from secrets.move_rename_dialog import MoveRenameDialog


class TestWindow(Adw.ApplicationWindow):
    """Test window to demonstrate UI improvements."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.set_title("UI Improvements Test")
        self.set_default_size(600, 400)
        
        # Create main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        self.set_content(main_box)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="UI Test", subtitle="Testing Dialog Improvements"))
        main_box.append(header)
        
        # Test buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.append(button_box)
        
        # Test edit dialog
        edit_button = Gtk.Button(label="Test Edit Dialog")
        edit_button.connect("clicked", self._test_edit_dialog)
        edit_button.add_css_class("suggested-action")
        button_box.append(edit_button)
        
        # Test add dialog
        add_button = Gtk.Button(label="Test Add Dialog")
        add_button.connect("clicked", self._test_add_dialog)
        button_box.append(add_button)
        
        # Test move/rename dialog
        move_button = Gtk.Button(label="Test Move/Rename Dialog")
        move_button.connect("clicked", self._test_move_dialog)
        button_box.append(move_button)
        
        # Test message dialog
        message_button = Gtk.Button(label="Test Message Dialog")
        message_button.connect("clicked", self._test_message_dialog)
        button_box.append(message_button)
        
        # Test custom dialog
        custom_button = Gtk.Button(label="Test Custom Dialog")
        custom_button.connect("clicked", self._test_custom_dialog)
        button_box.append(custom_button)
    
    def _test_edit_dialog(self, button):
        """Test the edit dialog."""
        dialog = EditPasswordDialog(
            password_path="Test/Password",
            password_content="test password\nusername: testuser\nurl: https://example.com\nnotes: This is a test password entry",
            transient_for_window=self
        )
        dialog.connect("save-requested", self._on_dialog_save)
        dialog.present()
    
    def _test_add_dialog(self, button):
        """Test the add dialog."""
        dialog = AddPasswordDialog(
            transient_for_window=self,
            suggested_folder_path="Test"
        )
        dialog.connect("add-requested", self._on_dialog_add)
        dialog.present()
    
    def _test_move_dialog(self, button):
        """Test the move/rename dialog."""
        dialog = MoveRenameDialog(
            current_path="Test/OldPassword",
            transient_for_window=self
        )
        dialog.connect("save-requested", self._on_dialog_move)
        dialog.present()
    
    def _test_message_dialog(self, button):
        """Test the message dialog."""
        dialog = DialogManager.create_message_dialog(
            parent=self,
            heading="Test Message Dialog",
            body="This is a test message dialog with improved positioning and styling.",
            dialog_type="info",
            default_size=UIConstants.SMALL_DIALOG
        )
        # Add response button using the AlertDialog API
        DialogManager.add_dialog_response(dialog, "ok", "_OK", "suggested")
        dialog.connect("response", lambda _d, _r: None)
        
        # Set up proper dialog behavior
        DialogManager.setup_dialog_keyboard_navigation(dialog)
        DialogManager.center_dialog_on_parent(dialog, self)
        
        dialog.present()
    
    def _test_custom_dialog(self, button):
        """Test a custom dialog."""
        dialog = DialogManager.create_custom_dialog(
            parent=self,
            title="Custom Test Dialog",
            default_size=UIConstants.MEDIUM_DIALOG
        )
        
        # Add content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(18)
        content_box.set_margin_bottom(18)
        content_box.set_margin_start(18)
        content_box.set_margin_end(18)
        dialog.set_content(content_box)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Custom Dialog"))
        close_button = Gtk.Button(label="_Close", use_underline=True)
        close_button.connect("clicked", lambda b: dialog.close())
        header.pack_end(close_button)
        content_box.append(header)
        
        # Content
        label = Gtk.Label(label="This is a custom dialog with improved styling and positioning.")
        label.set_wrap(True)
        content_box.append(label)
        
        # Set up dialog behavior
        DialogManager.setup_dialog_keyboard_navigation(dialog)
        DialogManager.ensure_dialog_focus(dialog)
        DialogManager.center_dialog_on_parent(dialog, self)
        
        dialog.present()
    
    def _on_dialog_save(self, dialog, path, content):
        """Handle dialog save."""
        print(f"Save requested: {path}")
        print(f"Content: {content}")
        dialog.close()
    
    def _on_dialog_add(self, dialog, path, content):
        """Handle dialog add."""
        print(f"Add requested: {path}")
        print(f"Content: {content}")
        dialog.close()
    
    def _on_dialog_move(self, dialog, old_path, new_path):
        """Handle dialog move."""
        print(f"Move requested: {old_path} -> {new_path}")
        dialog.close()


class TestApplication(Adw.Application):
    """Test application."""
    
    def __init__(self):
        super().__init__(application_id="com.example.ui_test")
    
    def do_activate(self):
        """Activate the application."""
        window = TestWindow(application=self)
        window.present()


if __name__ == "__main__":
    app = TestApplication()
    app.run(sys.argv)
