i18n = import('i18n')

# Get project_id from the main meson.build file
# This requires project_id to be defined in the root meson.build
# For simplicity here, we'll redefine it or assume it's 'com.example.secrets'
# A better way is to pass it via subproject_options or get it from project_source_root()
# if it matches the app_id.
app_id = get_variable('project_id', 'io.github.tobagin.secrets')


# UI files and CSS - organized structure
# CSS file (only Blueprint compilation targets are now used for UI files)
install_data(
  ['style.css'],
  install_dir: get_option('datadir') / app_id / 'ui'
)

# Blueprint files for the new single-window design
# These need to be compiled to UI files
blueprint_prog = find_program('blueprint-compiler', required: false)
if blueprint_prog.found()
  # Main window blueprint
  main_window_ui = custom_target(
    'main_window_ui',
    input: 'ui/main_window.blp',
    output: 'main_window.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui'
  )
  
  # Password details dialog blueprint
  password_details_dialog_ui = custom_target(
    'password_details_dialog_ui',
    input: 'ui/dialogs/password_details_dialog.blp',
    output: 'password_details_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  # Password entry row blueprint
  password_entry_row_ui = custom_target(
    'password_entry_row_ui',
    input: 'ui/widgets/password_entry_row.blp',
    output: 'password_entry_row.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'widgets'
  )
  
  # Folder expander row blueprint
  folder_expander_row_ui = custom_target(
    'folder_expander_row_ui',
    input: 'ui/widgets/folder_expander_row.blp',
    output: 'folder_expander_row.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'widgets'
  )
  
  
  # Unified password dialog blueprint (replaces add/edit password dialogs)
  password_dialog_ui = custom_target(
    'password_dialog_ui',
    input: 'ui/dialogs/password_dialog.blp',
    output: 'password_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  # Password generator dialog blueprint
  password_generator_dialog_ui = custom_target(
    'password_generator_dialog_ui',
    input: 'ui/dialogs/password_generator_dialog.blp',
    output: 'password_generator_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  # Shortcuts window blueprint
  shortcuts_window_ui = custom_target(
    'shortcuts_window_ui',
    input: 'ui/shortcuts_window.blp',
    output: 'shortcuts_window.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui'
  )
  
  
  # Unified folder dialog blueprint (replaces add/edit folder dialogs)
  folder_dialog_ui = custom_target(
    'folder_dialog_ui',
    input: 'ui/dialogs/folder_dialog.blp',
    output: 'folder_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  
  
  # Header bar component blueprint
  header_bar_ui = custom_target(
    'header_bar_ui',
    input: 'ui/components/header_bar.blp',
    output: 'header_bar.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'components'
  )
  
  # Password list component blueprint
  password_list_ui = custom_target(
    'password_list_ui',
    input: 'ui/components/password_list.blp',
    output: 'password_list.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'components'
  )
  
  
  # Main menu component blueprint
  main_menu_ui = custom_target(
    'main_menu_ui',
    input: 'ui/components/main_menu.blp',
    output: 'main_menu.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'components'
  )
  
  # Password generator popover component blueprint
  password_generator_popover_ui = custom_target(
    'password_generator_popover_ui',
    input: 'ui/components/password_generator_popover.blp',
    output: 'password_generator_popover.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'components'
  )
  
  # Password generator widget component blueprint
  password_generator_widget_ui = custom_target(
    'password_generator_widget_ui',
    input: 'ui/components/password_generator_widget.blp',
    output: 'password_generator_widget.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'components'
  )
  
  # Dialog blueprints
  import_export_dialog_ui = custom_target(
    'import_export_dialog_ui',
    input: 'ui/dialogs/import_export_dialog.blp',
    output: 'import_export_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  lock_dialog_ui = custom_target(
    'lock_dialog_ui',
    input: 'ui/dialogs/lock_dialog.blp',
    output: 'lock_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  git_setup_dialog_ui = custom_target(
    'git_setup_dialog_ui',
    input: 'ui/dialogs/git_setup_dialog.blp',
    output: 'git_setup_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  git_status_dialog_ui = custom_target(
    'git_status_dialog_ui',
    input: 'ui/dialogs/git_status_dialog.blp',
    output: 'git_status_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  # Compliance dashboard dialog blueprint
  compliance_dashboard_dialog_ui = custom_target(
    'compliance_dashboard_dialog_ui',
    input: 'ui/dialogs/compliance_dashboard_dialog.blp',
    output: 'compliance_dashboard_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  # Preferences dialog blueprint
  preferences_dialog_ui = custom_target(
    'preferences_dialog_ui',
    input: 'ui/dialogs/preferences_dialog.blp',
    output: 'preferences_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'dialogs'
  )
  
  # Setup blueprints
  wizard_dialog_ui = custom_target(
    'wizard_dialog_ui',
    input: 'ui/setup/wizard_dialog.blp',
    output: 'wizard_dialog.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
  )
  
  dependencies_page_ui = custom_target(
    'dependencies_page_ui',
    input: 'ui/setup/dependencies_page.blp',
    output: 'dependencies_page.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
  )
  
  install_pass_page_ui = custom_target(
    'install_pass_page_ui',
    input: 'ui/setup/install_pass_page.blp',
    output: 'install_pass_page.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
  )
  
  create_gpg_page_ui = custom_target(
    'create_gpg_page_ui',
    input: 'ui/setup/create_gpg_page.blp',
    output: 'create_gpg_page.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
  )
  
  setup_complete_page_ui = custom_target(
    'setup_complete_page_ui',
    input: 'ui/setup/setup_complete_page.blp',
    output: 'setup_complete_page.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
  )
  
  # Setup wizard dialog blueprint
  setup_wizard_ui = custom_target(
    'setup_wizard_ui',
    input: 'ui/setup/setup_wizard.blp',
    output: 'setup_wizard.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
  )
  
  # Main setup window blueprint
  main_setup_ui = custom_target(
    'main_setup_ui',
    input: 'ui/setup/main.blp',
    output: 'main.ui',
    command: [blueprint_prog, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: get_option('datadir') / app_id / 'ui' / 'setup'
  )
  
  # Make these targets available globally
  all_blueprint_targets = [
    main_window_ui,
    password_details_dialog_ui,
    password_entry_row_ui,
    folder_expander_row_ui,
    password_dialog_ui,
    password_generator_dialog_ui,
    shortcuts_window_ui,
    folder_dialog_ui,
    header_bar_ui,
    password_list_ui,
    main_menu_ui,
    password_generator_popover_ui,
    password_generator_widget_ui,
    import_export_dialog_ui,
    lock_dialog_ui,
    git_setup_dialog_ui,
    git_status_dialog_ui,
    compliance_dashboard_dialog_ui,
    preferences_dialog_ui,
    wizard_dialog_ui,
    dependencies_page_ui,
    install_pass_page_ui,
    create_gpg_page_ui,
    setup_complete_page_ui,
    setup_wizard_ui,
    main_setup_ui,
  ]
  
  set_variable('all_blueprint_targets', all_blueprint_targets)
endif

# Component UI files (excluding Blueprint-converted files)
# All component UI files are now converted to Blueprint

# Dialog UI files (excluding Blueprint-converted files)
# All dialog files are now converted to Blueprint

# Widget UI files (excluding Blueprint-converted files)
# All widget UI files are now converted to Blueprint

# Setup wizard UI files
# All setup UI files are now converted to Blueprint

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
# Scalable SVG icon (fallback) - commented out as file doesn't exist
# install_data(
#   'icons/io.github.tobagin.secrets.svg',
#   install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
#   rename: app_id + '.svg'
# )

# PNG icons in multiple sizes
icon_sizes = ['16x16', '22x22', '24x24', '32x32', '48x48', '64x64', '96x96', '128x128', '256x256', '512x512']

foreach size : icon_sizes
  install_data(
    'icons' / size / (app_id + '.png'),
    install_dir: get_option('datadir') / 'icons' / 'hicolor' / size / 'apps',
    rename: app_id + '.png'
  )
endforeach

# Custom symbolic icons
symbolic_icons = [
  'io.github.tobagin.secrets-add-password-symbolic.svg',
  'io.github.tobagin.secrets-add-folder-symbolic.svg',
  'io.github.tobagin.secrets-banking-symbolic.svg',
  'io.github.tobagin.secrets-chat-symbolic.svg',
  'io.github.tobagin.secrets-cloud-download-symbolic.svg',
  'io.github.tobagin.secrets-cloud-symbolic.svg',
  'io.github.tobagin.secrets-cloud-upload-symbolic.svg',
  'io.github.tobagin.secrets-development-symbolic.svg',
  'io.github.tobagin.secrets-export-symbolic.svg',
  'io.github.tobagin.secrets-external-link-symbolic.svg',
  'io.github.tobagin.secrets-gaming-symbolic.svg',
  'io.github.tobagin.secrets-import-symbolic.svg',
  'io.github.tobagin.secrets-office-symbolic.svg',
  'io.github.tobagin.secrets-password-symbolic.svg',
  'io.github.tobagin.secrets-remove-folder-symbolic.svg',
  'io.github.tobagin.secrets-remove-password-symbolic.svg',
  'io.github.tobagin.secrets-shopping-symbolic.svg',
  'io.github.tobagin.secrets-totp-symbolic.svg',
  'io.github.tobagin.secrets-trading-symbolic.svg',
  'io.github.tobagin.secrets-username-symbolic.svg',
  'io.github.tobagin.secrets-verified-symbolic.svg',
  'io.github.tobagin.secrets-view-details-symbolic.svg',
  'io.github.tobagin.secrets-wallet-symbolic.svg',
  'io.github.tobagin.secrets-website-symbolic.svg'
]

foreach icon : symbolic_icons
  install_data(
    'icons/symbolic' / icon,
    install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'symbolic' / 'apps'
  )
endforeach

# GSettings (if you add them later)
# gsettings_schemas = files('com.example.secrets.gschema.xml') # Placeholder
# gnome.compile_schemas(
#   build_by_default: true,
#   depend_files: gsettings_schemas,
#   install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
# )
