"""
GPG Setup Helper for the Secrets application.
Provides utilities to help users set up GPG keys and initialize the password store.
"""

import subprocess
import tempfile
import os
import shutil
from typing import Tuple, Optional, Dict


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
            
            # Generate the key with proper environment setup
            env = GPGSetupHelper.setup_gpg_environment()
            result = subprocess.run(
                ["gpg", "--batch", "--generate-key", batch_file],
                capture_output=True,
                text=True,
                timeout=120,  # GPG key generation can take a while
                env=env
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
            env = GPGSetupHelper.setup_gpg_environment()
            result = subprocess.run(
                ["gpg", "--list-secret-keys", "--with-colons"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
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

    @staticmethod
    def setup_gpg_environment() -> Dict[str, str]:
        """
        Set up GPG environment variables for proper operation in Flatpak.

        Returns:
            Dictionary of environment variables to set
        """
        env = os.environ.copy()

        # Set GPG_TTY for proper terminal handling
        # In Flatpak, we need to ensure GPG can communicate properly
        if 'GPG_TTY' not in env:
            try:
                # Try to get TTY, but don't fail if not available
                result = subprocess.run(['tty'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    env['GPG_TTY'] = result.stdout.strip()
                else:
                    # Fallback for GUI environments
                    env['GPG_TTY'] = '/dev/pts/0'
            except:
                env['GPG_TTY'] = '/dev/pts/0'

        # Ensure GPG agent is used
        env['GPG_AGENT_INFO'] = env.get('GPG_AGENT_INFO', '')

        # Set pinentry program for GUI
        # This helps ensure password prompts work in Flatpak
        pinentry_programs = [
            '/app/bin/pinentry-gtk2',
            '/usr/bin/pinentry-gtk2',
            '/app/bin/pinentry-qt5',
            '/usr/bin/pinentry-qt5',
            '/app/bin/pinentry-qt',
            '/usr/bin/pinentry-qt',
            '/app/bin/pinentry-gnome3',
            '/usr/bin/pinentry-gnome3',
            '/app/bin/pinentry',
            '/usr/bin/pinentry'
        ]

        for pinentry in pinentry_programs:
            if os.path.exists(pinentry):
                env['PINENTRY_USER_DATA'] = pinentry
                break

        # Set GPG home directory if not set
        if 'GNUPGHOME' not in env:
            env['GNUPGHOME'] = os.path.expanduser('~/.gnupg')

        # Ensure the GPG home directory exists
        gnupg_home = env['GNUPGHOME']
        if not os.path.exists(gnupg_home):
            os.makedirs(gnupg_home, mode=0o700, exist_ok=True)

        return env

    @staticmethod
    def configure_gpg_agent():
        """
        Configure GPG agent for GUI operation in Flatpak.
        """
        gnupg_home = os.path.expanduser('~/.gnupg')
        gpg_agent_conf = os.path.join(gnupg_home, 'gpg-agent.conf')

        # Create .gnupg directory if it doesn't exist
        if not os.path.exists(gnupg_home):
            os.makedirs(gnupg_home, mode=0o700, exist_ok=True)

        # Configure gpg-agent.conf for GUI pinentry
        config_lines = []

        # Find available pinentry program
        pinentry_programs = [
            ('/app/bin/pinentry-gtk2', 'pinentry-gtk2'),
            ('/usr/bin/pinentry-gtk2', 'pinentry-gtk2'),
            ('/app/bin/pinentry-qt5', 'pinentry-qt5'),
            ('/usr/bin/pinentry-qt5', 'pinentry-qt5'),
            ('/app/bin/pinentry-qt', 'pinentry-qt'),
            ('/usr/bin/pinentry-qt', 'pinentry-qt'),
            ('/app/bin/pinentry-gnome3', 'pinentry-gnome3'),
            ('/usr/bin/pinentry-gnome3', 'pinentry-gnome3'),
            ('/app/bin/pinentry', 'pinentry'),
            ('/usr/bin/pinentry', 'pinentry')
        ]

        pinentry_program = None
        for path, name in pinentry_programs:
            if os.path.exists(path):
                pinentry_program = path
                break

        if pinentry_program:
            config_lines.append(f'pinentry-program {pinentry_program}')

        # Add other useful settings
        config_lines.extend([
            'default-cache-ttl 28800',  # 8 hours
            'max-cache-ttl 86400',      # 24 hours
            'allow-loopback-pinentry',
            'enable-ssh-support'
        ])

        # Write configuration
        try:
            with open(gpg_agent_conf, 'w') as f:
                f.write('\n'.join(config_lines) + '\n')

            # Set proper permissions
            os.chmod(gpg_agent_conf, 0o600)

            # Restart GPG agent to apply new configuration
            try:
                subprocess.run(['gpgconf', '--kill', 'gpg-agent'],
                             capture_output=True, timeout=5)
            except:
                pass  # Ignore errors, agent will restart automatically

        except Exception as e:
            print(f"Warning: Could not configure GPG agent: {e}")

    @staticmethod
    def test_gpg_operation() -> Tuple[bool, str]:
        """
        Test if GPG operations work properly.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Set up environment
            env = GPGSetupHelper.setup_gpg_environment()

            # Test GPG version
            result = subprocess.run(
                ['gpg', '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )

            if result.returncode != 0:
                return False, "GPG command failed"

            # Test listing keys
            result = subprocess.run(
                ['gpg', '--batch', '--list-secret-keys', '--with-colons'],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )

            if result.returncode != 0:
                return False, "Could not list GPG keys"

            if not result.stdout.strip():
                return False, "No GPG secret keys found"

            return True, "GPG operations working correctly"

        except subprocess.TimeoutExpired:
            return False, "GPG operation timed out"
        except Exception as e:
            return False, f"GPG test failed: {e}"
