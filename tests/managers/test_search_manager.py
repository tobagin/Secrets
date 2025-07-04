"""Unit tests for SearchManager."""

from unittest.mock import Mock, MagicMock, call

import pytest
from gi.repository import Gtk

from src.secrets.managers.search_manager import SearchManager
from src.secrets.managers.toast_manager import ToastManager
from src.secrets.models import PasswordEntry, SearchResult


class TestSearchManager:
    """Test cases for SearchManager."""
    
    @pytest.fixture
    def mock_search_entry(self):
        """Create a mock Gtk.SearchEntry."""
        entry = Mock(spec=Gtk.SearchEntry)
        entry.get_text.return_value = ""
        entry.connect = Mock()
        return entry
    
    @pytest.fixture
    def mock_password_store(self):
        """Create a mock password store."""
        store = Mock()
        store.search_passwords.return_value = (True, [])
        return store
    
    @pytest.fixture
    def mock_toast_manager(self):
        """Create a mock ToastManager."""
        return Mock(spec=ToastManager)
    
    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback function."""
        return Mock()
    
    @pytest.fixture
    def search_manager(self, mock_search_entry, mock_password_store, mock_toast_manager, mock_callback):
        """Create a SearchManager instance."""
        return SearchManager(
            mock_search_entry,
            mock_password_store,
            mock_toast_manager,
            mock_callback
        )
    
    def test_init_connects_signal(self, mock_search_entry, mock_password_store, mock_toast_manager, mock_callback):
        """Test that SearchManager connects to search-changed signal."""
        search_manager = SearchManager(
            mock_search_entry,
            mock_password_store,
            mock_toast_manager,
            mock_callback
        )
        
        mock_search_entry.connect.assert_called_once_with(
            "search-changed",
            search_manager._on_search_changed
        )
    
    def test_on_search_changed_empty_query(self, search_manager, mock_callback):
        """Test search with empty query."""
        mock_search_entry = Mock()
        mock_search_entry.get_text.return_value = "  "  # Whitespace only
        
        search_manager._on_search_changed(mock_search_entry)
        
        # Should call callback with empty result
        mock_callback.assert_called_once()
        result = mock_callback.call_args[0][0]
        assert isinstance(result, SearchResult)
        assert result.query == ""
        assert result.entries == []
        assert result.total_count == 0
    
    def test_on_search_changed_successful_search(self, search_manager, mock_password_store, mock_callback, mock_toast_manager):
        """Test successful search with results."""
        mock_search_entry = Mock()
        mock_search_entry.get_text.return_value = "test"
        mock_password_store.search_passwords.return_value = (True, ["test/password1", "test/password2"])
        
        search_manager._on_search_changed(mock_search_entry)
        
        # Should call password store search
        mock_password_store.search_passwords.assert_called_with("test")
        
        # Should call callback with results
        mock_callback.assert_called_once()
        result = mock_callback.call_args[0][0]
        assert isinstance(result, SearchResult)
        assert result.query == "test"
        assert len(result.entries) == 2
        assert result.total_count == 2
        assert result.entries[0].path == "test/password1"
        assert result.entries[1].path == "test/password2"
        assert all(not entry.is_folder for entry in result.entries)
        
        # Should show info toast
        mock_toast_manager.show_info.assert_called_once()
    
    def test_on_search_changed_no_results(self, search_manager, mock_password_store, mock_callback, mock_toast_manager):
        """Test search with no results."""
        mock_search_entry = Mock()
        mock_search_entry.get_text.return_value = "nonexistent"
        mock_password_store.search_passwords.return_value = (True, [])
        
        search_manager._on_search_changed(mock_search_entry)
        
        # Should call callback with empty results
        mock_callback.assert_called_once()
        result = mock_callback.call_args[0][0]
        assert result.query == "nonexistent"
        assert result.entries == []
        assert result.total_count == 0
        
        # Should show info toast
        mock_toast_manager.show_info.assert_called_once()
    
    def test_on_search_changed_search_failure(self, search_manager, mock_password_store, mock_callback, mock_toast_manager):
        """Test search failure."""
        mock_search_entry = Mock()
        mock_search_entry.get_text.return_value = "test"
        mock_password_store.search_passwords.return_value = (False, "Search error")
        
        search_manager._on_search_changed(mock_search_entry)
        
        # Should call callback with empty results
        mock_callback.assert_called_once()
        result = mock_callback.call_args[0][0]
        assert result.query == "test"
        assert result.entries == []
        assert result.total_count == 0
        
        # Should show error toast
        mock_toast_manager.show_error.assert_called_with("Search failed: Search error")
    
    def test_on_search_changed_exception(self, search_manager, mock_password_store, mock_callback, mock_toast_manager):
        """Test exception during search."""
        mock_search_entry = Mock()
        mock_search_entry.get_text.return_value = "test"
        mock_password_store.search_passwords.side_effect = Exception("Unexpected error")
        
        search_manager._on_search_changed(mock_search_entry)
        
        # Should call callback with empty results
        mock_callback.assert_called_once()
        result = mock_callback.call_args[0][0]
        assert result.query == "test"
        assert result.entries == []
        assert result.total_count == 0
        
        # Should show error toast
        mock_toast_manager.show_error.assert_called()
        assert "Search error: Unexpected error" in mock_toast_manager.show_error.call_args[0][0]
    
    def test_search_results_sorted(self, search_manager, mock_password_store, mock_callback):
        """Test that search results are sorted."""
        mock_search_entry = Mock()
        mock_search_entry.get_text.return_value = "test"
        # Return unsorted list
        mock_password_store.search_passwords.return_value = (True, ["zebra", "apple", "banana"])
        
        search_manager._on_search_changed(mock_search_entry)
        
        result = mock_callback.call_args[0][0]
        paths = [entry.path for entry in result.entries]
        assert paths == ["apple", "banana", "zebra"]  # Should be sorted
    
    def test_search_strips_whitespace(self, search_manager, mock_password_store):
        """Test that search query is stripped of whitespace."""
        mock_search_entry = Mock()
        mock_search_entry.get_text.return_value = "  test query  "
        mock_password_store.search_passwords.return_value = (True, [])
        
        search_manager._on_search_changed(mock_search_entry)
        
        # Should search with trimmed query
        mock_password_store.search_passwords.assert_called_with("test query")