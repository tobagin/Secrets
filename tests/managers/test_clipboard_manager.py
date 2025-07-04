"""Unit tests for ClipboardManager."""

from unittest.mock import Mock, MagicMock, call, patch

import pytest
from gi.repository import GLib

from src.secrets.managers.clipboard_manager import ClipboardManager
from src.secrets.managers.toast_manager import ToastManager


class TestClipboardManager:
    """Test cases for ClipboardManager."""
    
    @pytest.fixture
    def mock_display(self):
        """Create a mock Gdk.Display."""
        display = Mock()
        display.get_clipboard.return_value = Mock()
        return display
    
    @pytest.fixture
    def mock_toast_manager(self):
        """Create a mock ToastManager."""
        return Mock(spec=ToastManager)
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock ConfigManager."""
        config_manager = Mock()
        config = Mock()
        config.security.clear_clipboard_timeout = 45
        config_manager.get_config.return_value = config
        return config_manager
    
    @pytest.fixture
    def clipboard_manager(self, mock_display, mock_toast_manager, mock_config_manager):
        """Create a ClipboardManager instance."""
        return ClipboardManager(mock_display, mock_toast_manager, mock_config_manager)
    
    def test_copy_text_empty(self, clipboard_manager, mock_toast_manager):
        """Test copy_text with empty text."""
        result = clipboard_manager.copy_text("", "Test")
        
        assert not result
        mock_toast_manager.show_warning.assert_called_with("No test to copy")
        clipboard_manager.clipboard.set.assert_not_called()
    
    def test_copy_text_success(self, clipboard_manager, mock_toast_manager):
        """Test successful text copy without auto-clear."""
        result = clipboard_manager.copy_text("test text", "Test")
        
        assert result
        clipboard_manager.clipboard.set.assert_called_with("test text")
        mock_toast_manager.show_success.assert_called_with("Test copied to clipboard")
    
    def test_copy_text_failure(self, clipboard_manager, mock_toast_manager):
        """Test copy_text with clipboard error."""
        clipboard_manager.clipboard.set.side_effect = Exception("Clipboard error")
        
        result = clipboard_manager.copy_text("test text", "Test")
        
        assert not result
        mock_toast_manager.show_error.assert_called()
        assert "Failed to copy test" in mock_toast_manager.show_error.call_args[0][0]
    
    @patch('gi.repository.GLib.timeout_add_seconds')
    def test_copy_text_with_auto_clear(self, mock_timeout, clipboard_manager, mock_toast_manager):
        """Test copy_text with auto-clear enabled."""
        mock_timeout.return_value = 123
        
        result = clipboard_manager.copy_text("secret", "Password", auto_clear=True)
        
        assert result
        clipboard_manager.clipboard.set.assert_called_with("secret")
        mock_toast_manager.show_success.assert_called()
        
        # Check that timer was set
        mock_timeout.assert_called_once()
        assert mock_timeout.call_args[0][0] == 45  # Default timeout
        assert mock_timeout.call_args[0][2] == "secret"  # Original text
    
    def test_copy_password(self, clipboard_manager):
        """Test copy_password method."""
        with patch.object(clipboard_manager, 'copy_text') as mock_copy:
            mock_copy.return_value = True
            
            result = clipboard_manager.copy_password("mypassword")
            
            assert result
            mock_copy.assert_called_with("mypassword", "Password", auto_clear=True)
    
    def test_copy_username(self, clipboard_manager):
        """Test copy_username method."""
        with patch.object(clipboard_manager, 'copy_text') as mock_copy:
            mock_copy.return_value = True
            
            result = clipboard_manager.copy_username("user@example.com")
            
            assert result
            mock_copy.assert_called_with("user@example.com", "Username")
    
    @patch('gi.repository.GLib.timeout_add_seconds')
    @patch('gi.repository.GLib.source_remove')
    def test_setup_auto_clear_cancel_existing(self, mock_remove, mock_timeout, clipboard_manager):
        """Test that existing timer is cancelled when setting up new one."""
        clipboard_manager._clear_timeout_id = 999
        mock_timeout.return_value = 123
        
        clipboard_manager._setup_auto_clear("new text")
        
        # Should cancel existing timer
        mock_remove.assert_called_with(999)
        # Should set new timer
        mock_timeout.assert_called_once()
        assert clipboard_manager._clear_timeout_id == 123
    
    @patch('gi.repository.GLib.timeout_add_seconds')
    def test_setup_auto_clear_custom_timeout(self, mock_timeout, clipboard_manager):
        """Test auto-clear with custom timeout from config."""
        clipboard_manager.config_manager.get_config().security.clear_clipboard_timeout = 30
        
        clipboard_manager._setup_auto_clear("text")
        
        assert mock_timeout.call_args[0][0] == 30
    
    def test_auto_clear_callback_matching_text(self, clipboard_manager, mock_toast_manager):
        """Test auto-clear callback when clipboard still contains original text."""
        # Mock async read operation
        result_mock = Mock()
        clipboard_manager.clipboard.read_text_async = Mock()
        
        # Simulate callback execution
        clipboard_manager._auto_clear_callback("original text")
        
        # Get the callback function that was passed to read_text_async
        read_callback = clipboard_manager.clipboard.read_text_async.call_args[0][1]
        
        # Mock clipboard containing the same text
        clipboard_manager.clipboard.read_text_finish = Mock(return_value="original text")
        
        # Execute the callback
        read_callback(clipboard_manager.clipboard, result_mock)
        
        # Should clear clipboard
        clipboard_manager.clipboard.set.assert_called_with("")
        mock_toast_manager.show_info.assert_called_with("Clipboard automatically cleared")
    
    def test_auto_clear_callback_different_text(self, clipboard_manager, mock_toast_manager):
        """Test auto-clear callback when clipboard contains different text."""
        # Mock async read operation
        result_mock = Mock()
        clipboard_manager.clipboard.read_text_async = Mock()
        
        # Simulate callback execution
        clipboard_manager._auto_clear_callback("original text")
        
        # Get the callback function
        read_callback = clipboard_manager.clipboard.read_text_async.call_args[0][1]
        
        # Mock clipboard containing different text
        clipboard_manager.clipboard.read_text_finish = Mock(return_value="different text")
        
        # Execute the callback
        read_callback(clipboard_manager.clipboard, result_mock)
        
        # Should NOT clear clipboard
        clipboard_manager.clipboard.set.assert_not_called()
        mock_toast_manager.show_info.assert_not_called()
    
    def test_auto_clear_callback_read_error(self, clipboard_manager, mock_toast_manager):
        """Test auto-clear callback when reading clipboard fails."""
        # Mock async read operation
        result_mock = Mock()
        clipboard_manager.clipboard.read_text_async = Mock()
        
        # Simulate callback execution
        clipboard_manager._auto_clear_callback("original text")
        
        # Get the callback function
        read_callback = clipboard_manager.clipboard.read_text_async.call_args[0][1]
        
        # Mock read failure
        clipboard_manager.clipboard.read_text_finish = Mock(side_effect=Exception("Read error"))
        
        # Execute the callback
        read_callback(clipboard_manager.clipboard, result_mock)
        
        # Should still clear clipboard for safety
        clipboard_manager.clipboard.set.assert_called_with("")
        mock_toast_manager.show_info.assert_called_with("Clipboard automatically cleared")
    
    def test_cleanup(self, clipboard_manager):
        """Test cleanup method cancels timer."""
        with patch('gi.repository.GLib.source_remove') as mock_remove:
            clipboard_manager._clear_timeout_id = 456
            
            clipboard_manager.cleanup()
            
            mock_remove.assert_called_with(456)
            assert clipboard_manager._clear_timeout_id is None