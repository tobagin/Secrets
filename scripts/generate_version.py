#!/usr/bin/env python3
"""
Generate version information from meson.build

This script extracts the version number from meson.build and generates
version files for Python modules, ensuring a single source of truth.
"""

import re
import sys
import os
from pathlib import Path


def extract_version_from_meson(meson_file: Path) -> str:
    """Extract version from meson.build file."""
    try:
        with open(meson_file, 'r') as f:
            content = f.read()
        
        # Match version in project() declaration
        pattern = r"project\s*\(\s*['\"]secrets['\"]\s*,\s*version\s*:\s*['\"]([^'\"]+)['\"]"
        match = re.search(pattern, content)
        
        if match:
            return match.group(1)
        else:
            raise ValueError("Could not find version in meson.build")
    except FileNotFoundError:
        raise FileNotFoundError(f"meson.build not found at {meson_file}")


def generate_python_version_file(version: str, output_file: Path) -> None:
    """Generate Python __init__.py with version."""
    content = f'''"""
Secrets - A GTK4/Libadwaita GUI for pass
"""

from .main import main

__version__ = "{version}"
__all__ = ["main"]
'''
    
    os.makedirs(output_file.parent, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(content)


def generate_app_info_file(version: str, output_file: Path) -> None:
    """Generate app_info.py with version."""
    content = f'''# Application Information

# This is a placeholder App ID.
# Replace it with your actual App ID, e.g., org.example.YourAppName
# It's crucial this ID is unique and follows reverse-DNS notation.
# See: https://developer.gnome.org/documentation/tutorials/application_id.html

import os

# Detect the environment and use appropriate app ID
def _get_app_id():
    # Check if running from Flatpak (will have FLATPAK_ID set)
    flatpak_id = os.environ.get('FLATPAK_ID')
    if flatpak_id:
        return flatpak_id
    
    # Default to base app ID for development/source builds
    return "io.github.tobagin.secrets"

APP_ID = _get_app_id()

VERSION = "{version}"

# Name of the gettext domain
# Usually, this is the same as your application ID or your project name
GETTEXT_DOMAIN = "io.github.tobagin.secrets"
'''
    
    os.makedirs(output_file.parent, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(content)


def validate_version(version: str) -> bool:
    """Validate version format (semantic versioning)."""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))


def main():
    """Main function to generate version files."""
    if len(sys.argv) < 2:
        print("Usage: generate_version.py <project_root> [output_dir]")
        sys.exit(1)
    
    project_root = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else project_root
    
    meson_file = project_root / "meson.build"
    
    try:
        # Extract version from meson.build
        version = extract_version_from_meson(meson_file)
        
        # Validate version format
        if not validate_version(version):
            print(f"Warning: Version '{version}' does not follow semantic versioning")
        
        print(f"Extracted version: {version}")
        
        # Generate version files
        init_file = output_dir / "src" / "secrets" / "__init__.py"
        app_info_file = output_dir / "src" / "secrets" / "app_info.py"
        
        generate_python_version_file(version, init_file)
        generate_app_info_file(version, app_info_file)
        
        print(f"Generated: {init_file}")
        print(f"Generated: {app_info_file}")
        print("Version files generated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()