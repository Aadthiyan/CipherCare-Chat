#!/usr/bin/env python3
"""Check why jsmith can't access PID-108"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("\n=== USER jsmith STATUS ===")
    cursor.execute("""
        SELECT username, email_verified, roles, assigned_patients 
        FROM users 
        WHERE username = 'jsmith'
    """)
    
    result = cursor.fetchone()
    if result:
        username, email_verified, roles, assigned = result
        print(f"Username: {username}")
        print(f"Email Verified: {email_verified}")
        print(f"Roles: {roles}")
        print(f"Assigned Patients: {assigned}")
        
        # Check role
        if roles and 'attending' in roles:
            print("\n✅ User IS attending - should have access to all patients")
        else:
            print("\n❌ User is NOT attending")
    else:
        print("❌ User jsmith not found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
