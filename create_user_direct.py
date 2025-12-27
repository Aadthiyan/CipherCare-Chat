#!/usr/bin/env python3
"""Create test user directly in database"""

import os
from dotenv import load_dotenv
import psycopg2
import bcrypt

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Hash the password
    password = "Aadhithiyan@99"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Create user
    cursor.execute("""
        INSERT INTO users (username, email, full_name, password_hash, roles, assigned_patients, department, email_verified, is_active)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
        RETURNING id, username, email, full_name
    """, (
        "jsmith",
        "jsmith@hospital.com",
        "Dr. John Smith",
        password_hash,
        '["attending"]',
        '["any"]',
        "Internal Medicine",
        True,
        True
    ))
    
    user = cursor.fetchone()
    conn.commit()
    
    if user:
        print("✅ User created successfully!")
        print(f"   ID: {user[0]}")
        print(f"   Username: {user[1]}")
        print(f"   Email: {user[2]}")
        print(f"   Name: {user[3]}")
        print(f"\nLogin with:")
        print(f"   Username: jsmith")
        print(f"   Password: Aadhithiyan@99")
    else:
        print("❌ Failed to create user")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
