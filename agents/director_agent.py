"""
Director Agent for the AI Executive Team.
This agent orchestrates the team and delegates tasks to specialized agents.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import Agent

logger = logging.getLogger(__name__)

class DirectorAgent(Agent):
    """
    Director Agent that orchestrates the team and delegates tasks to specialized agents.
    
    This agent is responsible for:
    1. Analyzing incoming messages to determine intent
    2. Routing messages to the appropriate specialized agent
    3. Handling general company inquiries
    4. Coordinating complex tasks that require multiple agents
    """
    
    def __init__(self, knowledge_base: Any, agents: Optional[Dict[str, Agent]] = None):
        """
        Initialize the Director Agent.
        
        Args:
            knowledge_base (Any): The knowledge base instance for retrieving information
            agents (Optional[Dict[str, Agent]]): Dictionary of specialized agents
        """
        super().__init__("Director", "Executive Director", knowledge_base)
        self.agents = agents or {}
        self.agent_keywords = {
            "sales": ["sales", "revenue", "customer", "deal", "pipeline", "prospect", "lead", "opportunity", "commission", "quota", "target"],
            "marketing": ["marketing", "campaign", "brand", "social media", "advertisement", "promotion", "market research", "seo", "content", "audience"],
            "finance": ["finance", "budget", "expense", "revenue", "cost", "profit", "loss", "investment", "funding", "financial", "accounting", "tax"],
            "customer": ["customer service", "support", "complaint", "refund", "satisfaction", "feedback", "help", "assistance", "issue resolution"],
            "technical": ["technical", "technology", "software", "hardware", "bug", "error", "system", "network", "infrastructure", "development", "engineering"]
        }
        
    def add_agent(self, agent_name: str, agent: Agent) -> None:
        """
        Add an agent to the team.
        
        Args:
            agent_name (str): The name/key for the agent
            agent (Agent): The agent instance
        """
        self.agents[agent_name] = agent
        logger.info(f"Added {agent.name} ({agent.role}) to the team as '{agent_name}'")
        
    def delegate_task(self, message: str, user_id: Optional[str] = None, 
                     channel_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Delegate a task to the appropriate agent based on message content.
        
        This method uses a combination of keyword matching and intent analysis
        to determine which specialized agent should handle the message.
        
        Args:
            message (str): The message to process
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The response from the appropriate agent
        """
        # Record the incoming message in conversation history
        self._add_to_history("user", message, user_id, metadata)
        
        # Determine which agent should handle this message
        agent_name, confidence = self._determine_best_agent(message)
        
        # If we have high confidence in our agent selection, delegate to that agent
        if confidence >= 0.7 and agent_name in self.agents:
            logger.info(f"Delegating message to {agent_name} agent with confidence {confidence:.2f}")
            
            # Get the agent's response
            agent_response = self.agents[agent_name].process_message(message, user_id, channel_id, metadata)
            
            # Record the delegation and response in conversation history
            self._add_to_history(
                "agent", 
                agent_response, 
                None, 
                {"delegated_to": agent_name, "confidence": confidence}
            )
            
            return agent_response
        
        # For company-related general inquiries
        if self._is_company_inquiry(message):
            logger.info("Handling company-related inquiry")
            
            # Get context specifically about company information
            company_context = self.get_context("company information mission vision values")
            
            # Generate a response about the company
            response = self._generate_company_response(message, company_context, user_id, channel_id, metadata)
            
            # Record the response in conversation history
            self._add_to_history("agent", response, None, {"handled_by": "director", "inquiry_type": "company"})
            
            return response
        
        # If we're not confident or it's a general inquiry, handle it at the director level
        logger.info(f"Handling message at Director level (best agent was {agent_name} with confidence {confidence:.2f})")
        response = self.process_message(message, user_id, channel_id, metadata)
        
        return response
    
    def _determine_best_agent(self, message: str) -> Tuple[str, float]:
        """
        Determine which agent is best suited to handle a message.
        
        Args:
            message (str): The message to analyze
            
        Returns:
            Tuple[str, float]: The name of the best agent and the confidence score
        """
        scores = {}
        message_lower = message.lower()
        
        # Check for explicit mentions of department names
        for agent_name in self.agents:
            if agent_name.lower() in message_lower:
                return agent_name, 1.0
        
        # Check for keywords associated with each department
        for agent_name, keywords in self.agent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    # More specific keywords get higher scores
                    score += len(keyword) / 5
            
            if score > 0:
                scores[agent_name] = score
        
        # Find the agent with the highest score
        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])
            # Normalize confidence to 0-1 range
            confidence = min(best_agent[1] / 5, 1.0)
            return best_agent[0], confidence
        
        # Default to director with low confidence
        return "director", 0.1
    
    def _is_company_inquiry(self, message: str) -> bool:
        """
        Determine if a message is a general inquiry about the company.
        
        Args:
            message (str): The message to analyze
            
        Returns:
            bool: True if the message is a company inquiry, False otherwise
        """
        company_keywords = [
            "company", "organization", "business", "mission", "vision", 
            "values", "about", "history", "founded", "headquarters", "hq",
            "office", "location", "team", "executive", "leadership", "ceo",
            "culture", "philosophy", "approach", "strategy"
        ]
        
        message_lower = message.lower()
        
        # Check for company-related keywords
        for keyword in company_keywords:
            if keyword in message_lower:
                return True
        
        # Check for common company questions
        company_questions = [
            r"what (is|does) .* (do|offer)",
            r"who (is|are) .*",
            r"where (is|are) .* (located|based)",
            r"when (was|were) .* (founded|established|started)",
            r"why (does|do) .* exist",
            r"how (does|do) .* (work|operate)"
        ]
        
        for pattern in company_questions:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _generate_company_response(self, message: str, context: List[Dict[str, Any]], 
                                 user_id: Optional[str], channel_id: Optional[str], 
                                 metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a response for company-related inquiries.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The response about the company
        """
        if not context:
            return (
                f"I'm {self.name}, the {self.role} of our company. "
                "I'd be happy to tell you about our organization, but I don't have specific "
                "information in my knowledge base at the moment. Is there something specific "
                "about our company you'd like to know?"
            )
        
        # Extract company information from context
        company_info = {
            "mission": "",
            "vision": "",
            "values": "",
            "products": "",
            "history": "",
            "team": ""
        }
        
        for doc in context:
            content = doc.get("content", "")
            if not content:
                continue
                
            # Extract sections based on keywords
            for key in company_info:
                if key.capitalize() in content:
                    # Extract the section
                    pattern = f"{key.capitalize()}:?(.*?)(?:(?:{list(company_info.keys())[0].capitalize()})|$)"
                    matches = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        company_info[key] = matches.group(1).strip()
        
        # Determine which aspects of the company to include in the response
        aspects_to_include = []
        message_lower = message.lower()
        
        if "mission" in message_lower or "purpose" in message_lower:
            aspects_to_include.append("mission")
        
        if "vision" in message_lower or "future" in message_lower:
            aspects_to_include.append("vision")
        
        if "values" in message_lower or "culture" in message_lower or "believe" in message_lower:
            aspects_to_include.append("values")
        
        if "product" in message_lower or "service" in message_lower or "offer" in message_lower or "do" in message_lower:
            aspects_to_include.append("products")
        
        if "history" in message_lower or "founded" in message_lower or "started" in message_lower:
            aspects_to_include.append("history")
        
        if "team" in message_lower or "people" in message_lower or "employee" in message_lower:
            aspects_to_include.append("team")
        
        # If no specific aspects were mentioned, include all non-empty aspects
        if not aspects_to_include:
            aspects_to_include = [key for key, value in company_info.items() if value]
        
        # Generate the response
        response = f"I'm {self.name}, the {self.role} of our company. "
        
        if not aspects_to_include:
            response += (
                "I'd be happy to tell you about our organization, but I don't have specific "
                "information in my knowledge base at the moment. Is there something specific "
                "about our company you'd like to know?"
            )
        else:
            response += "Here's some information about our company:\n\n"
            
            for aspect in aspects_to_include:
                if company_info[aspect]:
                    response += f"**{aspect.capitalize()}**: {company_info[aspect]}\n\n"
        
        return response
    
    def _generate_response(self, message: str, context: List[Dict[str, Any]], 
                          user_id: Optional[str], channel_id: Optional[str], 
                          metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a response as the Director.
        
        This overrides the base implementation to provide Director-specific responses.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The Director's response
        """
        if not context:
            return (
                f"I'm {self.name}, the {self.role} of our company. "
                "I don't have specific information about that in my knowledge base. "
                "Would you like me to direct your question to one of our specialized departments? "
                "We have experts in Sales, Marketing, Finance, Customer Service, and Technical Support."
            )
        
        # Create a response based on the context
        response = f"I'm {self.name}, the {self.role} of our company. Here's what I know about that:\n\n"
        
        # Extract relevant information from the context
        for i, doc in enumerate(context):
            if "content" in doc:
                content = doc["content"]
            elif isinstance(doc, str):
                content = doc
            else:
                content = str(doc)
                
            # Add a summary of the document content (first 200 characters)
            summary = content.split('\n\n')[0]  # Get the first paragraph
            if len(summary) > 200:
                summary = summary[:197] + '...'
            response += f"{i+1}. {summary}\n\n"
        
        # Add a suggestion to consult specialized departments if appropriate
        response += (
            "If you need more specific information, I can direct your question to one of our "
            "specialized departments. We have experts in Sales, Marketing, Finance, Customer Service, "
            "and Technical Support."
        )
        
        return response
