# Developer Guide

This guide provides comprehensive information for developers who want to extend or modify the AI Executive Team system.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Agent System](#agent-system)
5. [Knowledge Base](#knowledge-base)
6. [LLM Integration](#llm-integration)
7. [Slack Integration](#slack-integration)
8. [Web Dashboard](#web-dashboard)
9. [API Development](#api-development)
10. [Testing](#testing)
11. [Performance Optimization](#performance-optimization)
12. [Security Considerations](#security-considerations)
13. [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/ai-executive-team.git
   cd ai-executive-team
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python -m scripts.init_db
   ```

### Running the Development Server

```bash
python main.py
```

For the web dashboard development server:

```bash
cd web_dashboard
npm install
npm run dev
```

## Project Structure

The AI Executive Team project follows a modular structure:

```
ai_executive_team/
├── agents/                 # Agent implementations
│   ├── base_agent.py       # Base agent class
│   ├── director_agent.py   # Director agent implementation
│   ├── sales_agent.py      # Sales agent implementation
│   └── ...
├── api/                    # API implementation
│   ├── routes/             # API route handlers
│   ├── models/             # API data models
│   └── middleware/         # API middleware
├── brain_data/             # Brain data storage
├── config/                 # Configuration files
├── data/                   # Data storage
├── knowledge_base/         # Knowledge base implementation
│   ├── base.py             # Base knowledge base class
│   ├── document_processor.py # Document processing
│   ├── vector_store.py     # Vector storage
│   └── version_manager.py  # Document versioning
├── llm/                    # LLM integration
│   ├── base.py             # Base LLM provider
│   ├── openai_provider.py  # OpenAI integration
│   ├── anthropic_provider.py # Anthropic integration
│   └── ...
├── slack/                  # Slack integration
│   ├── client.py           # Slack client
│   ├── event_handler.py    # Event handling
│   └── ...
├── tests/                  # Test suite
├── utils/                  # Utility functions
│   ├── caching.py          # Caching utilities
│   ├── db_optimization.py  # Database optimization
│   └── ...
├── web_dashboard/          # Web dashboard
│   ├── static/             # Static assets
│   ├── templates/          # HTML templates
│   ├── routes/             # Route handlers
│   └── ...
├── main.py                 # Main application entry point
├── conversational_main.py  # Conversational interface entry point
├── simple_main.py          # Simple interface entry point
├── run_api.py              # API server entry point
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker Compose configuration
└── Dockerfile              # Docker configuration
```

## Core Components

### Configuration System

The configuration system uses environment variables and configuration files to manage application settings.

```python
# Example: Loading configuration
from config import Config

# Access configuration values
api_key = Config.get('OPENAI_API_KEY')
debug_mode = Config.get('DEBUG', default=False, cast=bool)
```

### Database Models

The application uses SQLAlchemy for database operations.

```python
# Example: Defining a model
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Logging

The application uses a structured logging system.

```python
# Example: Using the logger
from utils.logging_config import setup_logging

logger = setup_logging()

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

## Agent System

### Base Agent

The `BaseAgent` class provides the foundation for all specialized agents.

```python
# Example: Creating a custom agent
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, name="Custom Agent", **kwargs):
        super().__init__(name=name, **kwargs)
        
    def process_message(self, message, conversation_id=None):
        # Custom processing logic
        response = self._generate_response(message)
        return response
        
    def _generate_response(self, message):
        # Custom response generation
        return {"text": "This is a custom response"}
```

### Agent Registration

New agents must be registered with the system.

```python
# Example: Registering a custom agent
from agents import register_agent
from custom_agent import CustomAgent

register_agent("custom", CustomAgent)
```

### Conversation Memory

Agents use a conversation memory system to maintain context.

```python
# Example: Accessing conversation memory
from agents.memory import ConversationMemory

memory = ConversationMemory(conversation_id="conv123")
memory.add_message("user", "Hello, how are you?")
memory.add_message("agent", "I'm doing well, thank you!")

# Get conversation history
history = memory.get_history()
```

## Knowledge Base

### Document Processing

The knowledge base supports processing multiple document types.

```python
# Example: Processing a document
from knowledge_base.document_processor import DocumentProcessor

processor = DocumentProcessor()
document_id = processor.process_document(
    file_path="/path/to/document.pdf",
    metadata={"title": "Sales Report", "category": "sales"}
)
```

### Vector Store

The vector store manages embeddings for semantic search.

```python
# Example: Searching the vector store
from knowledge_base.vector_store import VectorStore

vector_store = VectorStore()
results = vector_store.search(
    query="sales targets for Q2",
    filters={"category": "sales"},
    limit=5
)
```

### Custom Document Processors

You can create custom document processors for specialized file types.

```python
# Example: Creating a custom document processor
from knowledge_base.document_processor import BaseDocumentProcessor

class CustomFileProcessor(BaseDocumentProcessor):
    def __init__(self):
        super().__init__()
        self.supported_extensions = [".custom"]
        
    def process(self, file_path, metadata=None):
        # Custom processing logic
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract text and create chunks
        chunks = self._create_chunks(content)
        return chunks
```

## LLM Integration

### LLM Providers

The system supports multiple LLM providers through a unified interface.

```python
# Example: Using an LLM provider
from llm.openai_provider import OpenAIProvider

llm = OpenAIProvider(model="gpt-4")
response = llm.generate(
    prompt="Summarize the sales performance for Q2",
    max_tokens=500,
    temperature=0.7
)
```

### Prompt Templates

The system includes a template engine for LLM prompts.

```python
# Example: Using prompt templates
from llm.prompt_template import PromptTemplate

template = PromptTemplate("""
You are a {{role}} assistant.
User: {{query}}
Assistant:
""")

prompt = template.render(
    role="sales",
    query="What were our top-selling products last quarter?"
)
```

### Context Management

The context manager optimizes token usage for LLM requests.

```python
# Example: Using the context manager
from llm.context_manager import ContextManager

context = ContextManager(max_tokens=4000)
context.add("system", "You are a helpful assistant.")
context.add("user", "What is the capital of France?")
context.add("assistant", "The capital of France is Paris.")
context.add("user", "What about Germany?")

# Get optimized context for the LLM
optimized_messages = context.get_messages()
```

## Slack Integration

### Event Handling

The Slack integration uses an event-driven architecture.

```python
# Example: Creating a custom event handler
from slack.event_handler import register_event_handler

@register_event_handler("message")
def handle_message(event, client):
    # Custom message handling logic
    channel = event["channel"]
    text = event["text"]
    
    # Process the message
    response = "I received your message: " + text
    
    # Send a response
    client.chat_postMessage(channel=channel, text=response)
```

### Interactive Components

The system supports Slack interactive components.

```python
# Example: Handling interactive components
from slack.interactive_handler import register_interactive_handler

@register_interactive_handler("button_click")
def handle_button_click(payload, client):
    # Handle button click
    action_id = payload["actions"][0]["action_id"]
    channel = payload["channel"]["id"]
    
    # Process the action
    if action_id == "approve_button":
        response = "Request approved!"
    else:
        response = "Request denied."
    
    # Send a response
    client.chat_postMessage(channel=channel, text=response)
```

## Web Dashboard

### Route Handlers

The web dashboard uses Flask for route handling.

```python
# Example: Creating a custom route
from flask import Blueprint, render_template, request
from web_dashboard.utils.permissions import requires_permission

custom_bp = Blueprint('custom', __name__)

@custom_bp.route('/custom-page')
@requires_permission('view_custom_page')
def custom_page():
    # Custom page logic
    return render_template('custom_page.html')
```

### API Integration

The web dashboard integrates with the API.

```python
# Example: Making API requests from the dashboard
from web_dashboard.utils.api_client import APIClient

api_client = APIClient()
agents = api_client.get('/agents')
```

### Custom Widgets

You can create custom widgets for the dashboard.

```python
# Example: Creating a custom widget template
# In templates/widgets/custom_widget.html
<div class="widget custom-widget">
    <h3>{{ title }}</h3>
    <div class="widget-content">
        {{ content }}
    </div>
</div>

# In your route handler
@custom_bp.route('/dashboard')
def dashboard():
    return render_template(
        'dashboard.html',
        widgets=[
            {
                'template': 'widgets/custom_widget.html',
                'title': 'Custom Widget',
                'content': 'This is a custom widget'
            }
        ]
    )
```

## API Development

### Creating New Endpoints

The API uses a modular structure for endpoints.

```python
# Example: Creating a new API endpoint
from flask import Blueprint, jsonify, request
from api.middleware import require_auth, validate_json

custom_api = Blueprint('custom_api', __name__)

@custom_api.route('/custom', methods=['POST'])
@require_auth
@validate_json({'name': str, 'value': int})
def custom_endpoint():
    data = request.get_json()
    
    # Process the request
    result = {
        'name': data['name'],
        'value': data['value'] * 2
    }
    
    return jsonify({'success': True, 'data': result})
```

### Response Formatting

The API uses a standard response format.

```python
# Example: Formatting API responses
from api.utils.response import success_response, error_response

# Success response
return success_response(data={'key': 'value'}, message='Operation successful')

# Error response
return error_response(message='Invalid input', status_code=400)
```

## Testing

### Unit Testing

The project uses pytest for unit testing.

```python
# Example: Writing a unit test
import pytest
from agents.base_agent import BaseAgent

def test_base_agent_initialization():
    agent = BaseAgent(name="Test Agent")
    assert agent.name == "Test Agent"
    assert agent.is_initialized() == True
```

### Integration Testing

Integration tests verify the interaction between components.

```python
# Example: Writing an integration test
import pytest
from knowledge_base.vector_store import VectorStore
from knowledge_base.document_processor import DocumentProcessor

@pytest.fixture
def setup_knowledge_base():
    processor = DocumentProcessor()
    vector_store = VectorStore()
    
    # Process a test document
    doc_id = processor.process_document("tests/data/test_document.pdf")
    
    return vector_store, doc_id

def test_document_search(setup_knowledge_base):
    vector_store, doc_id = setup_knowledge_base
    
    # Search for content in the document
    results = vector_store.search("test query")
    
    assert len(results) > 0
    assert results[0]['document_id'] == doc_id
```

### Mocking

The testing framework supports mocking external dependencies.

```python
# Example: Mocking an LLM provider
import pytest
from unittest.mock import patch, MagicMock
from llm.openai_provider import OpenAIProvider

def test_llm_generation():
    # Create a mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mocked response"
    
    # Patch the OpenAI client
    with patch('openai.ChatCompletion.create', return_value=mock_response):
        llm = OpenAIProvider()
        response = llm.generate("Test prompt")
        
        assert response == "Mocked response"
```

## Performance Optimization

### Caching

The system includes utilities for caching.

```python
# Example: Using the caching system
from utils.caching import memoize

@memoize(ttl_seconds=300)
def expensive_operation(param1, param2):
    # Expensive computation
    return result
```

### Database Optimization

The system includes utilities for optimizing database queries.

```python
# Example: Using the optimized query builder
from utils.db_optimization import optimize_query
from models import User

# Create an optimized query
query = optimize_query(User, db.session)
query.with_eager_load(User.roles)
query.with_only_columns(User.id, User.username, User.email)
query.filter_by(is_active=True)

# Execute the query
users = query.all()
```

### Asynchronous Tasks

The system includes utilities for asynchronous task processing.

```python
# Example: Using the async task system
from utils.async_tasks import async_task

@async_task()
def process_large_document(document_id):
    # Long-running task
    # This will run in a background thread
    process_document(document_id)
    
# Call the function
task = process_large_document("doc123")

# Check task status
status = task.status  # 'pending', 'running', 'completed', or 'failed'
```

## Security Considerations

### Input Validation

Always validate user input to prevent injection attacks.

```python
# Example: Validating user input
from utils.security import validate_input

def process_user_data(data):
    # Define validation schema
    schema = {
        'username': {
            'type': 'string',
            'required': True,
            'min_length': 3,
            'max_length': 50,
            'pattern': r'^[a-zA-Z0-9_]+$'
        },
        'email': {
            'type': 'string',
            'required': True,
            'validate': lambda x: '@' in x or 'Invalid email format'
        }
    }
    
    # Validate input
    validated_data = validate_input(data, schema)
    
    # Process validated data
    return process_valid_data(validated_data)
```

### Authentication and Authorization

The system uses a role-based access control system.

```python
# Example: Checking permissions
from web_dashboard.utils.permissions import check_permission

def perform_action(user, action):
    # Check if user has permission
    if not check_permission(user, f'can_{action}'):
        raise AuthorizationError(f"User does not have permission to {action}")
    
    # Perform the action
    return do_action(action)
```

### Error Handling

Always use proper error handling to prevent information leakage.

```python
# Example: Proper error handling
from utils.security import SecurityException

def sensitive_operation():
    try:
        # Perform sensitive operation
        result = perform_operation()
        return result
    except Exception as e:
        # Log the detailed error internally
        logger.error(f"Error in sensitive_operation: {str(e)}")
        
        # Return a generic error message to the user
        raise SecurityException("An error occurred during the operation")
```

## Contributing Guidelines

### Code Style

The project follows the PEP 8 style guide for Python code.

```bash
# Check code style
flake8 .

# Format code
black .
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

### Documentation

All new features should include documentation:

- Code comments
- Function/method docstrings
- Updates to relevant documentation files

### Testing Requirements

All new features should include tests:

- Unit tests for individual components
- Integration tests for component interactions
- End-to-end tests for user workflows
