"""
LLM module for AI Executive Team.

This module provides functionality for interacting with various LLM providers, including:
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Local models via LlamaCpp
- Hugging Face models

Features include:
- Unified API for different LLM providers
- Prompt templates and chain-of-thought reasoning
- Streaming response capabilities
- Context management for efficient token usage
- Fallback mechanisms for reliability
"""

from .base import LLMProvider, LLMResponse
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .huggingface_provider import HuggingFaceProvider
from .local_provider import LocalProvider
from .prompt_template import PromptTemplate
from .context_manager import ContextManager

__all__ = [
    'LLMProvider',
    'LLMResponse',
    'OpenAIProvider',
    'AnthropicProvider',
    'HuggingFaceProvider',
    'LocalProvider',
    'PromptTemplate',
    'ContextManager'
]
