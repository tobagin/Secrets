"""Unit tests for GitService."""

import os
import subprocess
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest

from src.secrets.services.git_service import GitService, GitStatus, GitCommit
from src.secrets.config import ConfigManager


class TestGitService:
    """Test cases for GitService."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock ConfigManager."""
        config = Mock(spec=ConfigManager)
        config.get_git_config.return_value = {
            'enabled': True,
            'auto_pull': True,
            'auto_push': True
        }
        return config
    
    @pytest.fixture
    def git_service(self, temp_dir, mock_config_manager):
        """Create a GitService instance."""
        return GitService(str(temp_dir), mock_config_manager)
    
    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock subprocess.run for git commands."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            yield mock_run
    
    def test_is_git_available_success(self, git_service, mock_subprocess_run):
        """Test is_git_available when git is installed."""
        mock_subprocess_run.return_value.returncode = 0
        
        assert git_service.is_git_available()
        mock_subprocess_run.assert_called_with(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
    
    def test_is_git_available_not_installed(self, git_service, mock_subprocess_run):
        """Test is_git_available when git is not installed."""
        mock_subprocess_run.side_effect = FileNotFoundError()
        
        assert not git_service.is_git_available()
    
    def test_is_git_available_timeout(self, git_service, mock_subprocess_run):
        """Test is_git_available when command times out."""
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("git", 5)
        
        assert not git_service.is_git_available()
    
    def test_is_git_available_cached(self, git_service, mock_subprocess_run):
        """Test that git availability is cached."""
        mock_subprocess_run.return_value.returncode = 0
        
        # First call
        assert git_service.is_git_available()
        # Second call (should use cache)
        assert git_service.is_git_available()
        
        # Should only be called once
        assert mock_subprocess_run.call_count == 1
    
    def test_is_git_repo_no_git(self, git_service, mock_subprocess_run):
        """Test is_git_repo when git is not available."""
        mock_subprocess_run.side_effect = FileNotFoundError()
        
        assert not git_service.is_git_repo()
    
    def test_is_git_repo_no_git_dir(self, git_service, temp_dir, mock_subprocess_run):
        """Test is_git_repo when .git directory doesn't exist."""
        mock_subprocess_run.return_value.returncode = 0
        
        assert not git_service.is_git_repo()
    
    def test_is_git_repo_exists(self, git_service, temp_dir, mock_subprocess_run):
        """Test is_git_repo when .git directory exists."""
        mock_subprocess_run.return_value.returncode = 0
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        
        assert git_service.is_git_repo()
    
    def test_get_git_status_no_git(self, git_service, mock_subprocess_run):
        """Test get_git_status when git is not available."""
        mock_subprocess_run.side_effect = FileNotFoundError()
        
        status = git_service.get_git_status()
        
        assert not status.is_repo
        assert not status.has_remote
        assert status.current_branch == ""
    
    def test_get_git_status_not_repo(self, git_service, mock_subprocess_run):
        """Test get_git_status when not a git repo."""
        mock_subprocess_run.return_value.returncode = 0
        
        status = git_service.get_git_status()
        
        assert not status.is_repo
    
    @patch('src.secrets.services.git_service.GitService._run_git_command')
    def test_get_git_status_full(self, mock_run_git, git_service, temp_dir, mock_subprocess_run):
        """Test get_git_status with full repository information."""
        # Make it a git repo
        mock_subprocess_run.return_value.returncode = 0
        (temp_dir / ".git").mkdir()
        
        # Mock git command responses
        command_responses = {
            "branch --show-current": (True, "main\n"),
            "remote get-url origin": (True, "https://github.com/user/repo.git\n"),
            "rev-list --count --left-right origin/main...HEAD": (True, "2\t3\n"),
            "status --porcelain=v1": (True, "M  file1.txt\nA  file2.txt\n?? file3.txt\n"),
            "log -1 --pretty=format:%H|%h|%an|%ai|%s": (
                True, 
                "abc123|abc|John Doe|2023-01-01 12:00:00 +0000|Initial commit\n"
            )
        }
        
        def mock_git_command(args):
            key = " ".join(args)
            return command_responses.get(key, (False, ""))
        
        mock_run_git.side_effect = mock_git_command
        
        status = git_service.get_git_status()
        
        assert status.is_repo
        assert status.has_remote
        assert status.remote_url == "https://github.com/user/repo.git"
        assert status.current_branch == "main"
        assert status.ahead == 3
        assert status.behind == 2
        assert status.staged == 1  # A file2.txt
        assert status.unstaged == 1  # M file1.txt
        assert status.untracked == 1  # ?? file3.txt
        assert status.is_dirty
        assert status.last_commit == "Initial commit"
        assert "John Doe" in status.last_commit_date
    
    @patch('src.secrets.services.git_service.GitService._run_git_command')
    def test_init_repo(self, mock_run_git, git_service):
        """Test init_repo method."""
        mock_run_git.return_value = (True, "Initialized empty Git repository")
        
        success, message = git_service.init_repo()
        
        assert success
        assert "Initialized" in message
        mock_run_git.assert_called_with(["init"])
    
    @patch('src.secrets.services.git_service.GitService._run_git_command')
    def test_add_remote(self, mock_run_git, git_service):
        """Test add_remote method."""
        mock_run_git.return_value = (True, "")
        
        success = git_service.add_remote("https://github.com/user/repo.git")
        
        assert success
        mock_run_git.assert_called_with([
            "remote", "add", "origin", "https://github.com/user/repo.git"
        ])
    
    @patch('src.secrets.services.git_service.GitService._run_git_command')
    def test_commit_changes(self, mock_run_git, git_service):
        """Test commit_changes method."""
        # Mock the sequence of git commands
        mock_run_git.side_effect = [
            (True, ""),  # git add -A
            (True, "")   # git commit
        ]
        
        success, message = git_service.commit_changes("Test commit")
        
        assert success
        assert message == "Changes committed successfully"
        
        # Verify both commands were called
        assert mock_run_git.call_count == 2
        calls = mock_run_git.call_args_list
        assert calls[0][0][0] == ["add", "-A"]
        assert calls[1][0][0][:2] == ["commit", "-m"]
    
    @patch('src.secrets.services.git_service.GitService._run_git_command')
    def test_push_changes(self, mock_run_git, git_service):
        """Test push_changes method."""
        mock_run_git.return_value = (True, "Everything up-to-date")
        
        success, message = git_service.push_changes()
        
        assert success
        assert "pushed successfully" in message
        mock_run_git.assert_called_with(["push", "origin", "HEAD"])
    
    @patch('src.secrets.services.git_service.GitService._run_git_command')
    def test_pull_changes(self, mock_run_git, git_service):
        """Test pull_changes method."""
        mock_run_git.return_value = (True, "Already up to date.")
        
        success, message = git_service.pull_changes()
        
        assert success
        assert "pulled successfully" in message
        mock_run_git.assert_called_with(["pull", "origin", "HEAD"])
    
    @patch('src.secrets.services.git_service.GitService._run_git_command')
    def test_get_commit_history(self, mock_run_git, git_service):
        """Test get_commit_history method."""
        mock_run_git.return_value = (
            True,
            "abc123|abc|John Doe|2023-01-01 12:00:00 +0000|Initial commit\n"
            "def456|def|Jane Smith|2023-01-02 14:00:00 +0000|Add feature\n"
        )
        
        commits = git_service.get_commit_history(limit=2)
        
        assert len(commits) == 2
        assert commits[0].hash == "abc123"
        assert commits[0].short_hash == "abc"
        assert commits[0].author == "John Doe"
        assert commits[0].message == "Initial commit"
        assert commits[1].hash == "def456"
        assert commits[1].message == "Add feature"
    
    @patch('subprocess.run')
    @patch('src.secrets.services.git_service.GPGSetupHelper.setup_gpg_environment')
    def test_run_git_command_success(self, mock_gpg_setup, mock_run, git_service):
        """Test _run_git_command with successful execution."""
        mock_gpg_setup.return_value = {"GPG_TTY": "/dev/tty"}
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="success output",
            stderr=""
        )
        
        success, output = git_service._run_git_command(["status"])
        
        assert success
        assert output == "success output"
        
        # Verify command was called with correct args
        args = mock_run.call_args[0][0]
        assert args == ["git", "-C", git_service.store_dir, "status"]
        
        # Verify environment was set
        kwargs = mock_run.call_args[1]
        assert "env" in kwargs
        assert kwargs["env"]["GPG_TTY"] == "/dev/tty"
    
    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_run, git_service):
        """Test _run_git_command with failed execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error: something went wrong"
        )
        
        success, output = git_service._run_git_command(["push"])
        
        assert not success
        assert "error: something went wrong" in output
    
    def test_validate_remote_url_valid(self, git_service):
        """Test validate_remote_url with valid URLs."""
        valid_urls = [
            "https://github.com/user/repo.git",
            "git@github.com:user/repo.git",
            "https://gitlab.com/user/repo",
            "ssh://git@codeberg.org/user/repo.git"
        ]
        
        for url in valid_urls:
            assert git_service.validate_remote_url(url)
    
    def test_validate_remote_url_invalid(self, git_service):
        """Test validate_remote_url with invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com/repo",
            "file:///etc/passwd",
            "../../../etc/passwd"
        ]
        
        for url in invalid_urls:
            assert not git_service.validate_remote_url(url)