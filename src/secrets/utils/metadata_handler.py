"""Metadata handling utilities for password entries."""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


@dataclass
class EntryMetadata:
    """Metadata for a password entry."""
    color: str = "blue"
    icon: str = "password"
    favicon_data: str = ""
    username: str = ""
    url: str = ""
    notes: str = ""
    created_at: str = ""
    modified_at: str = ""
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntryMetadata':
        """Create EntryMetadata from dictionary."""
        # Handle missing fields gracefully
        valid_fields = {k: v for k, v in data.items() if hasattr(cls, k)}
        return cls(**valid_fields)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def merge(self, other: 'EntryMetadata') -> 'EntryMetadata':
        """Merge with another metadata object, keeping non-empty values."""
        merged_data = self.to_dict()
        other_data = other.to_dict()
        
        for key, value in other_data.items():
            if value:  # Only override with non-empty values
                merged_data[key] = value
        
        return EntryMetadata.from_dict(merged_data)


@dataclass
class FolderMetadata:
    """Metadata for a folder."""
    color: str = "folder"
    icon: str = "folder"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FolderMetadata':
        """Create FolderMetadata from dictionary."""
        valid_fields = {k: v for k, v in data.items() if hasattr(cls, k)}
        return cls(**valid_fields)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class MetadataHandler:
    """Handles metadata operations for password entries and folders."""
    
    def __init__(self, store_dir: str):
        """
        Initialize metadata handler.
        
        Args:
            store_dir: Password store directory
        """
        self.store_dir = Path(store_dir)
        self.metadata_dir = self.store_dir / ".metadata"
        self._cache: Dict[str, EntryMetadata] = {}
        self._folder_cache: Dict[str, FolderMetadata] = {}
        
        # Ensure metadata directory exists
        self.metadata_dir.mkdir(exist_ok=True)
    
    def get_entry_metadata(self, path: str) -> EntryMetadata:
        """
        Get metadata for a password entry.
        
        Args:
            path: Entry path relative to store directory
            
        Returns:
            EntryMetadata object
        """
        if path in self._cache:
            return self._cache[path]
        
        metadata_file = self.metadata_dir / f"{path}.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                metadata = EntryMetadata.from_dict(data)
            except (json.JSONDecodeError, OSError):
                metadata = EntryMetadata()
        else:
            metadata = EntryMetadata()
        
        # Cache the result
        self._cache[path] = metadata
        return metadata
    
    def set_entry_metadata(self, path: str, metadata: EntryMetadata) -> bool:
        """
        Set metadata for a password entry.
        
        Args:
            path: Entry path relative to store directory
            metadata: EntryMetadata object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_file = self.metadata_dir / f"{path}.json"
            metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            # Update cache
            self._cache[path] = metadata
            return True
            
        except OSError:
            return False
    
    def get_folder_metadata(self, path: str) -> FolderMetadata:
        """
        Get metadata for a folder.
        
        Args:
            path: Folder path relative to store directory
            
        Returns:
            FolderMetadata object
        """
        if path in self._folder_cache:
            return self._folder_cache[path]
        
        metadata_file = self.metadata_dir / f"{path}/_folder.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                metadata = FolderMetadata.from_dict(data)
            except (json.JSONDecodeError, OSError):
                metadata = FolderMetadata()
        else:
            metadata = FolderMetadata()
        
        # Cache the result
        self._folder_cache[path] = metadata
        return metadata
    
    def set_folder_metadata(self, path: str, metadata: FolderMetadata) -> bool:
        """
        Set metadata for a folder.
        
        Args:
            path: Folder path relative to store directory
            metadata: FolderMetadata object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_file = self.metadata_dir / f"{path}/_folder.json"
            metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            # Update cache
            self._folder_cache[path] = metadata
            return True
            
        except OSError:
            return False
    
    def batch_get_metadata(self, paths: List[str]) -> Dict[str, EntryMetadata]:
        """
        Get metadata for multiple entries efficiently.
        
        Args:
            paths: List of entry paths
            
        Returns:
            Dictionary mapping paths to metadata
        """
        result = {}
        uncached_paths = []
        
        # Check cache first
        for path in paths:
            if path in self._cache:
                result[path] = self._cache[path]
            else:
                uncached_paths.append(path)
        
        # Load uncached metadata
        for path in uncached_paths:
            metadata = self.get_entry_metadata(path)
            result[path] = metadata
        
        return result
    
    def search_by_tag(self, tag: str) -> List[str]:
        """
        Search for entries by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of entry paths with the tag
        """
        matching_paths = []
        
        # Search through metadata files
        for metadata_file in self.metadata_dir.glob("**/*.json"):
            if metadata_file.name.startswith("_"):
                continue  # Skip folder metadata
            
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if tag in data.get("tags", []):
                    # Convert metadata file path back to entry path
                    relative_path = metadata_file.relative_to(self.metadata_dir)
                    entry_path = str(relative_path).replace(".json", "")
                    matching_paths.append(entry_path)
                    
            except (json.JSONDecodeError, OSError):
                continue
        
        return matching_paths
    
    def get_all_tags(self) -> List[str]:
        """
        Get all tags used in the password store.
        
        Returns:
            List of unique tags
        """
        all_tags = set()
        
        # Collect tags from entry metadata
        for metadata_file in self.metadata_dir.glob("**/*.json"):
            if metadata_file.name.startswith("_"):
                continue  # Skip folder metadata
            
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                tags = data.get("tags", [])
                all_tags.update(tags)
                
            except (json.JSONDecodeError, OSError):
                continue
        
        return sorted(list(all_tags))
    
    def cleanup_orphaned_metadata(self) -> int:
        """
        Remove metadata files for entries that no longer exist.
        
        Returns:
            Number of orphaned files removed
        """
        removed_count = 0
        
        for metadata_file in self.metadata_dir.glob("**/*.json"):
            if metadata_file.name.startswith("_"):
                continue  # Skip folder metadata
            
            # Convert metadata file path back to entry path
            relative_path = metadata_file.relative_to(self.metadata_dir)
            entry_path = str(relative_path).replace(".json", "")
            
            # Check if corresponding .gpg file exists
            gpg_file = self.store_dir / f"{entry_path}.gpg"
            if not gpg_file.exists():
                try:
                    metadata_file.unlink()
                    removed_count += 1
                    # Remove from cache if present
                    self._cache.pop(entry_path, None)
                except OSError:
                    pass
        
        return removed_count
    
    def clear_cache(self):
        """Clear the metadata cache."""
        self._cache.clear()
        self._folder_cache.clear()
    
    def export_metadata(self, output_file: str) -> bool:
        """
        Export all metadata to a JSON file.
        
        Args:
            output_file: Path to output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                "entries": {},
                "folders": {}
            }
            
            # Export entry metadata
            for metadata_file in self.metadata_dir.glob("**/*.json"):
                if metadata_file.name.startswith("_"):
                    continue
                
                relative_path = metadata_file.relative_to(self.metadata_dir)
                entry_path = str(relative_path).replace(".json", "")
                
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        export_data["entries"][entry_path] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue
            
            # Export folder metadata
            for metadata_file in self.metadata_dir.glob("**/_folder.json"):
                relative_path = metadata_file.relative_to(self.metadata_dir)
                folder_path = str(relative_path.parent)
                
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        export_data["folders"][folder_path] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True
            
        except OSError:
            return False
    
    def import_metadata(self, input_file: str) -> Tuple[bool, str]:
        """
        Import metadata from a JSON file.
        
        Args:
            input_file: Path to input file
            
        Returns:
            (success, message)
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            entries_imported = 0
            folders_imported = 0
            
            # Import entry metadata
            for path, metadata_dict in import_data.get("entries", {}).items():
                metadata = EntryMetadata.from_dict(metadata_dict)
                if self.set_entry_metadata(path, metadata):
                    entries_imported += 1
            
            # Import folder metadata
            for path, metadata_dict in import_data.get("folders", {}).items():
                metadata = FolderMetadata.from_dict(metadata_dict)
                if self.set_folder_metadata(path, metadata):
                    folders_imported += 1
            
            message = f"Imported {entries_imported} entry metadata and {folders_imported} folder metadata"
            return True, message
            
        except (OSError, json.JSONDecodeError, KeyError) as e:
            return False, f"Import failed: {e}"