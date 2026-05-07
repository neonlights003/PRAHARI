#!/usr/bin/env python3
"""
Clear all data from PostgreSQL database tables
"""

import backend.db_config as db_config

print("🗑️  Clearing all data from PostgreSQL database...")

try:
    conn = db_config.get_connection()
    cursor = conn.cursor()
    
    # List of tables to clear (in order to respect foreign key constraints)
    tables = [
        'comparison_messages',
        'comparison_chat_pdfs',
        'comparison_chats',
        'messages',
        'client_dprs',
        'dprs',
        'projects',
        'users'
    ]
    
    # Truncate all tables
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        print(f"  ✓ Cleared table: {table}")
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print("\n✅ All data cleared successfully!")
    print("📊 Database is now empty and ready for fresh data")
    
except Exception as e:
    print(f"\n❌ Error clearing data: {str(e)}")
    import traceback
    traceback.print_exc()
