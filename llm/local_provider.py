"""
Local LLM provider implementation using llama.cpp.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, AsyncIterator
import asyncio

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

class LocalProvider(LLMProvider):
    """
    Local implementation of the LLM provider using llama.cpp.
    """
    
    def __init__(
        self,
        model: str,
        model_path: Optional[str] = None,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1
    ):
        """
        Initialize the Local provider.
        
        Args:
            model: Model identifier
            model_path: Path to the model file (if not provided, will look in standard locations)
            n_ctx: Context size
            n_gpu_layers: Number of layers to offload to GPU (-1 for all)
        """
        super().__init__(model, None)
        
        # Import here to avoid dependency issues
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError("llama-cpp-python is required for LocalProvider")
        
        # Determine model path if not provided
        if not model_path:
            # Check common locations
            possible_paths = [
                os.path.join(os.path.expanduser("~"), ".cache", "llama", model),
                os.path.join(os.path.expanduser("~"), "models", model),
                os.path.join("/models", model)
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if not model_path:
                raise ValueError(f"Model file for {model} not found in standard locations")
        
        # Initialize llama.cpp
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers
        )
        
        # Store context size
        self.context_size = n_ctx
    
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
        Generate a response from the local model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for the model
            **kwargs: Additional parameters
            
        Returns:
            LLM response
        """
        try:
            # Set default max tokens if not provided
            if max_tokens is None:
                max_tokens = 512
            
            # Prepare the full prompt with system message if provided
            full_prompt = prompt
            if system_message:
                # Format depends on the model, this is a generic approach
                full_prompt = f"{system_message}\n\n{prompt}"
            
            # Prepare parameters
            params = {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "echo": False
            }
            
            # Add top_p if provided
            if top_p is not None:
                params["top_p"] = top_p
                
            # Add stop sequences if provided
            if stop_sequences:
                params["stop"] = stop_sequences
                
            # Add any additional parameters
            params.update(kwargs)
            
            # Call the local model
            start_time = asyncio.get_event_loop().time()
            response = self.llm(full_prompt, **params)
            end_time = asyncio.get_event_loop().time()
            
            # Extract the response text
            text = response["choices"][0]["text"]
            
            # Count tokens for usage statistics
            prompt_tokens = self.count_tokens(full_prompt)
            completion_tokens = self.count_tokens(text)
            
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "generation_time": end_time - start_time
            }
            
            return LLMResponse(
                text=text,
                model=self.model,
                usage=usage,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error generating response from local model: {e}")
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
        Generate a streaming response from the local model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for the model
            **kwargs: Additional parameters
            
        Returns:
            Async iterator of response chunks
        """
        try:
            # Set default max tokens if not provided
            if max_tokens is None:
                max_tokens = 512
            
            # Prepare the full prompt with system message if provided
            full_prompt = prompt
            if system_message:
                # Format depends on the model, this is a generic approach
                full_prompt = f"{system_message}\n\n{prompt}"
            
            # Prepare parameters
            params = {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "echo": False,
                "stream": True
            }
            
            # Add top_p if provided
            if top_p is not None:
                params["top_p"] = top_p
                
            # Add stop sequences if provided
            if stop_sequences:
                params["stop"] = stop_sequences
                
            # Add any additional parameters
            params.update(kwargs)
            
            # Call the local model with streaming
            for chunk in self.llm(full_prompt, **params):
                if "choices" in chunk and chunk["choices"] and "text" in chunk["choices"][0]:
                    yield chunk["choices"][0]["text"]
                    
        except Exception as e:
            logger.error(f"Error generating streaming response from local model: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.llm.tokenize(text.encode("utf-8")))
    
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models.
        
        Returns:
            List of available models
        """
        # This is a local provider, so we only have the current model
        return [self.model]
    
    def get_model_context_size(self, model: Optional[str] = None) -> int:
        """
        Get the context size for a model.
        
        Args:
            model: Model to get context size for (defaults to the current model)
            
        Returns:
            Context size in tokens
        """
        # For local models, we know the context size from initialization
        return self.context_size
