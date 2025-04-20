# AI-Powered Executive Team - Simplified Version
# This version doesn't rely on external dependencies for testing

import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simple knowledge base implementation
class SimpleKnowledgeBase:
    def __init__(self, persist_directory="./brain_data"):
        self.persist_directory = persist_directory
        self.documents = []
        self._load_documents()

    def _load_documents(self):
        """Load documents from the data directory"""
        try:
            data_dir = "./data"
            for filename in os.listdir(data_dir):
                if filename.endswith(".txt"):
                    with open(os.path.join(data_dir, filename), 'r') as f:
                        content = f.read()
                        self.documents.append({
                            "filename": filename,
                            "content": content
                        })
            logger.info(f"Loaded {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error loading documents: {e}")

    def add_document(self, filename, content):
        """Add a document to the knowledge base"""
        self.documents.append({
            "filename": filename,
            "content": content
        })
        self._save_documents()

    def _save_documents(self):
        """Save documents to the persist directory"""
        os.makedirs(self.persist_directory, exist_ok=True)
        with open(os.path.join(self.persist_directory, "documents.json"), 'w') as f:
            json.dump(self.documents, f)

    def query(self, query_text, k=3):
        """Simple query implementation - just looks for keyword matches"""
        results = []
        for doc in self.documents:
            if query_text.lower() in doc["content"].lower():
                results.append(doc)
                if len(results) >= k:
                    break
        return results

# Base Agent class
class Agent:
    def __init__(self, name, role, knowledge_base):
        self.name = name
        self.role = role
        self.knowledge_base = knowledge_base

    def process_message(self, message):
        """Process incoming message and generate a response"""
        context = self.get_context(message)

        if not context:
            return f"I'm {self.name}, the {self.role}. I don't have specific information about that. How else can I assist you?"

        # Create a more concise response based on the context
        response = f"I'm {self.name}, the {self.role}. Here's what I know about that:\n\n"

        # Extract relevant information from the context
        for doc_content in context:
            # Add a summary of the document content (first 150 characters)
            summary = doc_content.split('\n\n')[0]  # Get the first paragraph
            if len(summary) > 150:
                summary = summary[:147] + '...'
            response += f"- {summary}\n"

        return response

    def get_context(self, message, k=3):
        """Get relevant context from the knowledge base"""
        docs = self.knowledge_base.query(message, k=k)
        return [doc["content"] for doc in docs]

# Director Agent - Orchestrates other agents
class DirectorAgent(Agent):
    def __init__(self, knowledge_base, agents=None):
        super().__init__("Director", "Executive Director", knowledge_base)
        self.agents = agents or {}

    def add_agent(self, agent_name, agent):
        """Add an agent to the team"""
        self.agents[agent_name] = agent

    def delegate_task(self, message):
        """Delegate a task to the appropriate agent"""
        # Check if the message mentions a specific department
        for agent_name, agent in self.agents.items():
            if agent_name.lower() in message.lower():
                return agent.process_message(message)

        # If the message is about the company in general
        if any(keyword in message.lower() for keyword in ['company', 'mission', 'vision', 'values', 'about']):
            context = self.get_context('company information')
            if context:
                response = f"I'm {self.name}, the {self.role}. Here's information about our company:\n\n"
                # Extract company information
                for doc_content in context:
                    if 'Company Information' in doc_content:
                        # Extract key sections
                        sections = doc_content.split('\n\n')
                        for section in sections:
                            if any(key in section for key in ['Mission', 'Vision', 'Core Values', 'Products']):
                                response += f"{section}\n\n"
                return response

        # If no specific agent or topic matches, handle it at the director level
        return self.process_message(message)

# Specialized agents
class SalesAgent(Agent):
    def __init__(self, knowledge_base):
        super().__init__("Sales", "Sales Director", knowledge_base)

    def process_message(self, message):
        # Override to provide sales-specific responses
        context = self.get_context("sales")

        if not context:
            return f"I'm {self.name}, the {self.role}. I don't have specific information about that. How else can I assist you with sales matters?"

        response = f"I'm {self.name}, the {self.role}. Here's what I can tell you about our sales operations:\n\n"

        # Extract key sales information
        for doc_content in context:
            if "Sales Process" in doc_content:
                response += "Our sales process includes:\n"
                process_section = doc_content.split("Sales Process:")[1].split("\n\n")[0]
                response += process_section + "\n\n"

            if "Key Industries" in doc_content:
                response += "We focus on these key industries:\n"
                industries_section = doc_content.split("Key Industries:")[1].split("\n\n")[0]
                response += industries_section + "\n\n"

        return response

class MarketingAgent(Agent):
    def __init__(self, knowledge_base):
        super().__init__("Marketing", "Marketing Director", knowledge_base)

    def process_message(self, message):
        # Override to provide marketing-specific responses
        context = self.get_context("marketing")

        if not context:
            return f"I'm {self.name}, the {self.role}. I don't have specific information about that. How else can I assist you with marketing matters?"

        response = f"I'm {self.name}, the {self.role}. Here's what I can tell you about our marketing efforts:\n\n"

        # Extract key marketing information
        for doc_content in context:
            if "Marketing Strategies" in doc_content:
                response += "Our marketing strategies include:\n"
                strategies_section = doc_content.split("Marketing Strategies:")[1].split("\n\n")[0]
                response += strategies_section + "\n\n"

            if "Current Marketing Initiatives" in doc_content:
                response += "Our current initiatives:\n"
                initiatives_section = doc_content.split("Current Marketing Initiatives:")[1].split("\n\n")[0]
                response += initiatives_section + "\n\n"

        return response

class FinanceAgent(Agent):
    def __init__(self, knowledge_base):
        super().__init__("Finance", "Finance Director", knowledge_base)

class CustomerServiceAgent(Agent):
    def __init__(self, knowledge_base):
        super().__init__("Support", "Customer Service Manager", knowledge_base)

class TechnicalSupportAgent(Agent):
    def __init__(self, knowledge_base):
        super().__init__("Tech", "Technical Support Manager", knowledge_base)

# Simple CLI interface
def run_cli():
    """Run a simple command-line interface for testing"""
    print("=" * 50)
    print("AI Executive Team - CLI Mode")
    print("=" * 50)
    print("Type 'exit' to quit")
    print()

    # Initialize knowledge base
    brain = SimpleKnowledgeBase()

    # Initialize agents
    sales_agent = SalesAgent(brain)
    marketing_agent = MarketingAgent(brain)
    finance_agent = FinanceAgent(brain)
    customer_service_agent = CustomerServiceAgent(brain)
    technical_support_agent = TechnicalSupportAgent(brain)

    # Initialize director agent and add team members
    director = DirectorAgent(brain)
    director.add_agent("sales", sales_agent)
    director.add_agent("marketing", marketing_agent)
    director.add_agent("finance", finance_agent)
    director.add_agent("customer", customer_service_agent)
    director.add_agent("technical", technical_support_agent)

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break

        # Process the message through the Director Agent
        response = director.delegate_task(user_input)
        print(f"\nAI: {response}")

if __name__ == "__main__":
    run_cli()
