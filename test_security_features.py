#!/usr/bin/env python3
"""
Test script for security features.
"""

import sys
import os
import time
import threading

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_security_settings():
    """Test that security configuration settings are properly defined."""
    print("Testing security configuration...")
    
    try:
        from secrets.config import ConfigManager, SecurityConfig
        
        # Test default security config
        security_config = SecurityConfig()
        
        # Check that all new security settings exist
        assert hasattr(security_config, 'lock_on_idle')
        assert hasattr(security_config, 'idle_timeout_minutes')
        assert hasattr(security_config, 'lock_on_screen_lock')
        assert hasattr(security_config, 'master_password_timeout_minutes')
        assert hasattr(security_config, 'clear_memory_on_lock')
        assert hasattr(security_config, 'require_master_password_for_export')
        assert hasattr(security_config, 'max_failed_unlock_attempts')
        assert hasattr(security_config, 'lockout_duration_minutes')
        
        # Check default values
        assert security_config.lock_on_idle == False
        assert security_config.idle_timeout_minutes == 15
        assert security_config.lock_on_screen_lock == True
        assert security_config.master_password_timeout_minutes == 60
        assert security_config.clear_memory_on_lock == True
        assert security_config.require_master_password_for_export == True
        assert security_config.max_failed_unlock_attempts == 3
        assert security_config.lockout_duration_minutes == 5
        
        print("✓ Security configuration settings are properly defined")
        
        # Test config manager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert hasattr(config, 'security')
        assert isinstance(config.security, SecurityConfig)
        
        print("✓ ConfigManager properly loads security settings")
        
    except Exception as e:
        print(f"✗ Security configuration test failed: {e}")
        return False
        
    return True

def test_idle_detector():
    """Test the idle detection functionality."""
    print("Testing idle detector...")
    
    try:
        from secrets.security_manager import IdleDetector
        
        detector = IdleDetector()
        
        # Test initial state
        assert detector.get_idle_time_seconds() >= 0
        
        # Test activity callback registration
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
            
        detector.register_activity_callback(test_callback)
        detector.reset_idle_timer()
        
        assert callback_called, "Activity callback should be called"
        
        print("✓ Idle detector basic functionality works")
        
    except Exception as e:
        print(f"✗ Idle detector test failed: {e}")
        return False
        
    return True

def test_security_manager():
    """Test the security manager functionality."""
    print("Testing security manager...")
    
    try:
        from secrets.config import ConfigManager
        from secrets.security_manager import SecurityManager
        
        config_manager = ConfigManager()
        security_manager = SecurityManager(config_manager)
        
        # Test initial state
        assert not security_manager.is_locked()
        assert not security_manager.is_in_lockout()
        
        # Test lock/unlock
        security_manager.lock_application("Test lock")
        assert security_manager.is_locked()
        
        # Test unlock
        success = security_manager.unlock_application("test_password")
        assert success  # Should succeed with current implementation
        assert not security_manager.is_locked()
        
        print("✓ Security manager basic functionality works")
        
    except Exception as e:
        print(f"✗ Security manager test failed: {e}")
        return False
        
    return True

def test_security_constants():
    """Test that security constants are properly defined."""
    print("Testing security constants...")
    
    try:
        from secrets.config import Constants
        
        # Check that new constants exist
        assert hasattr(Constants, 'DEFAULT_IDLE_TIMEOUT_MINUTES')
        assert hasattr(Constants, 'DEFAULT_MASTER_PASSWORD_TIMEOUT_MINUTES')
        assert hasattr(Constants, 'DEFAULT_LOCKOUT_DURATION_MINUTES')
        assert hasattr(Constants, 'MAX_FAILED_UNLOCK_ATTEMPTS')
        
        # Check values
        assert Constants.DEFAULT_IDLE_TIMEOUT_MINUTES == 15
        assert Constants.DEFAULT_MASTER_PASSWORD_TIMEOUT_MINUTES == 60
        assert Constants.DEFAULT_LOCKOUT_DURATION_MINUTES == 5
        assert Constants.MAX_FAILED_UNLOCK_ATTEMPTS == 3
        
        print("✓ Security constants are properly defined")
        
    except Exception as e:
        print(f"✗ Security constants test failed: {e}")
        return False
        
    return True

def main():
    """Run all security feature tests."""
    print("Running security features tests...\n")
    
    tests = [
        test_config_security_settings,
        test_security_constants,
        test_idle_detector,
        test_security_manager,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All security feature tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
