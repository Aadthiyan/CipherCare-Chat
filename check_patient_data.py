#!/usr/bin/env python3
"""Check what patient data exists in the system"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print("\n" + "="*60)
print("CHECKING PATIENT DATA IN SYSTEM")
print("="*60)

try:
    # Check PostgreSQL for patient metadata
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("\n1️⃣  Checking PostgreSQL users table...")
    cursor.execute("""
        SELECT COUNT(*) as total FROM users
    """)
    user_count = cursor.fetchone()[0]
    print(f"   Users in database: {user_count}")
    
    # Check for patient data files
    print("\n2️⃣  Checking for patient data files...")
    
    import glob
    
    patterns = [
        'data/**/*.json',
        '*.json',
        'synthetic/**/*.json',
        'mimic/**/*.json',
    ]
    
    patient_files = []
    for pattern in patterns:
        patient_files.extend(glob.glob(pattern, recursive=True))
    
    patient_files = list(set([f for f in patient_files if 'patient' in f.lower() or 'synthea' in f.lower() or 'mimic' in f.lower()]))
    
    if patient_files:
        print(f"   Found {len(patient_files)} patient data files:")
        for f in patient_files[:5]:  # Show first 5
            print(f"      - {f}")
    else:
        print("   No patient data files found")
    
    # Check CyborgDB collections
    print("\n3️⃣  Checking CyborgDB for patient records...")
    
    try:
        from backend.services import services
        db = services.get("db")
        
        if db:
            print("   CyborgDB is connected")
            # Try to list collections
            print("   (Note: Collection data would need direct CyborgDB query)")
        else:
            print("   CyborgDB service not initialized")
    except Exception as e:
        print(f"   Cannot check CyborgDB: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("RECOMMENDATION:")
    print("="*60)
    print("""
To upload patient data:

1. Option A - Quick Sample Data:
   python -c "
from backend.upload_to_cyborgdb import CyborgDBUploader
uploader = CyborgDBUploader()
uploader.upload_sample_patients()
   "

2. Option B - Convert Synthea Data:
   python convert_synthea_to_cipercare.py

3. Option C - Convert MIMIC Data:
   python convert_mimic_to_cipercare.py

4. Option D - Upload Existing File:
   python upload_patient_data.py <filename.json>
   """)
    
except Exception as e:
    print(f"❌ Error: {e}")

print()
