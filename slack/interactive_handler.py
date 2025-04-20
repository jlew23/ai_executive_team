"""
Interactive handler for Slack interactive components.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SlackInteraction:
    """
    Representation of a Slack interactive component interaction.
    """
    type: str
    user_id: str
    channel_id: Optional[str]
    team_id: str
    trigger_id: str
    response_url: Optional[str]
    action_id: Optional[str]
    value: Optional[str]
    view_id: Optional[str]
    callback_id: Optional[str]
    data: Dict[str, Any]

class SlackInteractiveHandler:
    """
    Handler for Slack interactive components.
    
    This class provides functionality for:
    1. Registering interaction handlers
    2. Processing button clicks, select menus, and modals
    3. Managing view submissions and cancellations
    4. Handling interactive message components
    """
    
    def __init__(self, slack_client, auth_manager=None):
        """
        Initialize the interactive handler.
        
        Args:
            slack_client: Slack client instance
            auth_manager: Optional authentication manager for permission checks
        """
        self.slack_client = slack_client
        self.auth_manager = auth_manager
        self.action_handlers = {}
        self.view_handlers = {}
        
        # Register with the Slack client
        self._register_with_client()
    
    def register_action_handler(
        self,
        action_id: str,
        handler: Callable[[SlackInteraction], None],
        required_permission: Optional[str] = None
    ) -> None:
        """
        Register a handler for an interactive action.
        
        Args:
            action_id: Action identifier
            handler: Function to call when the action is triggered
            required_permission: Optional permission required to use the action
        """
        self.action_handlers[action_id] = {
            "handler": handler,
            "required_permission": required_permission
        }
    
    def register_view_handler(
        self,
        callback_id: str,
        handler: Callable[[SlackInteraction], None],
        required_permission: Optional[str] = None
    ) -> None:
        """
        Register a handler for a view submission or cancellation.
        
        Args:
            callback_id: Callback identifier
            handler: Function to call when the view is submitted or cancelled
            required_permission: Optional permission required to submit the view
        """
        self.view_handlers[callback_id] = {
            "handler": handler,
            "required_permission": required_permission
        }
    
    def handle_interaction(self, payload: Dict[str, Any]) -> None:
        """
        Handle an incoming interactive component interaction.
        
        Args:
            payload: Raw interaction payload from Slack
        """
        # Extract common information
        interaction_type = payload.get("type", "")
        user_id = payload.get("user", {}).get("id", "")
        team_id = payload.get("team", {}).get("id", "")
        trigger_id = payload.get("trigger_id", "")
        
        # Handle different interaction types
        if interaction_type == "block_actions":
            self._handle_block_actions(payload, user_id, team_id, trigger_id)
        elif interaction_type == "view_submission":
            self._handle_view_submission(payload, user_id, team_id, trigger_id)
        elif interaction_type == "view_closed":
            self._handle_view_closed(payload, user_id, team_id, trigger_id)
        elif interaction_type == "message_action":
            self._handle_message_action(payload, user_id, team_id, trigger_id)
        else:
            logger.warning(f"Unknown interaction type: {interaction_type}")
    
    def _handle_block_actions(
        self,
        payload: Dict[str, Any],
        user_id: str,
        team_id: str,
        trigger_id: str
    ) -> None:
        """
        Handle block actions (buttons, select menus, etc.).
        
        Args:
            payload: Raw interaction payload
            user_id: User ID
            team_id: Team ID
            trigger_id: Trigger ID
        """
        # Extract additional information
        channel_id = payload.get("channel", {}).get("id")
        response_url = payload.get("response_url")
        
        # Process each action
        for action in payload.get("actions", []):
            action_id = action.get("action_id", "")
            value = action.get("value")
            
            # Create SlackInteraction object
            interaction = SlackInteraction(
                type="block_actions",
                user_id=user_id,
                channel_id=channel_id,
                team_id=team_id,
                trigger_id=trigger_id,
                response_url=response_url,
                action_id=action_id,
                value=value,
                view_id=None,
                callback_id=None,
                data=payload
            )
            
            # Check if we have a handler for this action
            if action_id not in self.action_handlers:
                logger.warning(f"No handler registered for action {action_id}")
                continue
                
            # Check permissions if auth manager is available
            handler_info = self.action_handlers[action_id]
            required_permission = handler_info.get("required_permission")
            
            if required_permission and self.auth_manager:
                has_permission = self.auth_manager.check_permission(
                    user_id,
                    required_permission,
                    team_id
                )
                
                if not has_permission:
                    logger.warning(f"User {user_id} does not have permission {required_permission} for action {action_id}")
                    continue
            
            # Call the handler
            try:
                handler_info["handler"](interaction)
            except Exception as e:
                logger.error(f"Error handling action {action_id}: {e}")
    
    def _handle_view_submission(
        self,
        payload: Dict[str, Any],
        user_id: str,
        team_id: str,
        trigger_id: str
    ) -> None:
        """
        Handle view submissions (modals).
        
        Args:
            payload: Raw interaction payload
            user_id: User ID
            team_id: Team ID
            trigger_id: Trigger ID
        """
        # Extract additional information
        view = payload.get("view", {})
        view_id = view.get("id")
        callback_id = view.get("callback_id")
        
        # Create SlackInteraction object
        interaction = SlackInteraction(
            type="view_submission",
            user_id=user_id,
            channel_id=None,
            team_id=team_id,
            trigger_id=trigger_id,
            response_url=None,
            action_id=None,
            value=None,
            view_id=view_id,
            callback_id=callback_id,
            data=payload
        )
        
        # Check if we have a handler for this view
        if callback_id not in self.view_handlers:
            logger.warning(f"No handler registered for view {callback_id}")
            return
            
        # Check permissions if auth manager is available
        handler_info = self.view_handlers[callback_id]
        required_permission = handler_info.get("required_permission")
        
        if required_permission and self.auth_manager:
            has_permission = self.auth_manager.check_permission(
                user_id,
                required_permission,
                team_id
            )
            
            if not has_permission:
                logger.warning(f"User {user_id} does not have permission {required_permission} for view {callback_id}")
                return
        
        # Call the handler
        try:
            handler_info["handler"](interaction)
        except Exception as e:
            logger.error(f"Error handling view submission {callback_id}: {e}")
    
    def _handle_view_closed(
        self,
        payload: Dict[str, Any],
        user_id: str,
        team_id: str,
        trigger_id: str
    ) -> None:
        """
        Handle view closures (modals).
        
        Args:
            payload: Raw interaction payload
            user_id: User ID
            team_id: Team ID
            trigger_id: Trigger ID
        """
        # Extract additional information
        view = payload.get("view", {})
        view_id = view.get("id")
        callback_id = view.get("callback_id")
        
        # Create SlackInteraction object
        interaction = SlackInteraction(
            type="view_closed",
            user_id=user_id,
            channel_id=None,
            team_id=team_id,
            trigger_id=trigger_id,
            response_url=None,
            action_id=None,
            value=None,
            view_id=view_id,
            callback_id=callback_id,
            data=payload
        )
        
        # Check if we have a handler for this view
        if callback_id not in self.view_handlers:
            logger.warning(f"No handler registered for view {callback_id}")
            return
            
        # Call the handler
        try:
            handler_info = self.view_handlers[callback_id]
            handler_info["handler"](interaction)
        except Exception as e:
            logger.error(f"Error handling view closure {callback_id}: {e}")
    
    def _handle_message_action(
        self,
        payload: Dict[str, Any],
        user_id: str,
        team_id: str,
        trigger_id: str
    ) -> None:
        """
        Handle message actions (shortcuts).
        
        Args:
            payload: Raw interaction payload
            user_id: User ID
            team_id: Team ID
            trigger_id: Trigger ID
        """
        # Extract additional information
        callback_id = payload.get("callback_id")
        channel_id = payload.get("channel", {}).get("id")
        response_url = payload.get("response_url")
        
        # Create SlackInteraction object
        interaction = SlackInteraction(
            type="message_action",
            user_id=user_id,
            channel_id=channel_id,
            team_id=team_id,
            trigger_id=trigger_id,
            response_url=response_url,
            action_id=None,
            value=None,
            view_id=None,
            callback_id=callback_id,
            data=payload
        )
        
        # Check if we have a handler for this action
        if callback_id not in self.action_handlers:
            logger.warning(f"No handler registered for message action {callback_id}")
            return
            
        # Check permissions if auth manager is available
        handler_info = self.action_handlers[callback_id]
        required_permission = handler_info.get("required_permission")
        
        if required_permission and self.auth_manager:
            has_permission = self.auth_manager.check_permission(
                user_id,
                required_permission,
                team_id
            )
            
            if not has_permission:
                logger.warning(f"User {user_id} does not have permission {required_permission} for message action {callback_id}")
                return
        
        # Call the handler
        try:
            handler_info["handler"](interaction)
        except Exception as e:
            logger.error(f"Error handling message action {callback_id}: {e}")
    
    def _register_with_client(self) -> None:
        """
        Register this handler with the Slack client.
        """
        # Register for interactive components
        self.slack_client.register_event_handler("interactive", self.handle_interaction)
