"""
Setup wizard package for the Secrets application.

This package contains the setup wizard components for guiding users through
the initial configuration of pass and GPG.
"""

from .dependencies_page import DependenciesPage
from .wizard_dialog import SetupWizard
from .install_pass_page import InstallPassPage
from .create_gpg_page import CreateGpgPage
from .setup_complete_page import SetupCompletePage

__all__ = [
    'DependenciesPage',
    'SetupWizard',
    'InstallPassPage',
    'CreateGpgPage',
    'SetupCompletePage'
]
