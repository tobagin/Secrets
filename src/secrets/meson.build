python = import('python')
py_mod = python.find_installation()
py_install_dir = py_mod.get_install_dir()

# Main module files
python_sources = [
  '__init__.py',
  '__main__.py',
  'application.py',
  'window.py',
  'app_info.py',
  'password_store.py',
  'models.py',
  'commands.py',
  'config.py',
  'async_operations.py',
  'error_handling.py',
  'performance.py',
  'main.py',
  'shortcuts_window.py',
  'i18n.py',
  'security_manager.py',
  'logging_system.py',
  'log_parser.py',
  'version.py',
  'build_info.py'
]

# UI module files
ui_sources = [
  'ui/__init__.py',
  'ui/components/__init__.py',
  'ui/components/header_bar.py',
  'ui/components/password_list.py',
  'ui/components/password_details.py',
  'ui/components/password_generator_popover.py',
  'ui/components/password_generator_widget.py',
  'ui/components/git_status_component.py',
  'ui/dialogs/__init__.py',
  'ui/dialogs/about_dialog.py',
  'ui/dialogs/folder_dialog.py',
  'ui/dialogs/password_dialog_utils.py',
  'ui/dialogs/password_dialog.py',
  'ui/dialogs/preferences_dialog.py',
  'ui/dialogs/password_generator_dialog.py',
  'ui/dialogs/import_export_dialog.py',
  'ui/dialogs/git_setup_dialog.py',
  'ui/dialogs/git_status_dialog.py',
  'ui/dialogs/lock_dialog.py',
  'ui/dialogs/password_details_dialog.py',
  'ui/dialogs/compliance_dashboard_dialog.py',
  'ui/widgets/__init__.py',
  'ui/widgets/color_paintable.py',
  'ui/widgets/password_row.py',
  'ui/widgets/password_entry_row.py',
  'ui/widgets/folder_expander_row.py',
]

# Controller files
controller_sources = [
  'controllers/__init__.py',
  'controllers/action_controller.py',
  'controllers/password_details_controller.py',
  'controllers/password_list_controller.py',
  'controllers/setup_controller.py',
  'controllers/window_state_manager.py',
  'controllers/window_controller.py',
  'controllers/dynamic_folder_controller.py'
]

# Setup wizard files
setup_wizard_sources = [
  'setup_wizard/__init__.py',
  'setup_wizard/dependencies_page.py',
  'setup_wizard/wizard_dialog.py',
  'setup_wizard/install_pass_page.py',
  'setup_wizard/create_gpg_page.py',
  'setup_wizard/setup_complete_page.py'
]

# Utility files
utils_sources = [
  'utils/__init__.py',
  'utils/ui_utils.py',
  'utils/system_utils.py',
  'utils/gpg_utils.py',
  'utils/path_validator.py',
  'utils/environment_setup.py',
  'utils/metadata_handler.py',
  'utils/url_extractor.py',
  'utils/avatar_manager.py',
  'utils/password_strength.py'
]

# Services files
services_sources = [
  'services/__init__.py',
  'services/password_service.py',
  'services/git_service.py',
  'services/password_content_parser.py'
]

# Managers files
managers_sources = [
  'managers/__init__.py',
  'managers/toast_manager.py',
  'managers/clipboard_manager.py',
  'managers/password_display_manager.py',
  'managers/search_manager.py',
  'managers/git_manager.py',
  'managers/favicon_manager.py',
  'managers/metadata_manager.py'
]

# Security files
security_sources = [
  'security/__init__.py',
  'security/secure_memory.py',
  'security/keyring_manager.py',
  'security/encrypted_config.py',
  'security/hardware_keys.py',
  'security/two_factor_auth.py',
  'security/cert_pinning.py',
  'security/audit_logger.py',
  'security/incident_response.py'
]

# Compliance files
compliance_sources = [
  'compliance/__init__.py',
  'compliance/compliance_manager.py',
  'compliance/hipaa/__init__.py',
  'compliance/hipaa/hipaa_compliance.py',
  'compliance/pci_dss/__init__.py',
  'compliance/pci_dss/pci_dss_compliance.py',
  'compliance/gdpr/__init__.py',
  'compliance/gdpr/gdpr_compliance.py'
]

# Install all Python files
install_data(python_sources, install_dir : py_install_dir / 'secrets')
install_data(ui_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(controller_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(setup_wizard_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(utils_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(services_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(managers_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(security_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(compliance_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)

# Compile GResources for Python: generate .gresource file, not C code
# Get the blueprint targets from the global variable if available
blueprint_targets = get_variable('all_blueprint_targets', [])

gresource = custom_target('secrets.gresource',
  input: 'secrets.gresource.xml',
  output: 'secrets.gresource',
  command: [
    find_program('glib-compile-resources'),
    '--target=@OUTPUT@',
    '--sourcedir', meson.project_build_root() / 'data',
    '--sourcedir', meson.project_source_root() / 'data',
    '@INPUT@'
  ],
  depends: blueprint_targets,
  install: true,
  install_dir: py_install_dir / 'secrets',
  build_by_default: true  # Ensure it's built for development
)

# Create a development environment setup
meson.add_devenv({
  'PYTHONPATH': meson.project_source_root() / 'src',
  'SECRETS_RESOURCE_PATH': meson.project_build_root() / 'src' / 'secrets' / 'secrets.gresource'
})
