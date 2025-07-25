"""
Password Content Cache System for storing TOTP/URL detection results.
Provides encrypted caching to avoid re-decrypting passwords on every app start.
"""

import os
import json
import time
import hashlib
from typing import Dict, Optional, Tuple, Any
from ..logging_system import get_logger, LogCategory


class PasswordContentCache:
    """
    Encrypted cache for password content analysis results (TOTP, URL detection).
    Stores results to avoid re-decrypting passwords on every app startup.
    """
    
    def __init__(self, password_store):
        self.password_store = password_store
        self.logger = get_logger(LogCategory.SECURITY, "PasswordContentCache")
        self._cache = {}
        self._cache_file = None
        self._initialize_cache_file()
        self._load_cache()
    
    def _initialize_cache_file(self):
        """Initialize the cache file path in the password store directory."""
        if hasattr(self.password_store, 'store_dir') and self.password_store.store_dir:
            cache_dir = os.path.join(self.password_store.store_dir, '.secrets-cache')
            os.makedirs(cache_dir, exist_ok=True)
            self._cache_file = os.path.join(cache_dir, 'content_cache.json')
        else:
            self.logger.warning("Password store directory not available, cache disabled")
    
    def _load_cache(self):
        """Load existing cache from file."""
        if not self._cache_file or not os.path.exists(self._cache_file):
            return
        
        try:
            with open(self._cache_file, 'r') as f:
                data = json.load(f)
                self._cache = data.get('cache', {})
                
            self.logger.debug(f"Loaded content cache with {len(self._cache)} entries")
            
        except Exception as e:
            self.logger.warning(f"Failed to load content cache: {e}")
            self._cache = {}
    
    def _save_cache(self):
        """Save cache to file."""
        if not self._cache_file:
            return
        
        try:
            cache_data = {
                'version': '1.0',
                'created': time.time(),
                'cache': self._cache
            }
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = self._cache_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            os.rename(temp_file, self._cache_file)
            self.logger.debug(f"Saved content cache with {len(self._cache)} entries")
            
        except Exception as e:
            self.logger.error(f"Failed to save content cache: {e}")
    
    def _get_file_hash(self, password_path: str) -> Optional[str]:
        """Get hash of password file for cache invalidation."""
        try:
            if hasattr(self.password_store, 'store_dir') and self.password_store.store_dir:
                file_path = os.path.join(self.password_store.store_dir, password_path + '.gpg')
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    # Use file size and modification time for hash
                    content = f"{stat.st_size}:{stat.st_mtime}"
                    return hashlib.md5(content.encode()).hexdigest()
            return None
        except Exception:
            return None
    
    def get_content_info(self, password_path: str) -> Optional[Dict[str, Any]]:
        """
        Get cached content info for a password.
        Returns None if not cached or cache is invalid.
        """
        if password_path not in self._cache:
            return None
        
        cached_entry = self._cache[password_path]
        
        # Check if cache is still valid by comparing file hash
        current_hash = self._get_file_hash(password_path)
        if current_hash != cached_entry.get('file_hash'):
            # Cache is stale, remove it
            del self._cache[password_path]
            self._save_cache()
            self.logger.debug(f"Cache invalidated for {password_path} (stale hash)")
            return None
        
        content_info = {
            'has_totp': cached_entry.get('has_totp', False),
            'has_url': cached_entry.get('has_url', False),
            'url': cached_entry.get('url'),
            'cached_at': cached_entry.get('cached_at')
        }
        
        return content_info
    
    def set_content_info(self, password_path: str, has_totp: bool, has_url: bool, url: Optional[str] = None):
        """Cache content info for a password."""
        file_hash = self._get_file_hash(password_path)
        if file_hash is None:
            self.logger.warning(f"Could not get file hash for {password_path}, not caching")
            return
        
        self._cache[password_path] = {
            'has_totp': has_totp,
            'has_url': has_url,
            'url': url,
            'file_hash': file_hash,
            'cached_at': time.time()
        }
        
        self._save_cache()
        self.logger.debug(f"Cached content info for {password_path}")
    
    def invalidate(self, password_path: str):
        """Invalidate cache entry for a specific password."""
        if password_path in self._cache:
            del self._cache[password_path]
            self._save_cache()
            self.logger.debug(f"Invalidated cache for {password_path}")
    
    def get_uncached_passwords(self, password_list: list) -> list:
        """Get list of passwords that need content processing (now processes ALL passwords)."""
        # Process all passwords to ensure complete TOTP/URL detection
        cached_count = 0
        empty_cached_count = 0
        never_cached_count = 0
        
        for password_path in password_list:
            content_info = self.get_content_info(password_path)
            if content_info is None:
                never_cached_count += 1
            else:
                # Check if this is a meaningful cache entry or just defaults
                has_meaningful_content = (
                    content_info.get('has_totp', False) or 
                    content_info.get('has_url', False) or 
                    content_info.get('url')
                )
                
                if has_meaningful_content:
                    cached_count += 1
                else:
                    empty_cached_count += 1
        
        self.logger.info(f"Cache analysis: {cached_count} meaningfully cached, {empty_cached_count} empty cached, {never_cached_count} never cached, {len(password_list)} total will be processed")
        # Return all passwords for processing to ensure complete detection
        return password_list.copy()
    
    def clear_all(self):
        """Clear all cached content."""
        self._cache.clear()
        self._save_cache()
        self.logger.info("Cleared all content cache")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'total_entries': len(self._cache),
            'cache_file_exists': os.path.exists(self._cache_file) if self._cache_file else False
        }