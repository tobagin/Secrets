"""
Security manager for handling session locking, idle detection, and security features.
"""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

import time
import threading
from typing import Optional, Callable
from gi.repository import GLib, Gtk, Adw

from .config import ConfigManager
from .i18n import get_translation_function

# Get translation function
_ = get_translation_function()


class IdleDetector:
    """Detects user idle time by monitoring activity."""
    
    def __init__(self):
        self._last_activity_time = time.time()
        self._activity_callbacks = []
        self._monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring user activity."""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._last_activity_time = time.time()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_activity, daemon=True)
        self._monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring user activity."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            
    def register_activity_callback(self, callback: Callable):
        """Register callback to be called on user activity."""
        self._activity_callbacks.append(callback)
        
    def get_idle_time_seconds(self) -> float:
        """Get current idle time in seconds."""
        return time.time() - self._last_activity_time
        
    def reset_idle_timer(self):
        """Reset the idle timer (called on user activity)."""
        self._last_activity_time = time.time()
        for callback in self._activity_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in activity callback: {e}")
                
    def _monitor_activity(self):
        """Monitor activity in background thread."""
        while self._monitoring:
            try:
                # Check for system idle time using various methods
                idle_time = self._get_system_idle_time()
                if idle_time is not None and idle_time < 1.0:
                    # User is active, reset timer
                    GLib.idle_add(self.reset_idle_timer)
                    
                time.sleep(1.0)  # Check every second
            except Exception as e:
                print(f"Error monitoring activity: {e}")
                time.sleep(5.0)  # Wait longer on error
                
    def _get_system_idle_time(self) -> Optional[float]:
        """Get system idle time using available methods."""
        try:
            # Try X11 method first
            import subprocess
            result = subprocess.run(['xprintidle'], capture_output=True, text=True, timeout=1.0)
            if result.returncode == 0:
                return float(result.stdout.strip()) / 1000.0  # Convert ms to seconds
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
            pass
            
        try:
            # Try using /proc/interrupts as fallback
            with open('/proc/interrupts', 'r') as f:
                content = f.read()
                # This is a very basic heuristic - in real implementation
                # you'd want more sophisticated idle detection
                return None
        except (FileNotFoundError, PermissionError):
            pass
            
        return None


class SecurityManager:
    """Manages application security features including session locking."""
    
    def __init__(self, config_manager: ConfigManager, main_window=None):
        self.config_manager = config_manager
        self.main_window = main_window
        self.idle_detector = IdleDetector()
        
        # Security state
        self._is_locked = False
        self._failed_unlock_attempts = 0
        self._lockout_until = None
        self._master_password_last_entered = None
        self._idle_timeout_id = None
        self._master_password_timeout_id = None
        
        # Callbacks
        self._lock_callbacks = []
        self._unlock_callbacks = []
        
        # Setup idle detection
        self.idle_detector.register_activity_callback(self._on_user_activity)
        
    def start_security_monitoring(self):
        """Start security monitoring (idle detection, timeouts)."""
        config = self.config_manager.get_config()
        
        if config.security.lock_on_idle:
            self.idle_detector.start_monitoring()
            self._schedule_idle_check()
            
        if config.security.master_password_timeout_minutes > 0:
            self._schedule_master_password_timeout()
            
    def stop_security_monitoring(self):
        """Stop security monitoring."""
        self.idle_detector.stop_monitoring()
        self._cancel_timeouts()
        
    def register_lock_callback(self, callback: Callable):
        """Register callback to be called when application is locked."""
        self._lock_callbacks.append(callback)
        
    def register_unlock_callback(self, callback: Callable):
        """Register callback to be called when application is unlocked."""
        self._unlock_callbacks.append(callback)
        
    def is_locked(self) -> bool:
        """Check if application is currently locked."""
        return self._is_locked
        
    def is_in_lockout(self) -> bool:
        """Check if application is in lockout period."""
        if self._lockout_until is None:
            return False
        return time.time() < self._lockout_until
        
    def get_lockout_remaining_seconds(self) -> int:
        """Get remaining lockout time in seconds."""
        if not self.is_in_lockout():
            return 0
        return int(self._lockout_until - time.time())
        
    def lock_application(self, reason: str = "Manual lock"):
        """Lock the application."""
        if self._is_locked:
            return
            
        self._is_locked = True
        print(f"Application locked: {reason}")
        
        # Clear sensitive data if configured
        config = self.config_manager.get_config()
        if config.security.clear_memory_on_lock:
            self._clear_sensitive_memory()
            
        # Call lock callbacks
        for callback in self._lock_callbacks:
            try:
                GLib.idle_add(callback)
            except Exception as e:
                print(f"Error in lock callback: {e}")
                
        # Show lock screen
        GLib.idle_add(self._show_lock_screen)
        
    def unlock_application(self, password: str = None) -> bool:
        """Attempt to unlock the application."""
        if not self._is_locked:
            return True
            
        if self.is_in_lockout():
            return False
            
        # For now, we'll assume unlock is successful if GPG is working
        # In a real implementation, you'd verify the master password
        success = self._verify_master_password(password)
        
        if success:
            self._is_locked = False
            self._failed_unlock_attempts = 0
            self._master_password_last_entered = time.time()
            
            # Call unlock callbacks
            for callback in self._unlock_callbacks:
                try:
                    GLib.idle_add(callback)
                except Exception as e:
                    print(f"Error in unlock callback: {e}")
                    
            print("Application unlocked successfully")
            return True
        else:
            self._failed_unlock_attempts += 1
            config = self.config_manager.get_config()
            
            if self._failed_unlock_attempts >= config.security.max_failed_unlock_attempts:
                # Start lockout period
                lockout_duration = config.security.lockout_duration_minutes * 60
                self._lockout_until = time.time() + lockout_duration
                print(f"Too many failed attempts. Locked out for {config.security.lockout_duration_minutes} minutes.")
                
            return False
            
    def _verify_master_password(self, password: str = None) -> bool:
        """Verify the master password (GPG passphrase)."""
        # This is a simplified implementation
        # In practice, you'd test GPG decryption with the provided password
        return True  # For now, always succeed
        
    def _clear_sensitive_memory(self):
        """Clear sensitive data from memory."""
        # This would clear password caches, clipboard, etc.
        try:
            from .performance import password_cache
            password_cache.clear()
        except ImportError:
            pass
            
    def _show_lock_screen(self):
        """Show the lock screen dialog."""
        if not self.main_window:
            return
            
        # Create and show lock dialog
        from .ui.dialogs.lock_dialog import LockDialog
        lock_dialog = LockDialog(self.main_window, self)
        lock_dialog.present()
        
    def _on_user_activity(self):
        """Called when user activity is detected."""
        # Reset idle timeout
        self._schedule_idle_check()
        
    def _schedule_idle_check(self):
        """Schedule the next idle check."""
        self._cancel_idle_timeout()
        
        config = self.config_manager.get_config()
        if not config.security.lock_on_idle:
            return
            
        timeout_seconds = config.security.idle_timeout_minutes * 60
        self._idle_timeout_id = GLib.timeout_add_seconds(timeout_seconds, self._check_idle_timeout)
        
    def _schedule_master_password_timeout(self):
        """Schedule master password timeout check."""
        config = self.config_manager.get_config()
        if config.security.master_password_timeout_minutes <= 0:
            return
            
        timeout_seconds = config.security.master_password_timeout_minutes * 60
        self._master_password_timeout_id = GLib.timeout_add_seconds(
            timeout_seconds, self._check_master_password_timeout
        )
        
    def _check_idle_timeout(self) -> bool:
        """Check if idle timeout has been reached."""
        config = self.config_manager.get_config()
        
        if not config.security.lock_on_idle:
            return False
            
        idle_time = self.idle_detector.get_idle_time_seconds()
        timeout_seconds = config.security.idle_timeout_minutes * 60
        
        if idle_time >= timeout_seconds:
            self.lock_application("Idle timeout")
            return False  # Don't repeat
            
        return True  # Continue checking
        
    def _check_master_password_timeout(self) -> bool:
        """Check if master password timeout has been reached."""
        config = self.config_manager.get_config()
        
        if config.security.master_password_timeout_minutes <= 0:
            return False
            
        if self._master_password_last_entered is None:
            return True  # Continue checking
            
        elapsed = time.time() - self._master_password_last_entered
        timeout_seconds = config.security.master_password_timeout_minutes * 60
        
        if elapsed >= timeout_seconds:
            self.lock_application("Master password timeout")
            return False  # Don't repeat
            
        return True  # Continue checking
        
    def _cancel_timeouts(self):
        """Cancel all active timeouts."""
        self._cancel_idle_timeout()
        self._cancel_master_password_timeout()
        
    def _cancel_idle_timeout(self):
        """Cancel idle timeout."""
        if self._idle_timeout_id:
            GLib.source_remove(self._idle_timeout_id)
            self._idle_timeout_id = None
            
    def _cancel_master_password_timeout(self):
        """Cancel master password timeout."""
        if self._master_password_timeout_id:
            GLib.source_remove(self._master_password_timeout_id)
            self._master_password_timeout_id = None
