#!/usr/bin/env python3
"""Delete all users from the database"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Load .env from project root
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not found in .env file")
    sys.exit(1)

print(f"📝 Using DATABASE_URL: {DATABASE_URL[:50]}...")

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
    sys.exit(1)
