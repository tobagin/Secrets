"""
Tests for the services module.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import secrets
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secrets.services import PasswordService, ValidationService, HierarchyService
from secrets.models import PasswordEntry


class TestPasswordService(unittest.TestCase):
    """Test cases for PasswordService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_password_store = Mock()
        self.service = PasswordService(self.mock_password_store)
    
    def test_get_all_entries_empty_store(self):
        """Test getting entries from empty store."""
        self.mock_password_store.is_initialized = False
        
        entries = self.service.get_all_entries()
        
        self.assertEqual(entries, [])
    
    def test_get_all_entries_with_passwords(self):
        """Test getting entries with passwords."""
        self.mock_password_store.is_initialized = True
        self.mock_password_store.list_passwords.return_value = [
            "Services/Gmail",
            "Services/GitHub",
            "Personal/Bank"
        ]
        
        entries = self.service.get_all_entries()
        
        # Should have folders and password entries
        self.assertTrue(len(entries) > 3)  # At least the 3 passwords + folders
        
        # Check that we have the expected password entries
        password_paths = [e.path for e in entries if not e.is_folder]
        self.assertIn("Services/Gmail", password_paths)
        self.assertIn("Services/GitHub", password_paths)
        self.assertIn("Personal/Bank", password_paths)
        
        # Check that we have folder entries
        folder_paths = [e.path for e in entries if e.is_folder]
        self.assertIn("Services", folder_paths)
        self.assertIn("Personal", folder_paths)
    
    def test_get_entry_details_success(self):
        """Test getting entry details successfully."""
        self.mock_password_store.get_parsed_password_details.return_value = {
            'password': 'secret123',
            'username': 'user@example.com',
            'url': 'https://example.com',
            'notes': 'Test notes'
        }
        
        success, entry = self.service.get_entry_details("Services/Gmail")
        
        self.assertTrue(success)
        self.assertEqual(entry.path, "Services/Gmail")
        self.assertEqual(entry.password, "secret123")
        self.assertEqual(entry.username, "user@example.com")
        self.assertEqual(entry.url, "https://example.com")
        self.assertEqual(entry.notes, "Test notes")
        self.assertFalse(entry.is_folder)
    
    def test_get_entry_details_error(self):
        """Test getting entry details with error."""
        self.mock_password_store.get_parsed_password_details.return_value = {
            'error': 'Failed to decrypt'
        }
        
        success, entry = self.service.get_entry_details("Services/Gmail")
        
        self.assertFalse(success)
        self.assertEqual(entry.path, "Services/Gmail")
        self.assertIsNone(entry.password)
    
    def test_search_entries_success(self):
        """Test searching entries successfully."""
        self.mock_password_store.search_passwords.return_value = (True, [
            "Services/Gmail",
            "Services/GitHub"
        ])
        
        success, entries = self.service.search_entries("gmail")
        
        self.assertTrue(success)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].path, "Services/Gmail")
        self.assertEqual(entries[1].path, "Services/GitHub")
    
    def test_search_entries_empty_query(self):
        """Test searching with empty query returns all entries."""
        self.mock_password_store.is_initialized = True
        self.mock_password_store.list_passwords.return_value = ["test"]
        
        success, entries = self.service.search_entries("")
        
        self.assertTrue(success)
        # Should call get_all_entries
        self.mock_password_store.list_passwords.assert_called_once()
    
    def test_create_entry(self):
        """Test creating a new entry."""
        self.mock_password_store.insert_password.return_value = (True, "Success")
        
        success, message = self.service.create_entry("test", "content")
        
        self.assertTrue(success)
        self.assertEqual(message, "Success")
        self.mock_password_store.insert_password.assert_called_once_with(
            "test", "content", multiline=True, force=False
        )
    
    def test_update_entry(self):
        """Test updating an existing entry."""
        self.mock_password_store.insert_password.return_value = (True, "Updated")
        
        success, message = self.service.update_entry("test", "new content")
        
        self.assertTrue(success)
        self.assertEqual(message, "Updated")
        self.mock_password_store.insert_password.assert_called_once_with(
            "test", "new content", multiline=True, force=True
        )


class TestValidationService(unittest.TestCase):
    """Test cases for ValidationService."""
    
    def test_validate_password_path_valid(self):
        """Test validating valid password paths."""
        valid_paths = [
            "simple",
            "Services/Gmail",
            "Personal/Banking/Account1",
            "test-password",
            "test_password"
        ]
        
        for path in valid_paths:
            with self.subTest(path=path):
                valid, message = ValidationService.validate_password_path(path)
                self.assertTrue(valid, f"Path '{path}' should be valid")
                self.assertEqual(message, "")
    
    def test_validate_password_path_invalid(self):
        """Test validating invalid password paths."""
        invalid_paths = [
            "",  # Empty
            "/absolute/path",  # Starts with /
            "path/with/../dots",  # Contains ..
            "path/ending/",  # Ends with /
        ]
        
        for path in invalid_paths:
            with self.subTest(path=path):
                valid, message = ValidationService.validate_password_path(path)
                self.assertFalse(valid, f"Path '{path}' should be invalid")
                self.assertNotEqual(message, "")
    
    def test_validate_password_content_valid(self):
        """Test validating valid password content."""
        valid_content = [
            "simple password",
            "password\nwith\nmultiple\nlines",
            "password with special chars !@#$%^&*()"
        ]
        
        for content in valid_content:
            with self.subTest(content=content):
                valid, message = ValidationService.validate_password_content(content)
                self.assertTrue(valid)
                self.assertEqual(message, "")
    
    def test_validate_password_content_invalid(self):
        """Test validating invalid password content."""
        valid, message = ValidationService.validate_password_content("")
        self.assertFalse(valid)
        self.assertNotEqual(message, "")
    
    def test_validate_gpg_id_valid(self):
        """Test validating valid GPG IDs."""
        valid_ids = [
            "user@example.com",
            "1234567890ABCDEF",
            "long-gpg-key-id-here"
        ]
        
        for gpg_id in valid_ids:
            with self.subTest(gpg_id=gpg_id):
                valid, message = ValidationService.validate_gpg_id(gpg_id)
                self.assertTrue(valid)
                self.assertEqual(message, "")
    
    def test_validate_gpg_id_invalid(self):
        """Test validating invalid GPG IDs."""
        invalid_ids = [
            "",  # Empty
            "short",  # Too short
        ]
        
        for gpg_id in invalid_ids:
            with self.subTest(gpg_id=gpg_id):
                valid, message = ValidationService.validate_gpg_id(gpg_id)
                self.assertFalse(valid)
                self.assertNotEqual(message, "")


class TestHierarchyService(unittest.TestCase):
    """Test cases for HierarchyService."""
    
    def test_build_hierarchy_simple(self):
        """Test building hierarchy from simple entries."""
        entries = [
            PasswordEntry(path="Gmail", is_folder=False),
            PasswordEntry(path="GitHub", is_folder=False)
        ]
        
        hierarchy = HierarchyService.build_hierarchy(entries)
        
        self.assertIn("Gmail", hierarchy)
        self.assertIn("GitHub", hierarchy)
        self.assertEqual(hierarchy["Gmail"]["entry"].path, "Gmail")
        self.assertEqual(hierarchy["GitHub"]["entry"].path, "GitHub")
    
    def test_build_hierarchy_nested(self):
        """Test building hierarchy from nested entries."""
        entries = [
            PasswordEntry(path="Services/Gmail", is_folder=False),
            PasswordEntry(path="Services/GitHub", is_folder=False),
            PasswordEntry(path="Personal/Bank", is_folder=False)
        ]
        
        hierarchy = HierarchyService.build_hierarchy(entries)
        
        self.assertIn("Services", hierarchy)
        self.assertIn("Personal", hierarchy)
        
        # Check Services folder
        services = hierarchy["Services"]
        self.assertTrue(services["entry"].is_folder)
        self.assertIn("Gmail", services["children"])
        self.assertIn("GitHub", services["children"])
        
        # Check Personal folder
        personal = hierarchy["Personal"]
        self.assertTrue(personal["entry"].is_folder)
        self.assertIn("Bank", personal["children"])
    
    def test_get_parent_path(self):
        """Test getting parent path."""
        self.assertEqual(HierarchyService.get_parent_path("Services/Gmail"), "Services")
        self.assertEqual(HierarchyService.get_parent_path("Services/Email/Gmail"), "Services/Email")
        self.assertEqual(HierarchyService.get_parent_path("Simple"), "")
    
    def test_get_entry_name(self):
        """Test getting entry name."""
        self.assertEqual(HierarchyService.get_entry_name("Services/Gmail"), "Gmail")
        self.assertEqual(HierarchyService.get_entry_name("Services/Email/Gmail"), "Gmail")
        self.assertEqual(HierarchyService.get_entry_name("Simple"), "Simple")
        self.assertEqual(HierarchyService.get_entry_name(""), "")


if __name__ == '__main__':
    unittest.main()
