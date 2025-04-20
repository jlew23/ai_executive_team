"""
Web dashboard application for AI Executive Team.

This module provides a web interface for:
- Monitoring agent status
- Viewing conversation history
- Managing knowledge base
- User and permission management
- Analytics and reporting
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Load configuration
app.config.from_object('web_dashboard.config.Config')

# Set secret key for sessions
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key')

# Import and register blueprints
from web_dashboard.routes.auth import auth_bp
from web_dashboard.routes.dashboard import dashboard_bp
from web_dashboard.routes.agents import agents_bp
from web_dashboard.routes.knowledge_base import kb_bp
from web_dashboard.routes.analytics import analytics_bp
from web_dashboard.routes.admin import admin_bp
from web_dashboard.routes.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(agents_bp)
app.register_blueprint(kb_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "message": "Web dashboard is running"})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Context processors
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask application instance
    """
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
