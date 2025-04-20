"""
Unit tests for the web dashboard components.
"""

import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit
def test_dashboard_routes(client):
    """Test that the dashboard routes are accessible."""
    # Test the index route
    response = client.get('/')
    assert response.status_code == 200
    
    # Test the login route
    response = client.get('/login')
    assert response.status_code == 200
    
    # Test the dashboard route (should redirect to login)
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

@pytest.mark.unit
def test_dashboard_authenticated_routes(auth_client):
    """Test that authenticated routes are accessible when logged in."""
    # Test the dashboard route
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    
    # Test the agents route
    response = auth_client.get('/agents')
    assert response.status_code == 200
    
    # Test the knowledge base route
    response = auth_client.get('/knowledge-base')
    assert response.status_code == 200
    
    # Test the analytics route
    response = auth_client.get('/analytics')
    assert response.status_code == 200

@pytest.mark.unit
def test_user_authentication(client, db):
    """Test user authentication."""
    from web_dashboard.models import User
    
    # Create a test user
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password')
    
    db.session.add(user)
    db.session.commit()
    
    # Test login with correct credentials
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    
    # Test login with incorrect credentials
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrong_password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data
    
    # Test logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

@pytest.mark.unit
def test_user_registration(client, db):
    """Test user registration."""
    # Test registration with valid data
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password',
        'confirm_password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data
    
    # Check that the user was created
    from web_dashboard.models import User
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    assert user.email == 'newuser@example.com'
    
    # Test registration with existing username
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'another@example.com',
        'password': 'password',
        'confirm_password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Username already exists' in response.data
    
    # Test registration with mismatched passwords
    response = client.post('/register', data={
        'username': 'anotheruser',
        'email': 'another@example.com',
        'password': 'password1',
        'confirm_password': 'password2'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Passwords must match' in response.data

@pytest.mark.unit
def test_agent_routes(auth_client):
    """Test the agent routes."""
    # Test the agent list route
    response = auth_client.get('/agents')
    assert response.status_code == 200
    
    # Test the agent detail route
    response = auth_client.get('/agents/director')
    assert response.status_code == 200
    
    # Test the agent configuration route
    response = auth_client.get('/agents/director/config')
    assert response.status_code == 200

@pytest.mark.unit
def test_knowledge_base_routes(auth_client):
    """Test the knowledge base routes."""
    # Test the knowledge base list route
    response = auth_client.get('/knowledge-base')
    assert response.status_code == 200
    
    # Test the document upload route
    response = auth_client.get('/knowledge-base/upload')
    assert response.status_code == 200
    
    # Test the document search route
    response = auth_client.get('/knowledge-base/search?query=test')
    assert response.status_code == 200

@pytest.mark.unit
def test_analytics_routes(auth_client):
    """Test the analytics routes."""
    # Test the analytics dashboard route
    response = auth_client.get('/analytics')
    assert response.status_code == 200
    
    # Test the agent performance route
    response = auth_client.get('/analytics/agents/director')
    assert response.status_code == 200
    
    # Test the conversation analytics route
    response = auth_client.get('/analytics/conversations')
    assert response.status_code == 200
    
    # Test the knowledge base analytics route
    response = auth_client.get('/analytics/knowledge-base')
    assert response.status_code == 200

@pytest.mark.unit
def test_api_routes(auth_client):
    """Test the API routes."""
    # Test the agents API route
    response = auth_client.get('/api/agents')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    
    # Test the conversations API route
    response = auth_client.get('/api/conversations')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    
    # Test the knowledge base API route
    response = auth_client.get('/api/knowledge-base/documents')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

@pytest.mark.unit
def test_permissions_system():
    """Test the permissions system."""
    from web_dashboard.utils.permissions import check_permission, require_permission
    
    # Create a mock user
    user = MagicMock()
    user.roles = [MagicMock()]
    user.roles[0].permissions = ['view_dashboard', 'view_agents']
    
    # Test permission checking
    assert check_permission(user, 'view_dashboard') == True
    assert check_permission(user, 'view_agents') == True
    assert check_permission(user, 'edit_agents') == False
    
    # Test the require_permission decorator
    @require_permission('view_dashboard')
    def test_function(user):
        return 'Function executed'
    
    # Test with permitted user
    result = test_function(user)
    assert result == 'Function executed'
    
    # Test with non-permitted user
    user.roles[0].permissions = ['view_agents']
    with pytest.raises(Exception):
        test_function(user)

@pytest.mark.unit
def test_form_validation():
    """Test form validation."""
    from web_dashboard.utils.validation import validate_form
    
    # Define a schema
    schema = {
        'username': {
            'required': True,
            'min_length': 3,
            'max_length': 20
        },
        'email': {
            'required': True,
            'pattern': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        },
        'age': {
            'required': False,
            'type': 'integer',
            'min': 18,
            'max': 120
        }
    }
    
    # Test valid data
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'age': '25'
    }
    errors = validate_form(data, schema)
    assert len(errors) == 0
    
    # Test invalid username
    data = {
        'username': 'te',
        'email': 'test@example.com',
        'age': '25'
    }
    errors = validate_form(data, schema)
    assert len(errors) == 1
    assert 'username' in errors
    
    # Test invalid email
    data = {
        'username': 'testuser',
        'email': 'invalid-email',
        'age': '25'
    }
    errors = validate_form(data, schema)
    assert len(errors) == 1
    assert 'email' in errors
    
    # Test invalid age
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'age': '17'
    }
    errors = validate_form(data, schema)
    assert len(errors) == 1
    assert 'age' in errors
    
    # Test missing required field
    data = {
        'username': 'testuser',
        'age': '25'
    }
    errors = validate_form(data, schema)
    assert len(errors) == 1
    assert 'email' in errors
