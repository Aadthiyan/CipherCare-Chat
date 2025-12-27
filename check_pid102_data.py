import json

with open('synthea_structured_FIXED.json', 'r') as f:
    data = json.load(f)

pid102_obs = [x for x in data if x['patient_id']=='PID-102' and x['record_type']=='observation'][:5]

print(f"Found {len(pid102_obs)} observations for PID-102")
print("\nSample observations:")
for r in pid102_obs:
    print(f"  {r.get('display')}: value={r.get('value')}, unit={r.get('unit')}")

# Check the full structure of one record
if pid102_obs:
    print("\nFull structure of first observation:")
    print(json.dumps(pid102_obs[0], indent=2))
