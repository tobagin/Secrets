"""Two-factor authentication system for application unlock."""

import base64
import hashlib
import hmac
import logging
import os
import qrcode
import struct
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import io

from .secure_memory import SecureString
from .encrypted_config import EncryptedConfigManager
from .hardware_keys import HardwareKeyManager, HardwareKeyAuth

logger = logging.getLogger(__name__)


class TwoFactorMethod(Enum):
    """Two-factor authentication methods."""
    TOTP = "totp"  # Time-based OTP
    HARDWARE_KEY = "hardware_key"
    BACKUP_CODES = "backup_codes"


@dataclass
class TwoFactorConfig:
    """Configuration for two-factor authentication."""
    enabled: bool = False
    methods: List[TwoFactorMethod] = None
    totp_secret: Optional[str] = None
    backup_codes: List[str] = None
    hardware_key_ids: List[str] = None
    require_multiple: bool = False
    
    def __post_init__(self):
        if self.methods is None:
            self.methods = []
        if self.backup_codes is None:
            self.backup_codes = []
        if self.hardware_key_ids is None:
            self.hardware_key_ids = []


class TOTPGenerator:
    """Time-based One-Time Password generator."""
    
    def __init__(self, secret: str, digits: int = 6, period: int = 30):
        """
        Initialize TOTP generator.
        
        Args:
            secret: Base32-encoded secret key
            digits: Number of digits in the OTP
            period: Time period in seconds
        """
        self.secret = secret
        self.digits = digits
        self.period = period
    
    def generate_otp(self, timestamp: Optional[int] = None) -> str:
        """
        Generate a TOTP code.
        
        Args:
            timestamp: Unix timestamp (uses current time if None)
            
        Returns:
            OTP code as string
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Calculate time counter
        counter = timestamp // self.period
        
        # Decode secret
        try:
            secret_bytes = base64.b32decode(self.secret.upper())
        except Exception as e:
            logger.error(f"Failed to decode TOTP secret: {e}")
            return "000000"
        
        # Generate HMAC
        counter_bytes = struct.pack(">Q", counter)
        hmac_digest = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation
        offset = hmac_digest[-1] & 0x0f
        truncated = struct.unpack(">I", hmac_digest[offset:offset + 4])[0]
        truncated &= 0x7fffffff
        
        # Generate OTP
        otp = truncated % (10 ** self.digits)
        return str(otp).zfill(self.digits)
    
    def verify_otp(self, token: str, timestamp: Optional[int] = None, 
                   window: int = 1) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            token: OTP token to verify
            timestamp: Unix timestamp (uses current time if None)
            window: Number of time periods to check (allows for clock drift)
            
        Returns:
            True if token is valid
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Check current time and nearby periods
        for i in range(-window, window + 1):
            check_time = timestamp + (i * self.period)
            expected = self.generate_otp(check_time)
            if self._constant_time_compare(token, expected):
                return True
        
        return False
    
    def _constant_time_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    @staticmethod
    def generate_secret() -> str:
        """Generate a new random secret key."""
        secret_bytes = os.urandom(20)  # 160 bits
        return base64.b32encode(secret_bytes).decode('ascii')
    
    def get_provisioning_uri(self, name: str, issuer: str = "Secrets") -> str:
        """
        Get provisioning URI for QR code generation.
        
        Args:
            name: Account name
            issuer: Issuer name
            
        Returns:
            otpauth:// URI
        """
        return (
            f"otpauth://totp/{issuer}:{name}?"
            f"secret={self.secret}&"
            f"issuer={issuer}&"
            f"digits={self.digits}&"
            f"period={self.period}"
        )
    
    def generate_qr_code(self, name: str, issuer: str = "Secrets") -> bytes:
        """
        Generate QR code for TOTP setup.
        
        Args:
            name: Account name
            issuer: Issuer name
            
        Returns:
            PNG image data
        """
        uri = self.get_provisioning_uri(name, issuer)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to PNG bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        return img_buffer.getvalue()


class BackupCodeGenerator:
    """Generator for backup authentication codes."""
    
    @staticmethod
    def generate_codes(count: int = 8, length: int = 8) -> List[str]:
        """
        Generate backup codes.
        
        Args:
            count: Number of codes to generate
            length: Length of each code
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate random code
            code_bytes = os.urandom(length // 2)
            code = code_bytes.hex().upper()
            # Format with dashes for readability
            formatted = '-'.join(code[i:i+4] for i in range(0, len(code), 4))
            codes.append(formatted)
        
        return codes
    
    @staticmethod
    def hash_code(code: str) -> str:
        """
        Hash a backup code for secure storage.
        
        Args:
            code: Backup code to hash
            
        Returns:
            Hashed code
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def verify_code(code: str, hashed_codes: List[str]) -> bool:
        """
        Verify a backup code against stored hashes.
        
        Args:
            code: Code to verify
            hashed_codes: List of hashed codes
            
        Returns:
            True if code is valid
        """
        code_hash = BackupCodeGenerator.hash_code(code)
        return code_hash in hashed_codes


class TwoFactorAuthManager:
    """Manages two-factor authentication for the application."""
    
    CONFIG_NAME = "two_factor_auth"
    
    def __init__(self, config_manager: EncryptedConfigManager):
        """
        Initialize 2FA manager.
        
        Args:
            config_manager: Encrypted configuration manager
        """
        self.config_manager = config_manager
        self.hardware_key_manager = HardwareKeyManager()
        self.hardware_key_auth = HardwareKeyAuth(self.hardware_key_manager)
        self._config: Optional[TwoFactorConfig] = None
        self._load_config()
    
    def _load_config(self):
        """Load 2FA configuration."""
        config_data = self.config_manager.load_config(self.CONFIG_NAME)
        if config_data:
            self._config = TwoFactorConfig(**config_data)
        else:
            self._config = TwoFactorConfig()
    
    def _save_config(self) -> bool:
        """Save 2FA configuration."""
        if self._config:
            config_data = {
                'enabled': self._config.enabled,
                'methods': [m.value for m in self._config.methods],
                'totp_secret': self._config.totp_secret,
                'backup_codes': self._config.backup_codes,
                'hardware_key_ids': self._config.hardware_key_ids,
                'require_multiple': self._config.require_multiple
            }
            return self.config_manager.store_config(self.CONFIG_NAME, config_data)
        return False
    
    def is_enabled(self) -> bool:
        """Check if 2FA is enabled."""
        return self._config.enabled if self._config else False
    
    def get_enabled_methods(self) -> List[TwoFactorMethod]:
        """Get list of enabled 2FA methods."""
        return self._config.methods.copy() if self._config else []
    
    def setup_totp(self, name: str) -> Tuple[bool, Optional[str], Optional[bytes]]:
        """
        Set up TOTP authentication.
        
        Args:
            name: Account name for TOTP
            
        Returns:
            (success, secret, qr_code_png)
        """
        try:
            # Generate new secret
            secret = TOTPGenerator.generate_secret()
            totp = TOTPGenerator(secret)
            
            # Generate QR code
            qr_code = totp.generate_qr_code(name)
            
            # Store secret (will be saved when 2FA is enabled)
            if not self._config:
                self._config = TwoFactorConfig()
            
            self._config.totp_secret = secret
            
            logger.info("TOTP setup completed")
            return True, secret, qr_code
            
        except Exception as e:
            logger.error(f"TOTP setup failed: {e}")
            return False, None, None
    
    def setup_hardware_keys(self) -> Tuple[bool, List[str]]:
        """
        Set up hardware key authentication.
        
        Returns:
            (success, list_of_registered_key_ids)
        """
        try:
            # Detect available keys
            detected_keys = self.hardware_key_manager.detect_keys()
            
            if not detected_keys:
                logger.warning("No hardware keys detected")
                return False, []
            
            registered_ids = []
            
            # Register each detected key
            for i, key in enumerate(detected_keys):
                key_id = f"hw_key_{i}_{key.serial or 'unknown'}"
                if self.hardware_key_auth.register_key(key, key_id):
                    registered_ids.append(key_id)
            
            # Store registered key IDs
            if not self._config:
                self._config = TwoFactorConfig()
            
            self._config.hardware_key_ids = registered_ids
            
            logger.info(f"Hardware key setup completed: {len(registered_ids)} keys registered")
            return True, registered_ids
            
        except Exception as e:
            logger.error(f"Hardware key setup failed: {e}")
            return False, []
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for recovery.
        
        Returns:
            List of backup codes (unhashed)
        """
        codes = BackupCodeGenerator.generate_codes()
        
        # Store hashed versions
        if not self._config:
            self._config = TwoFactorConfig()
        
        hashed_codes = [BackupCodeGenerator.hash_code(code) for code in codes]
        self._config.backup_codes = hashed_codes
        
        logger.info(f"Generated {len(codes)} backup codes")
        return codes
    
    def enable_two_factor(self, methods: List[TwoFactorMethod], 
                         require_multiple: bool = False) -> bool:
        """
        Enable two-factor authentication.
        
        Args:
            methods: List of methods to enable
            require_multiple: Whether multiple methods are required
            
        Returns:
            True if successful
        """
        if not self._config:
            logger.error("2FA not configured")
            return False
        
        # Validate that required methods are set up
        for method in methods:
            if method == TwoFactorMethod.TOTP and not self._config.totp_secret:
                logger.error("TOTP not configured")
                return False
            elif method == TwoFactorMethod.HARDWARE_KEY and not self._config.hardware_key_ids:
                logger.error("Hardware keys not configured")
                return False
        
        self._config.enabled = True
        self._config.methods = methods
        self._config.require_multiple = require_multiple
        
        # Generate backup codes if not already done
        if TwoFactorMethod.BACKUP_CODES not in methods and not self._config.backup_codes:
            self.generate_backup_codes()
            methods.append(TwoFactorMethod.BACKUP_CODES)
            self._config.methods = methods
        
        success = self._save_config()
        if success:
            logger.info(f"2FA enabled with methods: {[m.value for m in methods]}")
        
        return success
    
    def disable_two_factor(self) -> bool:
        """
        Disable two-factor authentication.
        
        Returns:
            True if successful
        """
        if not self._config:
            return True
        
        self._config.enabled = False
        self._config.methods = []
        
        success = self._save_config()
        if success:
            logger.info("2FA disabled")
        
        return success
    
    def authenticate(self, token: str, method: Optional[TwoFactorMethod] = None) -> bool:
        """
        Authenticate using a 2FA token.
        
        Args:
            token: Authentication token
            method: Specific method to use (auto-detect if None)
            
        Returns:
            True if authentication successful
        """
        if not self.is_enabled():
            logger.warning("2FA not enabled")
            return False
        
        # Try each enabled method if not specified
        methods_to_try = [method] if method else self._config.methods
        
        for auth_method in methods_to_try:
            if auth_method == TwoFactorMethod.TOTP:
                if self._authenticate_totp(token):
                    return True
            elif auth_method == TwoFactorMethod.BACKUP_CODES:
                if self._authenticate_backup_code(token):
                    return True
            elif auth_method == TwoFactorMethod.HARDWARE_KEY:
                if self._authenticate_hardware_key(token):
                    return True
        
        logger.warning("2FA authentication failed")
        return False
    
    def _authenticate_totp(self, token: str) -> bool:
        """Authenticate using TOTP."""
        if not self._config.totp_secret:
            return False
        
        try:
            totp = TOTPGenerator(self._config.totp_secret)
            return totp.verify_otp(token)
        except Exception as e:
            logger.error(f"TOTP authentication error: {e}")
            return False
    
    def _authenticate_backup_code(self, code: str) -> bool:
        """Authenticate using backup code."""
        if not self._config.backup_codes:
            return False
        
        try:
            if BackupCodeGenerator.verify_code(code, self._config.backup_codes):
                # Remove used code
                code_hash = BackupCodeGenerator.hash_code(code)
                self._config.backup_codes.remove(code_hash)
                self._save_config()
                logger.info("Backup code used for authentication")
                return True
        except Exception as e:
            logger.error(f"Backup code authentication error: {e}")
        
        return False
    
    def _authenticate_hardware_key(self, challenge_response: str) -> bool:
        """Authenticate using hardware key."""
        if not self._config.hardware_key_ids:
            return False
        
        try:
            # For simplicity, we'll just check if any registered key is present
            # In a real implementation, you'd verify the challenge response
            for key_id in self._config.hardware_key_ids:
                registered_keys = self.hardware_key_auth.get_registered_keys()
                if key_id in registered_keys:
                    key = registered_keys[key_id]
                    if self.hardware_key_manager.test_key_presence(key):
                        logger.info(f"Hardware key authentication successful: {key_id}")
                        return True
        except Exception as e:
            logger.error(f"Hardware key authentication error: {e}")
        
        return False
    
    def get_backup_codes_count(self) -> int:
        """Get number of remaining backup codes."""
        return len(self._config.backup_codes) if self._config else 0
    
    def regenerate_backup_codes(self) -> List[str]:
        """
        Regenerate backup codes.
        
        Returns:
            New backup codes (unhashed)
        """
        codes = self.generate_backup_codes()
        self._save_config()
        return codes
    
    def get_totp_qr_code(self, name: str) -> Optional[bytes]:
        """
        Get QR code for current TOTP setup.
        
        Args:
            name: Account name
            
        Returns:
            QR code PNG data or None
        """
        if not self._config or not self._config.totp_secret:
            return None
        
        try:
            totp = TOTPGenerator(self._config.totp_secret)
            return totp.generate_qr_code(name)
        except Exception as e:
            logger.error(f"QR code generation failed: {e}")
            return None
    
    def get_hardware_keys_status(self) -> Dict[str, bool]:
        """
        Get status of registered hardware keys.
        
        Returns:
            Dictionary mapping key IDs to presence status
        """
        status = {}
        
        if self._config and self._config.hardware_key_ids:
            registered_keys = self.hardware_key_auth.get_registered_keys()
            for key_id in self._config.hardware_key_ids:
                if key_id in registered_keys:
                    key = registered_keys[key_id]
                    status[key_id] = self.hardware_key_manager.test_key_presence(key)
                else:
                    status[key_id] = False
        
        return status
    
    def get_stats(self) -> Dict[str, Any]:
        """Get 2FA statistics."""
        return {
            'enabled': self.is_enabled(),
            'methods': [m.value for m in self.get_enabled_methods()],
            'totp_configured': bool(self._config and self._config.totp_secret),
            'hardware_keys_count': len(self._config.hardware_key_ids) if self._config else 0,
            'backup_codes_remaining': self.get_backup_codes_count(),
            'require_multiple': self._config.require_multiple if self._config else False
        }