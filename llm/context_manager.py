"""
Context manager for efficient token usage in LLM interactions.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field

from .base import LLMProvider

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """
    A message in a conversation.
    """
    role: str  # "system", "user", "assistant"
    content: str
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ContextManager:
    """
    Manages context for LLM interactions.
    
    This class provides functionality for:
    1. Tracking conversation history
    2. Managing token usage
    3. Pruning context to fit within token limits
    4. Summarizing conversation history
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        max_tokens: int = 4096,
        reserve_tokens: int = 1024,
        system_message: Optional[str] = None
    ):
        """
        Initialize the context manager.
        
        Args:
            llm_provider: LLM provider to use for token counting and generation
            max_tokens: Maximum number of tokens to use for context
            reserve_tokens: Number of tokens to reserve for the response
            system_message: System message to include in all contexts
        """
        self.llm_provider = llm_provider
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.messages: List[Message] = []
        
        # Add system message if provided
        if system_message:
            self.add_message("system", system_message)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the context.
        
        Args:
            role: Role of the message sender ("system", "user", "assistant")
            content: Content of the message
            metadata: Additional metadata about the message
        """
        # Count tokens
        token_count = self.llm_provider.count_tokens(content)
        
        # Add message
        self.messages.append(Message(
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {}
        ))
        
        # Prune context if necessary
        self._prune_context()
    
    def get_context(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        Get the current context as a list of messages.
        
        Args:
            include_system: Whether to include system messages
            
        Returns:
            List of messages in the format expected by LLM providers
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
            if include_system or msg.role != "system"
        ]
    
    def get_context_string(self, include_system: bool = True) -> str:
        """
        Get the current context as a string.
        
        Args:
            include_system: Whether to include system messages
            
        Returns:
            String representation of the context
        """
        context = ""
        
        for msg in self.messages:
            if not include_system and msg.role == "system":
                continue
                
            if msg.role == "system":
                context += f"System: {msg.content}\n\n"
            elif msg.role == "user":
                context += f"User: {msg.content}\n\n"
            elif msg.role == "assistant":
                context += f"Assistant: {msg.content}\n\n"
                
        return context.strip()
    
    def get_token_count(self) -> int:
        """
        Get the total token count of the current context.
        
        Returns:
            Total token count
        """
        return sum(msg.token_count or 0 for msg in self.messages)
    
    def get_available_tokens(self) -> int:
        """
        Get the number of tokens available for the next response.
        
        Returns:
            Number of available tokens
        """
        return max(0, self.max_tokens - self.get_token_count() - self.reserve_tokens)
    
    def clear(self, keep_system: bool = True) -> None:
        """
        Clear the context.
        
        Args:
            keep_system: Whether to keep system messages
        """
        if keep_system:
            self.messages = [msg for msg in self.messages if msg.role == "system"]
        else:
            self.messages = []
    
    def summarize_history(self, max_tokens: Optional[int] = None) -> str:
        """
        Summarize the conversation history.
        
        Args:
            max_tokens: Maximum number of tokens for the summary
            
        Returns:
            Summary of the conversation history
        """
        # If no history to summarize, return empty string
        if len(self.messages) <= 1:
            return ""
            
        # Filter out system messages
        history = [msg for msg in self.messages if msg.role != "system"]
        
        if not history:
            return ""
            
        # Create a prompt for summarization
        context_string = self.get_context_string(include_system=False)
        
        prompt = f"""
        Please summarize the following conversation concisely, capturing the key points and important information:
        
        {context_string}
        
        Summary:
        """
        
        # Generate summary
        response = self.llm_provider.generate(
            prompt=prompt,
            max_tokens=max_tokens or 200,
            temperature=0.3
        )
        
        return response.text.strip()
    
    def _prune_context(self) -> None:
        """
        Prune the context to fit within the token limit.
        
        This method removes older messages (except system messages) to ensure
        the context fits within the token limit.
        """
        # Calculate current token count
        current_tokens = self.get_token_count()
        
        # If we're within the limit, no need to prune
        if current_tokens <= self.max_tokens - self.reserve_tokens:
            return
            
        # Separate system messages from other messages
        system_messages = [msg for msg in self.messages if msg.role == "system"]
        other_messages = [msg for msg in self.messages if msg.role != "system"]
        
        # Calculate tokens used by system messages
        system_tokens = sum(msg.token_count or 0 for msg in system_messages)
        
        # Calculate how many tokens we need to remove
        tokens_to_remove = current_tokens - (self.max_tokens - self.reserve_tokens)
        
        # If we can't remove enough tokens even by removing all non-system messages,
        # we need to summarize or truncate
        if tokens_to_remove > current_tokens - system_tokens:
            logger.warning("Cannot prune enough tokens while preserving system messages")
            
            # Keep only the most recent messages
            other_messages.sort(key=lambda msg: msg.metadata.get("timestamp", 0), reverse=True)
            
            # Keep removing messages until we're within the limit
            while self.get_token_count() > self.max_tokens - self.reserve_tokens and other_messages:
                removed_msg = other_messages.pop()
                self.messages.remove(removed_msg)
                
            return
        
        # Remove oldest messages first
        other_messages.sort(key=lambda msg: msg.metadata.get("timestamp", 0))
        
        # Keep removing messages until we've removed enough tokens
        removed_tokens = 0
        while removed_tokens < tokens_to_remove and other_messages:
            removed_msg = other_messages.pop(0)
            removed_tokens += removed_msg.token_count or 0
            self.messages.remove(removed_msg)
            
        logger.debug(f"Pruned {removed_tokens} tokens from context")
