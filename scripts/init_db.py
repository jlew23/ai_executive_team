"""
Initialize the database for the web dashboard.
"""

import os
import logging
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database."""
    from web_dashboard import create_app
    from web_dashboard.models import init_db as init_database
    
    logger.info("Initializing database...")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Initialize database
        init_database(app)
        
    logger.info("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
