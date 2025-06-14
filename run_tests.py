#!/usr/bin/env python3
"""
Test runner for the Secrets application.
This script can run tests without requiring GTK4 to be available.
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def mock_gtk_imports():
    """Mock GTK imports so tests can run without GTK4."""
    # Mock gi module
    gi_mock = Mock()
    gi_mock.require_version = Mock()
    
    # Mock GTK and Adw modules
    gtk_mock = Mock()
    adw_mock = Mock()
    gdk_mock = Mock()
    gio_mock = Mock()
    glib_mock = Mock()
    gobject_mock = Mock()
    
    # Mock repository
    repository_mock = Mock()
    repository_mock.Gtk = gtk_mock
    repository_mock.Adw = adw_mock
    repository_mock.Gdk = gdk_mock
    repository_mock.Gio = gio_mock
    repository_mock.GLib = glib_mock
    repository_mock.GObject = gobject_mock
    
    gi_mock.repository = repository_mock
    
    # Install mocks
    sys.modules['gi'] = gi_mock
    sys.modules['gi.repository'] = repository_mock

def run_model_tests():
    """Run tests for models module."""
    print("Running model tests...")
    
    # Import and run tests
    from tests.test_models import TestPasswordEntry, TestSearchResult, TestAppState
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPasswordEntry))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchResult))
    suite.addTests(loader.loadTestsFromTestCase(TestAppState))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_service_tests():
    """Run tests for services module (with mocked dependencies)."""
    print("\nRunning service tests...")
    
    try:
        # Mock GTK dependencies
        mock_gtk_imports()
        
        from tests.test_services import TestPasswordService, TestValidationService, TestHierarchyService
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTests(loader.loadTestsFromTestCase(TestPasswordService))
        suite.addTests(loader.loadTestsFromTestCase(TestValidationService))
        suite.addTests(loader.loadTestsFromTestCase(TestHierarchyService))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    except Exception as e:
        print(f"Service tests failed with error: {e}")
        return False

def run_command_tests():
    """Run tests for commands module (with mocked dependencies)."""
    print("\nRunning command tests...")
    
    try:
        # Mock GTK dependencies
        mock_gtk_imports()
        
        from tests.test_commands import (
            TestCommandInvoker, TestCopyPasswordCommand, TestCopyUsernameCommand,
            TestOpenUrlCommand, TestGitSyncCommand
        )
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTests(loader.loadTestsFromTestCase(TestCommandInvoker))
        suite.addTests(loader.loadTestsFromTestCase(TestCopyPasswordCommand))
        suite.addTests(loader.loadTestsFromTestCase(TestCopyUsernameCommand))
        suite.addTests(loader.loadTestsFromTestCase(TestOpenUrlCommand))
        suite.addTests(loader.loadTestsFromTestCase(TestGitSyncCommand))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    except Exception as e:
        print(f"Command tests failed with error: {e}")
        return False

def run_performance_tests():
    """Run basic performance tests."""
    print("\nRunning performance tests...")
    
    try:
        # Mock GTK dependencies
        mock_gtk_imports()
        
        # Import performance module
        from secrets.performance import LRUCache, PasswordCache, Debouncer, memoize_with_ttl
        
        # Test LRU Cache
        cache = LRUCache(max_size=3)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        cache.put("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None, "LRU cache should have evicted key1"
        assert cache.get("key2") == "value2", "LRU cache should have key2"
        assert cache.size() == 3, f"LRU cache size should be 3, got {cache.size()}"
        
        # Test Password Cache
        pwd_cache = PasswordCache(max_size=2, ttl_seconds=1)
        pwd_cache.put("pwd1", "secret1")
        pwd_cache.put("pwd2", "secret2")
        
        assert pwd_cache.get("pwd1") == "secret1", "Password cache should have pwd1"
        
        # Test memoization
        call_count = 0
        
        @memoize_with_ttl(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = expensive_function(5)
        result2 = expensive_function(5)  # Should use cache
        
        assert result1 == 10, f"Function should return 10, got {result1}"
        assert result2 == 10, f"Function should return 10, got {result2}"
        assert call_count == 1, f"Function should be called once, called {call_count} times"
        
        print("✓ All performance tests passed")
        return True
        
    except Exception as e:
        print(f"Performance tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner."""
    print("Secrets Application Test Runner")
    print("=" * 50)
    
    all_passed = True
    
    # Run different test suites
    test_suites = [
        ("Models", run_model_tests),
        ("Services", run_service_tests),
        ("Commands", run_command_tests),
        ("Performance", run_performance_tests),
    ]
    
    results = {}
    
    for suite_name, test_func in test_suites:
        try:
            success = test_func()
            results[suite_name] = success
            all_passed = all_passed and success
        except Exception as e:
            print(f"Error running {suite_name} tests: {e}")
            results[suite_name] = False
            all_passed = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for suite_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{suite_name:20} {status}")
    
    print("-" * 50)
    overall_status = "✓ ALL TESTS PASSED" if all_passed else "✗ SOME TESTS FAILED"
    print(f"Overall:             {overall_status}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
