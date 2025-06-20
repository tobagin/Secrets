"""
System Setup Helper for the Secrets application.
Detects the operating system and package manager, and provides installation commands
for pass and GPG across different Linux distributions.
"""

import subprocess
import os
import platform
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass


@dataclass
class DistroInfo:
    """Information about a Linux distribution."""
    name: str
    version: str
    id: str
    package_manager: str
    install_command: str
    pass_package: str
    gpg_package: str
    update_command: Optional[str] = None


class SystemSetupHelper:
    """Helper class for system detection and package installation."""
    
    # Known distributions and their package information
    DISTRO_MAP = {
        'ubuntu': DistroInfo(
            name='Ubuntu', version='', id='ubuntu',
            package_manager='apt', install_command='sudo apt install -y',
            pass_package='pass', gpg_package='gnupg',
            update_command='sudo apt update'
        ),
        'debian': DistroInfo(
            name='Debian', version='', id='debian',
            package_manager='apt', install_command='sudo apt install -y',
            pass_package='pass', gpg_package='gnupg',
            update_command='sudo apt update'
        ),
        'fedora': DistroInfo(
            name='Fedora', version='', id='fedora',
            package_manager='dnf', install_command='sudo dnf install -y',
            pass_package='pass', gpg_package='gnupg2',
            update_command='sudo dnf check-update'
        ),
        'centos': DistroInfo(
            name='CentOS', version='', id='centos',
            package_manager='yum', install_command='sudo yum install -y',
            pass_package='pass', gpg_package='gnupg2',
            update_command='sudo yum check-update'
        ),
        'rhel': DistroInfo(
            name='Red Hat Enterprise Linux', version='', id='rhel',
            package_manager='yum', install_command='sudo yum install -y',
            pass_package='pass', gpg_package='gnupg2',
            update_command='sudo yum check-update'
        ),
        'opensuse': DistroInfo(
            name='openSUSE', version='', id='opensuse',
            package_manager='zypper', install_command='sudo zypper install -y',
            pass_package='password-store', gpg_package='gpg2',
            update_command='sudo zypper refresh'
        ),
        'arch': DistroInfo(
            name='Arch Linux', version='', id='arch',
            package_manager='pacman', install_command='sudo pacman -S --noconfirm',
            pass_package='pass', gpg_package='gnupg',
            update_command='sudo pacman -Sy'
        ),
        'manjaro': DistroInfo(
            name='Manjaro', version='', id='manjaro',
            package_manager='pacman', install_command='sudo pacman -S --noconfirm',
            pass_package='pass', gpg_package='gnupg',
            update_command='sudo pacman -Sy'
        ),
        'alpine': DistroInfo(
            name='Alpine Linux', version='', id='alpine',
            package_manager='apk', install_command='sudo apk add',
            pass_package='pass', gpg_package='gnupg',
            update_command='sudo apk update'
        ),
    }
    
    @staticmethod
    def detect_distribution() -> Optional[DistroInfo]:
        """
        Detect the current Linux distribution and return its information.
        
        Returns:
            DistroInfo object if detected, None if unknown
        """
        try:
            # Try to read /etc/os-release first (most modern distributions)
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    os_release = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_release[key] = value.strip('"')
                
                distro_id = os_release.get('ID', '').lower()
                distro_name = os_release.get('NAME', '')
                distro_version = os_release.get('VERSION', '')
                
                # Check for known distributions
                if distro_id in SystemSetupHelper.DISTRO_MAP:
                    distro_info = SystemSetupHelper.DISTRO_MAP[distro_id]
                    distro_info.version = distro_version
                    return distro_info
                
                # Check for derivatives
                if 'ubuntu' in distro_id or 'ubuntu' in distro_name.lower():
                    distro_info = SystemSetupHelper.DISTRO_MAP['ubuntu']
                    distro_info.version = distro_version
                    return distro_info
                
                if 'debian' in distro_id or 'debian' in distro_name.lower():
                    distro_info = SystemSetupHelper.DISTRO_MAP['debian']
                    distro_info.version = distro_version
                    return distro_info
            
            # Fallback: try reading other distribution files
            try:
                # Try reading /etc/lsb-release for Ubuntu derivatives
                if os.path.exists('/etc/lsb-release'):
                    with open('/etc/lsb-release', 'r') as f:
                        lsb_content = f.read().lower()
                        if 'ubuntu' in lsb_content:
                            return SystemSetupHelper.DISTRO_MAP['ubuntu']
                        elif 'debian' in lsb_content:
                            return SystemSetupHelper.DISTRO_MAP['debian']
            except:
                pass
            
            # Last resort: check for specific files
            if os.path.exists('/etc/debian_version'):
                return SystemSetupHelper.DISTRO_MAP['debian']
            elif os.path.exists('/etc/redhat-release'):
                return SystemSetupHelper.DISTRO_MAP['fedora']
            elif os.path.exists('/etc/arch-release'):
                return SystemSetupHelper.DISTRO_MAP['arch']
            
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def check_package_installed(package_name: str, package_manager: str) -> bool:
        """
        Check if a package is installed using the appropriate package manager.
        
        Args:
            package_name: Name of the package to check
            package_manager: Package manager to use (apt, dnf, pacman, etc.)
            
        Returns:
            True if package is installed, False otherwise
        """
        try:
            if package_manager == 'apt':
                result = subprocess.run(['dpkg', '-l', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0 and 'ii' in result.stdout
            
            elif package_manager == 'dnf':
                result = subprocess.run(['rpm', '-q', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            
            elif package_manager == 'yum':
                result = subprocess.run(['rpm', '-q', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            
            elif package_manager == 'pacman':
                result = subprocess.run(['pacman', '-Q', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            
            elif package_manager == 'zypper':
                result = subprocess.run(['rpm', '-q', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            
            elif package_manager == 'apk':
                result = subprocess.run(['apk', 'info', '-e', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            
        except Exception:
            pass
        
        return False
    
    @staticmethod
    def check_command_available(command: str) -> bool:
        """Check if a command is available and working."""
        try:
            # Test the actual command instead of just checking PATH
            if command == 'pass':
                result = subprocess.run(['pass', 'help'],
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            elif command == 'gpg':
                result = subprocess.run(['gpg', '--version'],
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            else:
                # For other commands, use which
                result = subprocess.run(['which', command],
                                      capture_output=True, text=True)
                return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_installation_commands(distro_info: DistroInfo) -> Dict[str, str]:
        """
        Get installation commands for pass and GPG on the given distribution.
        
        Args:
            distro_info: Information about the distribution
            
        Returns:
            Dictionary with installation commands
        """
        commands = {}
        
        # Update package database if needed
        if distro_info.update_command:
            commands['update'] = distro_info.update_command
        
        # Install both packages together
        commands['install_both'] = f"{distro_info.install_command} {distro_info.pass_package} {distro_info.gpg_package}"
        
        # Individual package installation
        commands['install_pass'] = f"{distro_info.install_command} {distro_info.pass_package}"
        commands['install_gpg'] = f"{distro_info.install_command} {distro_info.gpg_package}"
        
        return commands
    
    @staticmethod
    def get_system_status() -> Dict[str, any]:
        """
        Get comprehensive system status for pass and GPG setup.
        
        Returns:
            Dictionary with system information and status
        """
        status = {
            'os': platform.system(),
            'distro': None,
            'distro_supported': False,
            'pass_installed': False,
            'gpg_installed': False,
            'can_install': False,
            'installation_commands': {},
            'manual_instructions': []
        }
        
        # Detect distribution
        if status['os'] == 'Linux':
            distro_info = SystemSetupHelper.detect_distribution()
            if distro_info:
                status['distro'] = distro_info
                status['distro_supported'] = True
                status['can_install'] = True
                status['installation_commands'] = SystemSetupHelper.get_installation_commands(distro_info)
                
                # Check if packages are already installed
                status['pass_installed'] = SystemSetupHelper.check_package_installed(
                    distro_info.pass_package, distro_info.package_manager
                )
                status['gpg_installed'] = SystemSetupHelper.check_package_installed(
                    distro_info.gpg_package, distro_info.package_manager
                )
        
        # Check if commands are available (regardless of package manager detection)
        if not status['pass_installed']:
            status['pass_installed'] = SystemSetupHelper.check_command_available('pass')
        if not status['gpg_installed']:
            status['gpg_installed'] = SystemSetupHelper.check_command_available('gpg')

        # Special handling for Flatpak environment - disable installation if in Flatpak
        is_flatpak = os.path.exists('/.flatpak-info') or 'FLATPAK_ID' in os.environ
        if is_flatpak:
            status['can_install'] = False  # No need to install in Flatpak
        
        # Generate manual instructions for unsupported systems
        if not status['distro_supported']:
            status['manual_instructions'] = [
                "Your distribution is not automatically supported.",
                "Please install the following packages manually:",
                "• pass (password-store) - The standard Unix password manager",
                "• gnupg (gpg) - GNU Privacy Guard for encryption",
                "",
                "Common installation methods:",
                "• Use your distribution's package manager",
                "• Compile from source",
                "• Use universal package managers like Snap or Flatpak"
            ]
        
        return status

    @staticmethod
    def run_installation_command(command: str, timeout: int = 300) -> Dict[str, any]:
        """
        Run an installation command with proper error handling.

        Args:
            command: The command to run
            timeout: Timeout in seconds (default: 5 minutes)

        Returns:
            Dictionary with success status and result/error information
        """
        try:
            # Split command into parts for subprocess
            cmd_parts = command.split()

            # Run the command
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise exception on non-zero exit
            )

            # Check for success based on return code
            # Many package managers output informational messages to stderr even on success
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': result.stderr,  # Keep stderr for informational purposes
                    'return_code': result.returncode
                }
            else:
                # For some commands like 'yum check-update', non-zero exit codes are normal
                # when updates are available, so we need to be more intelligent about errors
                error_message = result.stderr or result.stdout or f"Command failed with exit code {result.returncode}"

                # Special handling for specific package managers
                cmd_parts = command.split()
                if len(cmd_parts) > 0:
                    # For sudo commands, get the actual package manager command
                    pkg_manager_cmd = cmd_parts[1] if cmd_parts[0] == 'sudo' and len(cmd_parts) > 1 else cmd_parts[0]
                    pkg_manager = pkg_manager_cmd.split('/')[-1]  # Get command name without path

                    # yum/dnf check-update returns 100 when updates are available (not an error)
                    if ('yum' in pkg_manager or 'dnf' in pkg_manager) and 'check-update' in command and result.returncode == 100:
                        return {
                            'success': True,
                            'output': result.stdout,
                            'error': result.stderr,
                            'return_code': result.returncode
                        }

                    # zypper refresh might return non-zero but still succeed
                    if 'zypper' in pkg_manager and 'refresh' in command:
                        # Check if the output indicates success
                        combined_output = (result.stdout + result.stderr).lower()
                        if 'repositories loaded' in combined_output or 'repository' in combined_output:
                            return {
                                'success': True,
                                'output': result.stdout,
                                'error': result.stderr,
                                'return_code': result.returncode
                            }

                return {
                    'success': False,
                    'output': result.stdout,
                    'error': error_message,
                    'return_code': result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f"Command timed out after {timeout} seconds",
                'return_code': -1
            }
        except FileNotFoundError:
            return {
                'success': False,
                'output': '',
                'error': f"Command not found: {cmd_parts[0] if cmd_parts else command}",
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f"Unexpected error: {str(e)}",
                'return_code': -1
            }
