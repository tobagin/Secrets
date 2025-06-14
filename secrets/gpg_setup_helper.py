"""
GPG Setup Helper for the Secrets application.
Provides utilities to help users set up GPG keys and initialize the password store.
"""

import subprocess
import tempfile
import os
from typing import Tuple, Optional


class GPGSetupHelper:
    """Helper class for GPG setup operations."""
    
    @staticmethod
    def create_gpg_key_batch(name: str, email: str, passphrase: str = "") -> Tuple[bool, str]:
        """
        Create a GPG key using batch mode for automation.
        
        Args:
            name: Full name for the key
            email: Email address for the key
            passphrase: Passphrase for the key (empty for no passphrase)
            
        Returns:
            Tuple of (success, message_or_error)
        """
        # Create a temporary batch file for GPG key generation
        batch_content = f"""
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
"""
        
        if passphrase:
            batch_content += f"Passphrase: {passphrase}\n"
        else:
            batch_content += "%no-protection\n"
            
        batch_content += "%commit\n"
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.batch', delete=False) as f:
                f.write(batch_content)
                batch_file = f.name
            
            # Generate the key
            result = subprocess.run(
                ["gpg", "--batch", "--generate-key", batch_file],
                capture_output=True,
                text=True,
                timeout=120  # GPG key generation can take a while
            )
            
            # Clean up the batch file
            os.unlink(batch_file)
            
            if result.returncode == 0:
                return True, f"GPG key created successfully for {email}"
            else:
                error_msg = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
                return False, f"Failed to create GPG key: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "GPG key generation timed out. This may take a while on slower systems."
        except Exception as e:
            return False, f"Error creating GPG key: {e}"
        finally:
            # Ensure batch file is cleaned up even if an exception occurs
            try:
                if 'batch_file' in locals():
                    os.unlink(batch_file)
            except:
                pass
    
    @staticmethod
    def get_gpg_key_ids() -> Tuple[bool, list]:
        """
        Get a list of available GPG key IDs.
        
        Returns:
            Tuple of (success, list_of_key_info_dicts)
        """
        try:
            result = subprocess.run(
                ["gpg", "--list-secret-keys", "--with-colons"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, []
            
            keys = []
            current_key = None
            
            for line in result.stdout.splitlines():
                fields = line.split(':')
                if fields[0] == 'sec':  # Secret key
                    current_key = {
                        'keyid': fields[4],
                        'creation_date': fields[5],
                        'algorithm': fields[3],
                        'uids': []
                    }
                    keys.append(current_key)
                elif fields[0] == 'uid' and current_key:  # User ID
                    uid = fields[9]
                    current_key['uids'].append(uid)
            
            return True, keys
            
        except Exception as e:
            return False, []
    
    @staticmethod
    def suggest_gpg_setup_steps() -> list:
        """
        Return a list of suggested steps for GPG setup.
        
        Returns:
            List of step descriptions
        """
        return [
            "1. Create a GPG key: gpg --gen-key",
            "2. Follow the prompts to set up your key",
            "3. Use your email address as the key identifier",
            "4. Choose a strong passphrase (or none for testing)",
            "5. Initialize the password store: pass init your-email@example.com",
            "6. Restart the application"
        ]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Simple email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def get_recommended_key_settings() -> dict:
        """Get recommended settings for GPG key creation."""
        return {
            'key_type': 'RSA',
            'key_length': 4096,
            'subkey_type': 'RSA', 
            'subkey_length': 4096,
            'expire_date': '0',  # No expiration
            'usage': 'sign,encrypt,auth'
        }
