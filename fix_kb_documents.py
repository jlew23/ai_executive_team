#!/usr/bin/env python3
"""
Script to fix knowledge base document IDs and metadata.
This script updates the kb_documents.json file to ensure all documents have:
1. UUID-based document IDs
2. Proper timestamps
3. Correct document types
"""

import os
import json
import uuid
from datetime import datetime

# File path for knowledge base documents
KB_STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kb_documents.json')

def load_kb_documents():
    """Load knowledge base documents from file."""
    try:
        if os.path.exists(KB_STORAGE_FILE):
            with open(KB_STORAGE_FILE, 'r') as f:
                documents = json.load(f)
                print(f"Loaded {len(documents)} documents from {KB_STORAGE_FILE}")
                return documents
        else:
            print(f"File {KB_STORAGE_FILE} not found")
            return []
    except Exception as e:
        print(f"Error loading knowledge base documents: {e}")
        return []

def save_kb_documents(documents):
    """Save knowledge base documents to file."""
    try:
        with open(KB_STORAGE_FILE, 'w') as f:
            json.dump(documents, f, indent=2)
        print(f"Knowledge base documents saved to {KB_STORAGE_FILE}")
    except Exception as e:
        print(f"Error saving knowledge base documents: {e}")

def fix_kb_documents():
    """Fix knowledge base document IDs and metadata."""
    documents = load_kb_documents()
    fixed_documents = []
    
    for doc in documents:
        # Convert numeric IDs to UUID strings
        if isinstance(doc.get("doc_id"), int) or (isinstance(doc.get("doc_id"), str) and doc.get("doc_id").isdigit()):
            doc["doc_id"] = str(uuid.uuid4())
        
        # Ensure uploaded timestamp is present and formatted correctly
        if "uploaded" not in doc or doc["uploaded"] == "Unknown":
            doc["uploaded"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ensure document type is present
        if "type" not in doc or doc["type"] == "Unknown":
            # Try to determine type from name
            if "name" in doc and "." in doc["name"]:
                ext = doc["name"].rsplit('.', 1)[1].upper()
                doc["type"] = ext
            else:
                doc["type"] = "TEXT"
        
        # Ensure size is present
        if "size" not in doc or doc["size"] == "Unknown":
            if "content" in doc:
                doc["size"] = f"{len(doc['content']) / 1024:.1f} KB"
            else:
                doc["size"] = "1.0 KB"
        
        fixed_documents.append(doc)
    
    # Save the fixed documents
    save_kb_documents(fixed_documents)
    print(f"Fixed {len(fixed_documents)} documents")

if __name__ == "__main__":
    fix_kb_documents()
