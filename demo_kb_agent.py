"""
Demo script for the knowledge base integration with agents.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import configuration
from config.app_config import (
    BRAIN_DATA_DIR, EMBEDDING_MODEL
)

# Import knowledge base
from knowledge_base import VectorKnowledgeBase, DocumentProcessor

# Import agents
from agents import (
    DirectorAgent,
    SalesAgent,
    MarketingAgent,
    FinanceAgent,
    CustomerServiceAgent,
    TechnicalSupportAgent
)

def main():
    """
    Main function.
    """
    print("=" * 50)
    print("AI Executive Team - Knowledge Base Demo")
    print("=" * 50)
    print("Type 'exit' to quit")
    print("Type 'help' for available commands")
    print()
    
    # Initialize knowledge base
    kb = VectorKnowledgeBase(
        name="default",
        persist_directory=BRAIN_DATA_DIR,
        embedding_model=EMBEDDING_MODEL
    )
    
    # Initialize document processor
    doc_processor = DocumentProcessor()
    
    # Initialize agents
    sales_agent = SalesAgent(kb)
    marketing_agent = MarketingAgent(kb)
    finance_agent = FinanceAgent(kb)
    customer_service_agent = CustomerServiceAgent(kb)
    technical_support_agent = TechnicalSupportAgent(kb)
    
    # Initialize director agent and add team members
    director = DirectorAgent(kb)
    director.add_agent("sales", sales_agent)
    director.add_agent("marketing", marketing_agent)
    director.add_agent("finance", finance_agent)
    director.add_agent("customer", customer_service_agent)
    director.add_agent("technical", technical_support_agent)
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            break
        
        if user_input.lower() == 'help':
            print("\nAvailable commands:")
            print("  exit - Exit the demo")
            print("  help - Show this help message")
            print("  add_file <path> - Add a file to the knowledge base")
            print("  add_text <name> <text> - Add text to the knowledge base")
            print("  add_url <url> - Add a URL to the knowledge base")
            print("  list_sources - List all sources in the knowledge base")
            print("  search <query> [fuzziness] - Search the knowledge base")
            print("  Any other input will be processed by the Director Agent")
            continue
        
        if user_input.lower().startswith('add_file '):
            file_path = user_input[9:].strip()
            try:
                document = doc_processor.process_file(file_path)
                kb.add_document(document)
                print(f"\nAI: Added file {file_path} to the knowledge base")
            except Exception as e:
                print(f"\nAI: Error adding file: {e}")
            continue
        
        if user_input.lower().startswith('add_text '):
            parts = user_input[9:].strip().split(' ', 1)
            if len(parts) != 2:
                print("\nAI: Invalid command format. Use: add_text <name> <text>")
                continue
            
            name, text = parts
            try:
                document = doc_processor.process_text(text, name)
                kb.add_document(document)
                print(f"\nAI: Added text with name {name} to the knowledge base")
            except Exception as e:
                print(f"\nAI: Error adding text: {e}")
            continue
        
        if user_input.lower().startswith('add_url '):
            url = user_input[8:].strip()
            try:
                document = doc_processor.process_url(url)
                kb.add_document(document)
                print(f"\nAI: Added URL {url} to the knowledge base")
            except Exception as e:
                print(f"\nAI: Error adding URL: {e}")
            continue
        
        if user_input.lower() == 'list_sources':
            try:
                documents = kb.list_documents()
                print("\nAI: Knowledge Base Sources:")
                for i, doc in enumerate(documents):
                    print(f"  {i+1}. {doc['source_name']} ({doc['source_type']})")
            except Exception as e:
                print(f"\nAI: Error listing sources: {e}")
            continue
        
        if user_input.lower().startswith('search '):
            parts = user_input[7:].strip().split(' ')
            query = parts[0]
            fuzziness = 100
            if len(parts) > 1:
                try:
                    fuzziness = int(parts[1])
                except ValueError:
                    pass
            
            try:
                results = kb.query(query, k=3, search_fuzziness=fuzziness)
                print(f"\nAI: Search Results for '{query}' (fuzziness={fuzziness}):")
                for i, result in enumerate(results):
                    print(f"  {i+1}. Score: {result['score']:.2f}")
                    print(f"     Content: {result['content'][:100]}...")
                    print(f"     Source: {result['metadata']['source_name']}")
            except Exception as e:
                print(f"\nAI: Error searching: {e}")
            continue
        
        # Process the message through the Director Agent
        response = director.delegate_task(user_input)
        print(f"\nAI: {response}")

if __name__ == "__main__":
    main()
