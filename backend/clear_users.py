"""
Script to clear the users table for bcrypt migration.
Run this after implementing bcrypt password hashing to ensure all 
old plain-text passwords are removed.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backend.db_config as db_config

def clear_users_table():
    """Delete all users from the users table."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    try:
        # First check how many users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"📊 Found {count} user(s) in the database")
        
        if count == 0:
            print("✓ No users to delete. Table is already empty.")
            return True
        
        # Delete all users
        cursor.execute("DELETE FROM users")
        conn.commit()
        
        print(f"✓ Successfully deleted {count} user(s) from the users table")
        print("✓ Users can now register with bcrypt-hashed passwords")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error clearing users table: {str(e)}")
        return False
        
    finally:
        cursor.close()
        db_config.release_connection(conn)


if __name__ == "__main__":
    print("=" * 50)
    print("USERS TABLE CLEANUP FOR BCRYPT MIGRATION")
    print("=" * 50)
    print()
    
    # Confirm before proceeding
    response = input("⚠️  This will DELETE ALL existing users. Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = clear_users_table()
        if success:
            print()
            print("✅ Migration complete! Users can now register with secure passwords.")
    else:
        print("❌ Operation cancelled.")
