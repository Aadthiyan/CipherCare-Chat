#!/usr/bin/env python3
"""Analyze which patients are in the enriched JSON files."""

import json

def analyze_file(filename):
    """Analyze a patient JSON file and return patient IDs and their record counts."""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    patient_ids = set()
    # Handle both dict and list formats
    if isinstance(data, dict):
        data = list(data.values())
    
    for patient in data:
        if isinstance(patient, dict):
            patient_ids.add(patient.get('patient_id', 'UNKNOWN'))
    
    return sorted(patient_ids)

# Analyze both files
print("="*70)
print("ANALYZING ENRICHED JSON FILES")
print("="*70)

mimic_patients = analyze_file('mimic_patients_100.ready.json')
synthea_patients = analyze_file('synthea_patients_221.ready.json')

print(f"\n📋 MIMIC File: mimic_patients_100.ready.json")
print(f"   Total patients: {len(mimic_patients)}")
print(f"   Patient IDs: {mimic_patients}")

print(f"\n📋 Synthea File: synthea_patients_221.ready.json")
print(f"   Total patients: {len(synthea_patients)}")
print(f"   Patient IDs (first 50): {synthea_patients[:50]}")

# Combined analysis
all_patients = set(mimic_patients + synthea_patients)
print(f"\n📊 COMBINED ANALYSIS")
print(f"   Total unique patients in enriched files: {len(all_patients)}")
print(f"   MIMIC only: {len(set(mimic_patients) - set(synthea_patients))}")
print(f"   Synthea only: {len(set(synthea_patients) - set(mimic_patients))}")
print(f"   Overlap: {len(set(mimic_patients) & set(synthea_patients))}")

# Get expected patient count
print(f"\n📋 EXPECTED SUMMARY")
print(f"   MIMIC expected: 100 patients")
print(f"   Synthea expected: 221 patients")
print(f"   Total expected: 321 patients")
print(f"   Actually in files: {len(all_patients)}")
print(f"   Missing: {321 - len(all_patients)}")
