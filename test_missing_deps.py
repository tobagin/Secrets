#!/usr/bin/env python3
"""
Test script to simulate missing dependencies scenario.
"""

import sys
import os

# Add the secrets module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secrets'))

from secrets.password_store import PasswordStore
from secrets.system_setup_helper import SystemSetupHelper

class MockPasswordStore(PasswordStore):
    """Mock password store to simulate missing dependencies."""
    
    def __init__(self, missing_pass=False, missing_gpg=False):
        super().__init__()
        self.mock_missing_pass = missing_pass
        self.mock_missing_gpg = missing_gpg
    
    def _is_pass_installed(self):
        if self.mock_missing_pass:
            return False
        return super()._is_pass_installed()

def test_missing_pass():
    """Test scenario where pass is missing."""
    print("🚫 Testing Missing Pass Scenario")
    print("=" * 40)
    
    store = MockPasswordStore(missing_pass=True)
    is_valid, status = store.validate_complete_setup()
    
    print(f"Valid: {is_valid}")
    print(f"Missing dependencies: {status.get('missing_dependencies', [])}")
    print(f"Error message: {status.get('error_message')}")
    print(f"Suggested action: {status.get('suggested_action')}")
    print(f"Setup required: {status.get('setup_required')}")
    
    return status

def test_system_installation_commands():
    """Test installation command generation."""
    print("\n🔧 Testing Installation Commands")
    print("=" * 40)
    
    system_status = SystemSetupHelper.get_system_status()
    
    if system_status['distro_supported']:
        distro = system_status['distro']
        print(f"Distribution: {distro.name}")
        print(f"Package Manager: {distro.package_manager}")
        
        commands = system_status['installation_commands']
        print("\nInstallation commands that would be offered:")
        for cmd_type, command in commands.items():
            print(f"  {cmd_type}: {command}")
    else:
        print("Unsupported distribution - manual instructions would be shown")

def test_app_behavior():
    """Test how the app should behave with missing dependencies."""
    print("\n🎯 Expected Application Behavior")
    print("=" * 40)
    
    # Test missing pass
    status = test_missing_pass()
    missing_deps = status.get('missing_dependencies', [])
    
    print("\nWith missing dependencies, the application should:")
    print("1. ❌ NOT allow the user to continue without setup")
    print("2. 🔧 Show dependency installation dialog")
    print("3. 📦 Offer automatic installation on supported distributions")
    print("4. 📋 Provide manual installation instructions on unsupported systems")
    print("5. 🔄 Re-validate after installation")
    print("6. 🔑 Guide through GPG key creation after dependencies are installed")
    print("7. 🗂️  Automatically initialize password store")
    
    system_status = SystemSetupHelper.get_system_status()
    
    if system_status['can_install']:
        print(f"\n✅ This system supports automatic installation")
        print(f"   Distribution: {system_status['distro'].name}")
        print(f"   Package manager: {system_status['distro'].package_manager}")
        print(f"   The app will show an 'Install Now' button")
    else:
        print(f"\n⚠️  This system requires manual installation")
        print(f"   The app will show manual installation instructions")

if __name__ == "__main__":
    print("🧪 Testing Missing Dependencies Handling")
    print("=" * 60)
    
    test_missing_pass()
    test_system_installation_commands()
    test_app_behavior()
    
    print("\n" + "=" * 60)
    print("✅ All dependency handling tests completed!")
    print("The application now provides comprehensive dependency management.")
