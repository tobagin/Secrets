#!/usr/bin/env python3
"""
Update Flatpak dependencies to their latest versions.

This script automatically checks PyPI for the latest versions of Python packages
used in the Flatpak manifest and updates the URLs and SHA256 hashes accordingly.
"""

import json
import re
import sys
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, status: str = "info"):
    """Print colored status message."""
    colors = {
        "info": Colors.BLUE,
        "success": Colors.GREEN,
        "warning": Colors.YELLOW,
        "error": Colors.RED
    }
    color = colors.get(status, Colors.BLUE)
    print(f"{color}{'✓' if status == 'success' else '•'} {message}{Colors.END}")

def get_latest_version(package_name: str) -> Optional[Dict]:
    """Get the latest version info for a package from PyPI."""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        latest_version = data['info']['version']
        releases = data['releases'][latest_version]
        
        # Find the wheel file (prefer py3-none-any)
        wheel_file = None
        for release in releases:
            if release['filename'].endswith('-py3-none-any.whl'):
                wheel_file = release
                break
        
        if not wheel_file:
            # Fallback to any wheel file
            for release in releases:
                if release['filename'].endswith('.whl'):
                    wheel_file = release
                    break
        
        if wheel_file:
            return {
                'version': latest_version,
                'url': wheel_file['url'],
                'sha256': wheel_file['digests']['sha256'],
                'filename': wheel_file['filename']
            }
        
        return None
        
    except Exception as e:
        print_status(f"Error fetching {package_name}: {e}", "error")
        return None

def parse_flatpak_manifest(manifest_path: Path) -> List[str]:
    """Parse the Flatpak manifest and extract Python package dependencies."""
    with open(manifest_path, 'r') as f:
        content = f.read()

    # Find Python package modules
    packages = []

    # Look for existing wheel URLs to extract package names
    url_pattern = r'url: https://files\.pythonhosted\.org/packages/[^/]+/[^/]+/[^/]+/([a-zA-Z0-9_-]+)-([^-]+)-py3-none-any\.whl'
    url_matches = re.findall(url_pattern, content)

    for package_name, version in url_matches:
        # Skip local packages and invalid names
        if not package_name.startswith('file:') and package_name.replace('_', '-').isalnum() or '-' in package_name:
            if package_name not in packages:
                packages.append(package_name)

    return packages

def update_manifest_dependency(manifest_path: Path, package_name: str, new_info: Dict) -> bool:
    """Update a specific dependency in the Flatpak manifest."""
    with open(manifest_path, 'r') as f:
        content = f.read()
    
    # Pattern to match the file entry for this package
    pattern = rf'(\s+- type: file\s+url: https://files\.pythonhosted\.org/packages/[^/]+/[^/]+/[^/]+/{re.escape(package_name)}-[^-]+-py3-none-any\.whl\s+sha256: [a-f0-9]+)'
    
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        old_entry = match.group(1)
        new_entry = f"""      - type: file
        url: {new_info['url']}
        sha256: {new_info['sha256']}"""
        
        updated_content = content.replace(old_entry, new_entry)
        
        with open(manifest_path, 'w') as f:
            f.write(updated_content)
        
        return True
    
    return False

def main():
    """Main function to update Flatpak dependencies."""
    print_status("🔄 Updating Flatpak dependencies to latest versions", "info")
    print()
    
    # Find the Flatpak manifest
    manifest_path = Path("io.github.tobagin.secrets.yml")
    if not manifest_path.exists():
        print_status("Flatpak manifest not found!", "error")
        sys.exit(1)
    
    # Parse the manifest to find Python packages
    packages = parse_flatpak_manifest(manifest_path)
    
    if not packages:
        print_status("No Python packages found in manifest", "warning")
        return
    
    print_status(f"Found {len(packages)} Python packages to check:", "info")
    for pkg in packages:
        print(f"  • {pkg}")
    print()
    
    updates_made = 0
    
    for package_name in packages:
        print_status(f"Checking {package_name}...", "info")
        
        latest_info = get_latest_version(package_name)
        if not latest_info:
            print_status(f"Could not get latest version for {package_name}", "warning")
            continue
        
        # Check if we need to update
        with open(manifest_path, 'r') as f:
            content = f.read()
        
        current_version_match = re.search(rf'{re.escape(package_name)}-([^-]+)-py3-none-any\.whl', content)
        if current_version_match:
            current_version = current_version_match.group(1)
            
            if current_version == latest_info['version']:
                print_status(f"{package_name} is already up to date ({current_version})", "success")
                continue
            
            print_status(f"Updating {package_name}: {current_version} → {latest_info['version']}", "info")
            
            if update_manifest_dependency(manifest_path, package_name, latest_info):
                print_status(f"Updated {package_name} to {latest_info['version']}", "success")
                updates_made += 1
            else:
                print_status(f"Failed to update {package_name}", "error")
        else:
            print_status(f"Could not find current version for {package_name}", "warning")
    
    print()
    if updates_made > 0:
        print_status(f"✨ Updated {updates_made} package(s) in Flatpak manifest", "success")
        print_status("Remember to test the build and commit the changes!", "info")
    else:
        print_status("All packages are already up to date!", "success")

if __name__ == "__main__":
    main()
