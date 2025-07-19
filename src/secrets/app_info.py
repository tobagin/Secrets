# Application Information

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
    
    # For production builds, use the stable app ID
    try:
        from .build_info import is_production_build
        if is_production_build():
            return "io.github.tobagin.secrets"
        else:
            # Development builds may use a dev suffix to avoid conflicts
            return "io.github.tobagin.secrets.dev"
    except ImportError:
        # Fallback if build_info not available
        return "io.github.tobagin.secrets"

APP_ID = _get_app_id()

# Import version from centralized source
from .version import get_version

VERSION = get_version()

# Name of the gettext domain
# Usually, this is the same as your application ID or your project name
GETTEXT_DOMAIN = "io.github.tobagin.secrets"
