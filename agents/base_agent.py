"""
Base Agent class for the AI Executive Team.
This class provides the foundation for all specialized agents.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
import json

from .knowledge_base_tool import KnowledgeBaseTool

# Import the agent communication system
try:
    from agent_communication import DelegationSystem, TaskManager, MessageBus
    from agent_communication import Message, TaskMessage, StatusUpdateMessage, ResponseMessage
    from agent_communication.task_manager import TaskStatus, Task
    DELEGATION_AVAILABLE = True
except ImportError:
    DELEGATION_AVAILABLE = False
    logging.warning("Agent communication module not available. Delegation features will be disabled.")

logger = logging.getLogger(__name__)

class Agent:
    """
    Base Agent class with enhanced decision-making logic and conversation memory.

    This class provides the foundation for all specialized agents in the AI Executive Team.
    It includes conversation memory, context management, and integration with the knowledge base.
    """

    def __init__(self, name: str, role: str, knowledge_base: Any, agent_id: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            name (str): The name of the agent
            role (str): The role of the agent in the organization
            knowledge_base (Any): The knowledge base instance for retrieving information
            agent_id (Optional[str]): Unique identifier for the agent, generated if not provided
        """
        self.name = name
        self.role = role
        self.agent_id = agent_id or str(uuid.uuid4())
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

        # Initialize delegation system if available
        if DELEGATION_AVAILABLE:
            self.delegation_system = DelegationSystem()
            self.delegation_system.register_agent(self.agent_id, self.role)
            self.message_bus = MessageBus()
            self.message_bus.subscribe(self.agent_id, self._handle_message)
            self.task_manager = TaskManager()
            logger.info(f"Agent {self.name} ({self.role}) registered with delegation system")
        else:
            self.delegation_system = None
            self.message_bus = None
            self.task_manager = None

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
            # Handle different document structures
            if isinstance(doc, dict):
                # Try to extract content from various possible fields
                if "content" in doc:
                    content = doc["content"]
                elif "text" in doc:
                    content = doc["text"]
                elif "page_content" in doc:
                    content = doc["page_content"]
                else:
                    # If no content field is found, use the entire document as a string
                    content = json.dumps(doc, indent=2)
            elif isinstance(doc, str):
                content = doc
            else:
                content = str(doc)

            # Add a summary of the document content (first 150 characters)
            # Handle potential empty content
            if not content or content.strip() == "":
                continue
                
            # Get the first paragraph or a reasonable chunk of text
            if '\n\n' in content:
                summary = content.split('\n\n')[0]  # Get the first paragraph
            else:
                summary = content
                
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
        data = {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "metrics": self.metrics,
            "conversation_history_length": len(self.conversation_history),
            "delegation_enabled": DELEGATION_AVAILABLE
        }

        # Add delegation-related information if available
        if DELEGATION_AVAILABLE and self.delegation_system:
            tasks = self.get_assigned_tasks()
            data["assigned_tasks"] = len(tasks)
            data["pending_tasks"] = len([t for t in tasks if t.status == TaskStatus.PENDING])
            data["completed_tasks"] = len([t for t in tasks if t.status == TaskStatus.COMPLETED])

            messages = self.get_messages()
            data["unread_messages"] = len([m for m in messages if self.agent_id not in m.read_by])

        return data

    # Delegation system methods
    def _handle_message(self, message: Message) -> None:
        """
        Handle a message received from another agent.

        Args:
            message: The message to handle
        """
        if not DELEGATION_AVAILABLE:
            return

        logger.info(f"Agent {self.name} received message from {message.sender}: {message.content[:50]}...")

        # Mark the message as read
        self.message_bus.mark_as_read(message.id, self.agent_id)

        # Handle different types of messages
        if isinstance(message, TaskMessage):
            # A new task has been assigned
            self._handle_task_message(message)
        elif isinstance(message, StatusUpdateMessage):
            # A status update for a task
            self._handle_status_update(message)
        elif isinstance(message, ResponseMessage):
            # A response to a previous message
            self._handle_response_message(message)

    def _handle_task_message(self, message: TaskMessage) -> None:
        """
        Handle a task message.

        Args:
            message: The task message to handle
        """
        # This is a base implementation that should be overridden by specialized agents
        # For now, just acknowledge receipt
        task = self.delegation_system.get_task_by_id(message.task_id)
        if task:
            response = f"I've received the task '{task.title}' and will begin working on it."
            self.respond_to_task(task.id, response)

    def _handle_status_update(self, message: StatusUpdateMessage) -> None:
        """
        Handle a status update message.

        Args:
            message: The status update message to handle
        """
        # Base implementation - can be overridden by specialized agents
        pass

    def _handle_response_message(self, message: ResponseMessage) -> None:
        """
        Handle a response message.

        Args:
            message: The response message to handle
        """
        # Base implementation - can be overridden by specialized agents
        pass

    def delegate_task(self, title: str, description: str, assigned_role: str,
                      priority: int = 1, due_date: Optional[datetime] = None) -> Optional[Task]:
        """
        Delegate a task to another agent.

        Args:
            title: Short title of the task
            description: Detailed description of the task
            assigned_role: Role of the agent to assign the task to
            priority: Task priority (1-5, with 5 being highest)
            due_date: When the task should be completed

        Returns:
            The created task if successful, None otherwise
        """
        if not DELEGATION_AVAILABLE or not self.delegation_system:
            logger.warning("Delegation system not available. Cannot delegate task.")
            return None

        # Find an agent with the specified role
        assigned_to = self.delegation_system.get_agent_by_role(assigned_role)
        if not assigned_to:
            logger.error(f"No agent found with role {assigned_role}")
            return None

        # Delegate the task
        task, _ = self.delegation_system.delegate_task(
            title=title,
            description=description,
            created_by=self.agent_id,
            assigned_to=assigned_to,
            priority=priority,
            due_date=due_date
        )

        if task:
            logger.info(f"Task '{title}' delegated to {assigned_role}")
            return task
        else:
            logger.error(f"Failed to delegate task '{title}' to {assigned_role}")
            return None

    def update_task_status(self, task_id: str, status: str, progress: float = None,
                          note: Optional[str] = None) -> bool:
        """
        Update the status of a task.

        Args:
            task_id: ID of the task to update
            status: New status of the task (pending, in_progress, completed, blocked, failed, cancelled)
            progress: New progress percentage (0.0 to 1.0)
            note: Optional note about the status update

        Returns:
            True if successful, False otherwise
        """
        if not DELEGATION_AVAILABLE or not self.delegation_system:
            logger.warning("Delegation system not available. Cannot update task status.")
            return False

        # Convert string status to TaskStatus enum
        try:
            task_status = TaskStatus(status)
        except ValueError:
            logger.error(f"Invalid task status: {status}")
            return False

        # Update the task status
        success, _ = self.delegation_system.update_task_status(
            task_id=task_id,
            agent_id=self.agent_id,
            status=task_status,
            progress=progress,
            note=note
        )

        return success

    def respond_to_task(self, task_id: str, response: str) -> bool:
        """
        Send a response about a task.

        Args:
            task_id: ID of the task to respond to
            response: Content of the response

        Returns:
            True if successful, False otherwise
        """
        if not DELEGATION_AVAILABLE or not self.delegation_system:
            logger.warning("Delegation system not available. Cannot respond to task.")
            return False

        # Send the response
        success, _ = self.delegation_system.respond_to_task(
            task_id=task_id,
            agent_id=self.agent_id,
            response_content=response
        )

        return success

    def get_assigned_tasks(self, status_filter: Optional[str] = None) -> List[Task]:
        """
        Get all tasks assigned to this agent.

        Args:
            status_filter: Optional filter for task status

        Returns:
            List of tasks assigned to the agent
        """
        if not DELEGATION_AVAILABLE or not self.delegation_system:
            return []

        # Convert string status to TaskStatus enum if provided
        task_status = None
        if status_filter:
            try:
                task_status = TaskStatus(status_filter)
            except ValueError:
                logger.error(f"Invalid task status filter: {status_filter}")
                return []

        return self.delegation_system.get_agent_tasks(self.agent_id, task_status)

    def get_messages(self, unread_only: bool = False) -> List[Message]:
        """
        Get all messages for this agent.

        Args:
            unread_only: If True, only return unread messages

        Returns:
            List of messages for the agent
        """
        if not DELEGATION_AVAILABLE or not self.message_bus:
            return []

        return self.message_bus.get_messages_for_agent(self.agent_id, unread_only)

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a task by its ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        if not DELEGATION_AVAILABLE or not self.delegation_system:
            return None

        return self.delegation_system.get_task_by_id(task_id)

    def __str__(self) -> str:
        """
        Get a string representation of the agent.

        Returns:
            str: The string representation
        """
        return f"{self.name} ({self.role})"
