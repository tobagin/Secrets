"""Unit tests for PathValidator."""

import pytest
from src.secrets.utils.path_validator import PathValidator


class TestPathValidator:
    """Test cases for PathValidator."""
    
    def test_validate_password_path_valid(self):
        """Test validation with valid paths."""
        valid_paths = [
            "simple",
            "folder/password",
            "deep/folder/structure/password",
            "social/facebook.com",
            "email/gmail.com",
            "work/project-name",
            "personal/bank_account",
            "test123",
            "a/b/c/d/e"
        ]
        
        for path in valid_paths:
            valid, message = PathValidator.validate_password_path(path)
            assert valid, f"Path '{path}' should be valid: {message}"
    
    def test_validate_password_path_invalid(self):
        """Test validation with invalid paths."""
        invalid_paths = [
            "",  # Empty
            "../password",  # Directory traversal
            "/password",  # Absolute path
            "~/password",  # Home directory
            "password/",  # Trailing slash
            "pass//word",  # Double slash
            "pass<word",  # Invalid character
            "pass>word",  # Invalid character
            "pass|word",  # Invalid character
            "pass\x00word",  # Null byte
            "pass\x01word",  # Control character
            "a" * 300,  # Too long
        ]
        
        for path in invalid_paths:
            valid, message = PathValidator.validate_password_path(path)
            assert not valid, f"Path '{path}' should be invalid"
            assert message, f"Error message should be provided for '{path}'"
    
    def test_validate_folder_path(self):
        """Test folder path validation."""
        # Should use same validation as password paths
        valid, message = PathValidator.validate_folder_path("folder/subfolder")
        assert valid
        
        valid, message = PathValidator.validate_folder_path("../folder")
        assert not valid
    
    def test_validate_relative_path(self):
        """Test relative path validation."""
        # Valid relative paths
        valid, message = PathValidator.validate_relative_path("sub/folder", "parent")
        assert valid
        
        # Path within base
        valid, message = PathValidator.validate_relative_path("parent/child", "parent")
        assert valid
        
        # Exact match with base
        valid, message = PathValidator.validate_relative_path("parent", "parent")
        assert valid
        
        # Path outside base
        valid, message = PathValidator.validate_relative_path("other/path", "parent")
        assert not valid
    
    def test_sanitize_path(self):
        """Test path sanitization."""
        test_cases = [
            ("", ""),
            ("simple", "simple"),
            ("path\\with\\backslashes", "path/with/backslashes"),
            ("path//with//double//slashes", "path/with/double/slashes"),
            ("path/with/trailing/", "path/with/trailing"),
            ("  /path/with/spaces/  ", "path/with/spaces"),
            ("path<with>invalid|chars", "path_with_invalid_chars"),
            ("path\x00with\x01control", "pathwithcontrol"),
            ("a" * 300, "a" * 255),  # Truncated to max length
        ]
        
        for input_path, expected in test_cases:
            result = PathValidator.sanitize_path(input_path)
            assert result == expected, f"sanitize_path('{input_path}') = '{result}', expected '{expected}'"
    
    def test_normalize_path(self):
        """Test path normalization."""
        test_cases = [
            ("", ""),
            ("simple", "simple"),
            ("path\\with\\backslashes", "path/with/backslashes"),
            ("path//with//double//slashes", "path/with/double/slashes"),
            ("path/with/trailing/", "path/with/trailing"),
            ("/", "/"),  # Root should remain
            ("path/", "path"),
        ]
        
        for input_path, expected in test_cases:
            result = PathValidator.normalize_path(input_path)
            assert result == expected, f"normalize_path('{input_path}') = '{result}', expected '{expected}'"
    
    def test_get_parent_path(self):
        """Test parent path extraction."""
        test_cases = [
            ("simple", ""),
            ("folder/password", "folder"),
            ("deep/folder/structure/password", "deep/folder/structure"),
            ("a/b", "a"),
        ]
        
        for input_path, expected in test_cases:
            result = PathValidator.get_parent_path(input_path)
            assert result == expected, f"get_parent_path('{input_path}') = '{result}', expected '{expected}'"
    
    def test_get_filename(self):
        """Test filename extraction."""
        test_cases = [
            ("simple", "simple"),
            ("folder/password", "password"),
            ("deep/folder/structure/password", "password"),
            ("a/b", "b"),
        ]
        
        for input_path, expected in test_cases:
            result = PathValidator.get_filename(input_path)
            assert result == expected, f"get_filename('{input_path}') = '{result}', expected '{expected}'"
    
    def test_validate_component(self):
        """Test individual component validation."""
        # Valid components
        valid_components = ["password", "folder", "test123", "project-name"]
        for component in valid_components:
            assert PathValidator._validate_component(component)
        
        # Invalid components
        invalid_components = ["", ".", "..", "CON", "PRN", "AUX", "NUL", "test.", "test "]
        for component in invalid_components:
            assert not PathValidator._validate_component(component)
    
    def test_dangerous_patterns(self):
        """Test detection of dangerous patterns."""
        dangerous_paths = [
            "../etc/passwd",
            "../../sensitive",
            "/etc/passwd",
            "~/secrets",
            "path\x00injection",
            "path\x01control"
        ]
        
        for path in dangerous_paths:
            valid, message = PathValidator.validate_password_path(path)
            assert not valid, f"Dangerous path '{path}' should be rejected"
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Very long valid path (but under limit)
        long_path = "/".join(["a"] * 50)  # Should be under 255 chars
        if len(long_path) <= 255:
            valid, message = PathValidator.validate_password_path(long_path)
            assert valid
        
        # Path with Unicode characters (should be valid)
        unicode_path = "folder/пароль"
        valid, message = PathValidator.validate_password_path(unicode_path)
        assert valid