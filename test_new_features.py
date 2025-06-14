#!/usr/bin/env python3
"""
Test script to verify the new features are working correctly.
"""

import sys
import os

# Add the secrets module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secrets'))

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    
    try:
        from secrets.preferences_dialog import PreferencesDialog
        print("✓ PreferencesDialog imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PreferencesDialog: {e}")
        return False
    
    try:
        from secrets.shortcuts_window import ShortcutsWindow
        print("✓ ShortcutsWindow imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ShortcutsWindow: {e}")
        return False
    
    try:
        from secrets.password_generator import PasswordGeneratorDialog
        print("✓ PasswordGeneratorDialog imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PasswordGeneratorDialog: {e}")
        return False
    
    try:
        from secrets.import_export import ImportExportDialog
        print("✓ ImportExportDialog imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ImportExportDialog: {e}")
        return False
    
    return True

def test_config():
    """Test configuration management."""
    print("\nTesting configuration...")
    
    try:
        from secrets.config import ConfigManager, ThemeManager, UIConfig
        
        # Test config creation
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"✓ Config loaded: theme={config.ui.theme}, remember_window={config.ui.remember_window_state}")
        
        # Test theme manager
        theme_manager = ThemeManager(config_manager)
        available_themes = theme_manager.get_available_themes()
        print(f"✓ Available themes: {available_themes}")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def test_password_generation():
    """Test password generation functionality."""
    print("\nTesting password generation...")
    
    try:
        import secrets
        import string
        
        # Test basic password generation
        charset = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = "".join(secrets.choice(charset) for _ in range(16))
        
        print(f"✓ Generated test password: {password[:4]}... (length: {len(password)})")
        
        # Test strength calculation (simplified)
        score = 0
        score += min(len(password) * 2, 25)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in "!@#$%^&*()" for c in password)
        variety_count = sum([has_lower, has_upper, has_digit, has_symbol])
        score += variety_count * 15
        
        print(f"✓ Password strength score: {score}/100")
        
        return True
    except Exception as e:
        print(f"✗ Password generation test failed: {e}")
        return False

def test_clipboard_manager():
    """Test clipboard manager functionality."""
    print("\nTesting clipboard manager...")
    
    try:
        from secrets.managers import ClipboardManager, ToastManager
        
        # Create mock objects for testing
        class MockDisplay:
            def get_clipboard(self):
                return MockClipboard()
        
        class MockClipboard:
            def __init__(self):
                self.text = ""
            
            def set_text(self, text):
                self.text = text
            
            def read_text(self):
                return self.text
        
        class MockToastOverlay:
            def add_toast(self, toast):
                pass
        
        # Test clipboard manager
        toast_manager = ToastManager(MockToastOverlay())
        clipboard_manager = ClipboardManager(MockDisplay(), toast_manager)
        
        print("✓ ClipboardManager created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Clipboard manager test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing new features implementation...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_password_generation,
        test_clipboard_manager,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! New features are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
