"""
Hugging Face LLM provider implementation.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, AsyncIterator
import asyncio

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

class HuggingFaceProvider(LLMProvider):
    """
    Hugging Face implementation of the LLM provider.
    """
    
    # Model context sizes (these are estimates and may vary)
    MODEL_CONTEXT_SIZES = {
        "mistralai/Mistral-7B-Instruct-v0.2": 8192,
        "meta-llama/Llama-2-7b-chat-hf": 4096,
        "meta-llama/Llama-2-13b-chat-hf": 4096,
        "meta-llama/Llama-2-70b-chat-hf": 4096,
        "tiiuae/falcon-7b-instruct": 2048,
        "tiiuae/falcon-40b-instruct": 2048,
        "bigscience/bloom": 2048
    }
    
    def __init__(
        self,
        model: str = "mistralai/Mistral-7B-Instruct-v0.2",
        api_key: Optional[str] = None
    ):
        """
        Initialize the Hugging Face provider.
        
        Args:
            model: Model to use
            api_key: Hugging Face API key (defaults to HF_API_KEY environment variable)
        """
        super().__init__(model, api_key)
        
        # Use environment variable if API key not provided
        if not self.api_key:
            self.api_key = os.environ.get("HF_API_KEY")
            
        if not self.api_key:
            raise ValueError("Hugging Face API key not provided and not found in environment")
        
        # Import here to avoid dependency issues
        try:
            from huggingface_hub import InferenceClient
            from transformers import AutoTokenizer
        except ImportError:
            raise ImportError("huggingface_hub and transformers are required for HuggingFaceProvider")
        
        # Initialize client
        self.client = InferenceClient(token=self.api_key)
        
        # Initialize tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model)
        except Exception as e:
            logger.warning(f"Could not load tokenizer for {model}: {e}")
            self.tokenizer = None
    
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
        Generate a response from the Hugging Face model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for the model
            **kwargs: Additional Hugging Face-specific parameters
            
        Returns:
            LLM response
        """
        try:
            # Set default max tokens if not provided
            if max_tokens is None:
                max_tokens = 1024
            
            # Prepare the full prompt with system message if provided
            full_prompt = prompt
            if system_message:
                # Format depends on the model, this is a generic approach
                full_prompt = f"{system_message}\n\n{prompt}"
            
            # Prepare parameters
            params = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0,
                "return_full_text": False
            }
            
            # Add top_p if provided
            if top_p is not None:
                params["top_p"] = top_p
                
            # Add stop sequences if provided
            if stop_sequences:
                params["stop"] = stop_sequences
                
            # Add any additional parameters
            params.update(kwargs)
            
            # Call the Hugging Face API
            response = self.client.text_generation(
                full_prompt,
                model=self.model,
                **params
            )
            
            # Count tokens for usage statistics
            prompt_tokens = self.count_tokens(full_prompt)
            completion_tokens = self.count_tokens(response)
            
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
            
            return LLMResponse(
                text=response,
                model=self.model,
                usage=usage,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error generating response from Hugging Face: {e}")
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
        Generate a streaming response from the Hugging Face model.
        
        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            system_message: System message for the model
            **kwargs: Additional Hugging Face-specific parameters
            
        Returns:
            Async iterator of response chunks
        """
        try:
            # Set default max tokens if not provided
            if max_tokens is None:
                max_tokens = 1024
            
            # Prepare the full prompt with system message if provided
            full_prompt = prompt
            if system_message:
                # Format depends on the model, this is a generic approach
                full_prompt = f"{system_message}\n\n{prompt}"
            
            # Prepare parameters
            params = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0,
                "return_full_text": False
            }
            
            # Add top_p if provided
            if top_p is not None:
                params["top_p"] = top_p
                
            # Add stop sequences if provided
            if stop_sequences:
                params["stop"] = stop_sequences
                
            # Add any additional parameters
            params.update(kwargs)
            
            # Call the Hugging Face API with streaming
            stream = self.client.text_generation(
                full_prompt,
                model=self.model,
                stream=True,
                **params
            )
            
            # Yield chunks as they arrive
            for response in stream:
                yield response.token.text
                    
        except Exception as e:
            logger.error(f"Error generating streaming response from Hugging Face: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough estimate if tokenizer is not available
            return len(text.split())
    
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models.
        
        Returns:
            List of available models
        """
        # Return known models since listing all HF models would be too many
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
        logger.warning(f"Unknown model {model_name}, assuming default context size of 2048")
        return 2048
