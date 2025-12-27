"""
Parse the pre-processed synthea_patients_221.json format correctly
This data already has LOINC codes and proper structure - just needs reformatting
"""

import json
from pathlib import Path
from typing import List, Dict
import uuid
from datetime import datetime


def parse_preprocessed_synthea(input_file: str = "synthea_patients_221.json", limit: int = 1000):
    """Parse pre-processed Synthea data to structured format"""
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    all_records = []
    record_count = 0
    
    for patient_id, patient_data in data.items():
        if limit and record_count >= limit:
            break
        
        # Parse observations
        for obs in patient_data.get('observations', []):
            if limit and record_count >= limit:
                break
            
            record = {
                "patient_id": patient_id,
                "record_id": f"obs-{uuid.uuid4()}",
                "record_type": "observation",
                "data_source": "Synthea",
                "created_at": obs.get('date', datetime.now().isoformat()),
                "effective_date": obs.get('date', datetime.now().isoformat()),
                "provenance": "synthea-generator",
                "language": "en",
                
                "code": {
                    "system": "LOINC",
                    "code": obs.get('code', 'unknown'),
                    "display": obs.get('display', 'Unknown')
                },
                "display": obs.get('display', 'Unknown'),
                "loinc_code": obs.get('code', 'unknown'),
                
                "value": obs.get('value'),
                "value_normalized": obs.get('value'),
                "unit": obs.get('unit', ''),
                "value_type": "Quantity" if obs.get('value') else "String",
                "status": "final",
                
                "text_for_embedding": f"{obs.get('date', 'Unknown')}: {obs.get('display', 'Unknown')} {obs.get('value', '')} {obs.get('unit', '')}".strip(),
                "text_summary": f"{obs.get('display', 'Unknown')}: {obs.get('value', '')} {obs.get('unit', '')}".strip()
            }
            
            all_records.append(record)
            record_count += 1
        
        # Parse conditions
        for cond in patient_data.get('conditions', []):
            if limit and record_count >= limit:
                break
            
            record = {
                "patient_id": patient_id,
                "record_id": f"cond-{uuid.uuid4()}",
                "record_type": "condition",
                "data_source": "Synthea",
                "created_at": cond.get('onset', datetime.now().isoformat()),
                "effective_date": cond.get('onset', datetime.now().isoformat()),
                "provenance": "synthea-generator",
                "language": "en",
                
                "code": {
                    "system": "SNOMED-CT",
                    "code": cond.get('code', 'unknown'),
                    "display": cond.get('display', 'Unknown')
                },
                "display": cond.get('display', 'Unknown'),
                "snomed_code": cond.get('code', 'unknown'),
                "status": cond.get('status', 'active'),
                
                "text_for_embedding": f"{cond.get('onset', 'Unknown')}: {cond.get('display', 'Unknown')} (status: {cond.get('status', 'active')})",
                "text_summary": cond.get('display', 'Unknown')
            }
            
            all_records.append(record)
            record_count += 1
        
        # Parse medications
        for med in patient_data.get('medications', []):
            if limit and record_count >= limit:
                break
            
            record = {
                "patient_id": patient_id,
                "record_id": f"med-{uuid.uuid4()}",
                "record_type": "medication",
                "data_source": "Synthea",
                "created_at": datetime.now().isoformat(),
                "effective_date": datetime.now().isoformat(),
                "provenance": "synthea-generator",
                "language": "en",
                
                "medication_code": {
                    "system": "RxNorm",
                    "code": med.get('code', 'unknown'),
                    "display": med.get('display', 'Unknown')
                },
                "display": med.get('display', 'Unknown'),
                "rxnorm_code": med.get('code', 'unknown'),
                "status": med.get('status', 'active'),
                
                "text_for_embedding": f"{med.get('display', 'Unknown')} (status: {med.get('status', 'active')})",
                "text_summary": med.get('display', 'Unknown')
            }
            
            all_records.append(record)
            record_count += 1
    
    print(f"Created {len(all_records)} structured records")
    
    # Save
    output_file = "synthea_structured_FIXED.json"
    with open(output_file, 'w') as f:
        json.dump(all_records, f, indent=2)
    
    print(f"Saved to: {output_file}")
    
    # Stats
    by_type = {}
    for r in all_records:
        rtype = r['record_type']
        by_type[rtype] = by_type.get(rtype, 0) + 1
    
    print("\nRecord types:")
    for rtype, count in sorted(by_type.items()):
        print(f"  {rtype}: {count}")
    
    # Show sample
    print("\nSample observation:")
    obs_sample = [r for r in all_records if r['record_type'] == 'observation'][0]
    print(json.dumps(obs_sample, indent=2))
    
    return all_records


if __name__ == "__main__":
    # Limit=0 means NO LIMIT (Parse all 111,060 records)
    parse_preprocessed_synthea(limit=0)
    print("\n✓ Full dataset generated! Now run: python upload_incremental.py")
