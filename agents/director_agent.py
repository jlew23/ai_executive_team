"""
Director Agent for the AI Executive Team.
This agent orchestrates the team and delegates tasks to specialized agents.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import Agent, DELEGATION_AVAILABLE

# Import the agent communication system if available
try:
    from agent_communication import TaskMessage
except ImportError:
    pass

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

    def __init__(self, knowledge_base: Any, agents: Optional[Dict[str, Agent]] = None, agent_id: Optional[str] = None):
        """
        Initialize the Director Agent.

        Args:
            knowledge_base (Any): The knowledge base instance for retrieving information
            agents (Optional[Dict[str, Agent]]): Dictionary of specialized agents
            agent_id (Optional[str]): Unique identifier for the agent, generated if not provided
        """
        super().__init__("CEO", "Chief Executive Officer", knowledge_base, agent_id)
        self.agents = agents or {}
        self.agent_keywords = {
            "sales": ["sales", "revenue", "customer", "deal", "pipeline", "prospect", "lead", "opportunity", "commission", "quota", "target", "pricing", "discount", "contract", "client", "purchase", "buyer", "sell", "selling", "sold"],
            "marketing": ["marketing", "campaign", "brand", "social media", "advertisement", "promotion", "market research", "seo", "content", "audience", "advertising", "branding", "pr", "public relations", "market", "demographics", "segment", "positioning", "messaging", "outreach", "blog", "website", "digital", "email campaign", "newsletter"],
            "finance": ["finance", "budget", "expense", "revenue", "cost", "profit", "loss", "investment", "funding", "financial", "accounting", "tax", "money", "cash flow", "balance sheet", "income statement", "forecast", "projection", "roi", "return on investment", "capital", "expenditure", "spend", "spending", "fiscal", "quarter", "annual", "audit"],
            "customer": ["customer service", "support", "complaint", "refund", "satisfaction", "feedback", "help", "assistance", "issue resolution", "customer experience", "cx", "service desk", "helpdesk", "ticket", "query", "problem", "resolve", "resolution", "customer success", "onboarding", "training", "user", "client support"],
            "technical": ["technical", "technology", "software", "hardware", "bug", "error", "system", "network", "infrastructure", "development", "engineering", "code", "coding", "program", "programming", "developer", "develop", "app", "application", "website", "web", "mobile", "cloud", "server", "database", "data", "api", "integration", "security", "cybersecurity", "it", "information technology", "tech stack", "architecture", "devops", "agile", "sprint", "release", "version", "update", "upgrade", "install", "implementation"]
        }

        # Map agent roles to agent names
        self.role_to_agent = {
            "CTO": "technical",
            "CFO": "finance",
            "CMO": "marketing",
            "COO": "customer"
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

    def route_message(self, message: str, user_id: Optional[str] = None,
                     channel_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Route a message to the appropriate agent based on message content.

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

        # Check if this is a delegation request
        if self._is_delegation_request(message):
            logger.info("Handling delegation request")
            return self.process_delegation_request(message, user_id)

        # Determine which agent should handle this message
        agent_name, confidence = self._determine_best_agent(message)

        # If we have reasonable confidence in our agent selection, delegate to that agent
        # Lowering the threshold to make delegation more likely
        if confidence >= 0.4 and agent_name in self.agents:
            logger.info(f"Routing message to {agent_name} agent with confidence {confidence:.2f}")

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
            self._add_to_history("agent", response, None, {"handled_by": "CEO", "inquiry_type": "company"})

            return response

        # If we're not confident or it's a general inquiry, handle it at the CEO level
        logger.info(f"Handling message at CEO level (best agent was {agent_name} with confidence {confidence:.2f})")
        response = super().process_message(message, user_id, channel_id, metadata)

        return response

    def process_message(self, message: str, user_id: Optional[str] = None,
                       channel_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process incoming message and generate a response.

        This overrides the base implementation to handle delegation requests.

        Args:
            message (str): The message to process
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message

        Returns:
            str: The agent's response
        """
        # Check if this is a delegation request
        if self._is_delegation_request(message):
            logger.info("Handling delegation request")
            return self.process_delegation_request(message, user_id)

        # Otherwise, use the standard processing
        return super().process_message(message, user_id, channel_id, metadata)

    def _is_delegation_request(self, message: str) -> bool:
        """
        Determine if a message is a request to delegate a task.

        Args:
            message (str): The message to analyze

        Returns:
            bool: True if the message is a delegation request, False otherwise
        """
        delegation_keywords = [
            "delegate", "assign", "task", "tell the", "ask the", "have the",
            "get the", "tell", "ask", "have", "get", "work on", "handle"
        ]

        role_keywords = [
            "cto", "cfo", "cmo", "coo", "chief", "officer", "technology", "financial",
            "marketing", "operations", "technical", "finance", "tech"
        ]

        message_lower = message.lower()

        # Check for delegation keywords
        has_delegation_keyword = any(keyword in message_lower for keyword in delegation_keywords)

        # Check for role keywords
        has_role_keyword = any(keyword in message_lower for keyword in role_keywords)

        # If the message contains both delegation and role keywords, it's likely a delegation request
        return has_delegation_keyword and has_role_keyword

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
                    # Increased weight for keyword matches to make delegation more likely
                    score += len(keyword) / 3
                    
                    # Bonus points for keywords at the beginning of the message
                    if message_lower.startswith(keyword.lower()) or message_lower.startswith('the ' + keyword.lower()):
                        score += 2
                        
                    # Bonus points for multiple occurrences of the same keyword
                    occurrences = message_lower.count(keyword.lower())
                    if occurrences > 1:
                        score += occurrences - 1

            if score > 0:
                scores[agent_name] = score

        # Find the agent with the highest score
        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])
            # Normalize confidence to 0-1 range but with a higher baseline
            # This makes delegation more likely by boosting confidence scores
            confidence = min(0.3 + (best_agent[1] / 5), 1.0)
            logger.info(f"Determined best agent: {best_agent[0]} with score {best_agent[1]} and confidence {confidence}")
            return best_agent[0], confidence

        # Default to director with very low confidence
        # This makes the CEO less likely to handle messages itself
        return "director", 0.05

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
        Generate a response as the CEO.

        This overrides the base implementation to provide CEO-specific responses.

        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message

        Returns:
            str: The CEO's response
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

    def process_delegation_request(self, message: str, user_id: Optional[str] = None) -> str:
        """
        Process a request to delegate a task to another agent.

        This method parses the message to identify the task and the target agent,
        then delegates the task using the delegation system.

        Args:
            message (str): The message containing the delegation request
            user_id (Optional[str]): The ID of the user who sent the message

        Returns:
            str: The response indicating whether the delegation was successful
        """
        if not DELEGATION_AVAILABLE:
            return (
                f"I'm {self.name}, the {self.role} of our company. "
                "I understand you want me to delegate a task, but the delegation system is not available. "
                "Please try again later or contact the system administrator."
            )

        # Parse the message to identify the task and target agent
        target_role = self._identify_target_role(message)
        task_description = self._extract_task_description(message, target_role)

        if not target_role:
            return (
                f"I'm {self.name}, the {self.role} of our company. "
                "I couldn't determine which team member you want me to delegate this task to. "
                "Please specify a role such as CTO, CFO, CMO, or COO."
            )

        if not task_description:
            return (
                f"I'm {self.name}, the {self.role} of our company. "
                "I couldn't determine what task you want me to delegate. "
                "Please provide a clear description of the task."
            )

        # Create a title from the task description
        title = self._create_task_title(task_description)

        # Delegate the task using the delegation system
        if self.delegation_system:
            task, task_message = self.delegation_system.delegate_task(
                title=title,
                description=task_description,
                created_by=self.agent_id,
                assigned_role=target_role,
                priority=3  # Medium priority by default
            )
        else:
            task = None

        if task:
            return (
                f"I've delegated the task '{title}' to our {target_role}. "
                f"They will begin working on it right away. The task ID is {task.id} if you need to reference it later."
            )
        else:
            return (
                f"I'm sorry, but I couldn't delegate the task to our {target_role}. "
                "There may be an issue with the delegation system or the specified role may not be available."
            )

    def _identify_target_role(self, message: str) -> Optional[str]:
        """
        Identify the target role from the message.

        Args:
            message (str): The message to analyze

        Returns:
            Optional[str]: The identified role, or None if no role was found
        """
        message_lower = message.lower()

        # Check for explicit mentions of roles
        role_keywords = {
            "CTO": ["cto", "chief technology officer", "tech officer", "technology officer", "technical"],
            "CFO": ["cfo", "chief financial officer", "finance officer", "financial"],
            "CMO": ["cmo", "chief marketing officer", "marketing officer", "marketing"],
            "COO": ["coo", "chief operating officer", "operations officer", "operations"]
        }

        for role, keywords in role_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return role

        # If no explicit role is mentioned, try to infer from the task description
        for agent_name, keywords in self.agent_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Map agent name to role
                    for role, name in self.role_to_agent.items():
                        if name == agent_name:
                            return role

        return None

    def _extract_task_description(self, message: str, target_role: Optional[str] = None) -> str:
        """
        Extract the task description from the message.

        Args:
            message (str): The message to analyze
            target_role (Optional[str]): The identified target role

        Returns:
            str: The extracted task description
        """
        # Remove role-related phrases if a target role was identified
        if target_role:
            role_phrases = [
                f"tell the {target_role}", f"ask the {target_role}", f"have the {target_role}",
                f"get the {target_role}", f"delegate to the {target_role}", f"assign the {target_role}",
                f"tell {target_role}", f"ask {target_role}", f"have {target_role}",
                f"get {target_role}", f"delegate to {target_role}", f"assign {target_role}"
            ]

            for phrase in role_phrases:
                message = message.replace(phrase, "").strip()

        # Remove common delegation phrases
        delegation_phrases = [
            "please delegate", "can you delegate", "delegate the task", "assign the task",
            "please assign", "can you assign", "i need you to delegate", "i want you to delegate",
            "i need you to assign", "i want you to assign"
        ]

        for phrase in delegation_phrases:
            message = message.replace(phrase, "").strip()

        # Clean up the message
        message = message.strip()
        if message.startswith("to"):
            message = message[2:].strip()
        if message.startswith("of"):
            message = message[2:].strip()

        return message

    def _create_task_title(self, description: str) -> str:
        """
        Create a concise title from a task description.

        Args:
            description (str): The task description

        Returns:
            str: A concise title for the task
        """
        # Use the first sentence or up to 50 characters
        if "." in description[:100]:
            title = description.split(".")[0]
        else:
            title = description[:min(50, len(description))]
            if len(description) > 50:
                title += "..."

        return title

    def _handle_task_message(self, message: TaskMessage) -> None:
        """
        Handle a task message.

        This overrides the base implementation to provide CEO-specific handling.

        Args:
            message: The task message to handle
        """
        task = self.delegation_system.get_task_by_id(message.task_id)
        if not task:
            return

        # CEOs don't typically get assigned tasks, but they can receive them for approval
        response = f"I've received the task '{task.title}'. As CEO, I'll review this and provide guidance."

        # Add a note about delegation if appropriate
        if "delegate" in task.description.lower() or "assign" in task.description.lower():
            response += " I'll delegate this to the appropriate team member."

        self.respond_to_task(task.id, response)

        # Update the task status to in progress
        self.update_task_status(task.id, "in_progress", 0.1, "Task received and under review by CEO")
