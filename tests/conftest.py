"""Pytest configuration and shared fixtures for Secrets tests."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from gi.repository import GLib


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_password_store(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a mock password store directory structure."""
    store_dir = temp_dir / ".password-store"
    store_dir.mkdir()
    
    # Create some test password files
    (store_dir / "test.gpg").touch()
    (store_dir / "folder").mkdir()
    (store_dir / "folder" / "nested.gpg").touch()
    (store_dir / ".git").mkdir()
    (store_dir / ".gpg-id").write_text("test@example.com")
    
    yield store_dir


@pytest.fixture
def mock_config_dir(temp_dir: Path, monkeypatch) -> Generator[Path, None, None]:
    """Create a mock config directory and patch GLib.get_user_config_dir."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    
    monkeypatch.setattr(GLib, "get_user_config_dir", lambda: str(config_dir))
    
    yield config_dir


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for testing command execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_gpg_environment():
    """Mock GPG environment setup."""
    with patch("src.secrets.utils.gpg_setup_helper.GPGSetupHelper.setup_gpg_environment") as mock_setup:
        mock_setup.return_value = os.environ.copy()
        yield mock_setup


@pytest.fixture
def sample_password_data():
    """Provide sample password data for testing."""
    return {
        "simple": "password123",
        "with_metadata": "password123\nusername: user@example.com\nurl: https://example.com",
        "with_totp": "password123\notpauth://totp/Example:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example",
        "multiline": "password123\nline2\nline3\nkey: value",
    }


@pytest.fixture
def mock_gtk_clipboard():
    """Mock GTK clipboard operations."""
    clipboard = Mock()
    clipboard.set_text = Mock()
    clipboard.get_text = Mock(return_value="")
    
    with patch("gi.repository.Gtk.Clipboard") as mock_clipboard_class:
        mock_clipboard_class.get_for_display.return_value = clipboard
        yield clipboard


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Import the classes that use singleton pattern
    from src.secrets.managers.config_manager import ConfigManager
    from src.secrets.services.password_service import PasswordService
    
    # Reset their instances
    ConfigManager._instance = None
    PasswordService._instance = None
    
    yield
    
    # Clean up after test
    ConfigManager._instance = None
    PasswordService._instance = None