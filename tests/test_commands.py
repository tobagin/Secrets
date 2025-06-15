"""
Tests for the commands module.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import secrets
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secrets.commands import (
    CommandInvoker, CopyPasswordCommand, CopyUsernameCommand, 
    DeletePasswordCommand, OpenUrlCommand, GitSyncCommand
)
from secrets.models import PasswordEntry, AppState


class TestCommandInvoker(unittest.TestCase):
    """Test cases for CommandInvoker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.invoker = CommandInvoker()
        self.mock_command = Mock()
        self.mock_command.can_execute.return_value = True
        self.mock_command.execute.return_value = True
        self.mock_command.description = "Test command"
    
    def test_register_command(self):
        """Test registering a command."""
        self.invoker.register_command("test", self.mock_command)
        
        self.assertTrue(self.invoker.can_execute_command("test"))
        self.assertEqual(self.invoker.get_command_description("test"), "Test command")
    
    def test_execute_command_success(self):
        """Test executing a command successfully."""
        self.invoker.register_command("test", self.mock_command)
        
        result = self.invoker.execute_command("test")
        
        self.assertTrue(result)
        self.mock_command.can_execute.assert_called_once()
        self.mock_command.execute.assert_called_once()
    
    def test_execute_command_cannot_execute(self):
        """Test executing a command that cannot be executed."""
        self.mock_command.can_execute.return_value = False
        self.invoker.register_command("test", self.mock_command)
        
        result = self.invoker.execute_command("test")
        
        self.assertFalse(result)
        self.mock_command.can_execute.assert_called_once()
        self.mock_command.execute.assert_not_called()
    
    def test_execute_nonexistent_command(self):
        """Test executing a command that doesn't exist."""
        result = self.invoker.execute_command("nonexistent")
        
        self.assertFalse(result)
    
    def test_can_execute_command(self):
        """Test checking if a command can be executed."""
        self.invoker.register_command("test", self.mock_command)
        
        # Command exists and can execute
        self.assertTrue(self.invoker.can_execute_command("test"))
        
        # Command exists but cannot execute
        self.mock_command.can_execute.return_value = False
        self.assertFalse(self.invoker.can_execute_command("test"))
        
        # Command doesn't exist
        self.assertFalse(self.invoker.can_execute_command("nonexistent"))


class TestCopyPasswordCommand(unittest.TestCase):
    """Test cases for CopyPasswordCommand."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_password_service = Mock()
        self.mock_toast_manager = Mock()
        self.mock_clipboard_manager = Mock()
        self.app_state = AppState()
        
        self.command = CopyPasswordCommand(
            self.mock_password_service,
            self.mock_toast_manager,
            self.app_state,
            self.mock_clipboard_manager
        )
    
    def test_can_execute_with_password(self):
        """Test can_execute when entry has password."""
        entry = PasswordEntry(path="test", password="secret", is_folder=False)
        self.app_state.set_selected_entry(entry)
        
        self.assertTrue(self.command.can_execute())
    
    def test_can_execute_no_entry(self):
        """Test can_execute when no entry is selected."""
        self.assertFalse(self.command.can_execute())
    
    def test_can_execute_folder(self):
        """Test can_execute when entry is a folder."""
        entry = PasswordEntry(path="test", is_folder=True)
        self.app_state.set_selected_entry(entry)
        
        self.assertFalse(self.command.can_execute())
    
    def test_can_execute_no_password(self):
        """Test can_execute when entry has no password."""
        entry = PasswordEntry(path="test", password=None, is_folder=False)
        self.app_state.set_selected_entry(entry)

        # Should be able to execute because we have fallback to pass command
        self.assertTrue(self.command.can_execute())
    
    def test_execute_with_password(self):
        """Test executing command with password."""
        entry = PasswordEntry(path="test", password="secret", is_folder=False)
        self.app_state.set_selected_entry(entry)
        self.mock_clipboard_manager.copy_password.return_value = True
        
        result = self.command.execute()
        
        self.assertTrue(result)
        self.mock_clipboard_manager.copy_password.assert_called_once_with("secret")
    
    def test_execute_fallback_to_pass(self):
        """Test executing command with fallback to pass -c."""
        entry = PasswordEntry(path="test", password=None, is_folder=False)
        self.app_state.set_selected_entry(entry)
        self.mock_password_service.copy_password_to_clipboard.return_value = (True, "Copied")
        
        result = self.command.execute()
        
        self.assertTrue(result)
        self.mock_password_service.copy_password_to_clipboard.assert_called_once_with("test")
        self.mock_toast_manager.show_success.assert_called_once_with("Copied")


class TestCopyUsernameCommand(unittest.TestCase):
    """Test cases for CopyUsernameCommand."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_password_service = Mock()
        self.mock_toast_manager = Mock()
        self.mock_clipboard_manager = Mock()
        self.app_state = AppState()
        
        self.command = CopyUsernameCommand(
            self.mock_password_service,
            self.mock_toast_manager,
            self.app_state,
            self.mock_clipboard_manager
        )
    
    def test_can_execute_with_username(self):
        """Test can_execute when entry has username."""
        entry = PasswordEntry(path="test", username="user@example.com", is_folder=False)
        self.app_state.set_selected_entry(entry)
        
        self.assertTrue(self.command.can_execute())
    
    def test_can_execute_no_username(self):
        """Test can_execute when entry has no username."""
        entry = PasswordEntry(path="test", username=None, is_folder=False)
        self.app_state.set_selected_entry(entry)
        
        self.assertFalse(self.command.can_execute())
    
    def test_can_execute_empty_username(self):
        """Test can_execute when entry has empty username."""
        entry = PasswordEntry(path="test", username="", is_folder=False)
        self.app_state.set_selected_entry(entry)
        
        self.assertFalse(self.command.can_execute())
    
    def test_execute_success(self):
        """Test executing command successfully."""
        entry = PasswordEntry(path="test", username="user@example.com", is_folder=False)
        self.app_state.set_selected_entry(entry)
        self.mock_clipboard_manager.copy_username.return_value = True
        
        result = self.command.execute()
        
        self.assertTrue(result)
        self.mock_clipboard_manager.copy_username.assert_called_once_with("user@example.com")


class TestOpenUrlCommand(unittest.TestCase):
    """Test cases for OpenUrlCommand."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_password_service = Mock()
        self.mock_toast_manager = Mock()
        self.app_state = AppState()
        
        self.command = OpenUrlCommand(
            self.mock_password_service,
            self.mock_toast_manager,
            self.app_state
        )
    
    def test_can_execute_with_valid_url(self):
        """Test can_execute with valid URL."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "www.example.com"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                entry = PasswordEntry(path="test", url=url, is_folder=False)
                self.app_state.set_selected_entry(entry)
                
                self.assertTrue(self.command.can_execute())
    
    def test_can_execute_with_invalid_url(self):
        """Test can_execute with invalid URL."""
        invalid_urls = [
            None,
            "",
            "Not set",
            "N/A for folders",
            "invalid-url"
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                entry = PasswordEntry(path="test", url=url, is_folder=False)
                self.app_state.set_selected_entry(entry)
                
                self.assertFalse(self.command.can_execute())
    
    @patch('secrets.commands.Gtk.show_uri')
    def test_execute_success(self, mock_show_uri):
        """Test executing command successfully."""
        entry = PasswordEntry(path="test", url="https://example.com", is_folder=False)
        self.app_state.set_selected_entry(entry)
        
        result = self.command.execute()
        
        self.assertTrue(result)
        mock_show_uri.assert_called_once_with(None, "https://example.com", 0)
        self.mock_toast_manager.show_success.assert_called_once()
    
    @patch('secrets.commands.Gtk.show_uri')
    def test_execute_www_url(self, mock_show_uri):
        """Test executing command with www URL."""
        entry = PasswordEntry(path="test", url="www.example.com", is_folder=False)
        self.app_state.set_selected_entry(entry)
        
        result = self.command.execute()
        
        self.assertTrue(result)
        mock_show_uri.assert_called_once_with(None, "http://www.example.com", 0)


class TestGitSyncCommand(unittest.TestCase):
    """Test cases for GitSyncCommand."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_password_service = Mock()
        self.mock_toast_manager = Mock()
        self.app_state = AppState()
        self.mock_callback = Mock()
        
        self.pull_command = GitSyncCommand(
            self.mock_password_service,
            self.mock_toast_manager,
            self.app_state,
            "pull",
            self.mock_callback
        )
        
        self.push_command = GitSyncCommand(
            self.mock_password_service,
            self.mock_toast_manager,
            self.app_state,
            "push"
        )
    
    def test_can_execute_initialized(self):
        """Test can_execute when store is initialized."""
        self.mock_password_service.is_initialized.return_value = True
        
        self.assertTrue(self.pull_command.can_execute())
        self.assertTrue(self.push_command.can_execute())
    
    def test_can_execute_not_initialized(self):
        """Test can_execute when store is not initialized."""
        self.mock_password_service.is_initialized.return_value = False
        
        self.assertFalse(self.pull_command.can_execute())
        self.assertFalse(self.push_command.can_execute())
    
    def test_execute_pull_success(self):
        """Test executing pull command successfully."""
        self.mock_password_service.is_initialized.return_value = True
        self.mock_password_service.sync_pull.return_value = (True, "Success")
        
        result = self.pull_command.execute()
        
        self.assertTrue(result)
        self.mock_password_service.sync_pull.assert_called_once()
        self.mock_toast_manager.show_success.assert_called_once()
        self.mock_callback.assert_called_once()
    
    def test_execute_push_success(self):
        """Test executing push command successfully."""
        self.mock_password_service.is_initialized.return_value = True
        self.mock_password_service.sync_push.return_value = (True, "Success")
        
        result = self.push_command.execute()
        
        self.assertTrue(result)
        self.mock_password_service.sync_push.assert_called_once()
        self.mock_toast_manager.show_success.assert_called_once()
    
    def test_execute_failure(self):
        """Test executing command with failure."""
        self.mock_password_service.is_initialized.return_value = True
        self.mock_password_service.sync_pull.return_value = (False, "Error")
        
        result = self.pull_command.execute()
        
        self.assertFalse(result)
        self.mock_toast_manager.show_error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
