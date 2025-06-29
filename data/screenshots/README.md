# Screenshots

This directory contains screenshots for the Secrets application. All screenshots show both light and dark themes side-by-side for comprehensive theme coverage.

## Available Screenshots

### Main Interface
1. **main-window.png** - Main application window showing password store with hierarchical folder organization (light/dark theme comparison)

### Password Management
2. **add-new-password.png** - Add new password dialog with comprehensive field options (light/dark theme comparison)
3. **edit-password.png** - Edit password dialog with comprehensive field options (light/dark theme comparison)
4. **password-generator.png** - Password generator with strength indicators and customizable options (light/dark theme comparison)

### Folder Management
5. **add-new-folder.png** - Add new folder dialog with color and icon customization (light/dark theme comparison)
6. **edit-folder.png** - Edit folder dialog with color and icon customization (light/dark theme comparison)

### Application Features
7. **search-filter.png** - Search and filtering interface (light/dark theme comparison)
8. **general-settings.png** - General settings and preferences dialog (light/dark theme comparison)
9. **about-dialog.png** - About dialog showing application information (light/dark theme comparison)

## Screenshot Format

All screenshots in this directory are **combined theme screenshots** that show:
- **Left half**: Light theme version
- **Right half**: Dark theme version

This format provides comprehensive theme coverage in a single image, making it easier for users to see how the application looks in both themes.

## Screenshot Guidelines

- Combined screenshots show both light and dark themes side-by-side
- Use realistic aspect ratios that match typical dialog sizes
- Show the application in realistic use cases
- Ensure no real passwords or sensitive data are visible
- Use placeholder data that looks realistic but is clearly fake
- Maintain consistent window sizes between light and dark versions

## Taking Combined Screenshots

1. Run the application: `./run-dev.sh`
2. Set up some test data in your password store
3. Take screenshots in light theme first
4. Switch to dark theme and take matching screenshots
5. Use image editing tools to combine them side-by-side (left=light, right=dark)
6. Save the combined images in this directory with descriptive names
7. Update the appdata.xml.in file with the correct screenshot URLs

## Image Processing

Combined screenshots are created using Python PIL (Pillow) to merge light and dark theme versions:
- Left half: Light theme screenshot
- Right half: Dark theme screenshot
- Maintains original image quality and dimensions
