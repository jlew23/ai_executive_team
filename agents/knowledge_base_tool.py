"""
Knowledge Base Tool for agents.
"""

import logging
from typing import List, Dict, Any, Optional

from knowledge_base import VectorKnowledgeBase

logger = logging.getLogger(__name__)

class KnowledgeBaseTool:
    """
    Tool for agents to query the knowledge base.
    """
    
    def __init__(self, knowledge_base: VectorKnowledgeBase):
        """
        Initialize the knowledge base tool.
        
        Args:
            knowledge_base: Knowledge base to query
        """
        self.knowledge_base = knowledge_base
    
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
            List of documents matching the query
        """
        try:
            results = self.knowledge_base.query(
                query_text=query,
                k=max_results,
                search_fuzziness=search_fuzziness
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as a string.
        
        Args:
            results: Search results
            
        Returns:
            Formatted results
        """
        if not results:
            return "No results found."
        
        formatted = "Knowledge Base Search Results:\n\n"
        
        for i, result in enumerate(results):
            formatted += f"Result {i+1} (Score: {result['score']:.2f}):\n"
            formatted += f"{result['content']}\n"
            formatted += f"Source: {result['metadata']['source_name']}\n\n"
        
        return formatted
