"""
Performance optimizations for the Secrets application.
"""
import time
import functools
import threading
from typing import Any, Callable, Dict, Optional, Tuple
from collections import OrderedDict
from gi.repository import GLib


class LRUCache:
    """Simple LRU cache implementation for password entries."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Put item in cache."""
        with self._lock:
            if key in self.cache:
                # Update existing item
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                # Add new item
                self.cache[key] = value
                if len(self.cache) > self.max_size:
                    # Remove least recently used item
                    self.cache.popitem(last=False)
    
    def invalidate(self, key: str) -> None:
        """Remove item from cache."""
        with self._lock:
            self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self.cache)


class PasswordCache:
    """Specialized cache for password entries with TTL support."""
    
    def __init__(self, max_size: int = 50, ttl_seconds: int = 60):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self._access_order: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get password entry from cache if not expired."""
        with self._lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                
                # Check if expired
                if time.time() - timestamp > self.ttl_seconds:
                    self._remove(key)
                    return None
                
                # Update access order
                self._access_order.move_to_end(key)
                return value
            
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Put password entry in cache."""
        with self._lock:
            current_time = time.time()
            
            if key in self.cache:
                # Update existing
                self.cache[key] = (value, current_time)
                self._access_order.move_to_end(key)
            else:
                # Add new
                self.cache[key] = (value, current_time)
                self._access_order[key] = current_time
                
                # Evict if necessary
                while len(self.cache) > self.max_size:
                    oldest_key = next(iter(self._access_order))
                    self._remove(oldest_key)
    
    def _remove(self, key: str) -> None:
        """Remove entry from cache."""
        self.cache.pop(key, None)
        self._access_order.pop(key, None)
    
    def invalidate(self, key: str) -> None:
        """Remove specific entry from cache."""
        with self._lock:
            self._remove(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self._access_order.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, (_, timestamp) in self.cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove(key)
            
            return len(expired_keys)


class Debouncer:
    """Debounce function calls to improve performance."""
    
    def __init__(self, delay_ms: int = 300):
        self.delay_ms = delay_ms
        self._timeout_id: Optional[int] = None
        self._lock = threading.Lock()
    
    def debounce(self, func: Callable, *args, **kwargs) -> None:
        """Debounce a function call."""
        with self._lock:
            # Cancel previous timeout
            if self._timeout_id is not None:
                GLib.source_remove(self._timeout_id)
            
            # Schedule new timeout
            self._timeout_id = GLib.timeout_add(
                self.delay_ms,
                self._execute_debounced,
                func, args, kwargs
            )
    
    def _execute_debounced(self, func: Callable, args: tuple, kwargs: dict) -> bool:
        """Execute the debounced function."""
        with self._lock:
            self._timeout_id = None
        
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"Error in debounced function: {e}")
        
        return False  # Don't repeat


def memoize_with_ttl(ttl_seconds: int = 60):
    """Decorator to memoize function results with TTL."""
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Tuple[Any, float]] = {}
        lock = threading.RLock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            
            with lock:
                # Check cache
                if key in cache:
                    result, timestamp = cache[key]
                    if time.time() - timestamp < ttl_seconds:
                        return result
                    else:
                        # Remove expired entry
                        del cache[key]
                
                # Call function and cache result
                result = func(*args, **kwargs)
                cache[key] = (result, time.time())
                
                # Cleanup old entries periodically
                if len(cache) > 100:  # Arbitrary limit
                    current_time = time.time()
                    expired_keys = [
                        k for k, (_, ts) in cache.items()
                        if current_time - ts >= ttl_seconds
                    ]
                    for k in expired_keys:
                        cache.pop(k, None)
                
                return result
        
        # Add cache management methods
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'hits': getattr(wrapper, '_hits', 0),
            'misses': getattr(wrapper, '_misses', 0)
        }
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Monitor performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def time_function(self, name: str):
        """Decorator to time function execution."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    self.record_metric(name, execution_time)
            return wrapper
        return decorator
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []
            
            self.metrics[name].append(value)
            
            # Keep only last 100 measurements
            if len(self.metrics[name]) > 100:
                self.metrics[name] = self.metrics[name][-100:]
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return {}
            
            values = self.metrics[name]
            return {
                'count': len(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'recent': values[-1] if values else 0
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all metrics."""
        with self._lock:
            return {name: self.get_stats(name) for name in self.metrics.keys()}
    
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()


class LazyLoader:
    """Lazy loading utility for expensive operations."""
    
    def __init__(self):
        self._loaded: Dict[str, Any] = {}
        self._loaders: Dict[str, Callable] = {}
        self._lock = threading.RLock()
    
    def register_loader(self, key: str, loader: Callable) -> None:
        """Register a lazy loader function."""
        with self._lock:
            self._loaders[key] = loader
    
    def get(self, key: str) -> Any:
        """Get value, loading it if necessary."""
        with self._lock:
            if key in self._loaded:
                return self._loaded[key]
            
            if key in self._loaders:
                value = self._loaders[key]()
                self._loaded[key] = value
                return value
            
            raise KeyError(f"No loader registered for key: {key}")
    
    def is_loaded(self, key: str) -> bool:
        """Check if value is already loaded."""
        with self._lock:
            return key in self._loaded
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        with self._lock:
            self._loaded.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._loaded.clear()


# Global instances
password_cache = PasswordCache(ttl_seconds=60)
search_debouncer = Debouncer(delay_ms=300)
performance_monitor = PerformanceMonitor()
lazy_loader = LazyLoader()


def optimize_password_loading():
    """Setup optimizations for password loading."""
    # Schedule periodic cache cleanup
    def cleanup_caches():
        expired_count = password_cache.cleanup_expired()
        if expired_count > 0:
            print(f"Cleaned up {expired_count} expired cache entries")
        return True  # Continue periodic cleanup
    
    # Run cleanup every 5 minutes
    GLib.timeout_add_seconds(300, cleanup_caches)


def get_performance_report() -> str:
    """Get a formatted performance report."""
    stats = performance_monitor.get_all_stats()
    
    if not stats:
        return "No performance data available"
    
    report = ["Performance Report:", "=" * 50]
    
    for name, metrics in stats.items():
        if metrics:
            report.append(f"\n{name}:")
            report.append(f"  Count: {metrics['count']}")
            report.append(f"  Average: {metrics['avg']:.3f}s")
            report.append(f"  Min: {metrics['min']:.3f}s")
            report.append(f"  Max: {metrics['max']:.3f}s")
            report.append(f"  Recent: {metrics['recent']:.3f}s")
    
    report.append(f"\nCache Stats:")
    report.append(f"  Password cache size: {password_cache.size()}")
    
    return "\n".join(report)
