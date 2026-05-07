"""
Configuration module for MCP Server.

This module handles configuration for backend API connection.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Backend API URL
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')

def get_backend_url() -> str:
    """
    Get the backend API base URL.
    
    Returns:
        str: Backend API base URL
    """
    return BACKEND_URL
