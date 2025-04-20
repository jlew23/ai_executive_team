"""
OpenAI integration for AI Executive Team.
"""

import os
import logging
import openai
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class OpenAIIntegration:
    """
    Integration with OpenAI API for generating responses.
    """

    def __init__(self, api_key: str):
        """
        Initialize the OpenAI integration.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        openai.api_key = api_key
        logger.info("OpenAI integration initialized")

    def set_api_key(self, api_key: str):
        """
        Set the OpenAI API key.

        Args:
            api_key: OpenAI API key
        """
        if api_key and api_key.strip():
            self.api_key = api_key
            openai.api_key = api_key
            logger.info("OpenAI API key updated")

    def generate_response(self,
                         message: str,
                         agent_role: str,
                         system_prompt: Optional[str] = None,
                         model: str = "gpt-4",
                         temperature: float = 0.7,
                         max_tokens: int = 500,
                         kb_context: Optional[str] = None) -> str:
        """
        Generate a response using OpenAI.

        Args:
            message: User message
            agent_role: Role of the agent (CEO, CTO, etc.)
            system_prompt: Optional system prompt to override the default
            model: OpenAI model to use
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

            # Create messages for the API call
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]

            # Call the OpenAI API using the new client format (openai>=1.0.0)
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Extract and return the response text
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {e}")
            # Return a fallback response
            return f"I apologize, but I encountered an error while processing your request. As {agent_role}, I'd like to help, but I'm currently experiencing technical difficulties. Please try again later or contact support."

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
