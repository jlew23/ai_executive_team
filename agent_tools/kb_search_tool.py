"""
Knowledge Base search tool for AI Executive Team agents.
"""

import requests
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class KnowledgeBaseSearchTool:
    """
    Tool for searching the knowledge base.
    """
    
    def __init__(self, api_url: str = "http://localhost:3001/api/knowledgebase/search"):
        """
        Initialize the knowledge base search tool.
        
        Args:
            api_url: URL of the knowledge base search API
        """
        self.api_url = api_url
    
    def search(
        self,
        query: str,
        max_results: int = 4,
        search_fuzziness: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Args:
            query: Query text
            max_results: Maximum number of results to return
            search_fuzziness: Fuzziness of search (0-100, 100 = pure semantic, 0 = pure keyword)
            
        Returns:
            List of search results
        """
        try:
            # Call the API
            response = requests.post(
                self.api_url,
                json={
                    "query": query,
                    "max_results": max_results,
                    "search_fuzziness": search_fuzziness
                }
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if data.get("status") != "success":
                logger.error(f"Error searching knowledge base: {data.get('error', 'Unknown error')}")
                return []
            
            return data.get("results", [])
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def format_results_for_agent(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results for agent consumption.
        
        Args:
            results: Search results
            
        Returns:
            Formatted results as a string
        """
        if not results:
            return "No relevant information found in the knowledge base."
        
        formatted_results = "Here is relevant information from the knowledge base:\n\n"
        
        for i, result in enumerate(results, 1):
            formatted_results += f"[{i}] {result.get('source', 'Unknown source')}:\n"
            formatted_results += f"{result.get('content', '')}\n\n"
        
        return formatted_results
