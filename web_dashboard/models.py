"""
Database models for the web dashboard.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and authorization."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    roles = db.relationship('Role', secondary='user_roles', backref='users')
    api_keys = db.relationship('ApiKey', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set the user's password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if the user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name):
        """Check if the user has a specific permission through any of their roles."""
        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    """Role model for authorization."""
    
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    
    # Relationships
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Permission(db.Model):
    """Permission model for fine-grained access control."""
    
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    
    def __repr__(self):
        return f'<Permission {self.name}>'

class UserRole(db.Model):
    """Association table for User-Role relationship."""
    
    __tablename__ = 'user_roles'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RolePermission(db.Model):
    """Association table for Role-Permission relationship."""
    
    __tablename__ = 'role_permissions'
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ApiKey(db.Model):
    """API key model for API authentication."""
    
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    
    @staticmethod
    def generate_key():
        """Generate a new API key."""
        return str(uuid.uuid4())
    
    def __repr__(self):
        return f'<ApiKey {self.name}>'

class AgentStatus(db.Model):
    """Model for tracking agent status."""
    
    __tablename__ = 'agent_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(64), nullable=False)
    agent_type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False)  # active, idle, error
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)
    metadata = db.Column(db.JSON)
    
    def __repr__(self):
        return f'<AgentStatus {self.agent_id} ({self.status})>'

class Conversation(db.Model):
    """Model for storing conversation history."""
    
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy=True)
    
    def __repr__(self):
        return f'<Conversation {self.conversation_id}>'

class Message(db.Model):
    """Model for storing individual messages in conversations."""
    
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_type = db.Column(db.String(32), nullable=False)  # user, agent, system
    sender_id = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    metadata = db.Column(db.JSON)
    
    def __repr__(self):
        return f'<Message {self.id} from {self.sender_type}>'

class KnowledgeBaseEntry(db.Model):
    """Model for tracking knowledge base entries."""
    
    __tablename__ = 'kb_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    source = db.Column(db.String(256))
    file_path = db.Column(db.String(256))
    file_type = db.Column(db.String(32))
    status = db.Column(db.String(32), nullable=False)  # processing, ready, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    metadata = db.Column(db.JSON)
    
    # Relationships
    versions = db.relationship('KnowledgeBaseVersion', backref='entry', lazy=True)
    
    def __repr__(self):
        return f'<KnowledgeBaseEntry {self.document_id}>'

class KnowledgeBaseVersion(db.Model):
    """Model for tracking versions of knowledge base entries."""
    
    __tablename__ = 'kb_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('kb_entries.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_current = db.Column(db.Boolean, default=True)
    changes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<KnowledgeBaseVersion {self.entry_id} v{self.version}>'

class AnalyticsEvent(db.Model):
    """Model for storing analytics events."""
    
    __tablename__ = 'analytics_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(64), nullable=False)
    event_data = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AnalyticsEvent {self.event_type}>'

class AgentPerformanceMetric(db.Model):
    """Model for storing agent performance metrics."""
    
    __tablename__ = 'agent_performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(64), nullable=False)
    agent_type = db.Column(db.String(64), nullable=False)
    metric_name = db.Column(db.String(64), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    metadata = db.Column(db.JSON)
    
    def __repr__(self):
        return f'<AgentPerformanceMetric {self.agent_id} {self.metric_name}>'

def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Create default roles and permissions if they don't exist
        _create_default_roles_and_permissions()
        
        # Create admin user if it doesn't exist
        _create_admin_user()

def _create_default_roles_and_permissions():
    """Create default roles and permissions."""
    # Create permissions if they don't exist
    permissions = {
        'view_dashboard': 'Access the main dashboard',
        'manage_agents': 'Manage agent configuration and status',
        'view_conversations': 'View conversation history',
        'manage_kb': 'Manage knowledge base entries',
        'view_analytics': 'View analytics and reports',
        'manage_users': 'Manage users and permissions',
        'api_access': 'Access the API',
        'admin': 'Full administrative access'
    }
    
    for perm_name, perm_desc in permissions.items():
        if not Permission.query.filter_by(name=perm_name).first():
            permission = Permission(name=perm_name, description=perm_desc)
            db.session.add(permission)
    
    # Create roles if they don't exist
    roles = {
        'admin': 'Administrator with full access',
        'manager': 'Manager with access to most features',
        'user': 'Regular user with basic access',
        'api': 'API access only'
    }
    
    for role_name, role_desc in roles.items():
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name, description=role_desc)
            db.session.add(role)
    
    db.session.commit()
    
    # Assign permissions to roles
    admin_role = Role.query.filter_by(name='admin').first()
    manager_role = Role.query.filter_by(name='manager').first()
    user_role = Role.query.filter_by(name='user').first()
    api_role = Role.query.filter_by(name='api').first()
    
    # Assign all permissions to admin
    for perm in Permission.query.all():
        if admin_role and perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
    
    # Assign specific permissions to manager
    manager_perms = ['view_dashboard', 'manage_agents', 'view_conversations', 
                     'manage_kb', 'view_analytics']
    for perm_name in manager_perms:
        perm = Permission.query.filter_by(name=perm_name).first()
        if manager_role and perm and perm not in manager_role.permissions:
            manager_role.permissions.append(perm)
    
    # Assign specific permissions to user
    user_perms = ['view_dashboard', 'view_conversations']
    for perm_name in user_perms:
        perm = Permission.query.filter_by(name=perm_name).first()
        if user_role and perm and perm not in user_role.permissions:
            user_role.permissions.append(perm)
    
    # Assign API permission to API role
    api_perm = Permission.query.filter_by(name='api_access').first()
    if api_role and api_perm and api_perm not in api_role.permissions:
        api_role.permissions.append(api_perm)
    
    db.session.commit()

def _create_admin_user():
    """Create admin user if it doesn't exist."""
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_admin=True,
            is_active=True
        )
        admin_user.set_password('admin')  # Default password, should be changed
        
        # Assign admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            admin_user.roles.append(admin_role)
        
        db.session.add(admin_user)
        db.session.commit()
