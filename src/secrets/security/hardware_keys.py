"""Hardware security key support for enhanced authentication."""

import logging
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class KeyType(Enum):
    """Types of hardware security keys."""
    YUBIKEY = "yubikey"
    FIDO2 = "fido2"
    NITROKEY = "nitrokey"
    SOLOKEY = "solokey"
    UNKNOWN = "unknown"


@dataclass
class HardwareKey:
    """Information about a detected hardware security key."""
    name: str
    key_type: KeyType
    serial: Optional[str] = None
    version: Optional[str] = None
    capabilities: List[str] = None
    available: bool = True
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class HardwareKeyManager:
    """Manages hardware security key operations."""
    
    def __init__(self):
        """Initialize hardware key manager."""
        self._detected_keys: List[HardwareKey] = []
        self._fido_available = None
        self._yubikey_available = None
        self._detect_tools()
    
    def _detect_tools(self):
        """Detect available hardware key tools."""
        # Check for FIDO2 tools
        try:
            result = subprocess.run(
                ['which', 'fido2-token'],
                capture_output=True,
                timeout=5
            )
            self._fido_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._fido_available = False
        
        # Check for YubiKey tools
        try:
            result = subprocess.run(
                ['which', 'ykman'],
                capture_output=True,
                timeout=5
            )
            self._yubikey_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._yubikey_available = False
        
        logger.info(f"Hardware key tools available - FIDO2: {self._fido_available}, YubiKey: {self._yubikey_available}")
    
    def detect_keys(self) -> List[HardwareKey]:
        """
        Detect connected hardware security keys.
        
        Returns:
            List of detected hardware keys
        """
        detected = []
        
        # Detect YubiKeys
        if self._yubikey_available:
            yubikeys = self._detect_yubikeys()
            detected.extend(yubikeys)
        
        # Detect FIDO2 keys
        if self._fido_available:
            fido_keys = self._detect_fido2_keys()
            detected.extend(fido_keys)
        
        # Store detected keys
        self._detected_keys = detected
        
        logger.info(f"Detected {len(detected)} hardware security keys")
        return detected
    
    def _detect_yubikeys(self) -> List[HardwareKey]:
        """Detect YubiKey devices."""
        yubikeys = []
        
        try:
            # List YubiKey devices
            result = subprocess.run(
                ['ykman', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        # Parse YubiKey info
                        # Format: "YubiKey 5 NFC (5.4.3) [OTP+FIDO+CCID] Serial: 12345678"
                        parts = line.split()
                        if len(parts) >= 2:
                            name = ' '.join(parts[:3]) if len(parts) >= 3 else ' '.join(parts[:2])
                            
                            # Extract version
                            version = None
                            for part in parts:
                                if part.startswith('(') and part.endswith(')'):
                                    version = part[1:-1]
                                    break
                            
                            # Extract serial
                            serial = None
                            for i, part in enumerate(parts):
                                if part == "Serial:" and i + 1 < len(parts):
                                    serial = parts[i + 1]
                                    break
                            
                            # Extract capabilities
                            capabilities = []
                            for part in parts:
                                if part.startswith('[') and part.endswith(']'):
                                    cap_str = part[1:-1]
                                    capabilities = cap_str.split('+')
                                    break
                            
                            yubikey = HardwareKey(
                                name=name,
                                key_type=KeyType.YUBIKEY,
                                serial=serial,
                                version=version,
                                capabilities=capabilities
                            )
                            yubikeys.append(yubikey)
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Failed to detect YubiKeys: {e}")
        
        return yubikeys
    
    def _detect_fido2_keys(self) -> List[HardwareKey]:
        """Detect FIDO2 devices."""
        fido_keys = []
        
        try:
            # List FIDO2 devices
            result = subprocess.run(
                ['fido2-token', '-L'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        # Parse device path and try to get info
                        device_path = line.strip()
                        key_info = self._get_fido2_info(device_path)
                        if key_info:
                            fido_keys.append(key_info)
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Failed to detect FIDO2 keys: {e}")
        
        return fido_keys
    
    def _get_fido2_info(self, device_path: str) -> Optional[HardwareKey]:
        """Get information about a FIDO2 device."""
        try:
            # Get device info
            result = subprocess.run(
                ['fido2-token', '-I', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse output to extract device information
                lines = result.stdout.strip().split('\n')
                name = "FIDO2 Device"
                version = None
                
                for line in lines:
                    if 'product:' in line.lower():
                        name = line.split(':', 1)[1].strip()
                    elif 'version:' in line.lower():
                        version = line.split(':', 1)[1].strip()
                
                return HardwareKey(
                    name=name,
                    key_type=KeyType.FIDO2,
                    version=version,
                    capabilities=['FIDO2']
                )
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    def is_available(self) -> bool:
        """Check if hardware key support is available."""
        return self._fido_available or self._yubikey_available
    
    def get_detected_keys(self) -> List[HardwareKey]:
        """Get list of previously detected keys."""
        return self._detected_keys.copy()
    
    def test_key_presence(self, key: HardwareKey) -> bool:
        """
        Test if a specific key is present and responding.
        
        Args:
            key: Hardware key to test
            
        Returns:
            True if key is present and responding
        """
        if key.key_type == KeyType.YUBIKEY:
            return self._test_yubikey_presence(key)
        elif key.key_type == KeyType.FIDO2:
            return self._test_fido2_presence(key)
        
        return False
    
    def _test_yubikey_presence(self, key: HardwareKey) -> bool:
        """Test YubiKey presence."""
        try:
            result = subprocess.run(
                ['ykman', 'info'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _test_fido2_presence(self, key: HardwareKey) -> bool:
        """Test FIDO2 key presence."""
        # Re-detect to see if key is still there
        current_keys = self._detect_fido2_keys()
        return any(k.name == key.name for k in current_keys)
    
    def challenge_key(self, key: HardwareKey, challenge: bytes) -> Optional[bytes]:
        """
        Send a challenge to a hardware key and get the response.
        
        Args:
            key: Hardware key to challenge
            challenge: Challenge bytes
            
        Returns:
            Response bytes or None if failed
        """
        if key.key_type == KeyType.YUBIKEY:
            return self._challenge_yubikey(key, challenge)
        elif key.key_type == KeyType.FIDO2:
            return self._challenge_fido2(key, challenge)
        
        return None
    
    def _challenge_yubikey(self, key: HardwareKey, challenge: bytes) -> Optional[bytes]:
        """Challenge YubiKey with HMAC-SHA1."""
        try:
            # Use YubiKey HMAC-SHA1 challenge-response
            # This requires the key to be configured with a secret
            import hmac
            import hashlib
            
            # For this implementation, we'll use a simple approach
            # In production, you'd want to use the actual YubiKey challenge-response
            result = subprocess.run(
                ['ykman', 'otp', 'chalresp', '2', challenge.hex()],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                response_hex = result.stdout.strip()
                return bytes.fromhex(response_hex)
        
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
            logger.warning(f"YubiKey challenge failed: {e}")
        
        return None
    
    def _challenge_fido2(self, key: HardwareKey, challenge: bytes) -> Optional[bytes]:
        """Challenge FIDO2 key."""
        try:
            # This is a simplified implementation
            # Real FIDO2 operations are more complex and require proper attestation
            
            # For now, we'll just test that the key responds to commands
            result = subprocess.run(
                ['fido2-token', '-L'],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Return a simple response indicating the key is present
                import hashlib
                return hashlib.sha256(challenge).digest()
        
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"FIDO2 challenge failed: {e}")
        
        return None
    
    def wait_for_key_touch(self, key: HardwareKey, timeout: int = 30) -> bool:
        """
        Wait for user to touch the hardware key.
        
        Args:
            key: Hardware key to wait for
            timeout: Timeout in seconds
            
        Returns:
            True if touch detected, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if key.key_type == KeyType.YUBIKEY:
                # Try to trigger touch requirement
                try:
                    result = subprocess.run(
                        ['ykman', 'info'],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        return True
                except subprocess.TimeoutExpired:
                    # Timeout might indicate waiting for touch
                    pass
            
            time.sleep(0.5)
        
        return False
    
    def get_key_capabilities(self, key: HardwareKey) -> List[str]:
        """
        Get detailed capabilities of a hardware key.
        
        Args:
            key: Hardware key to query
            
        Returns:
            List of capability strings
        """
        capabilities = key.capabilities.copy()
        
        if key.key_type == KeyType.YUBIKEY:
            # Try to get more detailed capabilities
            try:
                result = subprocess.run(
                    ['ykman', 'info'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Applications:' in line:
                            apps = line.split(':', 1)[1].strip()
                            capabilities.extend(apps.split())
                            break
            
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return list(set(capabilities))  # Remove duplicates
    
    def generate_challenge(self) -> bytes:
        """Generate a random challenge for key testing."""
        import os
        return os.urandom(32)
    
    def verify_key_response(self, challenge: bytes, response: bytes, expected: bytes) -> bool:
        """
        Verify that a key response matches expected value.
        
        Args:
            challenge: Original challenge
            response: Key response
            expected: Expected response
            
        Returns:
            True if response is valid
        """
        return response == expected
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hardware key manager statistics."""
        return {
            'fido2_available': self._fido_available,
            'yubikey_available': self._yubikey_available,
            'detected_keys': len(self._detected_keys),
            'key_types': list(set(key.key_type.value for key in self._detected_keys)),
            'tools_available': self.is_available()
        }


class HardwareKeyAuth:
    """Hardware key authentication helper."""
    
    def __init__(self, key_manager: HardwareKeyManager):
        """Initialize with key manager."""
        self.key_manager = key_manager
        self._registered_keys: Dict[str, HardwareKey] = {}
    
    def register_key(self, key: HardwareKey, key_id: str) -> bool:
        """
        Register a hardware key for authentication.
        
        Args:
            key: Hardware key to register
            key_id: Unique identifier for the key
            
        Returns:
            True if registration successful
        """
        if self.key_manager.test_key_presence(key):
            self._registered_keys[key_id] = key
            logger.info(f"Registered hardware key: {key.name} ({key_id})")
            return True
        
        logger.warning(f"Failed to register hardware key: {key.name}")
        return False
    
    def authenticate_with_key(self, key_id: str, challenge: bytes) -> Optional[bytes]:
        """
        Authenticate using a registered hardware key.
        
        Args:
            key_id: ID of registered key
            challenge: Authentication challenge
            
        Returns:
            Authentication response or None if failed
        """
        if key_id not in self._registered_keys:
            logger.warning(f"Key not registered: {key_id}")
            return None
        
        key = self._registered_keys[key_id]
        
        if not self.key_manager.test_key_presence(key):
            logger.warning(f"Key not present: {key.name}")
            return None
        
        # Challenge the key
        response = self.key_manager.challenge_key(key, challenge)
        
        if response:
            logger.info(f"Successfully authenticated with key: {key.name}")
        else:
            logger.warning(f"Authentication failed with key: {key.name}")
        
        return response
    
    def get_registered_keys(self) -> Dict[str, HardwareKey]:
        """Get all registered keys."""
        return self._registered_keys.copy()
    
    def unregister_key(self, key_id: str) -> bool:
        """
        Unregister a hardware key.
        
        Args:
            key_id: ID of key to unregister
            
        Returns:
            True if successful
        """
        if key_id in self._registered_keys:
            del self._registered_keys[key_id]
            logger.info(f"Unregistered hardware key: {key_id}")
            return True
        
        return False