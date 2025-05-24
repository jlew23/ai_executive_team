"""
Message bus for inter-agent communication.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from .message import Message

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Central message bus for inter-agent communication.
    
    This class provides a publish-subscribe mechanism for agents to send
    and receive messages.
    """

    _instance = None

    def __new__(cls):
        """
        Create a singleton instance of the MessageBus.
        
        Returns:
            The singleton MessageBus instance
        """
        if cls._instance is None:
            cls._instance = super(MessageBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the message bus if not already initialized."""
        if not self._initialized:
            self._subscribers = {}  # agent_id -> callback function
            self._message_history = []  # List of all messages
            self._agent_inboxes = {}  # agent_id -> list of message IDs
            self._initialized = True
            logger.info("MessageBus initialized")

    def subscribe(self, agent_id: str, callback: Callable[[Message], Any]) -> None:
        """
        Subscribe an agent to receive messages.
        
        Args:
            agent_id: ID of the agent subscribing
            callback: Function to call when a message is received
        """
        self._subscribers[agent_id] = callback
        if agent_id not in self._agent_inboxes:
            self._agent_inboxes[agent_id] = []
        logger.info(f"Agent {agent_id} subscribed to MessageBus")

    def unsubscribe(self, agent_id: str) -> None:
        """
        Unsubscribe an agent from receiving messages.
        
        Args:
            agent_id: ID of the agent unsubscribing
        """
        if agent_id in self._subscribers:
            del self._subscribers[agent_id]
            logger.info(f"Agent {agent_id} unsubscribed from MessageBus")

    def publish(self, message: Message) -> None:
        """
        Publish a message to the bus.
        
        Args:
            message: The message to publish
        """
        # Add message to history
        self._message_history.append(message)
        
        # Add message to recipient inboxes
        for recipient in message.recipients:
            if recipient not in self._agent_inboxes:
                self._agent_inboxes[recipient] = []
            self._agent_inboxes[recipient].append(message.id)
            
            # Notify subscriber if available
            if recipient in self._subscribers:
                try:
                    self._subscribers[recipient](message)
                except Exception as e:
                    logger.error(f"Error delivering message to agent {recipient}: {e}")
        
        logger.info(f"Message {message.id} published from {message.sender} to {message.recipients}")

    def get_messages_for_agent(self, agent_id: str, unread_only: bool = False) -> List[Message]:
        """
        Get messages for a specific agent.
        
        Args:
            agent_id: ID of the agent
            unread_only: If True, only return unread messages
            
        Returns:
            List of messages for the agent
        """
        if agent_id not in self._agent_inboxes:
            return []
            
        messages = []
        for msg_id in self._agent_inboxes[agent_id]:
            message = self.get_message_by_id(msg_id)
            if message and (not unread_only or agent_id not in message.read_by):
                messages.append(message)
                
        return messages

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """
        Get a message by its ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            The message if found, None otherwise
        """
        for message in self._message_history:
            if message.id == message_id:
                return message
        return None

    def mark_as_read(self, message_id: str, agent_id: str) -> bool:
        """
        Mark a message as read by an agent.
        
        Args:
            message_id: ID of the message to mark
            agent_id: ID of the agent who read the message
            
        Returns:
            True if successful, False otherwise
        """
        message = self.get_message_by_id(message_id)
        if message:
            message.mark_as_read(agent_id)
            return True
        return False

    def clear_history(self) -> None:
        """Clear all message history and inboxes."""
        self._message_history = []
        self._agent_inboxes = {agent_id: [] for agent_id in self._agent_inboxes}
        logger.info("MessageBus history cleared")

    def get_all_messages(self) -> List[Message]:
        """
        Get all messages in the system.
        
        Returns:
            List of all messages
        """
        return self._message_history.copy()
