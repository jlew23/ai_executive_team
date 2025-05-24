"""
Supabase configuration for the AI Executive Team application.
This module provides the configuration and client for Supabase integration.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = None

def init_supabase():
    """Initialize the Supabase client."""
    global supabase
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and key must be provided in the .env file")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

def get_supabase_client():
    """Get the Supabase client."""
    global supabase
    
    if supabase is None:
        supabase = init_supabase()
    
    return supabase
