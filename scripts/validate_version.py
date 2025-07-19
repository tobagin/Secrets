#!/usr/bin/env python3
"""
Validate version consistency across all project files

This script ensures that all version references in the project
are consistent with the single source of truth in meson.build.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


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


def check_file_version(file_path: Path, patterns: List[str]) -> Tuple[bool, str]:
    """Check if a file contains the expected version."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        for pattern in patterns:
            # Check for dynamic version usage first
            if "get_version()" in pattern:
                if re.search(pattern, content):
                    return True, "get_version()"
            else:
                # Check for static version
                matches = re.findall(pattern, content)
                if matches:
                    return True, matches[0]
        
        return False, "Version pattern not found"
    except Exception as e:
        return False, f"Error reading file: {e}"


def validate_flatpak_manifest(project_root: Path, expected_version: str) -> Tuple[bool, List[str]]:
    """Validate Flatpak manifest versions (only for secrets app itself, not dependencies)."""
    issues = []
    
    # Check main Flatpak manifest
    manifest_file = project_root / "packaging" / "flatpak" / "io.github.tobagin.secrets.yml"
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            content = f.read()
        
        # Only check for secrets-specific version references (near the main source)
        # Look for our project's tag in the main source section
        secrets_source_pattern = r'- name:\s*secrets.*?tag:\s*v?([0-9]+\.[0-9]+\.[0-9]+)'
        match = re.search(secrets_source_pattern, content, re.DOTALL)
        
        if match:
            tag_version = match.group(1)
            if tag_version != expected_version:
                issues.append(f"Flatpak manifest secrets tag version mismatch: {tag_version} vs {expected_version}")
        # If no secrets source tag found, that's actually OK for now
    
    return len(issues) == 0, issues


def main():
    """Main validation function."""
    project_root = Path.cwd()
    
    try:
        # Get the authoritative version from meson.build
        expected_version = get_version_from_meson(project_root)
        print(f"Expected version (from meson.build): {expected_version}")
        print("=" * 50)
        
        all_good = True
        issues = []
        
        # Files to check with their version patterns
        files_to_check = [
            {
                'path': project_root / "src" / "secrets" / "__init__.py",
                'patterns': [
                    r'__version__\s*=\s*get_version\(\)'      # Dynamic version (check first)
                ],
                'name': '__init__.py',
                'dynamic': True
            },
            {
                'path': project_root / "src" / "secrets" / "app_info.py",
                'patterns': [
                    r'VERSION\s*=\s*get_version\(\)'         # Dynamic version (check first)
                ],
                'name': 'app_info.py',
                'dynamic': True
            }
        ]
        
        # Check each file
        for file_info in files_to_check:
            found, version_or_error = check_file_version(file_info['path'], file_info['patterns'])
            
            if found:
                # For dynamic versions, check if it uses get_version()
                if file_info.get('dynamic', False) and version_or_error == "get_version()":
                    print(f"✓ {file_info['name']}: uses centralized version (get_version())")
                elif version_or_error == expected_version:
                    print(f"✓ {file_info['name']}: {version_or_error}")
                else:
                    # Check if this is a dynamic version pattern match (whole line)
                    if "get_version()" in version_or_error:
                        print(f"✓ {file_info['name']}: uses centralized version (get_version())")
                    else:
                        print(f"✗ {file_info['name']}: {version_or_error} (expected {expected_version})")
                        all_good = False
                        issues.append(f"{file_info['name']} version mismatch: {version_or_error} vs {expected_version}")
            else:
                print(f"✗ {file_info['name']}: {version_or_error}")
                all_good = False
                issues.append(f"{file_info['name']}: {version_or_error}")
        
        # Check Flatpak manifest
        flatpak_ok, flatpak_issues = validate_flatpak_manifest(project_root, expected_version)
        if flatpak_ok:
            print("✓ Flatpak manifest: OK")
        else:
            print("✗ Flatpak manifest: Issues found")
            all_good = False
            issues.extend(flatpak_issues)
        
        print("=" * 50)
        
        if all_good:
            print("🎉 All version references are consistent!")
            sys.exit(0)
        else:
            print("❌ Version inconsistencies found:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nRun 'python3 scripts/generate_version.py .' to fix Python files.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()