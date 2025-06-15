"""
Service layer for password operations and business logic.
"""
from typing import Tuple, List, Optional, Dict, Any
import os
from ..models import PasswordEntry
from ..password_store import PasswordStore
from ..performance import password_cache, performance_monitor, memoize_with_ttl


class PasswordService:
    """Service layer for password operations."""
    
    def __init__(self, password_store: PasswordStore):
        self.password_store = password_store
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """Get all password entries as PasswordEntry objects."""
        if not self.password_store.is_initialized:
            return []
        
        raw_passwords = self.password_store.list_passwords()
        entries = []
        
        # Track folders we've seen
        folders_seen = set()
        
        for path_str in sorted(raw_passwords):
            # Add folder entries for parent directories
            parts = path_str.split(os.sep)
            for i in range(len(parts) - 1):
                folder_path = os.sep.join(parts[:i+1])
                if folder_path not in folders_seen:
                    folder_entry = PasswordEntry(path=folder_path, is_folder=True)
                    entries.append(folder_entry)
                    folders_seen.add(folder_path)
            
            # Add the password entry
            password_entry = PasswordEntry(path=path_str, is_folder=False)
            entries.append(password_entry)
        
        return entries
    
    @performance_monitor.time_function("get_entry_details")
    def get_entry_details(self, path: str) -> Tuple[bool, PasswordEntry]:
        """Get detailed information for a password entry with caching."""
        if not path:
            return False, PasswordEntry(path="")

        # Check cache first
        cached_entry = password_cache.get(path)
        if cached_entry is not None:
            return True, cached_entry

        # Check if it's a folder
        if self._is_folder_path(path):
            entry = PasswordEntry(path=path, is_folder=True)
            password_cache.put(path, entry)
            return True, entry

        # Get password details
        details = self.password_store.get_parsed_password_details(path)

        if 'error' in details:
            entry = PasswordEntry(path=path, is_folder=False)
            return False, entry

        entry = PasswordEntry(
            path=path,
            password=details.get('password'),
            username=details.get('username'),
            url=details.get('url'),
            notes=details.get('notes'),
            is_folder=False
        )

        # Cache the successful result
        password_cache.put(path, entry)
        return True, entry
    
    def _is_folder_path(self, path: str) -> bool:
        """Check if a path represents a folder."""
        all_passwords = self.password_store.list_passwords()
        return any(p.startswith(path + os.sep) for p in all_passwords)
    
    def search_entries(self, query: str) -> Tuple[bool, List[PasswordEntry]]:
        """Search for password entries."""
        if not query:
            return True, self.get_all_entries()
        
        success, result = self.password_store.search_passwords(query)
        
        if not success:
            return False, []
        
        entries = []
        if result:
            for path_str in sorted(result):
                entry = PasswordEntry(path=path_str, is_folder=False)
                entries.append(entry)
        
        return True, entries
    
    def create_entry(self, path: str, content: str) -> Tuple[bool, str]:
        """Create a new password entry."""
        result = self.password_store.insert_password(path, content, multiline=True, force=False)
        if result[0]:  # Success
            password_cache.invalidate(path)
        return result

    def update_entry(self, path: str, content: str) -> Tuple[bool, str]:
        """Update an existing password entry."""
        result = self.password_store.insert_password(path, content, multiline=True, force=True)
        if result[0]:  # Success
            password_cache.invalidate(path)
        return result

    def delete_entry(self, path: str) -> Tuple[bool, str]:
        """Delete a password entry."""
        result = self.password_store.delete_password(path)
        if result[0]:  # Success
            password_cache.invalidate(path)
        return result

    def move_entry(self, old_path: str, new_path: str) -> Tuple[bool, str]:
        """Move/rename a password entry."""
        result = self.password_store.move_password(old_path, new_path)
        if result[0]:  # Success
            password_cache.invalidate(old_path)
            password_cache.invalidate(new_path)
        return result
    
    def copy_password_to_clipboard(self, path: str) -> Tuple[bool, str]:
        """Copy password to clipboard using pass -c."""
        return self.password_store.copy_password(path)
    
    def get_raw_content(self, path: str) -> Tuple[bool, str]:
        """Get the raw content of a password file."""
        return self.password_store.get_password_content(path)
    
    def sync_pull(self) -> Tuple[bool, str]:
        """Pull changes from remote repository."""
        return self.password_store.git_pull()
    
    def sync_push(self) -> Tuple[bool, str]:
        """Push changes to remote repository."""
        return self.password_store.git_push()
    
    def is_initialized(self) -> bool:
        """Check if the password store is initialized."""
        return self.password_store.is_initialized
    
    def initialize_store(self, parent_window=None) -> bool:
        """Initialize the password store."""
        return self.password_store.ensure_store_initialized(parent_window)


class ValidationService:
    """Service for validating user input and operations."""
    
    @staticmethod
    def validate_password_path(path: str) -> Tuple[bool, str]:
        """Validate a password path."""
        if not path:
            return False, "Password path cannot be empty"
        
        if ".." in path or path.startswith("/"):
            return False, "Invalid password path"
        
        if path.endswith("/"):
            return False, "Password path cannot end with '/'"
        
        return True, ""
    
    @staticmethod
    def validate_password_content(content: str) -> Tuple[bool, str]:
        """Validate password content."""
        if not content:
            return False, "Password content cannot be empty"
        
        return True, ""
    
    @staticmethod
    def validate_gpg_id(gpg_id: str) -> Tuple[bool, str]:
        """Validate a GPG ID."""
        if not gpg_id:
            return False, "GPG ID cannot be empty"
        
        # Basic validation - could be enhanced
        if len(gpg_id.strip()) < 8:
            return False, "GPG ID seems too short"
        
        return True, ""


class HierarchyService:
    """Service for managing hierarchical password organization."""
    
    @staticmethod
    def build_hierarchy(entries: List[PasswordEntry]) -> Dict[str, Any]:
        """Build a hierarchical structure from flat password entries."""
        root = {}
        
        for entry in entries:
            parts = entry.path.split(os.sep)
            current = root
            
            for i, part in enumerate(parts):
                if part not in current:
                    is_final = (i == len(parts) - 1)
                    current[part] = {
                        'entry': entry if is_final else PasswordEntry(
                            path=os.sep.join(parts[:i+1]), 
                            is_folder=True
                        ),
                        'children': {} if not is_final else None
                    }
                
                if i < len(parts) - 1:  # Not the final part
                    current = current[part]['children']
        
        return root
    
    @staticmethod
    def get_parent_path(path: str) -> str:
        """Get the parent directory path."""
        parts = path.split(os.sep)
        return os.sep.join(parts[:-1]) if len(parts) > 1 else ""
    
    @staticmethod
    def get_entry_name(path: str) -> str:
        """Get the entry name (basename)."""
        return path.split(os.sep)[-1] if path else ""
