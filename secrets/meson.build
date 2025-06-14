python = import('python')
py_mod = python.find_installation()
py_install_dir = py_mod.get_install_dir()

python_sources = [
  '__init__.py',
  'application.py',
  'window.py',
  'app_info.py',
  'password_store.py',
  'edit_dialog.py',
  'move_rename_dialog.py',
  'add_password_dialog.py',
  'models.py',
  'managers.py',
  'services.py',
  'commands.py',
  'config.py',
  'async_operations.py',
  'error_handling.py',
  'performance.py'
]

install_data(python_sources, install_dir : py_install_dir / 'secrets')

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
  install_dir: py_install_dir / 'secrets'
)
