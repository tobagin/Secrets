#!/usr/bin/env python3
"""
Comprehensive version synchronization script for the Secrets project.

This script ensures that version information is synchronized across all project files
using meson.build as the single source of truth.
"""

import re
import sys
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET


def get_version_from_meson(project_root: Path) -> str:
    """Extract version from meson.build file."""
    meson_file = project_root / "meson.build"
    
    if not meson_file.exists():
        raise FileNotFoundError(f"meson.build not found at {meson_file}")
    
    with open(meson_file, 'r') as f:
        content = f.read()
    
    # Match version in project() declaration
    pattern = r"project\s*\(\s*['\"]secrets['\"]\s*,\s*version\s*:\s*['\"]([^'\"]+)['\"]"
    match = re.search(pattern, content)
    
    if match:
        return match.group(1)
    else:
        raise ValueError("Could not find version in meson.build")


def validate_version_format(version: str) -> bool:
    """Validate version follows semantic versioning."""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))


def update_python_files(project_root: Path, version: str) -> List[str]:
    """Update Python files to use centralized version."""
    updated_files = []
    
    # Update __init__.py
    init_file = project_root / "src" / "secrets" / "__init__.py"
    if init_file.exists():
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Ensure it uses get_version()
        if '__version__ = "' in content:
            content = re.sub(
                r'__version__\s*=\s*["\'][^"\']+["\']',
                '__version__ = get_version()',
                content
            )
            # Add import if not present
            if 'from .version import get_version' not in content:
                content = re.sub(
                    r'(from \.main import main)',
                    r'from .main import main\nfrom .version import get_version',
                    content
                )
        
        with open(init_file, 'w') as f:
            f.write(content)
        updated_files.append(str(init_file))
    
    # Update app_info.py
    app_info_file = project_root / "src" / "secrets" / "app_info.py"
    if app_info_file.exists():
        with open(app_info_file, 'r') as f:
            content = f.read()
        
        # Ensure it uses get_version()
        if 'VERSION = "' in content:
            content = re.sub(
                r'VERSION\s*=\s*["\'][^"\']+["\']',
                'VERSION = get_version()',
                content
            )
            # Add import if not present
            if 'from .version import get_version' not in content:
                content = re.sub(
                    r'(APP_ID = _get_app_id\(\))',
                    r'\1\n\n# Import version from centralized source\nfrom .version import get_version',
                    content
                )
        
        with open(app_info_file, 'w') as f:
            f.write(content)
        updated_files.append(str(app_info_file))
    
    return updated_files


def update_appdata_xml(project_root: Path, version: str) -> bool:
    """Update AppData XML file with current version."""
    appdata_file = project_root / "data" / "io.github.tobagin.secrets.appdata.xml.in"
    
    if not appdata_file.exists():
        return False
    
    with open(appdata_file, 'r') as f:
        content = f.read()
    
    # Update the most recent release version
    pattern = r'<release version="[^"]*" date="[^"]*"'
    current_date = date.today().strftime("%Y-%m-%d")
    replacement = f'<release version="{version}" date="{current_date}"'
    
    new_content = re.sub(pattern, replacement, content, count=1)
    
    if new_content != content:
        with open(appdata_file, 'w') as f:
            f.write(new_content)
        return True
    
    return False


def update_flatpak_manifest(project_root: Path, version: str) -> bool:
    """Update Flatpak manifest with current version (for app source)."""
    manifest_files = [
        project_root / "packaging" / "flatpak" / "io.github.tobagin.secrets.yml",
        project_root / "packaging" / "flatpak" / "io.github.tobagin.secrets.dev.yml"
    ]
    
    updated = False
    
    for manifest_file in manifest_files:
        if not manifest_file.exists():
            continue
        
        with open(manifest_file, 'r') as f:
            content = f.read()
        
        # Find the main secrets source section and update its tag
        # Look for the last source entry which should be the secrets app itself
        lines = content.split('\n')
        in_last_source = False
        
        for i, line in enumerate(lines):
            # Find the last "- name:" entry (should be the secrets app)
            if line.strip().startswith('- name:') and 'secrets' in line.lower():
                in_last_source = True
            elif line.strip().startswith('- name:') and in_last_source:
                in_last_source = False
            elif in_last_source and 'tag:' in line:
                # Update the tag for the secrets app
                lines[i] = re.sub(r'tag:\s*v?[0-9]+\.[0-9]+\.[0-9]+', f'tag: v{version}', line)
                updated = True
                break
        
        if updated:
            with open(manifest_file, 'w') as f:
                f.write('\n'.join(lines))
    
    return updated


def create_changelog_entry(project_root: Path, version: str) -> bool:
    """Create or update changelog entry for the version."""
    changelog_file = project_root / "CHANGELOG.md"
    
    # Create changelog if it doesn't exist
    if not changelog_file.exists():
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{version}] - {date.today().strftime("%Y-%m-%d")}

### Added
- Centralized version management system
- Automatic version synchronization across all project files

### Changed
- Version information now managed from single source (meson.build)

### Technical
- Implemented version synchronization system
- Enhanced build process with automatic version generation
"""
        with open(changelog_file, 'w') as f:
            f.write(changelog_content)
        return True
    
    return False


def backup_files(files: List[Path]) -> Dict[Path, str]:
    """Create backups of files before modification."""
    backups = {}
    for file_path in files:
        if file_path.exists():
            with open(file_path, 'r') as f:
                backups[file_path] = f.read()
    return backups


def restore_backups(backups: Dict[Path, str]) -> None:
    """Restore files from backups."""
    for file_path, content in backups.items():
        with open(file_path, 'w') as f:
            f.write(content)


def main():
    """Main synchronization function."""
    project_root = Path.cwd()
    
    try:
        # Extract version from meson.build
        version = get_version_from_meson(project_root)
        
        if not validate_version_format(version):
            print(f"Warning: Version '{version}' does not follow semantic versioning (x.y.z)")
        
        print(f"Synchronizing version {version} across all project files...")
        print("=" * 60)
        
        all_files_to_modify = [
            project_root / "src" / "secrets" / "__init__.py",
            project_root / "src" / "secrets" / "app_info.py",
            project_root / "data" / "io.github.tobagin.secrets.appdata.xml.in",
            project_root / "packaging" / "flatpak" / "io.github.tobagin.secrets.yml",
            project_root / "packaging" / "flatpak" / "io.github.tobagin.secrets.dev.yml",
        ]
        
        # Create backups
        backups = backup_files(all_files_to_modify)
        
        try:
            # Update Python files
            updated_python = update_python_files(project_root, version)
            for file_path in updated_python:
                print(f"✓ Updated Python file: {file_path}")
            
            # Update AppData XML
            if update_appdata_xml(project_root, version):
                print("✓ Updated AppData XML file")
            else:
                print("• AppData XML file already up to date")
            
            # Update Flatpak manifests
            if update_flatpak_manifest(project_root, version):
                print("✓ Updated Flatpak manifest files")
            else:
                print("• Flatpak manifest files already up to date")
            
            # Create changelog entry
            if create_changelog_entry(project_root, version):
                print("✓ Created changelog entry")
            else:
                print("• Changelog already exists")
            
            print("\n" + "=" * 60)
            print(f"✅ Version synchronization completed successfully!")
            print(f"All project files now reference version {version}")
            
            # Run validation
            print("\nRunning validation...")
            validate_script = project_root / "scripts" / "validate_version.py"
            if validate_script.exists():
                import subprocess
                result = subprocess.run([sys.executable, str(validate_script)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✓ Validation passed")
                else:
                    print("⚠ Validation found issues:")
                    print(result.stdout)
            
        except Exception as e:
            print(f"\n❌ Error during synchronization: {e}")
            print("Restoring backups...")
            restore_backups(backups)
            raise
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()