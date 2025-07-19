"""
Version utilities for the Secrets application.
Provides centralized version access from meson.build as single source of truth.
"""

import re
from pathlib import Path
from typing import Optional


def get_version_from_meson() -> str:
    """
    Extract version from meson.build file as the single source of truth.
    
    Returns:
        str: The version string from meson.build, or "unknown" if not found
    """
    try:
        # Try to find meson.build in project root
        current_dir = Path(__file__).parent  # src/secrets/
        project_root = current_dir.parent.parent  # Go up to project root
        
        meson_file = project_root / "meson.build"
        if not meson_file.exists():
            # Alternative: go up from current directory until we find meson.build
            search_dir = current_dir
            while search_dir.parent != search_dir:
                meson_file = search_dir / "meson.build"
                if meson_file.exists():
                    break
                search_dir = search_dir.parent
            else:
                return "unknown"
        
        with open(meson_file, 'r') as f:
            content = f.read()
        
        # Match version in project() declaration
        pattern = r"project\s*\(\s*['\"]secrets['\"]\s*,\s*version\s*:\s*['\"]([^'\"]+)['\"]"
        match = re.search(pattern, content)
        
        if match:
            return match.group(1)
        else:
            return "unknown"
    except Exception:
        return "unknown"


# Cache the version for performance
_cached_version: Optional[str] = None


def get_version() -> str:
    """
    Get the application version from meson.build (cached for performance).
    
    Returns:
        str: The application version
    """
    global _cached_version
    if _cached_version is None:
        _cached_version = get_version_from_meson()
    return _cached_version


def refresh_version_cache() -> str:
    """
    Refresh the cached version by re-reading from meson.build.
    
    Returns:
        str: The refreshed version
    """
    global _cached_version
    _cached_version = None
    return get_version()


# Export the version for backward compatibility
VERSION = get_version()


# Make version available at module level
__version__ = VERSION