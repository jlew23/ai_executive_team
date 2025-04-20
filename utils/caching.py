"""
Caching utilities for the AI Executive Team application.
"""

import logging
import functools
import hashlib
import json
import time
from datetime import datetime, timedelta
import threading
import pickle

logger = logging.getLogger(__name__)

class CacheItem:
    """
    Represents an item in the cache with metadata.
    """
    
    def __init__(self, value, expires_at=None):
        """
        Initialize a cache item.
        
        Args:
            value: The value to cache
            expires_at: Optional expiration datetime
        """
        self.value = value
        self.expires_at = expires_at
        self.created_at = datetime.utcnow()
        self.last_accessed_at = self.created_at
        self.access_count = 0
    
    def is_expired(self):
        """
        Check if the cache item is expired.
        
        Returns:
            True if expired, False otherwise
        """
        if self.expires_at is None:
            return False
        
        return datetime.utcnow() > self.expires_at
    
    def access(self):
        """
        Record an access to this cache item.
        """
        self.last_accessed_at = datetime.utcnow()
        self.access_count += 1
        
    def get_age_seconds(self):
        """
        Get the age of the cache item in seconds.
        
        Returns:
            Age in seconds
        """
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    def get_last_access_seconds(self):
        """
        Get the time since last access in seconds.
        
        Returns:
            Time since last access in seconds
        """
        return (datetime.utcnow() - self.last_accessed_at).total_seconds()

class MemoryCache:
    """
    In-memory cache implementation with expiration and LRU eviction.
    """
    
    def __init__(self, max_size=1000, default_ttl_seconds=300, cleanup_interval_seconds=60):
        """
        Initialize the memory cache.
        
        Args:
            max_size: Maximum number of items in the cache
            default_ttl_seconds: Default time-to-live for cache items in seconds
            cleanup_interval_seconds: Interval for cleanup of expired items
        """
        self.cache = {}
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get(self, key, default=None):
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        with self.lock:
            if key not in self.cache:
                return default
            
            item = self.cache[key]
            
            # Check if expired
            if item.is_expired():
                del self.cache[key]
                return default
            
            # Update access metadata
            item.access()
            
            return item.value
    
    def set(self, key, value, ttl_seconds=None):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional time-to-live in seconds
        """
        with self.lock:
            # Check if we need to evict items
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru_item()
            
            # Calculate expiration time
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            elif self.default_ttl_seconds is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=self.default_ttl_seconds)
            
            # Store the item
            self.cache[key] = CacheItem(value, expires_at)
    
    def delete(self, key):
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            
            return False
    
    def clear(self):
        """
        Clear all items from the cache.
        """
        with self.lock:
            self.cache.clear()
    
    def get_stats(self):
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary of cache statistics
        """
        with self.lock:
            total_items = len(self.cache)
            expired_items = sum(1 for item in self.cache.values() if item.is_expired())
            
            if total_items > 0:
                avg_age = sum(item.get_age_seconds() for item in self.cache.values()) / total_items
                avg_access_count = sum(item.access_count for item in self.cache.values()) / total_items
            else:
                avg_age = 0
                avg_access_count = 0
            
            return {
                'total_items': total_items,
                'expired_items': expired_items,
                'max_size': self.max_size,
                'utilization': total_items / self.max_size if self.max_size > 0 else 0,
                'avg_age_seconds': avg_age,
                'avg_access_count': avg_access_count
            }
    
    def _evict_lru_item(self):
        """
        Evict the least recently used item from the cache.
        """
        if not self.cache:
            return
        
        # Find the least recently used item
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed_at)
        
        # Remove it
        del self.cache[lru_key]
    
    def _cleanup_expired(self):
        """
        Remove all expired items from the cache.
        """
        now = datetime.utcnow()
        keys_to_delete = [
            key for key, item in self.cache.items()
            if item.is_expired()
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        return len(keys_to_delete)
    
    def _cleanup_loop(self):
        """
        Background thread for periodic cleanup of expired items.
        """
        while True:
            time.sleep(self.cleanup_interval_seconds)
            
            try:
                with self.lock:
                    removed_count = self._cleanup_expired()
                
                if removed_count > 0:
                    logger.debug(f"Cache cleanup: removed {removed_count} expired items")
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")

def cache_key(*args, **kwargs):
    """
    Generate a cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Convert args and kwargs to a string representation
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # Join parts and hash
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()

def memoize(ttl_seconds=300, max_size=1000):
    """
    Decorator to memoize a function with expiration.
    
    Args:
        ttl_seconds: Time-to-live for cache items in seconds
        max_size: Maximum number of items to cache
        
    Returns:
        Decorated function
    """
    cache = MemoryCache(max_size=max_size, default_ttl_seconds=ttl_seconds)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # Generate cache key
            key = cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result)
            
            return result
        
        # Add cache reference to function for manual invalidation
        wrapped.cache = cache
        wrapped.invalidate = lambda *args, **kwargs: cache.delete(cache_key(func.__name__, *args, **kwargs))
        wrapped.invalidate_all = cache.clear
        
        return wrapped
    
    return decorator

class DiskCache:
    """
    Disk-based cache implementation for larger objects.
    """
    
    def __init__(self, cache_dir, max_size_bytes=1024*1024*100, default_ttl_seconds=3600):
        """
        Initialize the disk cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_size_bytes: Maximum total size of cache in bytes
            default_ttl_seconds: Default time-to-live for cache items in seconds
        """
        import os
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_bytes
        self.default_ttl_seconds = default_ttl_seconds
        self.lock = threading.RLock()
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key):
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            File path
        """
        import os
        # Use hash of key as filename
        filename = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, filename)
    
    def get(self, key, default=None):
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        import os
        
        with self.lock:
            cache_path = self._get_cache_path(key)
            
            # Check if file exists
            if not os.path.exists(cache_path):
                return default
            
            try:
                # Read metadata and value
                with open(cache_path, 'rb') as f:
                    metadata = pickle.load(f)
                    value = pickle.load(f)
                
                # Check if expired
                if metadata.get('expires_at') and datetime.utcnow() > metadata['expires_at']:
                    os.remove(cache_path)
                    return default
                
                # Update access metadata
                metadata['last_accessed_at'] = datetime.utcnow()
                metadata['access_count'] += 1
                
                # Write updated metadata
                with open(cache_path, 'wb') as f:
                    pickle.dump(metadata, f)
                    pickle.dump(value, f)
                
                return value
            except Exception as e:
                logger.error(f"Error reading cache file {cache_path}: {str(e)}")
                
                # Remove corrupted file
                try:
                    os.remove(cache_path)
                except:
                    pass
                
                return default
    
    def set(self, key, value, ttl_seconds=None):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional time-to-live in seconds
        """
        import os
        
        with self.lock:
            # Check if we need to clean up
            self._cleanup_if_needed()
            
            cache_path = self._get_cache_path(key)
            
            # Calculate expiration time
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            elif self.default_ttl_seconds is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=self.default_ttl_seconds)
            
            # Create metadata
            metadata = {
                'key': key,
                'created_at': datetime.utcnow(),
                'last_accessed_at': datetime.utcnow(),
                'expires_at': expires_at,
                'access_count': 0
            }
            
            # Write metadata and value
            with open(cache_path, 'wb') as f:
                pickle.dump(metadata, f)
                pickle.dump(value, f)
    
    def delete(self, key):
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        import os
        
        with self.lock:
            cache_path = self._get_cache_path(key)
            
            # Check if file exists
            if not os.path.exists(cache_path):
                return False
            
            # Remove file
            os.remove(cache_path)
            return True
    
    def clear(self):
        """
        Clear all items from the cache.
        """
        import os
        import glob
        
        with self.lock:
            # Remove all files in cache directory
            for cache_file in glob.glob(os.path.join(self.cache_dir, '*')):
                try:
                    os.remove(cache_file)
                except Exception as e:
                    logger.error(f"Error removing cache file {cache_file}: {str(e)}")
    
    def _get_cache_size(self):
        """
        Get the total size of the cache in bytes.
        
        Returns:
            Total size in bytes
        """
        import os
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.cache_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
        
        return total_size
    
    def _cleanup_if_needed(self):
        """
        Clean up the cache if it exceeds the maximum size.
        """
        import os
        import glob
        
        # Check current size
        current_size = self._get_cache_size()
        
        # If we're under the limit, no need to clean up
        if current_size <= self.max_size_bytes:
            return
        
        # Get all cache files with their metadata
        cache_files = []
        for cache_file in glob.glob(os.path.join(self.cache_dir, '*')):
            try:
                with open(cache_file, 'rb') as f:
                    metadata = pickle.load(f)
                    
                    # Skip to next file position
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                
                cache_files.append({
                    'path': cache_file,
                    'size': file_size,
                    'last_accessed_at': metadata.get('last_accessed_at', datetime.min),
                    'access_count': metadata.get('access_count', 0)
                })
            except Exception as e:
                logger.error(f"Error reading cache file {cache_file}: {str(e)}")
                
                # Remove corrupted file
                try:
                    os.remove(cache_file)
                except:
                    pass
        
        # Sort by last accessed time (oldest first)
        cache_files.sort(key=lambda x: x['last_accessed_at'])
        
        # Remove files until we're under the limit
        target_size = self.max_size_bytes * 0.8  # Aim for 80% of max size
        for file_info in cache_files:
            if current_size <= target_size:
                break
            
            try:
                os.remove(file_info['path'])
                current_size -= file_info['size']
            except Exception as e:
                logger.error(f"Error removing cache file {file_info['path']}: {str(e)}")

# Create global cache instances
memory_cache = MemoryCache()
disk_cache = None  # Initialized on first use

def get_disk_cache():
    """
    Get the global disk cache instance.
    
    Returns:
        DiskCache instance
    """
    global disk_cache
    
    if disk_cache is None:
        import os
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        disk_cache = DiskCache(cache_dir)
    
    return disk_cache
