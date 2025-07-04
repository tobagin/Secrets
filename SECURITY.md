# Security Documentation for Secrets Password Manager

## Overview

Secrets is a security-critical application that manages user passwords. This document outlines the security architecture, known issues, and best practices for maintaining the security of the application.

## Security Architecture

### Encryption
- All password encryption is handled by GPG through the `pass` command-line utility
- Uses GPG with 4096-bit RSA keys by default
- No custom cryptographic implementations

### Password Storage
- Passwords are never stored in plaintext on disk
- Uses the standard `pass` directory structure (~/.password-store/)
- Each password is individually encrypted with GPG

### Memory Security
**⚠️ Current Limitations:**
- Passwords are temporarily held in Python string objects without memory locking
- Password cache stores decrypted passwords for up to 300 seconds
- No explicit memory wiping after password use

### Authentication
- Primary authentication through GPG passphrase
- Auto-lock feature with configurable timeout (default: 5 minutes)
- Failed unlock attempt tracking with rate limiting

## Security Features

### Clipboard Protection
- Automatic clipboard clearing after 45 seconds (configurable)
- Verification before clearing to prevent data loss
- Only clears if clipboard still contains the copied password

### Process Security
- GPG agent configuration includes `no-allow-external-cache`
- Proper file permissions (0o700 for directories, 0o600 for config files)
- Environment isolation for GPG operations

### Input Validation
- Path traversal prevention (blocks ".." and absolute paths)
- Command injection protection through argument validation
- Sanitized environment variables for subprocess calls

## Security Enhancements Implemented

### Critical Issues Fixed ✅
1. **Memory Security**: Implemented secure memory handling with mlock and automatic wiping
2. **Token Storage**: Integrated system keyring for encrypted credential storage
3. **Cache Duration**: Reduced default cache TTL from 5 minutes to 60 seconds
4. **Memory Cleanup**: Added secure string implementation with automatic memory wiping

### Medium Priority Features Added ✅
1. **Hardware Security Keys**: Full support for YubiKey and FIDO2 devices
2. **Two-Factor Authentication**: TOTP, hardware keys, and backup codes
3. **Encrypted Configuration**: All sensitive config stored encrypted
4. **Audit Logging**: Comprehensive security event logging

### Low Priority Features Added ✅
1. **Certificate Pinning**: Protection against MITM attacks for Git operations
2. **Incident Response**: Automated security incident detection and response

## Security Best Practices

### For Users
1. Use a strong GPG passphrase
2. Enable auto-lock with a short timeout
3. Reduce clipboard clear time in high-security environments
4. Regularly update the application
5. Use full-disk encryption to protect swap files

### For Developers
1. Never log password content
2. Always use stdin for passing passwords to subprocesses
3. Validate all user input before using in commands
4. Use the GPGSetupHelper for all GPG operations
5. Follow the principle of least privilege

## Incident Response

If you discover a security vulnerability:
1. Do NOT create a public issue
2. Email the maintainer privately at security@[domain]
3. Include steps to reproduce and potential impact
4. Allow reasonable time for a fix before public disclosure

## Advanced Security Features

### Available Security Modules
- **SecureMemory**: Memory locking and secure wiping for sensitive data
- **KeyringManager**: Integration with system keyrings (GNOME, KDE, macOS, Windows)
- **EncryptedConfigManager**: Encrypted storage for all sensitive configuration
- **HardwareKeyManager**: Support for YubiKey, FIDO2, and other hardware keys
- **TwoFactorAuthManager**: TOTP, hardware key, and backup code authentication
- **AuditLogger**: Comprehensive security event logging with multiple outputs
- **CertificatePinningManager**: Protection against certificate-based attacks
- **IncidentManager**: Automated security incident detection and response

### Security Configuration
All security features can be configured through encrypted configuration files:
- 2FA settings with multiple methods
- Hardware key registration and management
- Audit logging with customizable rules
- Incident response with automated actions
- Certificate pinning for trusted hosts

## Compliance

This application is designed for personal use and may not meet regulatory requirements for:
- HIPAA (healthcare data)
- PCI DSS (payment card data)
- GDPR (without additional configuration)

Users in regulated industries should consult with security professionals before use.

## Security Checklist for Releases

- [ ] No passwords or tokens in code or logs
- [ ] All dependencies updated to latest secure versions
- [ ] Security-critical changes reviewed by maintainer
- [ ] Flatpak permissions minimized
- [ ] No new subprocess calls without validation
- [ ] Documentation updated for security changes