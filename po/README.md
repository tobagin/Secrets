# Translations

Thank you for your interest in translating Secrets Password Manager! This document will guide you through the process of contributing translations.

## Current Translation Status

Secrets currently supports the following languages:

- **English (US)** - `en_US` (Base language)
- **English (UK)** - `en_GB` 
- **Portuguese (Brazil)** - `pt_BR`
- **Portuguese (Portugal)** - `pt_PT`
- **Spanish** - `es`
- **Irish** - `ga`

## How to Contribute Translations

### Option 1: Using Weblate (Recommended)
*Coming soon - We're working on setting up a Weblate instance for easier translation contributions.*

### Option 2: Manual Translation

1. **Fork the repository** on GitHub
2. **Choose your language code** from the [ISO 639-1 standard](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
3. **Create a new translation** or **update an existing one**:

#### For a new language:
```bash
# Navigate to the po directory
cd po

# Create a new translation file (replace 'xx' with your language code)
msginit -l xx -o xx.po -i secrets.pot

# Edit the translation file
# You can use any text editor or specialized tools like Poedit
```

#### For updating existing translations:
```bash
# Update the translation template
meson compile -C build secrets-pot

# Update your language file (replace 'xx' with your language code)
msgmerge -U po/xx.po po/secrets.pot

# Edit the updated translation file
```

### Translation Tools

We recommend using one of these tools for editing `.po` files:

- **[Poedit](https://poedit.net/)** - Cross-platform, user-friendly GUI
- **[Lokalize](https://apps.kde.org/lokalize/)** - KDE's translation tool
- **[Gtranslator](https://wiki.gnome.org/Apps/Gtranslator)** - GNOME's translation tool
- **Any text editor** - For simple edits

### Translation Guidelines

1. **Keep it natural** - Translate the meaning, not word-for-word
2. **Maintain consistency** - Use the same terms throughout the application
3. **Consider context** - Some strings may have specific technical meanings
4. **Test your translations** - Build and run the application to see how they look
5. **Follow your language's conventions** - Use appropriate capitalization, punctuation, etc.

### Key Areas to Translate

- **Main interface** - Menus, buttons, labels
- **Dialog boxes** - Add/edit password dialogs, preferences
- **Setup wizard** - First-time setup experience
- **Error messages** - User-facing error and warning messages
- **Tooltips** - Helpful hints and descriptions

### Testing Your Translations

After making changes, you can test them by:

1. **Building the application**:
   ```bash
   meson compile -C build
   ```

2. **Running with your locale**:
   ```bash
   LANG=xx_XX.UTF-8 ./build/secrets-dev
   ```

3. **Installing and testing as Flatpak**:
   ```bash
   flatpak-builder --user --install --force-clean flatpak-build io.github.tobagin.secrets.yml
   LANG=xx_XX.UTF-8 flatpak run io.github.tobagin.secrets
   ```

## Submitting Your Translation

1. **Commit your changes** with a descriptive message:
   ```bash
   git add po/xx.po
   git commit -m "Add/Update [Language Name] translation"
   ```

2. **Push to your fork** and **create a Pull Request**

3. **Describe your changes** in the PR description

## Translation Maintenance

Translations need periodic updates as the application evolves. We'll notify translators when new strings are added or existing ones are modified.

## Getting Help

If you need help with translations:

- **Open an issue** on [GitHub Issues](https://github.com/tobagin/Secrets/issues)
- **Start a discussion** on [GitHub Discussions](https://github.com/tobagin/Secrets/discussions)
- **Contact the maintainer** through GitHub

## Recognition

All translation contributors will be credited in the application's About dialog and in the project documentation.

Thank you for helping make Secrets accessible to users worldwide! 🌍
