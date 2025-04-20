"""
Unit tests for the Slack integration components.
"""

import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit
def test_slack_client_initialization(mock_slack):
    """Test that the Slack client initializes correctly."""
    from slack.client import SlackClient
    
    client = SlackClient(bot_token="xoxb-test-token")
    assert client is not None
    assert hasattr(client, 'send_message')
    assert hasattr(client, 'send_blocks')
    assert hasattr(client, 'update_message')

@pytest.mark.unit
def test_slack_client_send_message(mock_slack):
    """Test that the Slack client can send messages."""
    from slack.client import SlackClient
    
    client = SlackClient(bot_token="xoxb-test-token")
    
    # Send a message
    result = client.send_message(
        channel="C12345",
        text="This is a test message"
    )
    
    # Check that the message was sent
    assert result['ok'] == True
    
    # Check that the Slack client was called correctly
    mock_slack.chat_postMessage.assert_called_once_with(
        channel="C12345",
        text="This is a test message"
    )

@pytest.mark.unit
def test_slack_client_send_blocks(mock_slack):
    """Test that the Slack client can send block messages."""
    from slack.client import SlackClient
    
    client = SlackClient(bot_token="xoxb-test-token")
    
    # Create blocks
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "This is a test block message"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Click Me"
                    },
                    "action_id": "button_click"
                }
            ]
        }
    ]
    
    # Send blocks
    result = client.send_blocks(
        channel="C12345",
        blocks=blocks
    )
    
    # Check that the blocks were sent
    assert result['ok'] == True
    
    # Check that the Slack client was called correctly
    mock_slack.chat_postMessage.assert_called_once()
    args, kwargs = mock_slack.chat_postMessage.call_args
    assert kwargs["channel"] == "C12345"
    assert kwargs["blocks"] == blocks

@pytest.mark.unit
def test_slack_client_update_message(mock_slack):
    """Test that the Slack client can update messages."""
    from slack.client import SlackClient
    
    # Mock the update method
    mock_slack.chat_update.return_value = {'ok': True, 'message': {'text': 'Updated message'}}
    
    client = SlackClient(bot_token="xoxb-test-token")
    
    # Update a message
    result = client.update_message(
        channel="C12345",
        ts="1234567890.123456",
        text="This is an updated message"
    )
    
    # Check that the message was updated
    assert result['ok'] == True
    
    # Check that the Slack client was called correctly
    mock_slack.chat_update.assert_called_once_with(
        channel="C12345",
        ts="1234567890.123456",
        text="This is an updated message"
    )

@pytest.mark.unit
def test_event_handler():
    """Test the Slack event handler."""
    from slack.event_handler import EventHandler
    
    # Create an event handler
    handler = EventHandler()
    
    # Create a mock handler function
    mock_handler = MagicMock()
    
    # Register the handler
    handler.register("message", mock_handler)
    
    # Create an event
    event = {
        "type": "message",
        "channel": "C12345",
        "user": "U12345",
        "text": "This is a test message",
        "ts": "1234567890.123456"
    }
    
    # Handle the event
    handler.handle(event)
    
    # Check that the handler was called
    mock_handler.assert_called_once_with(event)

@pytest.mark.unit
def test_event_handler_filtering():
    """Test that the event handler filters events correctly."""
    from slack.event_handler import EventHandler
    
    # Create an event handler
    handler = EventHandler()
    
    # Create mock handler functions
    mock_handler1 = MagicMock()
    mock_handler2 = MagicMock()
    
    # Register handlers with filters
    handler.register("message", mock_handler1, channel="C12345")
    handler.register("message", mock_handler2, user="U67890")
    
    # Create events
    event1 = {
        "type": "message",
        "channel": "C12345",
        "user": "U12345",
        "text": "This is a test message",
        "ts": "1234567890.123456"
    }
    
    event2 = {
        "type": "message",
        "channel": "C67890",
        "user": "U67890",
        "text": "This is another test message",
        "ts": "1234567890.123457"
    }
    
    # Handle the events
    handler.handle(event1)
    handler.handle(event2)
    
    # Check that the handlers were called correctly
    mock_handler1.assert_called_once_with(event1)
    mock_handler2.assert_called_once_with(event2)

@pytest.mark.unit
def test_message_formatter():
    """Test the Slack message formatter."""
    from slack.message_formatter import MessageFormatter
    
    formatter = MessageFormatter()
    
    # Format a simple message
    blocks = formatter.format_message("This is a test message")
    
    # Check the blocks
    assert len(blocks) == 1
    assert blocks[0]["type"] == "section"
    assert blocks[0]["text"]["type"] == "mrkdwn"
    assert blocks[0]["text"]["text"] == "This is a test message"

@pytest.mark.unit
def test_message_formatter_with_buttons():
    """Test the Slack message formatter with buttons."""
    from slack.message_formatter import MessageFormatter
    
    formatter = MessageFormatter()
    
    # Format a message with buttons
    blocks = formatter.format_message(
        "This is a test message",
        buttons=[
            {"text": "Button 1", "action_id": "button_1"},
            {"text": "Button 2", "action_id": "button_2"}
        ]
    )
    
    # Check the blocks
    assert len(blocks) == 2
    assert blocks[0]["type"] == "section"
    assert blocks[0]["text"]["text"] == "This is a test message"
    assert blocks[1]["type"] == "actions"
    assert len(blocks[1]["elements"]) == 2
    assert blocks[1]["elements"][0]["type"] == "button"
    assert blocks[1]["elements"][0]["text"]["text"] == "Button 1"
    assert blocks[1]["elements"][0]["action_id"] == "button_1"
    assert blocks[1]["elements"][1]["text"]["text"] == "Button 2"
    assert blocks[1]["elements"][1]["action_id"] == "button_2"

@pytest.mark.unit
def test_command_handler():
    """Test the Slack command handler."""
    from slack.command_handler import CommandHandler
    
    # Create a command handler
    handler = CommandHandler()
    
    # Create a mock handler function
    mock_handler = MagicMock(return_value="Command executed")
    
    # Register the handler
    handler.register("test", mock_handler)
    
    # Create a command payload
    payload = {
        "command": "/ai_exec",
        "text": "test arg1 arg2",
        "user_id": "U12345",
        "channel_id": "C12345",
        "response_url": "https://hooks.slack.com/commands/12345"
    }
    
    # Handle the command
    response = handler.handle(payload)
    
    # Check that the handler was called
    mock_handler.assert_called_once()
    args, kwargs = mock_handler.call_args
    assert args[0] == ["arg1", "arg2"]
    assert kwargs["user_id"] == "U12345"
    assert kwargs["channel_id"] == "C12345"
    
    # Check the response
    assert response == "Command executed"

@pytest.mark.unit
def test_interactive_handler():
    """Test the Slack interactive handler."""
    from slack.interactive_handler import InteractiveHandler
    
    # Create an interactive handler
    handler = InteractiveHandler()
    
    # Create a mock handler function
    mock_handler = MagicMock(return_value="Button clicked")
    
    # Register the handler
    handler.register("button_click", mock_handler)
    
    # Create an interactive payload
    payload = {
        "type": "block_actions",
        "user": {"id": "U12345"},
        "channel": {"id": "C12345"},
        "actions": [
            {
                "type": "button",
                "action_id": "button_click",
                "value": "value1"
            }
        ]
    }
    
    # Handle the interaction
    response = handler.handle(payload)
    
    # Check that the handler was called
    mock_handler.assert_called_once_with(payload)
    
    # Check the response
    assert response == "Button clicked"
