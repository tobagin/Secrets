"""
Git status dialog for viewing detailed Git repository information and history.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, GLib, Gio
import threading
from typing import List

from ...managers.git_manager import GitManager
from ...services.git_service import GitCommit, GitStatus
from ...ui.components.git_status_component import GitStatusComponent


class GitStatusDialog(Adw.Window):
    """Dialog for viewing Git repository status and history."""
    
    __gtype_name__ = "GitStatusDialog"
    
    def __init__(self, git_manager: GitManager, **kwargs):
        super().__init__(**kwargs)
        
        self.git_manager = git_manager
        self.status_component = GitStatusComponent(git_manager)
        
        self.set_title("Git Repository Status")
        self.set_default_size(700, 600)
        self.set_modal(True)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Git Status"))
        
        # Refresh button
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh status")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        header_bar.pack_start(refresh_button)
        
        main_box.append(header_bar)
        
        # Content with tabs
        self.view_stack = Adw.ViewStack()
        main_box.append(self.view_stack)
        
        # Status tab
        self._setup_status_tab()
        
        # History tab
        self._setup_history_tab()
        
        # View switcher
        view_switcher = Adw.ViewSwitcher()
        view_switcher.set_stack(self.view_stack)
        view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        header_bar.set_title_widget(view_switcher)
    
    def _setup_status_tab(self):
        """Set up the status tab."""
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        scrolled.set_child(content_box)
        
        # Add detailed status widget
        self.detailed_status = self.status_component.create_detailed_status_widget()
        content_box.append(self.detailed_status)
        
        # Repository summary
        summary_group = Adw.PreferencesGroup()
        summary_group.set_title("Repository Summary")
        content_box.append(summary_group)
        
        self.summary_text = Gtk.TextView()
        self.summary_text.set_editable(False)
        self.summary_text.set_cursor_visible(False)
        self.summary_text.set_wrap_mode(Gtk.WrapMode.WORD)
        self.summary_text.add_css_class("card")
        self.summary_text.set_margin_top(6)
        self.summary_text.set_margin_bottom(6)
        self.summary_text.set_margin_start(6)
        self.summary_text.set_margin_end(6)
        
        summary_frame = Gtk.Frame()
        summary_frame.set_child(self.summary_text)
        summary_group.add(summary_frame)

        # Add the page to the view stack with proper method
        status_page = self.view_stack.add_named(scrolled, "status")
        status_page.set_title("Status")
        status_page.set_icon_name("dialog-information-symbolic")
    
    def _setup_history_tab(self):
        """Set up the history tab."""
        # Main box
        history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Toolbar
        toolbar = Adw.HeaderBar()
        toolbar.add_css_class("flat")
        
        # Commit button
        commit_button = Gtk.Button(label="Commit Changes")
        commit_button.set_icon_name("document-save-symbolic")
        commit_button.add_css_class("suggested-action")
        commit_button.connect("clicked", self._on_commit_clicked)
        toolbar.pack_start(commit_button)
        self.commit_button = commit_button
        
        history_box.append(toolbar)
        
        # History list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        history_box.append(scrolled)
        
        # Create list model and view
        self.history_model = Gio.ListStore.new(GObject.Object)
        
        self.history_list = Gtk.ListView()
        self.history_list.set_model(Gtk.NoSelection.new(self.history_model))
        
        # Create factory for list items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_history_item_setup)
        factory.connect("bind", self._on_history_item_bind)
        self.history_list.set_factory(factory)
        
        scrolled.set_child(self.history_list)

        # Add the history page to the view stack
        history_page = self.view_stack.add_named(history_box, "history")
        history_page.set_title("History")
        history_page.set_icon_name("document-open-recent-symbolic")
    
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
    
    def _on_refresh_clicked(self, button):
        """Handle refresh button click."""
        self.status_component.refresh_status()
        self._load_data()
    
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
