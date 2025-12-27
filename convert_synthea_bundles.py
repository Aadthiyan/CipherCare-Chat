"""
Quick script to convert Synthea FHIR Bundle JSON files to CipherCare format
"""
import json
import os
from pathlib import Path

def convert_synthea_bundles(input_dir, output_file="synthea_converted.json", start_pid=1):
    """Convert all Synthea bundle files with unified PID format
    
    Args:
        input_dir: Directory containing Synthea bundle JSON files
        output_file: Output JSON filename
        start_pid: Starting PID number (default 1, use higher if combining with MIMIC)
    """
    
    input_path = Path(input_dir)
    all_patients = {}
    
    # Get all JSON files
    json_files = list(input_path.glob("*.json"))
    print(f"📁 Found {len(json_files)} patient bundle files")
    print(f"🔢 Starting PID numbering from: PID-{start_pid:03d}")
    
    pid_counter = start_pid
    
    for i, json_file in enumerate(json_files, 1):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                bundle = json.load(f)
            
            if bundle.get('resourceType') != 'Bundle':
                continue
            
            # Extract resources from bundle
            patient_data = {
                'patient_id': None,
                'name': 'Unknown',
                'demographics': {},
                'conditions': [],
                'medications': [],
                'observations': []
            }
            
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                resource_type = resource.get('resourceType')
                
                if resource_type == 'Patient':
                    original_id = resource.get('id')  # Keep original for reference
                    patient_id = f"PID-{pid_counter:03d}"  # Use unified PID format
                    name_obj = resource.get('name', [{}])[0]
                    given = ' '.join(name_obj.get('given', ['Unknown']))
                    family = name_obj.get('family', 'Unknown')
                    
                    patient_data['patient_id'] = patient_id
                    patient_data['original_id'] = original_id  # Keep for reference
                    patient_data['name'] = f"{given} {family}"
                    patient_data['demographics'] = {
                        'gender': resource.get('gender', 'unknown'),
                        'birthDate': resource.get('birthDate', ''),
                        'address': resource.get('address', [{}])[0] if resource.get('address') else {}
                    }
                
                elif resource_type == 'Condition':
                    code = resource.get('code', {}).get('coding', [{}])[0]
                    patient_data['conditions'].append({
                        'code': code.get('code', ''),
                        'display': code.get('display', ''),
                        'status': resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', ''),
                        'onset': resource.get('onsetDateTime', '')
                    })
                
                elif resource_type == 'MedicationRequest':
                    med = resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0]
                    patient_data['medications'].append({
                        'code': med.get('code', ''),
                        'display': med.get('display', ''),
                        'status': resource.get('status', '')
                    })
                
                elif resource_type == 'Observation':
                    code = resource.get('code', {}).get('coding', [{}])[0]
                    value = resource.get('valueQuantity', {})
                    patient_data['observations'].append({
                        'code': code.get('code', ''),
                        'display': code.get('display', ''),
                        'value': value.get('value', ''),
                        'unit': value.get('unit', ''),
                        'date': resource.get('effectiveDateTime', '')
                    })
            
            if patient_data['patient_id']:
                all_patients[patient_data['patient_id']] = patient_data
                pid_counter += 1  # Increment PID for next patient
                
            if i % 50 == 0:
                print(f"  Processed {i}/{len(json_files)} files...")
        
        except Exception as e:
            print(f"  ⚠️  Error processing {json_file.name}: {e}")
            continue
    
    print(f"\n✅ Successfully converted {len(all_patients)} patients")
    print(f"   Total conditions: {sum(len(p['conditions']) for p in all_patients.values())}")
    print(f"   Total medications: {sum(len(p['medications']) for p in all_patients.values())}")
    print(f"   Total observations: {sum(len(p['observations']) for p in all_patients.values())}")
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_patients, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    return all_patients

if __name__ == '__main__':
    import sys
    
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "data/synthea/data/synthea/output/fhir"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "synthea_patients.json"
    start_pid = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    print(f"\n💡 Usage: python convert_synthea_bundles.py <input_dir> <output_file> <start_pid>")
    print(f"   Example: python convert_synthea_bundles.py ./fhir synthea.json 31")
    print(f"   (Use start_pid=31 if you have 30 MIMIC patients to avoid ID conflicts)\n")
    
    convert_synthea_bundles(input_dir, output_file, start_pid)
