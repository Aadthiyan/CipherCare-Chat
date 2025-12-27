#!/usr/bin/env python3
"""
Upload encrypted patient data to CyborgDB
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from backend.cyborg_manager import CyborgDBManager

if __name__ == "__main__":
    print("=" * 60)
    print("CipherCare Data Upload Utility")
    print("=" * 60)
    
    try:
        print("\n1. Initializing CyborgDBManager...")
        db = CyborgDBManager()
        print("   ✓ Database connection successful")
        
        print("\n2. Uploading encrypted patient data...")
        print("   File: data/processed/deidentified_dataset.json")
        db.upload_encrypted_data('data/processed/deidentified_dataset.json')
        
        print("\n3. Verifying data...")
        count = len(db.get_all_patient_ids())
        print(f"   ✓ Total patients in database: {count}")
        
        print("\n" + "=" * 60)
        print("✓ Data Upload Complete!")
        print("=" * 60)
        print("\nYou can now query the database. Try:")
        print("  python test_query.py")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
