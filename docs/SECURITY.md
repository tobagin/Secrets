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

## Compliance Framework Support

Secrets Password Manager now includes comprehensive compliance framework support for regulated industries:

### Supported Compliance Frameworks

#### HIPAA (Health Insurance Portability and Accountability Act)
- **Administrative Safeguards**: Security officer designation, workforce training, access management
- **Technical Safeguards**: Unique user identification, audit controls, encryption, transmission security
- **Physical Safeguards**: Device and media controls, workstation security
- **Documentation**: Security policies, risk assessments, contingency plans
- **Features**: PHI access logging, workforce training tracking, breach notification

#### PCI DSS (Payment Card Industry Data Security Standard)
- **Access Control**: Role-based access control, strong authentication, password complexity
- **Data Protection**: Encryption at rest and in transit, key management, data retention policies
- **Monitoring**: Comprehensive audit logging, intrusion detection, file integrity monitoring
- **Testing**: Vulnerability scanning, penetration testing, security assessments
- **Features**: Card data access logging, password history enforcement, account lockout

#### GDPR (General Data Protection Regulation)
- **Data Protection Principles**: Lawfulness, purpose limitation, data minimisation, accuracy
- **Individual Rights**: Access, rectification, erasure (right to be forgotten), portability
- **Privacy by Design**: Data protection by design and by default
- **Consent Management**: Valid consent recording, easy withdrawal mechanisms
- **Features**: Data subject request handling, breach notification, consent tracking

### Compliance Architecture

#### Role-Based Access Control (RBAC)
- Hierarchical role system with inheritance
- Fine-grained permissions for all resource types
- Automated access auditing and reporting
- Principle of least privilege enforcement
- Configurable role assignments with expiration

#### Audit and Monitoring
- Comprehensive compliance event logging
- Real-time access control decisions
- Automated violation detection
- Compliance dashboard and reporting
- Regular compliance assessments

#### Data Protection
- Encrypted configuration storage for sensitive settings
- Secure memory handling for compliance data
- Automated data retention and deletion policies
- Data export capabilities for subject rights
- Privacy impact assessment tools

### Configuration Requirements

To enable compliance features, administrators must:

1. **Configure Compliance Manager**:
   ```python
   from secrets.compliance import HIPAAComplianceManager, PCIDSSComplianceManager, GDPRComplianceManager
   ```

2. **Enable RBAC**:
   - Configure role-based access control
   - Assign appropriate roles to users
   - Set up access review processes

3. **Configure Audit Logging**:
   - Enable comprehensive audit events
   - Set appropriate retention periods
   - Configure log integrity protection

4. **Implement Policies**:
   - Define security policies and procedures
   - Set up training programs
   - Establish incident response plans

### Compliance Reporting

- Automated compliance assessments
- Export compliance reports in multiple formats (JSON, HTML)
- Track compliance scores and trends
- Violation tracking and remediation
- Evidence collection and management

### Important Notes

- **Professional Consultation Required**: Organizations in regulated industries must consult with qualified security and compliance professionals
- **Risk Assessment**: Perform thorough risk assessments before production deployment
- **Regular Reviews**: Compliance status requires ongoing monitoring and regular reviews
- **Documentation**: Maintain comprehensive documentation of all compliance measures
- **Training**: Ensure all users receive appropriate security awareness training

### Implementation Status

✅ **Core Compliance Framework**: Complete  
✅ **HIPAA Support**: Administrative, technical, and physical safeguards implemented  
✅ **PCI DSS Support**: All 12 requirements addressed with automated controls  
✅ **GDPR Support**: Data protection principles and individual rights implemented  
✅ **RBAC System**: Comprehensive role-based access control  
✅ **Audit Framework**: Compliance-aware audit logging and reporting  

For detailed implementation guidance, see the compliance module documentation in `src/secrets/compliance/`.

## Security Checklist for Releases

- [ ] No passwords or tokens in code or logs
- [ ] All dependencies updated to latest secure versions
- [ ] Security-critical changes reviewed by maintainer
- [ ] Flatpak permissions minimized
- [ ] No new subprocess calls without validation
- [ ] Documentation updated for security changes