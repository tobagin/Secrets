"""Path validation utilities for password store paths."""

import os
import re
from typing import Tuple


class PathValidator:
    """Centralized path validation for password store operations."""
    
    # Security patterns to reject
    DANGEROUS_PATTERNS = [
        r"\.\.",      # Directory traversal
        r"^/",        # Absolute paths
        r"^~",        # Home directory expansion
        r"\x00",      # Null bytes
        r"[\x01-\x1f]",  # Control characters
    ]
    
    # Maximum path length (reasonable limit)
    MAX_PATH_LENGTH = 255
    
    # Invalid characters for password store paths
    INVALID_CHARS = set('<>:"|?*\x00')
    
    @classmethod
    def validate_password_path(cls, path: str) -> Tuple[bool, str]:
        """
        Validate a password store path.
        
        Returns:
            (bool, str): (is_valid, error_message)
        """
        if not path:
            return False, "Path cannot be empty"
        
        if len(path) > cls.MAX_PATH_LENGTH:
            return False, f"Path too long (max {cls.MAX_PATH_LENGTH} characters)"
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path):
                return False, "Path contains dangerous patterns"
        
        # Check for invalid characters
        if any(char in cls.INVALID_CHARS for char in path):
            return False, "Path contains invalid characters"
        
        # Check path structure
        if path.endswith("/"):
            return False, "Path cannot end with '/'"
        
        if path.startswith("/"):
            return False, "Path cannot be absolute"
        
        # Check for empty path components
        if "//" in path:
            return False, "Path cannot contain empty components"
        
        # Validate individual path components
        components = path.split("/")
        for component in components:
            if not cls._validate_component(component):
                return False, f"Invalid path component: '{component}'"
        
        return True, ""
    
    @classmethod
    def validate_folder_path(cls, path: str) -> Tuple[bool, str]:
        """
        Validate a folder path (same as password path for now).
        
        Returns:
            (bool, str): (is_valid, error_message)
        """
        return cls.validate_password_path(path)
    
    @classmethod
    def validate_relative_path(cls, path: str, base_path: str = "") -> Tuple[bool, str]:
        """
        Validate a relative path within a base path.
        
        Args:
            path: The path to validate
            base_path: The base path to validate against
            
        Returns:
            (bool, str): (is_valid, error_message)
        """
        # First validate the path itself
        valid, message = cls.validate_password_path(path)
        if not valid:
            return valid, message
        
        # If base_path is provided, ensure path is within it
        if base_path:
            if not path.startswith(base_path + "/") and path != base_path:
                return False, f"Path must be within '{base_path}'"
        
        return True, ""
    
    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """
        Sanitize a path by removing/replacing dangerous characters.
        
        Note: This is for user input sanitization, not security validation.
        Always call validate_password_path() after sanitizing.
        """
        if not path:
            return ""
        
        # Remove control characters
        path = re.sub(r'[\x00-\x1f\x7f]', '', path)
        
        # Replace invalid characters with underscores
        for char in cls.INVALID_CHARS:
            path = path.replace(char, '_')
        
        # Normalize path separators
        path = path.replace('\\', '/')
        
        # Remove leading/trailing slashes and spaces
        path = path.strip('/ ')
        
        # Collapse multiple slashes
        path = re.sub(r'/+', '/', path)
        
        # Limit length
        if len(path) > cls.MAX_PATH_LENGTH:
            path = path[:cls.MAX_PATH_LENGTH]
        
        return path
    
    @classmethod
    def _validate_component(cls, component: str) -> bool:
        """Validate a single path component."""
        if not component:
            return False
        
        # Check for reserved names (basic set)
        reserved_names = {'.', '..', 'CON', 'PRN', 'AUX', 'NUL'}
        if component.upper() in reserved_names:
            return False
        
        # Check for names ending with dots or spaces (Windows compatibility)
        if component.endswith(('.', ' ')):
            return False
        
        return True
    
    @classmethod
    def normalize_path(cls, path: str) -> str:
        """
        Normalize a path for consistent handling.
        
        This only does safe normalizations and doesn't validate.
        """
        if not path:
            return ""
        
        # Convert to forward slashes
        path = path.replace('\\', '/')
        
        # Remove trailing slashes (except root)
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        
        # Collapse multiple slashes
        path = re.sub(r'/+', '/', path)
        
        return path
    
    @classmethod
    def get_parent_path(cls, path: str) -> str:
        """Get the parent directory of a path."""
        normalized = cls.normalize_path(path)
        if '/' not in normalized:
            return ""
        return normalized.rsplit('/', 1)[0]
    
    @classmethod
    def get_filename(cls, path: str) -> str:
        """Get the filename component of a path."""
        normalized = cls.normalize_path(path)
        if '/' not in normalized:
            return normalized
        return normalized.rsplit('/', 1)[1]