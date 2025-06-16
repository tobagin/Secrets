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
- **Import/export** functionality (JSON, CSV formats)
- **Comprehensive preferences** with security settings
- **Automatic clipboard clearing** for enhanced security

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

## 🛠️ Technology Stack

- **Language**: Python 3.8+
- **UI Framework**: GTK4 & Libadwaita
- **Build System**: Meson & Ninja
- **Dependencies**: PyGObject, pyotp
- **Backend**: `pass`, GnuPG, Git

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
├── po/                        # Internationalization
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
```

The test suite includes:
- **Model tests** (12 tests) - Data structures and validation
- **Service tests** (18 tests) - Business logic and password operations
- **Command tests** (24 tests) - User actions and clipboard operations
- **Performance tests** - Memory usage and response times

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
