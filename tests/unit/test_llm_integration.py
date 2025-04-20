"""
Unit tests for the LLM integration components.
"""

import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit
def test_llm_provider_initialization(llm_provider):
    """Test that the LLM provider initializes correctly."""
    assert llm_provider is not None
    assert hasattr(llm_provider, 'generate')
    assert hasattr(llm_provider, 'get_model_name')

@pytest.mark.unit
def test_llm_provider_generate(llm_provider, mock_openai):
    """Test that the LLM provider can generate responses."""
    # Generate a response
    response = llm_provider.generate(
        prompt="This is a test prompt",
        max_tokens=100,
        temperature=0.7
    )
    
    # Check the response
    assert response == "This is a mock response from OpenAI."

@pytest.mark.unit
def test_prompt_template():
    """Test the prompt template system."""
    from llm.prompt_template import PromptTemplate
    
    # Create a template
    template = PromptTemplate("""
    You are a {{role}} assistant.
    User: {{query}}
    Assistant:
    """)
    
    # Render the template
    prompt = template.render(
        role="helpful",
        query="What is the capital of France?"
    )
    
    # Check the rendered prompt
    assert "You are a helpful assistant." in prompt
    assert "User: What is the capital of France?" in prompt
    assert "Assistant:" in prompt

@pytest.mark.unit
def test_prompt_template_conditional():
    """Test conditional sections in prompt templates."""
    from llm.prompt_template import PromptTemplate
    
    # Create a template with conditional section
    template = PromptTemplate("""
    You are a {{role}} assistant.
    {% if context %}
    Here is some context: {{context}}
    {% endif %}
    User: {{query}}
    Assistant:
    """)
    
    # Render with context
    prompt1 = template.render(
        role="helpful",
        query="What is the capital of France?",
        context="France is a country in Europe."
    )
    
    # Render without context
    prompt2 = template.render(
        role="helpful",
        query="What is the capital of France?"
    )
    
    # Check the rendered prompts
    assert "Here is some context: France is a country in Europe." in prompt1
    assert "Here is some context:" not in prompt2

@pytest.mark.unit
def test_context_manager():
    """Test the context manager for token optimization."""
    from llm.context_manager import ContextManager
    
    # Create a context manager
    context = ContextManager(max_tokens=100)
    
    # Add messages
    context.add("system", "You are a helpful assistant.")
    context.add("user", "What is the capital of France?")
    context.add("assistant", "The capital of France is Paris.")
    context.add("user", "What about Germany?")
    
    # Get optimized messages
    messages = context.get_messages()
    
    # Check the messages
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a helpful assistant."
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "What is the capital of France?"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "The capital of France is Paris."
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "What about Germany?"

@pytest.mark.unit
def test_context_manager_pruning():
    """Test that the context manager prunes messages when over token limit."""
    from llm.context_manager import ContextManager
    
    # Mock the token counting function to return 50 tokens for each message
    with patch('llm.context_manager.ContextManager._count_tokens', return_value=50):
        # Create a context manager with max 100 tokens
        context = ContextManager(max_tokens=100)
        
        # Add messages (total 150 tokens, over the limit)
        context.add("system", "You are a helpful assistant.")
        context.add("user", "What is the capital of France?")
        context.add("assistant", "The capital of France is Paris.")
        
        # Get optimized messages
        messages = context.get_messages()
        
        # Check that messages were pruned
        assert len(messages) == 2
        assert messages[0]["role"] == "system"  # System message should be preserved
        assert messages[1]["role"] == "user"  # Most recent user message should be preserved

@pytest.mark.unit
def test_anthropic_provider():
    """Test the Anthropic provider."""
    from llm.anthropic_provider import AnthropicProvider
    
    # Mock the Anthropic client
    with patch('anthropic.Anthropic') as mock_anthropic:
        # Mock the completion method
        mock_instance = mock_anthropic.return_value
        mock_instance.completions.create.return_value.completion = "This is a mock response from Anthropic."
        
        # Create the provider
        provider = AnthropicProvider(model="claude-2")
        
        # Generate a response
        response = provider.generate(
            prompt="This is a test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        # Check the response
        assert response == "This is a mock response from Anthropic."
        
        # Check that the client was called correctly
        mock_instance.completions.create.assert_called_once()
        args, kwargs = mock_instance.completions.create.call_args
        assert kwargs["prompt"].endswith("This is a test prompt")
        assert kwargs["max_tokens_to_sample"] == 100
        assert kwargs["temperature"] == 0.7

@pytest.mark.unit
def test_huggingface_provider():
    """Test the HuggingFace provider."""
    from llm.huggingface_provider import HuggingFaceProvider
    
    # Mock the HuggingFace client
    with patch('requests.post') as mock_post:
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"generated_text": "This is a mock response from HuggingFace."}]
        mock_post.return_value = mock_response
        
        # Create the provider
        provider = HuggingFaceProvider(model="gpt2")
        
        # Generate a response
        response = provider.generate(
            prompt="This is a test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        # Check the response
        assert response == "This is a mock response from HuggingFace."
        
        # Check that the client was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "This is a test prompt" in str(kwargs["json"])

@pytest.mark.unit
def test_local_provider():
    """Test the Local provider."""
    from llm.local_provider import LocalProvider
    
    # Mock the llama_cpp.Llama class
    with patch('llama_cpp.Llama') as mock_llama:
        # Mock the completion method
        mock_instance = mock_llama.return_value
        mock_instance.create_completion.return_value = {
            "choices": [{"text": "This is a mock response from a local model."}]
        }
        
        # Create the provider
        provider = LocalProvider(model_path="/path/to/model.gguf")
        
        # Generate a response
        response = provider.generate(
            prompt="This is a test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        # Check the response
        assert response == "This is a mock response from a local model."
        
        # Check that the client was called correctly
        mock_instance.create_completion.assert_called_once()
        args, kwargs = mock_instance.create_completion.call_args
        assert kwargs["prompt"] == "This is a test prompt"
        assert kwargs["max_tokens"] == 100
        assert kwargs["temperature"] == 0.7
