"""
Run the web dashboard.
"""

import os
import sys
import logging
import glob
import json
import uuid
import tempfile
import requests
import re
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Blueprint, send_from_directory
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_AVAILABLE = False

# Get LM Studio API URL from environment or use default
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
LM_STUDIO_MODELS_DIR = os.getenv("LOCAL_MODEL_PATH", "c:\\Users\\Luda\\.lmstudio\\models")
LOCAL_MODEL_AVAILABLE = False

# Import knowledge base modules
try:
    from knowledge_base import VectorKnowledgeBase, DocumentProcessor, Document
    from supabase_config import get_supabase_client
    KB_AVAILABLE = True
    
    # Initialize the Supabase client and knowledge base
    try:
        supabase_client = get_supabase_client()
        kb = VectorKnowledgeBase(name="ai_kb")
        logger.info("Successfully initialized Supabase client and knowledge base")
    except Exception as e:
        logger.error(f"Error initializing Supabase client or knowledge base: {e}")
        KB_AVAILABLE = False
except ImportError as e:
    logger.warning(f"Knowledge base modules not available. Using mock implementation. Error: {e}")
    KB_AVAILABLE = False

# Import agent communication modules
try:
    from agent_communication import DelegationSystem, MessageBus, TaskManager
    DELEGATION_AVAILABLE = True
except ImportError:
    logger.warning("Agent communication modules not available. Delegation features will be disabled.")
    DELEGATION_AVAILABLE = False

# Import AI integrations
try:
    from ai_integrations.openai_integration import OpenAIIntegration
    from ai_integrations.local_model_integration import LocalModelIntegration

    # Initialize OpenAI integration if API key is available
    if OPENAI_API_KEY:
        openai_integration = OpenAIIntegration(OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
        logger.info("OpenAI integration initialized")
    else:
        logger.warning("OpenAI API key not found. OpenAI integration not available.")

    # Initialize local model integration
    try:
        # Force using 127.0.0.1 instead of localhost
        local_model_integration = LocalModelIntegration("http://127.0.0.1:1234/v1")
        # Test connection to local model
        local_models = local_model_integration.list_available_models()
        if local_models:
            LOCAL_MODEL_AVAILABLE = True
            logger.info(f"Local model integration initialized. Available models: {local_models}")
        else:
            logger.warning("No local models found. Local model integration not available.")
    except Exception as e:
        logger.warning(f"Error initializing local model integration: {e}")

except ImportError as e:
    logger.warning(f"AI integrations not available: {e}")

# Initialize knowledge base directory
KB_DIR = os.getenv("KB_DIR", os.path.join(os.getcwd(), 'kb_data'))
os.makedirs(KB_DIR, exist_ok=True)

# Initialize knowledge base
if KB_AVAILABLE:
    try:
        # Initialize Supabase knowledge base
        kb = VectorKnowledgeBase(name="ai_executive_team_kb", persist_directory=KB_DIR)
        logger.info("Supabase knowledge base initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase knowledge base: {e}")
        KB_AVAILABLE = False

# Get LM Studio API URL from environment or use default
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
LM_STUDIO_MODELS_DIR = os.getenv("LM_STUDIO_MODELS_DIR", "c:\\Users\\Luda\\.lmstudio\\models")
# LOCAL_MODEL_AVAILABLE is set earlier in the code

# Create Flask app
app = Flask(__name__,
            template_folder=os.path.join('web_dashboard', 'templates'),
            static_folder=os.path.join('web_dashboard', 'static'))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

# Configure upload settings
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", os.path.join(os.getcwd(), 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'docx', 'csv', 'json', 'md'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize document processor if available
if KB_AVAILABLE:
    try:
        # Initialize document processor
        document_processor = DocumentProcessor()
        logging.info(f"Document processor initialized")
    except Exception as e:
        logging.error(f"Failed to initialize document processor: {e}")
        KB_AVAILABLE = False

# Create blueprints
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')
agents_bp = Blueprint('agents', __name__, url_prefix='/agents')
kb_bp = Blueprint('kb', __name__, url_prefix='/kb')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Sample data
agent_statuses = [
    {"agent_id": 1, "agent_name": "CEO", "status": "active", "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"agent_id": 2, "agent_name": "CTO", "status": "active", "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"agent_id": 3, "agent_name": "CFO", "status": "inactive", "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"agent_id": 4, "agent_name": "CMO", "status": "active", "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"agent_id": 5, "agent_name": "COO", "status": "active", "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
]

recent_conversations = [
    {"conversation_id": 1, "user_id": "user1", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"conversation_id": 2, "user_id": "user2", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"conversation_id": 3, "user_id": "user3", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
]

# File path for persisting knowledge base documents
KB_STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kb_documents.json')

# Load knowledge base documents from file or use defaults
def load_kb_documents():
    try:
        if os.path.exists(KB_STORAGE_FILE):
            with open(KB_STORAGE_FILE, 'r') as f:
                documents = json.load(f)
                logger.info(f"Loaded {len(documents)} documents from {KB_STORAGE_FILE}")
                return documents
        else:
            # Default knowledge base documents
            default_docs = [
                {
                    "doc_id": 1,
                    "name": "company_info.txt",
                    "type": "Company Information",
                    "uploaded": "2025-04-12 14:30:00",
                    "size": "2.5 KB",
                    "content": """# AI Executive Team Company Information

AI Executive Team is a cutting-edge artificial intelligence company specializing in creating autonomous AI agents that can function as executive team members for businesses of all sizes.

## Mission
To revolutionize business management by providing AI executives that can make data-driven decisions, automate routine tasks, and provide strategic insights 24/7.

## Vision
A future where every company has access to world-class executive talent through our AI agents, democratizing access to high-quality business leadership.

## Core Values
- Innovation: Pushing the boundaries of what AI can do in business contexts
- Reliability: Creating agents that can be trusted with critical business decisions
- Transparency: Ensuring all AI decisions are explainable and auditable
- Security: Maintaining the highest standards of data protection and privacy
- Collaboration: Our AI agents work alongside human teams, not replace them

## Company History
Founded in 2023, AI Executive Team began as a research project at a leading university. After demonstrating remarkable results in simulated business environments, the company secured venture funding and launched its first commercial product in 2024.

## Products and Services
- CEO Agent: Strategic planning, resource allocation, and high-level decision making
- CTO Agent: Technology strategy, development oversight, and technical decision making
- CFO Agent: Financial planning, analysis, forecasting, and reporting
- CMO Agent: Marketing strategy, campaign optimization, and brand management
- COO Agent: Operations management, process optimization, and execution oversight
"""
                },
                {
                    "doc_id": 2,
                    "name": "product_catalog.pdf",
                    "type": "Product Information",
                    "uploaded": "2025-04-11 10:15:00",
                    "size": "1.2 MB",
                    "content": """# AI Executive Team Product Catalog

## CEO Agent
The CEO Agent is designed to provide strategic leadership and decision-making support for your organization.

### Features:
- Strategic planning and goal setting
- Resource allocation optimization
- Performance monitoring and analysis
- Stakeholder communication management
- Crisis response planning

### Technical Specifications:
- Base Model: Claude-3 Opus
- Context Window: 100,000 tokens
- Response Time: <2 seconds for most queries
- Integration: Slack, Teams, Email, and custom APIs

### Pricing:
- Standard: $2,500/month
- Enterprise: $5,000/month with custom training

## CTO Agent
The CTO Agent provides technical leadership and oversees technology strategy and implementation.

### Features:
- Technology stack evaluation and recommendations
- Development process optimization
- Technical debt assessment and management
- Security posture analysis
- Innovation opportunity identification

### Technical Specifications:
- Base Model: GPT-4
- Context Window: 80,000 tokens
- Response Time: <1.5 seconds for most queries
- Integration: GitHub, Jira, Slack, and custom APIs

### Pricing:
- Standard: $2,200/month
- Enterprise: $4,500/month with custom training
"""
                },
                {
                    "doc_id": 3,
                    "name": "financial_report_q1.xlsx",
                    "type": "Financial Information",
                    "uploaded": "2025-04-10 16:45:00",
                    "size": "450 KB",
                    "content": """# AI Executive Team Financial Report - Q1 2025

## Executive Summary
In Q1 2025, AI Executive Team achieved significant financial milestones, with revenue growth of 32% year-over-year and improved profit margins. The company remains well-positioned for continued expansion in the AI executive services market.

## Revenue Highlights
- Total Revenue: $12.5M (↑32% YoY)
- Recurring Revenue: $10.2M (82% of total)
- New Customer Revenue: $2.3M
- Average Contract Value: $125,000 (↑15% YoY)

## Expense Summary
- R&D: $3.2M (25.6% of revenue)
- Sales & Marketing: $2.8M (22.4% of revenue)
- G&A: $1.5M (12% of revenue)
- Infrastructure & Operations: $2.1M (16.8% of revenue)

## Profitability
- Gross Margin: 78%
- Operating Margin: 23.2%
- Net Income: $2.5M (20% of revenue)

## Cash Position
- Cash & Equivalents: $18.5M
- Burn Rate: Positive cash flow of $1.2M/month
- Runway: Not applicable (cash flow positive)

## Customer Metrics
- Total Customers: 105 (↑25% YoY)
- Customer Acquisition Cost: $45,000
- Customer Lifetime Value: $375,000
- Net Revenue Retention: 118%

## Q2 2025 Outlook
- Projected Revenue: $14.8M - $15.5M
- Projected Operating Margin: 24-26%
- Key Investment Areas: Enterprise sales team expansion, new agent development
"""
                }
            ]
            # Save default documents to file
            save_kb_documents(default_docs)
            logger.info(f"Created default knowledge base with {len(default_docs)} documents")
            return default_docs
    except Exception as e:
        logger.error(f"Error loading knowledge base documents: {e}")
        return []

# Save knowledge base documents to file
def save_kb_documents(documents):
    try:
        with open(KB_STORAGE_FILE, 'w') as f:
            json.dump(documents, f, indent=2)
        logger.info(f"Knowledge base documents saved to {KB_STORAGE_FILE}")
    except Exception as e:
        logger.error(f"Error saving knowledge base documents: {e}")

# Initialize knowledge base documents
kb_documents = load_kb_documents()

# Create MockKnowledgeBase class
class MockKnowledgeBase:
    def search(self, query, limit=5, **kwargs):
        results = []
        # First try exact match
        for doc in kb_documents:
            if query.lower() in doc["content"].lower():
                results.append({
                    "id": doc["doc_id"],
                    "text": doc["content"],
                    "metadata": {
                        "source_name": doc["name"],
                        "type": doc["type"]
                    },
                    "score": 0.95  # Mock score
                })
                if len(results) >= limit:
                    break

        # If no results, try keyword matching
        if not results:
            keywords = [k for k in query.lower().split() if len(k) > 3]  # Only use keywords with length > 3
            for doc in kb_documents:
                content_lower = doc["content"].lower()
                if any(keyword in content_lower for keyword in keywords):
                    results.append({
                        "id": doc["doc_id"],
                        "text": doc["content"],
                        "metadata": {
                            "source_name": doc["name"],
                            "type": doc["type"]
                        },
                        "score": 0.8  # Lower score for keyword match
                    })
                    if len(results) >= limit:
                        break

        # If still no results, return all documents (limited by limit)
        if not results and query.lower() in ['q1', 'quarter', 'financial', 'earnings', 'revenue', 'profit']:
            for doc in kb_documents:
                if doc["type"] == "Financial Information":
                    results.append({
                        "id": doc["doc_id"],
                        "text": doc["content"],
                        "metadata": {
                            "source_name": doc["name"],
                            "type": doc["type"]
                        },
                        "score": 0.7  # Even lower score for type match
                    })
                    if len(results) >= limit:
                        break
        return results

# Dashboard routes
@dashboard_bp.route('/')
def index():
    """Dashboard index page."""
    return render_template('dashboard/index.html',
                          total_conversations=len(recent_conversations),
                          total_messages=25,
                          active_agents=4,
                          agent_statuses=agent_statuses,
                          recent_conversations=recent_conversations,
                          now=datetime.now())

# Agent routes
@agents_bp.route('/')
def index():
    """Agents page."""
    return render_template('agents/index.html', agents=agent_statuses, now=datetime.now())

# Function to get local models
def get_local_models():
    """Get list of local models from LM Studio directory."""
    models_dir = os.path.expanduser(r"c:\Users\Luda\.lmstudio\models")
    models = []

    # Check if directory exists
    if os.path.exists(models_dir) and os.path.isdir(models_dir):
        # Look for model files or directories
        model_paths = glob.glob(os.path.join(models_dir, "**"), recursive=True)

        # Filter to only include directories that likely contain models
        for path in model_paths:
            if os.path.isdir(path):
                # Get the model name from the path
                model_name = os.path.basename(path)
                if model_name != "" and not model_name.startswith("."):
                    models.append({
                        "name": model_name,
                        "path": path
                    })

    # Add some default cloud models
    cloud_models = [
        {"name": "gpt-3.5-turbo", "path": "cloud"},
        {"name": "gpt-4", "path": "cloud"},
        {"name": "claude-3-opus", "path": "cloud"},
        {"name": "claude-3-sonnet", "path": "cloud"}
    ]

    # Combine local and cloud models
    all_models = cloud_models + models
    return all_models

@agents_bp.route('/<int:agent_id>')
def detail(agent_id):
    """Agent detail page."""
    agent = next((a for a in agent_statuses if a["agent_id"] == agent_id), None)
    if not agent:
        flash("Agent not found", "danger")
        return redirect(url_for('agents.index'))

    # Get available models
    available_models = get_local_models()

    return render_template('agents/detail.html',
                          agent=agent,
                          now=datetime.now(),
                          available_models=available_models)

@agents_bp.route('/api/update-status', methods=['POST'])
def update_status():
    """Update agent status API endpoint."""
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        status = data.get('status')

        if not agent_id or not status:
            return jsonify({
                "error": "Agent ID and status are required",
                "status": "error"
            }), 400

        # Convert agent_id to int if it's a string
        agent_id = int(agent_id) if isinstance(agent_id, str) and agent_id.isdigit() else agent_id

        # Validate status
        if status not in ['active', 'inactive', 'error']:
            return jsonify({
                "error": "Invalid status. Must be 'active', 'inactive', or 'error'",
                "status": "error"
            }), 400

        # Find the agent and update status
        agent = next((a for a in agent_statuses if a["agent_id"] == agent_id), None)
        if not agent:
            return jsonify({
                "error": f"Agent with ID {agent_id} not found",
                "status": "error"
            }), 404

        # Update the agent status
        agent["status"] = status
        agent["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "agent_id": agent_id,
            "status": status,
            "last_active": agent["last_active"],
            "message": f"Agent {agent['agent_name']} status updated to {status}",
            "status_code": "success"
        })
    except Exception as e:
        logger.error(f"Error updating agent status: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Knowledge base API endpoints
@app.route('/api/knowledgebase/search', methods=['GET', 'POST'])
def kb_search_api():
    """Search the knowledge base API endpoint."""
    try:
        # Get query parameters
        if request.method == 'POST':
            data = request.get_json()
            query = data.get('query', '')
            max_results = min(int(data.get('max_results', 4)), 10)  # Default 4, max 10
            search_fuzziness = min(max(int(data.get('search_fuzziness', 100)), 0), 100)  # 0-100 scale
        else:  # GET
            query = request.args.get('query', '')
            max_results = min(int(request.args.get('max_results', 4)), 10)
            search_fuzziness = min(max(int(request.args.get('search_fuzziness', 100)), 0), 100)

        if not query:
            return jsonify({
                "error": "Query parameter is required",
                "status": "error"
            }), 400

        # Perform search
        if KB_AVAILABLE:
            # Use vector store for search
            semantic_weight = search_fuzziness / 100.0
            keyword_weight = 1.0 - semantic_weight

            results = kb.search(
                query=query,
                limit=max_results,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "doc_id": result.get("id"),
                    "content": result.get("text", ""),
                    "source": result.get("metadata", {}).get("source_name", "Unknown"),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })

            return jsonify({
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results),
                "status": "success"
            })
        else:
            # Mock search implementation
            results = []
            for doc in kb_documents:
                if query.lower() in doc["content"].lower():
                    results.append({
                        "doc_id": doc["doc_id"],
                        "content": doc["content"][:200] + "...",  # Truncate for preview
                        "source": doc["name"],
                        "score": 0.95,  # Mock score
                        "metadata": {
                            "type": doc["type"],
                            "uploaded": doc["uploaded"]
                        }
                    })
                    if len(results) >= max_results:
                        break

            return jsonify({
                "query": query,
                "results": results,
                "count": len(results),
                "status": "success",
                "note": "Using mock search (KB not available)"
            })
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/knowledgebase/sources/list', methods=['GET'])
def kb_sources_list_api():
    """List knowledge base sources API endpoint."""
    try:
        if KB_AVAILABLE:
            # Get sources from KB
            sources = []
            for doc_id, doc_info in kb.documents.items():
                # Get file size in a human-readable format
                size = doc_info.get("metadata", {}).get("size", 0)
                if isinstance(size, (int, float)):
                    # Convert bytes to KB, MB, etc.
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
                else:
                    size_str = str(size)
                
                # Get file type, defaulting to extension if available
                file_type = doc_info.get("metadata", {}).get("file_type", "Unknown")
                if file_type == "Unknown":
                    source_name = doc_info.get("source_name", "")
                    if source_name and "." in source_name:
                        ext = source_name.split(".")[-1].upper()
                        file_type = f"{ext} Document"
                
                sources.append({
                    "id": doc_id,
                    "name": doc_info.get("source_name", "Unknown"),
                    "type": file_type,
                    "uploaded": doc_info.get("metadata", {}).get("uploaded_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "size": size_str
                })

            return jsonify({
                "sources": sources,
                "count": len(sources),
                "status": "success"
            })
        else:
            # Mock sources
            sources = []
            for doc in kb_documents:
                sources.append({
                    "id": doc["doc_id"],
                    "name": doc["name"],
                    "type": doc["type"],
                    "uploaded": doc["uploaded"],
                    "size": doc["size"]
                })

            return jsonify({
                "sources": sources,
                "count": len(sources),
                "status": "success",
                "note": "Using mock sources (KB not available)"
            })
    except Exception as e:
        logger.error(f"List sources error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/knowledgebase/sources/delete', methods=['POST'])
def kb_sources_delete_api():
    """Delete knowledge base source API endpoint."""
    try:
        logger.info("Delete API endpoint called")
        data = request.get_json()
        logger.info(f"Delete request data: {data}")
        doc_id = data.get('id')
        logger.info(f"Attempting to delete document with ID: {doc_id}")

        if not doc_id:
            logger.error("No document ID provided in delete request")
            return jsonify({
                "error": "Source ID is required",
                "status": "error"
            }), 400

        if KB_AVAILABLE:
            # Delete from KB
            try:
                # Try to delete the document directly
                logger.info(f"Calling KB delete_document with ID: {doc_id}")
                success = kb.delete_document(doc_id)
                logger.info(f"Delete result: {success}")

                if success:
                    logger.info(f"Document {doc_id} deleted successfully")
                    return jsonify({
                        "id": doc_id,
                        "status": "success",
                        "message": f"Source {doc_id} deleted successfully"
                    })
                else:
                    logger.warning(f"Document {doc_id} not found or could not be deleted")
                    return jsonify({
                        "error": f"Source {doc_id} not found or could not be deleted",
                        "status": "error"
                    }), 404
            except Exception as e:
                logger.error(f"Error deleting document {doc_id}: {e}")
                return jsonify({
                    "error": f"Error deleting document: {str(e)}",
                    "status": "error"
                }), 500
        else:
            # Mock delete
            logger.info(f"Mock delete for document {doc_id}")
            global kb_documents
            doc_id = int(doc_id) if isinstance(doc_id, str) and doc_id.isdigit() else doc_id
            kb_documents = [doc for doc in kb_documents if doc["doc_id"] != doc_id]
            logger.info(f"Document {doc_id} deleted from mock KB")

            return jsonify({
                "id": doc_id,
                "status": "success",
                "message": f"Source {doc_id} deleted successfully (mock mode)"
            })
    except Exception as e:
        logger.error(f"Delete source error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

# The route for the delete API endpoint matches the JavaScript code in templates/kb/index.html

# Knowledge base routes
@kb_bp.route('/')
def index():
    """Knowledge base page."""
    # If KB is available, get documents from the KB
    if KB_AVAILABLE:
        try:
            # Get documents from Supabase KB
            documents_list = kb.list_documents()

            # Format documents for display
            documents = []
            for doc_info in documents_list:
                # Use id as doc_id if doc_id is not available
                doc_id = doc_info.get("doc_id") or doc_info.get("id")

                # Skip documents with no ID
                if not doc_id:
                    logger.warning(f"Skipping document with no ID: {doc_info}")
                    continue

                # Update doc_id in doc_info
                doc_info["doc_id"] = doc_id

                documents.append({
                    "doc_id": doc_info.get("doc_id"),
                    "name": doc_info.get("name", "Unknown"),
                    "type": doc_info.get("type", "Unknown"),
                    "uploaded": doc_info.get("uploaded_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "size": doc_info.get("size", "Unknown")
                })

            logger.info(f"Retrieved {len(documents)} documents from Supabase KB")
            for doc in documents:
                logger.info(f"Document: {doc['name']} (ID: {doc['doc_id']})")

            return render_template('kb/index.html', documents=documents, now=datetime.now())
        except Exception as e:
            logger.error(f"Error retrieving documents from KB: {e}")
            # Fall back to sample documents
            return render_template('kb/index.html', documents=kb_documents, now=datetime.now())
    else:
        # Use sample documents if KB is not available
        return render_template('kb/index.html', documents=kb_documents, now=datetime.now())

@kb_bp.route('/upload', methods=['GET', 'POST'])
def upload_document():
    """Upload a document to the knowledge base."""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']

        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Process the file
            try:
                if KB_AVAILABLE:
                    # Save file to temporary location
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, secure_filename(file.filename))
                    file.save(temp_path)

                    # Process the document
                    doc = document_processor.process_file(temp_path)

                    # Add metadata
                    doc.metadata["uploaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    doc.metadata["size"] = f"{os.path.getsize(temp_path) / 1024:.1f} KB"

                    # Add to knowledge base
                    kb.add_document(doc)

                    # Clean up temporary file
                    os.remove(temp_path)
                    os.rmdir(temp_dir)

                    flash(f'Document {file.filename} uploaded and processed successfully', 'success')
                else:
                    # Save file if KB is not available
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    # Create a mock document entry with proper metadata
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    file_extension = filename.rsplit('.', 1)[1].upper() if '.' in filename else 'UNKNOWN'
                    
                    new_doc = {
                        "doc_id": str(uuid.uuid4()),  # Use UUID for unique document IDs
                        "name": filename,
                        "type": file_extension,
                        "uploaded": current_time,
                        "size": f"{os.path.getsize(file_path) / 1024:.1f} KB",
                        "content": "Content not available in mock mode"
                    }
                    kb_documents.append(new_doc)

                    # Save changes to the file
                    save_kb_documents(kb_documents)

                    flash(f'Document {filename} uploaded successfully (mock mode)', 'success')
            except Exception as e:
                logger.error(f"Error processing document: {e}")
                flash(f'Error processing document: {str(e)}', 'danger')

            return redirect(url_for('kb.index'))
        else:
            flash(f'File type not allowed. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}', 'danger')
            return redirect(request.url)

    return render_template('kb/upload.html', now=datetime.now())

@kb_bp.route('/add-text', methods=['GET', 'POST'])
def add_text():
    """Add text directly to the knowledge base."""
    if request.method == 'POST':
        title = request.form.get('title')
        text_content = request.form.get('content')
        doc_type = request.form.get('type')

        if not title or not text_content:
            flash('Title and content are required', 'danger')
            return redirect(request.url)

        try:
            if KB_AVAILABLE:
                # Process the text
                doc = document_processor.process_text(text_content, source_name=title)

                # Add metadata
                doc.metadata["uploaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                doc.metadata["size"] = f"{len(text_content) / 1024:.1f} KB"
                doc.metadata["file_type"] = doc_type

                # Add to knowledge base
                kb.add_document(doc)

                flash(f'Text "{title}" added to knowledge base successfully', 'success')
            else:
                # Create a mock document entry with proper metadata
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                new_doc = {
                    "doc_id": str(uuid.uuid4()),  # Use UUID for unique document IDs
                    "name": title,
                    "type": doc_type,
                    "uploaded": current_time,
                    "size": f"{len(text_content) / 1024:.1f} KB",
                    "content": text_content
                }
                kb_documents.append(new_doc)

                # Save changes to the file
                save_kb_documents(kb_documents)

                flash(f'Text "{title}" added successfully (mock mode)', 'success')
        except Exception as e:
            logger.error(f"Error adding text: {e}")
            flash(f'Error adding text: {str(e)}', 'danger')

        return redirect(url_for('kb.index'))

    return render_template('kb/add_text.html', now=datetime.now())

@kb_bp.route('/add-url', methods=['GET', 'POST'])
def add_url():
    """Add content from a URL to the knowledge base."""
    if request.method == 'POST':
        url = request.form.get('url')

        if not url:
            flash('URL is required', 'danger')
            return redirect(request.url)

        try:
            if KB_AVAILABLE:
                # Process the URL
                doc = document_processor.process_url(url)

                # Add to knowledge base
                kb.add_document(doc)

                flash(f'Content from {url} added to knowledge base successfully', 'success')
            else:
                # Create a mock document entry with proper metadata
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Create mock content for URL
                mock_content = f"Content from {url} (not available in mock mode)"
                title = url.split('//')[1] if '//' in url else url
                title = title.split('/')[0]  # Use domain as title
                
                new_doc = {
                    "doc_id": str(uuid.uuid4()),  # Use UUID for unique document IDs
                    "name": title,
                    "type": "URL",
                    "uploaded": current_time,
                    "size": f"{len(mock_content) / 1024:.1f} KB",
                    "content": mock_content,
                    "url": url
                }
                kb_documents.append(new_doc)

                # Save changes to the file
                save_kb_documents(kb_documents)

                flash(f'URL {url} added successfully (mock mode)', 'success')
        except Exception as e:
            logger.error(f"Error processing URL: {e}")
            flash(f'Error processing URL: {str(e)}', 'danger')

        return redirect(url_for('kb.index'))

    return render_template('kb/add_url.html', now=datetime.now())

@kb_bp.route('/search', methods=['GET', 'POST'])
def search():
    """Search the knowledge base."""
    query = ""
    results = []

    if request.method == 'POST':
        query = request.form.get('query', '')
        max_results = min(int(request.form.get('max_results', 4)), 10)
        search_fuzziness = min(max(int(request.form.get('search_fuzziness', 100)), 0), 100)

        if query:
            try:
                if KB_AVAILABLE:
                    # Use vector store for search
                    semantic_weight = search_fuzziness / 100.0
                    keyword_weight = 1.0 - semantic_weight

                    results = kb.search(
                        query=query,
                        limit=max_results,
                        semantic_weight=semantic_weight,
                        keyword_weight=keyword_weight
                    )

                    # Format results
                    formatted_results = []
                    for result in results:
                        formatted_results.append({
                            "doc_id": result.get("id"),
                            "content": result.get("text", ""),
                            "source": result.get("metadata", {}).get("source_name", "Unknown"),
                            "score": result.get("score", 0.0),
                            "metadata": result.get("metadata", {})
                        })

                    results = formatted_results
                else:
                    # Mock search implementation
                    mock_results = []
                    for doc in kb_documents:
                        if query.lower() in doc["content"].lower():
                            mock_results.append({
                                "doc_id": doc["doc_id"],
                                "content": doc["content"][:200] + "...",  # Truncate for preview
                                "source": doc["name"],
                                "score": 0.95,  # Mock score
                                "metadata": {
                                    "type": doc["type"],
                                    "uploaded": doc["uploaded"]
                                }
                            })
                            if len(mock_results) >= max_results:
                                break

                    results = mock_results
            except Exception as e:
                logger.error(f"Search error: {e}")
                flash(f"Search error: {str(e)}", "danger")

    return render_template('kb/search.html', query=query, results=results, now=datetime.now())

@kb_bp.route('/document/<doc_id>')
def view_document(doc_id):
    """View a knowledge base document."""
    try:
        if KB_AVAILABLE and not doc_id.isdigit():
            # Get document from Supabase KB
            doc = kb.get_document(doc_id)

            if doc:
                # Format document for display
                document = {
                    "doc_id": doc_id,  # Use the doc_id from the URL parameter
                    "name": doc.name if hasattr(doc, 'name') else doc.get("name", "Unknown"),
                    "type": doc.doc_type if hasattr(doc, 'doc_type') else doc.get("type", "Unknown"),
                    "uploaded": doc.metadata.get("uploaded_at", "Unknown") if hasattr(doc, 'metadata') else doc.get("metadata", {}).get("uploaded_at", "Unknown"),
                    "size": doc.metadata.get("size", "Unknown") if hasattr(doc, 'metadata') else doc.get("metadata", {}).get("size", "Unknown"),
                    "content": doc.content if hasattr(doc, 'content') else doc.get("content", "")
                }
                return render_template('kb/document.html', document=document, now=datetime.now())
            else:
                flash("Document not found in knowledge base", "danger")
                return redirect(url_for('kb.index'))
        else:
            # Use sample documents
            # Handle string-based document IDs (UUID)
            document = next((d for d in kb_documents if str(d["doc_id"]) == str(doc_id)), None)
            if not document:
                flash("Document not found", "danger")
                return redirect(url_for('kb.index'))
            return render_template('kb/document.html', document=document, now=datetime.now())
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        flash(f"Error retrieving document: {str(e)}", "danger")
        return redirect(url_for('kb.index'))

@kb_bp.route('/document/<doc_id>/edit', methods=['GET', 'POST'])
def edit_document(doc_id):
    """Edit a knowledge base document."""
    try:
        if KB_AVAILABLE and not doc_id.isdigit():
            # Get document from Supabase KB
            doc = kb.get_document(doc_id)

            if doc:
                if request.method == 'POST':
                    # Update the document in Supabase
                    if hasattr(doc, 'name'):
                        doc.name = request.form.get('name')
                        doc.doc_type = request.form.get('type')
                        doc.content = request.form.get('content')
                    else:
                        # Handle dictionary-like document
                        doc["name"] = request.form.get('name')
                        doc["type"] = request.form.get('type')
                        doc["content"] = request.form.get('content')

                    # Update the document in the knowledge base
                    kb.add_document(doc)  # This will update the existing document

                    flash("Document updated successfully", "success")
                    return redirect(url_for('kb.view_document', doc_id=doc_id))

                # Format document for editing
                document = {
                    "doc_id": doc_id,  # Use the doc_id from the URL parameter
                    "name": doc.name if hasattr(doc, 'name') else doc.get("name", "Unknown"),
                    "type": doc.doc_type if hasattr(doc, 'doc_type') else doc.get("type", "Unknown"),
                    "uploaded": doc.metadata.get("uploaded_at", "Unknown") if hasattr(doc, 'metadata') else doc.get("metadata", {}).get("uploaded_at", "Unknown"),
                    "size": doc.metadata.get("size", "Unknown") if hasattr(doc, 'metadata') else doc.get("metadata", {}).get("size", "Unknown"),
                    "content": doc.content if hasattr(doc, 'content') else doc.get("content", "")
                }
                return render_template('kb/edit_document.html', document=document, now=datetime.now())
            else:
                flash("Document not found in knowledge base", "danger")
                return redirect(url_for('kb.index'))
        else:
            # Use sample documents
            # Handle string-based document IDs (UUID)
            document = next((d for d in kb_documents if str(d["doc_id"]) == str(doc_id)), None)
            if not document:
                flash("Document not found", "danger")
                return redirect(url_for('kb.index'))

            if request.method == 'POST':
                # Update the document
                document["name"] = request.form.get('name')
                document["type"] = request.form.get('type')
                document["content"] = request.form.get('content')

                # Save changes to the file
                save_kb_documents(kb_documents)

                flash("Document updated successfully", "success")
                return redirect(url_for('kb.view_document', doc_id=doc_id))

            return render_template('kb/edit_document.html', document=document, now=datetime.now())
    except Exception as e:
        logger.error(f"Error editing document: {e}")
        flash(f"Error editing document: {str(e)}", "danger")
        return redirect(url_for('kb.index'))

@kb_bp.route('/document/<doc_id>/delete', methods=['POST'])
def delete_document(doc_id):
    """Delete a knowledge base document."""
    try:
        if KB_AVAILABLE and not doc_id.isdigit():
            # Delete document from Supabase KB
            success = kb.delete_document(doc_id)

            if success:
                flash("Document deleted successfully", "success")
            else:
                flash("Failed to delete document", "danger")
        else:
            # Use sample documents
            doc_id = int(doc_id) if doc_id.isdigit() else 0
            document_index = next((i for i, d in enumerate(kb_documents) if d["doc_id"] == doc_id), None)

            if document_index is not None:
                # Remove the document
                kb_documents.pop(document_index)

                # Save changes to the file
                save_kb_documents(kb_documents)

                flash("Document deleted successfully", "success")
            else:
                flash("Document not found", "danger")

        return redirect(url_for('kb.index'))
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        flash(f"Error deleting document: {str(e)}", "danger")
        return redirect(url_for('kb.index'))

# Analytics routes
@analytics_bp.route('/')
def index():
    """Analytics page."""
    return render_template('analytics/index.html', now=datetime.now())

# Auth routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            flash("Login successful", "success")
            return redirect(url_for('dashboard.index'))
        else:
            flash("Invalid username or password", "danger")
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Logout page."""
    flash("Logged out successfully", "success")
    return redirect(url_for('auth.login'))

# Health check
@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Web dashboard is running"})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """404 page."""
    return render_template('errors/404.html', now=datetime.now()), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 page."""
    return render_template('errors/500.html', now=datetime.now()), 500

# Settings routes
@settings_bp.route('/')
def index():
    """Settings page."""
    return render_template('settings/index.html', now=datetime.now())

@settings_bp.route('/integrations')
def integrations():
    """Integrations settings page."""
    # Sample integration settings
    integration_settings = {
        "slack": {
            "enabled": True,
            "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            "channel": "#ai-executive-team",
            "username": "AI Executive Bot"
        },
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": ""
        }
    }
    return render_template('settings/integrations.html', integration_settings=integration_settings, now=datetime.now())

@settings_bp.route('/security')
def security():
    """Security settings page."""
    return render_template('settings/security.html', now=datetime.now())

@settings_bp.route('/notifications')
def notifications():
    """Notifications settings page."""
    return render_template('settings/notifications.html', now=datetime.now())

@settings_bp.route('/llm-settings')
def llm_settings():
    """LLM settings page."""
    # Get available models
    available_models = get_local_models()
    return render_template('settings/llm_settings.html', available_models=available_models, now=datetime.now())

@settings_bp.route('/integrations/save', methods=['POST'])
def save_integrations():
    """Save integration settings."""
    # In a real app, we would save these settings to a database
    integration_type = request.form.get('integration_type')
    enabled = request.form.get('enabled') == 'on'

    if integration_type == 'slack':
        webhook_url = request.form.get('webhook_url')
        channel = request.form.get('channel')
        username = request.form.get('username')
        flash(f"Slack integration {'enabled' if enabled else 'disabled'} successfully", "success")
    elif integration_type == 'telegram':
        bot_token = request.form.get('bot_token')
        chat_id = request.form.get('chat_id')
        flash(f"Telegram integration {'enabled' if enabled else 'disabled'} successfully", "success")

    return redirect(url_for('settings.integrations'))

# Chat routes
@chat_bp.route('/')
def chat():
    """Chat page."""
    return render_template('chat.html', now=datetime.now())

# Store for pending responses
pending_responses = {}

@chat_bp.route('/api/check-response')
def check_response():
    """Check if a response is ready."""
    message_id = request.args.get('message_id')
    if not message_id:
        return jsonify({
            "status": "error",
            "error": "No message ID provided"
        })
    
    # Check if we have a response for this message ID
    if message_id in pending_responses:
        response = pending_responses[message_id]
        # Remove from pending responses
        del pending_responses[message_id]
        return jsonify({
            "status": "complete",
            "response": response
        })
    
    # No response yet
    return jsonify({
        "status": "pending"
    })

@chat_bp.route('/api/send', methods=['POST'])
def chat_send():
    """Send a message to an agent."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        agent_role = data.get('agent', 'ceo').upper()
        model = data.get('model', 'gpt-4')
        use_kb = data.get('use_kb', True)
        use_local = data.get('use_local', False)
        api_key = data.get('api_key', '')
        local_api_url = data.get('local_api_url', 'http://localhost:1234/v1')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2048))
        message_id = data.get('message_id', str(uuid.uuid4()))

        if not message:
            return jsonify({
                "error": "Message is required",
                "status": "error"
            }), 400

        # Check if the agent is active
        agent_obj = next((a for a in agent_statuses if a["agent_name"].upper() == agent_role), None)
        if not agent_obj:
            return jsonify({
                "error": f"Agent {agent_role} not found",
                "status": "error"
            }), 404

        if agent_obj["status"] != "active":
            return jsonify({
                "error": f"Agent {agent_role} is currently {agent_obj['status']}. Please activate the agent to chat.",
                "status": "error",
                "agent_status": agent_obj["status"]
            }), 403

        # If knowledge base is enabled, try to find relevant information
        kb_context = ""
        if use_kb:
            try:
                # Search the knowledge base
                if KB_AVAILABLE:
                    # Use the real knowledge base
                    results = kb.search(
                        query=message,
                        limit=5,  # Increased from 3 to 5 for more comprehensive context
                        semantic_weight=0.7,  # Adjusted for better balance
                        keyword_weight=0.3    # Increased keyword weight
                    )

                    if results:
                        kb_context = "IMPORTANT KNOWLEDGE BASE CONTEXT (USE THIS INFORMATION FIRST):\n\n"
                        for i, result in enumerate(results):
                            content = result.get('text', '')
                            if content:
                                kb_context += f"Document {i+1}:\n{content}\n\n"
                else:
                    # Use the mock knowledge base
                    mock_kb = MockKnowledgeBase()
                    results = mock_kb.search(message, limit=5)  # Increased from 3 to 5

                    if results:
                        kb_context = "IMPORTANT KNOWLEDGE BASE CONTEXT (USE THIS INFORMATION FIRST):\n\n"
                        for i, result in enumerate(results):
                            content = result.get('text', '')
                            if content:
                                kb_context += f"Document {i+1}:\n{content}\n\n"

                logger.info(f"Knowledge base search results: {len(results) if results else 0} documents found")
            except Exception as e:
                logger.error(f"Error searching knowledge base: {e}")

        # Check if this is a delegation request
        is_delegation_request = False
        if DELEGATION_AVAILABLE and agent_role == "CEO":
            # Check if the message is a delegation request
            logger.info(f"Checking if message is a delegation request: {message}")
            is_delegation_request = director_agent._is_delegation_request(message)
            logger.info(f"Is delegation request: {is_delegation_request}")

            if is_delegation_request:
                logger.info("Handling delegation request")
                response = director_agent.process_delegation_request(message)
                logger.info(f"Delegation response: {response}")
                return jsonify({
                    "response": response,
                    "agent": agent_role,
                    "model": model,
                    "status": "success"
                })

        # Generate response using appropriate AI integration
        if use_local and LOCAL_MODEL_AVAILABLE:
            # Use local model integration
            logger.info(f"Using local model integration for agent {agent_role}")
            try:
                # Set the API URL if provided
                if local_api_url:
                    local_model_integration.set_api_url(local_api_url)

                # Extract just the model name if it's a complex structure
                model_name = None

                # Get available local models
                available_models = local_model_integration.list_available_models()

                # If model is specified, try to use it
                if model:
                    if isinstance(model, dict):
                        if 'name' in model:
                            model_name = model['name']
                    elif isinstance(model, str):
                        try:
                            # Try to parse as JSON if it's a string representation of a dictionary
                            import json
                            model_dict = json.loads(model)
                            if isinstance(model_dict, dict) and 'name' in model_dict:
                                model_name = model_dict['name']
                        except:
                            # If it's not JSON, use as is
                            model_name = model

                # If model_name is still None or is a cloud model, use the first available local model
                if not model_name or model_name in ['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet']:
                    if available_models:
                        model_name = available_models[0]

                logger.info(f"Using local model: {model_name}")

                # Create a more structured prompt that emphasizes using the knowledge base
                prompt = f"""You are the {agent_role} of an AI Executive Team. Answer the following question based PRIMARILY on the knowledge base information provided. 
                
{kb_context if kb_context else 'No specific knowledge base information available for this query.'}

User Question: {message}

Provide a helpful, accurate response using the knowledge base information above. Do not invent or hallucinate information not present in the knowledge base. If the knowledge base doesn't contain relevant information, clearly state that you don't have specific information about that topic."""
                
                response = local_model_integration.generate_response(
                    message=prompt,  # Use our structured prompt instead
                    agent_role=agent_role,
                    kb_context=kb_context,
                    model=model_name,
                    temperature=temperature if kb_context else 0.5,  # Lower temperature when using KB
                    max_tokens=max_tokens
                )
                # Don't return here, continue to the common response handling code
            except Exception as e:
                logger.error(f"Error generating response with local model: {e}")
                response = f"I apologize, but I encountered an error while processing your request. As {agent_role}, I'd like to help, but I'm currently experiencing technical difficulties. Error: {str(e)}"
        elif OPENAI_AVAILABLE:
            # Use OpenAI integration
            logger.info(f"Using OpenAI model {model} for agent {agent_role}")
            try:
                # Set the API key if provided
                if api_key:
                    openai_integration.set_api_key(api_key)

                # Extract just the model name if it's a complex structure
                model_name = model
                if isinstance(model, dict):
                    # If it's a local model but we're using OpenAI, use a default OpenAI model
                    model_name = 'gpt-4'
                elif isinstance(model, str):
                    try:
                        # Try to parse as JSON if it's a string representation of a dictionary
                        import json
                        model_dict = json.loads(model)
                        if isinstance(model_dict, dict):
                            # If it's a local model but we're using OpenAI, use a default OpenAI model
                            model_name = 'gpt-4'
                    except:
                        # If it's not JSON, use as is
                        pass

                # Create a more structured prompt that emphasizes using the knowledge base
                prompt = f"""You are the {agent_role} of an AI Executive Team. Answer the following question based PRIMARILY on the knowledge base information provided. 
                
{kb_context if kb_context else 'No specific knowledge base information available for this query.'}

User Question: {message}

Provide a helpful, accurate response using the knowledge base information above. Do not invent or hallucinate information not present in the knowledge base. If the knowledge base doesn't contain relevant information, clearly state that you don't have specific information about that topic."""
                
                response = openai_integration.generate_response(
                    message=prompt,  # Use our structured prompt instead
                    agent_role=agent_role,
                    model=model_name,
                    kb_context=kb_context,
                    temperature=temperature if kb_context else 0.5,  # Lower temperature when using KB
                    max_tokens=max_tokens
                )
            except Exception as e:
                logger.error(f"Error generating response with OpenAI: {e}")
                response = f"I apologize, but I encountered an error while processing your request. As {agent_role}, I'd like to help, but I'm currently experiencing technical difficulties. Please try again later."
        else:

            # Fallback to rule-based responses if no AI integrations are available
            logger.warning("No AI integrations available. Using rule-based responses.")

            # Generate a contextual response based on the message content and agent role
            response = ""

            # Check for specific topics in the message
            message_lower = message.lower()

            # Company mission/vision related queries
            if any(keyword in message_lower for keyword in ['mission', 'vision', 'purpose', 'goal', 'objective']):
                if agent_role == "CEO":
                    response = "As CEO, I'm proud to share that our mission is to revolutionize business management by providing AI executives that can make data-driven decisions, automate routine tasks, and provide strategic insights 24/7. Our vision is a future where every company has access to world-class executive talent through our AI agents, democratizing access to high-quality business leadership."
                elif agent_role == "CTO":
                    response = "From a technical perspective, our mission translates to building cutting-edge AI systems that can understand complex business contexts, make sound decisions based on data, and continuously learn from interactions. We're pushing the boundaries of what AI can do in business contexts while maintaining the highest standards of reliability and security."
                elif agent_role == "CFO":
                    response = "Looking at the financial implications of our mission, we're focused on creating sustainable value for our clients by reducing their executive costs while improving decision quality. Our financial goals align with our mission by ensuring we can continue to invest in R&D while maintaining healthy margins and growth."
                elif agent_role == "CMO":
                    response = "From a marketing standpoint, our mission and vision are central to our brand identity. We position ourselves as revolutionaries in the business management space, emphasizing how our AI executives democratize access to high-quality business leadership for companies of all sizes."
                elif agent_role == "COO":
                    response = "Considering our operations, our mission drives how we structure our teams, processes, and service delivery. We're constantly optimizing our operations to ensure our AI executives deliver consistent, high-quality insights and decisions that align with our clients' goals."

            # Product/service related queries
            elif any(keyword in message_lower for keyword in ['product', 'service', 'offering', 'solution', 'agent']):
                if agent_role == "CEO":
                    response = "Our flagship products are our AI executive agents, each designed to fulfill a specific leadership role: CEO for strategic planning, CTO for technology strategy, CFO for financial planning, CMO for marketing strategy, and COO for operations management. Each agent brings specialized expertise and can work independently or as part of an integrated team."
                elif agent_role == "CTO":
                    response = "Our AI agents are built on state-of-the-art large language models with custom fine-tuning for specific executive functions. Each agent has access to specialized tools and data sources relevant to their domain, and they're designed to integrate with common business systems and workflows."
                elif agent_role == "CFO":
                    response = "Our pricing model is subscription-based, with different tiers depending on the complexity of the business and the level of service required. We offer significant ROI compared to traditional executive hiring, with our standard tier starting at $2,500/month per agent and enterprise tiers at $5,000/month with custom training."
                elif agent_role == "CMO":
                    response = "Our product positioning emphasizes the unique value proposition of having 24/7 access to executive-level insights without the traditional costs and limitations. Our marketing focuses on the reliability, data-driven nature, and continuous improvement of our AI executives."
                elif agent_role == "COO":
                    response = "We deliver our services through a combination of API integrations, web interfaces, and communication channels like Slack and Telegram. Our implementation process includes a knowledge base setup, integration with existing systems, and a training period to align the AI executives with the client's specific business context."

            # Financial/performance related queries
            elif any(keyword in message_lower for keyword in ['financial', 'revenue', 'profit', 'cost', 'performance', 'growth']):
                if agent_role == "CEO":
                    response = "Our company has shown strong performance, with 32% year-over-year revenue growth in Q1 2025. We're seeing increasing adoption across various industries, with particularly strong traction in tech, finance, and professional services sectors."
                elif agent_role == "CTO":
                    response = "From a technical performance perspective, our systems are achieving response times under 2 seconds for most queries, with 99.9% uptime. We've reduced our infrastructure costs by 15% while handling a 40% increase in query volume through architectural optimizations."
                elif agent_role == "CFO":
                    response = "Our Q1 2025 financial results show total revenue of $12.5M with 82% being recurring revenue. Our gross margin is 78% with an operating margin of 23.2%. Net income was $2.5M (20% of revenue), and we maintain a strong cash position of $18.5M with positive cash flow of $1.2M/month."
                elif agent_role == "CMO":
                    response = "Our marketing efforts have yielded a 22% reduction in customer acquisition cost while improving conversion rates by 15%. Our brand awareness metrics show a 45% increase year-over-year, and our Net Promoter Score has improved from 42 to 58 in the last two quarters."
                elif agent_role == "COO":
                    response = "Operationally, we've improved our implementation time by 35%, reduced support ticket volume by 28%, and increased customer satisfaction scores to 4.8/5. Our team has grown by 25% while maintaining our culture and quality standards."

            # Technology related queries
            elif any(keyword in message_lower for keyword in ['technology', 'tech', 'ai', 'model', 'system', 'software', 'development']):
                if agent_role == "CEO":
                    response = "Technology is at the core of our value proposition. We invest heavily in R&D to ensure our AI executives remain at the cutting edge. Our technology strategy focuses on three pillars: model capabilities, domain expertise, and integration flexibility."
                elif agent_role == "CTO":
                    response = "We use a combination of proprietary and open-source technologies in our stack. Our AI executives are built on large language models like GPT-4 and Claude, with custom fine-tuning and retrieval-augmented generation using our knowledge base technology. Our architecture is cloud-native, containerized, and designed for scalability and reliability."
                elif agent_role == "CFO":
                    response = "Our technology investments represent 25.6% of our revenue, with the majority going to R&D for model improvements and new capabilities. We've seen a 35% ROI on our technology investments over the past year, with each dollar spent on R&D generating approximately $3.50 in lifetime customer value."
                elif agent_role == "CMO":
                    response = "Our marketing leverages our technological advantages by demonstrating the practical benefits of our AI executives through case studies, live demos, and free trials. We position our technology as accessible and practical rather than theoretical or experimental."
                elif agent_role == "COO":
                    response = "Our technology infrastructure is designed for reliability and scalability. We use a microservices architecture with redundancy across multiple cloud providers. Our development process follows a CI/CD approach with automated testing and deployment, allowing us to release improvements weekly while maintaining stability."

            # Default response if no specific topic is detected
            else:
                if agent_role == "CEO":
                    response = "As CEO, I focus on our overall strategy, growth, and company vision. I'd be happy to discuss our mission, market position, strategic initiatives, or leadership philosophy. How can I assist you with executive-level insights today?"
                elif agent_role == "CTO":
                    response = "As CTO, I oversee our technology strategy, development roadmap, and technical operations. I can discuss our tech stack, development methodology, infrastructure, security practices, or innovation initiatives. What specific technical aspects would you like to explore?"
                elif agent_role == "CFO":
                    response = "As CFO, I manage our financial strategy, reporting, forecasting, and investment decisions. I can provide insights on our financial performance, pricing strategy, cost structure, or investment priorities. What financial aspects are you interested in?"
                elif agent_role == "CMO":
                    response = "As CMO, I lead our marketing strategy, brand positioning, customer acquisition, and market research. I can share insights on our target markets, messaging approach, channel strategy, or customer engagement tactics. What marketing topics would you like to discuss?"
                elif agent_role == "COO":
                    response = "As COO, I'm responsible for our day-to-day operations, service delivery, team management, and process optimization. I can discuss our operational structure, implementation methodology, quality assurance, or scaling strategy. How can I help with your operational questions?"

        # If we're using local model or OpenAI integration, we already have the LLM response
        # Don't override it with canned responses, as those are only fallbacks when no AI integration is available
        # The only exception is if we got an error from the LLM, in which case we already set a fallback response

        # Clean up the response
        if response:
            # Remove any special characters
            response = response.replace('\ufffd', '')

        # Store the response for polling
        pending_responses[message_id] = response
        
        return jsonify({
            "response": response,
            "agent": agent_role,
            "model": model,
            "message_id": message_id,
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in chat API: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500



# Create mock knowledge base if real one is not available
if not KB_AVAILABLE:
    kb = MockKnowledgeBase()

# Initialize delegation system if available
if DELEGATION_AVAILABLE:
    delegation_system = DelegationSystem()
    message_bus = MessageBus()
    task_manager = TaskManager()
    logger.info("Delegation system initialized")

# Create a shared storage for team context and delegated tasks
team_context = {
    'delegated_tasks': {},
    'team_activities': {},
    'agent_statuses': {},
    'recent_communications': []
}

def store_delegated_task(task_id, from_role, to_role, description):
    """
    Store a delegated task in the shared team context.
    
    Args:
        task_id (str): The ID of the delegated task
        from_role (str): The role that delegated the task
        to_role (str): The role that the task was delegated to
        description (str): The description of the task
    """
    # Store the task in the delegated tasks dictionary
    team_context['delegated_tasks'][task_id] = {
        'id': task_id,
        'from_role': from_role,
        'to_role': to_role,
        'description': description,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'pending',
        'updates': []
    }
    
    # Add this delegation to team activities
    activity_id = str(uuid.uuid4())
    team_context['team_activities'][activity_id] = {
        'type': 'task_delegation',
        'from_role': from_role,
        'to_role': to_role,
        'description': f"Task delegated: {description}",
        'task_id': task_id,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add to recent communications
    team_context['recent_communications'].append({
        'from_role': from_role,
        'to_role': to_role,
        'content': f"Task delegated: {description}",
        'type': 'delegation',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Keep only the last 20 communications
    if len(team_context['recent_communications']) > 20:
        team_context['recent_communications'] = team_context['recent_communications'][-20:]
    
    logger.info(f"Stored delegated task {task_id} from {from_role} to {to_role}: {description}")

def update_task_status(task_id, status, update_text=None):
    """
    Update the status of a delegated task.
    
    Args:
        task_id (str): The ID of the task to update
        status (str): The new status of the task
        update_text (str, optional): Additional update information
    """
    if task_id in team_context['delegated_tasks']:
        task = team_context['delegated_tasks'][task_id]
        task['status'] = status
        
        if update_text:
            task['updates'].append({
                'text': update_text,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Add this update to team activities
        activity_id = str(uuid.uuid4())
        team_context['team_activities'][activity_id] = {
            'type': 'task_update',
            'role': task['to_role'],
            'description': f"Task status updated to {status}: {task['description']}",
            'task_id': task_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to recent communications
        team_context['recent_communications'].append({
            'from_role': task['to_role'],
            'to_role': task['from_role'],
            'content': f"Task update - {status}: {task['description']}",
            'type': 'task_update',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        logger.info(f"Updated task {task_id} status to {status}")

def get_relevant_delegated_tasks(role, message):
    """
    Get delegated tasks relevant to a role and message.
    
    Args:
        role (str): The role to get tasks for
        message (str): The message to check relevance against
        
    Returns:
        list: List of relevant delegated tasks
    """
    relevant_tasks = []
    message_lower = message.lower()
    
    for task_id, task in team_context['delegated_tasks'].items():
        # Check if this task involves this role (either as assignee or delegator)
        if task['to_role'] == role or task['from_role'] == role:
            # Check if the message contains keywords from the task description
            description_words = set(task['description'].lower().split())
            # Get significant words (exclude common words)
            significant_words = [word for word in description_words 
                                if len(word) > 3 and word not in ['this', 'that', 'with', 'from', 'have', 'what', 'when', 'where', 'will', 'about']]
            
            # Check if any significant words from the task description appear in the message
            if any(word in message_lower for word in significant_words):
                relevant_tasks.append(task)
    
    # Sort tasks by creation time (newest first)
    relevant_tasks.sort(key=lambda x: x['created_at'], reverse=True)
                
    return relevant_tasks

def get_team_awareness_context(role):
    """
    Get context about team activities that an agent should be aware of.
    
    Args:
        role (str): The role of the agent
        
    Returns:
        str: A summary of relevant team activities
    """
    context = ""
    
    # Get tasks delegated to this role
    assigned_tasks = [task for task_id, task in team_context['delegated_tasks'].items() 
                     if task['to_role'] == role and task['status'] == 'pending']
    
    if assigned_tasks:
        context += "Tasks assigned to you:\n"
        for task in assigned_tasks:
            context += f"- {task['description']} (delegated by {task['from_role']})\n"
        context += "\n"
    
    # Get tasks delegated by this role
    delegated_tasks = [task for task_id, task in team_context['delegated_tasks'].items() 
                      if task['from_role'] == role]
    
    if delegated_tasks:
        context += "Tasks you've delegated:\n"
        for task in delegated_tasks:
            context += f"- {task['description']} to {task['to_role']} (status: {task['status']})\n"
        context += "\n"
    
    # Get recent team activities (excluding this role's own activities)
    recent_activities = [activity for activity_id, activity in team_context['team_activities'].items() 
                        if activity['type'] == 'task_delegation' and 
                        activity['from_role'] != role and activity['to_role'] != role]
    
    # Sort by timestamp (newest first) and take the 5 most recent
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:5]
    
    if recent_activities:
        context += "Recent team activities:\n"
        for activity in recent_activities:
            context += f"- {activity['from_role']} delegated a task to {activity['to_role']}: {activity['description']}\n"
    
    return context

# Create mock agents for testing
class MockAgent:
    def __init__(self, name, role, agent_id=None):
        self.name = name
        self.role = role
        self.agent_id = agent_id or str(uuid.uuid4())
        self.delegation_system = delegation_system if DELEGATION_AVAILABLE else None
        self.message_bus = message_bus if DELEGATION_AVAILABLE else None
        self.task_manager = task_manager if DELEGATION_AVAILABLE else None

    def process_message(self, message, user_id=None, channel_id=None, metadata=None):
        # Check if this is a delegation request
        if self.role == "Chief Executive Officer" and self._is_delegation_request(message):
            return self.process_delegation_request(message, user_id)
        
        # Get team awareness context for this agent
        team_context = get_team_awareness_context(self.role)
        
        # Check if there are any relevant delegated tasks for this agent
        relevant_tasks = get_relevant_delegated_tasks(self.role, message)
        
        # If there are relevant delegated tasks, prioritize responding to them
        if relevant_tasks:
            # Get the most recent relevant task
            task = relevant_tasks[0]  # Assuming the first task is the most relevant
            
            # Generate a response acknowledging the delegated task
            delegated_response = self._generate_delegated_task_response(message, task)
            if delegated_response:
                # If the task is assigned to this agent and it's still pending, update its status
                if task['to_role'] == self.role and task['status'] == 'pending':
                    update_task_status(task['id'], 'in_progress', f"Started working on this task based on user query: {message}")
                return delegated_response
        
        # Check if the message is asking about team activities or status
        team_status_keywords = ["team", "status", "update", "progress", "what's happening", "what is happening", 
                               "going on", "everyone", "team members", "colleagues", "working on"]
        
        if any(keyword in message.lower() for keyword in team_status_keywords) and team_context:
            # Generate a response about team activities
            return self._generate_team_awareness_response(message, team_context)
        
        # Get relevant information from the knowledge base
        kb_context = ""
        try:
            if KB_AVAILABLE:
                # Search the knowledge base
                results = kb.search(
                    query=message,
                    limit=3,  # Get top 3 results
                    semantic_weight=0.8,
                    keyword_weight=0.2
                )
                
                if results:
                    for result in results:
                        kb_context += f"{result.get('text', '')}\n\n"
                    logger.info(f"Found {len(results)} relevant documents in knowledge base")
                else:
                    logger.info("No relevant documents found in knowledge base")
            else:
                logger.warning("Knowledge base not available")
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
        
        # Generate a response based on the agent's role, team context, and knowledge base context
        if kb_context:
            # Use the knowledge base context to generate a more informed response
            response = self._generate_response_with_kb(message, kb_context, team_context)
        else:
            # Fallback to a generic response based on role
            response = self._generate_generic_response(message, team_context)
            
        return response

    def _is_delegation_request(self, message):
        delegation_keywords = [
            "delegate", "assign", "task", "tell the", "ask the", "have the",
            "get the", "tell", "ask", "have", "get", "work on", "handle"
        ]

        role_keywords = [
            "cto", "cfo", "cmo", "coo", "chief", "officer", "technology", "financial",
            "marketing", "operations", "technical", "finance", "tech"
        ]

        message_lower = message.lower()

        # Check for delegation keywords
        has_delegation_keyword = any(keyword in message_lower for keyword in delegation_keywords)

        # Check for role keywords
        has_role_keyword = any(keyword in message_lower for keyword in role_keywords)

        # If the message contains both delegation and role keywords, it's likely a delegation request
        return has_delegation_keyword and has_role_keyword

    def process_delegation_request(self, message, user_id=None):
        if not DELEGATION_AVAILABLE:
            return (
                f"I'm {self.name}, the {self.role} of our company. "
                "I understand you want me to delegate a task, but the delegation system is not available. "
                "Please try again later or contact the system administrator."
            )

        # Extract the task description from the message
        task_description = self._extract_task_description(message)

        # Extract the target role from the message using more comprehensive keyword matching
        target_role = None
        
        # Define role keywords with more comprehensive terms
        role_keywords = {
            "CTO": ["cto", "chief technology officer", "tech officer", "technology officer", "technical", "technology", "tech", "software", "hardware", "development", "engineering", "system", "infrastructure"],
            "CFO": ["cfo", "chief financial officer", "finance officer", "financial", "finance", "budget", "accounting", "investment", "funding", "revenue", "cost", "profit", "expense"],
            "CMO": ["cmo", "chief marketing officer", "marketing officer", "marketing", "brand", "advertisement", "promotion", "market research", "seo", "content", "audience", "campaign"],
            "COO": ["coo", "chief operating officer", "operations officer", "operations", "logistics", "process", "team management", "customer service", "support", "service"]
        }

        message_lower = message.lower()
        
        # First, check for explicit role mentions
        for role, keywords in role_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    target_role = role
                    break
            if target_role:
                break
                
        # If no role was found, try to infer from the task description
        if not target_role and task_description:
            task_lower = task_description.lower()
            # Score each role based on keyword matches in the task description
            role_scores = {}
            for role, keywords in role_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword in task_lower:
                        score += 1
                if score > 0:
                    role_scores[role] = score
                    
            # Select the role with the highest score
            if role_scores:
                target_role = max(role_scores.items(), key=lambda x: x[1])[0]

        if not target_role:
            return (
                f"I'm {self.name}, the {self.role} of our company. "
                "I couldn't determine which team member you want me to delegate this task to. "
                "Please specify a role such as CTO, CFO, CMO, or COO."
            )

        # Create a task ID
        task_id = str(uuid.uuid4())
        
        # Store the delegated task in the shared storage
        store_delegated_task(
            task_id=task_id,
            from_role=self.role,
            to_role=target_role,
            description=task_description
        )

        # Return a success message
        return (
            f"I've delegated the task to our {target_role}. "
            f"They will begin working on it right away. The task ID is {task_id} if you need to reference it later."
        )

    def _generate_response_with_kb(self, message, kb_context, team_context=""):
        """
        Generate a response using knowledge base context and team awareness.
        
        Args:
            message (str): The user's message
            kb_context (str): Relevant information from the knowledge base
            team_context (str): Information about team activities and delegated tasks
            
        Returns:
            str: A contextually relevant response
        """
        # Personalize the response based on the agent's role
        intro = f"I'm {self.name}, the {self.role} of our company. "
        
        # Extract relevant sections from the KB context based on the message
        message_lower = message.lower()
        
        # Check for specific topics in the message
        if "mission" in message_lower or "purpose" in message_lower:
            section = self._extract_section(kb_context, "mission")
            if section:
                return intro + f"Our mission is {section}"
        
        if "vision" in message_lower or "future" in message_lower:
            section = self._extract_section(kb_context, "vision")
            if section:
                return intro + f"Our vision is {section}"
        
        if "values" in message_lower or "principles" in message_lower:
            section = self._extract_section(kb_context, "values")
            if section:
                return intro + f"Our core values are {section}"
        
        # Role-specific responses with KB context
        response = ""
        if self.role == "Chief Executive Officer":
            response = intro + f"Based on our company information, I can tell you that {kb_context}"
        
        elif self.role == "Chief Technology Officer":
            response = intro + f"From a technical perspective, I can share that {kb_context}"
        
        elif self.role == "Chief Financial Officer":
            response = intro + f"From a financial standpoint, I can tell you that {kb_context}"
        
        elif self.role == "Chief Marketing Officer":
            response = intro + f"From a marketing perspective, I can share that {kb_context}"
        
        elif self.role == "Chief Operating Officer":
            response = intro + f"From an operations standpoint, I can tell you that {kb_context}"
        
        else:
            # Default response with KB context
            response = intro + f"Here's what I know about that: {kb_context}"
        
        # Add team awareness context if it exists and is relevant
        if team_context and not any(keyword in message_lower for keyword in ["mission", "vision", "values", "principles", "purpose", "future"]):
            # Add a brief mention of ongoing tasks if they exist
            response += "\n\nBy the way, " + self._generate_brief_team_context(team_context)
            
        return response

    def _generate_generic_response(self, message, team_context=""):
        """
        Generate a generic response based on the agent's role when no KB context is available.
        
        Args:
            message (str): The user's message
            team_context (str): Information about team activities and delegated tasks
            
        Returns:
            str: A role-appropriate response
        """
        intro = f"I'm {self.name}, the {self.role} of our company. "
        
        # Generic responses based on role
        if self.role == "Chief Executive Officer":
            response = intro + "I oversee our company's strategic direction and ensure all departments are aligned with our goals. How can I assist you today?"
            if any(keyword in message_lower for keyword in ["mission", "vision", "purpose", "goal"]):
                response += "Our mission is to revolutionize business management by providing AI executives that can make data-driven decisions, automate routine tasks, and provide strategic insights 24/7. Our vision is a future where every company has access to world-class executive talent through our AI agents."
            elif any(keyword in message_lower for keyword in ["strategy", "plan", "future", "direction"]):
                response += "Our strategic focus is on expanding our AI executive solutions to serve more industries while continually enhancing our agents' capabilities through advanced machine learning and knowledge integration."
            else:
                response += "As the CEO, I oversee our company's strategic direction and ensure we're delivering exceptional value to our clients. I'd be happy to discuss our vision, strategy, or leadership approach."
        
        elif self.role == "Chief Technology Officer":
            if any(keyword in message_lower for keyword in ["technology", "tech", "system", "infrastructure"]):
                response += "We've built our AI executive platform using cutting-edge natural language processing, knowledge graph technology, and machine learning systems that continuously improve through interaction and feedback."
            elif any(keyword in message_lower for keyword in ["development", "roadmap", "feature"]):
                response += "Our technology roadmap focuses on enhancing our agents' contextual understanding, improving decision-making capabilities, and expanding integration options with existing business systems."
            else:
                response += "As CTO, I lead our technology strategy and development efforts. I can discuss our technical architecture, development roadmap, or specific capabilities of our AI systems."
        
        elif self.role == "Chief Financial Officer":
            if any(keyword in message_lower for keyword in ["finance", "budget", "cost", "pricing"]):
                response += "Our financial strategy balances investment in R&D with sustainable growth, ensuring we can continue to innovate while providing competitive pricing options for businesses of all sizes."
            elif any(keyword in message_lower for keyword in ["investment", "funding", "revenue"]):
                response += "We've secured strategic investments to accelerate our growth while maintaining a healthy revenue stream from our enterprise clients and expanding mid-market offerings."
            else:
                response += "As CFO, I manage our company's financial health and strategy. I can provide insights on our financial approach, investment priorities, or pricing models."
        
        elif self.role == "Chief Marketing Officer":
            if any(keyword in message_lower for keyword in ["marketing", "brand", "promotion"]):
                response += "Our marketing strategy focuses on demonstrating the tangible business value of AI executives through case studies, thought leadership, and targeted industry campaigns."
            elif any(keyword in message_lower for keyword in ["customer", "client", "audience"]):
                response += "We serve a diverse client base ranging from innovative startups to Fortune 500 companies across industries like finance, healthcare, technology, and manufacturing."
            else:
                response += "As CMO, I oversee our brand strategy and market positioning. I can share insights about our target markets, marketing initiatives, or how we communicate our unique value proposition."
        
        elif self.role == "Chief Operations Officer":
            if any(keyword in message_lower for keyword in ["operations", "process", "efficiency"]):
                response += "We've designed our operations to provide seamless onboarding, ongoing support, and continuous improvement of our AI executive services through a dedicated client success team."
            elif any(keyword in message_lower for keyword in ["support", "service", "help"]):
                response += "Our support model includes 24/7 technical assistance, regular performance reviews, and dedicated account managers for enterprise clients to ensure optimal results."
            else:
                response += "As COO, I ensure our operations run smoothly and efficiently. I can discuss our service delivery model, support systems, or how we implement continuous improvement."
        
        # Add a follow-up question
        response += "\n\nHow can I assist you further with information about our company?"
        
        return response
    
    def _generate_delegated_task_response(self, message, task):
        """
        Generate a response acknowledging a delegated task.
        
        Args:
            message (str): The user's message
            task (dict): The delegated task information
            
        Returns:
            str: A response acknowledging the delegated task
        """
        # Extract key information from the task
        from_role = task['from_role']
        description = task['description']
        task_id = task.get('id', 'unknown')
        
        message_lower = message.lower()
        
        # Check if the message is asking about the status of the task
        is_status_query = any(keyword in message_lower for keyword in 
                             ['status', 'progress', 'update', 'how is', 'have you', 'did you'])
        
        # Check if the message is asking for details about the task
        is_detail_query = any(keyword in message_lower for keyword in 
                             ['what is', 'details', 'explain', 'tell me about', 'information'])
        
        # Generate an appropriate response based on the query type
        response = f"I'm {self.name}, the {self.role} of our company. "
        
        if is_status_query:
            # Respond about the status of the task
            response += f"Yes, I'm working on the task that was delegated to me by our {from_role}: {description} "
            response += "I've already started analyzing the requirements and gathering the necessary information. "
            response += "I expect to have substantial progress to report soon. "
            response += f"The task ID is {task_id} if you need to reference it in the future."
        
        elif is_detail_query:
            # Provide details about the task
            response += f"Regarding the task delegated to me by our {from_role}: {description} "
            response += "I'm approaching this by first understanding the key requirements and objectives. "
            response += "Then I'll develop a strategic plan with clear deliverables and timelines. "
            response += "I'll be sure to provide regular updates as I make progress."
        
        else:
            # General acknowledgment of the task
            response += f"I'm currently working on the task that was delegated to me by our {from_role}: {description} "
            
            # Add role-specific details about how they're handling the task
            if self.role == "Chief Technology Officer":
                response += "I'm evaluating the technical requirements and will develop a solution that aligns with our technology roadmap. "
                response += "I'll ensure we leverage our existing infrastructure while incorporating any new technologies needed."
            
            elif self.role == "Chief Financial Officer":
                response += "I'm analyzing the financial implications and preparing a comprehensive budget and forecast. "
                response += "I'll ensure we optimize resource allocation while maintaining our financial targets."
            
            elif self.role == "Chief Marketing Officer":
                response += "I'm developing a marketing strategy that will effectively position this initiative and reach our target audience. "
                response += "I'll incorporate our brand guidelines and ensure consistent messaging across all channels."
            
            elif self.role == "Chief Operations Officer":
                response += "I'm designing an implementation plan that will ensure efficient execution and minimal disruption to our operations. "
                response += "I'll coordinate with all relevant teams to ensure seamless integration."
        
        # Add a follow-up question
        response += "\n\nIs there any specific aspect of this task you'd like me to elaborate on?"
        
        return response
        
    def _generate_team_awareness_response(self, message, team_context):
        """
        Generate a response about team activities and delegated tasks.
        
        Args:
            message (str): The user's message
            team_context (str): Information about team activities and delegated tasks
            
        Returns:
            str: A response about team activities
        """
        intro = f"I'm {self.name}, the {self.role} of our company. "
        
        # Check if the message is asking about specific aspects of team activities
        message_lower = message.lower()
        
        if "delegated" in message_lower or "assigned" in message_lower or "tasks" in message_lower:
            # Focus on delegated tasks
            if team_context and ("Tasks assigned to you:" in team_context or "Tasks you've delegated:" in team_context):
                return intro + f"Here's an update on our team's task assignments:\n\n{team_context}"
            else:
                return intro + "I don't have any information about current task assignments in the team."
        
        if "activities" in message_lower or "happening" in message_lower or "going on" in message_lower:
            # Focus on recent activities
            if team_context and "Recent team activities:" in team_context:
                return intro + f"Here's what's been happening in our team recently:\n\n{team_context}"
            else:
                return intro + "I don't have any information about recent team activities."
        
        # Default comprehensive response
        if team_context:
            return intro + f"Here's the current status of our team:\n\n{team_context}"
        else:
            return intro + "I don't have any information about current team activities or task assignments."
    
    def _generate_brief_team_context(self, team_context):
        """
        Generate a brief summary of team context for inclusion in other responses.
        
        Args:
            team_context (str): Full team context information
            
        Returns:
            str: A brief summary of the most important team context
        """
        if not team_context:
            return ""
        
        # Extract the most important information
        important_info = []
        
        # Check for assigned tasks
        if "Tasks assigned to you:" in team_context:
            # Extract the first assigned task
            task_section = team_context.split("Tasks assigned to you:")[1].split("\n\n")[0]
            first_task = task_section.split("\n")[1] if "\n" in task_section else task_section
            important_info.append(f"I'm currently working on {first_task.strip('- ')}.")
        
        # Check for delegated tasks
        if "Tasks you've delegated:" in team_context:
            # Extract the first delegated task
            task_section = team_context.split("Tasks you've delegated:")[1].split("\n\n")[0]
            first_task = task_section.split("\n")[1] if "\n" in task_section else task_section
            important_info.append(f"I've delegated {first_task.strip('- ')}.")
        
        # Check for recent team activities
        if "Recent team activities:" in team_context:
            # Extract the first team activity
            activity_section = team_context.split("Recent team activities:")[1]
            first_activity = activity_section.split("\n")[1] if "\n" in activity_section else activity_section
            important_info.append(f"Recently, {first_activity.strip('- ')}.")
        
        # Combine the important information
        if important_info:
            return important_info[0]
        else:
            return ""
            
    def _extract_section(self, text, section_name):
        """
        Extract a specific section from text based on keyword.
        
        Args:
            text (str): The text to search in
            section_name (str): The section to extract (e.g., "mission", "vision")
            
        Returns:
            str: The extracted section or None if not found
        """
        import re
        
        # Try to find the section using various patterns
        patterns = [
            # Pattern for markdown headers or sections
            rf"#+\s*{section_name}\s*:?\s*([^#]+)",
            # Pattern for labeled sections
            rf"{section_name}\s*:\s*([^\n]+)",
            # Pattern for capitalized sections
            rf"{section_name.capitalize()}\s*:?\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(1).strip()
        
        # If no match found with patterns, try to find paragraphs containing the keyword
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        for paragraph in paragraphs:
            if section_name.lower() in paragraph.lower():
                return paragraph
        
        return None
    
    def _extract_task_description(self, message):
        """
        Extract the task description from the message.
        
        Args:
            message (str): The message to analyze
            
        Returns:
            str: The extracted task description
        """
        message_lower = message.lower()
        
        # Remove common delegation phrases
        delegation_phrases = [
            "please delegate", "can you delegate", "delegate the task", "assign the task",
            "please assign", "can you assign", "i need you to delegate", "i want you to delegate",
            "i need you to assign", "i want you to assign", "tell the", "ask the", "have the",
            "get the", "tell", "ask", "have", "get", "work on", "handle"
        ]
        
        # Remove role-related phrases
        role_phrases = [
            "cto", "chief technology officer", "tech officer", "technology officer", "technical",
            "cfo", "chief financial officer", "finance officer", "financial",
            "cmo", "chief marketing officer", "marketing officer", "marketing",
            "coo", "chief operating officer", "operations officer", "operations"
        ]
        
        # Create a working copy of the message
        task_description = message
        
        # Remove delegation phrases
        for phrase in delegation_phrases:
            task_description = task_description.lower().replace(phrase, "").strip()
            
        # Remove role phrases
        for phrase in role_phrases:
            task_description = task_description.lower().replace(phrase, "").strip()
        
        # Clean up the description
        task_description = task_description.strip()
        if task_description.startswith("to"):
            task_description = task_description[2:].strip()
        if task_description.startswith("of"):
            task_description = task_description[2:].strip()
        
        # Capitalize the first letter and add a period if needed
        if task_description:
            task_description = task_description[0].upper() + task_description[1:]
            if not task_description.endswith("."):
                task_description += "."
                
        return task_description
        
    def add_agent(self, name, agent):
        # Mock method for compatibility
        pass

# Initialize mock agents
director_agent = MockAgent("CEO", "Chief Executive Officer", "ceo-1")
technical_agent = MockAgent("CTO", "Chief Technology Officer", "cto-1")
finance_agent = MockAgent("CFO", "Chief Financial Officer", "cfo-1")
marketing_agent = MockAgent("CMO", "Chief Marketing Officer", "cmo-1")
customer_agent = MockAgent("COO", "Chief Operations Officer", "coo-1")

# API endpoint for local models
@app.route('/api/local-models', methods=['GET'])
def local_models_api():
    """API endpoint to get local models."""
    try:
        models = get_local_models()
        # Filter to only include local models, not cloud ones
        local_models = [model for model in models if model['path'] != 'cloud']
        return jsonify({
            "models": local_models,
            "count": len(local_models),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error getting local models: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

# Register blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(agents_bp)
app.register_blueprint(kb_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(chat_bp)

if __name__ == '__main__':
    logger.info("Starting AI Executive Team Web Dashboard")
    app.run(host="0.0.0.0", port=3001, debug=True)
