"""
Tests for the models module.
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import secrets
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secrets.models import PasswordEntry, SearchResult, AppState


class TestPasswordEntry(unittest.TestCase):
    """Test cases for PasswordEntry model."""
    
    def test_password_entry_creation(self):
        """Test creating a password entry."""
        entry = PasswordEntry(
            path="Services/Gmail",
            password="secret123",
            username="user@example.com",
            url="https://gmail.com",
            notes="My email account"
        )
        
        self.assertEqual(entry.path, "Services/Gmail")
        self.assertEqual(entry.password, "secret123")
        self.assertEqual(entry.username, "user@example.com")
        self.assertEqual(entry.url, "https://gmail.com")
        self.assertEqual(entry.notes, "My email account")
        self.assertFalse(entry.is_folder)
    
    def test_password_entry_name_property(self):
        """Test the name property returns the basename."""
        entry = PasswordEntry(path="Services/Gmail/Personal")
        self.assertEqual(entry.name, "Personal")
        
        entry = PasswordEntry(path="SimplePassword")
        self.assertEqual(entry.name, "SimplePassword")
    
    def test_password_entry_parent_path_property(self):
        """Test the parent_path property."""
        entry = PasswordEntry(path="Services/Gmail/Personal")
        self.assertEqual(entry.parent_path, "Services/Gmail")
        
        entry = PasswordEntry(path="Services/Gmail")
        self.assertEqual(entry.parent_path, "Services")
        
        entry = PasswordEntry(path="SimplePassword")
        self.assertEqual(entry.parent_path, "")
    
    def test_password_entry_folder(self):
        """Test creating a folder entry."""
        entry = PasswordEntry(path="Services", is_folder=True)
        self.assertTrue(entry.is_folder)
        self.assertEqual(entry.name, "Services")
    
    def test_password_entry_to_dict(self):
        """Test converting entry to dictionary."""
        entry = PasswordEntry(
            path="Services/Gmail",
            password="secret123",
            username="user@example.com"
        )
        
        expected = {
            'path': "Services/Gmail",
            'password': "secret123",
            'username': "user@example.com",
            'url': None,
            'notes': None,
            'is_folder': False
        }
        
        self.assertEqual(entry.to_dict(), expected)
    
    def test_password_entry_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            'path': "Services/Gmail",
            'password': "secret123",
            'username': "user@example.com",
            'url': "https://gmail.com",
            'notes': "My email",
            'is_folder': False
        }
        
        entry = PasswordEntry.from_dict(data)
        
        self.assertEqual(entry.path, "Services/Gmail")
        self.assertEqual(entry.password, "secret123")
        self.assertEqual(entry.username, "user@example.com")
        self.assertEqual(entry.url, "https://gmail.com")
        self.assertEqual(entry.notes, "My email")
        self.assertFalse(entry.is_folder)


class TestSearchResult(unittest.TestCase):
    """Test cases for SearchResult model."""
    
    def test_search_result_with_results(self):
        """Test search result with matches."""
        entries = [
            PasswordEntry(path="Services/Gmail"),
            PasswordEntry(path="Services/GitHub")
        ]
        
        result = SearchResult("gmail", entries, 2)
        
        self.assertEqual(result.query, "gmail")
        self.assertEqual(len(result.entries), 2)
        self.assertEqual(result.total_count, 2)
        self.assertTrue(result.has_results)
    
    def test_search_result_no_results(self):
        """Test search result with no matches."""
        result = SearchResult("nonexistent", [], 0)
        
        self.assertEqual(result.query, "nonexistent")
        self.assertEqual(len(result.entries), 0)
        self.assertEqual(result.total_count, 0)
        self.assertFalse(result.has_results)
    
    def test_search_result_summary(self):
        """Test search result summary messages."""
        # No results
        result = SearchResult("test", [], 0)
        self.assertEqual(result.get_summary(), "No results found for 'test'")
        
        # One result
        entries = [PasswordEntry(path="test")]
        result = SearchResult("test", entries, 1)
        self.assertEqual(result.get_summary(), "Found 1 result for 'test'")
        
        # Multiple results
        entries = [PasswordEntry(path="test1"), PasswordEntry(path="test2")]
        result = SearchResult("test", entries, 2)
        self.assertEqual(result.get_summary(), "Found 2 results for 'test'")


class TestAppState(unittest.TestCase):
    """Test cases for AppState model."""
    
    def test_app_state_initialization(self):
        """Test app state initialization."""
        state = AppState()
        
        self.assertIsNone(state.selected_entry)
        self.assertEqual(state.search_query, "")
        self.assertFalse(state.password_visible)
        self.assertIsNone(state.auto_hide_timeout_id)
    
    def test_app_state_set_selected_entry(self):
        """Test setting selected entry."""
        state = AppState()
        entry = PasswordEntry(path="test")
        
        state.set_selected_entry(entry)
        
        self.assertEqual(state.selected_entry, entry)
        self.assertFalse(state.password_visible)
    
    def test_app_state_clear_selection(self):
        """Test clearing selection."""
        state = AppState()
        entry = PasswordEntry(path="test")
        state.set_selected_entry(entry)
        state.password_visible = True
        
        state.clear_selection()
        
        self.assertIsNone(state.selected_entry)
        self.assertFalse(state.password_visible)


if __name__ == '__main__':
    unittest.main()
