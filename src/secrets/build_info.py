"""
Build information and production mode detection.

This module provides utilities to detect whether the application is running
in development or production mode, and adjusts behavior accordingly.
"""

import os
from pathlib import Path
from typing import Optional

def is_production_build() -> bool:
    """
    Determine if this is a production build.
    
    Returns:
        True if running in production mode, False for development
    """
    # Check for Flatpak environment (production)
    if os.environ.get('FLATPAK_ID'):
        return True
    
    # Check for production environment variable
    if os.environ.get('SECRETS_PRODUCTION_MODE', '').lower() in ('1', 'true', 'yes'):
        return True
    
    # Check if we're in a typical development directory structure
    try:
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]  # Go up from src/secrets/
        
        # Development indicators
        dev_indicators = [
            project_root / 'meson.build',
            project_root / 'src',
            project_root / '.git',
            project_root / 'build'
        ]
        
        # If these exist, likely development
        if all(indicator.exists() for indicator in dev_indicators[:3]):
            return False
            
    except (OSError, IndexError):
        pass
    
    # Default to production for safety
    return True

def is_development_build() -> bool:
    """
    Determine if this is a development build.
    
    Returns:
        True if running in development mode, False for production
    """
    return not is_production_build()

def get_build_mode() -> str:
    """
    Get the current build mode as a string.
    
    Returns:
        'production' or 'development'
    """
    return 'development' if is_development_build() else 'production'

def should_enable_debug_features() -> bool:
    """
    Determine if debug features should be enabled.
    
    Returns:
        True if debug features should be enabled
    """
    # Explicitly enabled debug
    if os.environ.get('SECRETS_DEBUG_MODE', '').lower() in ('1', 'true', 'yes'):
        return True
    
    # Debug enabled in development by default
    return is_development_build()

def get_resource_search_paths() -> list:
    """
    Get appropriate resource search paths based on build mode.
    
    Returns:
        List of paths to search for resources, prioritized for current mode
    """
    paths = []
    
    if is_development_build():
        # Development paths first
        if 'SECRETS_RESOURCE_PATH' in os.environ:
            paths.append(os.environ['SECRETS_RESOURCE_PATH'])
        
        # Try common development build locations
        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parents[2]
            dev_path = project_root / "build" / "src" / "secrets" / "secrets.gresource"
            paths.append(str(dev_path))
        except (OSError, IndexError):
            pass
    
    # Production/installed paths
    try:
        module_dir = Path(__file__).parent
        module_adjacent = module_dir / "secrets.gresource"
        paths.append(str(module_adjacent))
    except OSError:
        pass
    
    return paths

def filter_log_level_for_production(requested_level: str) -> str:
    """
    Filter log level based on production mode.
    
    In production, prevent DEBUG level logging for security.
    
    Args:
        requested_level: The requested log level
        
    Returns:
        Appropriate log level for current build mode
    """
    if is_production_build() and requested_level.upper() == 'DEBUG':
        # Force INFO as minimum level in production
        return 'INFO'
    
    return requested_level

def get_localization_search_paths(po_dir: Optional[str] = None) -> list:
    """
    Get appropriate localization search paths based on build mode.
    
    Args:
        po_dir: Development po directory path
        
    Returns:
        List of paths to search for localization files
    """
    paths = []
    
    if is_development_build() and po_dir:
        # Development: try local po directory first
        if os.path.exists(po_dir) and os.path.exists(os.path.join(po_dir, 'LINGUAS')):
            paths.append(po_dir)
    
    # Production/system paths
    # Let gettext find system directories (None means system paths)
    paths.append(None)
    
    return paths