"""
Metadata Manager for storing and retrieving color/icon metadata for folders and passwords.
"""

import os
import json
from typing import Dict, Optional, Any
from gi.repository import GLib


class MetadataManager:
    """Manages metadata storage for folders and passwords."""
    
    def __init__(self, store_dir: str):
        """
        Initialize the metadata manager.
        
        Args:
            store_dir: The password store directory
        """
        self.store_dir = store_dir
        self.metadata_file = os.path.join(store_dir, ".secrets_metadata.json")
        self._metadata = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from the JSON file."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {
                    "version": "1.0",
                    "folders": {},
                    "passwords": {}
                }
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load metadata file: {e}")
            self._metadata = {
                "version": "1.0",
                "folders": {},
                "passwords": {}
            }
    
    def _save_metadata(self):
        """Save metadata to the JSON file."""
        try:
            # Create a backup first
            if os.path.exists(self.metadata_file):
                backup_file = self.metadata_file + ".backup"
                try:
                    os.rename(self.metadata_file, backup_file)
                except OSError:
                    pass  # Backup failed, continue anyway
            
            # Write new metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
            
            # Remove backup on success
            backup_file = self.metadata_file + ".backup"
            if os.path.exists(backup_file):
                try:
                    os.remove(backup_file)
                except OSError:
                    pass
                    
        except OSError as e:
            print(f"Error saving metadata: {e}")
            # Try to restore backup
            backup_file = self.metadata_file + ".backup"
            if os.path.exists(backup_file):
                try:
                    os.rename(backup_file, self.metadata_file)
                except OSError:
                    pass
    
    def set_folder_metadata(self, folder_path: str, color: str, icon: str):
        """
        Set metadata for a folder.
        
        Args:
            folder_path: The folder path (relative to store root)
            color: The color for the folder
            icon: The icon name for the folder
        """
        if "folders" not in self._metadata:
            self._metadata["folders"] = {}
        
        self._metadata["folders"][folder_path] = {
            "color": color,
            "icon": icon
        }
        
        self._save_metadata()
    
    def get_folder_metadata(self, folder_path: str) -> Dict[str, str]:
        """
        Get metadata for a folder.
        
        Args:
            folder_path: The folder path (relative to store root)
            
        Returns:
            Dictionary with 'color' and 'icon' keys, or defaults if not found
        """
        folders = self._metadata.get("folders", {})
        folder_meta = folders.get(folder_path, {})
        
        return {
            "color": folder_meta.get("color", "#3584e4"),  # Default blue
            "icon": folder_meta.get("icon", "folder-symbolic")  # Default folder icon
        }
    
    def set_password_metadata(self, password_path: str, color: str, icon: str):
        """
        Set metadata for a password.
        
        Args:
            password_path: The password path (relative to store root)
            color: The color for the password
            icon: The icon name for the password
        """
        if "passwords" not in self._metadata:
            self._metadata["passwords"] = {}
        
        self._metadata["passwords"][password_path] = {
            "color": color,
            "icon": icon
        }
        
        self._save_metadata()

    def set_password_favicon(self, password_path: str, favicon_data: str):
        """
        Set favicon base64 data for a password.

        Args:
            password_path: The password path (relative to store root)
            favicon_data: The base64-encoded favicon data
        """
        print(f"📝 MetadataManager: Setting favicon data for {password_path} ({len(favicon_data)} chars)")

        if "passwords" not in self._metadata:
            self._metadata["passwords"] = {}

        if password_path not in self._metadata["passwords"]:
            self._metadata["passwords"][password_path] = {}

        self._metadata["passwords"][password_path]["favicon_data"] = favicon_data
        self._save_metadata()
        print(f"✅ MetadataManager: Favicon data saved for {password_path}")

    def get_password_metadata(self, password_path: str) -> Dict[str, str]:
        """
        Get metadata for a password.

        Args:
            password_path: The password path (relative to store root)

        Returns:
            Dictionary with 'color', 'icon', and 'favicon' keys, or defaults if not found
        """
        passwords = self._metadata.get("passwords", {})
        password_meta = passwords.get(password_path, {})

        # Get favicon data (base64 encoded)
        favicon_data = password_meta.get("favicon_data")
        if favicon_data:
            print(f"📁 Found cached favicon data for {password_path} ({len(favicon_data)} chars)")

        return {
            "color": password_meta.get("color", "#9141ac"),  # Default purple
            "icon": password_meta.get("icon", "dialog-password-symbolic"),  # Default password icon
            "favicon_data": favicon_data  # Base64-encoded favicon data or None
        }
    
    def remove_folder_metadata(self, folder_path: str):
        """
        Remove metadata for a folder.
        
        Args:
            folder_path: The folder path (relative to store root)
        """
        folders = self._metadata.get("folders", {})
        if folder_path in folders:
            del folders[folder_path]
            self._save_metadata()
    
    def remove_password_metadata(self, password_path: str):
        """
        Remove metadata for a password.
        
        Args:
            password_path: The password path (relative to store root)
        """
        passwords = self._metadata.get("passwords", {})
        if password_path in passwords:
            del passwords[password_path]
            self._save_metadata()
    
    def rename_folder_metadata(self, old_path: str, new_path: str):
        """
        Rename folder metadata when a folder is renamed.
        
        Args:
            old_path: The old folder path
            new_path: The new folder path
        """
        folders = self._metadata.get("folders", {})
        if old_path in folders:
            # Move metadata to new path
            folders[new_path] = folders[old_path]
            del folders[old_path]
            self._save_metadata()
    
    def rename_password_metadata(self, old_path: str, new_path: str):
        """
        Rename password metadata when a password is renamed/moved.
        
        Args:
            old_path: The old password path
            new_path: The new password path
        """
        passwords = self._metadata.get("passwords", {})
        if old_path in passwords:
            # Move metadata to new path
            passwords[new_path] = passwords[old_path]
            del passwords[old_path]
            self._save_metadata()
    
    def get_all_folder_metadata(self) -> Dict[str, Dict[str, str]]:
        """Get metadata for all folders."""
        return self._metadata.get("folders", {}).copy()
    
    def get_all_password_metadata(self) -> Dict[str, Dict[str, str]]:
        """Get metadata for all passwords."""
        return self._metadata.get("passwords", {}).copy()
    
    def clear_all_metadata(self):
        """Clear all metadata."""
        self._metadata = {
            "version": "1.0",
            "folders": {},
            "passwords": {}
        }
        self._save_metadata()
    
    def export_metadata(self) -> str:
        """Export metadata as JSON string."""
        return json.dumps(self._metadata, indent=2, ensure_ascii=False)
    
    def import_metadata(self, json_data: str) -> bool:
        """
        Import metadata from JSON string.
        
        Args:
            json_data: JSON string containing metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            imported_data = json.loads(json_data)
            
            # Validate structure
            if not isinstance(imported_data, dict):
                return False
            
            if "folders" not in imported_data or "passwords" not in imported_data:
                return False
            
            # Merge with existing metadata
            if "folders" in imported_data:
                if "folders" not in self._metadata:
                    self._metadata["folders"] = {}
                self._metadata["folders"].update(imported_data["folders"])
            
            if "passwords" in imported_data:
                if "passwords" not in self._metadata:
                    self._metadata["passwords"] = {}
                self._metadata["passwords"].update(imported_data["passwords"])
            
            self._save_metadata()
            return True
            
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error importing metadata: {e}")
            return False
