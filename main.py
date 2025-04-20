# AI-Powered Executive Team
# Main project structure and components

import logging
from llm import LocalProvider
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader, TextLoader

# Import agent modules
from agents import (
    DirectorAgent,
    SalesAgent,
    MarketingAgent,
    FinanceAgent,
    CustomerServiceAgent,
    TechnicalSupportAgent
)

# Import configuration
from config.app_config import (
    APP_NAME, APP_VERSION, APP_PORT,
    LOG_LEVEL, LOG_FORMAT,
    BRAIN_DATA_DIR, DOCUMENT_DIR, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP,
    SLACK_BOT_TOKEN, SLACK_APP_TOKEN,
    RASA_URL
)

# Note: activepieces-sdk is not available and has been removed from requirements

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Initialize Slack app
slack_app = App(token=SLACK_BOT_TOKEN)

# Initialize ChromaDB for the knowledge base (Brain)
class KnowledgeBase:
    def __init__(self, persist_directory=BRAIN_DATA_DIR):
        self.embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
        self.persist_directory = persist_directory
        self.vector_db = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )

    def add_documents(self, documents_path):
        """Add documents to the knowledge base from a directory"""
        loader = DirectoryLoader(documents_path, glob="**/*.txt", loader_cls=TextLoader)
        documents = loader.load()

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        splits = text_splitter.split_documents(documents)

        # Add to vector store
        self.vector_db.add_documents(splits)
        self.vector_db.persist()
        logger.info(f"Added {len(splits)} document chunks to the knowledge base")

    def query(self, query, k=5):
        """Query the knowledge base for relevant information"""
        results = self.vector_db.similarity_search(query, k=k)
        return results

# Initialize the local LLM provider
llm_provider = LocalProvider(
    model="Llama-3-WhiteRabbitNeo-8B-v2.0.Q4_K_M.gguf",  # or any other local model you have
    model_path="C:/Users/Luda/.lmstudio/models/Llama-3-WhiteRabbitNeo-8B-v2.0.Q4_K_M/Llama-3-WhiteRabbitNeo-8B-v2.0.Q4_K_M.gguf",  # specify your model path
    n_gpu_layers=-1  # use GPU acceleration if available
)

# Slack event handlers
@slack_app.event("app_mention")
def handle_mention(event, say):
    """Handle mentions in Slack"""
    message = event["text"]
    user = event["user"]
    channel = event["channel"]

    # This is where you would route the message to the Director Agent
    # For now, we'll just acknowledge it
    say(f"Hello <@{user}>! I received your message and I'm processing it.")

@slack_app.event("message")
def handle_message(event, say):
    """Handle direct messages in Slack"""
    if "channel_type" in event and event["channel_type"] == "im":
        message = event["text"]
        user = event["user"]

        # Process the message through the Director Agent
        # For now, we'll just acknowledge it
        say(f"Hello <@{user}>! I received your direct message and I'm processing it.")

# Main application
def main():
    # Initialize knowledge base
    brain = KnowledgeBase()

    # Add documents from the data directory
    try:
        brain.add_documents(DOCUMENT_DIR)
        logger.info(f"Added documents from {DOCUMENT_DIR}")
    except Exception as e:
        logger.error(f"Error adding documents: {e}")

    # Initialize agents
    sales_agent = SalesAgent(brain, llm_provider=llm_provider)
    marketing_agent = MarketingAgent(brain, llm_provider=llm_provider)
    finance_agent = FinanceAgent(brain, llm_provider=llm_provider)
    customer_service_agent = CustomerServiceAgent(brain, llm_provider=llm_provider)
    technical_support_agent = TechnicalSupportAgent(brain, llm_provider=llm_provider)

    # Initialize director agent and add team members
    director = DirectorAgent(brain, llm_provider=llm_provider)
    director.add_agent("sales", sales_agent)
    director.add_agent("marketing", marketing_agent)
    director.add_agent("finance", finance_agent)
    director.add_agent("customer", customer_service_agent)
    director.add_agent("technical", technical_support_agent)

    # Start Slack app
    SocketModeHandler(slack_app, SLACK_APP_TOKEN).start()

if __name__ == "__main__":
    main()

