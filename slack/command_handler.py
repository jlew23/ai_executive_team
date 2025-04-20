"""
Command handler for Slack slash commands.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SlackCommand:
    """
    Representation of a Slack slash command.
    """
    command: str
    text: str
    user_id: str
    channel_id: str
    team_id: str
    response_url: str
    trigger_id: str
    data: Dict[str, Any]

class SlackCommandHandler:
    """
    Handler for Slack slash commands.
    
    This class provides functionality for:
    1. Registering command handlers
    2. Parsing and routing commands
    3. Generating command responses
    4. Managing command permissions
    """
    
    def __init__(self, slack_client, auth_manager=None):
        """
        Initialize the command handler.
        
        Args:
            slack_client: Slack client instance
            auth_manager: Optional authentication manager for permission checks
        """
        self.slack_client = slack_client
        self.auth_manager = auth_manager
        self.command_handlers = {}
        
        # Register with the Slack client
        self._register_with_client()
    
    def register_command(
        self,
        command: str,
        handler: Callable[[SlackCommand], None],
        description: str = "",
        required_permission: Optional[str] = None
    ) -> None:
        """
        Register a handler for a slash command.
        
        Args:
            command: Command name (e.g., "/mycommand")
            handler: Function to call when the command is received
            description: Description of the command
            required_permission: Optional permission required to use the command
        """
        self.command_handlers[command] = {
            "handler": handler,
            "description": description,
            "required_permission": required_permission
        }
    
    def handle_command(self, command_data: Dict[str, Any]) -> None:
        """
        Handle an incoming slash command.
        
        Args:
            command_data: Raw command data from Slack
        """
        # Extract command information
        command = command_data.get("command", "")
        text = command_data.get("text", "")
        user_id = command_data.get("user_id", "")
        channel_id = command_data.get("channel_id", "")
        team_id = command_data.get("team_id", "")
        response_url = command_data.get("response_url", "")
        trigger_id = command_data.get("trigger_id", "")
        
        # Create SlackCommand object
        slack_command = SlackCommand(
            command=command,
            text=text,
            user_id=user_id,
            channel_id=channel_id,
            team_id=team_id,
            response_url=response_url,
            trigger_id=trigger_id,
            data=command_data
        )
        
        # Check if we have a handler for this command
        if command not in self.command_handlers:
            logger.warning(f"No handler registered for command {command}")
            self._send_ephemeral_response(
                channel_id,
                user_id,
                f"Sorry, I don't know how to handle the command `{command}`."
            )
            return
            
        # Check permissions if auth manager is available
        handler_info = self.command_handlers[command]
        required_permission = handler_info.get("required_permission")
        
        if required_permission and self.auth_manager:
            has_permission = self.auth_manager.check_permission(
                user_id,
                required_permission,
                team_id
            )
            
            if not has_permission:
                logger.warning(f"User {user_id} does not have permission {required_permission} for command {command}")
                self._send_ephemeral_response(
                    channel_id,
                    user_id,
                    f"Sorry, you don't have permission to use the command `{command}`."
                )
                return
        
        # Call the handler
        try:
            handler_info["handler"](slack_command)
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}")
            self._send_ephemeral_response(
                channel_id,
                user_id,
                f"Sorry, an error occurred while processing your command: {str(e)}"
            )
    
    def get_command_list(self) -> List[Dict[str, str]]:
        """
        Get a list of all registered commands.
        
        Returns:
            List of command information
        """
        return [
            {
                "command": command,
                "description": info.get("description", ""),
                "required_permission": info.get("required_permission")
            }
            for command, info in self.command_handlers.items()
        ]
    
    def _send_ephemeral_response(
        self,
        channel_id: str,
        user_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Send an ephemeral response to a command.
        
        Args:
            channel_id: Channel ID
            user_id: User ID
            text: Response text
            blocks: Optional Block Kit blocks
        """
        try:
            self.slack_client.send_message(
                channel=channel_id,
                text=text,
                blocks=blocks,
                ephemeral=True,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Error sending ephemeral response: {e}")
    
    def _register_with_client(self) -> None:
        """
        Register this handler with the Slack client.
        """
        # Register for slash commands
        self.slack_client.register_event_handler("slash_commands", self.handle_command)
