"""
Finance Agent for the AI Executive Team.
This agent handles finance-related queries and tasks.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from .base_agent import Agent

logger = logging.getLogger(__name__)

class FinanceAgent(Agent):
    """
    Finance Agent that handles finance-related queries and tasks.
    
    This agent is responsible for:
    1. Providing information about financial performance and metrics
    2. Answering questions about budgets, expenses, and investments
    3. Offering insights on financial planning and forecasting
    4. Assisting with financial reporting and compliance
    """
    
    def __init__(self, knowledge_base: Any):
        """
        Initialize the Finance Agent.
        
        Args:
            knowledge_base (Any): The knowledge base instance for retrieving information
        """
        super().__init__("Finance", "Finance Director", knowledge_base)
        
        # Finance-specific knowledge areas
        self.knowledge_areas = {
            "performance": ["performance", "revenue", "profit", "loss", "margin", "growth", "financial results"],
            "budgeting": ["budget", "expense", "cost", "spending", "allocation", "forecast"],
            "investment": ["investment", "funding", "capital", "roi", "return", "venture", "investor"],
            "reporting": ["report", "statement", "balance sheet", "income statement", "cash flow", "quarterly", "annual"],
            "compliance": ["compliance", "regulation", "tax", "audit", "legal", "policy", "procedure"]
        }
    
    def _generate_response(self, message: str, context: List[Dict[str, Any]], 
                          user_id: Optional[str], channel_id: Optional[str], 
                          metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a finance-specific response based on the message and context.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The Finance Agent's response
        """
        # Identify which finance knowledge area is most relevant to the message
        knowledge_area = self._identify_knowledge_area(message)
        
        # If we don't have context, provide a helpful response based on the knowledge area
        if not context:
            return self._generate_no_context_response(message, knowledge_area)
        
        # Create a response based on the context and knowledge area
        response = f"I'm {self.name}, the {self.role}. "
        
        if knowledge_area == "performance":
            response += "Here's information about our financial performance:\n\n"
        elif knowledge_area == "budgeting":
            response += "Here's information about our budgeting and expenses:\n\n"
        elif knowledge_area == "investment":
            response += "Here's information about our investments and funding:\n\n"
        elif knowledge_area == "reporting":
            response += "Here's information about our financial reporting:\n\n"
        elif knowledge_area == "compliance":
            response += "Here's information about our financial compliance:\n\n"
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
        Identify which finance knowledge area is most relevant to the message.
        
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
        
        # Default to general financial performance if no specific area is identified
        return "performance"
    
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
            "performance": ["Financial Performance", "Revenue", "Profit", "Loss", "Margin", "Growth", "Results"],
            "budgeting": ["Budget", "Expenses", "Costs", "Spending", "Allocation", "Forecast"],
            "investment": ["Investment", "Funding", "Capital", "ROI", "Return", "Venture", "Investor"],
            "reporting": ["Financial Reports", "Statements", "Balance Sheet", "Income Statement", "Cash Flow"],
            "compliance": ["Compliance", "Regulations", "Tax", "Audit", "Legal", "Policies", "Procedures"]
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
        
        if knowledge_area == "performance":
            response += (
                "I'd be happy to discuss our financial performance with you. "
                "We track various metrics including revenue growth, profit margins, "
                "operating expenses, and return on investment. "
                "Could you let me know which specific aspect of our financial performance you're interested in?"
            )
        elif knowledge_area == "budgeting":
            response += (
                "I'd be happy to discuss our budgeting process and expenses. "
                "We maintain detailed budgets for each department and track expenses against forecasts. "
                "Could you specify which budget area or expense category you're interested in?"
            )
        elif knowledge_area == "investment":
            response += (
                "I'd be happy to discuss our investment strategy and funding. "
                "We allocate capital based on strategic priorities and expected returns. "
                "Could you let me know which specific investment area you're interested in?"
            )
        elif knowledge_area == "reporting":
            response += (
                "I'd be happy to discuss our financial reporting processes. "
                "We prepare various reports including quarterly and annual statements, "
                "balance sheets, income statements, and cash flow analyses. "
                "Which specific reports are you interested in?"
            )
        elif knowledge_area == "compliance":
            response += (
                "I'd be happy to discuss our financial compliance procedures. "
                "We adhere to all relevant regulations and maintain strict policies "
                "for financial governance and risk management. "
                "Which specific compliance area are you interested in?"
            )
        else:
            response += (
                "I don't have specific information about that in my knowledge base. "
                "As the Finance Director, I can help with questions about our financial performance, "
                "budgeting, investments, reporting, and compliance. "
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
        if knowledge_area == "performance":
            return (
                "If you need more specific information about our financial performance metrics, "
                "historical trends, or future projections, please let me know, and I'd be happy to provide more details."
            )
        elif knowledge_area == "budgeting":
            return (
                "If you'd like more detailed information about specific budget allocations, expense categories, "
                "or cost management strategies, please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "investment":
            return (
                "If you need more specific information about our investment portfolio, funding sources, "
                "or capital allocation strategy, please let me know, and I'll be happy to help."
            )
        elif knowledge_area == "reporting":
            return (
                "If you're looking for information about specific financial reports, reporting periods, "
                "or accounting methods, please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "compliance":
            return (
                "If you need more detailed information about specific compliance requirements, audit procedures, "
                "or risk management strategies, please let me know, and I'll be happy to provide more information."
            )
        else:
            return (
                "Is there anything specific about our financial operations that you'd like to know more about? "
                "I'm here to help with any finance-related questions you might have."
            )
