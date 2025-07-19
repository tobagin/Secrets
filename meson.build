project('secrets', version : '0.8.13',
  meson_version : '>= 0.64.0', # Required for preserve_path and pure args
  default_options : ['warning_level=2', 'werror=false'])

python = import('python')

project_id = 'io.github.tobagin.secrets'

# Generate version files from meson.build as single source of truth
generate_version = find_program('scripts/generate_version.py')
sync_version = find_program('scripts/sync_version.py')

# Generate version files at configuration time
run_command(generate_version, meson.project_source_root(), check: true)

# Synchronize version across all project files
run_command(sync_version, check: false)  # Don't fail build if sync has warnings

subdir('data')
subdir('src/secrets')
subdir('po')

py_mod = python.find_installation(pure: false)

# Create a proper entry point script for development
configure_file(
  input: 'packaging/secrets-dev.in',
  output: 'secrets-dev',
  configuration: {
    'PYTHON': py_mod.full_path(),
    'PROJECT_ROOT': meson.project_source_root(),
  },
  install: false
)

# Create the main executable script for installation
configure_file(
  input: 'packaging/secrets.in',
  output: 'secrets-app',
  configuration: {
    'PYTHON': py_mod.full_path(),
    'APP_ID': meson.project_name(),
    'INSTALLED_PYTHONPATH': py_mod.get_install_dir(),
    'PROJECT_ID': project_id,
  },
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

# Executable for running directly (not for flatpak main binary)
run_target('secrets-dev',
  command: [py_mod, '-m', 'secrets.main'],
  env: {'PYTHONPATH': meson.project_source_root() / 'src'}
)
