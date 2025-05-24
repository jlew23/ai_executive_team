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
            # Use the search method instead of query
            results = self.knowledge_base.search(
                query=query,
                limit=max_results,
                semantic_weight=search_fuzziness/100,  # Convert to 0-1 range
                keyword_weight=(100-search_fuzziness)/100  # Inverse of semantic weight
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
            # Handle different result structures
            # Extract score if available
            score = result.get('score', 0)
            
            # Extract content from various possible fields
            text = ""
            if 'text' in result:
                text = result['text']
            elif 'content' in result:
                text = result['content']
            elif 'page_content' in result:
                text = result['page_content']
            else:
                # If no content field is found, use a placeholder
                text = "[Content not available in this format]"
            
            # Get metadata safely
            metadata = result.get('metadata', {})
            source_name = metadata.get('source_name', metadata.get('name', 'Unknown'))
            source_type = metadata.get('type', 'Document')
            uploaded_at = metadata.get('uploaded_at', metadata.get('uploaded', 'Unknown date'))
            
            # Format the result with more detailed information
            formatted += f"Result {i+1} (Relevance: {score:.2f}):\n"
            formatted += f"{text}\n\n"
            formatted += f"Source: {source_name} ({source_type})\n"
            formatted += f"Added: {uploaded_at}\n\n"
        
        return formatted
