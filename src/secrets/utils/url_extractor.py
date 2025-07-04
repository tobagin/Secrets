"""URL extraction and processing utilities."""

import re
import urllib.parse
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass


@dataclass
class ExtractedURL:
    """Container for extracted URL information."""
    url: str
    domain: str
    scheme: str
    path: str = ""
    is_valid: bool = True
    normalized_url: str = ""
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.normalized_url:
            self.normalized_url = self.url


class URLExtractor:
    """Utility class for extracting and processing URLs from password entries."""
    
    # Common URL patterns
    URL_PATTERNS = [
        r'https?://[^\s<>"]+',
        r'www\.[^\s<>"]+',
        r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"]*)?',
    ]
    
    # Compiled regex patterns
    _compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in URL_PATTERNS]
    
    # URL normalization rules
    NORMALIZATION_RULES = {
        'remove_www': True,
        'add_https': True,
        'remove_trailing_slash': True,
        'lowercase_domain': True,
    }
    
    @classmethod
    def extract_urls_from_text(cls, text: str) -> List[ExtractedURL]:
        """
        Extract URLs from text content.
        
        Args:
            text: Text to search for URLs
            
        Returns:
            List of ExtractedURL objects
        """
        urls = []
        seen_urls = set()
        
        for pattern in cls._compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                url = match.strip()
                if url and url not in seen_urls:
                    extracted = cls._process_url(url)
                    if extracted and extracted.is_valid:
                        urls.append(extracted)
                        seen_urls.add(url)
        
        return urls
    
    @classmethod
    def extract_primary_url(cls, text: str) -> Optional[ExtractedURL]:
        """
        Extract the primary URL from text (first valid URL found).
        
        Args:
            text: Text to search for URLs
            
        Returns:
            ExtractedURL object or None if no valid URL found
        """
        urls = cls.extract_urls_from_text(text)
        return urls[0] if urls else None
    
    @classmethod
    def extract_url_from_password_content(cls, content: str) -> Optional[ExtractedURL]:
        """
        Extract URL from password entry content.
        
        Looks for URLs in common patterns like:
        - url: https://example.com
        - URL: https://example.com
        - website: https://example.com
        
        Args:
            content: Password entry content
            
        Returns:
            ExtractedURL object or None
        """
        lines = content.split('\n')
        
        # Look for URL in structured format first
        url_keywords = ['url', 'website', 'site', 'link', 'domain']
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in url_keywords and value:
                    extracted = cls._process_url(value)
                    if extracted and extracted.is_valid:
                        return extracted
        
        # Fall back to general URL extraction
        return cls.extract_primary_url(content)
    
    @classmethod
    def _process_url(cls, url: str) -> Optional[ExtractedURL]:
        """
        Process and validate a URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            ExtractedURL object or None if invalid
        """
        if not url:
            return None
        
        original_url = url
        
        # Clean up the URL
        url = url.strip()
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
            if url.startswith('www.'):
                url = 'https://' + url
            else:
                # Try to determine if it's a domain
                if '.' in url and not url.startswith('.'):
                    url = 'https://' + url
                else:
                    return None
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Validate parsed URL
            if not parsed.netloc:
                return None
            
            # Extract components
            domain = parsed.netloc.lower()
            scheme = parsed.scheme.lower()
            path = parsed.path
            
            # Remove common prefixes from domain
            if domain.startswith('www.'):
                clean_domain = domain[4:]
            else:
                clean_domain = domain
            
            # Normalize URL
            normalized = cls._normalize_url(url)
            
            return ExtractedURL(
                url=original_url,
                domain=clean_domain,
                scheme=scheme,
                path=path,
                is_valid=True,
                normalized_url=normalized
            )
            
        except Exception:
            return None
    
    @classmethod
    def _normalize_url(cls, url: str) -> str:
        """
        Normalize a URL according to configured rules.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Apply normalization rules
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = parsed.path
            
            # Remove www if configured
            if cls.NORMALIZATION_RULES.get('remove_www', True):
                if netloc.startswith('www.'):
                    netloc = netloc[4:]
            
            # Use HTTPS by default if configured
            if cls.NORMALIZATION_RULES.get('add_https', True):
                if scheme == 'http':
                    scheme = 'https'
            
            # Remove trailing slash if configured
            if cls.NORMALIZATION_RULES.get('remove_trailing_slash', True):
                if path.endswith('/') and len(path) > 1:
                    path = path[:-1]
            
            # Reconstruct URL
            normalized = urllib.parse.urlunparse((
                scheme,
                netloc,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            return normalized
            
        except Exception:
            return url
    
    @classmethod
    def get_favicon_url(cls, url: str) -> Optional[str]:
        """
        Get the likely favicon URL for a website.
        
        Args:
            url: Website URL
            
        Returns:
            Favicon URL or None
        """
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                return None
            
            # Standard favicon location
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            return f"{base_url}/favicon.ico"
            
        except Exception:
            return None
    
    @classmethod
    def extract_domain_from_path(cls, path: str) -> Optional[str]:
        """
        Extract domain from a password path (e.g., "social/facebook.com" -> "facebook.com").
        
        Args:
            path: Password entry path
            
        Returns:
            Domain name or None
        """
        if not path:
            return None
        
        # Split path and look for domain-like components
        components = path.split('/')
        
        for component in reversed(components):  # Check from right to left
            # Simple domain pattern check
            if '.' in component and len(component) > 3:
                # Remove common extensions like .gpg
                clean_component = component
                if clean_component.endswith('.gpg'):
                    clean_component = clean_component[:-4]
                
                # Check if it looks like a domain
                if cls._is_likely_domain(clean_component):
                    return clean_component
        
        return None
    
    @classmethod
    def _is_likely_domain(cls, text: str) -> bool:
        """
        Check if text looks like a domain name.
        
        Args:
            text: Text to check
            
        Returns:
            True if it looks like a domain
        """
        if not text or '.' not in text:
            return False
        
        # Basic domain pattern
        domain_pattern = r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$'
        return bool(re.match(domain_pattern, text))
    
    @classmethod
    def generate_suggested_path(cls, url: str) -> Optional[str]:
        """
        Generate a suggested password path based on URL.
        
        Args:
            url: URL to generate path from
            
        Returns:
            Suggested path or None
        """
        extracted = cls._process_url(url)
        if not extracted:
            return None
        
        domain = extracted.domain
        
        # Common domain to category mappings
        category_mappings = {
            'gmail.com': 'email',
            'yahoo.com': 'email',
            'outlook.com': 'email',
            'facebook.com': 'social',
            'twitter.com': 'social',
            'instagram.com': 'social',
            'linkedin.com': 'social',
            'github.com': 'development',
            'gitlab.com': 'development',
            'stackoverflow.com': 'development',
        }
        
        # Check for direct mapping
        if domain in category_mappings:
            category = category_mappings[domain]
            return f"{category}/{domain}"
        
        # Guess category based on domain
        if any(keyword in domain for keyword in ['mail', 'email']):
            return f"email/{domain}"
        elif any(keyword in domain for keyword in ['social', 'facebook', 'twitter', 'instagram']):
            return f"social/{domain}"
        elif any(keyword in domain for keyword in ['bank', 'financial', 'finance']):
            return f"finance/{domain}"
        elif any(keyword in domain for keyword in ['shop', 'store', 'commerce', 'amazon', 'ebay']):
            return f"shopping/{domain}"
        else:
            return f"websites/{domain}"
    
    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, str]:
        """
        Validate a URL.
        
        Args:
            url: URL to validate
            
        Returns:
            (is_valid, error_message)
        """
        if not url:
            return False, "URL cannot be empty"
        
        if len(url) > 2000:
            return False, "URL is too long (max 2000 characters)"
        
        extracted = cls._process_url(url)
        if not extracted:
            return False, "Invalid URL format"
        
        # Additional validation
        if not extracted.domain:
            return False, "URL must have a valid domain"
        
        if '.' not in extracted.domain:
            return False, "Domain must contain at least one dot"
        
        return True, ""