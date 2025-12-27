#!/usr/bin/env python3
"""Load real patient data and convert to API format"""

import json
from pathlib import Path

def load_real_patients():
    """Load real Synthea patient data"""
    
    # Check for Synthea patient file
    patient_file = Path("synthea_patients_221.json")
    
    if not patient_file.exists():
        print(f"❌ Patient file not found: {patient_file}")
        return []
    
    try:
        with open(patient_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Loaded patient file: {patient_file}")
        print(f"   Type: {type(data)}")
        
        if isinstance(data, dict):
            # Check for different possible structures
            if 'patients' in data:
                patients = data['patients']
                print(f"   Found 'patients' key with {len(patients)} entries")
            elif 'entries' in data:
                patients = data['entries']
                print(f"   Found 'entries' key with {len(patients)} entries")
            else:
                print(f"   Top-level keys: {list(data.keys())[:5]}")
                patients = []
        elif isinstance(data, list):
            patients = data
            print(f"   Data is list with {len(patients)} entries")
        else:
            print(f"   Unexpected data type: {type(data)}")
            patients = []
        
        # Show sample structure
        if patients:
            print(f"\n   Sample patient structure:")
            sample = patients[0] if isinstance(patients, list) else list(patients.values())[0]
            if isinstance(sample, dict):
                print(f"   Keys: {list(sample.keys())[:10]}")
                print(f"\n   Full sample:")
                print(json.dumps(sample, indent=2)[:500])
        
        return patients
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return []

if __name__ == "__main__":
    patients = load_real_patients()
    print(f"\n✅ Total patients: {len(patients)}")
