#!/usr/bin/env python3
"""Check and fix jsmith user permissions"""

import os
from dotenv import load_dotenv
import psycopg2
import json

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check current user
    cursor.execute("""
        SELECT id, username, roles, assigned_patients FROM users WHERE username = 'jsmith'
    """)
    
    user = cursor.fetchone()
    
    if user:
        user_id, username, roles, assigned_patients = user
        print("Current User Status:")
        print(f"  Username: {username}")
        print(f"  Roles: {roles}")
        print(f"  Assigned Patients: {assigned_patients}")
        
        # Update to give access to all patients (attending role)
        cursor.execute("""
            UPDATE users 
            SET roles = %s::jsonb, assigned_patients = %s::jsonb
            WHERE id = %s
        """, (
            '["attending"]',
            '["any"]',
            user_id
        ))
        conn.commit()
        
        print("\n✅ Updated jsmith to have attending role with access to ALL patients")
        print("  New Roles: ['attending']")
        print("  New Assigned Patients: ['any']")
        
    else:
        print("❌ User jsmith not found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
