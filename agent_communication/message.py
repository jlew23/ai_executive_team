"""
Message classes for inter-agent communication.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class MessageType(Enum):
    """Types of messages that can be exchanged between agents."""
    TASK = "task"
    STATUS_UPDATE = "status_update"
    RESPONSE = "response"
    QUERY = "query"
    NOTIFICATION = "notification"


class Message:
    """Base class for all messages exchanged between agents."""

    def __init__(
        self,
        sender: str,
        recipients: List[str],
        content: str,
        message_type: MessageType,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new message.

        Args:
            sender: ID or name of the sending agent
            recipients: List of IDs or names of recipient agents
            content: The message content
            message_type: Type of message
            metadata: Additional metadata for the message
        """
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.recipients = recipients
        self.content = content
        self.message_type = message_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.read_by = []

    def mark_as_read(self, agent_id: str) -> None:
        """
        Mark the message as read by an agent.

        Args:
            agent_id: ID of the agent who read the message
        """
        if agent_id not in self.read_by:
            self.read_by.append(agent_id)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.

        Returns:
            Dictionary representation of the message
        """
        return {
            "id": self.id,
            "sender": self.sender,
            "recipients": self.recipients,
            "content": self.content,
            "message_type": self.message_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "read_by": self.read_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.

        Args:
            data: Dictionary representation of the message

        Returns:
            Message object
        """
        message = cls(
            sender=data["sender"],
            recipients=data["recipients"],
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            metadata=data.get("metadata", {})
        )
        message.id = data["id"]
        message.timestamp = datetime.fromisoformat(data["timestamp"])
        message.read_by = data.get("read_by", [])
        return message


class TaskMessage(Message):
    """Message for delegating tasks between agents."""

    def __init__(
        self,
        sender: str,
        recipients: List[str],
        content: str,
        task_id: str,
        priority: int = 1,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new task message.

        Args:
            sender: ID or name of the sending agent
            recipients: List of IDs or names of recipient agents
            content: The task description
            task_id: Unique identifier for the task
            priority: Task priority (1-5, with 5 being highest)
            due_date: When the task should be completed
            dependencies: List of task IDs that must be completed before this task
            metadata: Additional metadata for the message
        """
        super().__init__(
            sender=sender,
            recipients=recipients,
            content=content,
            message_type=MessageType.TASK,
            metadata=metadata or {}
        )
        self.task_id = task_id
        self.priority = min(max(priority, 1), 5)  # Ensure priority is between 1-5
        self.due_date = due_date
        self.dependencies = dependencies or []
        self.metadata["task_id"] = task_id
        self.metadata["priority"] = priority
        if due_date:
            self.metadata["due_date"] = due_date.isoformat()
        if dependencies:
            self.metadata["dependencies"] = dependencies

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskMessage':
        """
        Create a task message from a dictionary.

        Args:
            data: Dictionary representation of the task message

        Returns:
            TaskMessage object
        """
        due_date = None
        if "due_date" in data.get("metadata", {}):
            due_date = datetime.fromisoformat(data["metadata"]["due_date"])

        task_message = cls(
            sender=data["sender"],
            recipients=data["recipients"],
            content=data["content"],
            task_id=data["metadata"]["task_id"],
            priority=data["metadata"].get("priority", 1),
            due_date=due_date,
            dependencies=data["metadata"].get("dependencies", []),
            metadata=data.get("metadata", {})
        )
        task_message.id = data["id"]
        task_message.timestamp = datetime.fromisoformat(data["timestamp"])
        task_message.read_by = data.get("read_by", [])
        return task_message


class StatusUpdateMessage(Message):
    """Message for providing status updates on tasks."""

    def __init__(
        self,
        sender: str,
        recipients: List[str],
        content: str,
        task_id: str,
        status: str,
        progress: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new status update message.

        Args:
            sender: ID or name of the sending agent
            recipients: List of IDs or names of recipient agents
            content: The status update description
            task_id: ID of the task being updated
            status: Current status (e.g., "in_progress", "completed", "blocked")
            progress: Completion percentage (0.0 to 1.0)
            metadata: Additional metadata for the message
        """
        super().__init__(
            sender=sender,
            recipients=recipients,
            content=content,
            message_type=MessageType.STATUS_UPDATE,
            metadata=metadata or {}
        )
        self.task_id = task_id
        self.status = status
        self.progress = min(max(progress, 0.0), 1.0)  # Ensure progress is between 0-1
        self.metadata["task_id"] = task_id
        self.metadata["status"] = status
        self.metadata["progress"] = progress

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusUpdateMessage':
        """
        Create a status update message from a dictionary.

        Args:
            data: Dictionary representation of the status update message

        Returns:
            StatusUpdateMessage object
        """
        status_message = cls(
            sender=data["sender"],
            recipients=data["recipients"],
            content=data["content"],
            task_id=data["metadata"]["task_id"],
            status=data["metadata"]["status"],
            progress=data["metadata"].get("progress", 0.0),
            metadata=data.get("metadata", {})
        )
        status_message.id = data["id"]
        status_message.timestamp = datetime.fromisoformat(data["timestamp"])
        status_message.read_by = data.get("read_by", [])
        return status_message


class ResponseMessage(Message):
    """Message for responding to tasks or queries."""

    def __init__(
        self,
        sender: str,
        recipients: List[str],
        content: str,
        in_reply_to: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new response message.

        Args:
            sender: ID or name of the sending agent
            recipients: List of IDs or names of recipient agents
            content: The response content
            in_reply_to: ID of the message being replied to
            metadata: Additional metadata for the message
        """
        super().__init__(
            sender=sender,
            recipients=recipients,
            content=content,
            message_type=MessageType.RESPONSE,
            metadata=metadata or {}
        )
        self.in_reply_to = in_reply_to
        self.metadata["in_reply_to"] = in_reply_to

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseMessage':
        """
        Create a response message from a dictionary.

        Args:
            data: Dictionary representation of the response message

        Returns:
            ResponseMessage object
        """
        response_message = cls(
            sender=data["sender"],
            recipients=data["recipients"],
            content=data["content"],
            in_reply_to=data["metadata"]["in_reply_to"],
            metadata=data.get("metadata", {})
        )
        response_message.id = data["id"]
        response_message.timestamp = datetime.fromisoformat(data["timestamp"])
        response_message.read_by = data.get("read_by", [])
        return response_message
