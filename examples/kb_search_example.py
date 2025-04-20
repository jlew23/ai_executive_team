"""
Example of using the knowledge base search tool in an agent.
"""

import os
import sys
import logging
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_tools.kb_search_tool import KnowledgeBaseSearchTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_agent_with_kb_search():
    """
    Simulate an agent using the knowledge base search tool.
    """
    # Initialize the knowledge base search tool
    kb_search_tool = KnowledgeBaseSearchTool()
    
    # Simulate user query
    user_query = "What is the mission of AI Executive Team?"
    
    # Log the query
    logger.info(f"User query: {user_query}")
    
    # Agent decides to search the knowledge base
    logger.info("Agent: I'll search our knowledge base for information about the mission.")
    
    # Search the knowledge base
    search_results = kb_search_tool.search(
        query=user_query,
        max_results=2,
        search_fuzziness=80  # 80% semantic, 20% keyword
    )
    
    # Format results for agent consumption
    formatted_results = kb_search_tool.format_results_for_agent(search_results)
    
    # Log the results
    logger.info(f"Knowledge base search results:\n{formatted_results}")
    
    # Simulate agent response
    agent_response = "Based on our knowledge base, the mission of AI Executive Team is to revolutionize business management by providing AI executives that can make data-driven decisions, automate routine tasks, and provide strategic insights 24/7."
    
    # Log the agent response
    logger.info(f"Agent response: {agent_response}")
    
    return agent_response

if __name__ == "__main__":
    simulate_agent_with_kb_search()
