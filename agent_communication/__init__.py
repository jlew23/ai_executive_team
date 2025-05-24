"""
Agent Communication Module for AI Executive Team.

This module provides the infrastructure for inter-agent communication,
task delegation, and coordination between different AI agents.
"""

from .message_bus import MessageBus
from .task_manager import TaskManager
from .delegation_system import DelegationSystem
from .message import Message, TaskMessage, StatusUpdateMessage, ResponseMessage

__all__ = [
    'MessageBus',
    'TaskManager',
    'DelegationSystem',
    'Message',
    'TaskMessage',
    'StatusUpdateMessage',
    'ResponseMessage',
]
