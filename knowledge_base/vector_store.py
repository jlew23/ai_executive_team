"""
Vector store implementation for the knowledge base.
"""

import os
import json
import logging
import shutil
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from .base import KnowledgeBase
from .document_processor import Document, DocumentChunk

logger = logging.getLogger(__name__)

class VectorKnowledgeBase(KnowledgeBase):
    """
    Vector store implementation of the knowledge base.
    """

    def __init__(
        self,
        name: str,
        persist_directory: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the vector knowledge base.

        Args:
            name: Name of the knowledge base
            persist_directory: Directory to persist the knowledge base
            embedding_model: Name of the embedding model to use
            cache_dir: Directory to cache embeddings (None for no caching)
        """
        super().__init__(name, persist_directory)

        # Initialize embedding model
        self.embedding_model_name = embedding_model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=os.path.join(persist_directory, "chroma"),
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(name)

        # Initialize keyword index
        self.keyword_index_path = os.path.join(persist_directory, "keyword_index.json")
        self.keyword_index = self._load_keyword_index()

        # Initialize document store
        self.document_store_path = os.path.join(persist_directory, "documents.json")
        self.documents = self._load_documents()

        # Initialize cache
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            self.embedding_cache_path = os.path.join(cache_dir, f"{name}_embedding_cache.json")
            self.embedding_cache = self._load_embedding_cache()
        else:
            self.embedding_cache = {}

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the knowledge base.

        Args:
            documents: List of documents to add
        """
        for document in documents:
            self.add_document(document)

    def add_document(self, document: Document) -> None:
        """
        Add a document to the knowledge base.

        Args:
            document: Document to add
        """
        # Store document
        self.documents[document.id] = {
            "id": document.id,
            "source_type": document.source_type,
            "source_name": document.source_name,
            "metadata": document.metadata,
            "version": document.version
        }

        # Add chunks to vector store
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []
        chunk_embeddings = []

        for chunk in document.chunks:
            chunk_ids.append(chunk.id)
            chunk_texts.append(chunk.content)
            chunk_metadatas.append({
                "document_id": document.id,
                "chunk_id": chunk.id,
                "source_type": document.source_type,
                "source_name": document.source_name,
                "version": document.version,
                **chunk.metadata
            })

            # Check if we have a cached embedding
            cached_embedding = self._get_cached_embedding(chunk.content)
            if cached_embedding is not None:
                chunk_embeddings.append(cached_embedding)

            # Add to keyword index
            self._add_to_keyword_index(chunk.id, chunk.content)

        # Add to ChromaDB
        if chunk_embeddings and len(chunk_embeddings) == len(chunk_ids):
            # Use cached embeddings
            self.collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                metadatas=chunk_metadatas,
                embeddings=chunk_embeddings
            )
        else:
            # Let ChromaDB compute embeddings
            self.collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                metadatas=chunk_metadatas
            )

            # Cache the embeddings for future use
            if self.cache_dir:
                for text in chunk_texts:
                    self._cache_embedding(text)

        # Persist changes
        self.persist()

    def search(
        self,
        query: str,
        limit: int = 5,
        semantic_weight: float = 1.0,
        keyword_weight: float = 0.0,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base with hybrid search.

        Args:
            query: Query text
            limit: Number of results to return
            semantic_weight: Weight for semantic search (0.0-1.0)
            keyword_weight: Weight for keyword search (0.0-1.0)
            filter_criteria: Optional filter criteria for the query

        Returns:
            List of documents matching the query
        """
        # Validate weights
        if not (0.0 <= semantic_weight <= 1.0) or not (0.0 <= keyword_weight <= 1.0):
            raise ValueError("Weights must be between 0.0 and 1.0")

        # If weights sum to 0, default to semantic search
        if semantic_weight + keyword_weight == 0.0:
            semantic_weight = 1.0

        # Normalize weights to sum to 1.0
        total_weight = semantic_weight + keyword_weight
        semantic_weight = semantic_weight / total_weight
        keyword_weight = keyword_weight / total_weight

        # Convert to search_fuzziness for backward compatibility
        search_fuzziness = int(semantic_weight * 100)

        return self.query(query, limit, search_fuzziness, filter_criteria)

    def query(
        self,
        query_text: str,
        k: int = 5,
        search_fuzziness: int = 100,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base.

        Args:
            query_text: Query text
            k: Number of results to return
            search_fuzziness: Fuzziness of search (0-100, 100 = pure semantic, 0 = pure keyword)
            filter_criteria: Optional filter criteria for the query

        Returns:
            List of documents matching the query
        """
        if search_fuzziness < 0 or search_fuzziness > 100:
            raise ValueError("search_fuzziness must be between 0 and 100")

        # If pure keyword search
        if search_fuzziness == 0:
            return self._keyword_search(query_text, k, filter_criteria)

        # If pure semantic search
        if search_fuzziness == 100:
            return self._semantic_search(query_text, k, filter_criteria)

        # Hybrid search
        semantic_weight = search_fuzziness / 100
        keyword_weight = 1 - semantic_weight

        semantic_results = self._semantic_search(query_text, k * 2, filter_criteria)
        keyword_results = self._keyword_search(query_text, k * 2, filter_criteria)

        # Combine results
        combined_results = {}

        for result in semantic_results:
            chunk_id = result["chunk_id"]
            combined_results[chunk_id] = {
                **result,
                "score": result["score"] * semantic_weight
            }

        for result in keyword_results:
            chunk_id = result["chunk_id"]
            if chunk_id in combined_results:
                combined_results[chunk_id]["score"] += result["score"] * keyword_weight
                combined_results[chunk_id]["search_type"] = "hybrid"
            else:
                combined_results[chunk_id] = {
                    **result,
                    "score": result["score"] * keyword_weight
                }

        # Sort by score and return top k
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return sorted_results[:k]

    def delete_document(self, document_id: str) -> None:
        """
        Delete a document from the knowledge base.

        Args:
            document_id: ID of the document to delete
        """
        if document_id not in self.documents:
            logger.warning(f"Document {document_id} not found")
            return

        # Get all chunks for this document
        results = self.collection.get(
            where={"document_id": document_id}
        )

        if results["ids"]:
            # Remove from ChromaDB
            self.collection.delete(
                ids=results["ids"]
            )

            # Remove from keyword index
            for chunk_id in results["ids"]:
                self._remove_from_keyword_index(chunk_id)

        # Remove from document store
        del self.documents[document_id]

        # Persist changes
        self.persist()

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the knowledge base.

        Returns:
            List of documents
        """
        return list(self.documents.values())

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from the knowledge base.

        Args:
            document_id: ID of the document to get

        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(document_id)

    def clear(self) -> None:
        """
        Clear the knowledge base.
        """
        # Clear ChromaDB
        self.collection.delete(where={})

        # Clear keyword index
        self.keyword_index = defaultdict(list)

        # Clear document store
        self.documents = {}

        # Persist changes
        self.persist()

    def persist(self) -> None:
        """
        Persist the knowledge base to disk.
        """
        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Save keyword index
        with open(self.keyword_index_path, 'w') as f:
            json.dump(dict(self.keyword_index), f)

        # Save document store
        with open(self.document_store_path, 'w') as f:
            json.dump(self.documents, f)

        # Save embedding cache
        if self.cache_dir and self.embedding_cache:
            with open(self.embedding_cache_path, 'w') as f:
                json.dump(self.embedding_cache, f)

    def update_document(self, document: Document) -> None:
        """
        Update a document in the knowledge base.

        Args:
            document: Updated document
        """
        # Delete the old document
        self.delete_document(document.id)

        # Add the updated document
        self.add_document(document)

    def optimize(self) -> None:
        """
        Optimize the knowledge base for better performance.

        This method performs various optimizations:
        1. Removes duplicate entries
        2. Compacts the vector store
        3. Optimizes the keyword index
        """
        # Compact the vector store (not directly supported by ChromaDB, but we can rebuild)
        logger.info("Optimizing vector store...")

        # Get all documents and chunks
        all_chunks = self.collection.get()

        # Clear the collection
        self.collection.delete(where={})

        # Re-add all chunks
        if all_chunks["ids"]:
            self.collection.add(
                ids=all_chunks["ids"],
                documents=all_chunks["documents"],
                metadatas=all_chunks["metadatas"],
                embeddings=all_chunks["embeddings"]
            )

        # Optimize keyword index by removing empty entries
        logger.info("Optimizing keyword index...")
        optimized_index = defaultdict(list)
        for token, chunk_ids in self.keyword_index.items():
            if chunk_ids:  # Only keep non-empty entries
                optimized_index[token] = list(set(chunk_ids))  # Remove duplicates

        self.keyword_index = optimized_index

        # Persist changes
        self.persist()

        logger.info("Knowledge base optimization complete")

    def _semantic_search(
        self,
        query_text: str,
        k: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search.

        Args:
            query_text: Query text
            k: Number of results to return
            filter_criteria: Optional filter criteria for the query

        Returns:
            List of documents matching the query
        """
        # Get query embedding
        query_embedding = self.embedding_model.encode(query_text)

        # Prepare where clause if filter criteria is provided
        where = filter_criteria if filter_criteria else None

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            where=where
        )

        # Format results
        formatted_results = []

        for i, (chunk_id, document, metadata, distance) in enumerate(zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            # Convert distance to score (1 - distance for cosine distance)
            score = 1 - distance

            formatted_results.append({
                "chunk_id": chunk_id,
                "document_id": metadata["document_id"],
                "content": document,
                "metadata": metadata,
                "score": score,
                "search_type": "semantic"
            })

        return formatted_results

    def _keyword_search(
        self,
        query_text: str,
        k: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword search.

        Args:
            query_text: Query text
            k: Number of results to return
            filter_criteria: Optional filter criteria for the query

        Returns:
            List of documents matching the query
        """
        # Tokenize query
        query_tokens = self._tokenize(query_text)

        # Find matching chunks
        chunk_scores = defaultdict(float)

        for token in query_tokens:
            if token in self.keyword_index:
                for chunk_id in self.keyword_index[token]:
                    chunk_scores[chunk_id] += 1

        # Sort by score
        sorted_chunks = sorted(
            chunk_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Get top k
        top_chunks = sorted_chunks[:k*2]  # Get more than needed to account for filtering

        # Format results
        formatted_results = []

        for chunk_id, score in top_chunks:
            # Normalize score
            normalized_score = score / len(query_tokens)

            # Get chunk from ChromaDB
            where_clause = {"chunk_id": chunk_id}
            if filter_criteria:
                where_clause.update(filter_criteria)

            result = self.collection.get(
                ids=[chunk_id],
                where=where_clause
            )

            if result["ids"]:
                formatted_results.append({
                    "chunk_id": chunk_id,
                    "document_id": result["metadatas"][0]["document_id"],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0],
                    "score": normalized_score,
                    "search_type": "keyword"
                })

                if len(formatted_results) >= k:
                    break

        return formatted_results

    def _add_to_keyword_index(self, chunk_id: str, text: str) -> None:
        """
        Add a chunk to the keyword index.

        Args:
            chunk_id: ID of the chunk
            text: Text of the chunk
        """
        tokens = self._tokenize(text)

        for token in tokens:
            self.keyword_index[token].append(chunk_id)

    def _remove_from_keyword_index(self, chunk_id: str) -> None:
        """
        Remove a chunk from the keyword index.

        Args:
            chunk_id: ID of the chunk
        """
        for token, chunks in self.keyword_index.items():
            if chunk_id in chunks:
                chunks.remove(chunk_id)

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Simple tokenization - lowercase, split on non-alphanumeric
        text = text.lower()
        tokens = [token for token in re.findall(r'\w+', text) if len(token) > 2]
        return tokens

    def _load_keyword_index(self) -> Dict[str, List[str]]:
        """
        Load the keyword index from disk.

        Returns:
            Keyword index
        """
        if os.path.exists(self.keyword_index_path):
            try:
                with open(self.keyword_index_path, 'r') as f:
                    return defaultdict(list, json.load(f))
            except Exception as e:
                logger.error(f"Error loading keyword index: {e}")

        return defaultdict(list)

    def _load_documents(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the document store from disk.

        Returns:
            Document store
        """
        if os.path.exists(self.document_store_path):
            try:
                with open(self.document_store_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading document store: {e}")

        return {}

    def _load_embedding_cache(self) -> Dict[str, List[float]]:
        """
        Load the embedding cache from disk.

        Returns:
            Embedding cache
        """
        if os.path.exists(self.embedding_cache_path):
            try:
                with open(self.embedding_cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading embedding cache: {e}")

        return {}

    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get a cached embedding for a text.

        Args:
            text: Text to get embedding for

        Returns:
            Cached embedding if found, None otherwise
        """
        if not self.cache_dir:
            return None

        # Use a hash of the text as the key
        text_hash = str(hash(text))

        return self.embedding_cache.get(text_hash)

    def _cache_embedding(self, text: str) -> None:
        """
        Cache an embedding for a text.

        Args:
            text: Text to cache embedding for
        """
        if not self.cache_dir:
            return

        # Use a hash of the text as the key
        text_hash = str(hash(text))

        # Check if already cached
        if text_hash in self.embedding_cache:
            return

        # Generate and cache the embedding
        embedding = self.embedding_model.encode(text).tolist()
        self.embedding_cache[text_hash] = embedding

        # Periodically save the cache to disk
        if len(self.embedding_cache) % 100 == 0:
            with open(self.embedding_cache_path, 'w') as f:
                json.dump(self.embedding_cache, f)
