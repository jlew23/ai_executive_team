"""
API response optimization utilities for the AI Executive Team application.
"""

import logging
import json
import gzip
import io
import time
import functools
from flask import request, Response, current_app

logger = logging.getLogger(__name__)

def compress_response(response):
    """
    Compress a response using gzip if the client supports it.
    
    Args:
        response: Flask response object
        
    Returns:
        Compressed response if applicable, otherwise original response
    """
    # Check if client accepts gzip encoding
    if 'gzip' not in request.headers.get('Accept-Encoding', ''):
        return response
    
    # Check if response is compressible
    if response.mimetype not in ('text/html', 'text/css', 'text/javascript', 'application/javascript', 
                                'application/json', 'application/xml', 'text/xml'):
        return response
    
    # Check if response is already compressed
    if response.headers.get('Content-Encoding') == 'gzip':
        return response
    
    # Compress response
    compressed_data = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed_data, mode='wb') as f:
        f.write(response.data)
    
    response.data = compressed_data.getvalue()
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.data)
    
    return response

def add_cache_headers(response, max_age=300):
    """
    Add cache control headers to a response.
    
    Args:
        response: Flask response object
        max_age: Cache lifetime in seconds
        
    Returns:
        Response with cache headers
    """
    # Don't cache error responses
    if response.status_code >= 400:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    
    # Add cache headers
    response.headers['Cache-Control'] = f'public, max-age={max_age}'
    
    return response

def jsonify_with_etag(data):
    """
    Create a JSON response with ETag header for conditional requests.
    
    Args:
        data: Data to convert to JSON
        
    Returns:
        Flask response object
    """
    # Convert data to JSON
    json_data = json.dumps(data)
    
    # Generate ETag
    etag = f'W/"{hash(json_data)}"'
    
    # Create response
    response = Response(json_data, mimetype='application/json')
    response.headers['ETag'] = etag
    
    # Check If-None-Match header
    if_none_match = request.headers.get('If-None-Match')
    if if_none_match and if_none_match == etag:
        # Return 304 Not Modified
        return Response(status=304)
    
    return response

def paginate_results(query, page, per_page):
    """
    Paginate query results.
    
    Args:
        query: SQLAlchemy query
        page: Page number (1-based)
        per_page: Number of items per page
        
    Returns:
        Dictionary with pagination information and results
    """
    # Get total count
    total = query.count()
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get items for this page
    items = query.offset(offset).limit(per_page).all()
    
    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': has_next,
        'has_prev': has_prev,
        'next_page': page + 1 if has_next else None,
        'prev_page': page - 1 if has_prev else None
    }

def optimize_json_response(func):
    """
    Decorator to optimize JSON responses with compression and caching.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        # Call the original function
        response = func(*args, **kwargs)
        
        # Apply optimizations
        if isinstance(response, Response) and response.mimetype == 'application/json':
            response = add_cache_headers(response)
            response = compress_response(response)
        
        return response
    
    return wrapped

def timed_response(func):
    """
    Decorator to measure and log response time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        # Record start time
        start_time = time.time()
        
        # Call the original function
        response = func(*args, **kwargs)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log duration
        logger.debug(f"Response time for {func.__name__}: {duration:.3f}s")
        
        # Add timing header if in debug mode
        if current_app.debug:
            if isinstance(response, Response):
                response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    return wrapped

def setup_response_optimization(app):
    """
    Set up response optimization for a Flask application.
    
    Args:
        app: Flask application
    """
    # Add after_request handler for compression
    @app.after_request
    def optimize_response(response):
        # Compress response
        response = compress_response(response)
        
        # Add cache headers for static files
        if request.path.startswith('/static/'):
            response = add_cache_headers(response, max_age=3600)  # 1 hour
        
        return response
    
    logger.info("Response optimization configured")
