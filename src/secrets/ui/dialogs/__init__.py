"""
Dialog components for the Secrets application.

This module contains all dialog-related classes.
"""

from .about_dialog import AboutDialog
from .password_dialog import PasswordDialog
from .folder_dialog import FolderDialog
from .preferences_dialog import PreferencesDialog
from .password_generator_dialog import PasswordGeneratorDialog
from .import_export_dialog import ImportExportDialog
from .compliance_dashboard_dialog import ComplianceDashboardDialog

__all__ = [
    'AboutDialog',
    'PasswordDialog',
    'FolderDialog',
    'PreferencesDialog',
    'PasswordGeneratorDialog',
    'ImportExportDialog',
    'ComplianceDashboardDialog'
]
