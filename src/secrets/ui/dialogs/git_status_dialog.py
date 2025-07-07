"""
Git status dialog for viewing detailed Git repository information and history.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, GLib, Gio
import threading
from typing import List

from ...app_info import APP_ID
from ...managers.git_manager import GitManager
from ...services.git_service import GitCommit, GitStatus
from ...ui.components.git_status_component import GitStatusComponent


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/git_status_dialog.ui')
class GitStatusDialog(Adw.Window):
    """Dialog for viewing Git repository status and history."""
    
    __gtype_name__ = "GitStatusDialog"
    
    # Template widgets
    view_switcher = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    refresh_button = Gtk.Template.Child()
    status_content_box = Gtk.Template.Child()
    summary_text = Gtk.Template.Child()
    commit_button = Gtk.Template.Child()
    history_list = Gtk.Template.Child()
    
    def __init__(self, git_manager: GitManager, **kwargs):
        super().__init__(**kwargs)
        
        self.git_manager = git_manager
        self.status_component = GitStatusComponent(git_manager)
        
        # Set up view switcher
        self.view_switcher.set_stack(self.view_stack)
        
        # Set up history list
        self.history_model = Gio.ListStore.new(GObject.Object)
        self.history_list.set_model(Gtk.NoSelection.new(self.history_model))
        
        # Create factory for list items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_history_item_setup)
        factory.connect("bind", self._on_history_item_bind)
        self.history_list.set_factory(factory)
        
        # Add detailed status widget
        self.detailed_status = self.status_component.create_detailed_status_widget()
        self.status_content_box.prepend(self.detailed_status)
        
        self._load_data()
    
    
    def _on_history_item_setup(self, factory, list_item):
        """Set up history list item."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Header box
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.append(header_box)
        
        # Hash label
        hash_label = Gtk.Label()
        hash_label.add_css_class("monospace")
        hash_label.add_css_class("dim-label")
        hash_label.set_halign(Gtk.Align.START)
        header_box.append(hash_label)
        
        # Date label
        date_label = Gtk.Label()
        date_label.add_css_class("dim-label")
        date_label.set_halign(Gtk.Align.END)
        date_label.set_hexpand(True)
        header_box.append(date_label)
        
        # Message label
        message_label = Gtk.Label()
        message_label.set_halign(Gtk.Align.START)
        message_label.set_wrap(True)
        message_label.set_wrap_mode(Gtk.WrapMode.WORD)
        box.append(message_label)
        
        # Author label
        author_label = Gtk.Label()
        author_label.add_css_class("dim-label")
        author_label.set_halign(Gtk.Align.START)
        box.append(author_label)
        
        # Store references
        box.hash_label = hash_label
        box.date_label = date_label
        box.message_label = message_label
        box.author_label = author_label
        
        list_item.set_child(box)
    
    def _on_history_item_bind(self, factory, list_item):
        """Bind data to history list item."""
        commit_item = list_item.get_item()
        box = list_item.get_child()
        
        if hasattr(commit_item, 'commit'):
            commit = commit_item.commit
            box.hash_label.set_text(commit.short_hash)
            box.date_label.set_text(commit.date)
            box.message_label.set_text(commit.message)
            box.author_label.set_text(f"by {commit.author}")
    
    def _load_data(self):
        """Load Git data in background."""
        def load_worker():
            try:
                # Get status
                status = self.git_manager.get_status(use_cache=False)
                
                # Get commit history
                commits = self.git_manager.git_service.get_commit_history(50)
                
                # Get repository summary
                summary = self.git_manager.get_repository_summary()
                
                GLib.idle_add(self._on_data_loaded, status, commits, summary)
            except Exception as e:
                GLib.idle_add(self._on_data_load_error, str(e))
        
        threading.Thread(target=load_worker, daemon=True).start()
    
    def _on_data_loaded(self, status: GitStatus, commits: List[GitCommit], summary: dict):
        """Handle loaded data."""
        # Update status component
        self.status_component.update_status()
        
        # Update summary text
        summary_text = self._format_repository_summary(summary)
        buffer = self.summary_text.get_buffer()
        buffer.set_text(summary_text)
        
        # Update commit history
        self.history_model.remove_all()
        for commit in commits:
            # Create a simple object to hold commit data
            commit_item = GObject.Object()
            commit_item.commit = commit
            self.history_model.append(commit_item)
        
        # Update commit button sensitivity
        self.commit_button.set_sensitive(status.is_repo and status.is_dirty)
    
    def _on_data_load_error(self, error: str):
        """Handle data loading error."""
        print(f"Error loading Git data: {error}")
    
    def _format_repository_summary(self, summary: dict) -> str:
        """Format repository summary for display."""
        lines = []
        
        if summary['is_repo']:
            lines.append("✓ Git repository is initialized")
            
            if summary['current_branch']:
                lines.append(f"📍 Current branch: {summary['current_branch']}")
            
            if summary['has_remote']:
                lines.append(f"🔗 Remote: {summary['remote_url']}")
                
                if summary['platform_type']:
                    lines.append(f"🏢 Platform: {summary['platform_type'].title()}")
                
                if summary['ahead'] > 0:
                    lines.append(f"⬆️  Ahead by {summary['ahead']} commits")
                
                if summary['behind'] > 0:
                    lines.append(f"⬇️  Behind by {summary['behind']} commits")
                
                if summary['ahead'] == 0 and summary['behind'] == 0:
                    lines.append("✅ Up to date with remote")
            else:
                lines.append("⚠️  No remote repository configured")
            
            if summary['is_dirty']:
                lines.append("📝 Working directory has changes")
            else:
                lines.append("✨ Working directory is clean")
            
            if summary['last_commit']:
                lines.append(f"📅 Last commit: {summary['last_commit']}")
                if summary['last_commit_date']:
                    lines.append(f"🕒 Date: {summary['last_commit_date']}")
        else:
            lines.append("❌ No Git repository found")
            lines.append("💡 Use the Git setup dialog to initialize a repository")
        
        return "\n".join(lines)
    
    @Gtk.Template.Callback()
    def _on_refresh_clicked(self, button):
        """Handle refresh button click."""
        self.status_component.refresh_status()
        self._load_data()
    
    @Gtk.Template.Callback()
    def _on_commit_clicked(self, button):
        """Handle commit button click."""
        # Create commit dialog
        dialog = Adw.AlertDialog()
        dialog.set_heading("Commit Changes")
        dialog.set_body("Enter a commit message for your changes:")
        
        # Add entry for commit message
        entry = Gtk.Entry()
        entry.set_placeholder_text("Update passwords")
        dialog.set_extra_child(entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("commit", "Commit")
        dialog.set_response_appearance("commit", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("commit")
        
        dialog.connect("response", self._on_commit_dialog_response, entry)
        dialog.present(self)
    
    def _on_commit_dialog_response(self, dialog, response, entry):
        """Handle commit dialog response."""
        if response == "commit":
            message = entry.get_text().strip()
            if not message:
                message = "Update passwords"
            
            def commit_worker():
                try:
                    success, result_message = self.git_manager.git_service.commit_changes(message)
                    GLib.idle_add(self._on_commit_complete, success, result_message)
                except Exception as e:
                    GLib.idle_add(self._on_commit_complete, False, str(e))
            
            threading.Thread(target=commit_worker, daemon=True).start()
    
    def _on_commit_complete(self, success: bool, message: str):
        """Handle commit completion."""
        if success:
            self.git_manager.toast_manager.show_success(f"Commit successful: {message}")
            self._load_data()  # Refresh data
        else:
            self.git_manager.toast_manager.show_error(f"Commit failed: {message}")
