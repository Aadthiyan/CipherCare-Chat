#!/usr/bin/env python3
"""Delete all users from the database"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Delete all users
    cursor.execute("DELETE FROM users")
    conn.commit()
    
    # Check count
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    print(f"✅ All users deleted!")
    print(f"   Users remaining: {count}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
