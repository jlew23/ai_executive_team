#!/usr/bin/env python3
"""
Script to apply fixes to the run_dashboard.py file for knowledge base document handling.
This script updates the document viewing and editing functionality to properly handle UUID-based document IDs.
"""

import os
import re

# File path for the dashboard file
DASHBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_dashboard.py')

def fix_document_viewing():
    """Fix document viewing functionality to handle UUID-based document IDs."""
    with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix document viewing function
    view_pattern = r'(\s+else:\s+# Use sample documents\s+)doc_id = int\(doc_id\) if doc_id\.isdigit\(\) else 0\s+document = next\(\(d for d in kb_documents if d\["doc_id"\] == doc_id\), None\)'
    view_replacement = r'\1# Handle string-based document IDs (UUID)\n            document = next((d for d in kb_documents if str(d["doc_id"]) == str(doc_id)), None)'
    content = re.sub(view_pattern, view_replacement, content)
    
    # Fix document editing function
    edit_pattern = r'(\s+else:\s+# Use sample documents\s+)doc_id = int\(doc_id\) if doc_id\.isdigit\(\) else 0\s+document = next\(\(d for d in kb_documents if d\["doc_id"\] == doc_id\), None\)'
    edit_replacement = r'\1# Handle string-based document IDs (UUID)\n            document = next((d for d in kb_documents if str(d["doc_id"]) == str(doc_id)), None)'
    content = re.sub(edit_pattern, edit_replacement, content)
    
    # Fix document deletion function
    delete_pattern = r'(\s+else:\s+# Use sample documents\s+)doc_id = int\(doc_id\) if doc_id\.isdigit\(\) else 0\s+document_index = next\(\(i for i, d in enumerate\(kb_documents\) if d\["doc_id"\] == doc_id\), -1\)'
    delete_replacement = r'\1# Handle string-based document IDs (UUID)\n            document_index = next((i for i, d in enumerate(kb_documents) if str(d["doc_id"]) == str(doc_id)), -1)'
    content = re.sub(delete_pattern, delete_replacement, content)
    
    # Write the updated content back to the file
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed document viewing, editing, and deletion functionality")

if __name__ == "__main__":
    fix_document_viewing()
