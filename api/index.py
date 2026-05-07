import sys
import os

# Add the project root to the path so we can import from 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app
