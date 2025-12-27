"""
Check what data exists for PID-101 in the uploaded records
"""

import json

# Load the FIXED data
with open('synthea_structured_FIXED.json', 'r') as f:
    data = json.load(f)

# Filter for PID-101
pid101 = [r for r in data if r['patient_id'] == 'PID-101']
print(f"PID-101 records in file: {len(pid101)}")

# Find glucose records
glucose = [r for r in pid101 if 'glucose' in r.get('display', '').lower()]
print(f"\nGlucose records for PID-101: {len(glucose)}")

if glucose:
    print("\nSample glucose record:")
    print(json.dumps(glucose[0], indent=2))
else:
    print("\n❌ No glucose records found!")
    print("\nSample observation:")
    obs = [r for r in pid101 if r.get('record_type') == 'observation']
    if obs:
        print(json.dumps(obs[0], indent=2))
