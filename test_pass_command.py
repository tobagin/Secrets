#!/usr/bin/env python3
"""
Test script to debug the pass command issue.
"""

import subprocess
import os

def test_pass_command():
    """Test the pass command directly."""
    print("Testing pass command...")
    
    # Test 1: Check if pass is accessible
    try:
        result = subprocess.run(["pass", "--version"], capture_output=True, text=True, timeout=5)
        print(f"Pass version: {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("❌ Pass command timed out")
        return False
    except FileNotFoundError:
        print("❌ Pass command not found")
        return False
    except Exception as e:
        print(f"❌ Error running pass: {e}")
        return False
    
    # Test 2: List passwords
    try:
        result = subprocess.run(["pass", "ls"], capture_output=True, text=True, timeout=5)
        print(f"Pass ls output:\n{result.stdout}")
    except Exception as e:
        print(f"❌ Error listing passwords: {e}")
        return False
    
    # Test 3: Try to insert a test password
    test_path = "test/debug_entry"
    test_content = "test_password_123\nusername: testuser\nnotes: This is a test entry"
    
    print(f"Testing password insertion for: {test_path}")
    
    try:
        # Use a shorter timeout to avoid hanging
        result = subprocess.run(
            ["pass", "insert", "-m", "-f", test_path],
            input=test_content,
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout
        )
        
        if result.returncode == 0:
            print("✅ Password insertion successful!")
            print(f"Output: {result.stdout}")
            
            # Try to retrieve it
            result2 = subprocess.run(
                ["pass", "show", test_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result2.returncode == 0:
                print("✅ Password retrieval successful!")
                print(f"Retrieved content:\n{result2.stdout}")
                
                # Clean up
                subprocess.run(["pass", "rm", "-f", test_path], capture_output=True)
                print("✅ Test entry cleaned up")
                
            else:
                print(f"❌ Failed to retrieve test password: {result2.stderr}")
        else:
            print(f"❌ Password insertion failed!")
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Password insertion timed out - this is likely the issue!")
        print("This suggests GPG is waiting for a passphrase or there's another blocking issue.")
        return False
    except Exception as e:
        print(f"❌ Error during password insertion: {e}")
        return False
    
    return True

def check_gpg_setup():
    """Check GPG setup."""
    print("\nChecking GPG setup...")
    
    try:
        # Check GPG version
        result = subprocess.run(["gpg", "--version"], capture_output=True, text=True, timeout=5)
        print(f"GPG version: {result.stdout.split()[2]}")
        
        # List GPG keys
        result = subprocess.run(["gpg", "--list-secret-keys"], capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            print("✅ GPG secret keys found")
            print(f"Keys:\n{result.stdout}")
        else:
            print("❌ No GPG secret keys found - this might be the issue!")
            return False
            
    except Exception as e:
        print(f"❌ Error checking GPG: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Debugging pass command issues...")
    print("=" * 50)
    
    # Check environment
    print(f"PATH: {os.environ.get('PATH', 'Not set')}")
    print(f"PASSWORD_STORE_DIR: {os.environ.get('PASSWORD_STORE_DIR', 'Not set (using default)')}")
    print()
    
    # Run tests
    gpg_ok = check_gpg_setup()
    pass_ok = test_pass_command()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"GPG setup: {'✅ OK' if gpg_ok else '❌ Issues found'}")
    print(f"Pass command: {'✅ OK' if pass_ok else '❌ Issues found'}")
    
    if not gpg_ok:
        print("\n🔧 Suggested fixes for GPG:")
        print("1. Generate a GPG key: gpg --gen-key")
        print("2. Initialize pass with your key: pass init your-email@example.com")
    
    if not pass_ok:
        print("\n🔧 Suggested fixes for pass:")
        print("1. Check if GPG agent is running")
        print("2. Try running 'pass insert test/manual' manually to see what happens")
        print("3. Check if GPG is asking for a passphrase")

if __name__ == "__main__":
    main()
