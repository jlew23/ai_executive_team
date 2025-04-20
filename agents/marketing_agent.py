"""
Marketing Agent for the AI Executive Team.
This agent handles marketing-related queries and tasks.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from .base_agent import Agent

logger = logging.getLogger(__name__)

class MarketingAgent(Agent):
    """
    Marketing Agent that handles marketing-related queries and tasks.
    
    This agent is responsible for:
    1. Providing information about marketing strategies and campaigns
    2. Answering questions about brand positioning and messaging
    3. Offering insights on marketing performance and metrics
    4. Assisting with content marketing and social media strategies
    """
    
    def __init__(self, knowledge_base: Any):
        """
        Initialize the Marketing Agent.
        
        Args:
            knowledge_base (Any): The knowledge base instance for retrieving information
        """
        super().__init__("Marketing", "Marketing Director", knowledge_base)
        
        # Marketing-specific knowledge areas
        self.knowledge_areas = {
            "strategy": ["strategy", "plan", "approach", "positioning", "target audience", "segment"],
            "campaigns": ["campaign", "promotion", "launch", "initiative", "event", "program"],
            "content": ["content", "blog", "article", "video", "webinar", "ebook", "whitepaper"],
            "social_media": ["social media", "facebook", "twitter", "linkedin", "instagram", "tiktok", "social"],
            "performance": ["performance", "metric", "kpi", "roi", "conversion", "engagement", "analytics"]
        }
    
    def _generate_response(self, message: str, context: List[Dict[str, Any]], 
                          user_id: Optional[str], channel_id: Optional[str], 
                          metadata: Optional[Dict[str, Any]]) -> str:
        """
        Generate a marketing-specific response based on the message and context.
        
        Args:
            message (str): The message to respond to
            context (List[Dict[str, Any]]): The relevant context from the knowledge base
            user_id (Optional[str]): The ID of the user who sent the message
            channel_id (Optional[str]): The ID of the channel where the message was sent
            metadata (Optional[Dict[str, Any]]): Additional metadata about the message
            
        Returns:
            str: The Marketing Agent's response
        """
        # Identify which marketing knowledge area is most relevant to the message
        knowledge_area = self._identify_knowledge_area(message)
        
        # If we don't have context, provide a helpful response based on the knowledge area
        if not context:
            return self._generate_no_context_response(message, knowledge_area)
        
        # Create a response based on the context and knowledge area
        response = f"I'm {self.name}, the {self.role}. "
        
        if knowledge_area == "strategy":
            response += "Here's information about our marketing strategy:\n\n"
        elif knowledge_area == "campaigns":
            response += "Here's information about our marketing campaigns:\n\n"
        elif knowledge_area == "content":
            response += "Here's information about our content marketing:\n\n"
        elif knowledge_area == "social_media":
            response += "Here's information about our social media strategy:\n\n"
        elif knowledge_area == "performance":
            response += "Here's information about our marketing performance:\n\n"
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
        Identify which marketing knowledge area is most relevant to the message.
        
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
        
        # Default to general marketing strategy if no specific area is identified
        return "strategy"
    
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
            "strategy": ["Marketing Strategy", "Brand Strategy", "Positioning", "Target Audience", "Market Segments"],
            "campaigns": ["Marketing Campaigns", "Promotions", "Launches", "Initiatives", "Events", "Programs"],
            "content": ["Content Marketing", "Content Strategy", "Blog", "Articles", "Videos", "Webinars", "Ebooks"],
            "social_media": ["Social Media", "Social Media Strategy", "Facebook", "Twitter", "LinkedIn", "Instagram"],
            "performance": ["Marketing Performance", "Marketing Metrics", "KPIs", "ROI", "Conversions", "Analytics"]
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
        
        if knowledge_area == "strategy":
            response += (
                "I'd be happy to discuss our marketing strategy with you. "
                "Our approach focuses on understanding customer needs, creating compelling messaging, "
                "and delivering value through multiple channels. "
                "Could you let me know which aspect of our strategy you're interested in?"
            )
        elif knowledge_area == "campaigns":
            response += (
                "I'd be happy to tell you about our marketing campaigns. "
                "We run various types of campaigns including product launches, seasonal promotions, "
                "and ongoing awareness initiatives. "
                "Could you specify which campaign or type of campaign you're interested in?"
            )
        elif knowledge_area == "content":
            response += (
                "I'd be happy to discuss our content marketing strategy. "
                "We create various types of content including blog posts, videos, webinars, "
                "ebooks, and whitepapers to engage our audience at different stages of the buyer journey. "
                "Which aspect of our content marketing are you interested in?"
            )
        elif knowledge_area == "social_media":
            response += (
                "I'd be happy to discuss our social media strategy. "
                "We maintain an active presence on platforms like LinkedIn, Twitter, Facebook, and Instagram, "
                "each with tailored content and engagement strategies. "
                "Which platform or aspect of our social media approach would you like to know more about?"
            )
        elif knowledge_area == "performance":
            response += (
                "I'd be happy to discuss our marketing performance metrics. "
                "We track various KPIs including engagement rates, conversion rates, customer acquisition cost, "
                "and return on marketing investment. "
                "Which specific metrics are you interested in?"
            )
        else:
            response += (
                "I don't have specific information about that in my knowledge base. "
                "As the Marketing Director, I can help with questions about our marketing strategy, "
                "campaigns, content, social media, and performance metrics. "
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
        if knowledge_area == "strategy":
            return (
                "If you need more specific information about our marketing strategy, target audience, "
                "or brand positioning, please let me know, and I'd be happy to provide more details."
            )
        elif knowledge_area == "campaigns":
            return (
                "If you'd like more detailed information about specific campaigns, timelines, or results, "
                "please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "content":
            return (
                "If you need more specific information about our content strategy, editorial calendar, "
                "or content performance, please let me know, and I'll be happy to help."
            )
        elif knowledge_area == "social_media":
            return (
                "If you're looking for information about specific social media platforms, engagement strategies, "
                "or content types, please let me know, and I can provide more targeted information."
            )
        elif knowledge_area == "performance":
            return (
                "If you need more detailed performance metrics or have questions about specific KPIs, "
                "please let me know, and I'll be happy to provide more information."
            )
        else:
            return (
                "Is there anything specific about our marketing operations that you'd like to know more about? "
                "I'm here to help with any marketing-related questions you might have."
            )
