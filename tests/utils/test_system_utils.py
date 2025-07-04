"""Unit tests for system utilities."""

import os
import subprocess
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path

import pytest

from src.secrets.utils.system_utils import SystemSetupHelper


class TestSystemSetupHelper:
    """Test cases for SystemSetupHelper."""
    
    @pytest.fixture
    def system_helper(self):
        """Create a SystemSetupHelper instance."""
        return SystemSetupHelper()
    
    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock subprocess.run for system commands."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            yield mock_run
    
    def test_detect_distribution_ubuntu(self, system_helper):
        """Test Ubuntu distribution detection."""
        mock_content = '''PRETTY_NAME="Ubuntu 22.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.3 LTS (Jammy Jellyfish)"
VERSION_CODENAME=jammy
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
'''
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            distro = system_helper.detect_distribution()
            
            assert distro["id"] == "ubuntu"
            assert distro["name"] == "Ubuntu"
            assert distro["version"] == "22.04.3 LTS (Jammy Jellyfish)"
            assert distro["package_manager"] == "apt"
    
    def test_detect_distribution_fedora(self, system_helper):
        """Test Fedora distribution detection."""
        mock_content = '''NAME="Fedora Linux"
VERSION="38 (Workstation Edition)"
ID=fedora
VERSION_ID=38
VERSION_CODENAME=""
PLATFORM_ID="platform:f38"
PRETTY_NAME="Fedora Linux 38 (Workstation Edition)"
'''
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            distro = system_helper.detect_distribution()
            
            assert distro["id"] == "fedora"
            assert distro["name"] == "Fedora Linux"
            assert distro["package_manager"] == "dnf"
    
    def test_detect_distribution_arch(self, system_helper):
        """Test Arch Linux distribution detection."""
        mock_content = '''NAME="Arch Linux"
PRETTY_NAME="Arch Linux"
ID=arch
BUILD_ID=rolling
ANSI_COLOR="38;2;23;147;209"
HOME_URL="https://archlinux.org/"
DOCUMENTATION_URL="https://wiki.archlinux.org/"
SUPPORT_URL="https://bbs.archlinux.org/"
BUG_REPORT_URL="https://bugs.archlinux.org/"
'''
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            distro = system_helper.detect_distribution()
            
            assert distro["id"] == "arch"
            assert distro["name"] == "Arch Linux"
            assert distro["package_manager"] == "pacman"
    
    def test_detect_distribution_file_not_found(self, system_helper):
        """Test distribution detection when os-release file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            distro = system_helper.detect_distribution()
            
            assert distro["id"] == "unknown"
            assert distro["name"] == "Unknown"
            assert distro["package_manager"] == "unknown"
    
    def test_detect_distribution_permission_error(self, system_helper):
        """Test distribution detection with permission error."""
        with patch('builtins.open', side_effect=PermissionError()):
            distro = system_helper.detect_distribution()
            
            assert distro["id"] == "unknown"
    
    def test_check_package_installed_apt_installed(self, system_helper, mock_subprocess_run):
        """Test package check with apt when package is installed."""
        mock_subprocess_run.return_value.returncode = 0
        
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "apt"}
            
            is_installed = system_helper.check_package_installed("git")
            
            assert is_installed
            mock_subprocess_run.assert_called_with(
                ["dpkg", "-l", "git"],
                capture_output=True,
                text=True,
                timeout=10
            )
    
    def test_check_package_installed_apt_not_installed(self, system_helper, mock_subprocess_run):
        """Test package check with apt when package is not installed."""
        mock_subprocess_run.return_value.returncode = 1
        
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "apt"}
            
            is_installed = system_helper.check_package_installed("nonexistent")
            
            assert not is_installed
    
    def test_check_package_installed_dnf(self, system_helper, mock_subprocess_run):
        """Test package check with dnf."""
        mock_subprocess_run.return_value.returncode = 0
        
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "dnf"}
            
            is_installed = system_helper.check_package_installed("git")
            
            assert is_installed
            mock_subprocess_run.assert_called_with(
                ["rpm", "-q", "git"],
                capture_output=True,
                text=True,
                timeout=10
            )
    
    def test_check_package_installed_pacman(self, system_helper, mock_subprocess_run):
        """Test package check with pacman."""
        mock_subprocess_run.return_value.returncode = 0
        
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "pacman"}
            
            is_installed = system_helper.check_package_installed("git")
            
            assert is_installed
            mock_subprocess_run.assert_called_with(
                ["pacman", "-Q", "git"],
                capture_output=True,
                text=True,
                timeout=10
            )
    
    def test_check_package_installed_unknown_manager(self, system_helper):
        """Test package check with unknown package manager."""
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "unknown"}
            
            is_installed = system_helper.check_package_installed("git")
            
            assert not is_installed
    
    def test_get_installation_commands_apt(self, system_helper):
        """Test installation commands for apt."""
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "apt"}
            
            commands = system_helper.get_installation_commands(["git", "pass"])
            
            expected = [
                "sudo apt update",
                "sudo apt install -y git pass"
            ]
            assert commands == expected
    
    def test_get_installation_commands_dnf(self, system_helper):
        """Test installation commands for dnf."""
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "dnf"}
            
            commands = system_helper.get_installation_commands(["git", "pass"])
            
            expected = [
                "sudo dnf install -y git pass"
            ]
            assert commands == expected
    
    def test_get_installation_commands_pacman(self, system_helper):
        """Test installation commands for pacman."""
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "pacman"}
            
            commands = system_helper.get_installation_commands(["git", "pass"])
            
            expected = [
                "sudo pacman -S --noconfirm git pass"
            ]
            assert commands == expected
    
    def test_get_installation_commands_unknown_manager(self, system_helper):
        """Test installation commands for unknown package manager."""
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {"package_manager": "unknown"}
            
            commands = system_helper.get_installation_commands(["git", "pass"])
            
            assert commands == []
    
    def test_get_system_status_complete(self, system_helper):
        """Test complete system status check."""
        with patch.object(system_helper, 'detect_distribution') as mock_detect:
            mock_detect.return_value = {
                "id": "ubuntu",
                "name": "Ubuntu",
                "version": "22.04 LTS",
                "package_manager": "apt"
            }
            
            with patch.object(system_helper, 'check_package_installed') as mock_check:
                mock_check.side_effect = lambda pkg: pkg in ["git", "pass"]
                
                status = system_helper.get_system_status()
                
                assert status["distribution"]["id"] == "ubuntu"
                assert status["packages"]["git"]
                assert status["packages"]["pass"]
                assert not status["packages"]["tree"]
    
    def test_run_installation_command_success(self, system_helper, mock_subprocess_run):
        """Test successful installation command execution."""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Package installed successfully"
        
        success, output = system_helper.run_installation_command("sudo apt install git")
        
        assert success
        assert "Package installed successfully" in output
        mock_subprocess_run.assert_called_with(
            ["sudo", "apt", "install", "git"],
            capture_output=True,
            text=True,
            timeout=300
        )
    
    def test_run_installation_command_failure(self, system_helper, mock_subprocess_run):
        """Test failed installation command execution."""
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "Package not found"
        
        success, output = system_helper.run_installation_command("sudo apt install nonexistent")
        
        assert not success
        assert "Package not found" in output
    
    def test_run_installation_command_timeout(self, system_helper, mock_subprocess_run):
        """Test installation command timeout."""
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("sudo", 300)
        
        success, output = system_helper.run_installation_command("sudo apt install git")
        
        assert not success
        assert "Installation command timed out" in output
    
    def test_run_installation_command_permission_error(self, system_helper, mock_subprocess_run):
        """Test installation command permission error."""
        mock_subprocess_run.side_effect = PermissionError("Permission denied")
        
        success, output = system_helper.run_installation_command("sudo apt install git")
        
        assert not success
        assert "Permission denied" in output
    
    def test_get_package_manager_map(self, system_helper):
        """Test package manager mapping."""
        mapping = system_helper._get_package_manager_map()
        
        assert mapping["ubuntu"] == "apt"
        assert mapping["debian"] == "apt"
        assert mapping["fedora"] == "dnf"
        assert mapping["rhel"] == "dnf"
        assert mapping["centos"] == "dnf"
        assert mapping["arch"] == "pacman"
        assert mapping["manjaro"] == "pacman"
        assert mapping["opensuse"] == "zypper"
        assert mapping["alpine"] == "apk"
    
    def test_parse_os_release_content(self, system_helper):
        """Test parsing of os-release content."""
        content = '''NAME="Test Distribution"
VERSION="1.0"
ID=test
VERSION_ID="1.0"
PRETTY_NAME="Test Distribution 1.0"
'''
        
        result = system_helper._parse_os_release_content(content)
        
        assert result["NAME"] == "Test Distribution"
        assert result["VERSION"] == "1.0"
        assert result["ID"] == "test"
        assert result["VERSION_ID"] == "1.0"
        assert result["PRETTY_NAME"] == "Test Distribution 1.0"
    
    def test_parse_os_release_content_quoted_values(self, system_helper):
        """Test parsing of os-release content with quoted values."""
        content = '''NAME="Test Distribution"
VERSION='1.0'
ID=test
DESCRIPTION="A test distribution"
'''
        
        result = system_helper._parse_os_release_content(content)
        
        assert result["NAME"] == "Test Distribution"
        assert result["VERSION"] == "1.0"
        assert result["ID"] == "test"
        assert result["DESCRIPTION"] == "A test distribution"
    
    def test_is_flatpak_environment(self, system_helper):
        """Test Flatpak environment detection."""
        # Test with Flatpak environment
        with patch.dict(os.environ, {"FLATPAK_ID": "org.example.app"}):
            assert system_helper.is_flatpak_environment()
        
        # Test without Flatpak environment
        with patch.dict(os.environ, {}, clear=True):
            assert not system_helper.is_flatpak_environment()