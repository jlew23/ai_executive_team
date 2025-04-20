"""
Local model integration for AI Executive Team.

This module provides integration with locally running LLM servers like LM Studio.
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class LocalModelIntegration:
    """
    Integration with locally running LLM servers.
    """

    def __init__(self, api_url: str = "http://127.0.0.1:1234/v1"):
        """
        Initialize the local model integration.

        Args:
            api_url: URL of the local LLM server API
        """
        self.api_url = api_url
        logger.info(f"Local model integration initialized with API URL: {api_url}")

    def set_api_url(self, api_url: str):
        """
        Set the API URL for the local model server.

        Args:
            api_url: URL of the local LLM server API
        """
        if api_url and api_url.strip():
            # Ensure the URL ends with /v1
            if not api_url.endswith('/v1'):
                if api_url.endswith('/'):
                    api_url = api_url + 'v1'
                else:
                    api_url = api_url + '/v1'
            self.api_url = api_url
            logger.info(f"Local model API URL updated to: {api_url}")

    def generate_response(self,
                         message: str,
                         agent_role: str,
                         system_prompt: Optional[str] = None,
                         model: Optional[str] = None,  # Not used for local models
                         temperature: float = 0.7,
                         max_tokens: int = 500,
                         kb_context: Optional[str] = None) -> str:
        """
        Generate a response using a local model.

        Args:
            message: User message
            agent_role: Role of the agent (CEO, CTO, etc.)
            system_prompt: Optional system prompt to override the default
            model: Not used for local models
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in the response
            kb_context: Optional context from the knowledge base

        Returns:
            Generated response
        """
        try:
            # Create system prompt based on agent role if not provided
            if not system_prompt:
                system_prompt = self._get_system_prompt_for_role(agent_role)

            # Add knowledge base context if available
            if kb_context:
                system_prompt += f"\n\nUse the following information from our knowledge base to inform your response:\n{kb_context}"

            # Create payload for the API call
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Add model if specified
            if model:
                # Clean up model name if needed
                if isinstance(model, str):
                    # Remove any quotes or special characters
                    model = model.strip('"\'')
                    # If it contains a path, extract just the model name
                    if '\\' in model:
                        model = model.split('\\')[-1]
                    elif '/' in model:
                        model = model.split('/')[-1]

                    # Handle common model name formatting issues
                    # Convert spaces to hyphens
                    model = model.replace(' ', '-')
                    # Remove file extensions if present
                    if model.lower().endswith('.gguf'):
                        model = model[:-5]  # Remove .gguf
                    elif model.lower().endswith('.bin'):
                        model = model[:-4]  # Remove .bin

                    # Check if the model is in the list of available models
                    available_models = self.list_available_models()
                    if available_models and model not in available_models:
                        # Try to find a close match
                        for available_model in available_models:
                            if model.lower() in available_model.lower():
                                logger.info(f"Model '{model}' not found exactly, using closest match: '{available_model}'")
                                model = available_model
                                break

                logger.info(f"Using local model: {model}")
                payload["model"] = model

            # Call the local LLM server API
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json=payload
            )

            # Check for errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract and return the response text
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.HTTPError as e:
            error_msg = f"Error generating response with local model: {e}"
            logger.error(error_msg)
            if "404" in str(e):
                # Model not found error
                return f"I apologize, but I encountered an error while processing your request. The model '{model}' could not be found or is not properly loaded in LM Studio. Please check that the model is loaded and try again."
            elif "connection" in str(e).lower():
                # Connection error
                return f"I apologize, but I encountered an error while processing your request. Could not connect to the local LLM server at {self.api_url}. Please make sure LM Studio is running and try again."
            else:
                # Generic HTTP error
                return f"I apologize, but I encountered an error while processing your request. As {agent_role}, I'd like to help, but I'm currently experiencing technical difficulties. Error: {str(e)}"
        except Exception as e:
            error_msg = f"Error generating response with local model: {e}"
            logger.error(error_msg)
            # Return a fallback response
            return f"I apologize, but I encountered an error while processing your request. As {agent_role}, I'd like to help, but I'm currently experiencing technical difficulties. Please try again later or contact support."

    def list_available_models(self) -> List[str]:
        """
        List available local models.

        Returns:
            List of available model names
        """
        try:
            # Call the local LLM server API to get models
            response = requests.get(f"{self.api_url}/models")

            # Check for errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract and return model names
            return [model["id"] for model in data["data"]]

        except Exception as e:
            logger.error(f"Error listing local models: {e}")
            return []

    def _get_system_prompt_for_role(self, agent_role: str) -> str:
        """
        Get a role-specific system prompt.

        Args:
            agent_role: Role of the agent (CEO, CTO, etc.)

        Returns:
            System prompt for the specified role
        """
        role_prompts = {
            "CEO": """You are the CEO of AI Executive Team, a company that provides AI executive agents to businesses.
Your role is to provide strategic leadership, vision, and high-level business insights.
Focus on overall company strategy, growth opportunities, market positioning, and executive decision-making.
Your communication style should be confident, visionary, and focused on the big picture.
Provide insights that demonstrate strategic thinking and leadership.""",

            "CTO": """You are the CTO of AI Executive Team, a company that provides AI executive agents to businesses.
Your role is to provide technical leadership, technology strategy, and technical insights.
Focus on technology architecture, development methodology, technical innovation, and technical decision-making.
Your communication style should be analytical, technically precise, and solution-oriented.
Provide insights that demonstrate technical expertise and innovation thinking.""",

            "CFO": """You are the CFO of AI Executive Team, a company that provides AI executive agents to businesses.
Your role is to provide financial leadership, financial analysis, and business insights from a financial perspective.
Focus on financial performance, cost management, investment decisions, and financial planning.
Your communication style should be analytical, data-driven, and focused on financial implications.
Provide insights that demonstrate financial acumen and business understanding.""",

            "CMO": """You are the CMO of AI Executive Team, a company that provides AI executive agents to businesses.
Your role is to provide marketing leadership, brand strategy, and customer-focused insights.
Focus on marketing strategy, brand positioning, customer acquisition, and market trends.
Your communication style should be creative, customer-centric, and focused on growth.
Provide insights that demonstrate marketing expertise and customer understanding.""",

            "COO": """You are the COO of AI Executive Team, a company that provides AI executive agents to businesses.
Your role is to provide operational leadership, process optimization, and execution-focused insights.
Focus on operational efficiency, service delivery, team management, and process improvement.
Your communication style should be practical, detail-oriented, and focused on execution.
Provide insights that demonstrate operational expertise and execution capability."""
        }

        # Return the role-specific prompt or a generic one if role not found
        return role_prompts.get(agent_role.upper(),
                               f"You are an AI {agent_role} executive. Provide insights and answers from the perspective of a {agent_role}.")
