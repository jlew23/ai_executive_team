"""
Authentication routes for the web dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from datetime import datetime

from web_dashboard.models import db, User, ApiKey
from web_dashboard.forms.auth import LoginForm, RegisterForm, PasswordResetForm, ProfileForm

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))

def init_login_manager(app):
    """Initialize the login manager with the Flask app."""
    login_manager.init_app(app)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account is inactive. Please contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember.data)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log the login
            logger.info(f'User {user.username} logged in')
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
                
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logger.info(f'User {current_user.username} logged out')
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_active=True
        )
        user.set_password(form.password.data)
        
        # Add user to database
        db.session.add(user)
        db.session.commit()
        
        # Log the registration
        logger.info(f'New user registered: {user.username}')
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle user profile management."""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Update user profile
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        
        # Update password if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
        
        db.session.commit()
        
        # Log the profile update
        logger.info(f'User {current_user.username} updated their profile')
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    # Get user's API keys
    api_keys = ApiKey.query.filter_by(user_id=current_user.id).all()
    
    return render_template('auth/profile.html', form=form, api_keys=api_keys)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset requests."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # In a real application, send a password reset email
            # For this implementation, we'll just log it
            logger.info(f'Password reset requested for user {user.username}')
            
            flash('If your email is registered, you will receive password reset instructions.', 'info')
        else:
            # Don't reveal that the email doesn't exist
            flash('If your email is registered, you will receive password reset instructions.', 'info')
            
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/api-keys/generate', methods=['POST'])
@login_required
def generate_api_key():
    """Generate a new API key for the user."""
    key_name = request.form.get('key_name', 'API Key')
    
    if not key_name:
        flash('API key name is required', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Generate new API key
    api_key = ApiKey(
        key=ApiKey.generate_key(),
        name=key_name,
        user_id=current_user.id,
        is_active=True
    )
    
    db.session.add(api_key)
    db.session.commit()
    
    # Log the API key generation
    logger.info(f'User {current_user.username} generated a new API key: {api_key.name}')
    
    flash(f'API key "{api_key.name}" generated successfully. Please copy it now as it won\'t be shown again: {api_key.key}', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/api-keys/<int:key_id>/revoke', methods=['POST'])
@login_required
def revoke_api_key(key_id):
    """Revoke an API key."""
    api_key = ApiKey.query.filter_by(id=key_id, user_id=current_user.id).first()
    
    if not api_key:
        flash('API key not found', 'danger')
        return redirect(url_for('auth.profile'))
    
    api_key.is_active = False
    db.session.commit()
    
    # Log the API key revocation
    logger.info(f'User {current_user.username} revoked API key: {api_key.name}')
    
    flash(f'API key "{api_key.name}" revoked successfully', 'success')
    return redirect(url_for('auth.profile'))
