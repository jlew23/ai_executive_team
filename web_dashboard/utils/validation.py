"""
Input validation utilities for the AI Executive Team application.
"""

import re
import logging
from utils.security import InvalidInput

logger = logging.getLogger(__name__)

class Validator:
    """
    Utility class for validating input data.
    """
    
    @staticmethod
    def validate_email(email):
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, error message otherwise
        """
        if not email:
            return "Email address is required"
        
        # Basic email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return "Invalid email address format"
        
        return True
    
    @staticmethod
    def validate_username(username):
        """
        Validate a username.
        
        Args:
            username: Username to validate
            
        Returns:
            True if valid, error message otherwise
        """
        if not username:
            return "Username is required"
        
        if len(username) < 3:
            return "Username must be at least 3 characters long"
        
        if len(username) > 30:
            return "Username must be at most 30 characters long"
        
        # Only allow alphanumeric characters, underscores, and hyphens
        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, username):
            return "Username can only contain letters, numbers, underscores, and hyphens"
        
        return True
    
    @staticmethod
    def validate_password(password):
        """
        Validate a password.
        
        Args:
            password: Password to validate
            
        Returns:
            True if valid, error message otherwise
        """
        if not password:
            return "Password is required"
        
        if len(password) < 8:
            return "Password must be at least 8 characters long"
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            return "Password must contain at least one uppercase letter"
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            return "Password must contain at least one lowercase letter"
        
        # Check for at least one digit
        if not re.search(r'[0-9]', password):
            return "Password must contain at least one digit"
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return "Password must contain at least one special character"
        
        return True
    
    @staticmethod
    def validate_name(name, field_name="Name"):
        """
        Validate a name (first name, last name, etc.).
        
        Args:
            name: Name to validate
            field_name: Name of the field for error messages
            
        Returns:
            True if valid, error message otherwise
        """
        if not name:
            return f"{field_name} is required"
        
        if len(name) > 50:
            return f"{field_name} must be at most 50 characters long"
        
        # Allow letters, spaces, hyphens, and apostrophes
        pattern = r'^[a-zA-Z\s\'-]+$'
        if not re.match(pattern, name):
            return f"{field_name} can only contain letters, spaces, hyphens, and apostrophes"
        
        return True
    
    @staticmethod
    def validate_url(url):
        """
        Validate a URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, error message otherwise
        """
        if not url:
            return "URL is required"
        
        # Basic URL validation pattern
        pattern = r'^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        if not re.match(pattern, url):
            return "Invalid URL format"
        
        return True
    
    @staticmethod
    def validate_date(date_str, format="%Y-%m-%d"):
        """
        Validate a date string.
        
        Args:
            date_str: Date string to validate
            format: Expected date format
            
        Returns:
            True if valid, error message otherwise
        """
        if not date_str:
            return "Date is required"
        
        try:
            from datetime import datetime
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return f"Invalid date format, expected {format}"
    
    @staticmethod
    def validate_integer(value, min_value=None, max_value=None):
        """
        Validate an integer value.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            True if valid, error message otherwise
        """
        if value is None:
            return "Value is required"
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return "Value must be an integer"
        
        if min_value is not None and int_value < min_value:
            return f"Value must be at least {min_value}"
        
        if max_value is not None and int_value > max_value:
            return f"Value must be at most {max_value}"
        
        return True
    
    @staticmethod
    def validate_float(value, min_value=None, max_value=None):
        """
        Validate a float value.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            True if valid, error message otherwise
        """
        if value is None:
            return "Value is required"
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return "Value must be a number"
        
        if min_value is not None and float_value < min_value:
            return f"Value must be at least {min_value}"
        
        if max_value is not None and float_value > max_value:
            return f"Value must be at most {max_value}"
        
        return True
    
    @staticmethod
    def validate_boolean(value):
        """
        Validate a boolean value.
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid, error message otherwise
        """
        if value is None:
            return "Value is required"
        
        if not isinstance(value, bool):
            return "Value must be a boolean"
        
        return True
    
    @staticmethod
    def validate_choice(value, choices):
        """
        Validate that a value is one of the allowed choices.
        
        Args:
            value: Value to validate
            choices: List of allowed choices
            
        Returns:
            True if valid, error message otherwise
        """
        if value is None:
            return "Value is required"
        
        if value not in choices:
            return f"Value must be one of: {', '.join(map(str, choices))}"
        
        return True
    
    @staticmethod
    def validate_length(value, min_length=None, max_length=None):
        """
        Validate the length of a string or list.
        
        Args:
            value: Value to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            
        Returns:
            True if valid, error message otherwise
        """
        if value is None:
            return "Value is required"
        
        try:
            length = len(value)
        except (TypeError, AttributeError):
            return "Value must be a string or list"
        
        if min_length is not None and length < min_length:
            return f"Value must be at least {min_length} characters long"
        
        if max_length is not None and length > max_length:
            return f"Value must be at most {max_length} characters long"
        
        return True
    
    @staticmethod
    def validate_file_extension(filename, allowed_extensions):
        """
        Validate a file extension.
        
        Args:
            filename: Filename to validate
            allowed_extensions: List of allowed extensions
            
        Returns:
            True if valid, error message otherwise
        """
        if not filename:
            return "Filename is required"
        
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if extension not in allowed_extensions:
            return f"File extension must be one of: {', '.join(allowed_extensions)}"
        
        return True
    
    @staticmethod
    def validate_file_size(file_size, max_size_bytes):
        """
        Validate a file size.
        
        Args:
            file_size: File size in bytes
            max_size_bytes: Maximum allowed size in bytes
            
        Returns:
            True if valid, error message otherwise
        """
        if file_size is None:
            return "File size is required"
        
        if file_size > max_size_bytes:
            # Convert to more readable format
            if max_size_bytes >= 1024 * 1024:
                max_size_str = f"{max_size_bytes / (1024 * 1024):.1f} MB"
            elif max_size_bytes >= 1024:
                max_size_str = f"{max_size_bytes / 1024:.1f} KB"
            else:
                max_size_str = f"{max_size_bytes} bytes"
                
            return f"File size must be at most {max_size_str}"
        
        return True

def validate_form_data(form_data, validation_rules):
    """
    Validate form data against a set of validation rules.
    
    Args:
        form_data: Dictionary of form data
        validation_rules: Dictionary of validation rules
        
    Returns:
        Dictionary of validated data
        
    Raises:
        InvalidInput: If validation fails
    """
    validated_data = {}
    errors = {}
    
    for field, rules in validation_rules.items():
        # Check if field is required
        if rules.get('required', False) and field not in form_data:
            errors[field] = f"{field} is required"
            continue
        
        # Skip validation if field is not present and not required
        if field not in form_data:
            continue
        
        value = form_data[field]
        
        # Apply validation functions
        if 'validate' in rules:
            validate_func = rules['validate']
            result = validate_func(value)
            
            if result is not True:
                errors[field] = result
                continue
        
        # Add validated field to result
        validated_data[field] = value
    
    # Raise exception if validation errors occurred
    if errors:
        error_messages = [f"{field}: {message}" for field, message in errors.items()]
        raise InvalidInput('\n'.join(error_messages))
    
    return validated_data
