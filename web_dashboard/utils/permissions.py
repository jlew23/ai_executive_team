"""
Permission utilities for the AI Executive Team application.
"""

import logging
import functools
from flask import abort, g, current_app
from flask_login import current_user

logger = logging.getLogger(__name__)

def requires_permission(permission_name):
    """
    Decorator to require a specific permission for a route.
    
    Args:
        permission_name: Name of the required permission
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                logger.warning(f"Unauthenticated user attempted to access {permission_name} protected route")
                abort(401)
            
            # Check if user has the required permission
            if not current_user.has_permission(permission_name):
                logger.warning(f"User {current_user.username} attempted to access {permission_name} protected route without permission")
                abort(403)
            
            return f(*args, **kwargs)
        
        return wrapped
    
    return decorator

def requires_role(role_name):
    """
    Decorator to require a specific role for a route.
    
    Args:
        role_name: Name of the required role
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                logger.warning(f"Unauthenticated user attempted to access {role_name} protected route")
                abort(401)
            
            # Check if user has the required role
            if not current_user.has_role(role_name):
                logger.warning(f"User {current_user.username} attempted to access {role_name} protected route without role")
                abort(403)
            
            return f(*args, **kwargs)
        
        return wrapped
    
    return decorator

def check_permission(user, permission_name):
    """
    Check if a user has a specific permission.
    
    Args:
        user: User object to check
        permission_name: Name of the permission to check
        
    Returns:
        True if user has the permission, False otherwise
    """
    # Admin users have all permissions
    if user.is_admin:
        return True
    
    # Check if user has the permission through any of their roles
    return user.has_permission(permission_name)

def check_role(user, role_name):
    """
    Check if a user has a specific role.
    
    Args:
        user: User object to check
        role_name: Name of the role to check
        
    Returns:
        True if user has the role, False otherwise
    """
    # Admin users have all roles implicitly
    if user.is_admin and role_name != 'admin':
        return True
    
    # Check if user has the role
    return user.has_role(role_name)

def get_user_permissions(user):
    """
    Get all permissions for a user.
    
    Args:
        user: User object to check
        
    Returns:
        Set of permission names
    """
    # Admin users have all permissions
    if user.is_admin:
        from web_dashboard.models import Permission
        return {perm.name for perm in Permission.query.all()}
    
    # Get permissions from user's roles
    permissions = set()
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.name)
    
    return permissions

def get_user_roles(user):
    """
    Get all roles for a user.
    
    Args:
        user: User object to check
        
    Returns:
        Set of role names
    """
    return {role.name for role in user.roles}
