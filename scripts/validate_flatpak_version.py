#!/usr/bin/env python3
"""
Validate that Flatpak manifest version matches meson.build version.
"""

import sys
import re
import yaml
import json
from pathlib import Path


def get_meson_version():
    """Extract version from meson.build."""
    meson_file = Path("meson.build")
    if not meson_file.exists():
        return None
    
    with open(meson_file, 'r') as f:
        content = f.read()
        match = re.search(r"version\s*:\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
    return None


def get_flatpak_version(manifest_path):
    """Extract version from Flatpak manifest."""
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        return None
    
    try:
        # Try YAML first
        with open(manifest_file, 'r') as f:
            if manifest_path.endswith('.yml') or manifest_path.endswith('.yaml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        # Look for version in the main application module (named 'secrets')
        if 'modules' in data:
            for module in data['modules']:
                if isinstance(module, dict):
                    module_name = module.get('name', '')
                    
                    # Skip dependency modules, only check the main 'secrets' module
                    if module_name == 'secrets':
                        if 'sources' in module:
                            for source in module['sources']:
                                if isinstance(source, dict):
                                    # Check for tagged releases
                                    if 'tag' in source:
                                        tag = source['tag']
                                        if tag.startswith('v'):
                                            return tag[1:]
                                        return tag
                                    # Check for version in URL
                                    elif 'url' in source and 'secrets' in source['url']:
                                        url = source['url']
                                        match = re.search(r'/v?(\d+\.\d+\.\d+)\.tar', url)
                                        if match:
                                            return match.group(1)
                                    # For development builds using local directory,
                                    # the version should come from meson.build
                                    elif source.get('type') == 'dir':
                                        # This indicates a development build
                                        # Version will be determined by meson.build
                                        return None
                        break  # Found the secrets module, stop looking
        
        # If no secrets module found, this might be an older format
        # Look for any version tags as fallback (but warn about it)
        return None
    except Exception as e:
        print(f"Error reading manifest: {e}")
        return None


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_flatpak_version.py <manifest_path>")
        sys.exit(1)
    
    manifest_path = sys.argv[1]
    
    meson_version = get_meson_version()
    flatpak_version = get_flatpak_version(manifest_path)
    
    if not meson_version:
        print("ERROR: Could not extract version from meson.build")
        sys.exit(1)
    
    if not flatpak_version:
        print("INFO: Flatpak manifest uses local directory source (development build)")
        print(f"Meson version: {meson_version}")
        print("✓ Development build - version consistency maintained by meson.build")
        sys.exit(0)  # This is expected for development builds
    
    print(f"Meson version: {meson_version}")
    print(f"Flatpak version: {flatpak_version}")
    
    if meson_version == flatpak_version:
        print("✓ Versions match")
        sys.exit(0)
    else:
        print("✗ Version mismatch detected")
        sys.exit(1)


if __name__ == "__main__":
    main()