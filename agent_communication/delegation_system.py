"""
Delegation system for distributing tasks between agents.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .message_bus import MessageBus
from .task_manager import TaskManager, Task, TaskStatus
from .message import Message, TaskMessage, StatusUpdateMessage, ResponseMessage

logger = logging.getLogger(__name__)


class DelegationSystem:
    """
    System for delegating tasks between agents.
    
    This class provides functionality for the CEO agent to delegate tasks
    to other agents and track their progress.
    """

    _instance = None

    def __new__(cls):
        """
        Create a singleton instance of the DelegationSystem.
        
        Returns:
            The singleton DelegationSystem instance
        """
        if cls._instance is None:
            cls._instance = super(DelegationSystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the delegation system if not already initialized."""
        if not self._initialized:
            self._message_bus = MessageBus()
            self._task_manager = TaskManager()
            self._agent_roles = {}  # agent_id -> role
            self._role_capabilities = {
                "CEO": ["strategy", "leadership", "decision_making", "delegation"],
                "CTO": ["technology", "development", "architecture", "innovation"],
                "CFO": ["finance", "budgeting", "forecasting", "investment"],
                "CMO": ["marketing", "branding", "customer_acquisition", "market_research"],
                "COO": ["operations", "logistics", "process_optimization", "team_management"]
            }
            self._initialized = True
            logger.info("DelegationSystem initialized")

    def register_agent(self, agent_id: str, role: str) -> None:
        """
        Register an agent with the delegation system.
        
        Args:
            agent_id: ID of the agent
            role: Role of the agent (CEO, CTO, etc.)
        """
        self._agent_roles[agent_id] = role
        logger.info(f"Agent {agent_id} registered with role {role}")

    def get_agent_by_role(self, role: str) -> Optional[str]:
        """
        Get the ID of an agent with a specific role.
        
        Args:
            role: Role to look for
            
        Returns:
            Agent ID if found, None otherwise
        """
        for agent_id, agent_role in self._agent_roles.items():
            if agent_role == role:
                return agent_id
        return None

    def get_all_agents(self) -> Dict[str, str]:
        """
        Get all registered agents and their roles.
        
        Returns:
            Dictionary mapping agent IDs to roles
        """
        return self._agent_roles.copy()

    def delegate_task(
        self,
        title: str,
        description: str,
        created_by: str,
        assigned_to: Optional[str] = None,
        assigned_role: Optional[str] = None,
        priority: int = 1,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Task], Optional[TaskMessage]]:
        """
        Delegate a task to an agent.
        
        Args:
            title: Short title of the task
            description: Detailed description of the task
            created_by: ID of the agent creating the task
            assigned_to: ID of the agent to assign the task to (optional)
            assigned_role: Role of the agent to assign the task to (optional)
            priority: Task priority (1-5, with 5 being highest)
            due_date: When the task should be completed
            dependencies: List of task IDs that must be completed before this task
            metadata: Additional metadata for the task
            
        Returns:
            Tuple of (Task, TaskMessage) if successful, (None, None) otherwise
            
        Note:
            Either assigned_to or assigned_role must be provided.
        """
        if not assigned_to and not assigned_role:
            logger.error("Either assigned_to or assigned_role must be provided")
            return None, None
            
        # If only role is provided, find an agent with that role
        if not assigned_to and assigned_role:
            assigned_to = self.get_agent_by_role(assigned_role)
            if not assigned_to:
                logger.error(f"No agent found with role {assigned_role}")
                return None, None
                
        # Create the task
        task = self._task_manager.create_task(
            title=title,
            description=description,
            assigned_to=assigned_to,
            created_by=created_by,
            priority=priority,
            due_date=due_date,
            dependencies=dependencies,
            metadata=metadata
        )
        
        # Create and send the task message
        task_message = TaskMessage(
            sender=created_by,
            recipients=[assigned_to],
            content=description,
            task_id=task.id,
            priority=priority,
            due_date=due_date,
            dependencies=dependencies,
            metadata={"title": title, **(metadata or {})}
        )
        
        self._message_bus.publish(task_message)
        
        logger.info(f"Task {task.id} delegated from {created_by} to {assigned_to}")
        return task, task_message

    def update_task_status(
        self,
        task_id: str,
        agent_id: str,
        status: TaskStatus,
        progress: float = None,
        note: str = None
    ) -> Tuple[bool, Optional[StatusUpdateMessage]]:
        """
        Update the status of a task and notify relevant agents.
        
        Args:
            task_id: ID of the task to update
            agent_id: ID of the agent updating the task
            status: New status of the task
            progress: New progress percentage (0.0 to 1.0)
            note: Optional note about the status update
            
        Returns:
            Tuple of (success, StatusUpdateMessage)
        """
        task = self._task_manager.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False, None
            
        # Check if the agent is authorized to update this task
        if task.assigned_to != agent_id and task.created_by != agent_id:
            logger.error(f"Agent {agent_id} not authorized to update task {task_id}")
            return False, None
            
        # Update the task status
        success = self._task_manager.update_task_status(task_id, status, progress, note)
        if not success:
            return False, None
            
        # Create status update message
        content = f"Task '{task.title}' status updated to {status.value}"
        if note:
            content += f": {note}"
            
        status_message = StatusUpdateMessage(
            sender=agent_id,
            recipients=[task.created_by] if task.created_by != agent_id else [],
            content=content,
            task_id=task_id,
            status=status.value,
            progress=progress or task.progress
        )
        
        # Add the task assignee to recipients if they're not the sender
        if task.assigned_to != agent_id and task.assigned_to not in status_message.recipients:
            status_message.recipients.append(task.assigned_to)
            
        # If no recipients (e.g., if agent is both creator and assignee), don't send
        if status_message.recipients:
            self._message_bus.publish(status_message)
            
        logger.info(f"Task {task_id} status updated to {status.value} by {agent_id}")
        return True, status_message

    def respond_to_task(
        self,
        task_id: str,
        agent_id: str,
        response_content: str
    ) -> Tuple[bool, Optional[ResponseMessage]]:
        """
        Send a response about a task.
        
        Args:
            task_id: ID of the task to respond to
            agent_id: ID of the agent sending the response
            response_content: Content of the response
            
        Returns:
            Tuple of (success, ResponseMessage)
        """
        task = self._task_manager.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False, None
            
        # Create response message
        response_message = ResponseMessage(
            sender=agent_id,
            recipients=[task.created_by] if task.created_by != agent_id else [],
            content=response_content,
            in_reply_to=task_id
        )
        
        # Add the task assignee to recipients if they're not the sender
        if task.assigned_to != agent_id and task.assigned_to not in response_message.recipients:
            response_message.recipients.append(task.assigned_to)
            
        # If no recipients, don't send
        if not response_message.recipients:
            logger.warning(f"No recipients for response to task {task_id}")
            return False, None
            
        self._message_bus.publish(response_message)
        
        # Add the response as a note to the task
        task.add_note(f"Response from {agent_id}: {response_content}")
        
        logger.info(f"Response sent for task {task_id} by {agent_id}")
        return True, response_message

    def get_agent_tasks(self, agent_id: str, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """
        Get all tasks assigned to an agent.
        
        Args:
            agent_id: ID of the agent
            status_filter: Optional filter for task status
            
        Returns:
            List of tasks assigned to the agent
        """
        return self._task_manager.get_agent_tasks(agent_id, status_filter)

    def get_agent_messages(self, agent_id: str, unread_only: bool = False) -> List[Message]:
        """
        Get all messages for an agent.
        
        Args:
            agent_id: ID of the agent
            unread_only: If True, only return unread messages
            
        Returns:
            List of messages for the agent
        """
        return self._message_bus.get_messages_for_agent(agent_id, unread_only)

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a task by its ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            The task if found, None otherwise
        """
        return self._task_manager.get_task(task_id)

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """
        Get a message by its ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            The message if found, None otherwise
        """
        return self._message_bus.get_message_by_id(message_id)

    def get_role_capabilities(self, role: str) -> List[str]:
        """
        Get the capabilities of a role.
        
        Args:
            role: Role to get capabilities for
            
        Returns:
            List of capabilities for the role
        """
        return self._role_capabilities.get(role, [])
