"""
Unit tests for the base agent implementation.
"""

import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit
def test_base_agent_initialization(base_agent):
    """Test that the base agent initializes correctly."""
    assert base_agent.name == "Test Agent"
    assert base_agent.is_initialized() == True

@pytest.mark.unit
def test_base_agent_process_message(base_agent):
    """Test that the base agent can process messages."""
    # Mock the _generate_response method
    base_agent._generate_response = MagicMock(return_value={"text": "Test response"})
    
    # Process a message
    response = base_agent.process_message("Hello, agent!")
    
    # Check that _generate_response was called
    base_agent._generate_response.assert_called_once_with("Hello, agent!")
    
    # Check the response
    assert response["text"] == "Test response"

@pytest.mark.unit
def test_base_agent_conversation_memory(base_agent):
    """Test that the base agent maintains conversation memory."""
    # Mock the _generate_response method
    base_agent._generate_response = MagicMock(return_value={"text": "Test response"})
    
    # Process messages in a conversation
    base_agent.process_message("Hello!", conversation_id="test_conv")
    base_agent.process_message("How are you?", conversation_id="test_conv")
    
    # Check that the conversation history is maintained
    history = base_agent.get_conversation_history("test_conv")
    assert len(history) == 4  # 2 user messages + 2 agent responses
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello!"
    assert history[1]["role"] == "agent"
    assert history[1]["content"] == "Test response"
    assert history[2]["role"] == "user"
    assert history[2]["content"] == "How are you?"

@pytest.mark.unit
def test_base_agent_error_handling(base_agent):
    """Test that the base agent handles errors gracefully."""
    # Mock the _generate_response method to raise an exception
    base_agent._generate_response = MagicMock(side_effect=Exception("Test error"))
    
    # Process a message
    response = base_agent.process_message("This will cause an error")
    
    # Check that an error response is returned
    assert "error" in response
    assert response["error"] == "Failed to process message"

@pytest.mark.unit
def test_base_agent_metrics(base_agent):
    """Test that the base agent tracks performance metrics."""
    # Mock the _generate_response method
    base_agent._generate_response = MagicMock(return_value={"text": "Test response"})
    
    # Process some messages
    for i in range(5):
        base_agent.process_message(f"Message {i}")
    
    # Check metrics
    metrics = base_agent.get_metrics()
    assert metrics["total_messages"] == 5
    assert metrics["success_rate"] > 0
    assert "average_response_time" in metrics

@pytest.mark.unit
def test_base_agent_with_knowledge_base(base_agent, knowledge_base):
    """Test that the base agent can use a knowledge base."""
    # Mock the knowledge base search method
    knowledge_base.search = MagicMock(return_value=[
        {"content": "Test content", "document_id": "doc1", "relevance": 0.95}
    ])
    
    # Set the knowledge base for the agent
    base_agent.set_knowledge_base(knowledge_base)
    
    # Mock the _generate_response method
    base_agent._generate_response = MagicMock(return_value={"text": "Response with knowledge"})
    
    # Process a message
    response = base_agent.process_message("What do you know about tests?")
    
    # Check that the knowledge base was searched
    knowledge_base.search.assert_called_once()
    
    # Check that _generate_response was called with context
    args, kwargs = base_agent._generate_response.call_args
    assert "context" in kwargs
    assert kwargs["context"][0]["content"] == "Test content"
