"""Security module for the Secrets application."""

from .secure_memory import SecureMemory, SecureString, SecureStringFactory, cleanup_secure_memory
from .keyring_manager import KeyringManager, KeyringBackend
from .encrypted_config import EncryptedConfigManager, EncryptionInfo
from .hardware_keys import HardwareKeyManager, HardwareKeyAuth, HardwareKey, KeyType
from .two_factor_auth import TwoFactorAuthManager, TOTPGenerator, TwoFactorMethod, TwoFactorConfig
from .audit_logger import (
    AuditLogger, AuditEvent, AuditEventType, AuditLevel,
    get_audit_logger, configure_audit_logging,
    audit_auth_success, audit_auth_failure, audit_password_access,
    audit_security_event, audit_app_start, audit_app_stop
)
from .cert_pinning import CertificatePinningManager, CertificatePin, CertificatePinning
from .incident_response import (
    IncidentManager, SecurityIncident, IncidentSeverity, IncidentStatus,
    ResponseAction, IncidentDetector, IncidentResponder
)

__all__ = [
    # Secure memory
    'SecureMemory',
    'SecureString', 
    'SecureStringFactory',
    'cleanup_secure_memory',
    
    # Keyring
    'KeyringManager',
    'KeyringBackend',
    
    # Encrypted config
    'EncryptedConfigManager',
    'EncryptionInfo',
    
    # Hardware keys
    'HardwareKeyManager',
    'HardwareKeyAuth',
    'HardwareKey',
    'KeyType',
    
    # Two-factor auth
    'TwoFactorAuthManager',
    'TOTPGenerator',
    'TwoFactorMethod',
    'TwoFactorConfig',
    
    # Audit logging
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'AuditLevel',
    'get_audit_logger',
    'configure_audit_logging',
    'audit_auth_success',
    'audit_auth_failure',
    'audit_password_access',
    'audit_security_event',
    'audit_app_start',
    'audit_app_stop',
    
    # Certificate pinning
    'CertificatePinningManager',
    'CertificatePin',
    'CertificatePinning',
    
    # Incident response
    'IncidentManager',
    'SecurityIncident',
    'IncidentSeverity',
    'IncidentStatus',
    'ResponseAction',
    'IncidentDetector',
    'IncidentResponder',
]