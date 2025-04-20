"""
Configuration settings for the web dashboard.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Database settings
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///ai_executive_team.db')
    
    # API settings
    API_TOKEN_EXPIRATION = timedelta(days=30)
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/ai_executive_team_uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Agent settings
    AGENT_TIMEOUT = int(os.environ.get('AGENT_TIMEOUT', '30'))  # seconds
    
    # LLM settings
    DEFAULT_LLM_PROVIDER = os.environ.get('DEFAULT_LLM_PROVIDER', 'openai')
    DEFAULT_LLM_MODEL = os.environ.get('DEFAULT_LLM_MODEL', 'gpt-4')
    
    # Knowledge base settings
    KB_STORAGE_PATH = os.environ.get('KB_STORAGE_PATH', '/tmp/ai_executive_team_kb')
    
    # Analytics settings
    ANALYTICS_RETENTION_DAYS = int(os.environ.get('ANALYTICS_RETENTION_DAYS', '90'))

class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
class TestingConfig(Config):
    """Testing configuration."""
    
    DEBUG = False
    TESTING = True
    DATABASE_URI = 'sqlite:///:memory:'
    
class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # Use stronger secret key in production
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No FLASK_SECRET_KEY set for production environment")

# Select configuration based on environment
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

Config = config_map.get(os.environ.get('FLASK_ENV', 'development'), DevelopmentConfig)
