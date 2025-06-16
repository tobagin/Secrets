# Scripts Directory

This directory contains utility scripts for maintaining and releasing the Secrets Password Manager.

## Scripts

### `update-flatpak-deps.py`

Automatically checks PyPI for the latest versions of Python packages used in the Flatpak manifest and updates the URLs and SHA256 hashes accordingly.

**Features:**
- Fetches latest package versions from PyPI API
- Updates wheel URLs and SHA256 hashes automatically
- Colored output with clear status messages
- Handles multiple packages in a single run

**Usage:**
```bash
python3 scripts/update-flatpak-deps.py
```

**What it does:**
1. Parses the Flatpak manifest (`io.github.tobagin.secrets.yml`)
2. Extracts Python package names from wheel URLs
3. Queries PyPI for the latest version of each package
4. Updates the manifest with new URLs and SHA256 hashes
5. Reports which packages were updated

### `update-deps.sh`

Standalone wrapper script for updating Flatpak dependencies with additional Git integration.

**Features:**
- Runs the Python dependency updater
- Shows Git diff of changes
- Provides next steps for testing and committing
- Colored output and user guidance

**Usage:**
```bash
./scripts/update-deps.sh
```

**What it does:**
1. Runs `update-flatpak-deps.py`
2. Checks for changes in the Flatpak manifest
3. Shows a summary of what was updated
4. Provides guidance for testing and committing changes

## Integration with Release Process

The dependency update functionality is automatically integrated into the main release preparation script (`prepare-release.sh`). When preparing a release, dependencies are automatically checked and updated before building and testing.

This ensures that releases always use the latest stable versions of dependencies, improving security and compatibility.

## Manual Usage

You can run the dependency update scripts manually at any time:

```bash
# Quick update check
./scripts/update-deps.sh

# Direct Python script (more detailed output)
python3 scripts/update-flatpak-deps.py

# Then test the changes
flatpak-builder --force-clean build-dir io.github.tobagin.secrets.yml

# Commit if everything works
git add io.github.tobagin.secrets.yml
git commit -m "chore: Update Flatpak dependencies to latest versions"
```

## Dependencies

The scripts require:
- Python 3.6+
- Internet connection (to query PyPI)
- Git (for the wrapper script)

No additional Python packages are required - the scripts use only standard library modules.
