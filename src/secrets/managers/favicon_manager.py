"""
Favicon Manager for downloading and caching website favicons.
"""

import os
import hashlib
import time
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import io
import logging
from gi.repository import Gtk, GdkPixbuf, Gio, GLib
from typing import Optional, Callable

# Get logger for favicon management
logger = logging.getLogger(__name__)

# Try to import PIL for ICO conversion
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available, ICO files may not load properly", extra={
        'dependency': 'PIL',
        'impact': 'ico_conversion_disabled'
    })


class FaviconManager:
    """Manages downloading and caching of website favicons."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the favicon manager.

        Args:
            cache_dir: Directory to store cached favicons. If None, uses ~/.local/share/secrets/favicons
        """
        if cache_dir is None:
            # Use ~/.local/share/secrets/favicons for better Flatpak compatibility
            cache_dir = os.path.expanduser("~/.local/share/secrets/favicons")

        self.cache_dir = cache_dir
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create favicon cache directory: {e}", extra={
                'cache_dir': self.cache_dir,
                'error_type': type(e).__name__
            })
    
    def get_favicon_path(self, url: str) -> Optional[str]:
        """
        Get the local path to a cached favicon for the given URL.
        
        Args:
            url: The website URL
            
        Returns:
            Path to cached favicon file, or None if not cached
        """
        if not url:
            return None
        
        # Extract domain from URL
        domain = self._extract_domain(url)
        if not domain:
            return None
        
        # Generate cache filename
        cache_filename = self._get_cache_filename(domain)
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        if os.path.exists(cache_path):
            return cache_path
        
        return None
    
    def download_favicon_async(self, url: str, callback: Callable[[Optional[str]], None]):
        """
        Download favicon for the given URL asynchronously.
        
        Args:
            url: The website URL
            callback: Function to call with the favicon path (or None if failed)
        """
        if not url:
            GLib.idle_add(callback, None)
            return
        
        domain = self._extract_domain(url)
        if not domain:
            GLib.idle_add(callback, None)
            return

        # Check if already cached
        cached_path = self.get_favicon_path(url)
        if cached_path:
            logger.debug("Using cached favicon", extra={
                'tag': 'favicon',
                'domain': domain,
                'cached_path': cached_path,
                'action': 'cache_hit'
            })
            GLib.idle_add(callback, cached_path)
            return
        
        # Download in a separate thread
        logger.debug("Starting favicon download for domain", extra={
            'tag': 'favicon',
            'domain': domain,
            'action': 'download_start',
            'cache_status': 'not_cached'
        })
        def download_worker():
            try:
                favicon_path = self._download_favicon(domain)
                GLib.idle_add(callback, favicon_path)
            except Exception as e:
                logger.debug("Error downloading favicon", extra={
                    'tag': 'favicon',
                    'domain': domain,
                    'action': 'download_error',
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                GLib.idle_add(callback, None)
        
        # Use GLib thread pool for async download
        GLib.Thread.new("favicon-download", download_worker)

    def get_favicon_pixbuf_async(self, url: str, callback: Callable[[Optional[GdkPixbuf.Pixbuf]], None]):
        """
        Get favicon as a GdkPixbuf asynchronously.

        Args:
            url: The website URL
            callback: Function to call with the pixbuf (or None if failed)
        """
        # First check if we have a cached favicon
        cached_path = self.get_favicon_path(url)
        if cached_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(cached_path)
                logger.debug("Using cached favicon pixbuf", extra={
                    'tag': 'favicon',
                    'domain': self._extract_domain(url),
                    'cached_path': cached_path,
                    'action': 'pixbuf_cache_hit'
                })
                GLib.idle_add(callback, pixbuf)
                return
            except Exception as e:
                logger.debug("Cached favicon corrupted", extra={
                    'tag': 'favicon',
                    'domain': self._extract_domain(url),
                    'cached_path': cached_path,
                    'action': 'cache_corruption',
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                # Remove corrupted cache file
                try:
                    os.remove(cached_path)
                except OSError:
                    pass

        # If not cached, download it
        logger.debug("Starting favicon pixbuf download", extra={
            'tag': 'favicon',
            'domain': self._extract_domain(url),
            'action': 'pixbuf_download_start',
            'cache_status': 'not_cached'
        })
        def on_favicon_path(path):
            if path:
                try:
                    pixbuf = self._load_pixbuf_from_file(path)
                    GLib.idle_add(callback, pixbuf)
                except Exception as e:
                    logger.debug("Error loading favicon pixbuf", extra={
                        'tag': 'favicon',
                        'path': path,
                        'action': 'pixbuf_load_error',
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                    GLib.idle_add(callback, None)
            else:
                GLib.idle_add(callback, None)

        self.download_favicon_async(url, on_favicon_path)
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            original_url = url

            # Convert HTTP to HTTPS for security
            if url.startswith('http://'):
                url = 'https://' + url[7:]
                logger.debug("Converted HTTP to HTTPS for favicon", extra={
                    'tag': 'favicon',
                    'original_url': original_url,
                    'converted_url': url,
                    'action': 'protocol_conversion'
                })
            # Add protocol if missing
            elif not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()

            # If no domain found, the original might be just a domain
            if not domain and original_url:
                # Try treating the original as a domain directly
                domain = original_url.lower().strip()
                # Remove protocol if it was in the original
                if domain.startswith(('http://', 'https://')):
                    domain = urllib.parse.urlparse('https://' + domain if not domain.startswith(('http://', 'https://')) else domain).netloc.lower()

            # Remove www. prefix for consistency
            if domain.startswith('www.'):
                domain = domain[4:]

            logger.debug("Extracted domain from URL", extra={
                'tag': 'favicon',
                'original_url': original_url,
                'extracted_domain': domain,
                'action': 'domain_extraction'
            })
            return domain if domain else None
        except Exception as e:
            logger.debug("Error extracting domain from URL", extra={
                'tag': 'favicon',
                'url': url,
                'action': 'domain_extraction_error',
                'error': str(e),
                'error_type': type(e).__name__
            })
            return None
    
    def _get_cache_filename(self, domain: str) -> str:
        """Generate cache filename for domain."""
        # Use hash to avoid filesystem issues with special characters
        domain_hash = hashlib.md5(domain.encode()).hexdigest()
        return f"{domain_hash}.ico"
    
    def _download_favicon(self, domain: str) -> Optional[str]:
        """
        Download favicon for domain and save to cache.
        
        Args:
            domain: The domain to download favicon for
            
        Returns:
            Path to cached favicon file, or None if failed
        """
        # Try favicon URLs in order of preference (prioritize .ico files)
        favicon_urls = []

        # Check if we should try www. variant
        should_try_www = self._should_try_www_variant(domain)

        # Priority 1: Standard favicon.ico files (most common and reliable)
        favicon_urls.append(f"https://{domain}/favicon.ico")
        if should_try_www:
            favicon_urls.append(f"https://www.{domain}/favicon.ico")

        # Priority 2: PNG favicons (common alternative)
        favicon_urls.append(f"https://{domain}/favicon.png")
        if should_try_www:
            favicon_urls.append(f"https://www.{domain}/favicon.png")

        # Priority 3: Apple touch icons (fallback for mobile-first sites)
        favicon_urls.append(f"https://{domain}/apple-touch-icon.png")
        favicon_urls.append(f"https://{domain}/apple-touch-icon-precomposed.png")
        if should_try_www:
            favicon_urls.append(f"https://www.{domain}/apple-touch-icon.png")
            favicon_urls.append(f"https://www.{domain}/apple-touch-icon-precomposed.png")

        # Priority 4: For subdomains, also try the main domain as fallback
        # Example: for mail.zoho.eu, also try zoho.eu
        if not should_try_www:  # This means it's a subdomain
            main_domain = self._get_main_domain(domain)
            if main_domain and main_domain != domain:
                favicon_urls.append(f"https://{main_domain}/favicon.ico")
                favicon_urls.append(f"https://www.{main_domain}/favicon.ico")
                favicon_urls.append(f"https://{main_domain}/favicon.png")
                favicon_urls.append(f"https://www.{main_domain}/favicon.png")

        # Priority 5: Special cases for known problematic sites
        if "zoho" in domain:
            # Zoho has strict anti-bot protection, try alternative approaches
            favicon_urls.append(f"https://www.zoho.com/favicon.ico")
            favicon_urls.append(f"https://zoho.com/favicon.ico")
        
        cache_filename = self._get_cache_filename(domain)
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        for i, favicon_url in enumerate(favicon_urls, 1):
            try:
                logger.debug("Trying favicon URL", extra={
                    'tag': 'favicon',
                    'domain': domain,
                    'favicon_url': favicon_url,
                    'attempt': i,
                    'total_attempts': len(favicon_urls),
                    'action': 'download_attempt'
                })
                # Set a reasonable timeout and browser-like user agent
                # Extract domain for referrer
                parsed_url = urllib.parse.urlparse(favicon_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

                request = urllib.request.Request(
                    favicon_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Cache-Control': 'no-cache',
                        'Sec-Fetch-Dest': 'image',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'same-origin'
                    }
                )

                # Add a small delay to avoid being flagged as a bot
                time.sleep(0.1)

                # Create an opener that handles redirects and cookies
                cookie_jar = http.cookiejar.CookieJar()
                opener = urllib.request.build_opener(
                    urllib.request.HTTPRedirectHandler,
                    urllib.request.HTTPCookieProcessor(cookie_jar),
                    urllib.request.HTTPSHandler(context=None)  # Use default SSL context
                )

                logger.debug("Attempting to download favicon", extra={
                    'tag': 'favicon',
                    'url': favicon_url,
                    'action': 'download_request'
                })
                with opener.open(request, timeout=5) as response:
                    logger.debug("Received favicon response", extra={
                        'tag': 'favicon',
                        'url': favicon_url,
                        'status': response.status,
                        'content_type': response.headers.get('Content-Type', 'unknown'),
                        'action': 'download_response'
                    })
                    if response.status == 200:
                        # Save to cache
                        with open(cache_path, 'wb') as f:
                            f.write(response.read())

                        # Verify it's a valid image
                        if self._is_valid_image(cache_path):
                            # Success! Return immediately without trying other URLs
                            logger.debug("Successfully downloaded favicon", extra={
                                'tag': 'favicon',
                                'url': favicon_url,
                                'cache_path': cache_path,
                                'attempts_used': i,
                                'total_attempts': len(favicon_urls),
                                'action': 'download_success'
                            })
                            return cache_path
                        else:
                            logger.debug("Downloaded file is not a valid image", extra={
                                'tag': 'favicon',
                                'url': favicon_url,
                                'cache_path': cache_path,
                                'action': 'download_invalid_image'
                            })
                            # Remove invalid file and continue to next URL
                            try:
                                os.remove(cache_path)
                            except OSError:
                                pass

            except urllib.error.HTTPError as e:
                # HTTP error (404, 403, etc.)
                logger.debug("Failed to download favicon - HTTP error", extra={
                    'tag': 'favicon',
                    'url': favicon_url,
                    'http_code': e.code,
                    'http_reason': e.reason,
                    'action': 'download_http_error'
                })
                continue
            except urllib.error.URLError as e:
                # Network error (timeout, connection refused, etc.)
                logger.debug("Failed to download favicon - Network error", extra={
                    'tag': 'favicon',
                    'url': favicon_url,
                    'reason': str(e.reason),
                    'action': 'download_network_error'
                })
                continue
            except Exception as e:
                # Other errors
                logger.debug("Failed to download favicon - Other error", extra={
                    'tag': 'favicon',
                    'url': favicon_url,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'action': 'download_other_error'
                })
                continue

        # No favicon found after trying all URLs
        logger.debug("No valid favicon found for domain", extra={
            'tag': 'favicon',
            'domain': domain,
            'urls_tried': len(favicon_urls),
            'action': 'download_all_failed'
        })
        return None

    def _should_try_www_variant(self, domain: str) -> bool:
        """
        Determine if we should try the www. variant of a domain.

        Rules:
        - Don't try www. if domain already starts with www.
        - Don't try www. if domain has a subdomain (more than 2 parts)
        - Do try www. for simple domains like "example.com"
        """
        if domain.startswith('www.'):
            return False

        # Split domain into parts
        parts = domain.split('.')

        # If domain has more than 2 parts, it likely has a subdomain
        # Examples: mail.google.com, api.github.com, subdomain.example.com
        if len(parts) > 2:
            return False

        # For simple domains like "example.com", try www. variant
        return True

    def _get_main_domain(self, domain: str) -> Optional[str]:
        """
        Extract the main domain from a subdomain.

        Examples:
        - mail.zoho.eu -> zoho.eu
        - api.github.com -> github.com
        - subdomain.example.com -> example.com
        - example.com -> example.com (unchanged)
        """
        parts = domain.split('.')

        # If it's already a simple domain (2 parts), return as-is
        if len(parts) <= 2:
            return domain

        # For subdomains, take the last 2 parts
        # This works for most cases but might not be perfect for complex TLDs
        return '.'.join(parts[-2:])

    def _is_valid_image(self, file_path: str) -> bool:
        """Check if the file is a valid image."""
        try:
            # Check file size first
            file_size = os.path.getsize(file_path)
            logger.debug("Validating image file", extra={
                'tag': 'favicon',
                'file_path': file_path,
                'file_size': file_size,
                'action': 'validation_start'
            })

            if file_size == 0:
                logger.debug("File is empty", extra={
                    'tag': 'favicon',
                    'file_path': file_path,
                    'action': 'validation_empty_file'
                })
                return False

            # For ICO files, try a different approach since GdkPixbuf might not support them well
            if file_path.lower().endswith('.ico'):
                # Check if it looks like a valid ICO file by checking the header
                with open(file_path, 'rb') as f:
                    header = f.read(6)
                    if len(header) >= 6 and header[:4] == b'\x00\x00\x01\x00':
                        logger.debug("Valid ICO file detected", extra={
                            'tag': 'favicon',
                            'file_path': file_path,
                            'action': 'validation_ico_valid'
                        })
                        return True

            # Try to load with GdkPixbuf to verify it's a valid image
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(file_path)
            if pixbuf is not None:
                logger.debug("Valid image validated", extra={
                    'tag': 'favicon',
                    'file_path': file_path,
                    'width': pixbuf.get_width(),
                    'height': pixbuf.get_height(),
                    'action': 'validation_success'
                })
                return True
            else:
                logger.debug("GdkPixbuf returned None for file", extra={
                    'tag': 'favicon',
                    'file_path': file_path,
                    'action': 'validation_pixbuf_none'
                })
                return False
        except Exception as e:
            logger.debug("Image validation failed", extra={
                'tag': 'favicon',
                'file_path': file_path,
                'error': str(e),
                'error_type': type(e).__name__,
                'action': 'validation_error'
            })
            return False

    def _load_pixbuf_from_file(self, file_path: str):
        """Load a pixbuf from file, with special handling for ICO files."""
        try:
            # First try direct loading
            try:
                return GdkPixbuf.Pixbuf.new_from_file(file_path)
            except Exception as e:
                logger.debug("Direct pixbuf loading failed", extra={
                    'tag': 'favicon',
                    'file_path': file_path,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'action': 'pixbuf_direct_load_failed'
                })

            # If it's an ICO file and direct loading failed, try to convert it using PIL
            if file_path.lower().endswith('.ico') and PIL_AVAILABLE:
                logger.debug("Attempting ICO to PNG conversion using PIL", extra={
                    'tag': 'favicon',
                    'file_path': file_path,
                    'action': 'conversion_ico_to_png_start'
                })
                try:
                    # Open ICO file with PIL
                    with Image.open(file_path) as img:
                        # Convert to RGBA if needed
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        # Resize to a reasonable size if too large
                        if img.width > 64 or img.height > 64:
                            img = img.resize((32, 32), Image.Resampling.LANCZOS)

                        # Save to bytes as PNG
                        png_bytes = io.BytesIO()
                        img.save(png_bytes, format='PNG')
                        png_bytes.seek(0)

                        # Create GInputStream from bytes
                        stream = Gio.MemoryInputStream.new_from_data(png_bytes.getvalue())

                        # Load pixbuf from PNG stream
                        pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream)
                        logger.debug("Successfully converted ICO to PNG", extra={
                            'tag': 'favicon',
                            'file_path': file_path,
                            'width': pixbuf.get_width(),
                            'height': pixbuf.get_height(),
                            'action': 'conversion_ico_to_png_success'
                        })
                        return pixbuf

                except Exception as e:
                    logger.debug("PIL ICO conversion failed", extra={
                        'tag': 'favicon',
                        'file_path': file_path,
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'action': 'conversion_ico_to_png_failed'
                    })

            # If PIL is not available or conversion failed, try GdkPixbuf scaling methods
            if file_path.lower().endswith('.ico'):
                logger.debug("Attempting ICO conversion with GdkPixbuf", extra={
                    'tag': 'favicon',
                    'file_path': file_path,
                    'action': 'conversion_ico_gdkpixbuf_start'
                })
                # Try to load at a specific size (32x32 is common for favicons)
                try:
                    return GdkPixbuf.Pixbuf.new_from_file_at_scale(file_path, 32, 32, True)
                except Exception as e2:
                    logger.debug("ICO scaling failed", extra={
                        'tag': 'favicon',
                        'file_path': file_path,
                        'error': str(e2),
                        'error_type': type(e2).__name__,
                        'action': 'conversion_ico_scaling_failed'
                    })
                    # Try loading at original size
                    try:
                        return GdkPixbuf.Pixbuf.new_from_file_at_size(file_path, 32, 32)
                    except Exception as e3:
                        logger.debug("ICO size loading failed", extra={
                            'tag': 'favicon',
                            'file_path': file_path,
                            'error': str(e3),
                            'error_type': type(e3).__name__,
                            'action': 'conversion_ico_size_loading_failed'
                        })

            return None
        except Exception as e:
            logger.debug("Error loading pixbuf from file", extra={
                'tag': 'favicon',
                'file_path': file_path,
                'error': str(e),
                'error_type': type(e).__name__,
                'action': 'pixbuf_load_error'
            })
            return None
    
    def create_favicon_image(self, favicon_path: str, size: int = 32) -> Optional[Gtk.Image]:
        """
        Create a Gtk.Image from a favicon file.
        
        Args:
            favicon_path: Path to the favicon file
            size: Desired size for the image
            
        Returns:
            Gtk.Image widget, or None if failed
        """
        try:
            # Load and scale the favicon
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                favicon_path, size, size, True
            )
            
            if pixbuf:
                image = Gtk.Image()
                image.set_from_pixbuf(pixbuf)
                return image
                
        except Exception as e:
            logger.debug("Error creating image from favicon", extra={
                'tag': 'favicon',
                'favicon_path': favicon_path,
                'size': size,
                'error': str(e),
                'error_type': type(e).__name__,
                'action': 'image_creation_error'
            })
        
        return None
    
    def clear_cache(self):
        """Clear all cached favicons."""
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except OSError as e:
            logger.debug("Error clearing favicon cache", extra={
                'tag': 'favicon',
                'cache_dir': self.cache_dir,
                'error': str(e),
                'error_type': type(e).__name__,
                'action': 'cache_clear_error'
            })


# Global favicon manager instance
_favicon_manager = None

def get_favicon_manager() -> FaviconManager:
    """Get the global favicon manager instance."""
    global _favicon_manager
    if _favicon_manager is None:
        _favicon_manager = FaviconManager()
    return _favicon_manager
