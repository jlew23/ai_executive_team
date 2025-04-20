"""
Run the web dashboard.
"""

import os
import sys
import logging
import glob
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Blueprint
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__,
            template_folder=os.path.join('web_dashboard', 'templates'),
            static_folder=os.path.join('web_dashboard', 'static'))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

# Create blueprints
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')
agents_bp = Blueprint('agents', __name__, url_prefix='/agents')
kb_bp = Blueprint('kb', __name__, url_prefix='/kb')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

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

# Sample knowledge base documents
kb_documents = [
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

# Knowledge base routes
@kb_bp.route('/')
def index():
    """Knowledge base page."""
    return render_template('kb/index.html', documents=kb_documents, now=datetime.now())

@kb_bp.route('/document/<int:doc_id>')
def view_document(doc_id):
    """View a knowledge base document."""
    document = next((d for d in kb_documents if d["doc_id"] == doc_id), None)
    if not document:
        flash("Document not found", "danger")
        return redirect(url_for('kb.index'))
    return render_template('kb/document.html', document=document, now=datetime.now())

@kb_bp.route('/document/<int:doc_id>/edit', methods=['GET', 'POST'])
def edit_document(doc_id):
    """Edit a knowledge base document."""
    document = next((d for d in kb_documents if d["doc_id"] == doc_id), None)
    if not document:
        flash("Document not found", "danger")
        return redirect(url_for('kb.index'))

    if request.method == 'POST':
        # In a real app, we would update the document in the database
        document["name"] = request.form.get('name')
        document["type"] = request.form.get('type')
        document["content"] = request.form.get('content')
        flash("Document updated successfully", "success")
        return redirect(url_for('kb.view_document', doc_id=doc_id))

    return render_template('kb/edit_document.html', document=document, now=datetime.now())

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

# Register blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(agents_bp)
app.register_blueprint(kb_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(settings_bp)

if __name__ == '__main__':
    logger.info("Starting AI Executive Team Web Dashboard")
    app.run(host="0.0.0.0", port=3001, debug=True)
