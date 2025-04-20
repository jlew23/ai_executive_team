"""
Knowledge Base module for AI Executive Team.

This module provides functionality for managing knowledge bases, including:
- Document ingestion from various sources (files, text, websites)
- Vector embeddings for semantic search
- Keyword indexing for exact matches
- Hybrid search combining semantic and keyword search
- Document versioning and update capabilities
- Optimized vector storage and retrieval
"""

from .base import KnowledgeBase
from .vector_store import VectorKnowledgeBase
from .document_processor import DocumentProcessor, Document, DocumentChunk
from .version_manager import VersionManager

__all__ = [
    'KnowledgeBase',
    'VectorKnowledgeBase',
    'DocumentProcessor',
    'Document',
    'DocumentChunk',
    'VersionManager'
]
