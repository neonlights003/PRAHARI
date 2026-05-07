import os
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'dpr_analyzer'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Connection pool (for better performance in production)
connection_pool = None

def init_connection_pool():
    """Initialize the connection pool."""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1,  # Minimum connections
            10,  # Maximum connections
            **DB_CONFIG
        )
        print("✓ PostgreSQL connection pool initialized")
    except Exception as e:
        print(f"✗ Failed to initialize connection pool: {e}")
        raise

def get_connection():
    """
    Get a database connection from the pool.
    Returns a psycopg2 connection object.
    """
    if connection_pool is None:
        init_connection_pool()
    
    try:
        conn = connection_pool.getconn()
        return conn
    except Exception as e:
        print(f"✗ Failed to get connection from pool: {e}")
        # Fallback to direct connection
        return psycopg2.connect(**DB_CONFIG)

def release_connection(conn):
    """Return a connection to the pool."""
    if connection_pool:
        connection_pool.putconn(conn)
    else:
        conn.close()

def get_cursor(conn, dict_cursor=True):
    """
    Get a cursor from a connection.
    
    Args:
        conn: psycopg2 connection object
        dict_cursor: If True, returns RealDictCursor (rows as dicts)
                    If False, returns regular cursor (rows as tuples)
    """
    if dict_cursor:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        return conn.cursor()

def close_connection_pool():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("✓ Connection pool closed")
