# Knowledge Base Module

The Knowledge Base module provides Retrieval-Augmented Generation (RAG) capabilities for the AI Executive Team.

## Features

- **Document Ingestion**: Ingest documents from various sources (files, text, websites)
- **Vector Embeddings**: Generate vector embeddings for semantic search
- **Keyword Indexing**: Index documents for keyword search
- **Hybrid Search**: Combine semantic and keyword search for optimal results
- **Document Management**: Add, update, and delete documents
- **API Integration**: Expose search functionality via API endpoints
- **Agent Integration**: Provide search capabilities to AI Executive Team agents

## Usage

### Adding Documents

```python
from knowledge_base import DocumentProcessor, VectorKnowledgeBase

# Initialize document processor
document_processor = DocumentProcessor()

# Initialize knowledge base
kb = VectorKnowledgeBase(
    name="ai_executive_team_kb",
    persist_directory="kb_data",
    embedding_model="all-MiniLM-L6-v2"
)

# Process a file
document = document_processor.process_file("path/to/file.pdf")
kb.add_document(document)

# Process text
document = document_processor.process_text("This is some text to add to the knowledge base.")
kb.add_document(document)

# Process a URL
document = document_processor.process_url("https://example.com")
kb.add_document(document)
```

### Searching the Knowledge Base

```python
# Search with pure semantic search
results = kb.search(
    query="What is the mission of AI Executive Team?",
    limit=5,
    semantic_weight=1.0,
    keyword_weight=0.0
)

# Search with hybrid search (80% semantic, 20% keyword)
results = kb.search(
    query="What is the mission of AI Executive Team?",
    limit=5,
    semantic_weight=0.8,
    keyword_weight=0.2
)

# Format results
for result in results:
    print(f"Source: {result['source']}")
    print(f"Content: {result['content']}")
    print(f"Score: {result['score']}")
    print()
```

### Using the API

```bash
# Search the knowledge base
curl -X POST -H "Content-Type: application/json" -d '{
    "query": "What is the mission of AI Executive Team?",
    "max_results": 5,
    "search_fuzziness": 80
}' http://localhost:3001/api/knowledgebase/search
```

### Agent Integration

```python
from agent_tools.kb_search_tool import KnowledgeBaseSearchTool

# Initialize the knowledge base search tool
kb_search_tool = KnowledgeBaseSearchTool()

# Search the knowledge base
search_results = kb_search_tool.search(
    query="What is the mission of AI Executive Team?",
    max_results=2,
    search_fuzziness=80  # 80% semantic, 20% keyword
)

# Format results for agent consumption
formatted_results = kb_search_tool.format_results_for_agent(search_results)
```

## Architecture

The Knowledge Base module consists of the following components:

- **Document Processor**: Processes documents from various sources
- **Vector Store**: Stores document embeddings for semantic search
- **Keyword Index**: Indexes documents for keyword search
- **API Endpoints**: Expose search functionality via API
- **Agent Tools**: Provide search capabilities to agents

## Dependencies

- `sentence-transformers`: For generating vector embeddings
- `chromadb`: For storing and querying vector embeddings
- `langchain`: For text splitting and processing
- `beautifulsoup4`: For web scraping
- `pypdf2`: For PDF processing
- `python-docx`: For DOCX processing
- `pandas`: For CSV processing
