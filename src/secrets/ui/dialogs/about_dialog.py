import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from ...app_info import APP_ID, VERSION


def create_about_dialog(transient_for=None):
    """Create and return an AboutWindow for the Secrets application."""

    # Create the about window with all the properties
    about_dialog = Adw.AboutWindow(
        transient_for=transient_for,
        modal=True,
        title="About",
        application_name="Secrets Manager",
        application_icon=APP_ID,
        developer_name="Thiago Fernandes",
        version=VERSION,
        website="https://github.com/tobagin/Secrets",
        issue_url="https://github.com/tobagin/Secrets/issues",
        support_url="https://github.com/tobagin/Secrets/discussions",
        copyright="© 2024 Thiago Fernandes",
        license_type=Gtk.License.GPL_3_0,
        comments="A modern password manager with customizable colors, icons, and 2FA support built with GTK4 and Libadwaita.",
        developers=["Thiago Fernandes https://github.com/tobagin"],
        designers=["Thiago Fernandes"],
        documenters=["Thiago Fernandes"],
        translator_credits="Thiago Fernandes (Portuguese)\nContribute translations at: https://github.com/tobagin/Secrets/tree/main/po",
        release_notes="""<p>🎨 Major UI/UX redesign with modern color/icon pickers, enhanced favicon system, and comprehensive user experience improvements!</p>

<p>🎨 Visual Design &amp; Interface:</p>
<ul>
<li>✨ Root folder passwords now display as individual items instead of grouped under "Root" folder</li>
<li>🎨 Complete redesign of color and icon picker system with modern AdwComboRow interface</li>
<li>🖼️ Enhanced avatar system with custom ColorPaintable for superior rendering quality</li>
<li>🎯 Intelligent icon color adaptation based on background luminance for optimal contrast</li>
<li>📱 Improved header bar design with better button organization and visual hierarchy</li>
<li>🔧 Enhanced split button dropdown with visual consistency improvements</li>
<li>🎨 Theme-aware icon picker avatars that adapt to dark/light mode automatically</li>
<li>📏 Improved icon resolution with higher pixel density for crisp display (25% smaller but sharper)</li>
<li>🔄 Folder expansion state preservation during UI updates</li>
<li>🖼️ Updated icon combo rows to display actual icons instead of text names for better visual selection</li>
<li>🎯 Enhanced split button dropdown to show folder icon instead of text for visual consistency</li>
<li>🎨 Enhanced add password icon with bigger, centered padlock design and properly centered carved + symbol</li>
</ul>

<p>🌐 Favicon &amp; URL Handling:</p>
<ul>
<li>🌐 Automatic favicon download and display for passwords with URLs</li>
<li>🎯 Favicon-only avatar rendering without background colors when favicons are available</li>
<li>💾 Intelligent favicon caching system to prevent unnecessary re-downloads</li>
<li>🌐 Enhanced URL detection supporting multiple formats (github.com, www.github.com, https://github.com, git.hub, github.social, etc.)</li>
<li>🔒 Automatic HTTP to HTTPS conversion for enhanced security</li>
<li>📝 Improved URL field handling with consistent "url:" prefix format</li>
<li>🔧 Backward compatibility for legacy URL formats without prefixes</li>
<li>🔄 Enhanced favicon system with async loading and proper fallback to color+icon combinations</li>
<li>⚡ Optimized favicon download to stop after first successful download</li>
</ul>

<p>⚡ Performance &amp; Technical:</p>
<ul>
<li>⚡ Performance optimizations with targeted UI updates instead of full reloads</li>
<li>🔧 Enhanced password metadata refresh system for immediate visual feedback</li>
<li>🏷️ Flathub-compliant custom icon naming with proper app ID prefixes</li>
<li>🎨 Advanced paintable system supporting color backgrounds, icons, and favicons</li>
<li>🔄 Efficient state management with preserved UI context during updates</li>
<li>⚡ Replaced CSS-based avatar styling with native GTK4 paintable system for better performance</li>
<li>🎯 Separated dialog previews (color-only and icon-only) from row displays (combined color+icon+favicon)</li>
<li>📏 Standardized icon sizes across all pickers and menus to 16px for consistency</li>
</ul>

<p>🔧 User Experience Improvements:</p>
<ul>
<li>🔧 Fixed color picker activation to only trigger on color-select button, not entire row</li>
<li>🖼️ Added AdwAvatar previews in color/icon picker rows showing selected colors and icons</li>
<li>📁 Enhanced add/edit folder dialogs with new modern picker design</li>
<li>🔐 Enhanced add/edit password dialogs with new modern picker design</li>
<li>🖼️ Added edit folder functionality with dedicated edit button on folder rows</li>
<li>🔍 Moved search button to left of title for better accessibility</li>
<li>➕ Replaced add buttons with AdwSplitButton: main button for "Add Password", dropdown for "Add Folder"</li>
<li>📋 Moved main menu button to right of title for consistent navigation</li>
<li>🗂️ Removed redundant action buttons bar, integrating all actions into header bar</li>
<li>💾 Added metadata storage system to persist color and icon preferences</li>
<li>🔄 Enhanced folder renaming functionality with metadata preservation</li>
</ul>

<p>This release delivers a comprehensive UI/UX overhaul with modern design patterns, streamlined workflows, enhanced visual consistency, and full Flathub compliance. The new custom paintable system provides superior color and icon rendering with automatic favicon support, making password identification more intuitive and visually appealing than ever!</p>"""
    )

    return about_dialog


# For backward compatibility, create an alias
AboutDialog = create_about_dialog


if __name__ == '__main__':
    # Basic testing of the dialog
    app = Adw.Application(application_id="com.example.testaboutdialog")

    def on_activate(application):
        dialog = create_about_dialog()
        dialog.present()

    app.connect("activate", on_activate)
    app.run([])
