#!/usr/bin/env python3
"""
Test script to demonstrate the complete GPG validation and setup solution.
"""

import sys
import os

# Add the secrets module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secrets'))

from secrets.password_store import PasswordStore
from secrets.gpg_setup_helper import GPGSetupHelper

def test_complete_solution():
    """Test the complete GPG validation and setup solution."""
    print("🔐 Testing Complete GPG Solution")
    print("=" * 60)
    
    # Test 1: Password Store Validation
    print("\n1. Testing Password Store GPG Validation")
    print("-" * 40)
    
    store = PasswordStore()
    print(f"Store directory: {store.store_dir}")
    print(f"Store initialized: {store.is_initialized}")
    
    # Run comprehensive GPG validation
    is_valid, status = store.validate_gpg_setup()
    
    print(f"\nGPG Validation Results:")
    print(f"  Valid: {is_valid}")
    print(f"  GPG Installed: {status['gpg_installed']}")
    print(f"  GPG Keys Exist: {status['gpg_keys_exist']}")
    print(f"  Store GPG ID Exists: {status['store_gpg_id_exists']}")
    print(f"  Store GPG ID: {status['store_gpg_id']}")
    print(f"  Error: {status['error_message']}")
    print(f"  Suggested Action: {status['suggested_action']}")
    
    print(f"\nUser-friendly message:")
    print(f"  {store.get_gpg_status_message(status)}")
    
    # Test 2: GPG Setup Helper
    print("\n\n2. Testing GPG Setup Helper")
    print("-" * 40)
    
    helper = GPGSetupHelper()
    
    # Get current GPG keys
    success, keys = helper.get_gpg_key_ids()
    print(f"Current GPG keys found: {len(keys) if success else 0}")
    
    if success and keys:
        for i, key in enumerate(keys):
            print(f"  Key {i+1}:")
            print(f"    ID: {key['keyid']}")
            print(f"    UIDs: {', '.join(key['uids'])}")
    
    # Show setup recommendations
    print(f"\nRecommended setup steps:")
    steps = helper.suggest_gpg_setup_steps()
    for step in steps:
        print(f"  {step}")
    
    # Test 3: Password Listing with Better Error Handling
    print("\n\n3. Testing Password Listing")
    print("-" * 40)
    
    passwords = store.list_passwords()
    print(f"Passwords found: {len(passwords)}")
    
    if passwords:
        print("Password list:")
        for pwd in passwords[:5]:  # Show first 5
            print(f"  - {pwd}")
        if len(passwords) > 5:
            print(f"  ... and {len(passwords) - 5} more")
    else:
        print("No passwords found.")
        
        # Check if .gpg files exist but can't be read
        if store.store_dir and os.path.isdir(store.store_dir):
            gpg_files = []
            for root, dirs, files in os.walk(store.store_dir):
                gpg_files.extend([f for f in files if f.endswith('.gpg')])
            
            if gpg_files:
                print(f"Found {len(gpg_files)} .gpg files that cannot be accessed:")
                for gpg_file in gpg_files[:3]:
                    print(f"  - {gpg_file}")
                if len(gpg_files) > 3:
                    print(f"  ... and {len(gpg_files) - 3} more")
                print("This confirms the GPG key issue!")
    
    # Test 4: Summary and Recommendations
    print("\n\n4. Summary and Recommendations")
    print("-" * 40)
    
    if is_valid:
        print("✅ GPG setup is working correctly!")
        print("   The application should work normally.")
    else:
        print("❌ GPG setup issues detected!")
        print("   The application should:")
        print("   1. Show a clear error message to the user")
        print("   2. Offer to help set up GPG automatically")
        print("   3. Provide manual setup instructions")
        print("   4. Allow continuing with limited functionality")
        
        print(f"\n   Specific issue: {status['error_message']}")
        print(f"   Recommended action: {status['suggested_action']}")
    
    print("\n" + "=" * 60)
    print("🎯 Solution Summary:")
    print("   • Comprehensive GPG validation on startup")
    print("   • Clear error messages with specific issues")
    print("   • Automated GPG key creation option")
    print("   • Manual setup instructions")
    print("   • Graceful degradation with limited functionality")
    print("   • Better feedback when no passwords are visible")

if __name__ == "__main__":
    test_complete_solution()
