"""
Task manager for tracking and managing tasks between agents.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task in the system."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """Represents a task that can be assigned to agents."""

    def __init__(
        self,
        title: str,
        description: str,
        assigned_to: str,
        created_by: str,
        priority: int = 1,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new task.

        Args:
            title: Short title of the task
            description: Detailed description of the task
            assigned_to: ID of the agent assigned to the task
            created_by: ID of the agent who created the task
            priority: Task priority (1-5, with 5 being highest)
            due_date: When the task should be completed
            dependencies: List of task IDs that must be completed before this task
            metadata: Additional metadata for the task
        """
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.assigned_to = assigned_to
        self.created_by = created_by
        self.priority = min(max(priority, 1), 5)  # Ensure priority is between 1-5
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.due_date = due_date
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.notes = []
        self.completed_at = None

    def update_status(self, status: TaskStatus, progress: float = None, note: str = None) -> None:
        """
        Update the status of the task.

        Args:
            status: New status of the task
            progress: New progress percentage (0.0 to 1.0)
            note: Optional note about the status update
        """
        self.status = status
        if progress is not None:
            self.progress = min(max(progress, 0.0), 1.0)  # Ensure progress is between 0-1
        
        if status == TaskStatus.COMPLETED:
            self.progress = 1.0
            self.completed_at = datetime.now()
        
        if note:
            self.add_note(note)
            
        self.updated_at = datetime.now()

    def add_note(self, note: str) -> None:
        """
        Add a note to the task.

        Args:
            note: The note to add
        """
        self.notes.append({
            "content": note,
            "timestamp": datetime.now()
        })
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary.

        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "created_by": self.created_by,
            "priority": self.priority,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "notes": self.notes,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Create a task from a dictionary.

        Args:
            data: Dictionary representation of the task

        Returns:
            Task object
        """
        due_date = None
        if data.get("due_date"):
            due_date = datetime.fromisoformat(data["due_date"])
            
        task = cls(
            title=data["title"],
            description=data["description"],
            assigned_to=data["assigned_to"],
            created_by=data["created_by"],
            priority=data["priority"],
            due_date=due_date,
            dependencies=data["dependencies"],
            metadata=data["metadata"]
        )
        
        task.id = data["id"]
        task.status = TaskStatus(data["status"])
        task.progress = data["progress"]
        task.created_at = datetime.fromisoformat(data["created_at"])
        task.updated_at = datetime.fromisoformat(data["updated_at"])
        task.notes = data["notes"]
        
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
            
        return task


class TaskManager:
    """
    Manages tasks between agents in the system.
    
    This class provides functionality to create, assign, update, and track
    tasks across different agents.
    """

    _instance = None

    def __new__(cls):
        """
        Create a singleton instance of the TaskManager.
        
        Returns:
            The singleton TaskManager instance
        """
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the task manager if not already initialized."""
        if not self._initialized:
            self._tasks = {}  # task_id -> Task
            self._agent_tasks = {}  # agent_id -> list of task IDs
            self._initialized = True
            logger.info("TaskManager initialized")

    def create_task(
        self,
        title: str,
        description: str,
        assigned_to: str,
        created_by: str,
        priority: int = 1,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Create a new task.

        Args:
            title: Short title of the task
            description: Detailed description of the task
            assigned_to: ID of the agent assigned to the task
            created_by: ID of the agent who created the task
            priority: Task priority (1-5, with 5 being highest)
            due_date: When the task should be completed
            dependencies: List of task IDs that must be completed before this task
            metadata: Additional metadata for the task
            
        Returns:
            The created task
        """
        task = Task(
            title=title,
            description=description,
            assigned_to=assigned_to,
            created_by=created_by,
            priority=priority,
            due_date=due_date,
            dependencies=dependencies,
            metadata=metadata
        )
        
        self._tasks[task.id] = task
        
        if assigned_to not in self._agent_tasks:
            self._agent_tasks[assigned_to] = []
        self._agent_tasks[assigned_to].append(task.id)
        
        logger.info(f"Task {task.id} created and assigned to {assigned_to}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by its ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            The task if found, None otherwise
        """
        return self._tasks.get(task_id)

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: float = None,
        note: str = None
    ) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            status: New status of the task
            progress: New progress percentage (0.0 to 1.0)
            note: Optional note about the status update
            
        Returns:
            True if successful, False otherwise
        """
        task = self.get_task(task_id)
        if task:
            task.update_status(status, progress, note)
            logger.info(f"Task {task_id} updated to status {status.value}")
            return True
        return False

    def reassign_task(self, task_id: str, new_assignee: str) -> bool:
        """
        Reassign a task to a different agent.
        
        Args:
            task_id: ID of the task to reassign
            new_assignee: ID of the agent to assign the task to
            
        Returns:
            True if successful, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return False
            
        # Remove from current assignee's list
        if task.assigned_to in self._agent_tasks and task_id in self._agent_tasks[task.assigned_to]:
            self._agent_tasks[task.assigned_to].remove(task_id)
            
        # Add to new assignee's list
        if new_assignee not in self._agent_tasks:
            self._agent_tasks[new_assignee] = []
        self._agent_tasks[new_assignee].append(task_id)
        
        # Update task
        old_assignee = task.assigned_to
        task.assigned_to = new_assignee
        task.updated_at = datetime.now()
        task.add_note(f"Reassigned from {old_assignee} to {new_assignee}")
        
        logger.info(f"Task {task_id} reassigned from {old_assignee} to {new_assignee}")
        return True

    def get_agent_tasks(self, agent_id: str, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """
        Get all tasks assigned to an agent.
        
        Args:
            agent_id: ID of the agent
            status_filter: Optional filter for task status
            
        Returns:
            List of tasks assigned to the agent
        """
        if agent_id not in self._agent_tasks:
            return []
            
        tasks = []
        for task_id in self._agent_tasks[agent_id]:
            task = self.get_task(task_id)
            if task and (status_filter is None or task.status == status_filter):
                tasks.append(task)
                
        return tasks

    def get_all_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """
        Get all tasks in the system.
        
        Args:
            status_filter: Optional filter for task status
            
        Returns:
            List of all tasks
        """
        if status_filter is None:
            return list(self._tasks.values())
        else:
            return [task for task in self._tasks.values() if task.status == status_filter]

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the system.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            True if successful, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return False
            
        # Remove from assignee's list
        if task.assigned_to in self._agent_tasks and task_id in self._agent_tasks[task.assigned_to]:
            self._agent_tasks[task.assigned_to].remove(task_id)
            
        # Remove from tasks dictionary
        del self._tasks[task_id]
        
        logger.info(f"Task {task_id} deleted")
        return True

    def clear_all_tasks(self) -> None:
        """Clear all tasks from the system."""
        self._tasks = {}
        self._agent_tasks = {}
        logger.info("All tasks cleared")
