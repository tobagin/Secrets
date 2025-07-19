"""
Internationalization (i18n) support for Secrets application.

This module provides translation functions and utilities.
"""

import gettext
import os
from typing import Optional

from .app_info import GETTEXT_DOMAIN

# Import logging for warnings
try:
    from .logging_system import get_logger, LogCategory
    logger = get_logger(LogCategory.APPLICATION, "i18n")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Global translation function
_: Optional[callable] = None


def setup_i18n(localedir: Optional[str] = None) -> None:
    """
    Set up internationalization for the application.

    Args:
        localedir: Directory containing translation files. If None,
                  gettext will search in standard system directories.
    """
    global _

    try:
        # Set up gettext
        if localedir:
            # For development, look for .mo files in build directory structure
            import os
            build_locale_dir = None

            # Check if we have a build with compiled translations
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            build_locale = os.path.join(project_root, 'build', 'po')

            if os.path.exists(build_locale):
                build_locale_dir = build_locale

            translation = gettext.translation(
                GETTEXT_DOMAIN,
                localedir=build_locale_dir or localedir,
                fallback=True
            )
        else:
            # Let gettext find the locale directory automatically
            translation = gettext.translation(GETTEXT_DOMAIN, fallback=True)

        # Install the translation function globally
        _ = translation.gettext

        # Also bind to the standard gettext domain
        gettext.bindtextdomain(GETTEXT_DOMAIN, localedir)
        gettext.textdomain(GETTEXT_DOMAIN)

    except Exception as e:
        logger.warning("Failed to set up translations", extra={'error': str(e)})
        # Fallback to identity function
        _ = lambda x: x


def get_translation_function():
    """Get the translation function."""
    global _
    if _ is None:
        setup_i18n()
    return _


def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Return the appropriate plural form of a message.
    
    Args:
        singular: Singular form of the message
        plural: Plural form of the message  
        n: Number to determine which form to use
        
    Returns:
        Translated message in appropriate form
    """
    try:
        translation = gettext.translation(GETTEXT_DOMAIN, fallback=True)
        return translation.ngettext(singular, plural, n)
    except Exception:
        # Fallback to simple English pluralization
        return singular if n == 1 else plural


# Convenience function for marking strings for translation
# This is used in code where we want to mark strings for extraction
# but delay actual translation until runtime
def N_(message: str) -> str:
    """Mark a string for translation without translating it."""
    return message
