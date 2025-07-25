import gi
import json
import csv
import os
import threading
from typing import Dict, List, Tuple, Optional

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GLib

from secrets.app_info import APP_ID


@Gtk.Template(resource_path="/io/github/tobagin/secrets/ui/dialogs/import_export_dialog.ui")
class ImportExportDialog(Adw.Window):
    """Dialog for importing and exporting password data."""

    __gtype_name__ = "ImportExportDialog"

    # Template widgets
    export_json_button = Gtk.Template.Child()
    export_csv_button = Gtk.Template.Child()
    import_json_button = Gtk.Template.Child()
    import_csv_button = Gtk.Template.Child()
    
    # Password manager import buttons
    import_1password_button = Gtk.Template.Child()
    import_lastpass_button = Gtk.Template.Child()
    import_bitwarden_button = Gtk.Template.Child()
    import_dashlane_button = Gtk.Template.Child()
    import_keepass_button = Gtk.Template.Child()
    import_protonpass_button = Gtk.Template.Child()
    
    # Browser import buttons
    import_chrome_button = Gtk.Template.Child()
    import_firefox_button = Gtk.Template.Child()
    import_safari_button = Gtk.Template.Child()
    import_edge_button = Gtk.Template.Child()

    def __init__(self, parent_window, password_store, toast_manager, refresh_callback=None, **kwargs):
        super().__init__(**kwargs)

        self.set_transient_for(parent_window)

        self.password_store = password_store
        self.toast_manager = toast_manager
        self.refresh_callback = refresh_callback
        
        # Threading for imports
        self._import_thread = None
        self._is_importing = False

        self._setup_signals()
    
    def _setup_signals(self):
        """Setup signal connections for UI elements."""
        # Connect export signals
        self.export_json_button.connect("clicked", self._on_export_json)
        self.export_csv_button.connect("clicked", self._on_export_csv)
        
        # Connect generic import signals
        self.import_json_button.connect("clicked", self._on_import_json)
        self.import_csv_button.connect("clicked", self._on_import_csv)
        
        # Connect password manager import signals
        self.import_1password_button.connect("clicked", self._on_import_1password)
        self.import_lastpass_button.connect("clicked", self._on_import_lastpass)
        self.import_bitwarden_button.connect("clicked", self._on_import_bitwarden)
        self.import_dashlane_button.connect("clicked", self._on_import_dashlane)
        self.import_keepass_button.connect("clicked", self._on_import_keepass)
        self.import_protonpass_button.connect("clicked", self._on_import_protonpass)
        
        # Connect browser import signals
        self.import_chrome_button.connect("clicked", self._on_import_chrome)
        self.import_firefox_button.connect("clicked", self._on_import_firefox)
        self.import_safari_button.connect("clicked", self._on_import_safari)
        self.import_edge_button.connect("clicked", self._on_import_edge)
    
    def _start_import_thread(self, import_func, file_path):
        """Start an import operation in a background thread."""
        if self._is_importing:
            self.toast_manager.show_error("Import already in progress")
            return
        
        self._is_importing = True
        
        # Show progress indication
        self.toast_manager.show_info("Import started...")
        
        # Close the import dialog since processing has started
        self.close()
        
        # Start the import thread
        self._import_thread = threading.Thread(
            target=self._import_wrapper,
            args=(import_func, file_path),
            daemon=True
        )
        self._import_thread.start()
    
    def _import_wrapper(self, import_func, file_path):
        """Wrapper to run import functions in thread and handle completion."""
        try:
            # Run the import function 
            import_func(file_path)
        except Exception as e:
            # If the import function doesn't handle its own errors, handle them here
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _set_import_buttons_sensitive(self, sensitive):
        """Enable or disable all import buttons."""
        self.import_json_button.set_sensitive(sensitive)
        self.import_csv_button.set_sensitive(sensitive)
        self.import_1password_button.set_sensitive(sensitive)
        self.import_lastpass_button.set_sensitive(sensitive)
        self.import_bitwarden_button.set_sensitive(sensitive)
        self.import_dashlane_button.set_sensitive(sensitive)
        self.import_keepass_button.set_sensitive(sensitive)
        self.import_protonpass_button.set_sensitive(sensitive)
        self.import_chrome_button.set_sensitive(sensitive)
        self.import_firefox_button.set_sensitive(sensitive)
        self.import_safari_button.set_sensitive(sensitive)
        self.import_edge_button.set_sensitive(sensitive)
    
    def _import_completed(self, imported_count, skipped_count, error_message=None):
        """Called when import operation completes (from main thread)."""
        self._is_importing = False
        self._set_import_buttons_sensitive(True)
        
        if error_message:
            self.toast_manager.show_error(f"Import failed: {error_message}")
        else:
            self.toast_manager.show_success(f"Imported {imported_count} passwords, skipped {skipped_count}")
            
            # Refresh the UI to show imported passwords
            if imported_count > 0:
                self._refresh_password_list()
    
    def _on_export_json(self, button):
        """Export passwords to JSON format."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Export to JSON")
        file_dialog.set_initial_name("passwords_export.json")
        
        # Set up file filter
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON files")
        json_filter.add_pattern("*.json")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(json_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.save(self, None, self._on_export_json_response, None)
    
    def _on_export_json_response(self, dialog, result, user_data):
        """Handle JSON export file selection."""
        try:
            file = dialog.save_finish(result)
            if file:
                self._export_to_json(file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Export cancelled or failed: {e}")
    
    def _export_to_json(self, file_path: str):
        """Export passwords to JSON file."""
        try:
            passwords = self.password_store.list_passwords()
            export_data = []
            
            for password_path in passwords:
                details = self.password_store.get_parsed_password_details(password_path)
                if 'error' not in details:
                    export_data.append({
                        'path': password_path,
                        'password': details.get('password', ''),
                        'username': details.get('username', ''),
                        'url': details.get('url', ''),
                        'notes': details.get('notes', '')
                    })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.toast_manager.show_success(f"Exported {len(export_data)} passwords to {file_path}")
            
        except Exception as e:
            self.toast_manager.show_error(f"Export failed: {e}")
    
    def _on_export_csv(self, button):
        """Export passwords to CSV format."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Export to CSV")
        file_dialog.set_initial_name("passwords_export.csv")
        
        # Set up file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.save(self, None, self._on_export_csv_response, None)
    
    def _on_export_csv_response(self, dialog, result, user_data):
        """Handle CSV export file selection."""
        try:
            file = dialog.save_finish(result)
            if file:
                self._export_to_csv(file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Export cancelled or failed: {e}")
    
    def _export_to_csv(self, file_path: str):
        """Export passwords to CSV file."""
        try:
            passwords = self.password_store.list_passwords()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Path', 'Password', 'Username', 'URL', 'Notes'])
                
                exported_count = 0
                for password_path in passwords:
                    details = self.password_store.get_parsed_password_details(password_path)
                    if 'error' not in details:
                        writer.writerow([
                            password_path,
                            details.get('password', ''),
                            details.get('username', ''),
                            details.get('url', ''),
                            details.get('notes', '')
                        ])
                        exported_count += 1
            
            self.toast_manager.show_success(f"Exported {exported_count} passwords to {file_path}")
            
        except Exception as e:
            self.toast_manager.show_error(f"Export failed: {e}")
    
    def _on_import_json(self, button):
        """Import passwords from JSON format."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from JSON")
        
        # Set up file filter
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON files")
        json_filter.add_pattern("*.json")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(json_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_json_response, None)
    
    def _on_import_json_response(self, dialog, result, user_data):
        """Handle JSON import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_json_threaded, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_json_threaded(self, file_path: str):
        """Import passwords from JSON file (runs in background thread)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            total_entries = len(import_data) if isinstance(import_data, list) else 0
            imported_count = 0
            skipped_count = 0
            processed_count = 0
            
            for entry in import_data:
                if isinstance(entry, dict) and 'path' in entry:
                    path = entry['path']
                    password = entry.get('password', '')
                    username = entry.get('username', '')
                    url = entry.get('url', '')
                    notes = entry.get('notes', '')
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if notes:
                        content_lines.append(f"notes: {notes}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
                
                processed_count += 1
                
                # Update progress every 10 entries for large files
                if processed_count % 10 == 0 and total_entries > 50:
                    progress_msg = f"Processing... {processed_count}/{total_entries}"
                    GLib.idle_add(lambda msg=progress_msg: self.toast_manager.show_info(msg))

            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)

        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _import_from_json(self, file_path: str):
        """Import passwords from JSON file (legacy method - for compatibility)."""
        self._import_from_json_threaded(file_path)
    
    def _on_import_csv(self, button):
        """Import passwords from CSV format."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from CSV")
        
        # Set up file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_csv_response, None)
    
    def _on_import_csv_response(self, dialog, result, user_data):
        """Handle CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_csv_threaded, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_csv_threaded(self, file_path: str):
        """Import passwords from CSV file (runs in background thread)."""
        try:
            imported_count = 0
            skipped_count = 0
            processed_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    path = row.get('Path', '').strip()
                    password = row.get('Password', '').strip()
                    username = row.get('Username', '').strip()
                    url = row.get('URL', '').strip()
                    notes = row.get('Notes', '').strip()
                    
                    processed_count += 1
                    
                    if not path or not password:
                        skipped_count += 1
                        continue
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if notes:
                        content_lines.append(f"notes: {notes}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
                    
                    # Update progress every 25 entries for large files
                    if processed_count % 25 == 0 and processed_count > 50:
                        progress_msg = f"Processing... {processed_count} entries"
                        GLib.idle_add(lambda msg=progress_msg: self.toast_manager.show_info(msg))

            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)

        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _import_from_csv(self, file_path: str):
        """Import passwords from CSV file (legacy method - for compatibility)."""
        self._import_from_csv_threaded(file_path)

    def _refresh_password_list(self):
        """Refresh the password list in the main window."""
        if self.refresh_callback:
            self.refresh_callback()

    # Password Manager Import Methods
    
    def _on_import_1password(self, button):
        """Import passwords from 1Password CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from 1Password CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_1password_response, None)
    
    def _on_import_1password_response(self, dialog, result, user_data):
        """Handle 1Password CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_1password_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_1password_csv(self, file_path: str):
        """Import passwords from 1Password CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # 1Password CSV format: Title, Username, Password, URL, Notes
                    title = row.get('Title', '').strip()
                    username = row.get('Username', '').strip()
                    password = row.get('Password', '').strip()
                    url = row.get('URL', '').strip()
                    notes = row.get('Notes', '').strip()
                    
                    if not title or not password:
                        skipped_count += 1
                        continue
                    
                    # Create path from title (sanitize for filesystem)
                    path = self._sanitize_path(title)
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if notes:
                        content_lines.append(f"notes: {notes}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread  
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_lastpass(self, button):
        """Import passwords from LastPass CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from LastPass CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_lastpass_response, None)
    
    def _on_import_lastpass_response(self, dialog, result, user_data):
        """Handle LastPass CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_lastpass_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_lastpass_csv(self, file_path: str):
        """Import passwords from LastPass CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # LastPass CSV format: url, username, password, extra, name, grouping, fav
                    name = row.get('name', '').strip()
                    username = row.get('username', '').strip()
                    password = row.get('password', '').strip()
                    url = row.get('url', '').strip()
                    extra = row.get('extra', '').strip()
                    grouping = row.get('grouping', '').strip()
                    
                    if not name or not password:
                        skipped_count += 1
                        continue
                    
                    # Create path from name and grouping
                    if grouping:
                        path = f"{self._sanitize_path(grouping)}/{self._sanitize_path(name)}"
                    else:
                        path = self._sanitize_path(name)
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if extra:
                        content_lines.append(f"notes: {extra}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_bitwarden(self, button):
        """Import passwords from Bitwarden JSON export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from Bitwarden JSON")
        
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON files")
        json_filter.add_pattern("*.json")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(json_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_bitwarden_response, None)
    
    def _on_import_bitwarden_response(self, dialog, result, user_data):
        """Handle Bitwarden JSON import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_bitwarden_json, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_bitwarden_json(self, file_path: str):
        """Import passwords from Bitwarden JSON file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Bitwarden export has 'items' array and 'folders' array
            items = data.get('items', [])
            folders = {folder['id']: folder['name'] for folder in data.get('folders', [])}
            
            for item in items:
                # Skip non-login items
                if item.get('type') != 1:  # 1 = login item
                    continue
                    
                name = item.get('name', '').strip()
                folder_id = item.get('folderId')
                login = item.get('login', {})
                notes = item.get('notes', '').strip()
                
                username = login.get('username', '').strip()
                password = login.get('password', '').strip()
                
                # Get URIs (Bitwarden can have multiple URIs)
                uris = login.get('uris', [])
                url = uris[0].get('uri', '').strip() if uris else ''
                
                if not name or not password:
                    skipped_count += 1
                    continue
                
                # Create path from name and folder
                if folder_id and folder_id in folders:
                    path = f"{self._sanitize_path(folders[folder_id])}/{self._sanitize_path(name)}"
                else:
                    path = self._sanitize_path(name)
                
                # Build content in pass format
                content_lines = [password]
                if username:
                    content_lines.append(f"username: {username}")
                if url:
                    content_lines.append(f"url: {url}")
                if notes:
                    content_lines.append(f"notes: {notes}")
                
                content = '\n'.join(content_lines)
                
                # Try to import
                success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                if success:
                    imported_count += 1
                else:
                    skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_dashlane(self, button):
        """Import passwords from Dashlane CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from Dashlane CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_dashlane_response, None)
    
    def _on_import_dashlane_response(self, dialog, result, user_data):
        """Handle Dashlane CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_dashlane_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_dashlane_csv(self, file_path: str):
        """Import passwords from Dashlane CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Dashlane CSV format: name, url, username, password, note, category
                    name = row.get('name', '').strip()
                    username = row.get('username', '').strip()
                    password = row.get('password', '').strip()
                    url = row.get('url', '').strip()
                    note = row.get('note', '').strip()
                    category = row.get('category', '').strip()
                    
                    if not name or not password:
                        skipped_count += 1
                        continue
                    
                    # Create path from name and category
                    if category:
                        path = f"{self._sanitize_path(category)}/{self._sanitize_path(name)}"
                    else:
                        path = self._sanitize_path(name)
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if note:
                        content_lines.append(f"notes: {note}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_keepass(self, button):
        """Import passwords from KeePass CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from KeePass CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_keepass_response, None)
    
    def _on_import_keepass_response(self, dialog, result, user_data):
        """Handle KeePass CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_keepass_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_keepass_csv(self, file_path: str):
        """Import passwords from KeePass CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # KeePass CSV format: Group, Title, Username, Password, URL, Notes
                    group = row.get('Group', '').strip()
                    title = row.get('Title', '').strip()
                    username = row.get('Username', '').strip()
                    password = row.get('Password', '').strip()
                    url = row.get('URL', '').strip()
                    notes = row.get('Notes', '').strip()
                    
                    if not title or not password:
                        skipped_count += 1
                        continue
                    
                    # Create path from title and group
                    if group and group != "Root":
                        path = f"{self._sanitize_path(group)}/{self._sanitize_path(title)}"
                    else:
                        path = self._sanitize_path(title)
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if notes:
                        content_lines.append(f"notes: {notes}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    # Browser Import Methods
    
    def _on_import_chrome(self, button):
        """Import passwords from Chrome CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from Chrome CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_chrome_response, None)
    
    def _on_import_chrome_response(self, dialog, result, user_data):
        """Handle Chrome CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_chrome_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_chrome_csv(self, file_path: str):
        """Import passwords from Chrome CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Chrome CSV format: name, url, username, password
                    name = row.get('name', '').strip()
                    url = row.get('url', '').strip()
                    username = row.get('username', '').strip()
                    password = row.get('password', '').strip()
                    
                    if not name or not password:
                        # Try to use URL as name if name is missing
                        if url and password:
                            name = self._extract_domain_from_url(url)
                        else:
                            skipped_count += 1
                            continue
                    
                    # Create path from name
                    path = f"browsers/chrome/{self._sanitize_path(name)}"
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_firefox(self, button):
        """Import passwords from Firefox CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from Firefox CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_firefox_response, None)
    
    def _on_import_firefox_response(self, dialog, result, user_data):
        """Handle Firefox CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_firefox_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_firefox_csv(self, file_path: str):
        """Import passwords from Firefox CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Firefox CSV format: url, username, password, httpRealm, formActionOrigin, guid, timeCreated, timeLastUsed, timePasswordChanged
                    url = row.get('url', '').strip()
                    username = row.get('username', '').strip()
                    password = row.get('password', '').strip()
                    
                    if not url or not password:
                        skipped_count += 1
                        continue
                    
                    # Extract name from URL
                    name = self._extract_domain_from_url(url)
                    
                    # Create path from name
                    path = f"browsers/firefox/{self._sanitize_path(name)}"
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_safari(self, button):
        """Import passwords from Safari CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from Safari CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_safari_response, None)
    
    def _on_import_safari_response(self, dialog, result, user_data):
        """Handle Safari CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_safari_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_safari_csv(self, file_path: str):
        """Import passwords from Safari CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Safari CSV format: Title, URL, Username, Password, Notes, OTPAuth
                    title = row.get('Title', '').strip()
                    url = row.get('URL', '').strip()
                    username = row.get('Username', '').strip()
                    password = row.get('Password', '').strip()
                    notes = row.get('Notes', '').strip()
                    
                    if not password:
                        skipped_count += 1
                        continue
                    
                    # Use title if available, otherwise extract from URL
                    if title:
                        name = title
                    elif url:
                        name = self._extract_domain_from_url(url)
                    else:
                        name = 'unknown_site'
                    
                    # Create path from name
                    path = f"browsers/safari/{self._sanitize_path(name)}"
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if notes:
                        content_lines.append(f"notes: {notes}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_edge(self, button):
        """Import passwords from Edge CSV export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from Edge CSV")
        
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(csv_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_edge_response, None)
    
    def _on_import_edge_response(self, dialog, result, user_data):
        """Handle Edge CSV import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_edge_csv, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_edge_csv(self, file_path: str):
        """Import passwords from Edge CSV file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Edge CSV format: name, url, username, password
                    name = row.get('name', '').strip()
                    url = row.get('url', '').strip()
                    username = row.get('username', '').strip()
                    password = row.get('password', '').strip()
                    
                    if not name or not password:
                        # Try to use URL as name if name is missing
                        if url and password:
                            name = self._extract_domain_from_url(url)
                        else:
                            skipped_count += 1
                            continue
                    
                    # Create path from name
                    path = f"browsers/edge/{self._sanitize_path(name)}"
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    
                    content = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _on_import_protonpass(self, button):
        """Import passwords from Proton Pass JSON export."""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Import from Proton Pass JSON")
        
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON files")
        json_filter.add_pattern("*.json")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(json_filter)
        file_dialog.set_filters(filter_list)
        
        file_dialog.open(self, None, self._on_import_protonpass_response, None)
    
    def _on_import_protonpass_response(self, dialog, result, user_data):
        """Handle Proton Pass JSON import file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._start_import_thread(self._import_from_protonpass_json, file.get_path())
        except Exception as e:
            self.toast_manager.show_error(f"Import cancelled or failed: {e}")
    
    def _import_from_protonpass_json(self, file_path: str):
        """Import passwords from Proton Pass JSON file."""
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Proton Pass export has 'vaults' array containing items
            vaults = data.get('vaults', {})
            
            for vault_id, vault_data in vaults.items():
                vault_name = vault_data.get('name', 'Unknown Vault')
                items = vault_data.get('items', [])
                
                for item in items:
                    # Skip non-login items
                    item_type = item.get('data', {}).get('type')
                    if item_type != 'login':
                        continue
                    
                    metadata = item.get('data', {}).get('metadata', {})
                    content = item.get('data', {}).get('content', {})
                    
                    name = metadata.get('name', '').strip()
                    note = metadata.get('note', '').strip()
                    
                    # Get login data
                    username = content.get('username', '').strip()
                    password = content.get('password', '').strip()
                    
                    # Get URLs - Proton Pass stores them as an array
                    urls = content.get('urls', [])
                    url = urls[0] if urls else ''
                    
                    # Get TOTP if available
                    totp = content.get('totpUri', '').strip()
                    
                    if not name or not password:
                        skipped_count += 1
                        continue
                    
                    # Create path from vault name and item name
                    if vault_name and vault_name != 'Personal':
                        path = f"protonpass/{self._sanitize_path(vault_name)}/{self._sanitize_path(name)}"
                    else:
                        path = f"protonpass/{self._sanitize_path(name)}"
                    
                    # Build content in pass format
                    content_lines = [password]
                    if username:
                        content_lines.append(f"username: {username}")
                    if url:
                        content_lines.append(f"url: {url}")
                    if totp:
                        # Extract the secret from the TOTP URI
                        totp_secret = self._extract_totp_secret(totp)
                        if totp_secret:
                            content_lines.append(f"totp: {totp_secret}")
                    if note:
                        content_lines.append(f"notes: {note}")
                    
                    content_text = '\n'.join(content_lines)
                    
                    # Try to import
                    success, message = self.password_store.insert_password(path, content_text, multiline=True, force=False)
                    if success:
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            # Schedule completion callback on main thread
            GLib.idle_add(self._import_completed, imported_count, skipped_count)
                
        except Exception as e:
            # Schedule error callback on main thread
            GLib.idle_add(self._import_completed, 0, 0, str(e))
    
    def _extract_totp_secret(self, totp_uri: str) -> str:
        """Extract TOTP secret from URI format."""
        try:
            from urllib.parse import urlparse, parse_qs
            
            # Parse the TOTP URI (otpauth://totp/...)
            parsed = urlparse(totp_uri)
            if parsed.scheme != 'otpauth' or parsed.netloc != 'totp':
                return ''
            
            # Extract secret from query parameters
            params = parse_qs(parsed.query)
            secret = params.get('secret', [''])[0]
            return secret
        except Exception:
            return ''
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL for use as password name."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.split('.')[0] if domain else 'unknown_site'
        except:
            return 'unknown_site'
    
    def _sanitize_path(self, title: str) -> str:
        """Sanitize a title for use as a filesystem path."""
        # Replace problematic characters with underscores
        import re
        sanitized = re.sub(r'[^\w\s-]', '_', title)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.strip('_').lower()
