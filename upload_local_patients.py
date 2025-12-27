#!/usr/bin/env python3
"""Upload sample patient data to local CyborgDB Lite instance"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

# Local CyborgDB Lite endpoint
CYBORG_LITE_URL = "http://localhost:8002"
COLLECTION_NAME = "patient_records"

def upload_sample_patients():
    """Upload sample patient records to local CyborgDB"""
    
    sample_patients = {
        "PID-001": {
            "text": "John Doe, 45-year-old male with Type 2 Diabetes, hypertension, and hyperlipidemia. Recent lab work shows glucose 180 mg/dL, HbA1c 8.5%.",
            "metadata": {
                "patient_id": "PID-001",
                "name": "John Doe",
                "age": 45,
                "gender": "Male",
                "birth_date": "1979-12-26",
                "primary_condition": "Type 2 Diabetes",
                "conditions": ["Type 2 Diabetes", "Hypertension", "Hyperlipidemia"],
                "num_conditions": 3,
                "num_medications": 5,
                "pcp": "Dr. Sarah Johnson",
                "phone": "555-0101",
                "email": "john.doe@email.com",
                "address": "123 Main St, Boston, MA",
                "last_visit": "2024-12-20",
                "risk_level": "Medium"
            }
        },
        "PID-002": {
            "text": "Sarah Connor, 29-year-old female with well-controlled hypertension on lisinopril. BP consistently 130/80. No other significant medical history.",
            "metadata": {
                "patient_id": "PID-002",
                "name": "Sarah Connor",
                "age": 29,
                "gender": "Female",
                "birth_date": "1995-06-15",
                "primary_condition": "Hypertension",
                "conditions": ["Hypertension"],
                "num_conditions": 1,
                "num_medications": 1,
                "pcp": "Dr. Michael Chen",
                "phone": "555-0102",
                "email": "sarah.connor@email.com",
                "address": "456 Oak Ave, Boston, MA",
                "last_visit": "2024-12-18",
                "risk_level": "Low"
            }
        },
        "PID-003": {
            "text": "Michael Smith, 62-year-old male with COPD, former smoker. FEV1/FVC ratio 0.65. On albuterol and tiotropium inhalers. Recent exacerbation in October.",
            "metadata": {
                "patient_id": "PID-003",
                "name": "Michael Smith",
                "age": 62,
                "gender": "Male",
                "birth_date": "1962-04-10",
                "primary_condition": "COPD",
                "conditions": ["COPD", "Smoking History"],
                "num_conditions": 2,
                "num_medications": 3,
                "pcp": "Dr. Emily Brown",
                "phone": "555-0103",
                "email": "michael.smith@email.com",
                "address": "789 Elm St, Boston, MA",
                "last_visit": "2024-12-22",
                "risk_level": "High"
            }
        },
        "PID-004": {
            "text": "Emily Blunt, 34-year-old female with chronic migraine, currently on sumatriptan as needed. Frequency increased to 3-4 migraines per month.",
            "metadata": {
                "patient_id": "PID-004",
                "name": "Emily Blunt",
                "age": 34,
                "gender": "Female",
                "birth_date": "1990-08-22",
                "primary_condition": "Migraine",
                "conditions": ["Chronic Migraine"],
                "num_conditions": 1,
                "num_medications": 2,
                "pcp": "Dr. Robert Lee",
                "phone": "555-0104",
                "email": "emily.blunt@email.com",
                "address": "321 Pine Rd, Boston, MA",
                "last_visit": "2024-11-30",
                "risk_level": "Low"
            }
        },
        "PID-005": {
            "text": "Robert Stark, 55-year-old male with history of arrhythmia, now on metoprolol and amiodarone. Recent ECG shows normal sinus rhythm. Uses pacemaker.",
            "metadata": {
                "patient_id": "PID-005",
                "name": "Robert Stark",
                "age": 55,
                "gender": "Male",
                "birth_date": "1969-10-05",
                "primary_condition": "Arrhythmia",
                "conditions": ["Arrhythmia", "Pacemaker"],
                "num_conditions": 2,
                "num_medications": 4,
                "pcp": "Dr. Michael Chen",
                "phone": "555-0105",
                "email": "robert.stark@email.com",
                "address": "654 Cedar Ln, Boston, MA",
                "last_visit": "2024-12-21",
                "risk_level": "Medium"
            }
        }
    }
    
    print("\n" + "="*60)
    print("UPLOADING SAMPLE PATIENTS TO LOCAL CYBORGDB")
    print("="*60)
    
    successful = 0
    failed = 0
    
    for patient_id, patient_data in sample_patients.items():
        try:
            # Prepare upsert payload
            payload = {
                "ids": [patient_id],
                "documents": [patient_data["text"]],
                "embeddings": [[0.0] * 768],  # Placeholder, CyborgDB will embed it
                "metadatas": [patient_data["metadata"]]
            }
            
            # Upload to local CyborgDB
            url = f"{CYBORG_LITE_URL}/collections/{COLLECTION_NAME}/upsert"
            response = requests.post(url, json=payload)
            
            if response.status_code in [200, 201]:
                print(f"✅ {patient_id} - {patient_data['metadata']['name']}")
                successful += 1
            else:
                print(f"❌ {patient_id} - Error {response.status_code}: {response.text}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {patient_id} - Exception: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"UPLOAD COMPLETE: {successful} successful, {failed} failed")
    print("="*60)
    print("\nPatients should now appear in the dashboard!")
    print("Refresh the page to see them.\n")
    
    return successful > 0

if __name__ == "__main__":
    try:
        success = upload_sample_patients()
        if not success:
            print("⚠️  Warning: No patients uploaded. Is CyborgDB running at localhost:8002?")
            print("   Start it with: docker run -p 8002:8000 cyborgdb/lite")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Is CyborgDB Lite running? Make sure backend is running (python run_backend.py)")
