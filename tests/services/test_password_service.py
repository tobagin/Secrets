"""Unit tests for PasswordService."""

import os
from typing import List
from unittest.mock import Mock, MagicMock, patch

import pytest

from src.secrets.models import PasswordEntry
from src.secrets.services.password_service import PasswordService
from src.secrets.password_store import PasswordStore


class TestPasswordService:
    """Test cases for PasswordService."""
    
    @pytest.fixture
    def mock_password_store(self):
        """Create a mock PasswordStore."""
        store = Mock(spec=PasswordStore)
        store.is_initialized = True
        return store
    
    @pytest.fixture
    def password_service(self, mock_password_store):
        """Create a PasswordService instance with mocked store."""
        return PasswordService(mock_password_store)
    
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear password cache before each test."""
        from src.secrets.performance import password_cache
        password_cache.clear()
        yield
        password_cache.clear()
    
    def test_get_all_entries_not_initialized(self, password_service, mock_password_store):
        """Test get_all_entries when store is not initialized."""
        mock_password_store.is_initialized = False
        
        entries = password_service.get_all_entries()
        
        assert entries == []
        mock_password_store.list_passwords.assert_not_called()
    
    def test_get_all_entries_empty(self, password_service, mock_password_store):
        """Test get_all_entries with no passwords."""
        mock_password_store.list_passwords.return_value = []
        
        entries = password_service.get_all_entries()
        
        assert entries == []
    
    def test_get_all_entries_single_password(self, password_service, mock_password_store):
        """Test get_all_entries with a single password."""
        mock_password_store.list_passwords.return_value = ["test_password"]
        
        entries = password_service.get_all_entries()
        
        assert len(entries) == 1
        assert entries[0].path == "test_password"
        assert not entries[0].is_folder
    
    def test_get_all_entries_with_folders(self, password_service, mock_password_store):
        """Test get_all_entries with nested folder structure."""
        mock_password_store.list_passwords.return_value = [
            "folder1/password1",
            "folder1/folder2/password2",
            "folder3/password3"
        ]
        
        entries = password_service.get_all_entries()
        
        # Should have 3 passwords + 3 folders
        assert len(entries) == 6
        
        # Check folders are created
        paths = [e.path for e in entries]
        assert "folder1" in paths
        assert "folder1/folder2" in paths
        assert "folder3" in paths
        
        # Check folder entries
        folder_entries = [e for e in entries if e.is_folder]
        assert len(folder_entries) == 3
        
        # Check password entries
        password_entries = [e for e in entries if not e.is_folder]
        assert len(password_entries) == 3
    
    def test_get_all_entries_no_duplicate_folders(self, password_service, mock_password_store):
        """Test that folders are not duplicated."""
        mock_password_store.list_passwords.return_value = [
            "folder/password1",
            "folder/password2",
            "folder/subfolder/password3"
        ]
        
        entries = password_service.get_all_entries()
        
        # Count how many times each folder appears
        folder_paths = [e.path for e in entries if e.is_folder]
        assert folder_paths.count("folder") == 1
        assert folder_paths.count("folder/subfolder") == 1
    
    def test_get_entry_details_empty_path(self, password_service):
        """Test get_entry_details with empty path."""
        success, entry = password_service.get_entry_details("")
        
        assert not success
        assert entry.path == ""
    
    def test_get_entry_details_folder(self, password_service, mock_password_store):
        """Test get_entry_details for a folder."""
        mock_password_store.list_passwords.return_value = [
            "folder/password1",
            "folder/password2"
        ]
        
        success, entry = password_service.get_entry_details("folder")
        
        assert success
        assert entry.path == "folder"
        assert entry.is_folder
    
    def test_get_entry_details_password_success(self, password_service, mock_password_store):
        """Test get_entry_details for a password with all fields."""
        mock_password_store.list_passwords.return_value = ["test_password"]
        mock_password_store.get_parsed_password_details.return_value = {
            'password': 'secret123',
            'username': 'user@example.com',
            'url': 'https://example.com',
            'notes': 'Test notes'
        }
        
        success, entry = password_service.get_entry_details("test_password")
        
        assert success
        assert entry.path == "test_password"
        assert entry.password == "secret123"
        assert entry.username == "user@example.com"
        assert entry.url == "https://example.com"
        assert entry.notes == "Test notes"
        assert not entry.is_folder
    
    def test_get_entry_details_password_error(self, password_service, mock_password_store):
        """Test get_entry_details when password retrieval fails."""
        mock_password_store.list_passwords.return_value = []
        mock_password_store.get_parsed_password_details.return_value = {
            'error': 'Password not found'
        }
        
        success, entry = password_service.get_entry_details("missing_password")
        
        assert not success
        assert entry.path == "missing_password"
        assert not entry.is_folder
    
    def test_get_entry_details_caching(self, password_service, mock_password_store):
        """Test that password details are cached."""
        mock_password_store.list_passwords.return_value = ["test_password"]
        mock_password_store.get_parsed_password_details.return_value = {
            'password': 'secret123'
        }
        
        # First call
        success1, entry1 = password_service.get_entry_details("test_password")
        # Second call (should use cache)
        success2, entry2 = password_service.get_entry_details("test_password")
        
        # Both should succeed
        assert success1 and success2
        # Should only call the store once
        mock_password_store.get_parsed_password_details.assert_called_once()
        # Both should return the same password
        assert entry1.password == entry2.password == "secret123"
    
    def test_search_entries_empty_query(self, password_service, mock_password_store):
        """Test search_entries with empty query returns all entries."""
        mock_password_store.list_passwords.return_value = ["password1", "password2"]
        
        success, entries = password_service.search_entries("")
        
        assert success
        assert len(entries) == 2
        # Should call get_all_entries
        mock_password_store.list_passwords.assert_called()
    
    def test_search_entries_success(self, password_service, mock_password_store):
        """Test successful search."""
        mock_password_store.search_passwords.return_value = (True, ["password1", "password2"])
        
        success, entries = password_service.search_entries("test")
        
        assert success
        assert len(entries) == 2
        assert all(not e.is_folder for e in entries)
        assert entries[0].path == "password1"
        assert entries[1].path == "password2"
    
    def test_search_entries_failure(self, password_service, mock_password_store):
        """Test failed search."""
        mock_password_store.search_passwords.return_value = (False, None)
        
        success, entries = password_service.search_entries("test")
        
        assert not success
        assert entries == []
    
    def test_search_entries_no_results(self, password_service, mock_password_store):
        """Test search with no results."""
        mock_password_store.search_passwords.return_value = (True, [])
        
        success, entries = password_service.search_entries("nonexistent")
        
        assert success
        assert entries == []
    
    def test_is_folder_path(self, password_service, mock_password_store):
        """Test _is_folder_path method."""
        mock_password_store.list_passwords.return_value = [
            "folder/password1",
            "folder/subfolder/password2",
            "other/password3"
        ]
        
        # Test folder paths
        assert password_service._is_folder_path("folder")
        assert password_service._is_folder_path("folder/subfolder")
        assert password_service._is_folder_path("other")
        
        # Test non-folder paths
        assert not password_service._is_folder_path("folder/password1")
        assert not password_service._is_folder_path("nonexistent")
        assert not password_service._is_folder_path("fold")  # Partial match should fail