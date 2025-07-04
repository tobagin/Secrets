"""Unit tests for GPG utilities."""

import os
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

import pytest

from src.secrets.utils.gpg_utils import GPGSetupHelper


class TestGPGSetupHelper:
    """Test cases for GPGSetupHelper."""
    
    @pytest.fixture
    def gpg_helper(self, temp_dir):
        """Create a GPGSetupHelper instance."""
        return GPGSetupHelper(str(temp_dir))
    
    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock subprocess.run for GPG commands."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            yield mock_run
    
    def test_init_creates_gpg_home(self, temp_dir):
        """Test that GPGSetupHelper creates GPG home directory."""
        gpg_home = str(temp_dir / "gpg_home")
        helper = GPGSetupHelper(gpg_home)
        
        assert helper.gpg_home == gpg_home
        assert os.path.exists(gpg_home)
        assert oct(os.stat(gpg_home).st_mode)[-3:] == "700"  # 0o700 permissions
    
    def test_is_available_success(self, gpg_helper, mock_subprocess_run):
        """Test is_available when GPG is installed."""
        mock_subprocess_run.return_value.returncode = 0
        
        assert gpg_helper.is_available()
        mock_subprocess_run.assert_called_with(
            ["gpg", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
    
    def test_is_available_not_installed(self, gpg_helper, mock_subprocess_run):
        """Test is_available when GPG is not installed."""
        mock_subprocess_run.side_effect = FileNotFoundError()
        
        assert not gpg_helper.is_available()
    
    def test_is_available_timeout(self, gpg_helper, mock_subprocess_run):
        """Test is_available when command times out."""
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("gpg", 5)
        
        assert not gpg_helper.is_available()
    
    def test_is_available_cached(self, gpg_helper, mock_subprocess_run):
        """Test that availability check is cached."""
        mock_subprocess_run.return_value.returncode = 0
        
        # First call
        assert gpg_helper.is_available()
        # Second call (should use cache)
        assert gpg_helper.is_available()
        
        # Should only call subprocess once
        assert mock_subprocess_run.call_count == 1
    
    def test_get_gpg_key_ids_success(self, gpg_helper, mock_subprocess_run):
        """Test get_gpg_key_ids with keys present."""
        mock_subprocess_run.return_value.stdout = '''
sec   rsa4096/ABC123DEF456 2023-01-01 [SC]
uid                 [ultimate] Test User <test@example.com>
ssb   rsa4096/789GHI012JKL 2023-01-01 [E]

sec   rsa4096/MNO456PQR789 2023-01-02 [SC]
uid                 [ultimate] Another User <another@example.com>
ssb   rsa4096/STU123VWX456 2023-01-02 [E]
'''
        
        key_ids = gpg_helper.get_gpg_key_ids()
        
        assert key_ids == ["ABC123DEF456", "MNO456PQR789"]
        mock_subprocess_run.assert_called_with(
            ["gpg", "--homedir", gpg_helper.gpg_home, "--list-secret-keys"],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    def test_get_gpg_key_ids_no_keys(self, gpg_helper, mock_subprocess_run):
        """Test get_gpg_key_ids with no keys."""
        mock_subprocess_run.return_value.stdout = ""
        
        key_ids = gpg_helper.get_gpg_key_ids()
        
        assert key_ids == []
    
    def test_get_gpg_key_ids_error(self, gpg_helper, mock_subprocess_run):
        """Test get_gpg_key_ids with command error."""
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "GPG error"
        
        key_ids = gpg_helper.get_gpg_key_ids()
        
        assert key_ids == []
    
    def test_create_gpg_key_batch_success(self, gpg_helper, mock_subprocess_run):
        """Test successful GPG key creation."""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Key created successfully"
        
        success, message = gpg_helper.create_gpg_key_batch(
            name="Test User",
            email="test@example.com",
            passphrase="testpass123"
        )
        
        assert success
        assert "Key created successfully" in message
        
        # Verify the batch file was created and used
        args = mock_subprocess_run.call_args[0][0]
        assert "gpg" in args
        assert "--batch" in args
        assert "--generate-key" in args
        
        # Check that batch file exists and contains expected content
        batch_file = next(arg for arg in args if arg.startswith(gpg_helper.gpg_home))
        assert os.path.exists(batch_file)
        
        with open(batch_file, 'r') as f:
            content = f.read()
            assert "Name-Real: Test User" in content
            assert "Name-Email: test@example.com" in content
            assert "Passphrase: testpass123" in content
    
    def test_create_gpg_key_batch_failure(self, gpg_helper, mock_subprocess_run):
        """Test GPG key creation failure."""
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "Key creation failed"
        
        success, message = gpg_helper.create_gpg_key_batch(
            name="Test User",
            email="test@example.com",
            passphrase="testpass123"
        )
        
        assert not success
        assert "Key creation failed" in message
    
    def test_create_gpg_key_batch_cleans_up(self, gpg_helper, mock_subprocess_run):
        """Test that batch file is cleaned up after key creation."""
        mock_subprocess_run.return_value.returncode = 0
        
        gpg_helper.create_gpg_key_batch(
            name="Test User",
            email="test@example.com",
            passphrase="testpass123"
        )
        
        # Batch file should be removed
        batch_files = [f for f in os.listdir(gpg_helper.gpg_home) if f.startswith("batch_")]
        assert len(batch_files) == 0
    
    def test_setup_gpg_environment_default(self, gpg_helper):
        """Test setup_gpg_environment with default parameters."""
        env = gpg_helper.setup_gpg_environment()
        
        assert env["GNUPGHOME"] == gpg_helper.gpg_home
        assert "GPG_TTY" in env
        assert env["GPG_AGENT_INFO"] == ""
    
    def test_setup_gpg_environment_custom_tty(self, gpg_helper):
        """Test setup_gpg_environment with custom TTY."""
        env = gpg_helper.setup_gpg_environment(tty="/dev/pts/1")
        
        assert env["GPG_TTY"] == "/dev/pts/1"
    
    def test_setup_gpg_environment_flatpak(self, gpg_helper):
        """Test setup_gpg_environment in Flatpak environment."""
        with patch.dict(os.environ, {"FLATPAK_ID": "org.example.app"}):
            env = gpg_helper.setup_gpg_environment()
            
            assert env["GNUPGHOME"] == gpg_helper.gpg_home
            # Should still set GPG_TTY even in Flatpak
            assert "GPG_TTY" in env
    
    def test_configure_gpg_agent_success(self, gpg_helper, temp_dir):
        """Test successful GPG agent configuration."""
        agent_conf = temp_dir / "gpg-agent.conf"
        
        with patch('src.secrets.utils.gpg_utils.shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/pinentry-gtk3"
            
            success = gpg_helper.configure_gpg_agent()
            
            assert success
            assert agent_conf.exists()
            
            content = agent_conf.read_text()
            assert "pinentry-program /usr/bin/pinentry-gtk3" in content
            assert "no-allow-external-cache" in content
            assert "default-cache-ttl 300" in content
    
    def test_configure_gpg_agent_no_pinentry(self, gpg_helper):
        """Test GPG agent configuration when no pinentry is found."""
        with patch('src.secrets.utils.gpg_utils.shutil.which') as mock_which:
            mock_which.return_value = None
            
            success = gpg_helper.configure_gpg_agent()
            
            assert not success
    
    def test_test_basic_gpg_operation_success(self, gpg_helper, mock_subprocess_run):
        """Test successful basic GPG operation."""
        mock_subprocess_run.return_value.returncode = 0
        
        success, message = gpg_helper.test_basic_gpg_operation()
        
        assert success
        assert "GPG basic operation successful" in message
        
        # Should test both encrypt and decrypt
        calls = mock_subprocess_run.call_args_list
        assert len(calls) == 2
        assert any("--symmetric" in str(call) for call in calls)
        assert any("--decrypt" in str(call) for call in calls)
    
    def test_test_basic_gpg_operation_failure(self, gpg_helper, mock_subprocess_run):
        """Test failed basic GPG operation."""
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "GPG operation failed"
        
        success, message = gpg_helper.test_basic_gpg_operation()
        
        assert not success
        assert "GPG operation failed" in message
    
    def test_generate_batch_content(self, gpg_helper):
        """Test GPG batch file content generation."""
        content = gpg_helper._generate_batch_content(
            name="Test User",
            email="test@example.com",
            passphrase="secret123",
            key_type="RSA",
            key_length=2048,
            expire_date="2y"
        )
        
        expected_lines = [
            "Key-Type: RSA",
            "Key-Length: 2048",
            "Name-Real: Test User",
            "Name-Email: test@example.com",
            "Expire-Date: 2y",
            "Passphrase: secret123"
        ]
        
        for line in expected_lines:
            assert line in content
    
    def test_validate_email_valid(self, gpg_helper):
        """Test email validation with valid emails."""
        valid_emails = [
            "user@example.com",
            "test.user@domain.org",
            "user+tag@example.co.uk",
            "123@456.com"
        ]
        
        for email in valid_emails:
            assert gpg_helper._validate_email(email)
    
    def test_validate_email_invalid(self, gpg_helper):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "",
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "user@domain"
        ]
        
        for email in invalid_emails:
            assert not gpg_helper._validate_email(email)