#!/usr/bin/env python3
"""Get patient record statistics from the backend."""

import requests
import json

def main():
    # Login
    login_url = "http://127.0.0.1:8000/auth/login"
    login_data = {
        "username": "jsmith",
        "password": "Aadhithiyan@99"
    }
    
    print("🔐 Logging in...")
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    tokens = login_response.json()
    access_token = tokens.get("access_token")
    print(f"✅ Login successful\n")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get patient IDs - Using the internal debug endpoint
    print("📊 Fetching all patient IDs and record counts...")
    
    # We'll test a range of patient IDs to see which ones have data
    test_patients = [f"PID-{i}" for i in range(100, 351)]
    
    patient_records = {}
    
    for patient_id in test_patients:
        # Try a simple query to see if patient exists and has records
        query_url = "http://127.0.0.1:8000/api/v1/query"
        query_data = {
            "patient_id": patient_id,
            "question": "Summary",
            "retrieve_k": 100  # Get as many sources as possible
        }
        
        try:
            response = requests.post(query_url, json=query_data, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                sources = data.get("sources", [])
                record_count = len(sources)
                patient_records[patient_id] = record_count
        except:
            pass
    
    # Display results
    print(f"\n{'Patient ID':<15} {'Records':<12} {'Status'}")
    print("-" * 40)
    
    sorted_patients = sorted(patient_records.items(), key=lambda x: x[1], reverse=True)
    for patient_id, count in sorted_patients:
        status = "✅ Has data" if count > 0 else "❌ No data"
        print(f"{patient_id:<15} {count:<12} {status}")
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    with_data = sum(1 for count in patient_records.values() if count > 0)
    without_data = sum(1 for count in patient_records.values() if count == 0)
    total_records = sum(patient_records.values())
    avg_records = total_records / len(patient_records) if patient_records else 0
    
    print(f"Total patients queried: {len(patient_records)}")
    print(f"Patients with records: {with_data}")
    print(f"Patients without records: {without_data}")
    print(f"Total records returned: {total_records}")
    print(f"Average records per patient: {avg_records:.1f}")

if __name__ == "__main__":
    main()
