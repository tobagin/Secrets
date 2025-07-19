# Version Management System

The Secrets project uses a comprehensive version management system with `meson.build` as the single source of truth for version information.

## Overview

This system ensures that all version references throughout the project remain synchronized automatically, eliminating manual version updates and preventing inconsistencies.

## Architecture

### Single Source of Truth
- **`meson.build`**: Contains the authoritative version number in the `project()` declaration
- All other version references are automatically generated or dynamically retrieved from this source

### Core Components

1. **Version Module** (`src/secrets/version.py`)
   - Provides `get_version()` function that reads from meson.build
   - Implements caching for performance
   - Handles path resolution robustly

2. **Generation Script** (`scripts/generate_version.py`)
   - Generates Python module files with version information
   - Called automatically during meson configuration

3. **Synchronization Script** (`scripts/sync_version.py`)
   - Synchronizes version across all project files
   - Updates AppData XML, Flatpak manifests, and Python files
   - Creates changelog entries

4. **Validation Script** (`scripts/validate_version.py`)
   - Validates version consistency across all files
   - Supports both static and dynamic version patterns
   - Provides clear error reporting

5. **Monitoring System** (`scripts/monitor_version_sync.py`)
   - Comprehensive status monitoring
   - Generates detailed reports
   - Provides recommendations for fixes

## Files Synchronized

The system automatically synchronizes version information in:

- `src/secrets/__init__.py` - Python package version
- `src/secrets/app_info.py` - Application version constant
- `data/io.github.tobagin.secrets.appdata.xml.in` - AppData release information
- `packaging/flatpak/io.github.tobagin.secrets.yml` - Flatpak manifest
- `packaging/flatpak/io.github.tobagin.secrets.dev.yml` - Development Flatpak manifest
- `CHANGELOG.md` - Version history (auto-created)

## Usage

### For Developers

#### Updating Version
1. Edit version in `meson.build` only:
   ```meson
   project('secrets', version : '0.8.14', ...)
   ```

2. Run build configuration:
   ```bash
   meson setup --reconfigure build
   ```

3. Synchronization happens automatically during build

#### Manual Synchronization
```bash
# Sync all files
python3 scripts/sync_version.py

# Validate consistency
python3 scripts/validate_version.py

# Monitor system status
python3 scripts/monitor_version_sync.py
```

### For Release Management

#### Pre-Release Checklist
1. Update version in `meson.build`
2. Run synchronization: `python3 scripts/sync_version.py`
3. Validate: `python3 scripts/validate_version.py`
4. Review generated changelog entry
5. Commit synchronized files

#### Automated Integration
The system integrates with:
- **Meson Build**: Automatic sync during configuration
- **Pre-commit Hooks**: Version validation before commits
- **CI/CD**: Consistency checks in build pipelines

## Build Integration

### Meson Configuration
```meson
# Generate version files from meson.build as single source of truth
generate_version = find_program('scripts/generate_version.py')
sync_version = find_program('scripts/sync_version.py')

# Generate version files at configuration time
run_command(generate_version, meson.project_source_root(), check: true)

# Synchronize version across all project files
run_command(sync_version, check: false)
```

### Runtime Access
```python
# In Python code
from .version import get_version

version = get_version()  # Reads from meson.build
```

## Validation and Monitoring

### Validation Patterns
The system validates:
- Static version strings: `VERSION = "0.8.13"`
- Dynamic version calls: `VERSION = get_version()`
- AppData XML release entries
- Flatpak manifest tags

### Monitoring Features
- Build integration status
- Sync script functionality
- Version consistency validation
- Detailed JSON reporting
- Recommendation system

## Error Handling

### Common Issues and Solutions

1. **Version Mismatch**
   ```bash
   # Solution: Run synchronization
   python3 scripts/sync_version.py
   ```

2. **Missing Version Pattern**
   ```bash
   # Solution: Check file format and run sync
   python3 scripts/validate_version.py
   ```

3. **Build Integration Issues**
   ```bash
   # Solution: Reconfigure build
   meson setup --reconfigure build
   ```

### Recovery Procedures
1. Backup system creates automatic backups during sync
2. Validation runs before and after synchronization
3. Manual rollback available if issues occur

## Best Practices

### Development Workflow
1. Always update version in `meson.build` only
2. Never manually edit version in other files
3. Run validation before commits
4. Use monitoring script for status checks

### Release Workflow
1. Update version in `meson.build`
2. Run full synchronization
3. Review all synchronized files
4. Test build with new version
5. Commit all changes together

### Maintenance
- Regularly run monitoring script
- Keep synchronization scripts updated
- Validate after major refactoring
- Document any system changes

## Future Enhancements

Planned improvements include:
- Git tag synchronization
- Semantic version validation
- Automated changelog generation
- Integration with release workflows
- Multi-language project support

## Troubleshooting

### Debug Mode
```bash
# Enable verbose output
python3 scripts/sync_version.py --debug

# Generate detailed report
python3 scripts/monitor_version_sync.py --json
```

### Manual Override
In emergency situations, version synchronization can be bypassed:
```bash
# Skip version checks (not recommended)
meson setup build -Dskip_version_sync=true
```

This system ensures reliable, automated version management for the Secrets project, supporting both development and release workflows while maintaining consistency across all project components.