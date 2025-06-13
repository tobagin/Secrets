gnome = import('gnome')
i18n = import('i18n')

# Replace 'secrets' with your app's Gettext domain if different
gettext_package_name = project_id

gnome.gettext(gettext_package_name,
  args: ['--directory=' + meson.project_source_root()]
)

# Optional: Add a test to check .po files for errors
# pot_file = gettext_package_name + '.pot'
# find_program('msgfmt', required : false)
# if find_program('msgfmt').found()
#   test('Validate translations', find_program('msgfmt'),
#     args: ['--check', '--output=/dev/null', pot_file] + i18n.get_pofiles(meson.project_source_root() / 'po')
#   )
# endif
