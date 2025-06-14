project('secrets', version : '0.1.0',
  meson_version : '>= 0.64.0', # bump to match your usage of 'pure'
  default_options : ['warning_level=2', 'werror=false'])

python = import('python')

project_id = 'io.github.tobagin.secrets' # Placeholder App ID

subdir('secrets')
subdir('data')
subdir('po')

py_mod = python.find_installation(pure: false)

# Executable for running directly (not for flatpak main binary)
run_target('secrets-dev',
  command: [py_mod, 'secrets/__init__.py']
)
