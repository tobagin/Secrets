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
  'managers.py',
  'commands.py',
  'config.py',
  'async_operations.py',
  'error_handling.py',
  'performance.py',
  'main.py',
  'shortcuts_window.py',
  'i18n.py'
]

# UI module files
ui_sources = [
  'ui/__init__.py',
  'ui/components/__init__.py',
  'ui/components/header_bar.py',
  'ui/components/password_list.py',
  'ui/components/password_details.py',
  'ui/components/password_generator_popover.py',
  'ui/components/git_status_component.py',
  'ui/dialogs/__init__.py',
  'ui/dialogs/add_password_dialog.py',
  'ui/dialogs/edit_password_dialog.py',
  'ui/dialogs/preferences_dialog.py',
  'ui/dialogs/password_generator_dialog.py',
  'ui/dialogs/import_export_dialog.py',
  'ui/dialogs/git_setup_dialog.py',
  'ui/dialogs/git_status_dialog.py',
  'ui/widgets/__init__.py'
]

# Controller files
controller_sources = [
  'controllers/__init__.py',
  'controllers/action_controller.py',
  'controllers/password_details_controller.py',
  'controllers/password_list_controller.py',
  'controllers/setup_controller.py',
  'controllers/window_state_manager.py',
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
  'utils/gpg_utils.py'
]

# Services files
services_sources = [
  'services/__init__.py',
  'services/password_service.py',
  'services/git_service.py'
]

# Managers files
managers_sources = [
  'managers/__init__.py',
  'managers/toast_manager.py',
  'managers/clipboard_manager.py',
  'managers/password_display_manager.py',
  'managers/search_manager.py',
  'managers/git_manager.py'
]

# Install all Python files
install_data(python_sources, install_dir : py_install_dir / 'secrets')
install_data(ui_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(controller_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(setup_wizard_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(utils_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(services_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)
install_data(managers_sources, install_dir : py_install_dir / 'secrets', preserve_path: true)

# Compile GResources for Python: generate .gresource file, not C code
gresource = custom_target('secrets.gresource',
  input: 'secrets.gresource.xml',
  output: 'secrets.gresource',
  command: [
    find_program('glib-compile-resources'),
    '--target=@OUTPUT@',
    '--sourcedir', meson.project_source_root() / 'data',
    '@INPUT@'
  ],
  install: true,
  install_dir: py_install_dir / 'secrets',
  build_by_default: true  # Ensure it's built for development
)

# Create a development environment setup
meson.add_devenv({
  'PYTHONPATH': meson.project_source_root(),
  'SECRETS_RESOURCE_PATH': meson.project_build_root() / 'secrets' / 'secrets.gresource'
})
