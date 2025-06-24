import sys
import os # Added
import warnings
import gi

# Suppress the module name conflict warning
warnings.filterwarnings("ignore", message=".*'secrets.main' found in sys.modules.*")

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio # Added Gio
from .application import SecretsApplication
from .app_info import APP_ID, GETTEXT_DOMAIN
from .i18n import setup_i18n
from .utils.gpg_utils import GPGSetupHelper

import gettext

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Initialize localization
    # For development, try to use local po directory
    # For installed version, let gettext find system directories
    try:
        # Check if we're running from source directory
        source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        po_dir = os.path.join(source_dir, 'po')

        if os.path.exists(po_dir) and os.path.exists(os.path.join(po_dir, 'LINGUAS')):
            # Running from source, use local po directory
            setup_i18n(po_dir)
        else:
            # Running from installation, use system directories
            setup_i18n()
    except Exception as e:
        print(f"Could not set up localization: {e}")
        # Fallback setup
        setup_i18n()

    # Load GResources
    # Construct the path to the .gresource file.
    module_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(module_dir, ".."))

    # List of paths to check for the gresource file
    resource_paths_to_try = []

    # Path 1: Check if meson devenv set a specific path
    if 'SECRETS_RESOURCE_PATH' in os.environ:
        resource_paths_to_try.append(os.environ['SECRETS_RESOURCE_PATH'])

    # Path 2: Development path in a typical Meson build directory (e.g., 'build')
    # This assumes 'secrets.gresource' is generated in 'build/secrets/'
    dev_resource_path = os.path.join(project_root, "build", "secrets", "secrets.gresource")
    resource_paths_to_try.append(dev_resource_path)

    # Path 3: Next to the module (e.g., if installed or built in-tree and copied)
    module_adjacent_resource_path = os.path.join(module_dir, "secrets.gresource")
    resource_paths_to_try.append(module_adjacent_resource_path)

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

    # Configure GPG environment for Flatpak compatibility
    try:
        GPGSetupHelper.ensure_gui_pinentry()
    except Exception as e:
        print(f"Warning: Could not configure GPG environment: {e}")

    app = SecretsApplication(application_id=APP_ID)
    return app.run(argv)

if __name__ == "__main__":
    sys.exit(main())
