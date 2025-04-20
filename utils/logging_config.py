"""
Logging configuration for the AI Executive Team application.
"""

import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(app_name='ai_executive_team', log_dir='/home/ubuntu/ai_executive_team/logs', log_level=logging.INFO):
    """
    Set up logging for the application.
    
    Args:
        app_name: Name of the application
        log_dir: Directory to store log files
        log_level: Logging level
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create file handler for all logs
    log_file = os.path.join(log_dir, f'{app_name}.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Create file handler for error logs
    error_log_file = os.path.join(log_dir, f'{app_name}_error.log')
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(console_handler)
    
    # Log startup message
    logger.info(f"Logging initialized for {app_name} at {datetime.now().isoformat()}")
    
    return logger

class RequestLogger:
    """
    Logger for HTTP requests.
    """
    
    def __init__(self, app_name='ai_executive_team', log_dir='/home/ubuntu/ai_executive_team/logs'):
        """
        Initialize the request logger.
        
        Args:
            app_name: Name of the application
            log_dir: Directory to store log files
        """
        self.logger = logging.getLogger(f'{app_name}.requests')
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s'
        )
        
        # Create file handler
        log_file = os.path.join(log_dir, f'{app_name}_requests.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_request(self, request, user=None):
        """
        Log an HTTP request.
        
        Args:
            request: Flask request object
            user: Optional user object
        """
        # Build log message
        log_data = {
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string,
            'referrer': request.referrer
        }
        
        # Add user info if available
        if user:
            log_data['user_id'] = user.id
            log_data['username'] = user.username
        
        # Log the request
        self.logger.info(f"Request: {log_data}")
    
    def log_response(self, request, response, duration_ms, user=None):
        """
        Log an HTTP response.
        
        Args:
            request: Flask request object
            response: Flask response object
            duration_ms: Request duration in milliseconds
            user: Optional user object
        """
        # Build log message
        log_data = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': duration_ms
        }
        
        # Add user info if available
        if user:
            log_data['user_id'] = user.id
            log_data['username'] = user.username
        
        # Log the response
        self.logger.info(f"Response: {log_data}")

class SecurityLogger:
    """
    Logger for security events.
    """
    
    def __init__(self, app_name='ai_executive_team', log_dir='/home/ubuntu/ai_executive_team/logs'):
        """
        Initialize the security logger.
        
        Args:
            app_name: Name of the application
            log_dir: Directory to store log files
        """
        self.logger = logging.getLogger(f'{app_name}.security')
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler
        log_file = os.path.join(log_dir, f'{app_name}_security.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_login_attempt(self, username, success, ip_address, user_agent):
        """
        Log a login attempt.
        
        Args:
            username: Username used in the login attempt
            success: Whether the login was successful
            ip_address: IP address of the client
            user_agent: User agent of the client
        """
        status = "successful" if success else "failed"
        self.logger.info(f"Login {status} for user {username} from {ip_address} using {user_agent}")
    
    def log_permission_denied(self, user, permission, resource):
        """
        Log a permission denied event.
        
        Args:
            user: User who was denied permission
            permission: Permission that was denied
            resource: Resource that was accessed
        """
        self.logger.warning(f"Permission denied: User {user.username} (ID: {user.id}) attempted to access {resource} without {permission} permission")
    
    def log_csrf_failure(self, request):
        """
        Log a CSRF token validation failure.
        
        Args:
            request: Flask request object
        """
        self.logger.warning(f"CSRF validation failed for {request.method} {request.path} from {request.remote_addr}")
    
    def log_rate_limit_exceeded(self, ip_address, endpoint):
        """
        Log a rate limit exceeded event.
        
        Args:
            ip_address: IP address of the client
            endpoint: Endpoint that was accessed
        """
        self.logger.warning(f"Rate limit exceeded for {ip_address} on {endpoint}")
    
    def log_security_event(self, event_type, details, level=logging.INFO):
        """
        Log a general security event.
        
        Args:
            event_type: Type of security event
            details: Details of the event
            level: Logging level
        """
        self.logger.log(level, f"Security event: {event_type} - {details}")
