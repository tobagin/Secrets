"""
Dialog components for the Secrets application.

This module contains all dialog-related classes.
"""

from .about_dialog import AboutDialog
from .add_password_dialog import AddPasswordDialog
from .edit_password_dialog import EditPasswordDialog
from .add_folder_dialog import AddFolderDialog
from .edit_folder_dialog import EditFolderDialog
from .preferences_dialog import PreferencesDialog
from .password_generator_dialog import PasswordGeneratorDialog
from .import_export_dialog import ImportExportDialog

__all__ = [
    'AboutDialog',
    'AddPasswordDialog',
    'EditPasswordDialog',
    'AddFolderDialog',
    'EditFolderDialog',
    'PreferencesDialog',
    'PasswordGeneratorDialog',
    'ImportExportDialog'
]
