"""
Event handler for Slack events.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SlackEvent:
    """
    Representation of a Slack event.
    """
    type: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    text: Optional[str] = None
    ts: Optional[str] = None
    thread_ts: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class SlackEventHandler:
    """
    Handler for Slack events.
    
    This class provides functionality for:
    1. Processing incoming Slack events
    2. Routing events to appropriate handlers
    3. Filtering events based on criteria
    4. Managing event subscriptions
    """
    
    def __init__(self, slack_client):
        """
        Initialize the event handler.
        
        Args:
            slack_client: Slack client instance
        """
        self.slack_client = slack_client
        self.event_handlers = {}
        self.bot_user_id = slack_client.bot_user_id
        
        # Register with the Slack client
        self._register_with_client()
    
    def register_handler(
        self,
        event_type: str,
        handler: Callable[[SlackEvent], None],
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when the event is received
            filters: Optional filters to apply to events
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        self.event_handlers[event_type].append({
            "handler": handler,
            "filters": filters or {}
        })
    
    def handle_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle an incoming Slack event.
        
        Args:
            event_data: Raw event data from Slack
        """
        # Extract event type
        if "event" in event_data:
            # Events API format
            event = event_data["event"]
            event_type = event.get("type")
        elif "type" in event_data:
            # Socket Mode format
            event = event_data
            event_type = event.get("type")
        else:
            logger.warning(f"Unknown event format: {event_data}")
            return
            
        # Skip events from the bot itself
        if event.get("user") == self.bot_user_id:
            return
            
        # Create SlackEvent object
        slack_event = self._create_slack_event(event_type, event)
        
        # Call registered handlers
        self._call_event_handlers(event_type, slack_event)
    
    def _create_slack_event(self, event_type: str, event_data: Dict[str, Any]) -> SlackEvent:
        """
        Create a SlackEvent object from raw event data.
        
        Args:
            event_type: Type of event
            event_data: Raw event data
            
        Returns:
            SlackEvent object
        """
        # Extract common fields
        user_id = event_data.get("user")
        channel_id = event_data.get("channel")
        text = event_data.get("text")
        ts = event_data.get("ts")
        thread_ts = event_data.get("thread_ts")
        
        # Create event object
        return SlackEvent(
            type=event_type,
            data=event_data,
            user_id=user_id,
            channel_id=channel_id,
            text=text,
            ts=ts,
            thread_ts=thread_ts
        )
    
    def _call_event_handlers(self, event_type: str, event: SlackEvent) -> None:
        """
        Call all registered handlers for an event type.
        
        Args:
            event_type: Type of event
            event: SlackEvent object
        """
        # Call specific handlers for this event type
        for handler_info in self.event_handlers.get(event_type, []):
            if self._event_matches_filters(event, handler_info["filters"]):
                try:
                    handler_info["handler"](event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
                    
        # Call wildcard handlers
        for handler_info in self.event_handlers.get("*", []):
            if self._event_matches_filters(event, handler_info["filters"]):
                try:
                    handler_info["handler"](event)
                except Exception as e:
                    logger.error(f"Error in wildcard event handler for {event_type}: {e}")
    
    def _event_matches_filters(self, event: SlackEvent, filters: Dict[str, Any]) -> bool:
        """
        Check if an event matches the specified filters.
        
        Args:
            event: SlackEvent object
            filters: Filters to apply
            
        Returns:
            True if the event matches all filters, False otherwise
        """
        for key, value in filters.items():
            if key == "channel_id" and event.channel_id != value:
                return False
            elif key == "user_id" and event.user_id != value:
                return False
            elif key == "text_contains" and (not event.text or value not in event.text):
                return False
            elif key == "in_thread" and not event.thread_ts:
                return False
                
        return True
    
    def _register_with_client(self) -> None:
        """
        Register this handler with the Slack client.
        """
        # Register for all events
        self.slack_client.register_event_handler("*", self.handle_event)
        
        # Register for specific events we're interested in
        for event_type in ["message", "app_mention", "reaction_added"]:
            self.slack_client.register_event_handler(event_type, self.handle_event)
