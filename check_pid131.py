import json

with open('synthea_structured_FIXED.json', 'r') as f:
    data = json.load(f)

patients = sorted(set([x['patient_id'] for x in data]))
print(f'Total patients: {len(patients)}')
print(f'First 10: {patients[:10]}')
print(f'Last 10: {patients[-10:]}')
print(f'PID-131 exists: {"PID-131" in patients}')

if "PID-131" in patients:
    pid131_records = [x for x in data if x['patient_id'] == 'PID-131']
    print(f'PID-131 has {len(pid131_records)} records')
