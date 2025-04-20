# AI-Powered Executive Team - Conversational Version
# This version integrates with OpenAI to provide more natural responses

import os
import logging
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables. LLM functionality will not work.")

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

# Base Agent class with LLM integration
class Agent:
    def __init__(self, name, role, knowledge_base):
        self.name = name
        self.role = role
        self.knowledge_base = knowledge_base
        self.conversation_history = []
        
    def process_message(self, message):
        """Process incoming message and generate a response using LLM"""
        # Get context from knowledge base
        context = self.get_context(message)
        
        # Add message to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Prepare prompt for LLM
        if not context:
            prompt = self._create_prompt_without_context(message)
        else:
            prompt = self._create_prompt_with_context(message, context)
        
        # Generate response using LLM
        try:
            if openai.api_key:
                response = self._generate_llm_response(prompt)
            else:
                # Fallback if no API key
                response = self._generate_fallback_response(context)
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            response = self._generate_fallback_response(context)
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def _create_prompt_with_context(self, message, context):
        """Create a prompt for the LLM with context from the knowledge base"""
        context_text = "\n\n".join([doc["content"] for doc in context])
        
        system_prompt = f"""You are {self.name}, the {self.role} of an AI company. 
You have access to the following company information that you can use to answer questions:

{context_text}

Respond in a helpful, professional manner as if you were actually this executive. 
Keep your responses concise and focused on the question.
Don't mention that you're an AI or that you're using provided information."""
        
        return system_prompt
    
    def _create_prompt_without_context(self, message):
        """Create a prompt for the LLM without context"""
        system_prompt = f"""You are {self.name}, the {self.role} of an AI company.
You don't have specific information about the topic asked, but you should respond as this executive would.
Be professional, concise, and suggest what information you would need to better answer the question.
Don't mention that you're an AI or that you lack information."""
        
        return system_prompt
    
    def _generate_llm_response(self, system_prompt):
        """Generate a response using OpenAI's API"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (up to last 5 exchanges)
        for item in self.conversation_history[-10:]:
            messages.append(item)
            
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _generate_fallback_response(self, context):
        """Generate a fallback response when LLM is not available"""
        if not context:
            return f"I'm {self.name}, the {self.role}. I don't have specific information about that. How else can I assist you?"
        
        # Create a more concise response based on the context
        response = f"I'm {self.name}, the {self.role}. Here's what I know about that:\n\n"
        
        # Extract relevant information from the context
        for doc in context:
            # Add a summary of the document content (first 150 characters)
            summary = doc["content"].split('\n\n')[0]  # Get the first paragraph
            if len(summary) > 150:
                summary = summary[:147] + '...'
            response += f"- {summary}\n"
        
        return response
    
    def get_context(self, message, k=3):
        """Get relevant context from the knowledge base"""
        docs = self.knowledge_base.query(message, k=k)
        return docs

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
        
        # If no specific agent matches, handle it at the director level
        return self.process_message(message)

# Specialized agents
class SalesAgent(Agent):
    def __init__(self, knowledge_base):
        super().__init__("Sales", "Sales Director", knowledge_base)

class MarketingAgent(Agent):
    def __init__(self, knowledge_base):
        super().__init__("Marketing", "Marketing Director", knowledge_base)

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
    print("AI Executive Team - Conversational Mode")
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
