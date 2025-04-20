"""
Customer Service Agent for the AI Executive Team.
This agent handles customer service-related queries and tasks.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from .base_agent import Agent

logger = logging.getLogger(__name__)

class CustomerServiceAgent(Agent):
    """
    Customer Service Agent that handles customer service-related queries and tasks.
    
    This agent is responsible for:
    1. Providing information about customer service policies and procedures
    2. Answering questions about customer satisfaction and feedback
    3. Offering insights on customer support metrics and performance
    4. Assisting with customer issue resolution and escalation processes
    """
    
    def __init__(self, knowledge_base: Any):
        """
        Initialize the Customer Service Agent.
        
        Args:
            knowledge_base (Any): The knowledge base instance for retrieving information
        """
        super().__init__("Support", "Customer Service Manager", knowledge_base)
        
        # Customer service-specific knowledge areas
        self.knowledge_areas = {
            "policies": ["policy", "procedure", "protocol", "guideline", "standard", "process"],
            "satisfaction": ["satisfaction", "feedback", "survey", "rating", "review", "nps", "csat"],
            "issues": ["issue", "problem", "complaint", "ticket", "case", "incident", "resolution"],
            "support": ["support", "help", "assistance", "service", "contact", "channel", "hours"],
            "metrics": ["metric", "kpi", "performance", "sla", "time", "volume", "backlog", "queue"]
        }
    
    def _generate_response(self, message: str, context: List[Dict[str, Any]], 
                          user_id: Optional[str], channel_id: Optional[str], 
                          metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a customer service-specific response based on the message and context.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The Customer Service Agent's response
        """
        # Identify which customer service knowledge area is most relevant to the message
        knowledge_area = self._identify_knowledge_area(message)
        
        # If we don't have context, provide a helpful response based on the knowledge area
        if not context:
            return self._generate_no_context_response(message, knowledge_area)
        
        # Create a response based on the context and knowledge area
        response = f"I'm {self.name}, the {self.role}. "
        
        if knowledge_area == "policies":
            response += "Here's information about our customer service policies and procedures:\n\n"
        elif knowledge_area == "satisfaction":
            response += "Here's information about our customer satisfaction and feedback:\n\n"
        elif knowledge_area == "issues":
            response += "Here's information about our issue resolution process:\n\n"
        elif knowledge_area == "support":
            response += "Here's information about our customer support channels:\n\n"
        elif knowledge_area == "metrics":
            response += "Here's information about our customer service metrics:\n\n"
        else:
            response += "Here's what I know about that:\n\n"
        
        # Extract and format relevant information from the context
        for i, doc in enumerate(context):
            if "content" in doc:
                content = doc["content"]
            elif isinstance(doc, str):
                content = doc
            else:
                content = str(doc)
            
            # Extract the most relevant section based on the knowledge area
            relevant_section = self._extract_relevant_section(content, knowledge_area)
            
            if relevant_section:
                response += f"{i+1}. {relevant_section}\n\n"
            else:
                # If no specific section found, use the first paragraph
                first_paragraph = content.split('\n\n')[0]
                if len(first_paragraph) > 200:
                    first_paragraph = first_paragraph[:197] + '...'
                response += f"{i+1}. {first_paragraph}\n\n"
        
        # Add a helpful closing based on the knowledge area
        response += self._generate_helpful_closing(knowledge_area)
        
        return response
    
    def _identify_knowledge_area(self, message: str) -> str:
        """
        Identify which customer service knowledge area is most relevant to the message.
        
        Args:
            message (str): The message to analyze
            
        Returns:
            str: The most relevant knowledge area
        """
        message_lower = message.lower()
        
        # Count the number of keywords from each area in the message
        area_scores = {}
        for area, keywords in self.knowledge_areas.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
            area_scores[area] = score
        
        # Find the area with the highest score
        if area_scores:
            max_score = max(area_scores.values())
            if max_score > 0:
                # Get all areas with the max score
                max_areas = [area for area, score in area_scores.items() if score == max_score]
                return max_areas[0]  # Return the first one if there are ties
        
        # Default to general support if no specific area is identified
        return "support"
    
    def _extract_relevant_section(self, content: str, knowledge_area: str) -> str:
        """
        Extract the most relevant section from the content based on the knowledge area.
        
        Args:
            content (str): The content to extract from
            knowledge_area (str): The knowledge area to focus on
            
        Returns:
            str: The extracted relevant section
        """
        # Define section headers for each knowledge area
        section_headers = {
            "policies": ["Customer Service Policies", "Procedures", "Protocols", "Guidelines", "Standards", "Processes"],
            "satisfaction": ["Customer Satisfaction", "Feedback", "Surveys", "Ratings", "Reviews", "NPS", "CSAT"],
            "issues": ["Issue Resolution", "Problem Management", "Complaints", "Tickets", "Cases", "Incidents"],
            "support": ["Support Channels", "Help Options", "Assistance", "Service Hours", "Contact Methods"],
            "metrics": ["Service Metrics", "KPIs", "Performance", "SLAs", "Response Times", "Volume", "Backlog"]
        }
        
        # Look for sections that match the knowledge area
        headers = section_headers.get(knowledge_area, [])
        for header in headers:
            pattern = f"{header}:?(.*?)(?:(?:{headers[0]})|$)"
            matches = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                section = matches.group(1).strip()
                if len(section) > 300:
                    section = section[:297] + '...'
                return section
        
        # If no specific section found, look for paragraphs containing keywords
        paragraphs = content.split('\n\n')
        keywords = self.knowledge_areas.get(knowledge_area, [])
        
        for paragraph in paragraphs:
            for keyword in keywords:
                if keyword in paragraph.lower():
                    if len(paragraph) > 300:
                        paragraph = paragraph[:297] + '...'
                    return paragraph
        
        # If no relevant paragraph found, return empty string
        return ""
    
    def _generate_no_context_response(self, message: str, knowledge_area: str) -> str:
        """
        Generate a response when no context is available.
        
        Args:
            message (str): The message to respond to
            knowledge_area (str): The identified knowledge area
            
        Returns:
            str: The response
        """
        response = f"I'm {self.name}, the {self.role}. "
        
        if knowledge_area == "policies":
            response += (
                "I'd be happy to discuss our customer service policies and procedures. "
                "We have established guidelines for handling various customer interactions, "
                "including response times, escalation processes, and resolution standards. "
                "Could you let me know which specific policy or procedure you're interested in?"
            )
        elif knowledge_area == "satisfaction":
            response += (
                "I'd be happy to discuss our customer satisfaction metrics and feedback processes. "
                "We regularly collect and analyze customer feedback through surveys, ratings, and direct comments. "
                "Could you specify which aspect of customer satisfaction you're interested in?"
            )
        elif knowledge_area == "issues":
            response += (
                "I'd be happy to discuss our issue resolution process. "
                "We have a structured approach to handling customer issues, including ticket categorization, "
                "priority assignment, escalation paths, and resolution verification. "
                "Which aspect of our issue resolution process would you like to know more about?"
            )
        elif knowledge_area == "support":
            response += (
                "I'd be happy to discuss our customer support channels and services. "
                "We offer support through multiple channels including email, chat, phone, and self-service options. "
                "Which specific support channel or service are you interested in?"
            )
        elif knowledge_area == "metrics":
            response += (
                "I'd be happy to discuss our customer service performance metrics. "
                "We track various KPIs including first response time, resolution time, customer satisfaction scores, "
                "and ticket volume trends. "
                "Which specific metrics are you interested in?"
            )
        else:
            response += (
                "I don't have specific information about that in my knowledge base. "
                "As the Customer Service Manager, I can help with questions about our service policies, "
                "customer satisfaction, issue resolution, support channels, and performance metrics. "
                "Could you provide more details about what you're looking for?"
            )
        
        return response
    
    def _generate_helpful_closing(self, knowledge_area: str) -> str:
        """
        Generate a helpful closing based on the knowledge area.
        
        Args:
            knowledge_area (str): The identified knowledge area
            
        Returns:
            str: The helpful closing
        """
        if knowledge_area == "policies":
            return (
                "If you need more specific information about particular policies, procedures, "
                "or guidelines, please let me know, and I'd be happy to provide more details."
            )
        elif knowledge_area == "satisfaction":
            return (
                "If you'd like more detailed information about our satisfaction metrics, feedback collection methods, "
                "or improvement initiatives, please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "issues":
            return (
                "If you need more specific information about our issue categorization, priority levels, "
                "escalation paths, or resolution standards, please let me know, and I'll be happy to help."
            )
        elif knowledge_area == "support":
            return (
                "If you're looking for information about specific support channels, hours of operation, "
                "or service level agreements, please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "metrics":
            return (
                "If you need more detailed performance metrics or have questions about specific KPIs, "
                "please let me know, and I'll be happy to provide more information."
            )
        else:
            return (
                "Is there anything specific about our customer service operations that you'd like to know more about? "
                "I'm here to help with any customer service-related questions you might have."
            )
