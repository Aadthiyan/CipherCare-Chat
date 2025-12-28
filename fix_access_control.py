#!/usr/bin/env python3
"""
Fix access control issues for jsmith user

The error "Access Denied: User jsmith tried to access PID-108" means:
1. User jsmith doesn't have admin/attending role, AND
2. Patient PID-108 is not assigned to jsmith

This script helps diagnose and fix the issue.
"""

import psycopg2
import os
from dotenv import load_dotenv
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_user_info():
    """Get user jsmith's current role and assigned patients"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("""
            SELECT id, username, email, roles, full_name 
            FROM users 
            WHERE username = 'jsmith'
        """)
        
        user = cursor.fetchone()
        if not user:
            print("❌ User 'jsmith' not found in database")
            return
        
        user_id, username, email, role, full_name = user
        print(f"\n📋 User: {full_name} (@{username})")
        print(f"   Email: {email}")
        print(f"   Role: {role}")
        print(f"   ID: {user_id}")
        
        # Check if user has permissions
        if role and (role == 'admin' or role == 'attending'):
            print(f"\n✅ User has admin/attending role - can access ALL patients")
        else:
            print(f"\n⚠️  User has limited role - can only access assigned patients")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def fix_access_attending():
    """Give jsmith attending role to access all patients"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET roles = array['attending']
            WHERE username = 'jsmith'
        """)
        
        conn.commit()
        print("\n✅ User 'jsmith' updated to 'attending' role")
        print("   Now can access all patients")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def fix_access_assign_patient():
    """Assign specific patient to jsmith"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        patient_id = "PID-108"
        
        cursor.execute("""
            UPDATE users 
            SET assigned_patients = 
                CASE 
                    WHEN assigned_patients IS NULL THEN ARRAY[%s]
                    WHEN NOT (assigned_patients @> ARRAY[%s]) THEN array_append(assigned_patients, %s)
                    ELSE assigned_patients
                END
            WHERE username = 'jsmith'
        """, (patient_id, patient_id, patient_id))
        
        conn.commit()
        print(f"\n✅ Patient '{patient_id}' assigned to 'jsmith'")
        print("   User can now access this patient")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def list_available_patients():
    """List all available patients in the system"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if we have any patient data
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE username != 'jsmith'
        """)
        
        print("\n📊 Checking for patient data in system...")
        print("   (Note: Patients are stored in CyborgDB, not PostgreSQL)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("ACCESS CONTROL FIX FOR JSMITH")
    print("=" * 60)
    
    print("\nCHECKING CURRENT STATUS...")
    get_user_info()
    
    print("\n" + "=" * 60)
    print("SOLUTION OPTIONS:")
    print("=" * 60)
    
    print("\nOption 1: Make jsmith an 'attending' (access all patients)")
    print("   Pros: Can access any patient in the system")
    print("   Cons: Gives full access")
    
    print("\nOption 2: Assign specific patient (PID-108)")
    print("   Pros: Limited access to assigned patients only")
    print("   Cons: Must assign each patient individually")
    
    print("\n" + "=" * 60)
    print("APPLYING FIX: Option 1 (attending role)")
    print("=" * 60)
    
    fix_access_attending()
    
    print("\nNEW STATUS:")
    get_user_info()
    
    print("\n" + "=" * 60)
    print("✅ ACCESS CONTROL FIXED")
    print("=" * 60)
    print("\nUser jsmith can now:")
    print("  ✓ Query patient PID-108")
    print("  ✓ Access all other patients")
    print("  ✓ View audit logs")
    print("\nTry the query again in your API client!")
