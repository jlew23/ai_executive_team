"""
Version Manager for the knowledge base.
This module provides functionality for managing document versions.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

from .document_processor import Document

logger = logging.getLogger(__name__)

class VersionManager:
    """
    Manages document versions in the knowledge base.
    
    This class provides functionality for:
    1. Tracking document versions
    2. Storing version history
    3. Retrieving previous versions
    4. Comparing versions
    5. Rolling back to previous versions
    """
    
    def __init__(self, persist_directory: str):
        """
        Initialize the version manager.
        
        Args:
            persist_directory: Directory to persist version information
        """
        self.persist_directory = persist_directory
        self.versions_path = os.path.join(persist_directory, "versions")
        self.version_index_path = os.path.join(persist_directory, "version_index.json")
        self.version_index = self._load_version_index()
        
        # Create versions directory if it doesn't exist
        os.makedirs(self.versions_path, exist_ok=True)
    
    def add_document(self, document: Document) -> None:
        """
        Add a document to version control.
        
        Args:
            document: Document to add
        """
        # Add to version index
        self.version_index[document.id] = {
            "current_version": document.version,
            "versions": [document.version],
            "last_updated": self.get_current_timestamp()
        }
        
        # Save document version
        self._save_document_version(document)
        
        # Persist changes
        self._persist_version_index()
    
    def update_document(self, document: Document) -> None:
        """
        Update a document in version control.
        
        Args:
            document: Updated document
        """
        if document.id not in self.version_index:
            # If document doesn't exist, add it
            self.add_document(document)
            return
        
        # Update version index
        self.version_index[document.id]["current_version"] = document.version
        self.version_index[document.id]["versions"].append(document.version)
        self.version_index[document.id]["last_updated"] = self.get_current_timestamp()
        
        # Save document version
        self._save_document_version(document)
        
        # Persist changes
        self._persist_version_index()
    
    def get_document(self, document_id: str, version: Optional[int] = None) -> Optional[Document]:
        """
        Get a document from version control.
        
        Args:
            document_id: ID of the document to get
            version: Specific version to get (None for current version)
            
        Returns:
            Document if found, None otherwise
        """
        if document_id not in self.version_index:
            logger.warning(f"Document {document_id} not found in version index")
            return None
        
        # Determine which version to get
        if version is None:
            version = self.version_index[document_id]["current_version"]
        elif version not in self.version_index[document_id]["versions"]:
            logger.warning(f"Version {version} of document {document_id} not found")
            return None
        
        # Load document version
        return self._load_document_version(document_id, version)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from version control.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if document was deleted, False otherwise
        """
        if document_id not in self.version_index:
            logger.warning(f"Document {document_id} not found in version index")
            return False
        
        # Delete all version files
        for version in self.version_index[document_id]["versions"]:
            version_path = self._get_version_path(document_id, version)
            if os.path.exists(version_path):
                os.remove(version_path)
        
        # Remove from version index
        del self.version_index[document_id]
        
        # Persist changes
        self._persist_version_index()
        
        return True
    
    def list_document_versions(self, document_id: str) -> List[Dict[str, Any]]:
        """
        List all versions of a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of version information
        """
        if document_id not in self.version_index:
            logger.warning(f"Document {document_id} not found in version index")
            return []
        
        versions = []
        for version in sorted(self.version_index[document_id]["versions"]):
            document = self._load_document_version(document_id, version)
            if document:
                versions.append({
                    "version": version,
                    "timestamp": document.metadata.get("updated_at", "Unknown"),
                    "is_current": version == self.version_index[document_id]["current_version"]
                })
        
        return versions
    
    def rollback_document(self, document_id: str, version: int) -> Optional[Document]:
        """
        Roll back a document to a previous version.
        
        Args:
            document_id: ID of the document to roll back
            version: Version to roll back to
            
        Returns:
            Rolled back document if successful, None otherwise
        """
        if document_id not in self.version_index:
            logger.warning(f"Document {document_id} not found in version index")
            return None
        
        if version not in self.version_index[document_id]["versions"]:
            logger.warning(f"Version {version} of document {document_id} not found")
            return None
        
        # Get the document at the specified version
        document = self._load_document_version(document_id, version)
        if not document:
            logger.error(f"Failed to load version {version} of document {document_id}")
            return None
        
        # Create a new version based on the old one
        current_version = self.version_index[document_id]["current_version"]
        new_version = current_version + 1
        
        # Update document
        document.version = new_version
        document.metadata["updated_at"] = self.get_current_timestamp()
        document.metadata["rollback_from"] = version
        
        # Update version index
        self.version_index[document_id]["current_version"] = new_version
        self.version_index[document_id]["versions"].append(new_version)
        self.version_index[document_id]["last_updated"] = self.get_current_timestamp()
        
        # Save document version
        self._save_document_version(document)
        
        # Persist changes
        self._persist_version_index()
        
        return document
    
    def compare_versions(self, document_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        Compare two versions of a document.
        
        Args:
            document_id: ID of the document
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Comparison information
        """
        if document_id not in self.version_index:
            logger.warning(f"Document {document_id} not found in version index")
            return {"error": "Document not found"}
        
        if version1 not in self.version_index[document_id]["versions"]:
            logger.warning(f"Version {version1} of document {document_id} not found")
            return {"error": f"Version {version1} not found"}
        
        if version2 not in self.version_index[document_id]["versions"]:
            logger.warning(f"Version {version2} of document {document_id} not found")
            return {"error": f"Version {version2} not found"}
        
        # Load both versions
        doc1 = self._load_document_version(document_id, version1)
        doc2 = self._load_document_version(document_id, version2)
        
        if not doc1 or not doc2:
            return {"error": "Failed to load one or both versions"}
        
        # Compare metadata
        metadata_diff = {}
        for key in set(doc1.metadata.keys()) | set(doc2.metadata.keys()):
            if key not in doc1.metadata:
                metadata_diff[key] = {"added": doc2.metadata[key]}
            elif key not in doc2.metadata:
                metadata_diff[key] = {"removed": doc1.metadata[key]}
            elif doc1.metadata[key] != doc2.metadata[key]:
                metadata_diff[key] = {"from": doc1.metadata[key], "to": doc2.metadata[key]}
        
        # Compare content (simple diff for now)
        content_diff = {
            "length_change": len(doc2.content) - len(doc1.content),
            "char_count_v1": len(doc1.content),
            "char_count_v2": len(doc2.content),
            "word_count_v1": len(doc1.content.split()),
            "word_count_v2": len(doc2.content.split())
        }
        
        return {
            "document_id": document_id,
            "version1": version1,
            "version2": version2,
            "metadata_diff": metadata_diff,
            "content_diff": content_diff,
            "chunk_count_v1": len(doc1.chunks),
            "chunk_count_v2": len(doc2.chunks)
        }
    
    def get_current_timestamp(self) -> int:
        """
        Get the current timestamp.
        
        Returns:
            Current timestamp in seconds since epoch
        """
        return int(time.time())
    
    def _save_document_version(self, document: Document) -> None:
        """
        Save a document version.
        
        Args:
            document: Document to save
        """
        version_path = self._get_version_path(document.id, document.version)
        
        # Convert document to dictionary
        document_dict = asdict(document)
        
        # Save to file
        with open(version_path, 'w') as f:
            json.dump(document_dict, f)
    
    def _load_document_version(self, document_id: str, version: int) -> Optional[Document]:
        """
        Load a document version.
        
        Args:
            document_id: ID of the document
            version: Version to load
            
        Returns:
            Document if found, None otherwise
        """
        version_path = self._get_version_path(document_id, version)
        
        if not os.path.exists(version_path):
            logger.warning(f"Version file {version_path} not found")
            return None
        
        try:
            with open(version_path, 'r') as f:
                document_dict = json.load(f)
            
            # Convert dictionary to Document
            document = Document(
                id=document_dict["id"],
                source_type=document_dict["source_type"],
                source_name=document_dict["source_name"],
                content=document_dict["content"],
                metadata=document_dict["metadata"],
                version=document_dict["version"],
                previous_versions=document_dict["previous_versions"]
            )
            
            # Convert chunks
            document.chunks = []
            for chunk_dict in document_dict["chunks"]:
                chunk = DocumentChunk(
                    id=chunk_dict["id"],
                    document_id=chunk_dict["document_id"],
                    content=chunk_dict["content"],
                    metadata=chunk_dict["metadata"]
                )
                document.chunks.append(chunk)
            
            return document
            
        except Exception as e:
            logger.error(f"Error loading document version: {e}")
            return None
    
    def _get_version_path(self, document_id: str, version: int) -> str:
        """
        Get the path to a document version file.
        
        Args:
            document_id: ID of the document
            version: Version number
            
        Returns:
            Path to the version file
        """
        return os.path.join(self.versions_path, f"{document_id}_v{version}.json")
    
    def _load_version_index(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the version index from disk.
        
        Returns:
            Version index
        """
        if os.path.exists(self.version_index_path):
            try:
                with open(self.version_index_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading version index: {e}")
        
        return {}
    
    def _persist_version_index(self) -> None:
        """
        Persist the version index to disk.
        """
        try:
            with open(self.version_index_path, 'w') as f:
                json.dump(self.version_index, f)
        except Exception as e:
            logger.error(f"Error persisting version index: {e}")
