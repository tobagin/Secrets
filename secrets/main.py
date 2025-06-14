import sys
import os # Added
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio # Added Gio
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

    # Load GResources
    # Construct the path to the .gresource file.
    module_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(module_dir, ".."))

    # List of paths to check for the gresource file
    # Path 1: Development path in a typical Meson build directory (e.g., 'builddir')
    # This assumes 'secrets.gresource' is generated in 'builddir/secrets/'
    dev_resource_path = os.path.join(project_root, "builddir", "secrets", "secrets.gresource")
    # Path 2: Next to the module (e.g., if installed or built in-tree and copied)
    module_adjacent_resource_path = os.path.join(module_dir, "secrets.gresource")

    resource_paths_to_try = [
        dev_resource_path,              # Try typical development path first
        module_adjacent_resource_path,  # Then try path next to the module
    ]

    loaded_successfully = False
    for res_path in resource_paths_to_try:
        if os.path.exists(res_path):
            try:
                resource = Gio.Resource.load(res_path)
                Gio.Resource._register(resource) # Use _register for PyGObject
                print(f"Loaded GResource from {res_path}")
                loaded_successfully = True
                break # Stop searching once loaded
            except Exception as e:
                print(f"Error loading GResource from {res_path}: {e}", file=sys.stderr)

    if not loaded_successfully:
        print(f"GResource file (secrets.gresource) not found in checked paths: {resource_paths_to_try}. UI templates may fail.", file=sys.stderr)
        # Depending on strictness, you might want to sys.exit(1) here if GResource is critical

    app = SecretsApplication(application_id=APP_ID)
    return app.run(argv)

if __name__ == "__main__":
    sys.exit(main())
