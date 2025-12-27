"""
Quick check of how many records are in patient_records collection
"""
import os
from dotenv import load_dotenv

load_dotenv()

from backend.cyborg_lite_manager import get_cyborg_manager

def count_records():
    print("\n=== Checking patient_records collection ===\n")
    
    manager = get_cyborg_manager()
    
    try:
        index = manager.get_index("patient_records")
        
        # Get a large sample to count
        zero_embedding = [0.01] * 768
        results = index.query(query_vectors=[zero_embedding], top_k=20000)
        
        total = len(results)
        
        # Count by record type
        conditions = sum(1 for r in results if r.get('metadata', {}).get('record_type') == 'condition')
        medications = sum(1 for r in results if r.get('metadata', {}).get('record_type') == 'medication')
        observations = sum(1 for r in results if r.get('metadata', {}).get('record_type') == 'observation')
        patient_summary = sum(1 for r in results if r.get('metadata', {}).get('record_type') == 'patient_summary')
        
        # Count unique patients
        unique_patients = len(set(r.get('metadata', {}).get('patient_id') for r in results if r.get('metadata', {}).get('patient_id')))
        
        print(f"✅ Total Records: {total:,}")
        print(f"\nBreakdown by type:")
        print(f"  - Patient Summaries: {patient_summary}")
        print(f"  - Conditions: {conditions}")
        print(f"  - Medications: {medications}")
        print(f"  - Observations: {observations}")
        print(f"\n👥 Unique Patients: {unique_patients}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    count_records()
