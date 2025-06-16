# Flathub Submission Guide for Secrets

This document outlines the steps to submit Secrets to Flathub.

## Prerequisites

1. **Complete the application**: Ensure all features are working and tested
2. **Create screenshots**: ✅ **COMPLETED** - 12 high-quality screenshots added to `data/screenshots/`
3. **Test the Flatpak build**: Verify the Flatpak builds and runs correctly
4. **Create a release**: Tag a stable release on GitHub

## Available Screenshots

The following 12 screenshots are now available in `data/screenshots/`:

### Core Interface (6 screenshots)
- `main-window.png` - Main application window with password organization
- `password-page-view.png` - Password details with TOTP and structured fields
- `add-new-password.png` - Add password dialog with comprehensive options
- `edit-password.png` - Edit password dialog with comprehensive options
- `about-dialog.png` - Application information dialog
- `keyboard-shortcuts.png` - Keyboard shortcuts help

### Settings and Configuration (4 screenshots)
- `general-settings.png` - General application preferences
- `security-settings.png` - Advanced security and session management
- `search-settings.png` - Search and filtering preferences
- `git-settings.png` - Git integration configuration

### Git Features (2 screenshots)
- `git-status-dialog.png` - Git status and repository information
- `git-repo-history.png` - Git commit history viewer

All screenshots are referenced in the AppData file and README.md for Flathub submission.

## Pre-submission Checklist

### Code and Build
- [ ] Application builds successfully with meson
- [ ] All tests pass
- [ ] No critical bugs or crashes
- [ ] Application follows GNOME HIG guidelines
- [ ] Proper error handling and user feedback

### Metadata
- [ ] AppData file is complete and valid
- [ ] Desktop file is correct
- [ ] Icon is provided in SVG format
- [ ] License is clearly specified (MIT)
- [ ] All URLs in metadata are working

### Flatpak Manifest
- [ ] Manifest builds successfully
- [ ] All dependencies are correctly specified
- [ ] Permissions are minimal but sufficient
- [ ] Sources use stable releases or tagged commits

### Screenshots and Media
- [x] At least one screenshot is provided (12 screenshots available)
- [x] Screenshots show the app in realistic use
- [x] No sensitive data visible in screenshots
- [x] Screenshots are high quality (1280x800 or similar)
- [x] Screenshots cover main interface, dialogs, settings, and key features
- [x] Screenshots include Git integration, security features, and TOTP support

## Submission Steps

### 1. Prepare the Release

```bash
# Create a release tag
git tag -a v0.5.0 -m "Major update with enhanced UI and new features"
git push origin v0.5.0

# Update the Flatpak manifest with the correct commit hash
# Edit io.github.tobagin.secrets.yml and update the commit field
```

### 2. Test the Flatpak Build

```bash
# Install flatpak-builder
sudo dnf install flatpak-builder

# Build the Flatpak
flatpak-builder build-dir io.github.tobagin.secrets.yml --force-clean --install-deps-from=flathub

# Test the built application
flatpak-builder --run build-dir io.github.tobagin.secrets.yml io.github.tobagin.secrets
```

### 3. Submit to Flathub

1. **Fork the Flathub repository**: https://github.com/flathub/flathub
2. **Create a new repository**: Request a new repository for `io.github.tobagin.secrets`
3. **Submit the manifest**: Create a pull request with your Flatpak manifest
4. **Wait for review**: Flathub maintainers will review your submission

### 4. Repository Structure for Flathub

Your Flathub repository should contain:
```
io.github.tobagin.secrets/
├── io.github.tobagin.secrets.yml    # Main manifest
├── README.md                        # Brief description
└── flathub.json                     # Flathub metadata (optional)
```

## Common Issues and Solutions

### Build Failures
- Ensure all dependencies are available in Flathub
- Check that source URLs are accessible
- Verify SHA256 checksums are correct

### Permission Issues
- Use minimal permissions required for functionality
- Document why each permission is needed
- Consider using portals instead of direct filesystem access

### Metadata Validation
- Use `appstream-util validate` to check AppData
- Use `desktop-file-validate` to check desktop file
- Ensure all required fields are present

## Post-submission

1. **Monitor the review process**: Respond to feedback promptly
2. **Update documentation**: Keep README and help documentation current
3. **Plan updates**: Prepare for future releases and updates

## Resources

- [Flathub Documentation](https://docs.flathub.org/)
- [Flatpak Documentation](https://docs.flatpak.org/)
- [GNOME Application Guidelines](https://developer.gnome.org/hig/)
- [AppStream Specification](https://www.freedesktop.org/software/appstream/docs/)

## Contact

For questions about this submission, contact:
- GitHub: @tobagin
- Email: 140509353+tobagin@users.noreply.github.com
