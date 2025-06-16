"""
Toast manager for handling toast notifications.
"""

from gi.repository import Adw


class ToastManager:
    """Manages toast notifications throughout the application."""
    
    def __init__(self, toast_overlay: Adw.ToastOverlay):
        self.toast_overlay = toast_overlay
    
    def show_info(self, message: str):
        """Show an informational toast."""
        self.toast_overlay.add_toast(Adw.Toast.new(message))
    
    def show_success(self, message: str):
        """Show a success toast."""
        toast = Adw.Toast.new(message)
        self.toast_overlay.add_toast(toast)
    
    def show_error(self, message: str):
        """Show an error toast."""
        toast = Adw.Toast.new(f"Error: {message}")
        self.toast_overlay.add_toast(toast)
    
    def show_warning(self, message: str):
        """Show a warning toast."""
        toast = Adw.Toast.new(f"Warning: {message}")
        self.toast_overlay.add_toast(toast)
