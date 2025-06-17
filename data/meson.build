i18n = import('i18n')

# Get project_id from the main meson.build file
# This requires project_id to be defined in the root meson.build
# For simplicity here, we'll redefine it or assume it's 'com.example.secrets'
# A better way is to pass it via subproject_options or get it from project_source_root()
# if it matches the app_id.
app_id = get_variable('project_id', 'io.github.tobagin.secrets')


# UI files and CSS - organized structure
# Main UI files
install_data(
  ['ui/main_window.ui', 'style.css'],
  install_dir: get_option('datadir') / app_id / 'ui'
)

# Component UI files
install_data(
  ['ui/components/header_bar.ui', 'ui/components/password_list.ui',
   'ui/components/password_details.ui', 'ui/components/main_menu.ui',
   'ui/components/password_generator_popover.ui'],
  install_dir: get_option('datadir') / app_id / 'ui' / 'components'
)

# Dialog UI files
install_data(
  ['ui/dialogs/add_password_dialog.ui', 'ui/dialogs/edit_password_dialog.ui',
   'ui/dialogs/add_folder_dialog.ui'],
  install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
)

# Setup wizard UI files
install_data(
  ['ui/setup/setup_wizard.ui', 'ui/setup/wizard_dialog.ui', 'ui/setup/dependencies_page.ui',
   'ui/setup/install_pass_page.ui', 'ui/setup/create_gpg_page.ui', 'ui/setup/setup_complete_page.ui'],
  install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
)

# .desktop file
desktop_file_name = app_id + '.desktop'
desktop_file_input = 'io.github.tobagin.secrets.desktop.in' # Keep consistent with file to be created

i18n.merge_file(
  input: desktop_file_input,
  output: desktop_file_name,
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'applications'
)

desktop_utils = find_program('desktop-file-validate', required : false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args : ['--no-hints', desktop_file_name])
endif

# AppStream metadata
appstream_file_name = app_id + '.appdata.xml'
appstream_file_input = 'io.github.tobagin.secrets.appdata.xml.in'

i18n.merge_file(
  input: appstream_file_input,
  output: appstream_file_name,
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

appstream_util = find_program('appstream-util', required : false)
if appstream_util.found()
  test('Validate appstream file', appstream_util, args : ['validate', '--nonet', appstream_file_name])
endif

# Icons
# Scalable SVG icon (fallback)
install_data(
  'icons/io.github.tobagin.secrets.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
  rename: app_id + '.svg'
)

# PNG icons in multiple sizes
icon_sizes = ['16x16', '22x22', '24x24', '32x32', '48x48', '64x64', '96x96', '128x128', '256x256', '512x512']

foreach size : icon_sizes
  install_data(
    'icons' / size / (app_id + '.png'),
    install_dir: get_option('datadir') / 'icons' / 'hicolor' / size / 'apps',
    rename: app_id + '.png'
  )
endforeach

# Symbolic icons
install_data(
  'icons/symbolic/io.github.tobagin.secrets-cloud-download-symbolic.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'symbolic' / 'apps'
)

install_data(
  'icons/symbolic/io.github.tobagin.secrets-cloud-upload-symbolic.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'symbolic' / 'apps'
)

install_data(
  'icons/symbolic/io.github.tobagin.secrets-verified-symbolic.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'symbolic' / 'apps'
)

# GSettings (if you add them later)
# gsettings_schemas = files('com.example.secrets.gschema.xml') # Placeholder
# gnome.compile_schemas(
#   build_by_default: true,
#   depend_files: gsettings_schemas,
#   install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
# )
