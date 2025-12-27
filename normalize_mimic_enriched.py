#!/usr/bin/env python3
"""
Normalize MIMIC enriched file to match Synthea flat structure
"""
import json

print("Loading mimic_patients_100.ready.json...")
with open('mimic_patients_100.ready.json', 'r') as f:
    data = json.load(f)

# Convert from dict to list and normalize
if isinstance(data, dict):
    patients = list(data.values())
else:
    patients = data
normalized = []

for patient_data in patients:
    # Extract patient_id from nested 'patient' key
    patient_info = patient_data.get('patient', {})
    patient_id = patient_info.get('id', 'UNKNOWN')
    
    # Flatten to match Synthea structure
    normalized_patient = {
        'patient_id': patient_id,
        'name': patient_info.get('text', {}).get('value', 'Unknown') if isinstance(patient_info.get('text'), dict) else 'Unknown',
        'demographics': patient_data.get('demographics', {
            'gender': patient_info.get('gender', 'unknown'),
            'birthDate': patient_info.get('birthDate', 'unknown')
        }),
        'conditions': patient_data.get('conditions', []),
        'medications': patient_data.get('medications', []),
        'observations': patient_data.get('observations', []),
        'clinical_text': patient_data.get('clinical_text', ''),
        'original_id': patient_info.get('identifier', [{}])[0].get('value', 'unknown') if patient_info.get('identifier') else 'unknown'
    }
    
    normalized.append(normalized_patient)

print(f"Normalized {len(normalized)} patients")

# Write back as flat list (like Synthea)
with open('mimic_patients_100.ready.json', 'w') as f:
    json.dump(normalized, f, indent=2)

print("✅ Normalized mimic_patients_100.ready.json")
print(f"Sample patient_id: {normalized[0].get('patient_id')}")
