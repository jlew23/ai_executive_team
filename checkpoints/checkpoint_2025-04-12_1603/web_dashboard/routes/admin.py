"""
Admin routes for the web dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
import logging
from datetime import datetime

from web_dashboard.models import db, User, Role, Permission, UserRole, RolePermission
from web_dashboard.utils.permissions import requires_permission
from web_dashboard.forms.admin import UserForm, RoleForm

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@requires_permission('admin')
def index():
    """Render the admin dashboard page."""
    # Get counts for various entities
    user_count = User.query.count()
    role_count = Role.query.count()
    permission_count = Permission.query.count()
    
    return render_template(
        'admin/index.html',
        user_count=user_count,
        role_count=role_count,
        permission_count=permission_count
    )

@admin_bp.route('/users')
@login_required
@requires_permission('admin')
def users():
    """Render the user management page."""
    # Get all users
    users = User.query.all()
    
    return render_template(
        'admin/users.html',
        users=users
    )

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@requires_permission('admin')
def new_user():
    """Create a new user."""
    form = UserForm()
    
    # Get all roles for the form
    roles = Role.query.all()
    form.roles.choices = [(role.id, role.name) for role in roles]
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return render_template('admin/user_form.html', form=form, title='New User')
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'danger')
            return render_template('admin/user_form.html', form=form, title='New User')
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        
        # Add user to database
        db.session.add(user)
        db.session.commit()
        
        # Assign roles
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                user_role = UserRole(user_id=user.id, role_id=role.id)
                db.session.add(user_role)
        
        db.session.commit()
        
        # Log the user creation
        logger.info(f'User {user.username} created by admin {current_user.username}')
        
        flash(f'User {user.username} created successfully', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template(
        'admin/user_form.html',
        form=form,
        title='New User'
    )

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin')
def edit_user(user_id):
    """Edit a user."""
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    # Get all roles for the form
    roles = Role.query.all()
    form.roles.choices = [(role.id, role.name) for role in roles]
    
    # Set current roles
    if request.method == 'GET':
        form.roles.data = [role.id for role in user.roles]
    
    if form.validate_on_submit():
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        # Update password if provided
        if form.password.data:
            user.set_password(form.password.data)
        
        # Update roles
        # First, remove all current roles
        UserRole.query.filter_by(user_id=user.id).delete()
        
        # Then, add selected roles
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                user_role = UserRole(user_id=user.id, role_id=role.id)
                db.session.add(user_role)
        
        db.session.commit()
        
        # Log the user update
        logger.info(f'User {user.username} updated by admin {current_user.username}')
        
        flash(f'User {user.username} updated successfully', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template(
        'admin/user_form.html',
        form=form,
        title='Edit User',
        user=user
    )

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@requires_permission('admin')
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.users'))
    
    # Delete user roles
    UserRole.query.filter_by(user_id=user.id).delete()
    
    # Delete user
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    # Log the user deletion
    logger.info(f'User {username} deleted by admin {current_user.username}')
    
    flash(f'User {username} deleted successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/roles')
@login_required
@requires_permission('admin')
def roles():
    """Render the role management page."""
    # Get all roles
    roles = Role.query.all()
    
    return render_template(
        'admin/roles.html',
        roles=roles
    )

@admin_bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@requires_permission('admin')
def new_role():
    """Create a new role."""
    form = RoleForm()
    
    # Get all permissions for the form
    permissions = Permission.query.all()
    form.permissions.choices = [(perm.id, perm.name) for perm in permissions]
    
    if form.validate_on_submit():
        # Check if role name already exists
        if Role.query.filter_by(name=form.name.data).first():
            flash('Role name already exists', 'danger')
            return render_template('admin/role_form.html', form=form, title='New Role')
        
        # Create new role
        role = Role(
            name=form.name.data,
            description=form.description.data
        )
        
        # Add role to database
        db.session.add(role)
        db.session.commit()
        
        # Assign permissions
        for perm_id in form.permissions.data:
            perm = Permission.query.get(perm_id)
            if perm:
                role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                db.session.add(role_perm)
        
        db.session.commit()
        
        # Log the role creation
        logger.info(f'Role {role.name} created by admin {current_user.username}')
        
        flash(f'Role {role.name} created successfully', 'success')
        return redirect(url_for('admin.roles'))
    
    return render_template(
        'admin/role_form.html',
        form=form,
        title='New Role'
    )

@admin_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin')
def edit_role(role_id):
    """Edit a role."""
    role = Role.query.get_or_404(role_id)
    form = RoleForm(obj=role)
    
    # Get all permissions for the form
    permissions = Permission.query.all()
    form.permissions.choices = [(perm.id, perm.name) for perm in permissions]
    
    # Set current permissions
    if request.method == 'GET':
        form.permissions.data = [perm.id for perm in role.permissions]
    
    if form.validate_on_submit():
        # Update role
        role.name = form.name.data
        role.description = form.description.data
        
        # Update permissions
        # First, remove all current permissions
        RolePermission.query.filter_by(role_id=role.id).delete()
        
        # Then, add selected permissions
        for perm_id in form.permissions.data:
            perm = Permission.query.get(perm_id)
            if perm:
                role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                db.session.add(role_perm)
        
        db.session.commit()
        
        # Log the role update
        logger.info(f'Role {role.name} updated by admin {current_user.username}')
        
        flash(f'Role {role.name} updated successfully', 'success')
        return redirect(url_for('admin.roles'))
    
    return render_template(
        'admin/role_form.html',
        form=form,
        title='Edit Role',
        role=role
    )

@admin_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@requires_permission('admin')
def delete_role(role_id):
    """Delete a role."""
    role = Role.query.get_or_404(role_id)
    
    # Delete role permissions
    RolePermission.query.filter_by(role_id=role.id).delete()
    
    # Delete user roles
    UserRole.query.filter_by(role_id=role.id).delete()
    
    # Delete role
    role_name = role.name
    db.session.delete(role)
    db.session.commit()
    
    # Log the role deletion
    logger.info(f'Role {role_name} deleted by admin {current_user.username}')
    
    flash(f'Role {role_name} deleted successfully', 'success')
    return redirect(url_for('admin.roles'))

@admin_bp.route('/permissions')
@login_required
@requires_permission('admin')
def permissions():
    """Render the permission management page."""
    # Get all permissions
    permissions = Permission.query.all()
    
    return render_template(
        'admin/permissions.html',
        permissions=permissions
    )

@admin_bp.route('/system-settings')
@login_required
@requires_permission('admin')
def system_settings():
    """Render the system settings page."""
    # In a real implementation, this would load settings from a database or config file
    # For now, we'll just render a template with the current configuration
    
    return render_template(
        'admin/system_settings.html',
        config=vars(type('obj', (object,), {
            'DEBUG': False,
            'TESTING': False,
            'SECRET_KEY': '***',
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'PERMANENT_SESSION_LIFETIME': '1 day',
            'DATABASE_URI': '***',
            'API_TOKEN_EXPIRATION': '30 days',
            'UPLOAD_FOLDER': '/tmp/ai_executive_team_uploads',
            'MAX_CONTENT_LENGTH': '16 MB',
            'LOG_LEVEL': 'INFO',
            'AGENT_TIMEOUT': '30 seconds',
            'DEFAULT_LLM_PROVIDER': 'openai',
            'DEFAULT_LLM_MODEL': 'gpt-4',
            'KB_STORAGE_PATH': '/tmp/ai_executive_team_kb',
            'ANALYTICS_RETENTION_DAYS': '90'
        }))
    )

@admin_bp.route('/api/users')
@login_required
@requires_permission('admin')
def api_users():
    """API endpoint to get all users."""
    users = User.query.all()
    
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'roles': [role.name for role in user.roles]
        })
    
    return jsonify(user_list)

@admin_bp.route('/api/roles')
@login_required
@requires_permission('admin')
def api_roles():
    """API endpoint to get all roles."""
    roles = Role.query.all()
    
    role_list = []
    for role in roles:
        role_list.append({
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'permissions': [perm.name for perm in role.permissions],
            'user_count': len(role.users)
        })
    
    return jsonify(role_list)

@admin_bp.route('/api/permissions')
@login_required
@requires_permission('admin')
def api_permissions():
    """API endpoint to get all permissions."""
    permissions = Permission.query.all()
    
    perm_list = []
    for perm in permissions:
        perm_list.append({
            'id': perm.id,
            'name': perm.name,
            'description': perm.description,
            'role_count': len(perm.roles)
        })
    
    return jsonify(perm_list)
