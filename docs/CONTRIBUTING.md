# Contributing to Secrets Password Manager

Thank you for your interest in contributing to Secrets! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Submit bug fixes and new features
- **Translations**: Help make Secrets available in more languages
- **Documentation**: Improve guides, comments, and examples
- **Testing**: Test new features and report feedback

## 🐛 Reporting Issues

When reporting bugs, please include:

1. **Environment Information**:
   - Operating System and version
   - GTK/Libadwaita version
   - Installation method (Flatpak, source, etc.)

2. **Steps to Reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior
   - Screenshots if applicable

3. **Logs and Error Messages**:
   - Terminal output
   - Error dialogs
   - Relevant log files

## 💡 Feature Requests

For new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and problem it solves
3. **Provide mockups or examples** if applicable
4. **Consider implementation complexity** and user impact

## 🔧 Development Setup

### Prerequisites

- Python 3.11+
- GTK 4.0+
- Libadwaita 1.4+
- Meson build system
- Git

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tobagin/Secrets.git
   cd Secrets
   ```

2. **Install dependencies**:
   ```bash
   # On Fedora/RHEL
   sudo dnf install python3-devel gtk4-devel libadwaita-devel meson ninja-build

   # On Ubuntu/Debian
   sudo apt install python3-dev libgtk-4-dev libadwaita-1-dev meson ninja-build
   ```

3. **Build and install**:
   ```bash
   meson setup build
   meson compile -C build
   meson install -C build
   ```

4. **Run in development mode**:
   ```bash
   python -m secrets
   ```

### Flatpak Development

For Flatpak testing:

```bash
# Build Flatpak
flatpak-builder --force-clean build-dir io.github.tobagin.secrets.yml

# Install locally
flatpak-builder --user --install --force-clean build-dir io.github.tobagin.secrets.yml

# Run
flatpak run io.github.tobagin.secrets
```

## 📝 Code Style and Standards

### Python Code

- **PEP 8** compliance with 88-character line limit
- **Type hints** for function parameters and returns
- **Docstrings** for all public methods and classes
- **Meaningful variable names** and clear logic flow

### UI/UX Guidelines

- **Follow GNOME HIG** (Human Interface Guidelines)
- **Use Libadwaita widgets** when available
- **Ensure accessibility** with proper labels and keyboard navigation
- **Test on different screen sizes** and themes
- **Maintain visual consistency** across dialogs and components

### Git Workflow

1. **Fork the repository** and create a feature branch
2. **Make focused commits** with clear messages
3. **Test thoroughly** before submitting
4. **Update documentation** if needed
5. **Submit a pull request** with detailed description

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(ui): add color picker for folder customization`
- `fix(clipboard): resolve auto-clear timing issue`
- `docs(readme): update installation instructions`

## 🌍 Translation Guidelines

Secrets supports multiple languages. To contribute translations:

1. **Check existing translations** in the `po/` directory
2. **Use standard translation tools** like Poedit or GNOME Translation Editor
3. **Follow locale conventions** for your language
4. **Test translations** in the application
5. **Keep strings concise** while maintaining meaning

### Adding a New Language

1. Create a new `.po` file in `po/[language_code]/`
2. Update `po/LINGUAS` to include your language
3. Translate all strings in the `.po` file
4. Test the translation in the application
5. Submit a pull request

For more details, see [Translation Documentation](po/README.md).

## 🧪 Testing

### Manual Testing

- **Test all major workflows**: password creation, editing, deletion
- **Verify UI responsiveness** on different screen sizes
- **Check accessibility** with screen readers and keyboard navigation
- **Test error handling** with invalid inputs and edge cases

### Automated Testing

While we're working on comprehensive test coverage:

- **Run existing tests** before submitting changes
- **Add tests** for new functionality when possible
- **Verify no regressions** in existing features

## 📋 Pull Request Process

1. **Create a focused PR** addressing a single issue or feature
2. **Provide clear description** of changes and motivation
3. **Include screenshots** for UI changes
4. **Update documentation** if needed
5. **Ensure all checks pass** (builds, tests, linting)
6. **Respond to feedback** promptly and constructively

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Manual testing completed
- [ ] No regressions found
- [ ] Screenshots attached (for UI changes)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Translation strings updated (if applicable)
```

## 🏗️ Architecture Overview

### Project Structure

```
src/secrets/
├── ui/                 # User interface components
│   ├── dialogs/       # Dialog windows
│   ├── widgets/       # Custom widgets
│   └── components/    # Reusable UI components
├── controllers/       # Business logic controllers
├── managers/          # Service managers (clipboard, favicon, etc.)
├── services/          # External service integrations
└── utils/             # Utility functions
```

### Key Design Principles

- **Separation of concerns**: UI, business logic, and data are clearly separated
- **Modern GTK4/Libadwaita**: Uses latest UI toolkit features
- **Accessibility first**: Designed for all users
- **Performance focused**: Efficient operations and responsive UI
- **Extensible architecture**: Easy to add new features

## 🤝 Community Guidelines

- **Be respectful** and inclusive in all interactions
- **Provide constructive feedback** and suggestions
- **Help newcomers** get started with contributing
- **Share knowledge** and learn from others
- **Follow the Code of Conduct** (coming soon)

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Matrix/IRC**: Real-time chat (links coming soon)

## 🎉 Recognition

Contributors are recognized in:
- **About dialog** in the application
- **README.md** contributors section
- **Release notes** for significant contributions

Thank you for helping make Secrets better for everyone! 🔐✨
