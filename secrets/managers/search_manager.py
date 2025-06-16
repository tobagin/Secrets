"""
Search manager for handling search functionality.
"""

from typing import Callable
from gi.repository import Gtk
from ..models import PasswordEntry, SearchResult
from .toast_manager import ToastManager


class SearchManager:
    """Manages search functionality."""
    
    def __init__(self, 
                 search_entry: Gtk.SearchEntry,
                 password_store,
                 toast_manager: ToastManager,
                 on_search_results: Callable[[SearchResult], None]):
        self.search_entry = search_entry
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.on_search_results = on_search_results
        
        # Connect signals
        self.search_entry.connect("search-changed", self._on_search_changed)
    
    def _on_search_changed(self, search_entry):
        """Handle search entry changes."""
        query = search_entry.get_text().strip()
        
        if not query:
            # Empty query - show all passwords
            self.on_search_results(SearchResult("", [], 0))
            return
        
        try:
            success, result = self.password_store.search_passwords(query)
            
            if success:
                entries = []
                if result:
                    for path_str in sorted(result):
                        entry = PasswordEntry(path=path_str, is_folder=False)
                        entries.append(entry)
                
                search_result = SearchResult(query, entries, len(entries))
                self.on_search_results(search_result)
                self.toast_manager.show_info(search_result.get_summary())
            else:
                # Error occurred
                self.toast_manager.show_error(f"Search failed: {result}")
                self.on_search_results(SearchResult(query, [], 0))
                
        except Exception as e:
            self.toast_manager.show_error(f"Search error: {e}")
            self.on_search_results(SearchResult(query, [], 0))
