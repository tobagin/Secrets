project('secrets', version : '0.1.0',
  meson_version : '>= 0.59.0',
  default_options : ['warning_level=2', 'werror=false'])

python = import('python')

project_id = 'io.github.tobagin.secrets' # Placeholder App ID

subdir('secrets')
subdir('data')
subdir('po')

python.find_installation(pure: false)

# Executable for running directly (not for flatpak main binary)
executable('secrets-dev',
  'secrets/__init__.py', # Assuming main entry point will be here
  dependencies: [
    dependency('gtk4', version: '>=4.8'),
    dependency('libadwaita-1', version: '>=1.2')
  ],
  install: false # This is for development
)

meson.add_install_script('meson_post_install.py')
