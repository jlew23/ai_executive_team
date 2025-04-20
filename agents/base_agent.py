"""
Base Agent class for the AI Executive Team.
This class provides the foundation for all specialized agents.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Union
import json

from .knowledge_base_tool import KnowledgeBaseTool

logger = logging.getLogger(__name__)

class Agent:
    """
    Base Agent class with enhanced decision-making logic and conversation memory.
    
    This class provides the foundation for all specialized agents in the AI Executive Team.
    It includes conversation memory, context management, and integration with the knowledge base.
    """
    
    def __init__(self, name: str, role: str, knowledge_base: Any):
        """
        Initialize the agent.
        
        Args:
            name (str): The name of the agent
            role (str): The role of the agent in the organization
            knowledge_base (Any): The knowledge base instance for retrieving information
        """
        self.name = name
        self.role = role
        self.knowledge_base = knowledge_base
        self.kb_tool = KnowledgeBaseTool(knowledge_base)
        self.conversation_history = []
        self.max_history_length = 20  # Maximum number of conversation turns to remember
        self.created_at = time.time()
        self.last_active = time.time()
        self.metrics = {
            "total_queries": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "avg_response_time": 0,
            "total_response_time": 0
        }
        
    def process_message(self, message: str, user_id: Optional[str] = None, 
                        channel_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process incoming message and generate a response.
        
        Args:
            message (str): The message to process
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The agent's response
        """
        start_time = time.time()
        self.last_active = start_time
        self.metrics["total_queries"] += 1
        
        # Record the incoming message in conversation history
        self._add_to_history("user", message, user_id, metadata)
        
        try:
            # Get context from knowledge base
            context = self.get_context(message)
            
            # Generate response based on context and conversation history
            response = self._generate_response(message, context, user_id, channel_id, metadata)
            
            # Record the response in conversation history
            self._add_to_history("agent", response, None, metadata)
            
            # Update metrics
            self.metrics["successful_responses"] += 1
            response_time = time.time() - start_time
            self.metrics["total_response_time"] += response_time
            self.metrics["avg_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["successful_responses"]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.metrics["failed_responses"] += 1
            
            # Generate a fallback response
            fallback_response = self._generate_fallback_response(message, user_id)
            
            # Record the fallback response in conversation history
            self._add_to_history("agent", fallback_response, None, {"error": str(e)})
            
            return fallback_response
    
    def get_context(self, message: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant context from the knowledge base.
        
        Args:
            message (str): The message to get context for
            k (int): The number of results to return
            
        Returns:
            List[Dict[str, Any]]: The relevant context from the knowledge base
        """
        try:
            # Check if we're using the new knowledge base tool
            if hasattr(self, 'kb_tool'):
                results = self.kb_tool.search(message, max_results=k)
                return results
            else:
                # Fallback to old method
                docs = self.knowledge_base.query(message, k=k)
                return [{"content": doc.page_content} for doc in docs]
        except Exception as e:
            logger.error(f"Error getting context from knowledge base: {e}")
            return []
    
    def search_knowledge_base(self, query: str, max_results: int = 4, search_fuzziness: int = 100) -> str:
        """
        Search the knowledge base using the knowledge base tool.
        
        Args:
            query (str): The query to search for
            max_results (int): The maximum number of results to return
            search_fuzziness (int): The fuzziness of the search (0-100)
            
        Returns:
            str: The formatted search results
        """
        if hasattr(self, 'kb_tool'):
            results = self.kb_tool.search(query, max_results=max_results, search_fuzziness=search_fuzziness)
            return self.kb_tool.format_results(results)
        else:
            # Fallback to old method
            docs = self.knowledge_base.query(query, k=max_results)
            return "\n\n".join([doc.page_content for doc in docs])
    
    def _generate_response(self, message: str, context: List[Dict[str, Any]], 
                          user_id: Optional[str], channel_id: Optional[str], 
                          metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a response based on the message, context, and conversation history.
        
        This is a base implementation that should be overridden by specialized agents.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The agent's response
        """
        if not context:
            return f"I'm {self.name}, the {self.role}. I don't have specific information about that. How else can I assist you?"
        
        # Create a response based on the context
        response = f"I'm {self.name}, the {self.role}. Here's what I know about that:\n\n"
        
        # Extract relevant information from the context
        for i, doc in enumerate(context):
            if "content" in doc:
                content = doc["content"]
            elif isinstance(doc, str):
                content = doc
            else:
                content = str(doc)
                
            # Add a summary of the document content (first 150 characters)
            summary = content.split('\n\n')[0]  # Get the first paragraph
            if len(summary) > 150:
                summary = summary[:147] + '...'
            response += f"{i+1}. {summary}\n\n"
        
        return response
    
    def _generate_fallback_response(self, message: str, user_id: Optional[str] = None) -> str:
        """
        Generate a fallback response when an error occurs.
        
        Args:
            message (str): The message that caused the error
            user_id (Optional[str]): The ID of the user who sent the message
            
        Returns:
            str: The fallback response
        """
        return f"I'm {self.name}, the {self.role}. I apologize, but I encountered an issue processing your request. Could you please rephrase or try again later?"
    
    def _add_to_history(self, sender: str, message: str, user_id: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            sender (str): The sender of the message ('user' or 'agent')
            message (str): The message content
            user_id (Optional[str]): The ID of the user who sent the message
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
        """
        timestamp = time.time()
        
        history_entry = {
            "sender": sender,
            "message": message,
            "timestamp": timestamp,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        self.conversation_history.append(history_entry)
        
        # Trim history if it exceeds the maximum length
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            limit (Optional[int]): The maximum number of history entries to return
            
        Returns:
            List[Dict[str, Any]]: The conversation history
        """
        if limit is None or limit >= len(self.conversation_history):
            return self.conversation_history
        
        return self.conversation_history[-limit:]
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the agent's performance metrics.
        
        Returns:
            Dict[str, Any]: The agent's metrics
        """
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset the agent's performance metrics."""
        self.metrics = {
            "total_queries": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "avg_response_time": 0,
            "total_response_time": 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent to a dictionary representation.
        
        Returns:
            Dict[str, Any]: The agent as a dictionary
        """
        return {
            "name": self.name,
            "role": self.role,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "metrics": self.metrics,
            "conversation_history_length": len(self.conversation_history)
        }
    
    def __str__(self) -> str:
        """
        Get a string representation of the agent.
        
        Returns:
            str: The string representation
        """
        return f"{self.name} ({self.role})"
