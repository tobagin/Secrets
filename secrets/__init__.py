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
    # This assumes the .gresource file is installed in the same directory as the Python module.
    module_path = os.path.dirname(__file__)
    resource_file_path = os.path.join(module_path, "secrets-resources.gresource") # Match Meson target name

    if os.path.exists(resource_file_path):
        try:
            resource = Gio.Resource.load(resource_file_path)
            Gio.Resource._register(resource) # Use _register for PyGObject
            print(f"Loaded GResource from {resource_file_path}")
        except Exception as e:
            print(f"Error loading GResource {resource_file_path}: {e}", file=sys.stderr)
            # Fallback for development if .gresource isn't in module dir yet
            # This might be when running directly from source without full installation
            dev_resource_path = os.path.join(os.path.dirname(__file__), '..', 'builddir', 'secrets', 'secrets-resources.gresource') # Adjust path based on actual build output
            if os.path.exists(dev_resource_path):
                 try:
                    resource = Gio.Resource.load(dev_resource_path)
                    Gio.Resource._register(resource)
                    print(f"Loaded GResource from development path {dev_resource_path}")
                 except Exception as e_dev:
                    print(f"Error loading GResource from dev path {dev_resource_path}: {e_dev}", file=sys.stderr)
            else:
                print(f"GResource file not found at {resource_file_path} or typical dev paths.", file=sys.stderr)
    else:
        # This path is more likely during development if meson directly puts it in source tree adjacent to module
        # Or if running uninstalled from build directory.
        # This logic can get complex depending on how the project is run (installed vs. uninstalled).
        # A common pattern for uninstalled is to use environment variables set by meson devenv.
        resource_path_uninstalled = os.path.join(os.path.dirname(__file__), "secrets-resources.gresource") # if meson puts it next to .py files in build dir
        if os.path.exists(resource_path_uninstalled):
            try:
                resource = Gio.Resource.load(resource_path_uninstalled)
                Gio.Resource._register(resource)
                print(f"Loaded GResource from uninstalled path {resource_path_uninstalled}")
            except Exception as e_uninstalled:
                print(f"Error loading GResource from {resource_path_uninstalled}: {e_uninstalled}", file=sys.stderr)
        else:
            print(f"GResource file not found at primary path: {resource_file_path}. UI templates may fail.", file=sys.stderr)

    app = SecretsApplication(application_id=APP_ID)
    return app.run(argv)

if __name__ == "__main__":
    sys.exit(main())
