"""Environment setup utilities for GPG and password store operations."""

import os
from typing import Dict, Optional
from .gpg_utils import GPGSetupHelper


class EnvironmentSetup:
    """Centralized environment setup for password store and GPG operations."""
    
    def __init__(self, store_dir: Optional[str] = None, gpg_home: Optional[str] = None):
        """
        Initialize environment setup.
        
        Args:
            store_dir: Password store directory (defaults to ~/.password-store)
            gpg_home: GPG home directory (defaults to ~/.gnupg)
        """
        self.store_dir = store_dir or os.path.expanduser("~/.password-store")
        self.gpg_home = gpg_home or os.path.expanduser("~/.gnupg")
        self._cached_env: Optional[Dict[str, str]] = None
    
    def get_environment(self, tty: Optional[str] = None) -> Dict[str, str]:
        """
        Get a complete environment dictionary for password store operations.
        
        Args:
            tty: TTY device path (auto-detected if None)
            
        Returns:
            Environment dictionary with all necessary variables
        """
        if self._cached_env is None or tty is not None:
            self._cached_env = self._build_environment(tty)
        return self._cached_env.copy()
    
    def _build_environment(self, tty: Optional[str] = None) -> Dict[str, str]:
        """Build the environment dictionary."""
        # Start with current environment
        env = os.environ.copy()
        
        # Set up GPG environment using helper
        gpg_helper = GPGSetupHelper(self.gpg_home)
        gpg_env = gpg_helper.setup_gpg_environment(tty=tty)
        env.update(gpg_env)
        
        # Set password store directory if not default
        default_store = os.path.expanduser("~/.password-store")
        if self.store_dir != default_store:
            env["PASSWORD_STORE_DIR"] = self.store_dir
        
        # Ensure critical environment variables
        env["PASSWORD_STORE_ENABLE_EXTENSIONS"] = "true"
        env["PASSWORD_STORE_CLIP_TIME"] = "45"
        
        # Security settings
        env["PASSWORD_STORE_GENERATED_LENGTH"] = "25"
        
        return env
    
    def clear_cache(self):
        """Clear the cached environment (useful for testing or config changes)."""
        self._cached_env = None
    
    def get_store_environment(self) -> Dict[str, str]:
        """
        Get environment specifically for password store operations.
        
        This is a lightweight version that only includes store-specific variables.
        """
        env = {
            "PASSWORD_STORE_DIR": self.store_dir,
            "PASSWORD_STORE_ENABLE_EXTENSIONS": "true",
            "PASSWORD_STORE_CLIP_TIME": "45",
            "PASSWORD_STORE_GENERATED_LENGTH": "25",
        }
        
        # Add GPG home if not default
        default_gpg_home = os.path.expanduser("~/.gnupg")
        if self.gpg_home != default_gpg_home:
            env["GNUPGHOME"] = self.gpg_home
        
        return env
    
    def get_gpg_environment(self, tty: Optional[str] = None) -> Dict[str, str]:
        """
        Get environment specifically for GPG operations.
        
        Args:
            tty: TTY device path (auto-detected if None)
            
        Returns:
            Environment dictionary for GPG operations
        """
        gpg_helper = GPGSetupHelper(self.gpg_home)
        return gpg_helper.setup_gpg_environment(tty=tty)
    
    def validate_environment(self) -> tuple[bool, str]:
        """
        Validate that the environment is properly set up.
        
        Returns:
            (bool, str): (is_valid, error_message)
        """
        errors = []
        
        # Check store directory
        if not os.path.exists(self.store_dir):
            errors.append(f"Password store directory does not exist: {self.store_dir}")
        elif not os.path.isdir(self.store_dir):
            errors.append(f"Password store path is not a directory: {self.store_dir}")
        
        # Check GPG home
        if not os.path.exists(self.gpg_home):
            errors.append(f"GPG home directory does not exist: {self.gpg_home}")
        elif not os.path.isdir(self.gpg_home):
            errors.append(f"GPG home path is not a directory: {self.gpg_home}")
        
        # Check GPG availability
        gpg_helper = GPGSetupHelper(self.gpg_home)
        if not gpg_helper.is_available():
            errors.append("GPG is not available on the system")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "Environment is valid"
    
    def get_debug_info(self) -> Dict[str, str]:
        """
        Get debug information about the environment setup.
        
        Returns:
            Dictionary with debug information
        """
        env = self.get_environment()
        
        return {
            "store_dir": self.store_dir,
            "gpg_home": self.gpg_home,
            "store_dir_exists": str(os.path.exists(self.store_dir)),
            "gpg_home_exists": str(os.path.exists(self.gpg_home)),
            "PASSWORD_STORE_DIR": env.get("PASSWORD_STORE_DIR", "not set"),
            "GNUPGHOME": env.get("GNUPGHOME", "not set"),
            "GPG_TTY": env.get("GPG_TTY", "not set"),
            "is_flatpak": str("FLATPAK_ID" in os.environ),
        }


class PasswordStoreEnvironment(EnvironmentSetup):
    """Specialized environment setup for password store operations."""
    
    def __init__(self, store_dir: Optional[str] = None):
        """Initialize with store directory only."""
        super().__init__(store_dir=store_dir)
    
    def run_command(self, command: list[str], **kwargs) -> Dict[str, str]:
        """
        Get environment for running a command with proper password store setup.
        
        Args:
            command: Command to run (for context)
            **kwargs: Additional environment variables
            
        Returns:
            Environment dictionary for the command
        """
        env = self.get_environment()
        env.update(kwargs)
        return env


class GPGEnvironment(EnvironmentSetup):
    """Specialized environment setup for GPG operations."""
    
    def __init__(self, gpg_home: Optional[str] = None):
        """Initialize with GPG home directory only."""
        super().__init__(gpg_home=gpg_home)
    
    def get_signing_environment(self, key_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get environment for GPG signing operations.
        
        Args:
            key_id: Specific key ID to use for signing
            
        Returns:
            Environment dictionary for signing
        """
        env = self.get_gpg_environment()
        
        if key_id:
            env["GPG_KEY_ID"] = key_id
        
        return env