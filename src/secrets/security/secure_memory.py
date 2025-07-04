"""Secure memory handling for sensitive data."""

import ctypes
import ctypes.util
import os
import sys
import weakref
from typing import Optional, Union, Any
import logging

logger = logging.getLogger(__name__)


class SecureMemoryError(Exception):
    """Exception raised for secure memory operations."""
    pass


class SecureMemory:
    """Manages secure memory operations including mlock and memory wiping."""
    
    _instances = weakref.WeakSet()
    _libc = None
    _mlock_available = None
    
    @classmethod
    def _get_libc(cls):
        """Get libc library for system calls."""
        if cls._libc is None:
            try:
                if sys.platform.startswith('linux'):
                    cls._libc = ctypes.CDLL("libc.so.6")
                elif sys.platform == 'darwin':
                    cls._libc = ctypes.CDLL("libc.dylib")
                elif sys.platform.startswith('win'):
                    # Windows doesn't have mlock, use VirtualLock instead
                    cls._libc = ctypes.windll.kernel32
                else:
                    logger.warning(f"Unsupported platform for memory locking: {sys.platform}")
                    cls._libc = None
            except (OSError, AttributeError) as e:
                logger.warning(f"Could not load libc: {e}")
                cls._libc = None
        return cls._libc
    
    @classmethod
    def is_mlock_available(cls) -> bool:
        """Check if memory locking is available on this system."""
        if cls._mlock_available is None:
            libc = cls._get_libc()
            if libc is None:
                cls._mlock_available = False
            else:
                try:
                    if sys.platform.startswith('win'):
                        # Test VirtualLock availability
                        cls._mlock_available = hasattr(libc, 'VirtualLock')
                    else:
                        # Test mlock availability
                        cls._mlock_available = hasattr(libc, 'mlock')
                except:
                    cls._mlock_available = False
        return cls._mlock_available
    
    def __init__(self, size: int):
        """
        Initialize secure memory block.
        
        Args:
            size: Size of memory block in bytes
        """
        self.size = size
        self.address = None
        self.locked = False
        self._buffer = None
        
        # Allocate memory
        try:
            self._buffer = ctypes.create_string_buffer(size)
            self.address = ctypes.addressof(self._buffer)
            
            # Try to lock memory
            if self.is_mlock_available():
                self._lock_memory()
            else:
                logger.warning("Memory locking not available - sensitive data may be swapped to disk")
                
        except Exception as e:
            raise SecureMemoryError(f"Failed to allocate secure memory: {e}")
        
        # Track instances for cleanup
        SecureMemory._instances.add(self)
    
    def _lock_memory(self):
        """Lock memory to prevent swapping."""
        if not self.address or self.locked:
            return
        
        libc = self._get_libc()
        if libc is None:
            return
        
        try:
            if sys.platform.startswith('win'):
                # Windows VirtualLock
                result = libc.VirtualLock(self.address, self.size)
                if not result:
                    error_code = libc.GetLastError()
                    logger.warning(f"VirtualLock failed with error code: {error_code}")
                else:
                    self.locked = True
                    logger.debug(f"Successfully locked {self.size} bytes of memory")
            else:
                # Unix mlock
                result = libc.mlock(self.address, self.size)
                if result != 0:
                    # Get errno
                    errno = ctypes.get_errno()
                    if errno == 1:  # EPERM
                        logger.warning("Permission denied for mlock - run with appropriate privileges")
                    elif errno == 12:  # ENOMEM
                        logger.warning("Insufficient memory for mlock")
                    else:
                        logger.warning(f"mlock failed with errno: {errno}")
                else:
                    self.locked = True
                    logger.debug(f"Successfully locked {self.size} bytes of memory")
                    
        except Exception as e:
            logger.warning(f"Failed to lock memory: {e}")
    
    def _unlock_memory(self):
        """Unlock memory."""
        if not self.address or not self.locked:
            return
        
        libc = self._get_libc()
        if libc is None:
            return
        
        try:
            if sys.platform.startswith('win'):
                libc.VirtualUnlock(self.address, self.size)
            else:
                libc.munlock(self.address, self.size)
            self.locked = False
            logger.debug(f"Successfully unlocked {self.size} bytes of memory")
        except Exception as e:
            logger.warning(f"Failed to unlock memory: {e}")
    
    def write(self, data: bytes, offset: int = 0):
        """
        Write data to secure memory.
        
        Args:
            data: Data to write
            offset: Offset in bytes
        """
        if not self._buffer:
            raise SecureMemoryError("Memory not allocated")
        
        if offset + len(data) > self.size:
            raise SecureMemoryError("Data too large for memory block")
        
        # Copy data to secure memory
        ctypes.memmove(self.address + offset, data, len(data))
    
    def read(self, length: int, offset: int = 0) -> bytes:
        """
        Read data from secure memory.
        
        Args:
            length: Number of bytes to read
            offset: Offset in bytes
            
        Returns:
            Data read from memory
        """
        if not self._buffer:
            raise SecureMemoryError("Memory not allocated")
        
        if offset + length > self.size:
            raise SecureMemoryError("Read beyond memory block bounds")
        
        # Copy data from secure memory
        result = ctypes.string_at(self.address + offset, length)
        return result
    
    def wipe(self):
        """Securely wipe memory contents."""
        if not self.address:
            return
        
        try:
            # Multiple passes with different patterns for security
            patterns = [b'\x00', b'\xff', b'\xaa', b'\x55', b'\x00']
            
            for pattern in patterns:
                # Fill with pattern
                pattern_byte = pattern[0]
                for i in range(self.size):
                    ctypes.c_ubyte.from_address(self.address + i).value = pattern_byte
                
                # Force memory sync
                if hasattr(os, 'sync'):
                    os.sync()
            
            logger.debug(f"Successfully wiped {self.size} bytes of memory")
            
        except Exception as e:
            logger.warning(f"Failed to wipe memory: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up secure memory."""
        if self.address:
            # Wipe memory before releasing
            self.wipe()
            # Unlock memory
            self._unlock_memory()
            self.address = None
            self._buffer = None
    
    @classmethod
    def cleanup_all(cls):
        """Clean up all secure memory instances."""
        # Create a copy of the set to avoid modification during iteration
        instances = list(cls._instances)
        for instance in instances:
            instance.cleanup()


class SecureString:
    """A string class that stores data in secure memory with automatic wiping."""
    
    def __init__(self, initial_value: Union[str, bytes] = ""):
        """
        Initialize secure string.
        
        Args:
            initial_value: Initial string value
        """
        if isinstance(initial_value, str):
            self._data = initial_value.encode('utf-8')
        else:
            self._data = initial_value
        
        # Allocate secure memory with some extra space for growth
        self._secure_memory = SecureMemory(max(len(self._data) + 64, 256))
        
        # Write initial data
        if self._data:
            self._secure_memory.write(self._data)
        
        self._length = len(self._data)
        self._is_valid = True
    
    def get(self) -> str:
        """
        Get the string value.
        
        Returns:
            String value
        """
        if not self._is_valid:
            raise ValueError("SecureString has been wiped")
        
        if self._length == 0:
            return ""
        
        data = self._secure_memory.read(self._length)
        return data.decode('utf-8', errors='replace')
    
    def get_bytes(self) -> bytes:
        """
        Get the bytes value.
        
        Returns:
            Bytes value
        """
        if not self._is_valid:
            raise ValueError("SecureString has been wiped")
        
        if self._length == 0:
            return b""
        
        return self._secure_memory.read(self._length)
    
    def set(self, value: Union[str, bytes]):
        """
        Set the string value.
        
        Args:
            value: New string value
        """
        if not self._is_valid:
            raise ValueError("SecureString has been wiped")
        
        if isinstance(value, str):
            new_data = value.encode('utf-8')
        else:
            new_data = value
        
        # Check if we need more memory
        if len(new_data) > self._secure_memory.size:
            # Create new larger memory block
            old_memory = self._secure_memory
            self._secure_memory = SecureMemory(len(new_data) + 64)
            old_memory.cleanup()
        
        # Wipe old data first
        self._secure_memory.wipe()
        
        # Write new data
        if new_data:
            self._secure_memory.write(new_data)
        
        self._length = len(new_data)
    
    def append(self, value: Union[str, bytes]):
        """
        Append to the string value.
        
        Args:
            value: Value to append
        """
        current = self.get_bytes()
        if isinstance(value, str):
            value = value.encode('utf-8')
        self.set(current + value)
    
    def clear(self):
        """Clear the string value but keep the object valid."""
        if self._is_valid:
            self._secure_memory.wipe()
            self._length = 0
    
    def wipe(self):
        """Permanently wipe the string and make it invalid."""
        if self._secure_memory:
            self._secure_memory.cleanup()
            self._secure_memory = None
        self._length = 0
        self._is_valid = False
    
    def __len__(self) -> int:
        """Get the length of the string."""
        return self._length if self._is_valid else 0
    
    def __str__(self) -> str:
        """String representation (masked for security)."""
        if not self._is_valid:
            return "<wiped>"
        return f"<SecureString: {self._length} chars>"
    
    def __repr__(self) -> str:
        """String representation (masked for security)."""
        return self.__str__()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.wipe()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic wiping."""
        self.wipe()


class SecureStringFactory:
    """Factory for creating secure strings with global management."""
    
    _instances = weakref.WeakSet()
    
    @classmethod
    def create(cls, initial_value: Union[str, bytes] = "") -> SecureString:
        """
        Create a new secure string.
        
        Args:
            initial_value: Initial value
            
        Returns:
            SecureString instance
        """
        secure_string = SecureString(initial_value)
        cls._instances.add(secure_string)
        return secure_string
    
    @classmethod
    def wipe_all(cls):
        """Wipe all secure strings created by this factory."""
        instances = list(cls._instances)
        for instance in instances:
            instance.wipe()
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get statistics about secure strings."""
        instances = list(cls._instances)
        total_instances = len(instances)
        total_memory = sum(len(instance) for instance in instances if instance._is_valid)
        
        return {
            'total_instances': total_instances,
            'total_memory_bytes': total_memory,
            'mlock_available': SecureMemory.is_mlock_available()
        }


# Module cleanup function
def cleanup_secure_memory():
    """Clean up all secure memory allocations."""
    SecureMemory.cleanup_all()
    SecureStringFactory.wipe_all()


# Register cleanup function
import atexit
atexit.register(cleanup_secure_memory)