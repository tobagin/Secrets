project('secrets', version : '0.1.0',
  meson_version : '>= 0.64.0', # bump to match your usage of 'pure'
  default_options : ['warning_level=2', 'werror=false'])

python = import('python')

project_id = 'io.github.tobagin.secrets' # Placeholder App ID

subdir('secrets')
subdir('data')
subdir('po')

py_mod = python.find_installation(pure: false)

# Create a proper entry point script for development
configure_file(
  input: 'secrets-dev.in',
  output: 'secrets-dev',
  configuration: {
    'PYTHON': py_mod.full_path(),
    'PROJECT_ROOT': meson.project_source_root(),
  },
  install: false
)

# Executable for running directly (not for flatpak main binary)
run_target('secrets-dev',
  command: [py_mod, '-m', 'secrets.main'],
  env: {'PYTHONPATH': meson.project_source_root()}
)
