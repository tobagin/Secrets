"""
Git service for advanced Git operations and repository management.
"""

import os
import subprocess
import re
from typing import Tuple, Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from ..config import ConfigManager
from ..utils.gpg_utils import GPGSetupHelper
from ..logging_system import get_logger, LogCategory


@dataclass
class GitStatus:
    """Git repository status information."""
    is_repo: bool = False
    has_remote: bool = False
    remote_url: str = ""
    current_branch: str = ""
    ahead: int = 0
    behind: int = 0
    staged: int = 0
    unstaged: int = 0
    untracked: int = 0
    is_dirty: bool = False
    last_commit: str = ""
    last_commit_date: str = ""


@dataclass
class GitCommit:
    """Git commit information."""
    hash: str
    short_hash: str
    author: str
    date: str
    message: str


class GitService:
    """Service for Git operations and repository management."""
    
    def __init__(self, store_dir: str, config_manager: ConfigManager):
        self.store_dir = store_dir
        self.config_manager = config_manager
        self._git_available = None
        self.logger = get_logger(LogCategory.GIT, "GitService")
    
    def is_git_available(self) -> bool:
        """Check if Git is available on the system."""
        if self._git_available is None:
            try:
                result = subprocess.run(
                    ["git", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                self._git_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._git_available = False
        return self._git_available
    
    def is_git_repo(self) -> bool:
        """Check if the store directory is a Git repository."""
        if not self.is_git_available():
            return False
        
        git_dir = os.path.join(self.store_dir, '.git')
        return os.path.exists(git_dir)
    
    def get_git_status(self) -> GitStatus:
        """Get comprehensive Git repository status."""
        status = GitStatus()
        
        if not self.is_git_available():
            return status
        
        status.is_repo = self.is_git_repo()
        if not status.is_repo:
            return status
        
        try:
            # Get current branch
            result = self._run_git_command(["branch", "--show-current"])
            if result[0]:
                status.current_branch = result[1].strip()
            
            # Get remote information
            result = self._run_git_command(["remote", "get-url", "origin"])
            if result[0]:
                status.has_remote = True
                status.remote_url = result[1].strip()
            
            # Get ahead/behind status
            if status.has_remote and status.current_branch:
                result = self._run_git_command([
                    "rev-list", "--count", "--left-right",
                    f"origin/{status.current_branch}...HEAD"
                ])
                if result[0]:
                    parts = result[1].strip().split('\t')
                    if len(parts) == 2:
                        status.behind = int(parts[0])
                        status.ahead = int(parts[1])
            
            # Get working directory status
            result = self._run_git_command(["status", "--porcelain"])
            if result[0]:
                lines = result[1].strip().split('\n') if result[1].strip() else []
                for line in lines:
                    if line.startswith('??'):
                        status.untracked += 1
                    elif line[0] in 'MADRC':
                        status.staged += 1
                    elif line[1] in 'MADRC':
                        status.unstaged += 1
                
                status.is_dirty = len(lines) > 0
            
            # Get last commit info
            result = self._run_git_command([
                "log", "-1", "--pretty=format:%H|%h|%an|%ad|%s", 
                "--date=short"
            ])
            if result[0] and result[1].strip():
                parts = result[1].strip().split('|', 4)
                if len(parts) == 5:
                    status.last_commit = parts[4]
                    status.last_commit_date = parts[3]
        
        except Exception as e:
            self.logger.error("Failed to get Git repository status", extra={
                'store_dir': self.store_dir,
                'git_available': self.is_git_available(),
                'error': str(e),
                'operation': 'get_git_status'
            }, exc_info=True)
        
        return status
    
    def init_repository(self) -> Tuple[bool, str]:
        """Initialize a Git repository in the store directory."""
        if not self.is_git_available():
            return False, "Git is not available on this system"
        
        if self.is_git_repo():
            return True, "Repository already initialized"
        
        try:
            result = self._run_git_command(["init"])
            if result[0]:
                # Set up initial configuration
                self._run_git_command(["config", "user.name", "Secrets App"])
                self._run_git_command(["config", "user.email", "secrets@local"])
                return True, "Git repository initialized successfully"
            else:
                return False, f"Failed to initialize repository: {result[1]}"
        except Exception as e:
            return False, f"Error initializing repository: {e}"
    
    def add_remote(self, remote_url: str, remote_name: str = "origin") -> Tuple[bool, str]:
        """Add a remote repository."""
        if not self.is_git_repo():
            return False, "Not a Git repository"
        
        try:
            # Remove existing remote if it exists
            self._run_git_command(["remote", "remove", remote_name])
            
            # Add new remote
            result = self._run_git_command(["remote", "add", remote_name, remote_url])
            if result[0]:
                return True, f"Remote '{remote_name}' added successfully"
            else:
                return False, f"Failed to add remote: {result[1]}"
        except Exception as e:
            return False, f"Error adding remote: {e}"
    
    def get_commit_history(self, limit: int = 20) -> List[GitCommit]:
        """Get commit history."""
        commits = []
        
        if not self.is_git_repo():
            return commits
        
        try:
            result = self._run_git_command([
                "log", f"-{limit}", "--pretty=format:%H|%h|%an|%ad|%s", 
                "--date=short"
            ])
            
            if result[0] and result[1].strip():
                for line in result[1].strip().split('\n'):
                    parts = line.split('|', 4)
                    if len(parts) == 5:
                        commits.append(GitCommit(
                            hash=parts[0],
                            short_hash=parts[1],
                            author=parts[2],
                            date=parts[3],
                            message=parts[4]
                        ))
        except Exception as e:
            self.logger.error("Failed to get Git commit history", extra={
                'store_dir': self.store_dir,
                'limit': limit,
                'error': str(e),
                'operation': 'get_commit_history'
            }, exc_info=True)
        
        return commits
    
    def commit_changes(self, message: str = None) -> Tuple[bool, str]:
        """Commit all changes in the repository."""
        if not self.is_git_repo():
            return False, "Not a Git repository"
        
        if not message:
            config = self.config_manager.get_config()
            message = config.git.commit_message_template
        
        try:
            # Add all changes
            result = self._run_git_command(["add", "."])
            if not result[0]:
                return False, f"Failed to stage changes: {result[1]}"
            
            # Check if there are changes to commit
            result = self._run_git_command(["diff", "--cached", "--quiet"])
            if result[0]:  # No changes staged
                return True, "No changes to commit"
            
            # Commit changes
            result = self._run_git_command(["commit", "-m", message])
            if result[0]:
                return True, "Changes committed successfully"
            else:
                return False, f"Failed to commit: {result[1]}"
        except Exception as e:
            return False, f"Error committing changes: {e}"
    
    def _run_git_command(self, args: List[str]) -> Tuple[bool, str]:
        """Run a Git command in the store directory."""
        try:
            command = ["git"] + args
            env = GPGSetupHelper.setup_gpg_environment()
            
            result = subprocess.run(
                command,
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr or result.stdout
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except Exception as e:
            return False, f"Error running Git command: {e}"
