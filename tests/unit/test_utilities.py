"""
Unit tests for the utility components.
"""

import pytest
from unittest.mock import MagicMock, patch
import time

@pytest.mark.unit
def test_memory_cache(memory_cache):
    """Test the memory cache implementation."""
    # Add items to the cache
    memory_cache.set("key1", "value1")
    memory_cache.set("key2", "value2", ttl_seconds=10)
    
    # Get items from the cache
    assert memory_cache.get("key1") == "value1"
    assert memory_cache.get("key2") == "value2"
    assert memory_cache.get("key3") is None
    
    # Test default value
    assert memory_cache.get("key3", default="default") == "default"
    
    # Test contains
    assert "key1" in memory_cache
    assert "key3" not in memory_cache
    
    # Test delete
    memory_cache.delete("key1")
    assert "key1" not in memory_cache
    
    # Test clear
    memory_cache.clear()
    assert "key2" not in memory_cache

@pytest.mark.unit
def test_memory_cache_expiration():
    """Test that cache items expire correctly."""
    from utils.caching import MemoryCache
    
    cache = MemoryCache(max_size=10, default_ttl_seconds=1)
    
    # Add an item with a 1-second TTL
    cache.set("key1", "value1")
    
    # Check that it exists
    assert "key1" in cache
    
    # Wait for it to expire
    time.sleep(1.1)
    
    # Check that it's gone
    assert "key1" not in cache

@pytest.mark.unit
def test_memory_cache_max_size():
    """Test that the cache respects max size."""
    from utils.caching import MemoryCache
    
    cache = MemoryCache(max_size=2)
    
    # Add items to the cache
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    # Both should be in the cache
    assert "key1" in cache
    assert "key2" in cache
    
    # Add another item, which should evict the oldest
    cache.set("key3", "value3")
    
    # key1 should be gone, key2 and key3 should remain
    assert "key1" not in cache
    assert "key2" in cache
    assert "key3" in cache

@pytest.mark.unit
def test_memoize_decorator():
    """Test the memoize decorator."""
    from utils.caching import memoize
    
    # Create a mock function with the memoize decorator
    mock_func = MagicMock(return_value="result")
    decorated_func = memoize(ttl_seconds=10)(mock_func)
    
    # Call the function multiple times with the same arguments
    result1 = decorated_func("arg1", "arg2", kwarg1="kwarg1")
    result2 = decorated_func("arg1", "arg2", kwarg1="kwarg1")
    
    # Check that the results are correct
    assert result1 == "result"
    assert result2 == "result"
    
    # Check that the function was only called once
    assert mock_func.call_count == 1
    
    # Call with different arguments
    result3 = decorated_func("arg1", "arg3", kwarg1="kwarg1")
    
    # Check that the function was called again
    assert mock_func.call_count == 2

@pytest.mark.unit
def test_task_queue(task_queue):
    """Test the asynchronous task queue."""
    # Create a mock task
    mock_task = MagicMock()
    
    # Submit the task
    future = task_queue.submit(mock_task, "arg1", "arg2", kwarg1="kwarg1")
    
    # Wait for the task to complete
    result = future.result(timeout=1)
    
    # Check that the task was called with the correct arguments
    mock_task.assert_called_once_with("arg1", "arg2", kwarg1="kwarg1")

@pytest.mark.unit
def test_task_queue_exception_handling(task_queue):
    """Test that the task queue handles exceptions correctly."""
    # Create a task that raises an exception
    def failing_task():
        raise ValueError("Task failed")
    
    # Submit the task
    future = task_queue.submit(failing_task)
    
    # Wait for the task to complete and check the exception
    with pytest.raises(ValueError, match="Task failed"):
        future.result(timeout=1)

@pytest.mark.unit
def test_db_optimization():
    """Test the database optimization utilities."""
    from utils.db_optimization import optimize_query
    from sqlalchemy.orm import Query
    
    # Create a mock session and query
    mock_session = MagicMock()
    mock_query = MagicMock(spec=Query)
    mock_session.query.return_value = mock_query
    
    # Mock the filter, order_by, and limit methods
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    
    # Create a mock model
    mock_model = MagicMock()
    
    # Optimize the query
    optimized = optimize_query(mock_model, mock_session)
    
    # Check that the optimized query has the expected methods
    assert hasattr(optimized, 'filter_by')
    assert hasattr(optimized, 'with_eager_load')
    assert hasattr(optimized, 'with_only_columns')
    assert hasattr(optimized, 'paginate')
    
    # Test the methods
    optimized.filter_by(id=1)
    mock_query.filter.assert_called_once()
    
    optimized.paginate(page=1, per_page=10)
    mock_query.limit.assert_called_once_with(10)

@pytest.mark.unit
def test_security_input_validation():
    """Test the security input validation utilities."""
    from utils.security import validate_input
    
    # Define a schema
    schema = {
        'username': {
            'type': 'string',
            'required': True,
            'min_length': 3,
            'max_length': 20,
            'pattern': r'^[a-zA-Z0-9_]+$'
        },
        'email': {
            'type': 'string',
            'required': True,
            'validate': lambda x: '@' in x or 'Invalid email format'
        },
        'age': {
            'type': 'integer',
            'required': False,
            'min': 18,
            'max': 120
        }
    }
    
    # Test valid data
    valid_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'age': 25
    }
    
    result, errors = validate_input(valid_data, schema)
    assert result is True
    assert len(errors) == 0
    
    # Test invalid data
    invalid_data = {
        'username': 'te$t',  # Invalid character
        'email': 'invalid-email',  # Missing @
        'age': 15  # Below minimum
    }
    
    result, errors = validate_input(invalid_data, schema)
    assert result is False
    assert len(errors) == 3
    assert 'username' in errors
    assert 'email' in errors
    assert 'age' in errors

@pytest.mark.unit
def test_security_sanitize_html():
    """Test the HTML sanitization utility."""
    from utils.security import sanitize_html
    
    # Test basic sanitization
    html = '<p>This is <b>bold</b> text.</p><script>alert("XSS")</script>'
    sanitized = sanitize_html(html)
    
    # Script tag should be removed
    assert '<script>' not in sanitized
    assert 'alert("XSS")' not in sanitized
    
    # Allowed tags should remain
    assert '<p>' in sanitized
    assert '<b>' in sanitized
    
    # Test with custom allowed tags
    sanitized = sanitize_html(html, allowed_tags=['p'])
    assert '<p>' in sanitized
    assert '<b>' not in sanitized

@pytest.mark.unit
def test_logging_config():
    """Test the logging configuration."""
    from utils.logging_config import setup_logging
    import logging
    
    # Set up logging
    logger = setup_logging(log_level='INFO')
    
    # Check that the logger is configured correctly
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    
    # Test logging at different levels
    with patch.object(logger, 'info') as mock_info:
        logger.info('Info message')
        mock_info.assert_called_once_with('Info message')
    
    with patch.object(logger, 'error') as mock_error:
        logger.error('Error message')
        mock_error.assert_called_once_with('Error message')
    
    with patch.object(logger, 'debug') as mock_debug:
        logger.debug('Debug message')
        mock_debug.assert_called_once_with('Debug message')

@pytest.mark.unit
def test_response_optimization():
    """Test the response optimization utilities."""
    from utils.response_optimization import compress_response, add_cache_headers
    
    # Test response compression
    mock_response = MagicMock()
    mock_response.data = b'This is a test response'
    
    compress_response(mock_response)
    
    # Check that the response was compressed
    assert 'Content-Encoding' in mock_response.headers
    assert mock_response.headers['Content-Encoding'] == 'gzip'
    
    # Test cache headers
    mock_response = MagicMock()
    mock_response.headers = {}
    
    add_cache_headers(mock_response, max_age=3600)
    
    # Check that cache headers were added
    assert 'Cache-Control' in mock_response.headers
    assert 'max-age=3600' in mock_response.headers['Cache-Control']
    assert 'ETag' in mock_response.headers
