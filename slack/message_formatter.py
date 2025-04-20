"""
Message formatter for Slack messages.
"""

import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class SlackMessageFormatter:
    """
    Formatter for Slack messages.
    
    This class provides functionality for:
    1. Creating formatted messages using Block Kit
    2. Building common message patterns
    3. Converting markdown to Slack format
    4. Creating interactive components
    """
    
    def __init__(self):
        """
        Initialize the message formatter.
        """
        pass
    
    def format_text(self, text: str) -> str:
        """
        Format text for Slack, converting markdown to Slack's format.
        
        Args:
            text: Text to format
            
        Returns:
            Formatted text
        """
        # Replace markdown headers with bold text
        for i in range(6, 0, -1):
            heading = '#' * i
            text = text.replace(f"{heading} ", f"*")
            text = text.replace(f"\n{heading} ", f"\n*")
        
        # Replace markdown bold with Slack bold
        text = text.replace("**", "*")
        
        # Replace markdown italic with Slack italic
        text = text.replace("_", "_")
        
        # Replace markdown code blocks with Slack code blocks
        text = text.replace("```", "```")
        
        # Replace markdown inline code with Slack inline code
        text = text.replace("`", "`")
        
        return text
    
    def create_text_block(self, text: str, markdown: bool = True) -> Dict[str, Any]:
        """
        Create a text block.
        
        Args:
            text: Text content
            markdown: Whether to parse markdown in the text
            
        Returns:
            Text block
        """
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn" if markdown else "plain_text",
                "text": text
            }
        }
    
    def create_header_block(self, text: str) -> Dict[str, Any]:
        """
        Create a header block.
        
        Args:
            text: Header text
            
        Returns:
            Header block
        """
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True
            }
        }
    
    def create_divider_block(self) -> Dict[str, Any]:
        """
        Create a divider block.
        
        Returns:
            Divider block
        """
        return {
            "type": "divider"
        }
    
    def create_image_block(
        self,
        image_url: str,
        alt_text: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an image block.
        
        Args:
            image_url: URL of the image
            alt_text: Alternative text for the image
            title: Optional title for the image
            
        Returns:
            Image block
        """
        block = {
            "type": "image",
            "image_url": image_url,
            "alt_text": alt_text
        }
        
        if title:
            block["title"] = {
                "type": "plain_text",
                "text": title,
                "emoji": True
            }
            
        return block
    
    def create_button_block(
        self,
        text: str,
        action_id: str,
        value: str,
        style: Optional[str] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a button element.
        
        Args:
            text: Button text
            action_id: Action identifier
            value: Value to send when button is clicked
            style: Button style ("primary", "danger", or None for default)
            url: Optional URL to open when button is clicked
            
        Returns:
            Button element
        """
        button = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True
            },
            "action_id": action_id,
            "value": value
        }
        
        if style:
            button["style"] = style
            
        if url:
            button["url"] = url
            
        return button
    
    def create_actions_block(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create an actions block with interactive elements.
        
        Args:
            elements: List of interactive elements (buttons, selects, etc.)
            
        Returns:
            Actions block
        """
        return {
            "type": "actions",
            "elements": elements
        }
    
    def create_select_menu(
        self,
        placeholder: str,
        action_id: str,
        options: List[Dict[str, str]],
        initial_option: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a select menu element.
        
        Args:
            placeholder: Placeholder text
            action_id: Action identifier
            options: List of options, each with "text" and "value" keys
            initial_option: Optional initial selected option
            
        Returns:
            Select menu element
        """
        select_menu = {
            "type": "static_select",
            "placeholder": {
                "type": "plain_text",
                "text": placeholder,
                "emoji": True
            },
            "action_id": action_id,
            "options": [
                {
                    "text": {
                        "type": "plain_text",
                        "text": option["text"],
                        "emoji": True
                    },
                    "value": option["value"]
                }
                for option in options
            ]
        }
        
        if initial_option:
            select_menu["initial_option"] = {
                "text": {
                    "type": "plain_text",
                    "text": initial_option["text"],
                    "emoji": True
                },
                "value": initial_option["value"]
            }
            
        return select_menu
    
    def create_context_block(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a context block with text or images.
        
        Args:
            elements: List of text or image elements
            
        Returns:
            Context block
        """
        return {
            "type": "context",
            "elements": elements
        }
    
    def create_modal(
        self,
        title: str,
        callback_id: str,
        blocks: List[Dict[str, Any]],
        submit_text: str = "Submit",
        close_text: str = "Cancel",
        private_metadata: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a modal view.
        
        Args:
            title: Modal title
            callback_id: Callback identifier
            blocks: List of blocks to include in the modal
            submit_text: Text for the submit button
            close_text: Text for the close button
            private_metadata: Optional private metadata
            
        Returns:
            Modal view
        """
        modal = {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": title,
                "emoji": True
            },
            "submit": {
                "type": "plain_text",
                "text": submit_text,
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": close_text,
                "emoji": True
            },
            "callback_id": callback_id,
            "blocks": blocks
        }
        
        if private_metadata:
            modal["private_metadata"] = private_metadata
            
        return modal
    
    def create_input_block(
        self,
        label: str,
        action_id: str,
        placeholder: Optional[str] = None,
        initial_value: Optional[str] = None,
        multiline: bool = False,
        optional: bool = False
    ) -> Dict[str, Any]:
        """
        Create an input block.
        
        Args:
            label: Label for the input
            action_id: Action identifier
            placeholder: Optional placeholder text
            initial_value: Optional initial value
            multiline: Whether to use a multiline input
            optional: Whether the input is optional
            
        Returns:
            Input block
        """
        input_element = {
            "type": "plain_text_input",
            "action_id": action_id
        }
        
        if placeholder:
            input_element["placeholder"] = {
                "type": "plain_text",
                "text": placeholder,
                "emoji": True
            }
            
        if initial_value:
            input_element["initial_value"] = initial_value
            
        if multiline:
            input_element["multiline"] = True
            
        block = {
            "type": "input",
            "label": {
                "type": "plain_text",
                "text": label,
                "emoji": True
            },
            "element": input_element
        }
        
        if optional:
            block["optional"] = True
            
        return block
    
    def create_message_blocks(
        self,
        header: Optional[str] = None,
        text: Optional[str] = None,
        fields: Optional[List[Dict[str, str]]] = None,
        image_url: Optional[str] = None,
        image_alt: Optional[str] = None,
        buttons: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a complete message with multiple blocks.
        
        Args:
            header: Optional header text
            text: Optional main text
            fields: Optional list of fields, each with "title" and "value" keys
            image_url: Optional image URL
            image_alt: Optional image alt text
            buttons: Optional list of buttons
            context: Optional context text
            
        Returns:
            List of blocks
        """
        blocks = []
        
        # Add header if provided
        if header:
            blocks.append(self.create_header_block(header))
            
        # Add main text if provided
        if text:
            blocks.append(self.create_text_block(text))
            
        # Add fields if provided
        if fields:
            fields_block = {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{field['title']}*\n{field['value']}"
                    }
                    for field in fields
                ]
            }
            blocks.append(fields_block)
            
        # Add image if provided
        if image_url and image_alt:
            blocks.append(self.create_image_block(image_url, image_alt))
            
        # Add buttons if provided
        if buttons:
            button_elements = [
                self.create_button_block(
                    button.get("text", ""),
                    button.get("action_id", ""),
                    button.get("value", ""),
                    button.get("style"),
                    button.get("url")
                )
                for button in buttons
            ]
            blocks.append(self.create_actions_block(button_elements))
            
        # Add context if provided
        if context:
            blocks.append(self.create_context_block([
                {
                    "type": "mrkdwn",
                    "text": context
                }
            ]))
            
        return blocks
