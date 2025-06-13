import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from .application import SecretsApplication
from .app_info import APP_ID, GETTEXT_DOMAIN

import gettext

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Initialize localization
    # Adjust the localedir if your .mo files are in a different location
    # For a Flatpak, this might be /app/share/locale
    # For local development, it might be different.
    # Meson typically handles installation to the correct system paths.
    try:
        localedir = None # Let gettext find it, or specify if needed
        # Example for development: os.path.join(os.path.dirname(__file__), '..', 'po')
        # However, during installation, meson places it in standard system dirs.
        gettext.bindtextdomain(GETTEXT_DOMAIN, localedir)
        gettext.textdomain(GETTEXT_DOMAIN)
    except Exception as e:
        print(f"Could not set up localization: {e}")


    app = SecretsApplication(application_id=APP_ID)
    return app.run(argv)

if __name__ == "__main__":
    sys.exit(main())
