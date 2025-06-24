"""
Data models for the Secrets application.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from gi.repository import GObject, Gio


@dataclass
class PasswordEntry:
    """Represents a password entry with all its metadata."""
    path: str
    password: Optional[str] = None
    username: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    is_folder: bool = False
    
    @property
    def name(self) -> str:
        """Get the display name (basename) of the entry."""
        return self.path.split('/')[-1] if self.path else ""
    
    @property
    def parent_path(self) -> str:
        """Get the parent directory path."""
        parts = self.path.split('/')
        return '/'.join(parts[:-1]) if len(parts) > 1 else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'path': self.path,
            'password': self.password,
            'username': self.username,
            'url': self.url,
            'notes': self.notes,
            'is_folder': self.is_folder
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PasswordEntry':
        """Create from dictionary."""
        return cls(**data)


class PasswordListItem(GObject.Object):
    """GObject wrapper for password entries to use with Gio.ListStore."""
    
    def __init__(self, entry: PasswordEntry):
        super().__init__()
        self._entry = entry
        self._children_model = None
        
        if entry.is_folder:
            self._children_model = Gio.ListStore.new(PasswordListItem)
    
    @property
    def entry(self) -> PasswordEntry:
        return self._entry
    
    @property
    def name(self) -> str:
        return self._entry.name
    
    @property
    def full_path(self) -> str:
        return self._entry.path
    
    @property
    def is_folder(self) -> bool:
        return self._entry.is_folder
    
    @property
    def children_model(self) -> Optional[Gio.ListStore]:
        return self._children_model


class SearchResult:
    """Represents search results with metadata."""
    
    def __init__(self, query: str, entries: list[PasswordEntry], total_count: int):
        self.query = query
        self.entries = entries
        self.total_count = total_count
        self.has_results = len(entries) > 0
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the search results."""
        if not self.has_results:
            return f"No results found for '{self.query}'"
        elif self.total_count == 1:
            return f"Found 1 result for '{self.query}'"
        else:
            return f"Found {self.total_count} results for '{self.query}'"


class AppState:
    """Manages application state and settings."""
    
    def __init__(self):
        self.selected_entry: Optional[PasswordEntry] = None
        self.search_query: str = ""
        self.password_visible: bool = False
        self.auto_hide_timeout_id: Optional[int] = None
        
    def clear_selection(self):
        """Clear the current selection."""
        self.selected_entry = None
        self.password_visible = False
        if self.auto_hide_timeout_id:
            # Cancel timeout if active
            pass
    
    def set_selected_entry(self, entry: Optional[PasswordEntry]):
        """Set the currently selected entry."""
        self.selected_entry = entry
        self.password_visible = False
