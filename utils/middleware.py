"""
Error handling middleware for the AI Executive Team application.
"""

import logging
import traceback
from functools import wraps
from flask import request, jsonify, current_app, g
from werkzeug.exceptions import HTTPException

from utils.security import SecurityException, RateLimitExceeded, InvalidInput, AuthorizationError

logger = logging.getLogger(__name__)

def setup_error_handlers(app):
    """
    Set up error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global exception handler for the application."""
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
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors."""
        if request.path.startswith('/api/'):
            # Return JSON for API routes
            response = {
                'error': True,
                'message': 'Resource not found',
                'status_code': 404
            }
            return jsonify(response), 404
        
        # Return HTML for web routes
        return app.render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 errors."""
        if request.path.startswith('/api/'):
            # Return JSON for API routes
            response = {
                'error': True,
                'message': 'Access forbidden',
                'status_code': 403
            }
            return jsonify(response), 403
        
        # Return HTML for web routes
        return app.render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors."""
        if request.path.startswith('/api/'):
            # Return JSON for API routes
            response = {
                'error': True,
                'message': 'Internal server error',
                'status_code': 500
            }
            return jsonify(response), 500
        
        # Return HTML for web routes
        return app.render_template('errors/500.html'), 500

def setup_request_logging(app):
    """
    Set up request logging for the Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def log_request_info():
        """Log information about the current request."""
        # Don't log static file requests
        if request.path.startswith('/static'):
            return
        
        # Log request details
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        
        # Log user info if available
        if hasattr(g, 'user') and g.user:
            logger.info(f"User: {g.user.username} (ID: {g.user.id})")

def setup_response_headers(app):
    """
    Set up security headers for all responses.
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def add_security_headers(response):
        """Add security headers to the response."""
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Enable XSS protection in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Strict Transport Security
        if not current_app.config.get('DEBUG', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy
        response.headers['Feature-Policy'] = "geolocation 'none'; microphone 'none'; camera 'none'"
        
        return response

def setup_csrf_protection(app):
    """
    Set up CSRF protection for the Flask application.
    
    Args:
        app: Flask application instance
    """
    from utils.security import generate_csrf_token, verify_csrf_token
    
    # Make CSRF token available in templates
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf_token()}
    
    # Verify CSRF token for state-changing requests
    @app.before_request
    def csrf_protect():
        # Skip for GET, HEAD, OPTIONS, TRACE requests
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return
        
        # Skip for API routes that use token authentication
        if request.path.startswith('/api/'):
            return
        
        # Get token from form or header
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        
        if not verify_csrf_token(token):
            logger.warning(f"CSRF validation failed for {request.method} {request.path}")
            return app.render_template('errors/403.html'), 403

def setup_rate_limiting(app):
    """
    Set up rate limiting for the Flask application.
    
    Args:
        app: Flask application instance
    """
    from utils.security import RateLimiter, RateLimitExceeded
    
    # Create rate limiters for different endpoints
    api_limiter = RateLimiter(max_requests=100, window_seconds=60)
    login_limiter = RateLimiter(max_requests=5, window_seconds=60)
    
    @app.before_request
    def check_rate_limit():
        # Apply different rate limits based on the endpoint
        try:
            if request.path.startswith('/api/'):
                api_limiter.check(request.remote_addr)
            elif request.path == '/login' and request.method == 'POST':
                login_limiter.check(request.remote_addr)
        except RateLimitExceeded:
            logger.warning(f"Rate limit exceeded for {request.remote_addr} on {request.path}")
            
            if request.path.startswith('/api/'):
                response = {
                    'error': True,
                    'message': 'Rate limit exceeded. Please try again later.',
                    'status_code': 429
                }
                return jsonify(response), 429
            else:
                return app.render_template('errors/429.html'), 429

def setup_all_middleware(app):
    """
    Set up all middleware for the Flask application.
    
    Args:
        app: Flask application instance
    """
    setup_error_handlers(app)
    setup_request_logging(app)
    setup_response_headers(app)
    setup_csrf_protection(app)
    setup_rate_limiting(app)
