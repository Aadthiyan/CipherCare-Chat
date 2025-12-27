import json

with open('synthea_structured_FIXED.json', 'r') as f:
    data = json.load(f)

pid199 = [x for x in data if x['patient_id']=='PID-199']
print(f'PID-199 has {len(pid199)} records')

if pid199:
    obs = [x for x in pid199 if x['record_type']=='observation' and 'glucose' in x.get('display','').lower()]
    print(f'Glucose observations: {len(obs)}')
    if obs:
        print(f'Sample: {obs[0].get("display")} = {obs[0].get("value")} {obs[0].get("unit")}')
