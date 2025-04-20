"""
Slack integration module for AI Executive Team.

This module provides functionality for interacting with Slack, including:
- Slack API client
- Event handlers for messages and interactions
- Message formatting
- User authentication and workspace management
- Slash commands and interactive components
"""

from .client import SlackClient
from .event_handler import SlackEventHandler
from .message_formatter import SlackMessageFormatter
from .auth import SlackAuth
from .command_handler import SlackCommandHandler
from .interactive_handler import SlackInteractiveHandler

__all__ = [
    'SlackClient',
    'SlackEventHandler',
    'SlackMessageFormatter',
    'SlackAuth',
    'SlackCommandHandler',
    'SlackInteractiveHandler'
]
