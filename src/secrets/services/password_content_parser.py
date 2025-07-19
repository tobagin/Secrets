"""
PasswordContentParser service for centralized password content parsing and generation.

This service eliminates duplication in password content parsing logic that was
scattered across dialog classes and UI components.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class FieldType(Enum):
    """Types of fields that can be parsed from password content."""
    PASSWORD = "password"
    USERNAME = "username"
    URL = "url"
    TOTP = "totp"
    RECOVERY_CODE = "recovery_code"
    NOTE = "note"
    CUSTOM = "custom"


@dataclass
class ParsedField:
    """Represents a parsed field from password content."""
    type: FieldType
    value: str
    key: str = ""
    line_number: int = 0
    is_multiline: bool = False


@dataclass
class PasswordData:
    """Structured representation of password entry data."""
    password: str = ""
    username: str = ""
    url: str = ""
    totp: str = ""
    recovery_codes: List[str] = field(default_factory=list)
    notes: str = ""
    custom_fields: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'password': self.password,
            'username': self.username,
            'url': self.url,
            'totp': self.totp,
            'recovery_codes': self.recovery_codes.copy(),
            'notes': self.notes,
            'custom_fields': self.custom_fields.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PasswordData':
        """Create from dictionary representation."""
        return cls(
            password=data.get('password', ''),
            username=data.get('username', ''),
            url=data.get('url', ''),
            totp=data.get('totp', ''),
            recovery_codes=data.get('recovery_codes', []),
            notes=data.get('notes', ''),
            custom_fields=data.get('custom_fields', {})
        )
    
    def is_empty(self) -> bool:
        """Check if password data is empty."""
        return (not self.password and not self.username and not self.url and 
                not self.totp and not self.recovery_codes and not self.notes and 
                not self.custom_fields)


class PasswordContentParser:
    """
    Service for parsing and generating password file content.
    
    This service provides centralized functionality for:
    - Parsing password file content into structured data
    - Generating password file content from structured data
    - Validating password content format
    - Extracting specific fields from content
    - Handling various password file formats
    """
    
    # Standard field mappings (case-insensitive)
    FIELD_MAPPINGS = {
        'username': ['username', 'user', 'login', 'email', 'account'],
        'url': ['url', 'website', 'site', 'web', 'link'],
        'totp': ['totp', 'otp', 'secret', 'mfa', '2fa', 'authenticator'],
        'recovery': ['recovery', 'recovery_code', 'backup_code', 'backup'],
        'note': ['note', 'notes', 'comment', 'comments', 'description', 'desc']
    }
    
    # Recovery code patterns
    RECOVERY_CODE_PATTERNS = [
        re.compile(r'^recovery_?code_?\d*:', re.IGNORECASE),
        re.compile(r'^backup_?code_?\d*:', re.IGNORECASE),
        re.compile(r'^recovery_?\d*:', re.IGNORECASE),
    ]

    def __init__(self):
        """Initialize the password content parser."""
        self._field_cache = {}
    
    def parse_content(self, content: str) -> PasswordData:
        """
        Parse password file content into structured data.
        
        Args:
            content: Raw password file content
            
        Returns:
            PasswordData object with parsed fields
        """
        if not content or not content.strip():
            return PasswordData()
        
        lines = content.split('\n')
        parsed_data = PasswordData()
        
        if not lines:
            return parsed_data
        
        # First line is always the password
        parsed_data.password = lines[0].strip()
        
        # Parse remaining lines
        notes_started = False
        notes_lines = []
        recovery_count = 1
        
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            
            # Skip empty lines (but preserve them in notes)
            if not line:
                if notes_started:
                    notes_lines.append('')
                continue
            
            # Check if this starts the notes section
            if self._is_notes_marker(line):
                notes_started = True
                continue
            
            # If we're in notes section, collect all remaining lines
            if notes_started:
                notes_lines.append(line)
                continue
            
            # Parse key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Determine field type and set value
                field_type = self._determine_field_type(key)
                
                if field_type == 'username':
                    parsed_data.username = value
                elif field_type == 'url':
                    parsed_data.url = value
                elif field_type == 'totp':
                    parsed_data.totp = value
                elif field_type == 'recovery':
                    parsed_data.recovery_codes.append(value)
                else:
                    # Store as custom field
                    parsed_data.custom_fields[key] = value
            elif notes_started:
                # If we're in notes and this doesn't look like a key-value pair
                notes_lines.append(line)
        
        # Join notes lines
        if notes_lines:
            parsed_data.notes = '\n'.join(notes_lines).strip()
        
        return parsed_data
    
    def generate_content(self, data: PasswordData, 
                        include_empty_fields: bool = False,
                        custom_order: Optional[List[str]] = None) -> str:
        """
        Generate password file content from structured data.
        
        Args:
            data: PasswordData object to convert
            include_empty_fields: Whether to include empty optional fields
            custom_order: Custom order for fields (defaults to standard order)
            
        Returns:
            Formatted password file content
        """
        lines = []
        
        # Password is always first (required)
        if data.password:
            lines.append(data.password)
        
        # Determine field order
        field_order = custom_order or ['username', 'url', 'totp', 'recovery_codes', 'custom_fields']
        
        # Add fields in specified order
        for field_name in field_order:
            if field_name == 'username' and (data.username or include_empty_fields):
                if data.username:
                    lines.append(f"username: {data.username}")
            elif field_name == 'url' and (data.url or include_empty_fields):
                if data.url:
                    lines.append(f"url: {data.url}")
            elif field_name == 'totp' and (data.totp or include_empty_fields):
                if data.totp:
                    lines.append(f"totp: {data.totp}")
            elif field_name == 'recovery_codes' and data.recovery_codes:
                for i, code in enumerate(data.recovery_codes, 1):
                    lines.append(f"recovery_code_{i}: {code}")
            elif field_name == 'custom_fields' and data.custom_fields:
                for key, value in data.custom_fields.items():
                    lines.append(f"{key}: {value}")
        
        # Add notes at the end
        if data.notes:
            lines.append("")  # Empty line before notes
            lines.append("Notes:")
            lines.extend(data.notes.split('\n'))
        
        return '\n'.join(lines)
    
    def extract_field(self, content: str, field_name: str) -> Optional[str]:
        """
        Extract a specific field value from password content.
        
        Args:
            content: Password file content
            field_name: Name of field to extract (username, url, totp, etc.)
            
        Returns:
            Field value or None if not found
        """
        data = self.parse_content(content)
        
        field_map = {
            'password': data.password,
            'username': data.username,
            'url': data.url,
            'totp': data.totp,
            'notes': data.notes
        }
        
        return field_map.get(field_name.lower())
    
    def extract_recovery_codes(self, content: str) -> List[str]:
        """
        Extract all recovery codes from password content.
        
        Args:
            content: Password file content
            
        Returns:
            List of recovery codes
        """
        data = self.parse_content(content)
        return data.recovery_codes
    
    def update_field(self, content: str, field_name: str, new_value: str) -> str:
        """
        Update a specific field in password content.
        
        Args:
            content: Original password file content
            field_name: Name of field to update
            new_value: New value for the field
            
        Returns:
            Updated password file content
        """
        data = self.parse_content(content)
        
        # Update the specified field
        if field_name.lower() == 'password':
            data.password = new_value
        elif field_name.lower() == 'username':
            data.username = new_value
        elif field_name.lower() == 'url':
            data.url = new_value
        elif field_name.lower() == 'totp':
            data.totp = new_value
        elif field_name.lower() == 'notes':
            data.notes = new_value
        else:
            # Custom field
            data.custom_fields[field_name.lower()] = new_value
        
        return self.generate_content(data)
    
    def validate_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate password file content format.
        
        Args:
            content: Password file content to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not content or not content.strip():
            errors.append("Password content cannot be empty")
            return False, errors
        
        lines = content.split('\n')
        
        # Check if first line exists (password)
        if not lines[0].strip():
            errors.append("Password (first line) cannot be empty")
        
        # Validate key-value pairs
        for i, line in enumerate(lines[1:], 2):
            line = line.strip()
            if not line:
                continue
                
            # Skip notes section
            if self._is_notes_marker(line):
                break
                
            # Check key-value format (but allow notes without colons)
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if not key:
                    errors.append(f"Line {i}: Empty key in key-value pair")
                
                # Validate TOTP format if present
                if self._determine_field_type(key.lower()) == 'totp' and value:
                    if not self._validate_totp_secret(value):
                        errors.append(f"Line {i}: Invalid TOTP secret format")
                
                # Validate URL format if present
                if self._determine_field_type(key.lower()) == 'url' and value:
                    if not self._validate_url_format(value):
                        errors.append(f"Line {i}: Invalid URL format")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_field_suggestions(self, partial_key: str) -> List[str]:
        """
        Get field name suggestions based on partial input.
        
        Args:
            partial_key: Partial field name
            
        Returns:
            List of suggested field names
        """
        suggestions = []
        partial_lower = partial_key.lower()
        
        # Check standard fields
        for field_type, aliases in self.FIELD_MAPPINGS.items():
            for alias in aliases:
                if alias.startswith(partial_lower):
                    suggestions.append(alias)
        
        # Add some common custom fields
        common_fields = ['email', 'phone', 'pin', 'security_question', 'api_key', 'token']
        for field in common_fields:
            if field.startswith(partial_lower):
                suggestions.append(field)
        
        return sorted(list(set(suggestions)))
    
    def get_content_statistics(self, content: str) -> Dict[str, Any]:
        """
        Get statistics about password content.
        
        Args:
            content: Password file content
            
        Returns:
            Dictionary with content statistics
        """
        data = self.parse_content(content)
        
        stats = {
            'total_lines': len(content.split('\n')) if content else 0,
            'has_password': bool(data.password),
            'has_username': bool(data.username),
            'has_url': bool(data.url),
            'has_totp': bool(data.totp),
            'recovery_codes_count': len(data.recovery_codes),
            'custom_fields_count': len(data.custom_fields),
            'has_notes': bool(data.notes),
            'notes_lines': len(data.notes.split('\n')) if data.notes else 0,
            'password_length': len(data.password) if data.password else 0,
            'estimated_strength': self._estimate_password_strength(data.password)
        }
        
        return stats
    
    # Private helper methods
    
    def _determine_field_type(self, key: str) -> str:
        """Determine the type of field based on key."""
        key_lower = key.lower()
        
        for field_type, aliases in self.FIELD_MAPPINGS.items():
            if key_lower in aliases:
                return field_type
        
        # Check recovery code patterns
        for pattern in self.RECOVERY_CODE_PATTERNS:
            if pattern.match(key + ':'):
                return 'recovery'
        
        return 'custom'
    
    def _is_notes_marker(self, line: str) -> bool:
        """Check if line marks the start of notes section."""
        return line.lower().rstrip(':') in ['notes', 'note', 'comments', 'comment', 'description']
    
    def _validate_totp_secret(self, secret: str) -> bool:
        """Validate TOTP secret format."""
        # Basic validation - should be base32 encoded
        import string
        base32_chars = string.ascii_uppercase + '234567='
        return all(c in base32_chars for c in secret.upper())
    
    def _validate_url_format(self, url: str) -> bool:
        """Validate URL format."""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _estimate_password_strength(self, password: str) -> str:
        """Estimate password strength."""
        if not password:
            return 'none'
        
        score = 0
        
        # Length scoring
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        # Character variety scoring
        if any(c.islower() for c in password):
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 1
        
        # Convert score to strength
        if score <= 2:
            return 'weak'
        elif score <= 4:
            return 'medium'
        elif score <= 6:
            return 'strong'
        else:
            return 'very_strong'


# Convenience functions for common operations

def parse_password_content(content: str) -> PasswordData:
    """Convenience function to parse password content."""
    parser = PasswordContentParser()
    return parser.parse_content(content)


def generate_password_content(data: PasswordData) -> str:
    """Convenience function to generate password content."""
    parser = PasswordContentParser()
    return parser.generate_content(data)


def extract_password_field(content: str, field_name: str) -> Optional[str]:
    """Convenience function to extract a field from password content."""
    parser = PasswordContentParser()
    return parser.extract_field(content, field_name)


def validate_password_content(content: str) -> Tuple[bool, List[str]]:
    """Convenience function to validate password content."""
    parser = PasswordContentParser()
    return parser.validate_content(content)