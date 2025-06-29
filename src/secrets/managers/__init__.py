"""
Managers package for the Secrets application.
"""

from .toast_manager import ToastManager
from .clipboard_manager import ClipboardManager
from .password_display_manager import PasswordDisplayManager
from .search_manager import SearchManager
from .git_manager import GitManager, GitPlatformManager
from .favicon_manager import FaviconManager, get_favicon_manager
from .metadata_manager import MetadataManager

__all__ = [
    'ToastManager',
    'ClipboardManager',
    'PasswordDisplayManager',
    'SearchManager',
    'GitManager',
    'GitPlatformManager',
    'FaviconManager',
    'get_favicon_manager',
    'MetadataManager'
]
