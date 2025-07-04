"""Unit tests for secure memory functionality."""

import pytest
from unittest.mock import patch, MagicMock

from src.secrets.security.secure_memory import SecureMemory, SecureString, SecureStringFactory


class TestSecureMemory:
    """Test cases for SecureMemory."""
    
    def test_secure_memory_basic(self):
        """Test basic secure memory operations."""
        memory = SecureMemory(1024)
        
        assert memory.size == 1024
        assert memory.address is not None
        
        # Test write and read
        test_data = b"test data"
        memory.write(test_data)
        
        read_data = memory.read(len(test_data))
        assert read_data == test_data
        
        memory.cleanup()
    
    def test_secure_memory_wipe(self):
        """Test memory wiping."""
        memory = SecureMemory(64)
        
        test_data = b"sensitive data"
        memory.write(test_data)
        
        # Verify data is there
        read_data = memory.read(len(test_data))
        assert read_data == test_data
        
        # Wipe memory
        memory.wipe()
        
        # Data should be gone (all zeros)
        wiped_data = memory.read(len(test_data))
        assert wiped_data == b'\x00' * len(test_data)
        
        memory.cleanup()
    
    def test_secure_memory_bounds_checking(self):
        """Test bounds checking."""
        memory = SecureMemory(10)
        
        # Writing beyond bounds should raise error
        with pytest.raises(Exception):
            memory.write(b"this is too long", 0)
        
        # Reading beyond bounds should raise error
        with pytest.raises(Exception):
            memory.read(20, 0)
        
        memory.cleanup()
    
    @patch('src.secrets.security.secure_memory.SecureMemory.is_mlock_available')
    def test_mlock_unavailable(self, mock_mlock_available):
        """Test behavior when mlock is unavailable."""
        mock_mlock_available.return_value = False
        
        memory = SecureMemory(64)
        assert not memory.locked
        
        memory.cleanup()


class TestSecureString:
    """Test cases for SecureString."""
    
    def test_secure_string_basic(self):
        """Test basic secure string operations."""
        secure_str = SecureString("test string")
        
        assert secure_str.get() == "test string"
        assert len(secure_str) == 11
        
        secure_str.wipe()
    
    def test_secure_string_set(self):
        """Test setting string value."""
        secure_str = SecureString()
        
        secure_str.set("new value")
        assert secure_str.get() == "new value"
        
        secure_str.set("another value")
        assert secure_str.get() == "another value"
        
        secure_str.wipe()
    
    def test_secure_string_append(self):
        """Test appending to string."""
        secure_str = SecureString("hello")
        
        secure_str.append(" world")
        assert secure_str.get() == "hello world"
        
        secure_str.wipe()
    
    def test_secure_string_clear(self):
        """Test clearing string."""
        secure_str = SecureString("test")
        
        secure_str.clear()
        assert secure_str.get() == ""
        assert len(secure_str) == 0
        
        secure_str.wipe()
    
    def test_secure_string_wipe(self):
        """Test wiping string."""
        secure_str = SecureString("sensitive")
        
        secure_str.wipe()
        
        with pytest.raises(ValueError):
            secure_str.get()
        
        assert len(secure_str) == 0
    
    def test_secure_string_context_manager(self):
        """Test using SecureString as context manager."""
        with SecureString("context test") as secure_str:
            assert secure_str.get() == "context test"
        
        # String should be wiped after context exit
        with pytest.raises(ValueError):
            secure_str.get()
    
    def test_secure_string_bytes(self):
        """Test working with bytes."""
        secure_str = SecureString(b"byte data")
        
        assert secure_str.get_bytes() == b"byte data"
        assert secure_str.get() == "byte data"
        
        secure_str.wipe()
    
    def test_secure_string_growth(self):
        """Test string growth beyond initial capacity."""
        secure_str = SecureString("small")
        
        # Append large data to trigger growth
        large_data = "x" * 1000
        secure_str.append(large_data)
        
        expected = "small" + large_data
        assert secure_str.get() == expected
        
        secure_str.wipe()


class TestSecureStringFactory:
    """Test cases for SecureStringFactory."""
    
    def test_factory_create(self):
        """Test factory creation."""
        secure_str = SecureStringFactory.create("test")
        
        assert secure_str.get() == "test"
        
        secure_str.wipe()
    
    def test_factory_stats(self):
        """Test factory statistics."""
        # Clean slate
        SecureStringFactory.wipe_all()
        
        str1 = SecureStringFactory.create("test1")
        str2 = SecureStringFactory.create("test2")
        
        stats = SecureStringFactory.get_stats()
        
        assert stats['total_instances'] == 2
        assert stats['total_memory_bytes'] > 0
        
        str1.wipe()
        str2.wipe()
    
    def test_factory_wipe_all(self):
        """Test wiping all factory strings."""
        str1 = SecureStringFactory.create("test1")
        str2 = SecureStringFactory.create("test2")
        
        SecureStringFactory.wipe_all()
        
        with pytest.raises(ValueError):
            str1.get()
        
        with pytest.raises(ValueError):
            str2.get()
    
    def test_memory_cleanup_on_exit(self):
        """Test cleanup function registration."""
        # This mainly tests that the cleanup function is registered
        # without causing errors
        from src.secrets.security.secure_memory import cleanup_secure_memory
        
        # Should not raise exceptions
        cleanup_secure_memory()