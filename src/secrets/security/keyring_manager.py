"""System keyring integration for secure credential storage."""

import json
import logging
import os
import subprocess
import sys
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .secure_memory import SecureString

logger = logging.getLogger(__name__)


@dataclass
class KeyringBackend:
    """Information about a keyring backend."""
    name: str
    available: bool
    priority: int
    description: str


class KeyringManager:
    """Manages secure storage of credentials using system keyring."""
    
    SERVICE_NAME = "io.github.tobagin.secrets"
    
    def __init__(self):
        """Initialize keyring manager."""
        self._backend = None
        self._available_backends = []
        self._detect_backends()
    
    def _detect_backends(self):
        """Detect available keyring backends."""
        backends = [
            self._check_secret_service(),
            self._check_gnome_keyring(),
            self._check_kde_kwallet(),
            self._check_macos_keychain(),
            self._check_windows_credential_manager(),
            self._check_python_keyring(),
        ]
        
        # Filter available backends and sort by priority
        self._available_backends = [b for b in backends if b.available]
        self._available_backends.sort(key=lambda x: x.priority)
        
        # Select best backend
        if self._available_backends:
            self._backend = self._available_backends[0]
            logger.info(f"Selected keyring backend: {self._backend.name}")
        else:
            logger.warning("No keyring backend available - will use encrypted file storage")
    
    def _check_secret_service(self) -> KeyringBackend:
        """Check for Secret Service API (Linux)."""
        try:
            # Check if secret-tool is available
            result = subprocess.run(
                ['secret-tool', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            available = False
        
        return KeyringBackend(
            name="secret_service",
            available=available,
            priority=1,
            description="Linux Secret Service API"
        )
    
    def _check_gnome_keyring(self) -> KeyringBackend:
        """Check for GNOME Keyring (Linux)."""
        try:
            # Check if running in GNOME environment
            gnome_env = any(
                'gnome' in os.environ.get(var, '').lower()
                for var in ['DESKTOP_SESSION', 'XDG_CURRENT_DESKTOP', 'GDMSESSION']
            )
            
            # Check if gnome-keyring-daemon is running
            result = subprocess.run(
                ['pgrep', 'gnome-keyring'],
                capture_output=True,
                timeout=5
            )
            daemon_running = result.returncode == 0
            
            available = gnome_env and daemon_running
        except (FileNotFoundError, subprocess.TimeoutExpired):
            available = False
        
        return KeyringBackend(
            name="gnome_keyring",
            available=available,
            priority=2,
            description="GNOME Keyring"
        )
    
    def _check_kde_kwallet(self) -> KeyringBackend:
        """Check for KDE KWallet (Linux)."""
        try:
            # Check if running in KDE environment
            kde_env = any(
                'kde' in os.environ.get(var, '').lower()
                for var in ['DESKTOP_SESSION', 'XDG_CURRENT_DESKTOP']
            )
            
            # Check if kwalletd is available
            result = subprocess.run(
                ['which', 'kwalletcli'],
                capture_output=True,
                timeout=5
            )
            cli_available = result.returncode == 0
            
            available = kde_env and cli_available
        except (FileNotFoundError, subprocess.TimeoutExpired):
            available = False
        
        return KeyringBackend(
            name="kde_kwallet",
            available=available,
            priority=3,
            description="KDE KWallet"
        )
    
    def _check_macos_keychain(self) -> KeyringBackend:
        """Check for macOS Keychain."""
        try:
            is_macos = sys.platform == 'darwin'
            
            if is_macos:
                # Check if security command is available
                result = subprocess.run(
                    ['security', 'list-keychains'],
                    capture_output=True,
                    timeout=5
                )
                available = result.returncode == 0
            else:
                available = False
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            available = False
        
        return KeyringBackend(
            name="macos_keychain",
            available=available,
            priority=1,
            description="macOS Keychain"
        )
    
    def _check_windows_credential_manager(self) -> KeyringBackend:
        """Check for Windows Credential Manager."""
        try:
            is_windows = sys.platform.startswith('win')
            
            if is_windows:
                # Try to import win32cred
                import win32cred
                available = True
            else:
                available = False
                
        except ImportError:
            available = False
        
        return KeyringBackend(
            name="windows_credential_manager",
            available=available,
            priority=1,
            description="Windows Credential Manager"
        )
    
    def _check_python_keyring(self) -> KeyringBackend:
        """Check for Python keyring library."""
        try:
            import keyring
            # Test if keyring is functional
            keyring.get_keyring()
            available = True
        except (ImportError, Exception):
            available = False
        
        return KeyringBackend(
            name="python_keyring",
            available=available,
            priority=5,
            description="Python keyring library"
        )
    
    def is_available(self) -> bool:
        """Check if keyring storage is available."""
        return self._backend is not None
    
    def get_backend_info(self) -> Optional[KeyringBackend]:
        """Get information about the selected backend."""
        return self._backend
    
    def store_credential(self, key: str, credential: str) -> bool:
        """
        Store a credential in the keyring.
        
        Args:
            key: Unique key for the credential
            credential: Credential to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self._backend:
            return False
        
        try:
            if self._backend.name == "secret_service":
                return self._store_secret_service(key, credential)
            elif self._backend.name == "gnome_keyring":
                return self._store_gnome_keyring(key, credential)
            elif self._backend.name == "kde_kwallet":
                return self._store_kde_kwallet(key, credential)
            elif self._backend.name == "macos_keychain":
                return self._store_macos_keychain(key, credential)
            elif self._backend.name == "windows_credential_manager":
                return self._store_windows_credential_manager(key, credential)
            elif self._backend.name == "python_keyring":
                return self._store_python_keyring(key, credential)
            
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            return False
        
        return False
    
    def retrieve_credential(self, key: str) -> Optional[SecureString]:
        """
        Retrieve a credential from the keyring.
        
        Args:
            key: Unique key for the credential
            
        Returns:
            SecureString containing the credential, or None if not found
        """
        if not self._backend:
            return None
        
        try:
            if self._backend.name == "secret_service":
                credential = self._retrieve_secret_service(key)
            elif self._backend.name == "gnome_keyring":
                credential = self._retrieve_gnome_keyring(key)
            elif self._backend.name == "kde_kwallet":
                credential = self._retrieve_kde_kwallet(key)
            elif self._backend.name == "macos_keychain":
                credential = self._retrieve_macos_keychain(key)
            elif self._backend.name == "windows_credential_manager":
                credential = self._retrieve_windows_credential_manager(key)
            elif self._backend.name == "python_keyring":
                credential = self._retrieve_python_keyring(key)
            else:
                credential = None
            
            if credential:
                return SecureString(credential)
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential: {e}")
        
        return None
    
    def delete_credential(self, key: str) -> bool:
        """
        Delete a credential from the keyring.
        
        Args:
            key: Unique key for the credential
            
        Returns:
            True if successful, False otherwise
        """
        if not self._backend:
            return False
        
        try:
            if self._backend.name == "secret_service":
                return self._delete_secret_service(key)
            elif self._backend.name == "gnome_keyring":
                return self._delete_gnome_keyring(key)
            elif self._backend.name == "kde_kwallet":
                return self._delete_kde_kwallet(key)
            elif self._backend.name == "macos_keychain":
                return self._delete_macos_keychain(key)
            elif self._backend.name == "windows_credential_manager":
                return self._delete_windows_credential_manager(key)
            elif self._backend.name == "python_keyring":
                return self._delete_python_keyring(key)
            
        except Exception as e:
            logger.error(f"Failed to delete credential: {e}")
            return False
        
        return False
    
    # Backend-specific implementations
    
    def _store_secret_service(self, key: str, credential: str) -> bool:
        """Store credential using Secret Service API."""
        try:
            result = subprocess.run([
                'secret-tool', 'store',
                '--label', f'Secrets App: {key}',
                'application', self.SERVICE_NAME,
                'key', key
            ], input=credential, text=True, timeout=10)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    def _retrieve_secret_service(self, key: str) -> Optional[str]:
        """Retrieve credential using Secret Service API."""
        try:
            result = subprocess.run([
                'secret-tool', 'lookup',
                'application', self.SERVICE_NAME,
                'key', key
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            pass
        return None
    
    def _delete_secret_service(self, key: str) -> bool:
        """Delete credential using Secret Service API."""
        try:
            result = subprocess.run([
                'secret-tool', 'clear',
                'application', self.SERVICE_NAME,
                'key', key
            ], timeout=10)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    def _store_gnome_keyring(self, key: str, credential: str) -> bool:
        """Store credential using GNOME Keyring."""
        # This would require python-gnomekeyring or similar
        # For now, fallback to secret-service
        return self._store_secret_service(key, credential)
    
    def _retrieve_gnome_keyring(self, key: str) -> Optional[str]:
        """Retrieve credential using GNOME Keyring."""
        return self._retrieve_secret_service(key)
    
    def _delete_gnome_keyring(self, key: str) -> bool:
        """Delete credential using GNOME Keyring."""
        return self._delete_secret_service(key)
    
    def _store_kde_kwallet(self, key: str, credential: str) -> bool:
        """Store credential using KDE KWallet."""
        try:
            result = subprocess.run([
                'kwalletcli', '-e', key
            ], input=credential, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _retrieve_kde_kwallet(self, key: str) -> Optional[str]:
        """Retrieve credential using KDE KWallet."""
        try:
            result = subprocess.run([
                'kwalletcli', '-q', key
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    def _delete_kde_kwallet(self, key: str) -> bool:
        """Delete credential using KDE KWallet."""
        try:
            result = subprocess.run([
                'kwalletcli', '-d', key
            ], timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _store_macos_keychain(self, key: str, credential: str) -> bool:
        """Store credential using macOS Keychain."""
        try:
            result = subprocess.run([
                'security', 'add-generic-password',
                '-s', self.SERVICE_NAME,
                '-a', key,
                '-w', credential,
                '-U'  # Update if exists
            ], timeout=10)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    def _retrieve_macos_keychain(self, key: str) -> Optional[str]:
        """Retrieve credential using macOS Keychain."""
        try:
            result = subprocess.run([
                'security', 'find-generic-password',
                '-s', self.SERVICE_NAME,
                '-a', key,
                '-w'  # Show password
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            pass
        return None
    
    def _delete_macos_keychain(self, key: str) -> bool:
        """Delete credential using macOS Keychain."""
        try:
            result = subprocess.run([
                'security', 'delete-generic-password',
                '-s', self.SERVICE_NAME,
                '-a', key
            ], timeout=10)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    def _store_windows_credential_manager(self, key: str, credential: str) -> bool:
        """Store credential using Windows Credential Manager."""
        try:
            import win32cred
            target = f"{self.SERVICE_NAME}:{key}"
            
            win32cred.CredWrite({
                'Type': win32cred.CRED_TYPE_GENERIC,
                'TargetName': target,
                'UserName': key,
                'CredentialBlob': credential,
                'Persist': win32cred.CRED_PERSIST_LOCAL_MACHINE
            })
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.error(f"Windows credential storage failed: {e}")
            return False
    
    def _retrieve_windows_credential_manager(self, key: str) -> Optional[str]:
        """Retrieve credential using Windows Credential Manager."""
        try:
            import win32cred
            target = f"{self.SERVICE_NAME}:{key}"
            
            cred = win32cred.CredRead(target, win32cred.CRED_TYPE_GENERIC)
            return cred['CredentialBlob'].decode('utf-8')
        except ImportError:
            return None
        except Exception:
            return None
    
    def _delete_windows_credential_manager(self, key: str) -> bool:
        """Delete credential using Windows Credential Manager."""
        try:
            import win32cred
            target = f"{self.SERVICE_NAME}:{key}"
            
            win32cred.CredDelete(target, win32cred.CRED_TYPE_GENERIC)
            return True
        except ImportError:
            return False
        except Exception:
            return False
    
    def _store_python_keyring(self, key: str, credential: str) -> bool:
        """Store credential using Python keyring library."""
        try:
            import keyring
            keyring.set_password(self.SERVICE_NAME, key, credential)
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.error(f"Python keyring storage failed: {e}")
            return False
    
    def _retrieve_python_keyring(self, key: str) -> Optional[str]:
        """Retrieve credential using Python keyring library."""
        try:
            import keyring
            return keyring.get_password(self.SERVICE_NAME, key)
        except ImportError:
            return None
        except Exception:
            return None
    
    def _delete_python_keyring(self, key: str) -> bool:
        """Delete credential using Python keyring library."""
        try:
            import keyring
            keyring.delete_password(self.SERVICE_NAME, key)
            return True
        except ImportError:
            return False
        except Exception:
            return False
    
    def list_available_backends(self) -> list[KeyringBackend]:
        """Get list of all available backends."""
        return self._available_backends.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get keyring manager statistics."""
        return {
            'backend': self._backend.name if self._backend else None,
            'available_backends': len(self._available_backends),
            'backends': [
                {
                    'name': b.name,
                    'description': b.description,
                    'priority': b.priority
                }
                for b in self._available_backends
            ]
        }