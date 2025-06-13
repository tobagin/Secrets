python_sources = [
  '__init__.py',
  'application.py',
  'window.py',
  'app_info.py',
  'password_store.py',
  'edit_dialog.py'
]

install_data(python_sources, install_dir : python.get_install_dir() / 'secrets')

gnome = import('gnome')

# Compile GResources
# This creates a binary .gresource file and optionally C sources
# We want the binary .gresource file to be available.
gnome.compile_resources('secrets-resources', # Changed target name slightly
  'secrets.gresource.xml',
  source_dir: '../data', # Tells Meson where to find files listed in the XML (e.g., secrets.ui)
  install: true,
  install_dir: python.get_install_dir() / 'secrets' # Install .gresource file alongside Python module
)
