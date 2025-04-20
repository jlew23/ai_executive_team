"""
Unit tests for the knowledge base implementation.
"""

import pytest
from unittest.mock import MagicMock, patch
import os
import tempfile

@pytest.mark.unit
def test_knowledge_base_initialization(knowledge_base):
    """Test that the knowledge base initializes correctly."""
    assert knowledge_base is not None
    assert hasattr(knowledge_base, 'search')
    assert hasattr(knowledge_base, 'add_document')

@pytest.mark.unit
def test_vector_store_initialization(vector_store):
    """Test that the vector store initializes correctly."""
    assert vector_store is not None
    assert hasattr(vector_store, 'add')
    assert hasattr(vector_store, 'search')
    assert hasattr(vector_store, 'delete')

@pytest.mark.unit
def test_vector_store_add_and_search(vector_store):
    """Test adding vectors and searching."""
    # Mock the embedding function
    vector_store._get_embedding = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
    
    # Add some vectors
    vector_store.add(
        texts=["This is a test document", "Another test document"],
        metadatas=[{"source": "test1"}, {"source": "test2"}],
        ids=["id1", "id2"]
    )
    
    # Search for vectors
    results = vector_store.search(
        query="test document",
        limit=2
    )
    
    # Check results
    assert len(results) == 2
    assert results[0]["id"] in ["id1", "id2"]
    assert results[1]["id"] in ["id1", "id2"]
    assert results[0]["metadata"]["source"] in ["test1", "test2"]
    assert results[1]["metadata"]["source"] in ["test1", "test2"]

@pytest.mark.unit
def test_vector_store_delete(vector_store):
    """Test deleting vectors."""
    # Mock the embedding function
    vector_store._get_embedding = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
    
    # Add some vectors
    vector_store.add(
        texts=["This is a test document", "Another test document"],
        metadatas=[{"source": "test1"}, {"source": "test2"}],
        ids=["id1", "id2"]
    )
    
    # Delete a vector
    vector_store.delete(ids=["id1"])
    
    # Search for vectors
    results = vector_store.search(
        query="test document",
        limit=2
    )
    
    # Check results
    assert len(results) == 1
    assert results[0]["id"] == "id2"
    assert results[0]["metadata"]["source"] == "test2"

@pytest.mark.unit
def test_document_processor_initialization(document_processor):
    """Test that the document processor initializes correctly."""
    assert document_processor is not None
    assert hasattr(document_processor, 'process_document')
    assert hasattr(document_processor, 'get_supported_extensions')

@pytest.mark.unit
def test_document_processor_supported_extensions(document_processor):
    """Test that the document processor reports supported extensions."""
    extensions = document_processor.get_supported_extensions()
    assert len(extensions) > 0
    assert ".txt" in extensions
    assert ".pdf" in extensions
    assert ".docx" in extensions

@pytest.mark.unit
def test_document_processor_process_text_file(document_processor):
    """Test processing a text file."""
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
        temp.write(b"This is a test document.\nIt has multiple lines.\nThis is for testing.")
        temp_path = temp.name
    
    try:
        # Mock the vector store
        mock_vector_store = MagicMock()
        document_processor.vector_store = mock_vector_store
        
        # Process the document
        document_id = document_processor.process_document(
            file_path=temp_path,
            metadata={"title": "Test Document", "category": "test"}
        )
        
        # Check that the document was processed
        assert document_id is not None
        
        # Check that the vector store was called
        mock_vector_store.add.assert_called_once()
        
        # Check the chunks
        args, kwargs = mock_vector_store.add.call_args
        assert len(kwargs["texts"]) > 0
        assert "This is a test document" in kwargs["texts"][0]
        assert all(isinstance(m, dict) for m in kwargs["metadatas"])
        assert all("document_id" in m for m in kwargs["metadatas"])
        assert all("title" in m for m in kwargs["metadatas"])
        assert all("category" in m for m in kwargs["metadatas"])
    finally:
        # Clean up
        os.unlink(temp_path)

@pytest.mark.unit
def test_version_manager_initialization():
    """Test that the version manager initializes correctly."""
    from knowledge_base.version_manager import VersionManager
    
    manager = VersionManager()
    assert manager is not None
    assert hasattr(manager, 'create_version')
    assert hasattr(manager, 'get_version')
    assert hasattr(manager, 'get_versions')
    assert hasattr(manager, 'rollback')

@pytest.mark.unit
def test_version_manager_create_and_get_version():
    """Test creating and retrieving document versions."""
    from knowledge_base.version_manager import VersionManager
    
    manager = VersionManager()
    
    # Create a version
    version_id = manager.create_version(
        document_id="doc1",
        content="This is version 1",
        metadata={"version": 1}
    )
    
    # Get the version
    version = manager.get_version(version_id)
    
    # Check the version
    assert version is not None
    assert version["document_id"] == "doc1"
    assert version["content"] == "This is version 1"
    assert version["metadata"]["version"] == 1

@pytest.mark.unit
def test_version_manager_get_versions():
    """Test retrieving all versions of a document."""
    from knowledge_base.version_manager import VersionManager
    
    manager = VersionManager()
    
    # Create multiple versions
    manager.create_version(
        document_id="doc2",
        content="This is version 1",
        metadata={"version": 1}
    )
    manager.create_version(
        document_id="doc2",
        content="This is version 2",
        metadata={"version": 2}
    )
    
    # Get all versions
    versions = manager.get_versions("doc2")
    
    # Check the versions
    assert len(versions) == 2
    assert versions[0]["document_id"] == "doc2"
    assert versions[1]["document_id"] == "doc2"
    assert versions[0]["metadata"]["version"] == 1
    assert versions[1]["metadata"]["version"] == 2

@pytest.mark.unit
def test_version_manager_rollback():
    """Test rolling back to a previous version."""
    from knowledge_base.version_manager import VersionManager
    
    manager = VersionManager()
    
    # Create multiple versions
    v1_id = manager.create_version(
        document_id="doc3",
        content="This is version 1",
        metadata={"version": 1}
    )
    v2_id = manager.create_version(
        document_id="doc3",
        content="This is version 2",
        metadata={"version": 2}
    )
    
    # Rollback to version 1
    rollback_id = manager.rollback("doc3", v1_id)
    
    # Get the rollback version
    rollback = manager.get_version(rollback_id)
    
    # Check the rollback
    assert rollback is not None
    assert rollback["document_id"] == "doc3"
    assert rollback["content"] == "This is version 1"
    assert rollback["metadata"]["version"] == 3  # New version number
    assert rollback["metadata"]["rollback_from"] == v1_id
