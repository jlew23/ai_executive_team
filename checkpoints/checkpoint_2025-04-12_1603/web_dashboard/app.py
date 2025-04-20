"""
Simple Flask app for the web dashboard.
"""

import os
import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
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
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

# Sample data
agent_statuses = [
    {"agent_id": 1, "agent_name": "CEO", "status": "active", "last_active": "2025-04-12 14:30:00"},
    {"agent_id": 2, "agent_name": "CTO", "status": "active", "last_active": "2025-04-12 14:25:00"},
    {"agent_id": 3, "agent_name": "CFO", "status": "inactive", "last_active": "2025-04-12 10:15:00"},
    {"agent_id": 4, "agent_name": "CMO", "status": "active", "last_active": "2025-04-12 13:45:00"},
    {"agent_id": 5, "agent_name": "COO", "status": "error", "last_active": "2025-04-11 16:30:00"},
]

recent_conversations = [
    {"conversation_id": 1, "user_id": "user1", "created_at": "2025-04-12 14:00:00", "updated_at": "2025-04-12 14:30:00"},
    {"conversation_id": 2, "user_id": "user2", "created_at": "2025-04-12 13:30:00", "updated_at": "2025-04-12 13:45:00"},
    {"conversation_id": 3, "user_id": "user3", "created_at": "2025-04-12 12:15:00", "updated_at": "2025-04-12 12:30:00"},
]

# Routes
@app.route('/')
def index():
    """Dashboard index page."""
    return render_template('dashboard/index.html', 
                          total_conversations=len(recent_conversations),
                          total_messages=25,
                          active_agents=4,
                          agent_statuses=agent_statuses,
                          recent_conversations=recent_conversations)

@app.route('/agents')
def agents():
    """Agents page."""
    return render_template('agents/index.html', agents=agent_statuses)

@app.route('/agents/<int:agent_id>')
def agent_detail(agent_id):
    """Agent detail page."""
    agent = next((a for a in agent_statuses if a["agent_id"] == agent_id), None)
    if not agent:
        flash("Agent not found", "danger")
        return redirect(url_for('agents'))
    return render_template('agents/detail.html', agent=agent)

@app.route('/kb')
def kb():
    """Knowledge base page."""
    return render_template('kb/index.html')

@app.route('/analytics')
def analytics():
    """Analytics page."""
    return render_template('analytics/index.html')

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            flash("Login successful", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "danger")
    return render_template('auth/login.html')

@app.route('/auth/logout')
def logout():
    """Logout page."""
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Web dashboard is running"})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """404 page."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 page."""
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    logger.info("Starting AI Executive Team Web Dashboard")
    app.run(host="0.0.0.0", port=3001, debug=True)
