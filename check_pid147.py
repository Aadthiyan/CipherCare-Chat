import json

def check_pid147():
    print("Checking PID-147...")
    with open('synthea_structured_FIXED.json', 'r') as f:
        data = json.load(f)
    
    # Filter
    pid147 = [x for x in data if x['patient_id'] == 'PID-147']
    print(f"Total records for PID-147: {len(pid147)}")
    
    meds = [x for x in pid147 if x['record_type'] == 'medication']
    print(f"Medications found: {len(meds)}")
    for m in meds:
        print(f" - {m.get('display')}")

if __name__ == "__main__":
    check_pid147()
