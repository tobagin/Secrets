"""
Git status component for displaying Git repository status in the UI.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, GLib
from typing import Optional, Callable

from ...managers.git_manager import GitManager
from ...services.git_service import GitStatus


class GitStatusComponent(GObject.Object):
    """Component for displaying Git status information."""
    
    def __init__(self, git_manager: GitManager):
        super().__init__()
        self.git_manager = git_manager
        self._status_widgets = {}
        self._update_callbacks = []
    
    def create_status_indicator(self) -> Gtk.Widget:
        """Create a compact status indicator widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Status icon
        self.status_icon = Gtk.Image()
        self.status_icon.set_icon_size(Gtk.IconSize.NORMAL)
        box.append(self.status_icon)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_ellipsize(3)  # ELLIPSIZE_END
        self.status_label.add_css_class("caption")
        box.append(self.status_label)
        
        # Store reference
        self._status_widgets['indicator'] = {
            'container': box,
            'icon': self.status_icon,
            'label': self.status_label
        }
        
        # Initial update
        self.update_status()
        
        return box
    
    def create_detailed_status_widget(self) -> Gtk.Widget:
        """Create a detailed status widget for preferences or dialogs."""
        group = Adw.PreferencesGroup()
        group.set_title("Git Repository Status")
        
        # Repository status
        self.repo_status_row = Adw.ActionRow()
        self.repo_status_row.set_title("Repository")
        self.repo_status_icon = Gtk.Image()
        self.repo_status_row.add_suffix(self.repo_status_icon)
        group.add(self.repo_status_row)
        
        # Remote status
        self.remote_status_row = Adw.ActionRow()
        self.remote_status_row.set_title("Remote")
        self.remote_status_icon = Gtk.Image()
        self.remote_status_row.add_suffix(self.remote_status_icon)
        group.add(self.remote_status_row)
        
        # Sync status
        self.sync_status_row = Adw.ActionRow()
        self.sync_status_row.set_title("Sync Status")
        self.sync_status_icon = Gtk.Image()
        self.sync_status_row.add_suffix(self.sync_status_icon)
        group.add(self.sync_status_row)
        
        # Working directory status
        self.working_status_row = Adw.ActionRow()
        self.working_status_row.set_title("Working Directory")
        self.working_status_icon = Gtk.Image()
        self.working_status_row.add_suffix(self.working_status_icon)
        group.add(self.working_status_row)
        
        # Store reference
        self._status_widgets['detailed'] = {
            'container': group,
            'repo_row': self.repo_status_row,
            'repo_icon': self.repo_status_icon,
            'remote_row': self.remote_status_row,
            'remote_icon': self.remote_status_icon,
            'sync_row': self.sync_status_row,
            'sync_icon': self.sync_status_icon,
            'working_row': self.working_status_row,
            'working_icon': self.working_status_icon
        }
        
        # Initial update
        self.update_status()
        
        return group
    
    def create_status_popover(self, relative_to: Gtk.Widget) -> Gtk.Popover:
        """Create a popover with Git status information."""
        popover = Gtk.Popover()
        popover.set_parent(relative_to)
        
        # Content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        popover.set_child(content_box)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Git Repository Status</b>")
        title_label.set_halign(Gtk.Align.START)
        content_box.append(title_label)
        
        # Status grid
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        content_box.append(grid)
        
        # Repository status
        grid.attach(Gtk.Label(label="Repository:"), 0, 0, 1, 1)
        self.popover_repo_status = Gtk.Label()
        self.popover_repo_status.set_halign(Gtk.Align.START)
        grid.attach(self.popover_repo_status, 1, 0, 1, 1)
        
        # Remote status
        grid.attach(Gtk.Label(label="Remote:"), 0, 1, 1, 1)
        self.popover_remote_status = Gtk.Label()
        self.popover_remote_status.set_halign(Gtk.Align.START)
        grid.attach(self.popover_remote_status, 1, 1, 1, 1)
        
        # Branch
        grid.attach(Gtk.Label(label="Branch:"), 0, 2, 1, 1)
        self.popover_branch_status = Gtk.Label()
        self.popover_branch_status.set_halign(Gtk.Align.START)
        grid.attach(self.popover_branch_status, 1, 2, 1, 1)
        
        # Sync status
        grid.attach(Gtk.Label(label="Sync:"), 0, 3, 1, 1)
        self.popover_sync_status = Gtk.Label()
        self.popover_sync_status.set_halign(Gtk.Align.START)
        grid.attach(self.popover_sync_status, 1, 3, 1, 1)
        
        # Working directory
        grid.attach(Gtk.Label(label="Changes:"), 0, 4, 1, 1)
        self.popover_changes_status = Gtk.Label()
        self.popover_changes_status.set_halign(Gtk.Align.START)
        grid.attach(self.popover_changes_status, 1, 4, 1, 1)
        
        # Store reference
        self._status_widgets['popover'] = {
            'container': popover,
            'repo': self.popover_repo_status,
            'remote': self.popover_remote_status,
            'branch': self.popover_branch_status,
            'sync': self.popover_sync_status,
            'changes': self.popover_changes_status
        }
        
        # Initial update
        self.update_status()
        
        return popover
    
    def update_status(self):
        """Update all status widgets with current Git status."""
        status = self.git_manager.get_status(use_cache=True)
        
        # Update indicator widget
        if 'indicator' in self._status_widgets:
            self._update_indicator_widget(status)
        
        # Update detailed widget
        if 'detailed' in self._status_widgets:
            self._update_detailed_widget(status)
        
        # Update popover widget
        if 'popover' in self._status_widgets:
            self._update_popover_widget(status)
        
        # Call update callbacks
        for callback in self._update_callbacks:
            callback(status)
    
    def _update_indicator_widget(self, status: GitStatus):
        """Update the compact indicator widget."""
        widgets = self._status_widgets['indicator']
        
        if not status.is_repo:
            widgets['icon'].set_from_icon_name("dialog-error-symbolic")
            widgets['label'].set_text("No Git repo")
            return
        
        if not status.has_remote:
            widgets['icon'].set_from_icon_name("dialog-warning-symbolic")
            widgets['label'].set_text("Local only")
            return
        
        # Determine status based on sync state and changes
        if status.behind > 0:
            widgets['icon'].set_from_icon_name("software-update-available-symbolic")
            widgets['label'].set_text(f"Behind {status.behind}")
        elif status.ahead > 0:
            widgets['icon'].set_from_icon_name("software-update-urgent-symbolic")
            widgets['label'].set_text(f"Ahead {status.ahead}")
        elif status.is_dirty:
            widgets['icon'].set_from_icon_name("document-edit-symbolic")
            widgets['label'].set_text("Changes")
        else:
            widgets['icon'].set_from_icon_name("emblem-ok-symbolic")
            widgets['label'].set_text("Up to date")
    
    def _update_detailed_widget(self, status: GitStatus):
        """Update the detailed status widget."""
        widgets = self._status_widgets['detailed']
        
        # Repository status
        if status.is_repo:
            widgets['repo_row'].set_subtitle("Initialized")
            widgets['repo_icon'].set_from_icon_name("emblem-ok-symbolic")
        else:
            widgets['repo_row'].set_subtitle("Not initialized")
            widgets['repo_icon'].set_from_icon_name("dialog-error-symbolic")
        
        # Remote status
        if status.has_remote:
            widgets['remote_row'].set_subtitle(status.remote_url)
            widgets['remote_icon'].set_from_icon_name("emblem-ok-symbolic")
        else:
            widgets['remote_row'].set_subtitle("No remote configured")
            widgets['remote_icon'].set_from_icon_name("dialog-warning-symbolic")
        
        # Sync status
        if not status.has_remote:
            widgets['sync_row'].set_subtitle("N/A (no remote)")
            widgets['sync_icon'].set_from_icon_name("dialog-information-symbolic")
        elif status.behind > 0 and status.ahead > 0:
            widgets['sync_row'].set_subtitle(f"Diverged (↓{status.behind} ↑{status.ahead})")
            widgets['sync_icon'].set_from_icon_name("dialog-warning-symbolic")
        elif status.behind > 0:
            widgets['sync_row'].set_subtitle(f"Behind by {status.behind} commits")
            widgets['sync_icon'].set_from_icon_name("software-update-available-symbolic")
        elif status.ahead > 0:
            widgets['sync_row'].set_subtitle(f"Ahead by {status.ahead} commits")
            widgets['sync_icon'].set_from_icon_name("software-update-urgent-symbolic")
        else:
            widgets['sync_row'].set_subtitle("Up to date")
            widgets['sync_icon'].set_from_icon_name("emblem-ok-symbolic")
        
        # Working directory status
        if status.is_dirty:
            changes = []
            if status.staged > 0:
                changes.append(f"{status.staged} staged")
            if status.unstaged > 0:
                changes.append(f"{status.unstaged} modified")
            if status.untracked > 0:
                changes.append(f"{status.untracked} untracked")
            
            widgets['working_row'].set_subtitle(", ".join(changes))
            widgets['working_icon'].set_from_icon_name("document-edit-symbolic")
        else:
            widgets['working_row'].set_subtitle("Clean")
            widgets['working_icon'].set_from_icon_name("emblem-ok-symbolic")
    
    def _update_popover_widget(self, status: GitStatus):
        """Update the popover status widget."""
        widgets = self._status_widgets['popover']
        
        # Repository
        widgets['repo'].set_text("Initialized" if status.is_repo else "Not initialized")
        
        # Remote
        if status.has_remote:
            widgets['remote'].set_text(status.remote_url)
        else:
            widgets['remote'].set_text("None")
        
        # Branch
        widgets['branch'].set_text(status.current_branch or "Unknown")
        
        # Sync
        if not status.has_remote:
            widgets['sync'].set_text("N/A")
        elif status.behind > 0 and status.ahead > 0:
            widgets['sync'].set_text(f"Diverged (↓{status.behind} ↑{status.ahead})")
        elif status.behind > 0:
            widgets['sync'].set_text(f"Behind {status.behind}")
        elif status.ahead > 0:
            widgets['sync'].set_text(f"Ahead {status.ahead}")
        else:
            widgets['sync'].set_text("Up to date")
        
        # Changes
        if status.is_dirty:
            total_changes = status.staged + status.unstaged + status.untracked
            widgets['changes'].set_text(f"{total_changes} files")
        else:
            widgets['changes'].set_text("None")
    
    def add_update_callback(self, callback: Callable[[GitStatus], None]):
        """Add a callback to be called when status is updated."""
        self._update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable[[GitStatus], None]):
        """Remove an update callback."""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
    
    def refresh_status(self):
        """Force refresh of Git status."""
        self.git_manager.invalidate_status_cache()
        self.update_status()
