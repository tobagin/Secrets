"""Encrypted configuration storage for sensitive settings."""

import json
import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from .secure_memory import SecureString
from .keyring_manager import KeyringManager

logger = logging.getLogger(__name__)


@dataclass
class EncryptionInfo:
    """Information about encryption parameters."""
    version: int = 1
    algorithm: str = "Fernet"
    kdf: str = "PBKDF2"
    iterations: int = 100000
    salt_length: int = 32


class EncryptedConfigManager:
    """Manages encrypted configuration files for sensitive settings."""
    
    MASTER_KEY_NAME = "config_master_key"
    CONFIG_FILE_EXTENSION = ".enc.json"
    
    def __init__(self, config_dir: Union[str, Path]):
        """
        Initialize encrypted config manager.
        
        Args:
            config_dir: Directory to store encrypted config files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.keyring = KeyringManager()
        self._master_key: Optional[SecureString] = None
        self._encryption_info = EncryptionInfo()
    
    def _get_master_key(self) -> Optional[bytes]:
        """Get or create the master encryption key."""
        if self._master_key is None:
            # Try to get from keyring first
            if self.keyring.is_available():
                stored_key = self.keyring.retrieve_credential(self.MASTER_KEY_NAME)
                if stored_key:
                    self._master_key = stored_key
                    logger.debug("Retrieved master key from keyring")
            
            # If not found, generate a new one
            if self._master_key is None:
                key_bytes = Fernet.generate_key()
                self._master_key = SecureString(key_bytes.decode('ascii'))
                
                # Store in keyring if available
                if self.keyring.is_available():
                    success = self.keyring.store_credential(
                        self.MASTER_KEY_NAME, 
                        self._master_key.get()
                    )
                    if success:
                        logger.info("Stored new master key in keyring")
                    else:
                        logger.warning("Failed to store master key in keyring")
                else:
                    logger.warning("No keyring available - master key will not persist")
        
        if self._master_key:
            return self._master_key.get().encode('ascii')
        return None
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password and salt.
        
        Args:
            password: Password string
            salt: Salt bytes
            
        Returns:
            Derived key bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self._encryption_info.iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _encrypt_data(self, data: str, key: bytes) -> Dict[str, Any]:
        """
        Encrypt data with the given key.
        
        Args:
            data: Data to encrypt
            key: Encryption key
            
        Returns:
            Dictionary with encrypted data and metadata
        """
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode('utf-8'))
        
        return {
            'data': base64.b64encode(encrypted_data).decode('ascii'),
            'encryption_info': asdict(self._encryption_info)
        }
    
    def _decrypt_data(self, encrypted_dict: Dict[str, Any], key: bytes) -> str:
        """
        Decrypt data with the given key.
        
        Args:
            encrypted_dict: Dictionary with encrypted data
            key: Decryption key
            
        Returns:
            Decrypted data string
        """
        encrypted_data = base64.b64decode(encrypted_dict['data'])
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    
    def store_config(self, config_name: str, config_data: Dict[str, Any], 
                    use_master_key: bool = True) -> bool:
        """
        Store configuration data encrypted.
        
        Args:
            config_name: Name of the configuration
            config_data: Configuration data to store
            use_master_key: Whether to use master key or prompt for password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize config data
            json_data = json.dumps(config_data, indent=2)
            
            if use_master_key:
                key = self._get_master_key()
                if not key:
                    logger.error("No master key available")
                    return False
            else:
                # This would prompt for password in a real implementation
                # For now, use master key as fallback
                key = self._get_master_key()
                if not key:
                    return False
            
            # Encrypt data
            encrypted_dict = self._encrypt_data(json_data, key)
            
            # Save to file
            config_file = self.config_dir / f"{config_name}{self.CONFIG_FILE_EXTENSION}"
            with open(config_file, 'w') as f:
                json.dump(encrypted_dict, f, indent=2)
            
            # Set secure permissions
            os.chmod(config_file, 0o600)
            
            logger.info(f"Stored encrypted config: {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store encrypted config {config_name}: {e}")
            return False
    
    def load_config(self, config_name: str, use_master_key: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load configuration data from encrypted storage.
        
        Args:
            config_name: Name of the configuration
            use_master_key: Whether to use master key or prompt for password
            
        Returns:
            Configuration data or None if not found/failed
        """
        try:
            config_file = self.config_dir / f"{config_name}{self.CONFIG_FILE_EXTENSION}"
            
            if not config_file.exists():
                logger.debug(f"Encrypted config file not found: {config_name}")
                return None
            
            # Load encrypted data
            with open(config_file, 'r') as f:
                encrypted_dict = json.load(f)
            
            if use_master_key:
                key = self._get_master_key()
                if not key:
                    logger.error("No master key available")
                    return None
            else:
                # This would prompt for password in a real implementation
                key = self._get_master_key()
                if not key:
                    return None
            
            # Decrypt data
            json_data = self._decrypt_data(encrypted_dict, key)
            config_data = json.loads(json_data)
            
            logger.debug(f"Loaded encrypted config: {config_name}")
            return config_data
            
        except Exception as e:
            logger.error(f"Failed to load encrypted config {config_name}: {e}")
            return None
    
    def delete_config(self, config_name: str) -> bool:
        """
        Delete an encrypted configuration file.
        
        Args:
            config_name: Name of the configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_file = self.config_dir / f"{config_name}{self.CONFIG_FILE_EXTENSION}"
            
            if config_file.exists():
                # Securely overwrite file before deletion
                self._secure_delete_file(config_file)
                logger.info(f"Deleted encrypted config: {config_name}")
                return True
            else:
                logger.warning(f"Config file not found for deletion: {config_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete encrypted config {config_name}: {e}")
            return False
    
    def _secure_delete_file(self, file_path: Path):
        """
        Securely delete a file by overwriting it multiple times.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            # Get file size
            file_size = file_path.stat().st_size
            
            # Overwrite with random data multiple times
            patterns = [b'\x00', b'\xff', b'\xaa', b'\x55']
            
            with open(file_path, 'r+b') as f:
                for pattern in patterns:
                    f.seek(0)
                    f.write(pattern * file_size)
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            file_path.unlink()
            
        except Exception as e:
            logger.warning(f"Secure file deletion failed: {e}")
            # Fallback to regular deletion
            try:
                file_path.unlink()
            except:
                pass
    
    def list_configs(self) -> list[str]:
        """
        List all available encrypted configuration files.
        
        Returns:
            List of configuration names
        """
        try:
            config_files = self.config_dir.glob(f"*{self.CONFIG_FILE_EXTENSION}")
            return [
                f.stem.replace('.enc', '') 
                for f in config_files
            ]
        except Exception as e:
            logger.error(f"Failed to list configs: {e}")
            return []
    
    def config_exists(self, config_name: str) -> bool:
        """
        Check if a configuration exists.
        
        Args:
            config_name: Name of the configuration
            
        Returns:
            True if exists, False otherwise
        """
        config_file = self.config_dir / f"{config_name}{self.CONFIG_FILE_EXTENSION}"
        return config_file.exists()
    
    def change_master_key(self, old_password: Optional[str] = None, 
                         new_password: Optional[str] = None) -> bool:
        """
        Change the master encryption key and re-encrypt all configs.
        
        Args:
            old_password: Old password (if not using keyring)
            new_password: New password (if not using keyring)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load all existing configs with old key
            config_names = self.list_configs()
            configs_data = {}
            
            for config_name in config_names:
                config_data = self.load_config(config_name, use_master_key=True)
                if config_data is not None:
                    configs_data[config_name] = config_data
                else:
                    logger.error(f"Failed to load config {config_name} with old key")
                    return False
            
            # Generate new master key
            old_key = self._master_key
            self._master_key = None  # Force generation of new key
            
            # Delete old key from keyring
            if self.keyring.is_available():
                self.keyring.delete_credential(self.MASTER_KEY_NAME)
            
            # Get new master key
            new_key = self._get_master_key()
            if not new_key:
                # Restore old key if new key generation failed
                self._master_key = old_key
                return False
            
            # Re-encrypt all configs with new key
            for config_name, config_data in configs_data.items():
                if not self.store_config(config_name, config_data, use_master_key=True):
                    logger.error(f"Failed to re-encrypt config {config_name}")
                    return False
            
            # Clean up old key
            if old_key:
                old_key.wipe()
            
            logger.info("Successfully changed master key and re-encrypted all configs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change master key: {e}")
            return False
    
    def export_configs(self, export_file: str, include_sensitive: bool = False) -> bool:
        """
        Export configurations to a file.
        
        Args:
            export_file: Path to export file
            include_sensitive: Whether to include sensitive data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_names = self.list_configs()
            export_data = {
                'configs': {},
                'metadata': {
                    'version': 1,
                    'include_sensitive': include_sensitive,
                    'encryption_info': asdict(self._encryption_info)
                }
            }
            
            for config_name in config_names:
                config_data = self.load_config(config_name)
                if config_data is not None:
                    if not include_sensitive:
                        # Filter out sensitive fields
                        config_data = self._filter_sensitive_data(config_data)
                    export_data['configs'][config_name] = config_data
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(config_names)} configs to {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configs: {e}")
            return False
    
    def _filter_sensitive_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out sensitive data from config."""
        filtered = config_data.copy()
        
        # Common sensitive field names to filter
        sensitive_keys = {
            'password', 'token', 'key', 'secret', 'credential',
            'api_key', 'auth_token', 'access_token', 'private_key'
        }
        
        def filter_dict(d):
            if isinstance(d, dict):
                return {
                    k: filter_dict(v) if k.lower() not in sensitive_keys else "[FILTERED]"
                    for k, v in d.items()
                }
            elif isinstance(d, list):
                return [filter_dict(item) for item in d]
            else:
                return d
        
        return filter_dict(filtered)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get encrypted config manager statistics."""
        return {
            'config_dir': str(self.config_dir),
            'config_count': len(self.list_configs()),
            'keyring_available': self.keyring.is_available(),
            'keyring_backend': self.keyring.get_backend_info().name if self.keyring.get_backend_info() else None,
            'master_key_in_keyring': self.keyring.is_available() and 
                                   self.keyring.retrieve_credential(self.MASTER_KEY_NAME) is not None
        }