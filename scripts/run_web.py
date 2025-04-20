"""
Run the web dashboard.
"""

import os
import logging
from dotenv import load_dotenv
from web_dashboard import create_app

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting AI Executive Team Web Dashboard")
    app = create_app()
    app.run(host="0.0.0.0", port=3001, debug=True)
