"""
UI utilities for consistent dialog management and positioning.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk
from typing import Optional, Tuple, Union


class DialogManager:
    """Manages dialog creation, positioning, and behavior for consistent UX."""
    
    @staticmethod
    def center_dialog_on_parent(dialog: Union[Adw.Window, Adw.Dialog, Adw.AlertDialog], parent: Optional[Adw.Window] = None):
        """
        Center a dialog on its parent window.

        In GTK4, manual window positioning is discouraged and the window manager
        typically handles dialog positioning automatically when using transient_for.
        This method ensures the dialog has proper transient relationship.

        Args:
            dialog: The dialog window to center (Adw.Window, Adw.Dialog, or Adw.AlertDialog)
            parent: The parent window (if None, uses transient_for for Adw.Window)
        """
        # Handle Adw.Dialog and Adw.AlertDialog differently from Adw.Window
        if isinstance(dialog, (Adw.Dialog, Adw.AlertDialog)):
            # Adw.Dialog and Adw.AlertDialog don't use transient_for, they're presented on a parent
            # The centering is handled automatically when presented
            return

        # Handle Adw.Window
        if parent is None:
            parent = dialog.get_transient_for()

        # Ensure proper transient relationship for automatic centering
        if parent and dialog.get_transient_for() != parent:
            dialog.set_transient_for(parent)

        # In GTK4, the window manager handles centering automatically
        # when the dialog has a proper transient_for relationship.
        # We don't need to manually calculate positions.
    
    @staticmethod
    def _center_on_screen(dialog: Adw.Window):
        """
        Center dialog on the default screen.

        In GTK4, this is handled automatically by the window manager.
        This method is kept for compatibility but doesn't perform manual positioning.
        """
        # In GTK4, centering is handled automatically by the window manager
        # when no transient_for is set. No manual positioning needed.
        pass
    
    @staticmethod
    def create_message_dialog(
        parent: Adw.Window,
        heading: str,
        body: str,
        dialog_type: str = "info",
        default_size: Tuple[int, int] = (400, 250)
    ) -> Adw.AlertDialog:
        """
        Create a properly configured message dialog using Adw.AlertDialog.

        Args:
            parent: Parent window
            heading: Dialog heading text
            body: Dialog body text
            dialog_type: Type of dialog ("info", "warning", "error", "question")
            default_size: Default dialog size (width, height) - used for content sizing

        Returns:
            Configured Adw.AlertDialog
        """
        # Create the alert dialog with heading and body
        dialog = Adw.AlertDialog.new(heading, body)

        # Set content size
        dialog.set_content_width(default_size[0])
        dialog.set_content_height(default_size[1])

        # Add appropriate styling based on type
        if dialog_type == "error":
            dialog.add_css_class("error")
        elif dialog_type == "warning":
            dialog.add_css_class("warning")
        elif dialog_type == "question":
            dialog.add_css_class("question")

        return dialog

    @staticmethod
    def add_dialog_response(dialog: Adw.AlertDialog, response_id: str, label: str, appearance: str = "default"):
        """
        Add a response button to an Adw.AlertDialog.

        Args:
            dialog: The AlertDialog to add the response to
            response_id: ID for the response
            label: Button label
            appearance: Button appearance ("default", "suggested", "destructive")
        """
        # Add the response using AlertDialog's built-in method
        dialog.add_response(response_id, label)

        # Set appearance if specified
        if appearance == "suggested":
            dialog.set_response_appearance(response_id, Adw.ResponseAppearance.SUGGESTED)
        elif appearance == "destructive":
            dialog.set_response_appearance(response_id, Adw.ResponseAppearance.DESTRUCTIVE)

        # Set as default if it's suggested
        if appearance == "suggested":
            dialog.set_default_response(response_id)
    
    @staticmethod
    def create_custom_dialog(
        parent: Adw.Window,
        title: str,
        default_size: Tuple[int, int] = (450, 400),
        modal: bool = True,
        resizable: bool = True
    ) -> Adw.Window:
        """
        Create a properly configured custom dialog window.
        
        Args:
            parent: Parent window
            title: Dialog title
            default_size: Default dialog size (width, height)
            modal: Whether dialog should be modal
            resizable: Whether dialog should be resizable
        
        Returns:
            Configured Adw.Window
        """
        dialog = Adw.Window(
            modal=modal,
            transient_for=parent,
            title=title
        )
        
        dialog.set_default_size(*default_size)
        dialog.set_resizable(resizable)
        
        # Add dialog styling
        dialog.add_css_class("dialog")
        
        return dialog
    
    @staticmethod
    def setup_dialog_keyboard_navigation(dialog: Adw.Window):
        """
        Set up proper keyboard navigation for a dialog.
        
        Args:
            dialog: The dialog to configure
        """
        # Add Escape key handler to close dialog
        escape_controller = Gtk.EventControllerKey()
        
        def on_key_pressed(_controller, keyval, _keycode, _state):
            if keyval == Gdk.KEY_Escape:
                dialog.close()
                return True
            return False
        
        escape_controller.connect("key-pressed", on_key_pressed)
        dialog.add_controller(escape_controller)
    
    @staticmethod
    def ensure_dialog_focus(dialog: Adw.Window):
        """
        Ensure proper focus management for a dialog.
        
        Args:
            dialog: The dialog window
            focus_widget: Widget to focus (if None, finds first focusable widget)
        """
        def on_dialog_shown(dialog):
            DialogManager._focus_first_widget(dialog)
        
        dialog.connect("show", on_dialog_shown)
    
    @staticmethod
    def _focus_first_widget(container: Gtk.Widget):
        """Find and focus the first focusable widget in a container."""
        def find_focusable(widget):
            if widget.get_can_focus() and widget.get_sensitive() and widget.get_visible():
                widget.grab_focus()
                return True
            
            # Check children if it's a container
            if hasattr(widget, 'get_first_child'):
                child = widget.get_first_child()
                while child:
                    if find_focusable(child):
                        return True
                    child = child.get_next_sibling()
            
            return False
        
        find_focusable(container)


class UIConstants:
    """Constants for consistent UI sizing and spacing."""
    
    # Dialog sizes
    SMALL_DIALOG = (400, 250)
    MEDIUM_DIALOG = (450, 400)
    LARGE_DIALOG = (600, 500)
    EXTRA_LARGE_DIALOG = (700, 600)
    
    # Spacing
    SMALL_SPACING = 6
    MEDIUM_SPACING = 12
    LARGE_SPACING = 18
    EXTRA_LARGE_SPACING = 24
    
    # Margins
    SMALL_MARGIN = 6
    MEDIUM_MARGIN = 12
    LARGE_MARGIN = 18
    
    # Button sizes
    MIN_BUTTON_WIDTH = 80
    ICON_BUTTON_SIZE = 32


class AccessibilityHelper:
    """Helper functions for improving accessibility."""

    @staticmethod
    def set_accessible_name(widget: Gtk.Widget, name: str):
        """Set accessible name for a widget."""
        try:
            widget.set_accessible_role(Gtk.AccessibleRole.GENERIC)
            # GTK4 update_property expects lists of properties and values
            from gi.repository import GObject
            value = GObject.Value(GObject.TYPE_STRING, name)
            widget.update_property([Gtk.AccessibleProperty.LABEL], [value])
        except Exception as e:
            # Fallback: just set the role if accessibility update fails
            print(f"Warning: Failed to set accessible name: {e}")
            try:
                widget.set_accessible_role(Gtk.AccessibleRole.GENERIC)
            except:
                pass

    @staticmethod
    def set_accessible_description(widget: Gtk.Widget, description: str):
        """Set accessible description for a widget."""
        try:
            # GTK4 update_property expects lists of properties and values
            from gi.repository import GObject
            value = GObject.Value(GObject.TYPE_STRING, description)
            widget.update_property([Gtk.AccessibleProperty.DESCRIPTION], [value])
        except Exception as e:
            # Silently fail if accessibility update fails
            print(f"Warning: Failed to set accessible description: {e}")

    @staticmethod
    def mark_as_live_region(widget: Gtk.Widget, politeness: str = "polite"):
        """Mark a widget as a live region for screen readers."""
        try:
            # GTK4 update_property expects lists of properties and values
            from gi.repository import GObject
            if politeness == "assertive":
                live_value = Gtk.AccessibleLive.ASSERTIVE
            else:
                live_value = Gtk.AccessibleLive.POLITE

            value = GObject.Value(Gtk.AccessibleLive, live_value)
            widget.update_property([Gtk.AccessibleProperty.LIVE], [value])
        except Exception as e:
            # Silently fail if accessibility update fails
            print(f"Warning: Failed to set live region: {e}")
