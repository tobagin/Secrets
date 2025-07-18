# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Secrets is a GTK4/Libadwaita password manager providing a graphical interface for the Unix `pass` password store. It's written in Python and distributed as a Flatpak application.

## Commands

### Development Setup
```bash
# Initial setup
meson setup build
meson compile -C build

# Run in development mode (recommended)
./scripts/run-dev.sh

# Alternative: Direct Python execution
./scripts/run-dev.sh --direct
# or
python3 -m secrets.main
```

### Building and Testing
```bash
# Build with Meson
meson compile -C build

# Build Flatpak locally
flatpak-builder --user --install --force-clean build packaging/flatpak/io.github.tobagin.secrets.yml

# Run Flatpak version
flatpak run io.github.tobagin.secrets

# Run unit tests
python -m pytest tests/
# or with coverage
python -m pytest tests/ --cov=src/secrets --cov-report=html

# Code quality checks
ruff check src/ tests/          # Linting with ruff
black src/ tests/              # Code formatting with black
mypy src/secrets               # Type checking with mypy
bandit -r src/                 # Security analysis with bandit
```

### Release Management
```bash
# Prepare a new release (updates versions, builds, validates)
./scripts/prepare-release.sh [VERSION]

# Update Flatpak dependencies
python3 scripts/update-flatpak-deps.py
```

## Architecture

### Core Structure
- **MVC Pattern**: UI components (views) separated from controllers and business logic
- **Service Layer**: `services/` handles core operations (password management, git sync)
- **Manager Layer**: `managers/` provides specialized functionality (clipboard, search, git)
- **UI Components**: Modular dialogs and widgets in `ui/`

### Key Components
- **PasswordService** (`services/password_service.py`): Core interface to `pass` backend
- **GitService** (`services/git_service.py`): Git synchronization functionality
- **MainWindow** (`main_window.py`): Primary application window
- **SetupWizard** (`setup_wizard/`): Initial configuration flow
- **ComplianceManager** (`compliance/`): Regulatory compliance framework (HIPAA, PCI DSS, GDPR)
- **RBACManager** (`compliance/rbac/`): Role-based access control system
- **AuditLogger** (`security/audit_logger.py`): Comprehensive security event logging

### Dependencies
- **Runtime**: GTK 4.0+, Libadwaita 1.4+, Python 3.11+
- **Backend**: `pass` (password-store), `gpg`, `git`
- **Python**: requests, pyotp (TOTP), pillow (favicons)

### Development Guidelines
- Follow PEP 8 with 88-character line limit
- Use type hints for all function signatures
- Follow GNOME HIG for UI design
- Commit format: `type: description` (feat, fix, docs, etc.)
- Use the configured linting tools: ruff, black, mypy, bandit
- Run `make quality-check` before committing
- Use the provided utilities for common operations (PathValidator, MetadataHandler, etc.)

### Important Notes
- The application uses GResource for UI files - run `meson compile` after UI changes
- Translations are in `po/` directory using gettext
- Security-sensitive operations use memory protection (`mlock`)
- Git operations are async to prevent UI blocking
- Flatpak manifest (`packaging/flatpak/io.github.tobagin.secrets.yml`) defines the runtime environment

## Security Considerations

### Critical Security Areas
- **Password Handling**: All passwords handled through `pass` CLI, never log or print password content
- **Memory Security**: Currently lacks proper memory locking - passwords may be swapped to disk
- **Process Security**: Use `GPGSetupHelper.setup_gpg_environment()` for all GPG operations
- **Input Validation**: Always validate paths to prevent directory traversal attacks

### Security Guidelines
- Never store credentials in code or config files (except through proper encryption)
- Always pass sensitive data via stdin, not command arguments
- Validate all user input before using in subprocess commands
- Use existing security helpers (ClipboardManager, PasswordCache) rather than implementing new ones
- Check docs/SECURITY.md for detailed security architecture and known issues

### Testing Security Features
- Test auto-lock functionality with different timeouts
- Verify clipboard clearing works correctly
- Ensure failed login attempts trigger rate limiting
- Check that GPG operations fail gracefully with proper error messages

### Testing Compliance Features
- Run compliance assessments for each framework (HIPAA, PCI DSS, GDPR)
- Test RBAC role assignments and access control decisions
- Verify audit logging captures all required compliance events
- Test data subject rights (access, rectification, erasure, portability)
- Validate consent management and withdrawal mechanisms
- Check breach notification and incident response procedures