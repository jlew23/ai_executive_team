# AI-Powered Executive Team - Conversational Version
# This version integrates with OpenAI to provide more natural responses

import os
import logging
import json
import openai
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables. LLM functionality will not work.")

# Simple Context Manager for conversation history
class SimpleContextManager:
    def __init__(self, max_tokens=4000, system_message=None):
        self.max_tokens = max_tokens
        self.messages = []
        if system_message:
            self.add("system", system_message)

    def add(self, role, content):
        """Add a message to the context"""
        self.messages.append({"role": role, "content": content})
        # Simple pruning - keep only the last 10 messages (excluding system)
        if len(self.messages) > 11:  # 1 system + 10 conversation messages
            # Keep system messages
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            # Keep only the most recent messages
            other_messages = other_messages[-10:]
            self.messages = system_messages + other_messages

    def get_context(self):
        """Get the current context as a list of messages"""
        return self.messages

    def get_context_string(self):
        """Get the current context as a string"""
        context = ""
        for msg in self.messages:
            if msg["role"] == "system":
                context += f"System: {msg['content']}\n\n"
            elif msg["role"] == "user":
                context += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                context += f"Assistant: {msg['content']}\n\n"
        return context.strip()

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
        """Simple query implementation - looks for keyword matches in the query"""
        # Split the query into words and filter out common words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                      'in', 'on', 'at', 'to', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
                      'during', 'before', 'after', 'above', 'below', 'from', 'up', 'down', 'of', 'off', 'over',
                      'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                      'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
                      'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
                      'just', 'should', 'now', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
                      'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
                      'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                      'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'have', 'has',
                      'had', 'having', 'do', 'does', 'did', 'doing', 'would', 'could', 'should', 'ought',
                      'i', 'im', 'ive', 'tell', 'know', 'need', 'want', 'find', 'get', 'help', 'like', 'please',
                      'think', 'going', 'time', 'year', 'way', 'day', 'thing', 'man', 'world', 'life', 'hand',
                      'part', 'child', 'eye', 'woman', 'place', 'work', 'week', 'case', 'point', 'company',
                      'number', 'group', 'problem', 'fact', 'us', 'our', 'me', 'my', 'mine', 'ours'}

        query_words = [word.lower() for word in query_text.split() if word.lower() not in stop_words]

        # If no meaningful words in query, return empty results
        if not query_words:
            logger.info(f"No meaningful keywords found in query: {query_text}")
            return []

        # Score documents based on keyword matches
        scored_docs = []
        for doc in self.documents:
            score = 0
            doc_content_lower = doc["content"].lower()
            for word in query_words:
                if len(word) > 2 and word in doc_content_lower:  # Only consider words with length > 2
                    score += 1

            if score > 0:
                scored_docs.append((doc, score))

        # Sort by score (descending) and take top k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        results = [doc for doc, score in scored_docs[:k]]

        # Log the query results for debugging
        if results:
            logger.info(f"Found {len(results)} documents matching query keywords: {query_words}")
        else:
            logger.info(f"No documents found matching query keywords: {query_words}")

        return results

# Base Agent class with LLM integration
class Agent:
    def __init__(self, name, role, knowledge_base):
        self.name = name
        self.role = role
        self.knowledge_base = knowledge_base
        self.context_manager = SimpleContextManager(
            max_tokens=4000,
            system_message=f"You are {name}, the {role} of an AI company. Maintain context of the conversation and previous information provided."
        )

    def process_message(self, message):
        """Process incoming message and generate a response using LLM"""
        # Get context from knowledge base
        context = self.get_context(message)

        # Add message to context manager
        self.context_manager.add("user", message)

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
                response = self._generate_fallback_response(context)
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            response = self._generate_fallback_response(context)

        # Add response to context manager
        self.context_manager.add("assistant", response)

        return response

    def _create_prompt_with_context(self, message, context):
        """Create a prompt for the LLM with context from the knowledge base"""
        # Extract content from context documents
        context_text = "\n\n".join([doc["content"] for doc in context])
        logger.info(f"Using context: {context_text[:100]}...")

        # Include conversation history summary if available
        conversation_summary = self.context_manager.get_context_string()

        system_prompt = f"""You are {self.name}, the {self.role} of an AI company.
Previous conversation context:
{conversation_summary}

Relevant company information:
{context_text}

Respond in a helpful, professional manner as if you were actually this executive.
Keep your responses concise and focused on the question.
Maintain awareness of previously provided information.
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
        # Get the conversation history from context manager
        messages = [{"role": "system", "content": system_prompt}]
        context_messages = self.context_manager.get_context()
        # Filter out system messages since we already added our system prompt
        context_messages = [msg for msg in context_messages if msg["role"] != "system"]
        messages.extend(context_messages)

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
        # Define keyword mappings for better agent matching with priority order
        # More specific terms should be checked first
        keyword_mappings = {
            # Technical support keywords - check these first to avoid confusion with general support
            "technical": ["technical support", "tech support", "IT support", "technical help", "tech help",
                         "technical issue", "tech issue", "technical problem", "tech problem",
                         "technical", "tech", "technology", "IT", "system", "software", "hardware", "bug", "computer issue"],

            # Customer service keywords
            "customer": ["customer service", "customer support", "customer assistance", "customer complaint"],

            # Sales keywords
            "sales": ["sales", "sell", "selling", "deal", "purchase", "buying", "customer acquisition"],

            # Marketing keywords
            "marketing": ["marketing", "advertise", "promotion", "brand", "campaign", "market"],

            # Finance keywords
            "finance": ["finance", "financial", "money", "budget", "accounting", "revenue", "profit"]
        }

        # General support terms - only use these if no specific department matches
        general_support_terms = ["support", "help", "assistance", "issue", "problem"]

        # First check for specific department keywords
        for agent_name, keywords in keyword_mappings.items():
            if agent_name in self.agents:
                for keyword in keywords:
                    if keyword.lower() in message.lower():
                        logger.info(f"Delegating to {agent_name} agent based on keyword: {keyword}")
                        return self.agents[agent_name].process_message(message)

        # If no specific department keywords found, check for general support terms
        for term in general_support_terms:
            if term.lower() in message.lower():
                # Default to technical support for general support terms
                if "technical" in self.agents:
                    logger.info(f"Delegating to technical agent based on general support term: {term}")
                    return self.agents["technical"].process_message(message)

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

        # Determine which department is responding
        department = "Director"

        # Define keyword mappings for display names - same as in delegate_task
        keyword_mappings = {
            # Technical support keywords
            "technical": ["technical support", "tech support", "IT support", "technical help", "tech help",
                         "technical issue", "tech issue", "technical problem", "tech problem",
                         "technical", "tech", "technology", "IT", "system", "software", "hardware", "bug", "computer issue"],

            # Customer service keywords
            "customer": ["customer service", "customer support", "customer assistance", "customer complaint"],

            # Sales keywords
            "sales": ["sales", "sell", "selling", "deal", "purchase", "buying", "customer acquisition"],

            # Marketing keywords
            "marketing": ["marketing", "advertise", "promotion", "brand", "campaign", "market"],

            # Finance keywords
            "finance": ["finance", "financial", "money", "budget", "accounting", "revenue", "profit"]
        }

        # General support terms
        general_support_terms = ["support", "help", "assistance", "issue", "problem"]

        # First check for specific department keywords
        found_department = False
        for agent_name, keywords in keyword_mappings.items():
            if agent_name in director.agents:
                for keyword in keywords:
                    if keyword.lower() in user_input.lower():
                        if agent_name == "technical":
                            department = "Tech Support"
                        elif agent_name == "customer":
                            department = "Customer Service"
                        else:
                            department = agent_name.capitalize()
                        found_department = True
                        break
                if found_department:
                    break

        # If no specific department keywords found, check for general support terms
        if not found_department:
            for term in general_support_terms:
                if term.lower() in user_input.lower():
                    # Default to Tech Support for general support terms
                    department = "Tech Support"
                    break

        print(f"\n{department} AI: {response}")

if __name__ == "__main__":
    run_cli()



