#!/usr/bin/env python3
"""
Test script to verify the new GPG validation functionality.
"""

import sys
import os

# Add the secrets module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secrets'))

from secrets.password_store import PasswordStore

def test_gpg_validation():
    """Test the new GPG validation functionality."""
    print("Testing GPG validation...")
    print("=" * 50)
    
    # Create a password store instance
    store = PasswordStore()
    
    print(f"Store directory: {store.store_dir}")
    print(f"Store initialized: {store.is_initialized}")
    print()
    
    # Test GPG validation
    print("Running GPG validation...")
    is_valid, status = store.validate_gpg_setup()
    
    print(f"GPG setup valid: {is_valid}")
    print("Status details:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print()
    print("User-friendly status message:")
    print(store.get_gpg_status_message(status))
    
    print("\n" + "=" * 50)
    
    if not is_valid:
        print("❌ GPG setup issues detected!")
        print(f"Error: {status.get('error_message', 'Unknown error')}")
        print(f"Suggested action: {status.get('suggested_action', 'Check setup')}")
    else:
        print("✅ GPG setup is working correctly!")
        
        # Test listing passwords
        print("\nTesting password listing...")
        passwords = store.list_passwords()
        print(f"Found {len(passwords)} passwords:")
        for pwd in passwords:
            print(f"  - {pwd}")

if __name__ == "__main__":
    test_gpg_validation()
