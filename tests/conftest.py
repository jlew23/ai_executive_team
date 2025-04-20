"""
Test configuration for the AI Executive Team application.
"""

import os
import sys
import pytest
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load test environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.test'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable verbose logs during tests
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)

def pytest_configure(config):
    """
    Configure pytest.
    """
    # Register custom markers
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "e2e: mark a test as an end-to-end test")
    config.addinivalue_line("markers", "performance: mark a test as a performance test")
    config.addinivalue_line("markers", "security: mark a test as a security test")
    
    # Set test environment variable
    os.environ['APP_ENV'] = 'test'

@pytest.fixture(scope='session')
def app():
    """
    Create a Flask application for testing.
    """
    from web_dashboard import create_app
    app = create_app(testing=True)
    
    # Create application context
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    """
    Set up the database for testing.
    """
    from web_dashboard import db as _db
    
    # Create tables
    _db.create_all()
    
    yield _db
    
    # Clean up
    _db.session.close()
    _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """
    Create a new database session for a test.
    """
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to the connection
    session = db.create_scoped_session(
        options=dict(bind=connection, binds={})
    )
    
    # Override the session
    db.session = session
    
    yield session
    
    # Clean up
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope='function')
def client(app):
    """
    Create a test client for the application.
    """
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def auth_client(app, client):
    """
    Create an authenticated test client.
    """
    from web_dashboard.models import User
    from web_dashboard import db
    
    # Create a test user
    user = User(
        username='testuser',
        email='test@example.com',
        is_admin=True
    )
    user.set_password('password')
    
    db.session.add(user)
    db.session.commit()
    
    # Log in
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password'
    }, follow_redirects=True)
    
    yield client
    
    # Clean up
    db.session.delete(user)
    db.session.commit()

@pytest.fixture(scope='function')
def mock_openai():
    """
    Mock the OpenAI API.
    """
    import openai
    from unittest.mock import patch, MagicMock
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mock response from OpenAI."
    
    # Patch the OpenAI client
    with patch('openai.ChatCompletion.create', return_value=mock_response):
        yield

@pytest.fixture(scope='function')
def mock_slack():
    """
    Mock the Slack API.
    """
    from unittest.mock import patch, MagicMock
    
    # Create mock client
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {'ok': True, 'message': {'text': 'Mock message'}}
    
    # Patch the Slack client
    with patch('slack.client.WebClient', return_value=mock_client):
        yield mock_client

@pytest.fixture(scope='function')
def base_agent():
    """
    Create a base agent for testing.
    """
    from agents.base_agent import BaseAgent
    
    agent = BaseAgent(name="Test Agent")
    yield agent

@pytest.fixture(scope='function')
def director_agent():
    """
    Create a director agent for testing.
    """
    from agents.director_agent import DirectorAgent
    
    agent = DirectorAgent()
    yield agent

@pytest.fixture(scope='function')
def knowledge_base():
    """
    Create a knowledge base for testing.
    """
    from knowledge_base.base import KnowledgeBase
    
    kb = KnowledgeBase()
    yield kb

@pytest.fixture(scope='function')
def vector_store():
    """
    Create a vector store for testing.
    """
    from knowledge_base.vector_store import VectorStore
    
    vs = VectorStore()
    yield vs

@pytest.fixture(scope='function')
def document_processor():
    """
    Create a document processor for testing.
    """
    from knowledge_base.document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    yield processor

@pytest.fixture(scope='function')
def llm_provider():
    """
    Create an LLM provider for testing.
    """
    from llm.openai_provider import OpenAIProvider
    
    provider = OpenAIProvider()
    yield provider

@pytest.fixture(scope='function')
def memory_cache():
    """
    Create a memory cache for testing.
    """
    from utils.caching import MemoryCache
    
    cache = MemoryCache(max_size=100, default_ttl_seconds=60)
    yield cache
    
    # Clean up
    cache.clear()

@pytest.fixture(scope='function')
def task_queue():
    """
    Create a task queue for testing.
    """
    from utils.async_tasks import TaskQueue
    
    queue = TaskQueue(num_workers=1)
    queue.start()
    
    yield queue
    
    # Clean up
    queue.stop()
