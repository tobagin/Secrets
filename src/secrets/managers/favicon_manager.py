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
from gi.repository import Gtk, GdkPixbuf, Gio, GLib
from typing import Optional, Callable

# Try to import PIL for ICO conversion
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available, ICO files may not load properly")


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
            print(f"Warning: Could not create favicon cache directory: {e}")
    
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
            print(f"✓ Using cached favicon for {domain}: {cached_path}")
            GLib.idle_add(callback, cached_path)
            return
        
        # Download in a separate thread
        print(f"🔄 Starting favicon download for {domain} (not cached)")
        def download_worker():
            try:
                favicon_path = self._download_favicon(domain)
                GLib.idle_add(callback, favicon_path)
            except Exception as e:
                print(f"Error downloading favicon for {domain}: {e}")
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
                print(f"✓ Using cached favicon pixbuf for {self._extract_domain(url)}: {cached_path}")
                GLib.idle_add(callback, pixbuf)
                return
            except Exception as e:
                print(f"✗ Cached favicon corrupted for {self._extract_domain(url)}: {e}")
                # Remove corrupted cache file
                try:
                    os.remove(cached_path)
                except OSError:
                    pass

        # If not cached, download it
        print(f"🔄 Starting favicon pixbuf download for {self._extract_domain(url)} (not cached)")
        def on_favicon_path(path):
            if path:
                try:
                    pixbuf = self._load_pixbuf_from_file(path)
                    GLib.idle_add(callback, pixbuf)
                except Exception as e:
                    print(f"Error loading favicon pixbuf from {path}: {e}")
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
                print(f"Converted HTTP to HTTPS for favicon: {url}")
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

            print(f"Extracted domain '{domain}' from URL '{original_url}'")
            return domain if domain else None
        except Exception as e:
            print(f"Error extracting domain from '{url}': {e}")
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
                print(f"Trying favicon URL {i}/{len(favicon_urls)}: {favicon_url}")
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

                print(f"🌐 Attempting to download: {favicon_url}")
                with opener.open(request, timeout=5) as response:
                    print(f"📡 Response status: {response.status}, Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                    if response.status == 200:
                        # Save to cache
                        with open(cache_path, 'wb') as f:
                            f.write(response.read())

                        # Verify it's a valid image
                        if self._is_valid_image(cache_path):
                            # Success! Return immediately without trying other URLs
                            print(f"✓ Successfully downloaded favicon from: {favicon_url} (stopped after {i}/{len(favicon_urls)} attempts)")
                            return cache_path
                        else:
                            print(f"❌ Downloaded file is not a valid image: {favicon_url}")
                            # Remove invalid file and continue to next URL
                            try:
                                os.remove(cache_path)
                            except OSError:
                                pass

            except urllib.error.HTTPError as e:
                # HTTP error (404, 403, etc.)
                print(f"✗ Failed to download from {favicon_url}: HTTP Error {e.code}: {e.reason}")
                continue
            except urllib.error.URLError as e:
                # Network error (timeout, connection refused, etc.)
                print(f"✗ Failed to download from {favicon_url}: Network Error: {e.reason}")
                continue
            except Exception as e:
                # Other errors
                print(f"✗ Failed to download from {favicon_url}: {type(e).__name__}: {e}")
                continue

        # No favicon found after trying all URLs
        print(f"✗ No valid favicon found for domain: {domain} (tried {len(favicon_urls)} URLs)")
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
            print(f"🔍 Validating image: {file_path} (size: {file_size} bytes)")

            if file_size == 0:
                print(f"❌ File is empty: {file_path}")
                return False

            # For ICO files, try a different approach since GdkPixbuf might not support them well
            if file_path.lower().endswith('.ico'):
                # Check if it looks like a valid ICO file by checking the header
                with open(file_path, 'rb') as f:
                    header = f.read(6)
                    if len(header) >= 6 and header[:4] == b'\x00\x00\x01\x00':
                        print(f"✅ Valid ICO file detected")
                        return True

            # Try to load with GdkPixbuf to verify it's a valid image
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(file_path)
            if pixbuf is not None:
                print(f"✅ Valid image: {pixbuf.get_width()}x{pixbuf.get_height()}")
                return True
            else:
                print(f"❌ GdkPixbuf returned None for: {file_path}")
                return False
        except Exception as e:
            print(f"❌ Image validation failed for {file_path}: {e}")
            return False

    def _load_pixbuf_from_file(self, file_path: str):
        """Load a pixbuf from file, with special handling for ICO files."""
        try:
            # First try direct loading
            try:
                return GdkPixbuf.Pixbuf.new_from_file(file_path)
            except Exception as e:
                print(f"Direct pixbuf loading failed: {e}")

            # If it's an ICO file and direct loading failed, try to convert it using PIL
            if file_path.lower().endswith('.ico') and PIL_AVAILABLE:
                print(f"🔄 Attempting ICO to PNG conversion using PIL for: {file_path}")
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
                        print(f"✅ Successfully converted ICO to PNG: {pixbuf.get_width()}x{pixbuf.get_height()}")
                        return pixbuf

                except Exception as e:
                    print(f"PIL ICO conversion failed: {e}")

            # If PIL is not available or conversion failed, try GdkPixbuf scaling methods
            if file_path.lower().endswith('.ico'):
                print(f"🔄 Attempting ICO conversion with GdkPixbuf for: {file_path}")
                # Try to load at a specific size (32x32 is common for favicons)
                try:
                    return GdkPixbuf.Pixbuf.new_from_file_at_scale(file_path, 32, 32, True)
                except Exception as e2:
                    print(f"ICO scaling failed: {e2}")
                    # Try loading at original size
                    try:
                        return GdkPixbuf.Pixbuf.new_from_file_at_size(file_path, 32, 32)
                    except Exception as e3:
                        print(f"ICO size loading failed: {e3}")

            return None
        except Exception as e:
            print(f"Error loading pixbuf from {file_path}: {e}")
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
            print(f"Error creating image from favicon {favicon_path}: {e}")
        
        return None
    
    def clear_cache(self):
        """Clear all cached favicons."""
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except OSError as e:
            print(f"Error clearing favicon cache: {e}")


# Global favicon manager instance
_favicon_manager = None

def get_favicon_manager() -> FaviconManager:
    """Get the global favicon manager instance."""
    global _favicon_manager
    if _favicon_manager is None:
        _favicon_manager = FaviconManager()
    return _favicon_manager
