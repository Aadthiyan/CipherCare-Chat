#!/usr/bin/env python3
"""Check record counts for ALL patients in the index."""

import os
import sys
from backend.cyborg_lite_manager import CyborgLiteManager

def main():
    # Initialize manager
    manager = CyborgLiteManager()
    
    # Get all patient IDs
    all_patient_ids = manager.get_all_patient_ids()
    print(f"Total unique patients in index: {len(all_patient_ids)}")
    print("\n" + "="*70)
    print("RECORD COUNTS FOR ALL PATIENTS")
    print("="*70 + "\n")
    
    # Get record counts for each
    patient_records = {}
    for patient_id in all_patient_ids:
        count = manager.get_patient_records_count(patient_id)
        patient_records[patient_id] = count
    
    # Sort by record count (descending)
    sorted_patients = sorted(patient_records.items(), key=lambda x: x[1], reverse=True)
    
    # Display all
    print(f"{'Patient ID':<15} {'Records':<12} {'Status'}")
    print("-" * 40)
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
    
    print(f"Total patients in index: {len(patient_records)}")
    print(f"Patients with records: {with_data}")
    print(f"Patients without records: {without_data}")
    print(f"Total records across all patients: {total_records}")
    print(f"Average records per patient: {avg_records:.1f}")
    
    # Record distribution
    print("\nRecord Distribution:")
    ranges = [(0, 0), (1, 10), (11, 50), (51, 100), (101, 1000)]
    for low, high in ranges:
        if low == high:
            count = sum(1 for c in patient_records.values() if c == 0)
            print(f"  {low} records: {count} patients")
        else:
            count = sum(1 for c in patient_records.values() if low <= c <= high)
            print(f"  {low}-{high} records: {count} patients")

if __name__ == "__main__":
    main()
