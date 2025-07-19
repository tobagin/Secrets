import sys
import os # Added
import warnings
import gi
import logging

# Suppress the module name conflict warning
warnings.filterwarnings("ignore", message=".*'secrets.main' found in sys.modules.*")

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio # Added Gio
from .application import SecretsApplication
from .app_info import APP_ID, GETTEXT_DOMAIN
from .i18n import setup_i18n
from .utils.gpg_utils import GPGSetupHelper
from .build_info import get_resource_search_paths, get_localization_search_paths, is_development_build

import gettext

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Set up enhanced logging for early initialization 
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s [%(levelname)8s] %(name)s[%(module)s:%(funcName)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    # Initialize localization based on build mode
    try:
        if is_development_build():
            # Development mode: try local po directory first
            source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            po_dir = os.path.join(source_dir, 'po')
            localization_paths = get_localization_search_paths(po_dir)
        else:
            # Production mode: use system directories only
            localization_paths = get_localization_search_paths()
        
        # Try each path in order
        setup_successful = False
        for path in localization_paths:
            try:
                setup_i18n(path)
                setup_successful = True
                break
            except Exception:
                continue
        
        if not setup_successful:
            # Final fallback
            setup_i18n()
            
    except Exception as e:
        logger.warning(f"Could not set up localization: {e}")
        # Fallback setup
        setup_i18n()

    # Load GResources based on build mode
    resource_paths_to_try = get_resource_search_paths()

    loaded_successfully = False
    for res_path in resource_paths_to_try:
        if os.path.exists(res_path):
            try:
                resource = Gio.Resource.load(res_path)
                Gio.Resource._register(resource) # Use _register for PyGObject
                if is_development_build():
                    logger.info(f"Loaded GResource from {res_path}")
                else:
                    logger.debug(f"Loaded GResource from {res_path}")
                loaded_successfully = True
                break # Stop searching once loaded
            except Exception as e:
                logger.error(f"Error loading GResource from {res_path}: {e}")

    if not loaded_successfully:
        if is_development_build():
            logger.error(f"GResource file (secrets.gresource) not found in checked paths: {resource_paths_to_try}. UI templates may fail.")
        else:
            logger.error("GResource file not found. UI templates may fail.")
            # In production, this is a critical error
            sys.exit(1)

    # Configure GPG environment for Flatpak compatibility
    try:
        GPGSetupHelper.ensure_gui_pinentry()
    except Exception as e:
        logger.warning(f"Could not configure GPG environment: {e}")

    app = SecretsApplication(application_id=APP_ID)
    return app.run(argv)

if __name__ == "__main__":
    sys.exit(main())
