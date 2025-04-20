"""
Base Knowledge Base implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class KnowledgeBase(ABC):
    """
    Abstract base class for knowledge base implementations.
    """
    
    def __init__(self, name: str, persist_directory: str):
        """
        Initialize the knowledge base.
        
        Args:
            name: Name of the knowledge base
            persist_directory: Directory to persist the knowledge base
        """
        self.name = name
        self.persist_directory = persist_directory
    
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the knowledge base.
        
        Args:
            documents: List of documents to add
        """
        pass
    
    @abstractmethod
    def add_document(self, document: Dict[str, Any]) -> None:
        """
        Add a single document to the knowledge base.
        
        Args:
            document: Document to add
        """
        pass
    
    @abstractmethod
    def query(self, query_text: str, k: int = 5, search_fuzziness: int = 100) -> List[Dict[str, Any]]:
        """
        Query the knowledge base.
        
        Args:
            query_text: Query text
            k: Number of results to return
            search_fuzziness: Fuzziness of search (0-100, 100 = pure semantic, 0 = pure keyword)
            
        Returns:
            List of documents matching the query
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id: ID of the document to delete
        """
        pass
    
    @abstractmethod
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the knowledge base.
        
        Returns:
            List of documents
        """
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from the knowledge base.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear the knowledge base.
        """
        pass
    
    @abstractmethod
    def persist(self) -> None:
        """
        Persist the knowledge base to disk.
        """
        pass
