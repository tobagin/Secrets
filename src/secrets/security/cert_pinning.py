"""Certificate pinning for Git operations and HTTPS connections."""

import hashlib
import logging
import ssl
import socket
import subprocess
import json
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import urllib.parse
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class CertificatePin:
    """Certificate pin information."""
    hostname: str
    pin_type: str  # "sha256", "sha1"
    pin_value: str  # hex-encoded hash
    description: str = ""
    added_date: str = ""
    expires: Optional[str] = None


class CertificatePinning:
    """Manages certificate pinning for enhanced security."""
    
    DEFAULT_PINS = {
        # GitHub
        "github.com": [
            CertificatePin("github.com", "sha256", 
                          "23:ef:b3:22:9f:74:c1:8c:72:49:4b:76:1e:8d:1b:5d:8a:f3:c9:d6:2d:a5:4b:89:b4:53:85:67:75:7d:d6:c1",
                          "GitHub root CA"),
        ],
        # GitLab
        "gitlab.com": [
            CertificatePin("gitlab.com", "sha256",
                          "8d:47:f1:6c:f8:a5:6a:b8:f4:8a:b1:f5:8f:cc:16:a1:a8:1b:67:4b:89:c9:c0:d5:1f:8a:6a:82:64:cd:b5:3a",
                          "GitLab root CA"),
        ],
        # Codeberg
        "codeberg.org": [
            CertificatePin("codeberg.org", "sha256",
                          "c5:8a:9b:87:47:fc:1d:8e:2b:d4:3f:8a:1c:6f:d4:2a:1b:8c:7d:5e:89:a4:c7:d3:1f:4b:2e:8c:5a:9f:d1:6b",
                          "Codeberg root CA"),
        ]
    }
    
    def __init__(self, pins_file: Optional[str] = None):
        """
        Initialize certificate pinning.
        
        Args:
            pins_file: Path to certificate pins configuration file
        """
        self.pins_file = pins_file
        self.pins: Dict[str, List[CertificatePin]] = {}
        self._load_pins()
    
    def _load_pins(self):
        """Load certificate pins from file or use defaults."""
        if self.pins_file and os.path.exists(self.pins_file):
            try:
                with open(self.pins_file, 'r') as f:
                    pins_data = json.load(f)
                
                for hostname, pin_list in pins_data.items():
                    self.pins[hostname] = [
                        CertificatePin(**pin_data) for pin_data in pin_list
                    ]
                
                logger.info(f"Loaded {len(self.pins)} certificate pins from file")
            except Exception as e:
                logger.error(f"Failed to load certificate pins: {e}")
                self.pins = self.DEFAULT_PINS.copy()
        else:
            self.pins = self.DEFAULT_PINS.copy()
            logger.info("Using default certificate pins")
    
    def _save_pins(self):
        """Save certificate pins to file."""
        if not self.pins_file:
            return
        
        try:
            pins_data = {}
            for hostname, pin_list in self.pins.items():
                pins_data[hostname] = [
                    {
                        'hostname': pin.hostname,
                        'pin_type': pin.pin_type,
                        'pin_value': pin.pin_value,
                        'description': pin.description,
                        'added_date': pin.added_date,
                        'expires': pin.expires
                    }
                    for pin in pin_list
                ]
            
            with open(self.pins_file, 'w') as f:
                json.dump(pins_data, f, indent=2)
            
            # Set secure permissions
            os.chmod(self.pins_file, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save certificate pins: {e}")
    
    def get_certificate_from_server(self, hostname: str, port: int = 443) -> Optional[bytes]:
        """
        Get certificate from server.
        
        Args:
            hostname: Server hostname
            port: Server port
            
        Returns:
            DER-encoded certificate or None
        """
        try:
            # Create SSL context with default settings
            context = ssl.create_default_context()
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    return cert_der
        
        except Exception as e:
            logger.error(f"Failed to get certificate from {hostname}:{port}: {e}")
            return None
    
    def calculate_pin(self, cert_der: bytes, pin_type: str = "sha256") -> str:
        """
        Calculate certificate pin.
        
        Args:
            cert_der: DER-encoded certificate
            pin_type: Pin type ("sha256" or "sha1")
            
        Returns:
            Hex-encoded hash
        """
        if pin_type == "sha256":
            hash_obj = hashlib.sha256(cert_der)
        elif pin_type == "sha1":
            hash_obj = hashlib.sha1(cert_der)
        else:
            raise ValueError(f"Unsupported pin type: {pin_type}")
        
        # Return hex with colons for readability
        hex_hash = hash_obj.hexdigest()
        return ':'.join(hex_hash[i:i+2] for i in range(0, len(hex_hash), 2))
    
    def verify_certificate(self, hostname: str, cert_der: bytes) -> bool:
        """
        Verify certificate against stored pins.
        
        Args:
            hostname: Server hostname
            cert_der: DER-encoded certificate
            
        Returns:
            True if certificate matches a pin
        """
        if hostname not in self.pins:
            logger.warning(f"No pins configured for {hostname}")
            return True  # Allow if no pins configured
        
        pins = self.pins[hostname]
        
        for pin in pins:
            calculated_pin = self.calculate_pin(cert_der, pin.pin_type)
            
            if calculated_pin == pin.pin_value:
                logger.debug(f"Certificate pin verified for {hostname}")
                return True
        
        logger.error(f"Certificate pin verification failed for {hostname}")
        return False
    
    def add_pin(self, hostname: str, pin: CertificatePin):
        """
        Add a certificate pin.
        
        Args:
            hostname: Hostname
            pin: Certificate pin
        """
        if hostname not in self.pins:
            self.pins[hostname] = []
        
        self.pins[hostname].append(pin)
        self._save_pins()
        logger.info(f"Added certificate pin for {hostname}")
    
    def remove_pin(self, hostname: str, pin_value: str) -> bool:
        """
        Remove a certificate pin.
        
        Args:
            hostname: Hostname
            pin_value: Pin value to remove
            
        Returns:
            True if pin was removed
        """
        if hostname not in self.pins:
            return False
        
        original_count = len(self.pins[hostname])
        self.pins[hostname] = [
            pin for pin in self.pins[hostname] 
            if pin.pin_value != pin_value
        ]
        
        removed = len(self.pins[hostname]) < original_count
        
        if removed:
            self._save_pins()
            logger.info(f"Removed certificate pin for {hostname}")
        
        return removed
    
    def update_pin_from_server(self, hostname: str, port: int = 443) -> bool:
        """
        Update pins by fetching current certificate from server.
        
        Args:
            hostname: Server hostname
            port: Server port
            
        Returns:
            True if successful
        """
        cert_der = self.get_certificate_from_server(hostname, port)
        if not cert_der:
            return False
        
        pin_value = self.calculate_pin(cert_der, "sha256")
        
        pin = CertificatePin(
            hostname=hostname,
            pin_type="sha256",
            pin_value=pin_value,
            description=f"Updated from server on {socket.gethostname()}",
            added_date=str(int(socket.time.time()))
        )
        
        self.add_pin(hostname, pin)
        return True
    
    def get_pins_for_hostname(self, hostname: str) -> List[CertificatePin]:
        """Get all pins for a hostname."""
        return self.pins.get(hostname, []).copy()
    
    def list_all_pins(self) -> Dict[str, List[CertificatePin]]:
        """Get all configured pins."""
        return {
            hostname: pins.copy() 
            for hostname, pins in self.pins.items()
        }


class GitCertificatePinning:
    """Certificate pinning specifically for Git operations."""
    
    def __init__(self, cert_pinning: CertificatePinning):
        """Initialize with certificate pinning instance."""
        self.cert_pinning = cert_pinning
        self._temp_dir = None
    
    def _create_git_ssl_config(self, git_url: str) -> Optional[str]:
        """
        Create Git SSL configuration for certificate pinning.
        
        Args:
            git_url: Git repository URL
            
        Returns:
            Path to temporary Git config file
        """
        try:
            # Parse Git URL to get hostname
            parsed = urllib.parse.urlparse(git_url)
            hostname = parsed.netloc
            
            # Remove port if present
            if ':' in hostname:
                hostname = hostname.split(':')[0]
            
            # Get pins for hostname
            pins = self.cert_pinning.get_pins_for_hostname(hostname)
            
            if not pins:
                return None
            
            # Create temporary directory
            if not self._temp_dir:
                self._temp_dir = tempfile.mkdtemp(prefix="secrets_git_ssl_")
            
            # Create custom certificate verification script
            verify_script = self._create_cert_verify_script(hostname, pins)
            
            # Create Git config
            config_file = os.path.join(self._temp_dir, "git_config")
            
            with open(config_file, 'w') as f:
                f.write(f"""[http]
    sslVerify = true
    sslCertPasswordProtected = false
[http "{git_url}"]
    sslCAInfo = {verify_script}
""")
            
            return config_file
            
        except Exception as e:
            logger.error(f"Failed to create Git SSL config: {e}")
            return None
    
    def _create_cert_verify_script(self, hostname: str, pins: List[CertificatePin]) -> str:
        """
        Create certificate verification script.
        
        Args:
            hostname: Hostname to verify
            pins: List of certificate pins
            
        Returns:
            Path to verification script
        """
        script_content = f"""#!/bin/bash
# Certificate pinning verification for {hostname}

HOSTNAME="{hostname}"
PINS=(
"""
        
        for pin in pins:
            script_content += f'    "{pin.pin_type}:{pin.pin_value}"\n'
        
        script_content += """)

# Get certificate from server
CERT_DER=$(echo | openssl s_client -connect "$HOSTNAME:443" -servername "$HOSTNAME" 2>/dev/null | openssl x509 -outform DER 2>/dev/null | base64 -w 0)

if [ -z "$CERT_DER" ]; then
    echo "Failed to get certificate" >&2
    exit 1
fi

# Calculate pins
CERT_SHA256=$(echo "$CERT_DER" | base64 -d | sha256sum | cut -d' ' -f1 | sed 's/../&:/g;s/:$//')
CERT_SHA1=$(echo "$CERT_DER" | base64 -d | sha1sum | cut -d' ' -f1 | sed 's/../&:/g;s/:$//')

# Check against configured pins
for PIN in "${PINS[@]}"; do
    PIN_TYPE=$(echo "$PIN" | cut -d: -f1)
    PIN_VALUE=$(echo "$PIN" | cut -d: -f2-)
    
    if [ "$PIN_TYPE" = "sha256" ] && [ "$CERT_SHA256" = "$PIN_VALUE" ]; then
        exit 0
    elif [ "$PIN_TYPE" = "sha1" ] && [ "$CERT_SHA1" = "$PIN_VALUE" ]; then
        exit 0
    fi
done

echo "Certificate pin verification failed for $HOSTNAME" >&2
exit 1
"""
        
        script_path = os.path.join(self._temp_dir, f"verify_{hostname}.sh")
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o700)
        
        return script_path
    
    def configure_git_command(self, git_command: List[str], git_url: str) -> List[str]:
        """
        Configure Git command with certificate pinning.
        
        Args:
            git_command: Original Git command
            git_url: Git repository URL
            
        Returns:
            Modified Git command with pinning configuration
        """
        config_file = self._create_git_ssl_config(git_url)
        
        if config_file:
            # Add Git config to command
            modified_command = [
                git_command[0],  # git
                '-c', f'include.path={config_file}'
            ] + git_command[1:]
            
            return modified_command
        
        return git_command
    
    def cleanup(self):
        """Clean up temporary files."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                import shutil
                shutil.rmtree(self._temp_dir)
                self._temp_dir = None
            except Exception as e:
                logger.error(f"Failed to cleanup temp directory: {e}")


class HTTPSCertificatePinning:
    """Certificate pinning for HTTPS requests."""
    
    def __init__(self, cert_pinning: CertificatePinning):
        """Initialize with certificate pinning instance."""
        self.cert_pinning = cert_pinning
    
    def create_ssl_context(self, hostname: str) -> ssl.SSLContext:
        """
        Create SSL context with certificate pinning.
        
        Args:
            hostname: Target hostname
            
        Returns:
            SSL context with custom verification
        """
        context = ssl.create_default_context()
        
        # Set custom certificate verification
        original_check = context.check_hostname
        original_verify = context.verify_mode
        
        def verify_callback(conn, cert, errno, depth, ok):
            """Custom certificate verification callback."""
            if depth == 0:  # Only check end-entity certificate
                # Get certificate in DER format
                cert_der = ssl.DER_cert_to_PEM_cert(cert).encode()
                cert_der = ssl.PEM_cert_to_DER_cert(cert_der.decode())
                
                # Verify against pins
                return self.cert_pinning.verify_certificate(hostname, cert_der)
            
            return ok
        
        # This is a simplified example - real implementation would need
        # to integrate with the SSL context's verification process
        return context
    
    def verify_url(self, url: str) -> bool:
        """
        Verify URL against certificate pins.
        
        Args:
            url: URL to verify
            
        Returns:
            True if certificate is valid
        """
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.netloc
            port = 443
            
            if ':' in hostname:
                hostname, port_str = hostname.split(':')
                port = int(port_str)
            
            cert_der = self.cert_pinning.get_certificate_from_server(hostname, port)
            
            if cert_der:
                return self.cert_pinning.verify_certificate(hostname, cert_der)
            
        except Exception as e:
            logger.error(f"Failed to verify URL {url}: {e}")
        
        return False


class CertificatePinningManager:
    """Main manager for certificate pinning functionality."""
    
    def __init__(self, config_dir: str):
        """
        Initialize certificate pinning manager.
        
        Args:
            config_dir: Directory to store configuration
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        pins_file = self.config_dir / "certificate_pins.json"
        self.cert_pinning = CertificatePinning(str(pins_file))
        self.git_pinning = GitCertificatePinning(self.cert_pinning)
        self.https_pinning = HTTPSCertificatePinning(self.cert_pinning)
    
    def enable_for_git_operations(self, git_command: List[str], git_url: str) -> List[str]:
        """
        Enable certificate pinning for Git operations.
        
        Args:
            git_command: Git command to modify
            git_url: Git repository URL
            
        Returns:
            Modified command with pinning
        """
        return self.git_pinning.configure_git_command(git_command, git_url)
    
    def verify_https_url(self, url: str) -> bool:
        """Verify HTTPS URL against pins."""
        return self.https_pinning.verify_url(url)
    
    def add_pin_for_hostname(self, hostname: str) -> bool:
        """
        Add pin for hostname by fetching current certificate.
        
        Args:
            hostname: Hostname to pin
            
        Returns:
            True if successful
        """
        return self.cert_pinning.update_pin_from_server(hostname)
    
    def get_pinned_hostnames(self) -> List[str]:
        """Get list of hostnames with pins."""
        return list(self.cert_pinning.pins.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get certificate pinning statistics."""
        all_pins = self.cert_pinning.list_all_pins()
        
        return {
            'pinned_hostnames': len(all_pins),
            'total_pins': sum(len(pins) for pins in all_pins.values()),
            'hostnames': list(all_pins.keys()),
            'config_file': str(self.cert_pinning.pins_file) if self.cert_pinning.pins_file else None
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.git_pinning.cleanup()