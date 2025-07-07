# Settings and Preferences Guide

This guide covers all the settings and preferences available in the Secrets password manager, including the newly implemented compliance features.

## Accessing Settings

### Preferences Dialog
- **Location**: Main menu → Preferences (or keyboard shortcut)
- **Pages**: 5 main categories of settings

### Compliance Dashboard  
- **Location**: Main menu → Compliance Dashboard
- **Alternative**: Preferences → Compliance → Open Dashboard button

## Settings Categories

### 1. General Settings
**Location**: Preferences → General

- **Theme**: Auto (Follow System), Light, Dark
- **Window State**: Remember window size and position on startup

### 2. Security Settings
**Location**: Preferences → Security

#### Password Display
- **Auto-hide Passwords**: Automatically hide passwords after timeout
- **Auto-hide Timeout**: Seconds before passwords are hidden (5-300)

#### Clipboard Security
- **Clear Clipboard Timeout**: Seconds before clipboard is cleared (10-300)

#### Confirmations
- **Confirm Deletions**: Show confirmation dialog before deleting passwords

#### Session Security
- **Lock on Idle**: Automatically lock application when idle
- **Idle Timeout**: Minutes of inactivity before locking (1-120)
- **Lock on Screen Lock**: Lock application when system screen locks
- **Master Password Timeout**: Minutes before requiring password re-entry (0-480)

#### Advanced Security
- **Clear Memory on Lock**: Clear sensitive data from memory when locked
- **Require Master Password for Export**: Require master password for export operations
- **Max Failed Unlock Attempts**: Maximum failed attempts before lockout (1-10)
- **Lockout Duration**: Minutes to lock out after failed attempts (1-60)

### 3. Compliance Settings
**Location**: Preferences → Compliance

#### Framework Toggles
- **HIPAA Compliance**: Health Insurance Portability and Accountability Act
- **PCI DSS Compliance**: Payment Card Industry Data Security Standard  
- **GDPR Compliance**: General Data Protection Regulation
- **Role-Based Access Control**: Enable RBAC system
- **Audit Logging**: Enable comprehensive audit event logging

#### Quick Configuration
- **Compliance Dashboard**: Opens detailed compliance configuration
- **Security Officer Email**: Email for security notifications
- **Data Protection Officer Email**: Email for data protection inquiries

#### Detailed Compliance (Dashboard)
**Access**: Compliance Dashboard or Preferences → Compliance → Open Dashboard

**HIPAA Settings** (45+ options):
- Security officer configuration
- Workforce training programs and intervals
- Risk assessment scheduling
- Administrative safeguards

**PCI DSS Settings**:
- Password complexity enforcement
- Minimum password length (8-32 characters)
- Password history tracking (1-12 previous passwords)
- Account lockout policies
- Failed login attempt limits (3-10)

**GDPR Settings**:
- Data export capabilities
- Data retention policies
- Breach notification systems
- Data Protection Officer requirements
- Data subject rights management

**RBAC Settings**:
- Role assignment controls
- Justification requirements for role changes
- Maximum role assignments per user (1-20)

**Audit & Monitoring**:
- Comprehensive audit logging
- Access logging controls  
- Audit retention periods (365-3650 days)
- Event tracking and monitoring

### 4. Search Settings
**Location**: Preferences → Search

#### Search Options
- **Case Sensitive**: Make searches case sensitive
- **Search in Content**: Include password content in search results
- **Search in Filenames**: Include filenames in search
- **Maximum Results**: Maximum number of search results (10-1000)

### 5. Git Settings
**Location**: Preferences → Git

#### Automation
- **Auto-pull on Startup**: Automatically pull changes when app starts
- **Auto-push on Changes**: Automatically push changes after modifications

#### Status & Monitoring
- **Show Git Status**: Display git repository status information
- **Git Timeout**: Timeout for git operations in seconds (5-120)

#### Repository Management
- **Repository Setup**: Configure Git repository and remote connections
- **Repository Status**: View Git repository status and history

#### Advanced Settings
- **Auto-commit Changes**: Automatically commit changes before push/pull
- **Show Git Notifications**: Display notifications for Git operations
- **Check Remote on Startup**: Check for remote changes when app starts

## How Settings Are Stored

### Configuration Files
- **Location**: User configuration directory
- **Format**: JSON with encryption for sensitive data
- **Backup**: Automatic backup of configuration on changes

### Compliance Configuration
- **Encryption**: All compliance settings are encrypted at rest
- **Audit Trail**: Changes to compliance settings are logged
- **Export**: Compliance reports can be exported as JSON

## Best Practices

### Security Settings
1. Enable auto-lock with appropriate timeout for your environment
2. Set clipboard clearing to minimize exposure time
3. Enable memory clearing for high-security environments
4. Configure appropriate failed attempt limits

### Compliance Settings
1. Enable relevant compliance frameworks for your organization
2. Configure security officer and DPO email addresses
3. Set appropriate audit retention periods
4. Regular review compliance dashboard for violations
5. Export compliance reports for auditing

### Search Settings
1. Enable case-sensitive search for precise matching
2. Be cautious with content search in sensitive environments
3. Limit maximum results for performance

### Git Settings
1. Configure appropriate timeouts for your network
2. Enable auto-commit to ensure changes are tracked
3. Use auto-pull/push carefully in multi-user environments
4. Monitor Git status for synchronization issues

## Troubleshooting

### Settings Not Saving
- Check file permissions in configuration directory
- Verify disk space availability
- Review application logs for errors

### Compliance Dashboard Not Opening
- Ensure compliance features are enabled in configuration
- Check for proper permissions
- Verify all compliance dependencies are installed

### Git Features Not Working
- Verify Git is installed and accessible
- Check repository configuration
- Confirm network connectivity for remote operations

## Security Considerations

### Sensitive Settings
- Master password timeouts affect security vs. convenience balance
- Clipboard timeouts should be minimized in shared environments  
- Memory clearing impacts performance but increases security

### Compliance Settings
- Changes to compliance settings may trigger audit events
- Some settings require administrator privileges
- Compliance configurations are encrypted and require proper access

### Backup and Recovery
- Regular backup of configuration recommended
- Export compliance settings before major changes
- Test recovery procedures periodically