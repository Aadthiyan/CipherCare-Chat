#!/usr/bin/env python3
"""Quick fix for jsmith access control"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("\n=== CHECKING USER jsmith ===")
    cursor.execute("""SELECT username, roles FROM users WHERE username = 'jsmith'""")
    result = cursor.fetchone()
    
    if result:
        user, roles = result
        print(f"Current roles: {roles}")
    
    print("\n=== UPDATING TO ATTENDING ===")
    cursor.execute("""UPDATE users SET roles = array['attending'] WHERE username = 'jsmith'""")
    conn.commit()
    
    cursor.execute("""SELECT username, roles FROM users WHERE username = 'jsmith'""")
    result = cursor.fetchone()
    user, roles = result
    print(f"New roles: {roles}")
    print("\n✅ FIXED! User can now access all patients")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
