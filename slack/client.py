"""
Slack client for interacting with the Slack API.
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional, Union, Callable
import slack_sdk
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

logger = logging.getLogger(__name__)

class SlackClient:
    """
    Client for interacting with the Slack API.
    
    This class provides functionality for:
    1. Sending messages to Slack
    2. Receiving events from Slack
    3. Managing users and channels
    4. Handling interactive components
    """
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        app_token: Optional[str] = None,
        signing_secret: Optional[str] = None
    ):
        """
        Initialize the Slack client.
        
        Args:
            bot_token: Slack bot token (defaults to SLACK_BOT_TOKEN environment variable)
            app_token: Slack app token for Socket Mode (defaults to SLACK_APP_TOKEN environment variable)
            signing_secret: Slack signing secret for request verification (defaults to SLACK_SIGNING_SECRET environment variable)
        """
        # Use environment variables if tokens not provided
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")
        self.app_token = app_token or os.environ.get("SLACK_APP_TOKEN")
        self.signing_secret = signing_secret or os.environ.get("SLACK_SIGNING_SECRET")
        
        if not self.bot_token:
            raise ValueError("Slack bot token not provided and not found in environment")
            
        # Initialize Web API client
        self.web_client = WebClient(token=self.bot_token)
        
        # Initialize Socket Mode client if app token is provided
        self.socket_mode_client = None
        if self.app_token:
            self.socket_mode_client = SocketModeClient(
                app_token=self.app_token,
                web_client=self.web_client
            )
            
        # Store bot info
        self.bot_info = None
        self.bot_user_id = None
        self._fetch_bot_info()
        
        # Event handlers
        self.event_handlers = {}
    
    def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        reply_broadcast: bool = False,
        ephemeral: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: Channel ID to send the message to
            text: Text content of the message
            blocks: Block Kit blocks for rich formatting
            thread_ts: Thread timestamp to reply to
            reply_broadcast: Whether to broadcast the reply to the channel
            ephemeral: Whether to send as an ephemeral message (only visible to the user)
            user_id: User ID to send ephemeral message to (required if ephemeral=True)
            
        Returns:
            Slack API response
        """
        try:
            if ephemeral:
                if not user_id:
                    raise ValueError("user_id is required for ephemeral messages")
                    
                return self.web_client.chat_postEphemeral(
                    channel=channel,
                    user=user_id,
                    text=text,
                    blocks=blocks,
                    thread_ts=thread_ts
                )
            else:
                return self.web_client.chat_postMessage(
                    channel=channel,
                    text=text,
                    blocks=blocks,
                    thread_ts=thread_ts,
                    reply_broadcast=reply_broadcast
                )
                
        except SlackApiError as e:
            logger.error(f"Error sending message to Slack: {e}")
            raise
    
    def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing message.
        
        Args:
            channel: Channel ID where the message was sent
            ts: Timestamp of the message to update
            text: New text content
            blocks: New Block Kit blocks
            
        Returns:
            Slack API response
        """
        try:
            return self.web_client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks
            )
        except SlackApiError as e:
            logger.error(f"Error updating message in Slack: {e}")
            raise
    
    def delete_message(
        self,
        channel: str,
        ts: str
    ) -> Dict[str, Any]:
        """
        Delete a message.
        
        Args:
            channel: Channel ID where the message was sent
            ts: Timestamp of the message to delete
            
        Returns:
            Slack API response
        """
        try:
            return self.web_client.chat_delete(
                channel=channel,
                ts=ts
            )
        except SlackApiError as e:
            logger.error(f"Error deleting message in Slack: {e}")
            raise
    
    def add_reaction(
        self,
        channel: str,
        ts: str,
        reaction: str
    ) -> Dict[str, Any]:
        """
        Add a reaction to a message.
        
        Args:
            channel: Channel ID where the message was sent
            ts: Timestamp of the message to react to
            reaction: Name of the reaction emoji (without colons)
            
        Returns:
            Slack API response
        """
        try:
            return self.web_client.reactions_add(
                channel=channel,
                timestamp=ts,
                name=reaction
            )
        except SlackApiError as e:
            logger.error(f"Error adding reaction in Slack: {e}")
            raise
    
    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """
        Get information about a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Channel information
        """
        try:
            return self.web_client.conversations_info(channel=channel_id)
        except SlackApiError as e:
            logger.error(f"Error getting channel info from Slack: {e}")
            raise
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get information about a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User information
        """
        try:
            return self.web_client.users_info(user=user_id)
        except SlackApiError as e:
            logger.error(f"Error getting user info from Slack: {e}")
            raise
    
    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when the event is received
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        self.event_handlers[event_type].append(handler)
    
    def start_socket_mode(self) -> None:
        """
        Start listening for events in Socket Mode.
        
        Raises:
            ValueError: If app token is not provided
        """
        if not self.socket_mode_client:
            raise ValueError("Socket Mode client not initialized (app token missing)")
            
        # Register handler for all events
        self.socket_mode_client.socket_mode_request_listeners.append(self._handle_socket_mode_request)
        
        # Start the client
        self.socket_mode_client.connect()
        logger.info("Slack Socket Mode client started")
    
    def stop_socket_mode(self) -> None:
        """
        Stop listening for events in Socket Mode.
        """
        if self.socket_mode_client:
            self.socket_mode_client.disconnect()
            logger.info("Slack Socket Mode client stopped")
    
    def _handle_socket_mode_request(self, client: SocketModeClient, request: SocketModeRequest) -> None:
        """
        Handle a Socket Mode request.
        
        Args:
            client: Socket Mode client
            request: Socket Mode request
        """
        # Acknowledge the request
        client.send_socket_mode_response(SocketModeResponse(envelope_id=request.envelope_id))
        
        # Extract the event
        if request.type == "events_api":
            # Handle Events API event
            event = request.payload.get("event", {})
            event_type = event.get("type")
            
            # Call registered handlers
            self._call_event_handlers(event_type, event)
            
        elif request.type == "interactive":
            # Handle interactive event (buttons, modals, etc.)
            payload = request.payload
            action_type = payload.get("type")
            
            # Call registered handlers
            self._call_event_handlers(f"interactive_{action_type}", payload)
            
        elif request.type == "slash_commands":
            # Handle slash command
            payload = request.payload
            command = payload.get("command", "")
            
            # Call registered handlers
            self._call_event_handlers(f"command_{command}", payload)
    
    def _call_event_handlers(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Call all registered handlers for an event type.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        # Call specific handlers for this event type
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
                
        # Call wildcard handlers
        for handler in self.event_handlers.get("*", []):
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in wildcard event handler for {event_type}: {e}")
    
    def _fetch_bot_info(self) -> None:
        """
        Fetch information about the bot user.
        """
        try:
            auth_info = self.web_client.auth_test()
            self.bot_user_id = auth_info["user_id"]
            
            user_info = self.web_client.users_info(user=self.bot_user_id)
            self.bot_info = user_info["user"]
            
            logger.info(f"Connected to Slack as {self.bot_info['name']} ({self.bot_user_id})")
            
        except SlackApiError as e:
            logger.error(f"Error fetching bot info from Slack: {e}")
            raise
