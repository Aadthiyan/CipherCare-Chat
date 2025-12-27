#!/usr/bin/env python3
"""Verify user and test login"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("""
        SELECT id, username, email, full_name, email_verified FROM users WHERE username = 'jsmith'
    """)
    
    user = cursor.fetchone()
    
    if user:
        print("✅ User found:")
        print(f"   ID: {user[0]}")
        print(f"   Username: {user[1]}")
        print(f"   Email: {user[2]}")
        print(f"   Full Name: {user[3]}")
        print(f"   Email Verified: {user[4]}")
    else:
        print("❌ User not found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
