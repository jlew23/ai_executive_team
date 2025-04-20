"""
Error handling and security utilities for the AI Executive Team application.
"""

import logging
import traceback
import functools
import re
import hashlib
import secrets
import json
from datetime import datetime
from flask import request, jsonify, current_app, g, abort
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class SecurityException(Exception):
    """Base exception for security-related issues."""
    pass

class RateLimitExceeded(SecurityException):
    """Exception raised when rate limit is exceeded."""
    pass

class InvalidInput(SecurityException):
    """Exception raised when input validation fails."""
    pass

class AuthorizationError(SecurityException):
    """Exception raised when authorization fails."""
    pass

def handle_exception(e):
    """
    Global exception handler for the application.
    
    Args:
        e: The exception that was raised
        
    Returns:
        JSON response with error details
    """
    # Log the exception
    logger.error(f"Exception occurred: {str(e)}")
    logger.error(traceback.format_exc())
    
    # Handle different types of exceptions
    if isinstance(e, HTTPException):
        response = {
            'error': True,
            'message': e.description,
            'status_code': e.code
        }
        return jsonify(response), e.code
    
    if isinstance(e, SecurityException):
        if isinstance(e, RateLimitExceeded):
            response = {
                'error': True,
                'message': 'Rate limit exceeded. Please try again later.',
                'status_code': 429
            }
            return jsonify(response), 429
        
        if isinstance(e, InvalidInput):
            response = {
                'error': True,
                'message': str(e),
                'status_code': 400
            }
            return jsonify(response), 400
        
        if isinstance(e, AuthorizationError):
            response = {
                'error': True,
                'message': 'Unauthorized access',
                'status_code': 403
            }
            return jsonify(response), 403
    
    # Default error response for unhandled exceptions
    response = {
        'error': True,
        'message': 'An unexpected error occurred',
        'status_code': 500
    }
    
    # In development mode, include more details
    if current_app.config.get('DEBUG', False):
        response['exception'] = str(e)
        response['traceback'] = traceback.format_exc()
    
    return jsonify(response), 500

def log_request():
    """Log details about the current request."""
    # Don't log static file requests
    if request.path.startswith('/static'):
        return
    
    # Create log entry
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'referrer': request.referrer
    }
    
    # Add user info if available
    if hasattr(g, 'user') and g.user:
        log_data['user_id'] = g.user.id
        log_data['username'] = g.user.username
    
    # Log the request
    logger.info(f"Request: {json.dumps(log_data)}")

def sanitize_input(data, allowed_tags=None):
    """
    Sanitize input data to prevent XSS attacks.
    
    Args:
        data: String input to sanitize
        allowed_tags: List of allowed HTML tags, or None to strip all tags
        
    Returns:
        Sanitized string
    """
    if not isinstance(data, str):
        return data
    
    # Strip all HTML tags if no allowed tags specified
    if allowed_tags is None:
        return re.sub(r'<[^>]*>', '', data)
    
    # Otherwise, only allow specified tags
    allowed_tags_pattern = '|'.join(allowed_tags)
    pattern = f'<(?!/?({allowed_tags_pattern}))[^>]*>'
    return re.sub(pattern, '', data)

def validate_input(data, schema):
    """
    Validate input data against a schema.
    
    Args:
        data: Input data to validate
        schema: Dictionary defining validation rules
        
    Returns:
        Validated data
        
    Raises:
        InvalidInput: If validation fails
    """
    validated = {}
    errors = []
    
    for field, rules in schema.items():
        # Check if field is required
        if rules.get('required', False) and field not in data:
            errors.append(f"Field '{field}' is required")
            continue
        
        # Skip validation if field is not present and not required
        if field not in data:
            continue
        
        value = data[field]
        
        # Check field type
        if 'type' in rules:
            expected_type = rules['type']
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Field '{field}' must be an array")
            elif expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Field '{field}' must be an object")
        
        # Check minimum length
        if 'min_length' in rules and isinstance(value, str) and len(value) < rules['min_length']:
            errors.append(f"Field '{field}' must be at least {rules['min_length']} characters long")
        
        # Check maximum length
        if 'max_length' in rules and isinstance(value, str) and len(value) > rules['max_length']:
            errors.append(f"Field '{field}' must be at most {rules['max_length']} characters long")
        
        # Check minimum value
        if 'min_value' in rules and isinstance(value, (int, float)) and value < rules['min_value']:
            errors.append(f"Field '{field}' must be at least {rules['min_value']}")
        
        # Check maximum value
        if 'max_value' in rules and isinstance(value, (int, float)) and value > rules['max_value']:
            errors.append(f"Field '{field}' must be at most {rules['max_value']}")
        
        # Check pattern
        if 'pattern' in rules and isinstance(value, str) and not re.match(rules['pattern'], value):
            errors.append(f"Field '{field}' does not match the required pattern")
        
        # Check enum
        if 'enum' in rules and value not in rules['enum']:
            errors.append(f"Field '{field}' must be one of: {', '.join(map(str, rules['enum']))}")
        
        # Apply custom validation function
        if 'validate' in rules and callable(rules['validate']):
            try:
                result = rules['validate'](value)
                if result is not True:
                    errors.append(result or f"Field '{field}' failed validation")
            except Exception as e:
                errors.append(f"Field '{field}' validation error: {str(e)}")
        
        # Sanitize if specified
        if 'sanitize' in rules and rules['sanitize'] and isinstance(value, str):
            value = sanitize_input(value, rules.get('allowed_tags'))
        
        # Add validated field to result
        validated[field] = value
    
    # Raise exception if validation errors occurred
    if errors:
        raise InvalidInput('\n'.join(errors))
    
    return validated

class RateLimiter:
    """
    Rate limiter to prevent abuse of API endpoints.
    """
    
    def __init__(self, max_requests=100, window_seconds=60):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def check(self, key):
        """
        Check if a request is allowed for the given key.
        
        Args:
            key: Identifier for the client (e.g., IP address)
            
        Returns:
            True if request is allowed, False otherwise
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        now = datetime.utcnow()
        
        # Initialize or clean up request history for this key
        if key not in self.requests:
            self.requests[key] = []
        else:
            # Remove requests outside the time window
            self.requests[key] = [
                timestamp for timestamp in self.requests[key]
                if (now - timestamp).total_seconds() < self.window_seconds
            ]
        
        # Check if rate limit is exceeded
        if len(self.requests[key]) >= self.max_requests:
            raise RateLimitExceeded()
        
        # Add current request to history
        self.requests[key].append(now)
        
        return True

def rate_limit(max_requests=100, window_seconds=60, key_func=None):
    """
    Decorator to apply rate limiting to a route.
    
    Args:
        max_requests: Maximum number of requests allowed in the time window
        window_seconds: Time window in seconds
        key_func: Function to generate the rate limit key (defaults to IP address)
        
    Returns:
        Decorated function
    """
    limiter = RateLimiter(max_requests, window_seconds)
    
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Get rate limit key
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr
            
            # Check rate limit
            limiter.check(key)
            
            # Call the original function
            return f(*args, **kwargs)
        
        return wrapped
    
    return decorator

def generate_csrf_token():
    """
    Generate a CSRF token.
    
    Returns:
        CSRF token string
    """
    if 'csrf_token' not in g:
        g.csrf_token = secrets.token_hex(16)
    
    return g.csrf_token

def verify_csrf_token(token):
    """
    Verify a CSRF token.
    
    Args:
        token: CSRF token to verify
        
    Returns:
        True if token is valid, False otherwise
    """
    if not token or 'csrf_token' not in g:
        return False
    
    return token == g.csrf_token

def require_csrf(f):
    """
    Decorator to require CSRF token for a route.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        # Only check POST, PUT, PATCH, DELETE requests
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            
            if not verify_csrf_token(token):
                abort(403, description="CSRF token validation failed")
        
        return f(*args, **kwargs)
    
    return wrapped

def hash_password(password, salt=None):
    """
    Hash a password using PBKDF2.
    
    Args:
        password: Password to hash
        salt: Optional salt, generated if not provided
        
    Returns:
        Tuple of (hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 with SHA-256
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000,  # Number of iterations
        dklen=32  # Length of the derived key
    )
    
    # Convert binary hash to hexadecimal
    hash_hex = key.hex()
    
    return hash_hex, salt

def verify_password(password, hash_hex, salt):
    """
    Verify a password against a hash.
    
    Args:
        password: Password to verify
        hash_hex: Stored password hash
        salt: Salt used for hashing
        
    Returns:
        True if password matches, False otherwise
    """
    # Hash the provided password with the same salt
    new_hash, _ = hash_password(password, salt)
    
    # Compare the hashes
    return new_hash == hash_hex

def encrypt_data(data, key):
    """
    Encrypt data using AES.
    
    Args:
        data: Data to encrypt
        key: Encryption key
        
    Returns:
        Encrypted data
    """
    # This is a placeholder for actual encryption implementation
    # In a real application, use a library like cryptography
    return data

def decrypt_data(encrypted_data, key):
    """
    Decrypt data using AES.
    
    Args:
        encrypted_data: Data to decrypt
        key: Encryption key
        
    Returns:
        Decrypted data
    """
    # This is a placeholder for actual decryption implementation
    # In a real application, use a library like cryptography
    return encrypted_data
