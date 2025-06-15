# Project Structure

This document describes the organization of the Secrets Password Manager project.

## Root Directory

```
Secrets/
├── secrets/                    # Main Python package
├── data/                       # Application data files
├── po/                         # Translations
├── tests/                      # Test suite
├── builddir/                   # Meson build directory (generated)
├── docs/                       # Documentation files
├── scripts/                    # Utility scripts
└── flatpak/                    # Flatpak-related files
```

## Main Package (`secrets/`)

```
secrets/
├── __init__.py                 # Package initialization
├── __main__.py                 # Module entry point
├── main.py                     # Application entry point
├── application.py              # Main application class
├── window.py                   # Main window implementation
├── app_info.py                 # Application metadata
├── models.py                   # Data models
├── managers.py                 # Manager classes
├── commands.py                 # Command pattern implementation
├── config.py                   # Configuration management
├── password_store.py           # Pass integration
├── async_operations.py         # Async operations
├── error_handling.py           # Error handling
├── performance.py              # Performance utilities
├── shortcuts_window.py         # Keyboard shortcuts
├── controllers/                # UI controllers
├── ui/                         # UI components
├── setup_wizard/               # Setup wizard
├── utils/                      # Utility modules
├── services/                   # Business logic services
├── meson.build                 # Build configuration
└── secrets.gresource.xml       # Resource bundle definition
```

## Data Files (`data/`)

```
data/
├── ui/                         # UI definition files
│   ├── main_window.ui
│   ├── components/
│   ├── dialogs/
│   └── setup/
├── icons/                      # Application icons
│   └── io.github.tobagin.secrets.svg
├── screenshots/                # Screenshots for Flathub
├── style.css                   # Application styles
├── io.github.tobagin.secrets.desktop.in    # Desktop entry
├── io.github.tobagin.secrets.appdata.xml.in # AppStream metadata
└── meson.build                 # Data build configuration
```

## Build System

### Meson Files
- `meson.build` - Root build configuration
- `secrets/meson.build` - Python package build
- `data/meson.build` - Data files build
- `po/meson.build` - Translation build

### Generated Files
- `builddir/` - Meson build directory
- `secrets.in` - Executable script template
- `secrets-dev.in` - Development script template

## Flatpak Integration

### Core Files
- `io.github.tobagin.secrets.yml` - Flatpak manifest
- `flathub.json` - Flathub configuration
- `FLATHUB_SUBMISSION.md` - Submission guide

### Metadata
- Desktop file with proper Exec and Icon
- AppStream metadata with screenshots
- Application icon in SVG format

## Development Tools

### Scripts
- `run-dev.sh` - Development runner
- `secrets-dev` - Simple launcher
- `cleanup.sh` - Project cleanup
- `prepare-release.sh` - Release preparation

### Testing
- `tests/` - Test suite
- `run_tests.py` - Test runner

## Documentation

### User Documentation
- `README.md` - Main project documentation
- `FLATHUB_SUBMISSION.md` - Flathub submission guide
- `PROJECT_STRUCTURE.md` - This file

### Development Documentation
- `ANALYSIS.md` - Code analysis
- `IMPLEMENTED_FEATURES.md` - Feature documentation
- `REFACTORING_SUMMARY.md` - Refactoring notes
- `UI_IMPROVEMENTS_SUMMARY.md` - UI improvements

## Key Design Patterns

### Architecture
- **MVC Pattern**: Controllers manage UI logic
- **Command Pattern**: Actions are encapsulated as commands
- **Manager Pattern**: Specialized managers for different concerns
- **Service Pattern**: Business logic in service classes

### UI Organization
- **Component-based**: Reusable UI components
- **Resource bundles**: GResource for UI files and assets
- **Responsive design**: Adaptive layouts with Libadwaita

### Build System
- **Meson**: Modern build system with proper dependency management
- **GResource**: Bundled resources for distribution
- **i18n ready**: Translation support with gettext

## Dependencies

### Runtime Dependencies
- Python 3.8+
- GTK4
- Libadwaita
- PyGObject
- pass (password store)
- GPG

### Build Dependencies
- Meson
- Ninja
- glib-compile-resources
- gettext

### Development Dependencies
- flatpak-builder (for Flatpak builds)
- appstream-util (for validation)
- desktop-file-validate (for validation)

## Installation Paths

### System Installation
- Executable: `/usr/bin/io.github.tobagin.secrets`
- Python modules: `/usr/lib/python3.x/site-packages/secrets/`
- Data files: `/usr/share/io.github.tobagin.secrets/`
- Desktop file: `/usr/share/applications/io.github.tobagin.secrets.desktop`
- Icon: `/usr/share/icons/hicolor/scalable/apps/io.github.tobagin.secrets.svg`
- AppData: `/usr/share/metainfo/io.github.tobagin.secrets.appdata.xml`

### Flatpak Installation
- All files under `/app/` prefix in the Flatpak sandbox
- Proper isolation and permission management
- Integration with host system through portals
