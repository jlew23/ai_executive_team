"""
Integration tests for the AI Executive Team application.
"""

import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.integration
def test_agent_with_knowledge_base_integration(base_agent, knowledge_base, vector_store, document_processor):
    """Test the integration between agents and the knowledge base."""
    # Set up the knowledge base with the vector store
    knowledge_base.vector_store = vector_store
    
    # Mock the embedding function
    vector_store._get_embedding = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
    
    # Add some test data to the vector store
    vector_store.add(
        texts=["Sales targets for Q2 are $2.5M", "Marketing budget for Q2 is $500K"],
        metadatas=[
            {"document_id": "doc1", "title": "Sales Report", "page": 1},
            {"document_id": "doc2", "title": "Marketing Plan", "page": 5}
        ],
        ids=["chunk1", "chunk2"]
    )
    
    # Set the knowledge base for the agent
    base_agent.set_knowledge_base(knowledge_base)
    
    # Mock the _generate_response method to return the context
    base_agent._generate_response = MagicMock(
        side_effect=lambda message, conversation_id=None, context=None: {
            "text": f"Response with context: {context[0]['text'] if context else 'No context'}"
        }
    )
    
    # Process a message that should trigger knowledge base search
    response = base_agent.process_message("What are the sales targets for Q2?")
    
    # Check that the knowledge base was used
    assert "Sales targets for Q2 are $2.5M" in response["text"]

@pytest.mark.integration
def test_agent_with_llm_integration(base_agent, llm_provider, mock_openai):
    """Test the integration between agents and LLM providers."""
    # Set the LLM provider for the agent
    base_agent.llm_provider = llm_provider
    
    # Override the _generate_response method to use the LLM provider
    def generate_response(message, conversation_id=None, context=None):
        prompt = f"User: {message}\nContext: {context if context else 'None'}\nAssistant:"
        response_text = llm_provider.generate(prompt)
        return {"text": response_text}
    
    base_agent._generate_response = generate_response
    
    # Process a message
    response = base_agent.process_message("Hello, how are you?")
    
    # Check that the LLM provider was used
    assert response["text"] == "This is a mock response from OpenAI."

@pytest.mark.integration
def test_agent_with_slack_integration(base_agent, mock_slack):
    """Test the integration between agents and Slack."""
    from slack.client import SlackClient
    
    # Create a Slack client
    slack_client = SlackClient(bot_token="xoxb-test-token")
    
    # Create a handler function that uses the agent
    def handle_message(event):
        message = event["text"]
        channel = event["channel"]
        
        # Process the message with the agent
        response = base_agent.process_message(message)
        
        # Send the response to Slack
        slack_client.send_message(channel=channel, text=response["text"])
    
    # Mock the agent's _generate_response method
    base_agent._generate_response = MagicMock(return_value={"text": "This is a response from the agent"})
    
    # Create a test event
    event = {
        "type": "message",
        "channel": "C12345",
        "user": "U12345",
        "text": "Hello, agent!",
        "ts": "1234567890.123456"
    }
    
    # Handle the event
    handle_message(event)
    
    # Check that the agent processed the message
    base_agent._generate_response.assert_called_once_with("Hello, agent!")
    
    # Check that the response was sent to Slack
    mock_slack.chat_postMessage.assert_called_once_with(
        channel="C12345",
        text="This is a response from the agent"
    )

@pytest.mark.integration
def test_web_dashboard_with_agent_integration(auth_client, base_agent):
    """Test the integration between the web dashboard and agents."""
    # Mock the agent manager to return our test agent
    with patch('web_dashboard.routes.agents.get_agent', return_value=base_agent):
        # Mock the agent's process_message method
        base_agent.process_message = MagicMock(return_value={"text": "This is a response from the agent"})
        
        # Send a message to an agent via the API
        response = auth_client.post('/api/agents/test/message', json={
            "message": "Hello, agent!",
            "conversation_id": "test_conv"
        })
        
        # Check the response
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] == True
        assert data["data"]["text"] == "This is a response from the agent"
        
        # Check that the agent was called correctly
        base_agent.process_message.assert_called_once_with("Hello, agent!", conversation_id="test_conv")

@pytest.mark.integration
def test_knowledge_base_with_document_processor_integration(knowledge_base, document_processor, vector_store):
    """Test the integration between the knowledge base and document processor."""
    import tempfile
    import os
    
    # Set up the knowledge base with the vector store
    knowledge_base.vector_store = vector_store
    document_processor.vector_store = vector_store
    
    # Mock the embedding function
    vector_store._get_embedding = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
    
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
        temp.write(b"This is a test document about sales targets.\nThe Q2 target is $2.5M.\nThis is important information.")
        temp_path = temp.name
    
    try:
        # Process the document
        document_id = document_processor.process_document(
            file_path=temp_path,
            metadata={"title": "Sales Targets", "category": "sales"}
        )
        
        # Search the knowledge base
        results = knowledge_base.search("What are the sales targets?")
        
        # Check the results
        assert len(results) > 0
        assert "sales targets" in results[0]["text"].lower()
        assert results[0]["metadata"]["document_id"] == document_id
    finally:
        # Clean up
        os.unlink(temp_path)

@pytest.mark.integration
def test_director_agent_with_specialized_agents_integration(director_agent):
    """Test the integration between the director agent and specialized agents."""
    # Create mock specialized agents
    sales_agent = MagicMock()
    sales_agent.name = "Sales Agent"
    sales_agent.process_message.return_value = {"text": "This is a response from the Sales Agent"}
    
    marketing_agent = MagicMock()
    marketing_agent.name = "Marketing Agent"
    marketing_agent.process_message.return_value = {"text": "This is a response from the Marketing Agent"}
    
    # Register the specialized agents with the director
    director_agent.register_agent("sales", sales_agent)
    director_agent.register_agent("marketing", marketing_agent)
    
    # Process a sales-related message
    response1 = director_agent.process_message("What are our sales targets?")
    
    # Check that the sales agent was used
    sales_agent.process_message.assert_called_once()
    assert response1["text"] == "This is a response from the Sales Agent"
    
    # Process a marketing-related message
    response2 = director_agent.process_message("What is our marketing budget?")
    
    # Check that the marketing agent was used
    marketing_agent.process_message.assert_called_once()
    assert response2["text"] == "This is a response from the Marketing Agent"

@pytest.mark.integration
def test_llm_with_context_manager_integration(llm_provider, mock_openai):
    """Test the integration between LLM providers and the context manager."""
    from llm.context_manager import ContextManager
    
    # Create a context manager
    context = ContextManager(max_tokens=1000)
    
    # Add messages to the context
    context.add("system", "You are a helpful assistant.")
    context.add("user", "What is the capital of France?")
    context.add("assistant", "The capital of France is Paris.")
    context.add("user", "What about Germany?")
    
    # Get the optimized messages
    messages = context.get_messages()
    
    # Use the LLM provider with the context
    prompt = ""
    for message in messages:
        prompt += f"{message['role']}: {message['content']}\n"
    
    response = llm_provider.generate(prompt)
    
    # Check the response
    assert response == "This is a mock response from OpenAI."

@pytest.mark.integration
def test_web_dashboard_with_knowledge_base_integration(auth_client, knowledge_base, vector_store):
    """Test the integration between the web dashboard and knowledge base."""
    # Set up the knowledge base with the vector store
    knowledge_base.vector_store = vector_store
    
    # Mock the embedding function
    vector_store._get_embedding = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
    
    # Add some test data to the vector store
    vector_store.add(
        texts=["Sales targets for Q2 are $2.5M", "Marketing budget for Q2 is $500K"],
        metadatas=[
            {"document_id": "doc1", "title": "Sales Report", "page": 1},
            {"document_id": "doc2", "title": "Marketing Plan", "page": 5}
        ],
        ids=["chunk1", "chunk2"]
    )
    
    # Mock the knowledge base search function
    with patch('web_dashboard.routes.knowledge_base.get_knowledge_base', return_value=knowledge_base):
        # Search the knowledge base via the API
        response = auth_client.get('/api/knowledge-base/search?query=sales+targets')
        
        # Check the response
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] == True
        assert len(data["data"]["items"]) > 0
        assert "Sales targets for Q2 are $2.5M" in data["data"]["items"][0]["text"]
