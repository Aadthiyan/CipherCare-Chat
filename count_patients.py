"""Count unique patients in the system"""
import json

with open('synthea_structured_FIXED.json', 'r') as f:
    data = json.load(f)

patients = sorted(set([x['patient_id'] for x in data]))

print(f"Total unique patients: {len(patients)}")
print(f"Total records: {len(data)}")
print(f"Average records per patient: {len(data) / len(patients):.1f}")
print(f"\nPatient ID range:")
print(f"  First: {patients[0]}")
print(f"  Last: {patients[-1]}")
print(f"\nSample of 10 patients:")
for i in range(0, len(patients), len(patients)//10):
    print(f"  {patients[i]}")
