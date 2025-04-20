"""
Base LLM provider interface.
"""

import abc
from typing import Dict, Any, List, Optional, Union, Callable, AsyncIterator
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """
    Response from an LLM.
    """
    text: str
    model: str
    usage: Dict[str, int]
    raw_response: Any = None
    
    @property
    def total_tokens(self) -> int:
        """
        Get the total number of tokens used.
        
        Returns:
            Total tokens
        """
        return self.usage.get("total_tokens", 0)
    
    @property
    def prompt_tokens(self) -> int:
        """
        Get the number of tokens used in the prompt.
        
        Returns:
            Prompt tokens
        """
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        """
        Get the number of tokens used in the completion.
        
        Returns:
            Completion tokens
        """
        return self.usage.get("completion_tokens", 0)

class LLMProvider(abc.ABC):
    """
    Abstract base class for LLM providers.
    """
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        """
        Initialize the LLM provider.
        
        Args:
            model: Model to use
            api_key: API key for the provider
        """
        self.model = model
        self.api_key = api_key
    
    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: Prompt to send to the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response
        """
        pass
    
    @abc.abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            prompt: Prompt to send to the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Async iterator of response chunks
        """
        pass
    
    @abc.abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    @abc.abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models.
        
        Returns:
            List of available models
        """
        pass
    
    @abc.abstractmethod
    def get_model_context_size(self, model: Optional[str] = None) -> int:
        """
        Get the context size for a model.
        
        Args:
            model: Model to get context size for (defaults to the current model)
            
        Returns:
            Context size in tokens
        """
        pass
