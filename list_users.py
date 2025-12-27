#!/usr/bin/env python3
"""Check what users exist in the database"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("\n=== USERS IN DATABASE ===\n")
    cursor.execute("""
        SELECT username, email, full_name, email_verified, roles 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    for row in results:
        username, email, full_name, verified, roles = row
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Name: {full_name}")
        print(f"Verified: {verified}")
        print(f"Roles: {roles}")
        print()
    
    if not results:
        print("❌ No users found! Create a new account via signup")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
