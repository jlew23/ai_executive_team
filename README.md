# AI-Powered Executive Team

This project implements an AI-powered executive team that can assist a CEO in running their company. The system consists of AI agents with different roles (Sales, Marketing, Finance, Customer Service, Technical Support) that communicate via Slack and have access to a shared knowledge base.

## Project Structure

- `main.py`: Main application entry point
- `agents/`: Contains the specialized agent implementations
- `brain_data/`: Vector database storage for the knowledge base
- `data/`: Company documents and other data sources
- `config/`: Configuration files
- `logs/`: Log files
- `rasa/`: Rasa NLU configuration and training data

## Setup Instructions

### Quick Start Options

#### Simplified Version (No Dependencies)

If you want to quickly test the application without installing any dependencies:

1. Clone this repository
2. Run the simplified version: `python simple_main.py`

This version doesn't require external dependencies and provides a simple CLI interface.

#### Conversational Version (OpenAI Integration)

For a more natural, conversational experience using OpenAI's language models:

1. Clone this repository
2. Install the OpenAI package: `pip install openai python-dotenv`
3. Create a `.env` file with your OpenAI API key (see `.env.example`)
4. Run the conversational version: `python conversational_main.py`

This version provides much more natural and detailed responses by leveraging OpenAI's language models.

### Full Setup

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Upgrade pip and install setuptools: `pip install --upgrade pip setuptools wheel`
5. Install dependencies: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and fill in your credentials
7. Set up the knowledge base by adding documents to the `data/` directory
8. Run the application: `python main.py`

### Troubleshooting Installation

If you encounter issues with the installation:

1. Make sure you have Python 3.8+ installed
2. If you get errors about missing build dependencies, install the development tools:
   - Ubuntu/Debian: `sudo apt-get install python3-dev build-essential`
   - CentOS/RHEL: `sudo yum install python3-devel gcc`
   - macOS: `xcode-select --install`
   - Windows: Install Visual C++ Build Tools

3. For issues with specific packages:
   - If Rasa installation fails, you can use the simplified version: `python simple_main.py`
   - Some packages may require specific versions of numpy or other dependencies

### Alternative Setup with Docker

You can also use Docker to run the application:

```bash
docker-compose up -d
```

This will start both the main application and the Rasa NLU service.

## Agent Types

- **Director Agent**: Orchestrates the team and delegates tasks
- **Sales Agent**: Handles sales-related queries and tasks
- **Marketing Agent**: Manages marketing campaigns and content
- **Finance Agent**: Deals with financial matters and reporting
- **Customer Service Agent**: Provides customer support
- **Technical Support Agent**: Offers technical assistance

## Knowledge Base ("Brain")

The knowledge base stores company documents, procedures, and best practices. It uses vector embeddings to enable semantic search and retrieval of relevant information.

### Enhanced Knowledge Base Features

- **Multiple Document Types**: Support for TXT, PDF, DOCX, and CSV files
- **Direct Text Input**: Add text directly to the knowledge base
- **Web Scraping**: Extract content from websites
- **Hybrid Search**: Combine semantic and keyword search with adjustable weights
- **Web Interface**: User-friendly interface for managing and searching the knowledge base
- **API Access**: RESTful API for programmatic access

### Running the Knowledge Base API

```bash
python run_api.py
```

Then open your browser to http://localhost:5000 to access the web interface.

## Technology Stack

### Full Version
- Slack API: For communication with users
- Rasa (v1.10.2): For natural language understanding
- ChromaDB: For vector storage and retrieval
- SentenceTransformers: For document embeddings
- LangChain: For agent framework and utilities
- FastAPI: For the knowledge base API
- BeautifulSoup4: For web scraping
- PyPDF2 & python-docx: For document parsing

### Conversational Version
- OpenAI API: For natural language generation
- Python-dotenv: For environment variable management
- Simple CLI interface for testing
- Context-aware responses using company knowledge base

### Simplified Version
- Pure Python implementation with no external dependencies
- Simple CLI interface for testing
- Basic text-based knowledge retrieval
