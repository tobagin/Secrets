# Get project_id from the main meson.build file
# This requires project_id to be defined in the root meson.build
# For simplicity here, we'll redefine it or assume it's 'com.example.secrets'
# A better way is to pass it via subproject_options or get it from project_source_root()
# if it matches the app_id.
app_id = get_variable('project_id', 'io.github.tobagin.secrets')



# UI files
# We'll create secrets.ui soon.
# If you use .blp (Blueprint) files, you'll need to set up blueprint-compiler
# and change how these are handled.
install_data(
  ['secrets.ui'], # Add other .ui files here if you have them
  install_dir: get_option('datadir') / app_id / 'ui'
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
appstream_file_input = 'io.github.tobagin.secrets.appdata.xml.in' # Keep consistent

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

# Icons directory - create it so it can be used
install_emptydir(get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps')

# Scalable icon
install_data(
  'icons/io.github.tobagin.secrets.svg', # Assumes icon file will be named this in data/icons/
   install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
   rename: app_id + '.svg' # Ensures installed icon is named e.g. io.github.tobagin.secrets.svg
)

# GSettings (if you add them later)
# gsettings_schemas = files('com.example.secrets.gschema.xml') # Placeholder
# gnome.compile_schemas(
#   build_by_default: true,
#   depend_files: gsettings_schemas,
#   install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
# )
