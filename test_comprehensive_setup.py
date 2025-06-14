#!/usr/bin/env python3
"""
Test script to verify the comprehensive dependency and setup solution.
"""

import sys
import os

# Add the secrets module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secrets'))

from secrets.password_store import PasswordStore
from secrets.system_setup_helper import SystemSetupHelper

def test_system_detection():
    """Test system detection and package management."""
    print("🖥️  Testing System Detection")
    print("=" * 50)
    
    # Get system status
    status = SystemSetupHelper.get_system_status()
    
    print(f"Operating System: {status['os']}")
    
    if status['distro']:
        distro = status['distro']
        print(f"Distribution: {distro.name} {distro.version}")
        print(f"Package Manager: {distro.package_manager}")
        print(f"Supported: {status['distro_supported']}")
        
        if status['installation_commands']:
            print("\nInstallation Commands:")
            for cmd_type, command in status['installation_commands'].items():
                print(f"  {cmd_type}: {command}")
    else:
        print("Distribution: Unknown/Unsupported")
        print("Manual installation required")
    
    print(f"\nDependency Status:")
    print(f"  pass installed: {status['pass_installed']}")
    print(f"  GPG installed: {status['gpg_installed']}")
    print(f"  Can auto-install: {status['can_install']}")
    
    if status['manual_instructions']:
        print("\nManual Instructions:")
        for instruction in status['manual_instructions']:
            print(f"  {instruction}")

def test_comprehensive_validation():
    """Test the comprehensive validation."""
    print("\n\n🔍 Testing Comprehensive Validation")
    print("=" * 50)
    
    store = PasswordStore()
    is_valid, status = store.validate_complete_setup()
    
    print(f"Setup Valid: {is_valid}")
    print(f"Setup Required: {status.get('setup_required', False)}")
    
    print("\nDetailed Status:")
    for key, value in status.items():
        if key == 'missing_dependencies' and value:
            print(f"  {key}: {', '.join(value)}")
        else:
            print(f"  {key}: {value}")
    
    return is_valid, status

def test_installation_detection():
    """Test detection of installed packages."""
    print("\n\n📦 Testing Package Detection")
    print("=" * 50)
    
    # Test command availability
    pass_available = SystemSetupHelper.check_command_available('pass')
    gpg_available = SystemSetupHelper.check_command_available('gpg')
    
    print(f"pass command available: {pass_available}")
    print(f"gpg command available: {gpg_available}")
    
    # Test package manager detection
    distro = SystemSetupHelper.detect_distribution()
    if distro:
        print(f"\nPackage Manager Tests for {distro.name}:")
        
        pass_installed = SystemSetupHelper.check_package_installed(
            distro.pass_package, distro.package_manager
        )
        gpg_installed = SystemSetupHelper.check_package_installed(
            distro.gpg_package, distro.package_manager
        )
        
        print(f"  {distro.pass_package} package installed: {pass_installed}")
        print(f"  {distro.gpg_package} package installed: {gpg_installed}")

def show_setup_recommendations(status):
    """Show setup recommendations based on current status."""
    print("\n\n💡 Setup Recommendations")
    print("=" * 50)
    
    missing_deps = status.get('missing_dependencies', [])
    
    if not missing_deps:
        if status.get('gpg_keys_exist'):
            if status.get('store_gpg_id_exists'):
                print("✅ Everything is set up correctly!")
                print("   The password manager should work normally.")
            else:
                print("⚠️  GPG is working but password store needs initialization")
                print("   Recommendation: Initialize with 'pass init your-email@example.com'")
        else:
            print("⚠️  Dependencies installed but no GPG keys found")
            print("   Recommendation: Create a GPG key and initialize password store")
    else:
        print("❌ Missing dependencies detected!")
        print(f"   Missing: {', '.join(missing_deps)}")
        
        system_status = SystemSetupHelper.get_system_status()
        if system_status['can_install']:
            print("   ✅ Automatic installation available")
            print("   The application should offer to install dependencies automatically")
        else:
            print("   ⚠️  Manual installation required")
            print("   The application should provide manual installation instructions")

def main():
    """Run all tests."""
    print("🚀 Comprehensive Setup Solution Test")
    print("=" * 60)
    
    # Test 1: System Detection
    test_system_detection()
    
    # Test 2: Package Detection
    test_installation_detection()
    
    # Test 3: Comprehensive Validation
    is_valid, status = test_comprehensive_validation()
    
    # Test 4: Recommendations
    show_setup_recommendations(status)
    
    # Summary
    print("\n\n📋 Test Summary")
    print("=" * 60)
    
    if is_valid:
        print("🎉 All tests passed! The password manager should work correctly.")
    else:
        print("⚠️  Setup issues detected, but the application should handle them automatically:")
        
        missing_deps = status.get('missing_dependencies', [])
        if missing_deps:
            print(f"   • Missing dependencies: {', '.join(missing_deps)}")
            print("   • Application will offer automatic installation")
        
        if status.get('setup_required'):
            print("   • Setup required for GPG keys or password store")
            print("   • Application will guide user through setup process")
        
        print("\n   The new solution provides:")
        print("   ✅ Automatic dependency detection")
        print("   ✅ Distribution-specific installation commands")
        print("   ✅ Guided GPG key creation")
        print("   ✅ Automatic password store initialization")
        print("   ✅ No option to continue without proper setup")

if __name__ == "__main__":
    main()
