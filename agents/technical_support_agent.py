"""
Technical Support Agent for the AI Executive Team.
This agent handles technical support-related queries and tasks.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from .base_agent import Agent

logger = logging.getLogger(__name__)

class TechnicalSupportAgent(Agent):
    """
    Technical Support Agent that handles technical support-related queries and tasks.
    
    This agent is responsible for:
    1. Providing information about technical systems and infrastructure
    2. Answering questions about software, hardware, and network issues
    3. Offering insights on technical troubleshooting and problem resolution
    4. Assisting with system maintenance and upgrade procedures
    """
    
    def __init__(self, knowledge_base: Any):
        """
        Initialize the Technical Support Agent.
        
        Args:
            knowledge_base (Any): The knowledge base instance for retrieving information
        """
        super().__init__("Tech", "Technical Support Manager", knowledge_base)
        
        # Technical support-specific knowledge areas
        self.knowledge_areas = {
            "systems": ["system", "infrastructure", "architecture", "platform", "environment", "server"],
            "software": ["software", "application", "program", "code", "bug", "feature", "update", "version"],
            "hardware": ["hardware", "device", "equipment", "computer", "server", "network", "component"],
            "troubleshooting": ["troubleshoot", "issue", "problem", "error", "bug", "fix", "resolve", "solution"],
            "maintenance": ["maintenance", "upgrade", "update", "patch", "backup", "restore", "monitor", "security"]
        }
    
    def _generate_response(self, message: str, context: List[Dict[str, Any]], 
                          user_id: Optional[str], channel_id: Optional[str], 
                          metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a technical support-specific response based on the message and context.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The Technical Support Agent's response
        """
        # Identify which technical support knowledge area is most relevant to the message
        knowledge_area = self._identify_knowledge_area(message)
        
        # If we don't have context, provide a helpful response based on the knowledge area
        if not context:
            return self._generate_no_context_response(message, knowledge_area)
        
        # Create a response based on the context and knowledge area
        response = f"I'm {self.name}, the {self.role}. "
        
        if knowledge_area == "systems":
            response += "Here's information about our technical systems and infrastructure:\n\n"
        elif knowledge_area == "software":
            response += "Here's information about our software applications:\n\n"
        elif knowledge_area == "hardware":
            response += "Here's information about our hardware and equipment:\n\n"
        elif knowledge_area == "troubleshooting":
            response += "Here's information about troubleshooting and issue resolution:\n\n"
        elif knowledge_area == "maintenance":
            response += "Here's information about system maintenance and updates:\n\n"
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
        Identify which technical support knowledge area is most relevant to the message.
        
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
        
        # Default to general systems if no specific area is identified
        return "systems"
    
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
            "systems": ["Systems", "Infrastructure", "Architecture", "Platform", "Environment", "Servers"],
            "software": ["Software", "Applications", "Programs", "Code", "Features", "Updates", "Versions"],
            "hardware": ["Hardware", "Devices", "Equipment", "Computers", "Servers", "Network", "Components"],
            "troubleshooting": ["Troubleshooting", "Issues", "Problems", "Errors", "Bugs", "Fixes", "Solutions"],
            "maintenance": ["Maintenance", "Upgrades", "Updates", "Patches", "Backups", "Monitoring", "Security"]
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
        
        if knowledge_area == "systems":
            response += (
                "I'd be happy to discuss our technical systems and infrastructure. "
                "We maintain various systems including cloud services, on-premises servers, "
                "development environments, and network infrastructure. "
                "Could you let me know which specific system or component you're interested in?"
            )
        elif knowledge_area == "software":
            response += (
                "I'd be happy to discuss our software applications and services. "
                "We develop and maintain various applications with different technologies and frameworks. "
                "Could you specify which software application or feature you're interested in?"
            )
        elif knowledge_area == "hardware":
            response += (
                "I'd be happy to discuss our hardware and equipment. "
                "We utilize various devices including servers, workstations, network equipment, and peripherals. "
                "Which specific hardware component are you interested in?"
            )
        elif knowledge_area == "troubleshooting":
            response += (
                "I'd be happy to discuss our troubleshooting processes and common issues. "
                "We have established procedures for diagnosing and resolving various technical problems. "
                "Could you provide more details about the specific issue you're inquiring about?"
            )
        elif knowledge_area == "maintenance":
            response += (
                "I'd be happy to discuss our system maintenance and update procedures. "
                "We follow regular schedules for updates, patches, backups, and security reviews. "
                "Which aspect of our maintenance process are you interested in?"
            )
        else:
            response += (
                "I don't have specific information about that in my knowledge base. "
                "As the Technical Support Manager, I can help with questions about our systems, "
                "software, hardware, troubleshooting procedures, and maintenance processes. "
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
        if knowledge_area == "systems":
            return (
                "If you need more specific information about particular systems, architecture details, "
                "or infrastructure components, please let me know, and I'd be happy to provide more details."
            )
        elif knowledge_area == "software":
            return (
                "If you'd like more detailed information about specific software applications, features, "
                "or development processes, please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "hardware":
            return (
                "If you need more specific information about our hardware specifications, configurations, "
                "or equipment inventory, please let me know, and I'll be happy to help."
            )
        elif knowledge_area == "troubleshooting":
            return (
                "If you're looking for information about specific technical issues, error messages, "
                "or resolution steps, please let me know, and I can provide more targeted assistance."
            )
        elif knowledge_area == "maintenance":
            return (
                "If you need more detailed information about our maintenance schedules, update procedures, "
                "or security protocols, please let me know, and I'll be happy to provide more information."
            )
        else:
            return (
                "Is there anything specific about our technical operations that you'd like to know more about? "
                "I'm here to help with any technical support-related questions you might have."
            )
