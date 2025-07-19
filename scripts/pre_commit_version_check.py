#!/usr/bin/env python3
"""
Pre-commit hook for version synchronization validation.

This script ensures that all version references are synchronized
before allowing commits, preventing version inconsistency issues.
"""

import sys
import subprocess
from pathlib import Path


def check_version_sync() -> bool:
    """Check if version synchronization is consistent."""
    try:
        # Run validation script
        result = subprocess.run(
            [sys.executable, "scripts/validate_version.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Check if validation passed
        if result.returncode == 0 and "🎉 All version references are consistent!" in result.stdout:
            return True
        else:
            print("❌ Version synchronization check failed!")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running version sync check: {e}")
        return False


def auto_fix_version_sync() -> bool:
    """Attempt to automatically fix version synchronization."""
    try:
        print("🔧 Attempting to fix version synchronization...")
        
        # Run sync script
        result = subprocess.run(
            [sys.executable, "scripts/sync_version.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode == 0:
            print("✅ Version synchronization fixed automatically")
            return True
        else:
            print("❌ Failed to fix version synchronization automatically")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during auto-fix: {e}")
        return False


def main():
    """Main pre-commit hook function."""
    print("Checking version synchronization...")
    
    # First check if everything is synchronized
    if check_version_sync():
        print("✅ Version synchronization check passed")
        sys.exit(0)
    
    # If not synchronized, try to auto-fix
    print("\n⚠ Version synchronization issues detected")
    user_input = input("Attempt automatic fix? (y/n): ").lower().strip()
    
    if user_input in ['y', 'yes']:
        if auto_fix_version_sync():
            # Check again after fix
            if check_version_sync():
                print("\n✅ Version synchronization restored - commit can proceed")
                sys.exit(0)
            else:
                print("\n❌ Auto-fix completed but issues remain")
        else:
            print("\n❌ Auto-fix failed")
    
    print("\n💡 Manual steps to fix:")
    print("1. Run: python3 scripts/sync_version.py")
    print("2. Run: python3 scripts/validate_version.py")
    print("3. Commit the synchronized files")
    print("\n❌ Blocking commit due to version synchronization issues")
    sys.exit(1)


if __name__ == "__main__":
    main()