"""
Sales Agent for the AI Executive Team.
This agent handles sales-related queries and tasks.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from .base_agent import Agent

logger = logging.getLogger(__name__)

class SalesAgent(Agent):
    """
    Sales Agent that handles sales-related queries and tasks.
    
    This agent is responsible for:
    1. Providing information about sales processes and strategies
    2. Answering questions about products, pricing, and deals
    3. Offering insights on sales performance and metrics
    4. Assisting with customer and prospect information
    """
    
    def __init__(self, knowledge_base: Any):
        """
        Initialize the Sales Agent.
        
        Args:
            knowledge_base (Any): The knowledge base instance for retrieving information
        """
        super().__init__("Sales", "Sales Director", knowledge_base)
        
        # Sales-specific knowledge areas
        self.knowledge_areas = {
            "sales_process": ["sales process", "sales methodology", "sales cycle", "pipeline", "funnel"],
            "products": ["product", "offering", "solution", "service", "feature"],
            "pricing": ["price", "pricing", "cost", "discount", "promotion", "deal"],
            "customers": ["customer", "client", "account", "prospect", "lead", "opportunity"],
            "performance": ["performance", "metric", "quota", "target", "forecast", "revenue", "commission"]
        }
    
    def _generate_response(self, message: str, context: List[Dict[str, Any]], 
                          user_id: Optional[str], channel_id: Optional[str], 
                          metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a sales-specific response based on the message and context.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The Sales Agent's response
        """
        # Identify which sales knowledge area is most relevant to the message
        knowledge_area = self._identify_knowledge_area(message)
        
        # If we don't have context, provide a helpful response based on the knowledge area
        if not context:
            return self._generate_no_context_response(message, knowledge_area)
        
        # Create a response based on the context and knowledge area
        response = f"I'm {self.name}, the {self.role}. "
        
        if knowledge_area == "sales_process":
            response += "Here's information about our sales process:\n\n"
        elif knowledge_area == "products":
            response += "Here's information about our products and offerings:\n\n"
        elif knowledge_area == "pricing":
            response += "Here's information about our pricing and deals:\n\n"
        elif knowledge_area == "customers":
            response += "Here's information about our customers and prospects:\n\n"
        elif knowledge_area == "performance":
            response += "Here's information about our sales performance:\n\n"
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
        Identify which sales knowledge area is most relevant to the message.
        
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
        
        # Default to general sales process if no specific area is identified
        return "sales_process"
    
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
            "sales_process": ["Sales Process", "Sales Methodology", "Sales Cycle", "Pipeline", "Funnel"],
            "products": ["Products", "Offerings", "Solutions", "Services", "Features"],
            "pricing": ["Pricing", "Costs", "Discounts", "Promotions", "Deals"],
            "customers": ["Customers", "Clients", "Accounts", "Prospects", "Leads", "Opportunities"],
            "performance": ["Performance", "Metrics", "Quotas", "Targets", "Forecasts", "Revenue", "Commissions"]
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
        
        if knowledge_area == "sales_process":
            response += (
                "I'd be happy to discuss our sales process with you. "
                "Our typical sales cycle includes lead generation, qualification, needs assessment, "
                "proposal, negotiation, and closing. "
                "Could you let me know which part of the process you're interested in?"
            )
        elif knowledge_area == "products":
            response += (
                "I'd be happy to tell you about our products and offerings. "
                "We have a range of solutions designed to meet various customer needs. "
                "Could you specify which product line or feature you're interested in?"
            )
        elif knowledge_area == "pricing":
            response += (
                "I'd be happy to discuss our pricing structure. "
                "We offer competitive pricing with various options including subscription models, "
                "one-time purchases, and enterprise agreements. "
                "Could you let me know which specific pricing details you're looking for?"
            )
        elif knowledge_area == "customers":
            response += (
                "I'd be happy to discuss our customer base. "
                "We serve a diverse range of clients across various industries. "
                "Could you specify which customer segment or account you're interested in?"
            )
        elif knowledge_area == "performance":
            response += (
                "I'd be happy to discuss our sales performance metrics. "
                "We track various KPIs including revenue growth, conversion rates, average deal size, "
                "sales cycle length, and customer acquisition cost. "
                "Which specific metrics are you interested in?"
            )
        else:
            response += (
                "I don't have specific information about that in my knowledge base. "
                "As the Sales Director, I can help with questions about our sales process, "
                "products, pricing, customers, and performance metrics. "
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
        if knowledge_area == "sales_process":
            return (
                "If you need more specific information about our sales process or methodology, "
                "please let me know which stage you're interested in, and I'd be happy to provide more details."
            )
        elif knowledge_area == "products":
            return (
                "If you'd like more detailed information about specific products, features, or use cases, "
                "please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "pricing":
            return (
                "If you need more specific pricing information or have questions about discounts, "
                "promotions, or custom pricing, please let me know, and I'll be happy to help."
            )
        elif knowledge_area == "customers":
            return (
                "If you're looking for information about specific customers, market segments, or success stories, "
                "please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "performance":
            return (
                "If you need more detailed performance metrics or have questions about specific KPIs, "
                "please let me know, and I'll be happy to provide more information."
            )
        else:
            return (
                "Is there anything specific about our sales operations that you'd like to know more about? "
                "I'm here to help with any sales-related questions you might have."
            )
