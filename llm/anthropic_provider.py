"""
Anthropic LLM provider implementation.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, AsyncIterator
import anthropic

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    """
    Anthropic implementation of the LLM provider.
    """
    
    # Model context sizes
    MODEL_CONTEXT_SIZES = {
        "claude-instant-1": 100000,
        "claude-1": 100000,
        "claude-2": 100000,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000
    }
    
    def __init__(
        self,
        model: str = "claude-3-sonnet",
        api_key: Optional[str] = None
    ):
        """
        Initialize the Anthropic provider.
        
        Args:
            model: Model to use
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY environment variable)
        """
        super().__init__(model, api_key)
        
        # Use environment variable if API key not provided
        if not self.api_key:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            
        if not self.api_key:
            raise ValueError("Anthropic API key not provided and not found in environment")
        
        # Initialize client
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        system_message: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the Anthropic model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for the model
            **kwargs: Additional Anthropic-specific parameters
            
        Returns:
            LLM response
        """
        try:
            # Set default max tokens if not provided
            if max_tokens is None:
                max_tokens = 1024
            
            # Create the message
            message_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop_sequences": stop_sequences
            }
            
            # Add system message if provided
            if system_message:
                message_params["system"] = system_message
                
            # Add top_p if provided
            if top_p is not None:
                message_params["top_p"] = top_p
                
            # Add any additional parameters
            message_params.update(kwargs)
            
            # Call the Anthropic API
            response = self.client.messages.create(**message_params)
            
            # Extract the response text
            text = response.content[0].text
            
            # Create usage dictionary (Anthropic doesn't provide detailed token usage)
            # We'll estimate based on input and output length
            prompt_tokens = self.count_tokens(prompt)
            completion_tokens = self.count_tokens(text)
            
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
            
            return LLMResponse(
                text=text,
                model=self.model,
                usage=usage,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error generating response from Anthropic: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the Anthropic model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for the model
            **kwargs: Additional Anthropic-specific parameters
            
        Returns:
            Async iterator of response chunks
        """
        try:
            # Set default max tokens if not provided
            if max_tokens is None:
                max_tokens = 1024
            
            # Create the message
            message_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop_sequences": stop_sequences,
                "stream": True
            }
            
            # Add system message if provided
            if system_message:
                message_params["system"] = system_message
                
            # Add top_p if provided
            if top_p is not None:
                message_params["top_p"] = top_p
                
            # Add any additional parameters
            message_params.update(kwargs)
            
            # Call the Anthropic API with streaming
            with self.client.messages.stream(**message_params) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Error generating streaming response from Anthropic: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return anthropic.count_tokens(text)
    
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models.
        
        Returns:
            List of available models
        """
        # Anthropic doesn't have an API to list models, so we return the known models
        return list(self.MODEL_CONTEXT_SIZES.keys())
    
    def get_model_context_size(self, model: Optional[str] = None) -> int:
        """
        Get the context size for a model.
        
        Args:
            model: Model to get context size for (defaults to the current model)
            
        Returns:
            Context size in tokens
        """
        model_name = model or self.model
        
        # Check if we have the context size for this model
        if model_name in self.MODEL_CONTEXT_SIZES:
            return self.MODEL_CONTEXT_SIZES[model_name]
        
        # For unknown models, assume a default size
        logger.warning(f"Unknown model {model_name}, assuming default context size of 100000")
        return 100000
