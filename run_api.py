"""
Run the API server.
"""

import os
import logging
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import configuration
from config.app_config import (
    APP_NAME, APP_VERSION, APP_PORT,
    LOG_LEVEL, LOG_FORMAT
)

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting {APP_NAME} API server v{APP_VERSION}")
    uvicorn.run("api.app:app", host="0.0.0.0", port=APP_PORT, reload=True)
