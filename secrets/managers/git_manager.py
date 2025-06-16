"""
Git manager for high-level Git operations and platform integration.
"""

import os
import json
import requests
from typing import Tuple, Dict, List, Optional, Any
from urllib.parse import urlparse

from ..services.git_service import GitService, GitStatus
from ..config import ConfigManager
from .toast_manager import ToastManager


class GitPlatformManager:
    """Manager for Git platform integrations (GitHub, GitLab, etc.)."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def get_platform_info(self, url: str) -> Dict[str, str]:
        """Extract platform information from a Git URL."""
        parsed = urlparse(url)
        
        if 'github.com' in parsed.netloc:
            return {
                'type': 'github',
                'api_base': 'https://api.github.com',
                'name': 'GitHub'
            }
        elif 'gitlab.com' in parsed.netloc:
            return {
                'type': 'gitlab',
                'api_base': 'https://gitlab.com/api/v4',
                'name': 'GitLab'
            }
        elif 'codeberg.org' in parsed.netloc:
            return {
                'type': 'gitea',
                'api_base': 'https://codeberg.org/api/v1',
                'name': 'Codeberg'
            }
        else:
            return {
                'type': 'custom',
                'api_base': '',
                'name': 'Custom Git Server'
            }
    
    def validate_repository_url(self, url: str) -> Tuple[bool, str]:
        """Validate a Git repository URL."""
        if not url:
            return False, "URL cannot be empty"
        
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"
        
        # Check if it's a Git URL
        if not (url.endswith('.git') or 
                'github.com' in url or 
                'gitlab.com' in url or 
                'codeberg.org' in url or
                parsed.scheme in ['git', 'ssh']):
            return False, "URL does not appear to be a Git repository"
        
        return True, "Valid Git repository URL"
    
    def get_repository_info(self, url: str, token: str = None) -> Dict[str, Any]:
        """Get repository information from the platform API."""
        platform = self.get_platform_info(url)
        
        if platform['type'] == 'custom':
            return {'name': 'Custom Repository', 'description': ''}
        
        try:
            # Extract owner/repo from URL
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return {'error': 'Invalid repository path'}
            
            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')
            
            # Make API request
            if platform['type'] == 'github':
                api_url = f"{platform['api_base']}/repos/{owner}/{repo}"
            elif platform['type'] == 'gitlab':
                api_url = f"{platform['api_base']}/projects/{owner}%2F{repo}"
            else:
                return {'name': repo, 'description': ''}
            
            headers = {}
            if token:
                if platform['type'] == 'github':
                    headers['Authorization'] = f'token {token}'
                elif platform['type'] == 'gitlab':
                    headers['Private-Token'] = token
            
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('name', repo),
                    'description': data.get('description', ''),
                    'private': data.get('private', False),
                    'clone_url': data.get('clone_url', url),
                    'ssh_url': data.get('ssh_url', ''),
                    'default_branch': data.get('default_branch', 'main')
                }
            else:
                return {'error': f'API request failed: {response.status_code}'}
        
        except Exception as e:
            return {'error': f'Failed to get repository info: {e}'}


class GitManager:
    """High-level Git manager for the Secrets application."""

    def __init__(self, store_dir: str, config_manager: ConfigManager, toast_manager: ToastManager):
        self.store_dir = store_dir
        self.config_manager = config_manager
        self.toast_manager = toast_manager
        self.git_service = GitService(store_dir, config_manager)
        self.platform_manager = GitPlatformManager(config_manager)
        self._status_cache = None
        self._status_cache_time = 0
    
    def get_status(self, use_cache: bool = True) -> GitStatus:
        """Get Git status with optional caching."""
        import time
        
        current_time = time.time()
        if use_cache and self._status_cache and (current_time - self._status_cache_time) < 30:
            return self._status_cache
        
        self._status_cache = self.git_service.get_git_status()
        self._status_cache_time = current_time
        return self._status_cache
    
    def invalidate_status_cache(self):
        """Invalidate the status cache."""
        self._status_cache = None
        self._status_cache_time = 0
    
    def setup_repository(self, remote_url: str = None, init_if_needed: bool = True) -> Tuple[bool, str]:
        """Set up Git repository with optional remote."""
        # Initialize repository if needed
        if init_if_needed and not self.git_service.is_git_repo():
            success, message = self.git_service.init_repository()
            if not success:
                return False, message
        
        # Add remote if provided
        if remote_url:
            # Validate URL
            valid, validation_message = self.platform_manager.validate_repository_url(remote_url)
            if not valid:
                return False, validation_message
            
            # Add remote
            success, message = self.git_service.add_remote(remote_url)
            if not success:
                return False, message
            
            # Update configuration
            config = self.config_manager.get_config()
            config.git.remote_url = remote_url
            
            # Set platform information
            platform_info = self.platform_manager.get_platform_info(remote_url)
            config.git.platform_type = platform_info['type']
            
            self.config_manager.save_config(config)
        
        self.invalidate_status_cache()
        return True, "Repository setup completed successfully"
    
    def sync_with_remote(self, operation: str) -> Tuple[bool, str]:
        """Perform sync operations with remote repository."""
        status = self.get_status(use_cache=False)
        
        if not status.is_repo:
            return False, "Not a Git repository"
        
        if not status.has_remote:
            return False, "No remote repository configured"
        
        config = self.config_manager.get_config()
        
        try:
            if operation == "pull":
                # Auto-commit changes before pull if configured
                if config.git.auto_commit_on_changes and status.is_dirty:
                    commit_success, commit_message = self.git_service.commit_changes()
                    if not commit_success:
                        return False, f"Failed to commit changes before pull: {commit_message}"
                
                # Perform pull
                from ..password_store import PasswordStore
                store = PasswordStore(self.store_dir)
                result = store.git_pull()
                
            elif operation == "push":
                # Auto-commit changes before push if configured
                if config.git.auto_commit_on_changes and status.is_dirty:
                    commit_success, commit_message = self.git_service.commit_changes()
                    if not commit_success:
                        return False, f"Failed to commit changes before push: {commit_message}"
                
                # Perform push
                from ..password_store import PasswordStore
                store = PasswordStore(self.store_dir)
                result = store.git_push()
                
            else:
                return False, f"Unknown operation: {operation}"
            
            self.invalidate_status_cache()
            
            # Show notification if configured
            if config.git.show_git_notifications and result[0]:
                self.toast_manager.show_success(f"Git {operation} completed successfully")
            
            return result
            
        except Exception as e:
            return False, f"Error during {operation}: {e}"
    
    def get_repository_summary(self) -> Dict[str, Any]:
        """Get a summary of the repository state."""
        status = self.get_status()
        config = self.config_manager.get_config()
        
        summary = {
            'is_repo': status.is_repo,
            'has_remote': status.has_remote,
            'remote_url': status.remote_url or config.git.remote_url,
            'platform_type': config.git.platform_type,
            'current_branch': status.current_branch,
            'is_dirty': status.is_dirty,
            'ahead': status.ahead,
            'behind': status.behind,
            'last_commit': status.last_commit,
            'last_commit_date': status.last_commit_date
        }
        
        return summary
    
    def auto_pull_on_startup(self) -> bool:
        """Perform auto-pull on startup if configured."""
        config = self.config_manager.get_config()
        
        if not config.git.auto_pull_on_startup:
            return True
        
        status = self.get_status()
        if not status.is_repo or not status.has_remote:
            return True
        
        if config.git.check_remote_on_startup:
            success, message = self.sync_with_remote("pull")
            if not success:
                self.toast_manager.show_warning(f"Auto-pull failed: {message}")
                return False
        
        return True
    
    def auto_push_on_changes(self) -> bool:
        """Perform auto-push on changes if configured."""
        config = self.config_manager.get_config()
        
        if not config.git.auto_push_on_changes:
            return True
        
        status = self.get_status()
        if not status.is_repo or not status.has_remote or not status.is_dirty:
            return True
        
        success, message = self.sync_with_remote("push")
        if not success:
            self.toast_manager.show_warning(f"Auto-push failed: {message}")
            return False
        
        return True
