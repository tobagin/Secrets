# Secrets - A GTK4/Libadwaita GUI for pass

Secrets is a modern desktop application that provides a clean and user-friendly graphical interface for managing your passwords with `pass`, the standard unix password manager. It leverages the power and security of `pass`, GPG, and Git, wrapped in a beautiful GTK4/Libadwaita UI.

## ✨ Features

### 🔐 **Password Management**
- **Hierarchical folder organization** with expandable tree view
- **Add, edit, delete, and move** password entries
- **Structured password fields**: username, password, URL, notes, TOTP
- **TOTP support** with live 6-digit codes and countdown timers
- **Recovery codes management** for 2FA backup
- **Password generator** with customizable options and strength indicator
- **Copy to clipboard** with automatic clearing for security

### 🔍 **Search & Navigation**
- **Full-text search** across all password content
- **Real-time filtering** as you type
- **Keyboard shortcuts** for efficient navigation
- **Quick access** to frequently used passwords

### 🎨 **Modern Interface**
- **GTK4/Libadwaita design** following GNOME HIG
- **Adaptive layout** with split-view navigation
- **Dark/light theme support** with system integration
- **Toast notifications** for user feedback
- **Responsive design** that works on different screen sizes

### 🔧 **Advanced Features**
- **Git synchronization** (push/pull) for backup and sync
- **GPG integration** with automatic setup wizard
- **Flatpak compatibility** with enhanced GPG environment setup
- **Import/export** functionality (JSON, CSV formats)
- **Comprehensive preferences** with security settings
- **Automatic clipboard clearing** for enhanced security
- **Internationalization** support for multiple languages

### 🔒 **Security Features**
- **Automatic idle locking** - Lock application after configurable inactivity period
- **Master password timeout** - Require re-entering GPG passphrase periodically
- **Failed attempt protection** - Lockout after too many failed unlock attempts
- **Memory clearing** - Clear sensitive data from memory when locked
- **Screen lock integration** - Lock application when system screen locks
- **Configurable timeouts** - Auto-hide passwords and clear clipboard
- **Export security** - Require master password for data export operations
- **Session management** - Comprehensive security controls in preferences

### ⌨️ **Keyboard Shortcuts**
- `Ctrl+N` - Add new password
- `Ctrl+E` - Edit password
- `Ctrl+C` - Copy password
- `Ctrl+Shift+C` - Copy username
- `Ctrl+F` - Focus search
- `Ctrl+G` - Generate password
- `Ctrl+Shift+P` - Git pull
- `Ctrl+Shift+U` - Git push
- `Ctrl+,` - Preferences
- `F5` - Refresh

## 🔒 Security

Secrets provides comprehensive security features to protect your sensitive data:

### Session Security
- **Idle Lock**: Automatically lock the application after a configurable period of inactivity (1-120 minutes)
- **Screen Lock Integration**: Lock application when the system screen locks
- **Master Password Timeout**: Require re-entering GPG passphrase after a configurable period (15-480 minutes, or never)
- **Memory Clearing**: Clear sensitive data from memory when the application is locked

### Access Protection
- **Failed Attempt Lockout**: Lock out users after too many failed unlock attempts (1-10 attempts)
- **Lockout Duration**: Configurable lockout period after failed attempts (1-60 minutes)
- **Secure Unlock Dialog**: Password entry with attempt tracking and countdown display

### Data Protection
- **Auto-hide Passwords**: Automatically hide visible passwords after timeout (5-300 seconds)
- **Clipboard Security**: Automatically clear clipboard after copying sensitive data (10-300 seconds)
- **Export Security**: Require master password confirmation for data export operations
- **Delete Confirmation**: Require confirmation before deleting password entries

### Configuration
All security features are configurable through **Preferences → Security**:
- **Password Display**: Auto-hide settings and timeouts
- **Clipboard**: Auto-clear timeout configuration
- **Session Security**: Idle lock, screen lock, and master password timeouts
- **Advanced Security**: Memory clearing, export protection, and failed attempt settings

### Security Benefits
- **Defense in Depth**: Multiple layers of protection (UI lock + memory clearing + timeouts)
- **User Control**: Balance security vs convenience with configurable settings
- **Automatic Protection**: Passive security that doesn't require user intervention
- **Visual Feedback**: Clear indication of security status and remaining time

## 🌍 Internationalization

Secrets has full internationalization support with automatic locale detection and fallback to English when translations are unavailable.

### Supported Languages

- **🇧🇷 Portuguese (Brazil)** - pt_BR ⚠️ Partial (42% coverage)
- **🇵🇹 Portuguese (Portugal)** - pt_PT ⚠️ Partial (37% coverage)
- **🇺🇸 English (United States)** - en_US ✅ Complete (source)
- **🇬🇧 English (United Kingdom)** - en_GB ✅ Complete (source)
- **🇪🇸 Spanish** - es 👍 Good (79% coverage)
- **🇮🇪 Irish (Gaeilge)** - ga 👍 Good (79% coverage)

### Translation Features

- **Automatic locale detection** - Detects system locale and loads appropriate translations
- **Fallback support** - Falls back to English if translation not available
- **Development support** - Works in both development and installed environments
- **UI integration** - All user-facing strings in dialogs, menus, and interface are translatable
- **UTF-8 encoding** - Proper Unicode support for all languages

### Testing Translations

```bash
# Test specific locale
LANGUAGE=pt_BR python3 -m secrets.main

# Test Spanish interface
LANGUAGE=es ./run-dev.sh
```

### Adding New Translations

1. Add language code to `po/LINGUAS`
2. Create new .po file: `msginit --input=po/secrets.pot --locale=LANG --output=po/LANG.po`
3. Translate strings in the .po file
4. Rebuild: `meson compile -C builddir`

### Translation File Structure

```
po/
├── LINGUAS              # List of supported languages
├── secrets.pot          # Translation template
├── pt_BR.po            # Portuguese (Brazil) translations
├── pt_PT.po            # Portuguese (Portugal) translations
├── en_GB.po            # English (UK) translations
├── en_US.po            # English (US) translations
├── es.po               # Spanish translations
├── ga.po               # Irish translations
└── meson.build         # Build configuration
```

## 🛠️ Technology Stack

- **Language**: Python 3.8+
- **UI Framework**: GTK4 & Libadwaita
- **Build System**: Meson & Ninja
- **Dependencies**: PyGObject, pyotp
- **Backend**: `pass`, GnuPG, Git
- **Packaging**: Flatpak with enhanced GPG environment support

## 📦 Installation

### From Flathub (Recommended)

*Coming soon - the application will be available on Flathub once submitted and approved.*

```bash
flatpak install flathub io.github.tobagin.secrets
flatpak run io.github.tobagin.secrets
```

### Building from Source

#### Prerequisites
- Python 3.8+
- GTK4 and Libadwaita development libraries
- Meson (>= 0.64.0) and Ninja
- `pass`, `git`, and `gpg` installed and configured

#### Build Steps
```bash
# Clone the repository
git clone https://github.com/tobagin/Secrets.git
cd Secrets

# Build with meson
meson setup builddir
meson compile -C builddir

# Run for development
./run-dev.sh
```

#### Development Options
```bash
./run-dev.sh                 # Recommended: run with meson devenv
./run-dev.sh --direct        # Run directly without meson
./builddir/secrets-dev       # Run generated script
python3 -m secrets.main      # Run module directly
```

### Building Flatpak Locally

```bash
# Install flatpak-builder
sudo dnf install flatpak-builder  # Fedora
sudo apt install flatpak-builder  # Ubuntu/Debian

# Build and install
flatpak-builder --user --install --force-clean build-dir io.github.tobagin.secrets.yml

# Run the Flatpak
flatpak run io.github.tobagin.secrets
```

#### Flatpak GPG Compatibility

The Flatpak version includes enhanced GPG environment setup for proper password decryption in sandboxed environments:

- **Automatic GPG environment configuration** - Sets up proper `GPG_TTY`, `GNUPGHOME`, and agent settings
- **GUI pinentry integration** - Includes pinentry-gtk2 for password prompts in the GUI
- **Robust error handling** - Graceful fallbacks when GPG components are missing
- **Seamless operation** - No manual configuration required for GPG operations

### System Installation

```bash
# Build and install system-wide
meson setup builddir --prefix=/usr
meson compile -C builddir
sudo meson install -C builddir

# Run the installed application
io.github.tobagin.secrets
```

## 🏗️ Project Structure

```
Secrets/
├── secrets/                    # Main Python package
│   ├── controllers/           # UI controllers (MVC pattern)
│   ├── ui/                    # UI components and dialogs
│   ├── setup_wizard/          # GPG/pass setup wizard
│   ├── services/              # Business logic services
│   ├── utils/                 # Utility modules
│   └── *.py                   # Core application files
├── data/                      # Application data
│   ├── ui/                    # GTK UI definition files
│   ├── icons/                 # Application icons
│   └── *.xml.in              # Desktop/AppData metadata
├── tests/                     # Comprehensive test suite
├── po/                        # Internationalization (i18n)
│   ├── *.po                   # Translation files
│   └── LINGUAS               # Supported languages
└── *.yml                     # Flatpak manifest
```

### Architecture Patterns
- **MVC Pattern**: Controllers manage UI logic
- **Command Pattern**: Actions encapsulated as commands
- **Service Pattern**: Business logic in service classes
- **Manager Pattern**: Specialized managers for different concerns

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python3 run_tests.py

# Or run specific test categories
python3 -m unittest tests.test_models
python3 -m unittest tests.test_services
python3 -m unittest tests.test_commands

# Test GPG environment setup (for development)
python3 test_gpg_env.py

# Test security features
python3 test_security_features.py
```

The test suite includes:
- **Model tests** (12 tests) - Data structures and validation
- **Service tests** (18 tests) - Business logic and password operations
- **Command tests** (24 tests) - User actions and clipboard operations
- **Security tests** (4 tests) - Idle detection, session locking, and security configuration
- **Performance tests** - Memory usage and response times
- **GPG environment tests** - Flatpak compatibility and GPG setup verification

## 🤝 Contributing

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** and add tests
4. **Run the test suite**: `python3 run_tests.py`
5. **Submit a pull request** with a clear description

### Development Guidelines
- Follow existing code patterns and architecture
- Add tests for new functionality
- Update documentation as needed
- Use GTK4/Libadwaita best practices
- Ensure accessibility compliance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **pass** - The standard unix password manager
- **GNOME** - For GTK4 and Libadwaita
- **Flatpak** - For modern Linux app distribution
- **Contributors** - Everyone who helps improve this project

---

**Secrets** - Secure, modern password management for the Linux desktop.
