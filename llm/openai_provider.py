"""
OpenAI LLM provider implementation.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, AsyncIterator
import tiktoken
import openai
from openai import OpenAI, AsyncOpenAI

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """
    OpenAI implementation of the LLM provider.
    """
    
    # Model context sizes
    MODEL_CONTEXT_SIZES = {
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000
    }
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        organization: Optional[str] = None
    ):
        """
        Initialize the OpenAI provider.
        
        Args:
            model: Model to use
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
            organization: OpenAI organization ID
        """
        super().__init__(model, api_key)
        
        # Use environment variable if API key not provided
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")
            
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in environment")
        
        # Initialize clients
        self.client = OpenAI(api_key=self.api_key, organization=organization)
        self.async_client = AsyncOpenAI(api_key=self.api_key, organization=organization)
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base for newer models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
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
        Generate a response from the OpenAI model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for chat models
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            LLM response
        """
        try:
            # Prepare messages for chat models
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
                
            messages.append({"role": "user", "content": prompt})
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p if top_p is not None else 1.0,
                stop=stop_sequences,
                **kwargs
            )
            
            # Extract the response text
            text = response.choices[0].message.content
            
            # Create usage dictionary
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                text=text,
                model=self.model,
                usage=usage,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
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
        Generate a streaming response from the OpenAI model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for chat models
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            Async iterator of response chunks
        """
        try:
            # Prepare messages for chat models
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
                
            messages.append({"role": "user", "content": prompt})
            
            # Call the OpenAI API with streaming
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p if top_p is not None else 1.0,
                stop=stop_sequences,
                stream=True,
                **kwargs
            )
            
            # Yield chunks as they arrive
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error generating streaming response from OpenAI: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))
    
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models.
        
        Returns:
            List of available models
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Error getting available models from OpenAI: {e}")
            # Return default models if API call fails
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
        logger.warning(f"Unknown model {model_name}, assuming default context size of 4096")
        return 4096
