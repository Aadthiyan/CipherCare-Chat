"""
Convert Synthea FHIR data to CipherCare format and upload to CyborgDB

Supports:
- NDJSON format (Patient.ndjson, Condition.ndjson, etc.)
- FHIR Bundle JSON
- Individual FHIR resources

Usage:
    python convert_synthea_to_cipercare.py --input ./synthea/output/fhir/ --upload
    python convert_synthea_to_cipercare.py --bundle synthea_bundle.json --upload
"""

import os
import json
import argparse
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def parse_ndjson(file_path: str) -> List[Dict]:
    """Parse NDJSON file (one JSON object per line)"""
    resources = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                resources.append(json.loads(line))
    return resources


def parse_bundle(file_path: str) -> List[Dict]:
    """Parse FHIR Bundle JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data.get('resourceType') == 'Bundle':
        return [entry['resource'] for entry in data.get('entry', [])]
    else:
        # Single resource
        return [data]


def extract_patient_info(patient: Dict) -> Dict:
    """Extract patient demographics"""
    name_obj = patient.get('name', [{}])[0]
    given = name_obj.get('given', ['Unknown'])
    family = name_obj.get('family', 'Unknown')
    
    return {
        'patient_id': patient.get('id', str(uuid.uuid4())),
        'name': f"{' '.join(given)} {family}",
        'gender': patient.get('gender', 'unknown'),
        'birthDate': patient.get('birthDate', 'unknown'),
        'resourceType': 'Patient'
    }


def extract_condition_info(condition: Dict) -> Dict:
    """Extract condition/diagnosis information"""
    code = condition.get('code', {})
    coding = code.get('coding', [{}])[0]
    
    # Get patient reference
    subject_ref = condition.get('subject', {}).get('reference', '')
    patient_id = subject_ref.replace('Patient/', '').replace('urn:uuid:', '')
    
    return {
        'patient_id': patient_id,
        'condition_id': condition.get('id', str(uuid.uuid4())),
        'code': coding.get('code', ''),
        'system': coding.get('system', ''),
        'display': coding.get('display', code.get('text', 'Unknown condition')),
        'clinical_status': condition.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'unknown'),
        'onset_date': condition.get('onsetDateTime', condition.get('recordedDate', '')),
        'resourceType': 'Condition'
    }


def extract_medication_info(medication: Dict) -> Dict:
    """Extract medication information"""
    med_code = medication.get('medicationCodeableConcept', {})
    coding = med_code.get('coding', [{}])[0]
    
    subject_ref = medication.get('subject', {}).get('reference', '')
    patient_id = subject_ref.replace('Patient/', '').replace('urn:uuid:', '')
    
    return {
        'patient_id': patient_id,
        'medication_id': medication.get('id', str(uuid.uuid4())),
        'code': coding.get('code', ''),
        'display': coding.get('display', med_code.get('text', 'Unknown medication')),
        'status': medication.get('status', 'unknown'),
        'effective_date': medication.get('effectiveDateTime', ''),
        'resourceType': 'MedicationRequest'
    }


def extract_observation_info(observation: Dict) -> Dict:
    """Extract lab/observation information"""
    code = observation.get('code', {})
    coding = code.get('coding', [{}])[0]
    
    subject_ref = observation.get('subject', {}).get('reference', '')
    patient_id = subject_ref.replace('Patient/', '').replace('urn:uuid:', '')
    
    # Get value
    value = observation.get('valueQuantity', {})
    value_str = f"{value.get('value', '')} {value.get('unit', '')}" if value else observation.get('valueString', '')
    
    return {
        'patient_id': patient_id,
        'observation_id': observation.get('id', str(uuid.uuid4())),
        'code': coding.get('code', ''),
        'display': coding.get('display', code.get('text', 'Unknown observation')),
        'value': value_str,
        'effective_date': observation.get('effectiveDateTime', ''),
        'resourceType': 'Observation'
    }


def create_clinical_text(patient_data: Dict, conditions: List[Dict], 
                        medications: List[Dict], observations: List[Dict]) -> str:
    """Create rich clinical text for embedding"""
    
    text_parts = []
    
    # Patient demographics
    text_parts.append(f"Patient: {patient_data['name']}, {patient_data['gender']}, DOB: {patient_data['birthDate']}")
    
    # Conditions
    if conditions:
        text_parts.append("\nConditions:")
        for cond in conditions:
            status = cond.get('clinical_status', 'active')
            text_parts.append(f"- {cond['display']} ({status})")
    
    # Medications
    if medications:
        text_parts.append("\nMedications:")
        for med in medications:
            text_parts.append(f"- {med['display']} ({med.get('status', 'active')})")
    
    # Observations (recent vitals/labs)
    if observations:
        text_parts.append("\nRecent Observations:")
        for obs in observations[:5]:  # Limit to recent 5
            text_parts.append(f"- {obs['display']}: {obs.get('value', 'N/A')}")
    
    return "\n".join(text_parts)


def convert_synthea_data(input_path: str) -> Dict[str, Any]:
    """
    Convert Synthea FHIR data to CipherCare format
    
    Returns:
        Dict with patients, conditions, medications, observations
    """
    input_path = Path(input_path)
    
    patients = {}
    conditions = []
    medications = []
    observations = []
    
    print(f"🔍 Scanning: {input_path}")
    
    # Handle directory of NDJSON files
    if input_path.is_dir():
        # Patient file
        patient_file = input_path / "Patient.ndjson"
        if patient_file.exists():
            print(f"📄 Reading {patient_file.name}...")
            for resource in parse_ndjson(str(patient_file)):
                info = extract_patient_info(resource)
                patients[info['patient_id']] = info
        
        # Condition file
        condition_file = input_path / "Condition.ndjson"
        if condition_file.exists():
            print(f"📄 Reading {condition_file.name}...")
            for resource in parse_ndjson(str(condition_file)):
                conditions.append(extract_condition_info(resource))
        
        # Medication file
        med_file = input_path / "MedicationRequest.ndjson"
        if med_file.exists():
            print(f"📄 Reading {med_file.name}...")
            for resource in parse_ndjson(str(med_file)):
                medications.append(extract_medication_info(resource))
        
        # Observation file
        obs_file = input_path / "Observation.ndjson"
        if obs_file.exists():
            print(f"📄 Reading {obs_file.name}...")
            for resource in parse_ndjson(str(obs_file)):
                observations.append(extract_observation_info(resource))
    
    # Handle single bundle file
    elif input_path.is_file():
        print(f"📄 Reading bundle file...")
        resources = parse_bundle(str(input_path))
        
        for resource in resources:
            resource_type = resource.get('resourceType')
            
            if resource_type == 'Patient':
                info = extract_patient_info(resource)
                patients[info['patient_id']] = info
            elif resource_type == 'Condition':
                conditions.append(extract_condition_info(resource))
            elif resource_type == 'MedicationRequest':
                medications.append(extract_medication_info(resource))
            elif resource_type == 'Observation':
                observations.append(extract_observation_info(resource))
    
    print(f"\n✅ Converted:")
    print(f"   - {len(patients)} patients")
    print(f"   - {len(conditions)} conditions")
    print(f"   - {len(medications)} medications")
    print(f"   - {len(observations)} observations")
    
    return {
        'patients': patients,
        'conditions': conditions,
        'medications': medications,
        'observations': observations
    }


def group_by_patient(data: Dict[str, Any]) -> Dict[str, Dict]:
    """Group all data by patient ID"""
    
    patients = data['patients']
    grouped = {}
    
    for patient_id, patient_info in patients.items():
        # Find all conditions for this patient
        patient_conditions = [c for c in data['conditions'] if c['patient_id'] == patient_id]
        patient_medications = [m for m in data['medications'] if m['patient_id'] == patient_id]
        patient_observations = [o for o in data['observations'] if o['patient_id'] == patient_id]
        
        # Create clinical text
        clinical_text = create_clinical_text(
            patient_info,
            patient_conditions,
            patient_medications,
            patient_observations
        )
        
        grouped[patient_id] = {
            'patient': patient_info,
            'conditions': patient_conditions,
            'medications': patient_medications,
            'observations': patient_observations,
            'clinical_text': clinical_text
        }
    
    return grouped


def save_to_json(data: Dict, output_path: str):
    """Save converted data to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved to: {output_path}")


def upload_to_cyborgdb(grouped_data: Dict[str, Dict]):
    """Upload patient data to CyborgDB"""
    try:
        from sentence_transformers import SentenceTransformer
        from backend.cyborg_lite_manager import CyborgLiteManager
        
        print("\n🚀 Uploading to CyborgDB...")
        
        embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        db = CyborgLiteManager()
        
        success_count = 0
        
        for patient_id, patient_data in grouped_data.items():
            try:
                # Generate embedding from clinical text
                clinical_text = patient_data['clinical_text']
                embedding = embedder.encode(clinical_text).tolist()
                
                # Create metadata
                metadata = {
                    'patient_id': patient_id,
                    'patient_name': patient_data['patient']['name'],
                    'gender': patient_data['patient']['gender'],
                    'birth_date': patient_data['patient']['birthDate'],
                    'condition_count': len(patient_data['conditions']),
                    'medication_count': len(patient_data['medications']),
                    'source': 'synthea',
                    'upload_date': datetime.now().isoformat()
                }
                
                # Upload to CyborgDB
                record_id = str(uuid.uuid4())
                db.upsert(
                    record_id=record_id,
                    patient_id=patient_id,
                    embedding=embedding,
                    metadata=metadata,
                    collection="patient_embeddings"
                )
                
                success_count += 1
                print(f"   ✓ Uploaded: {patient_id} - {patient_data['patient']['name']}")
                
            except Exception as e:
                print(f"   ✗ Failed: {patient_id} - {str(e)}")
        
        print(f"\n✅ Upload complete: {success_count}/{len(grouped_data)} patients")
        
    except ImportError as e:
        print(f"\n⚠️  Cannot upload: Missing dependencies ({str(e)})")
        print("   Run: pip install sentence-transformers")


def main():
    parser = argparse.ArgumentParser(description='Convert Synthea FHIR data to CipherCare format')
    parser.add_argument('--input', '-i', required=True, help='Input path (NDJSON directory or bundle JSON file)')
    parser.add_argument('--output', '-o', default='synthea_converted.json', help='Output JSON file')
    parser.add_argument('--upload', action='store_true', help='Upload to CyborgDB after conversion')
    
    args = parser.parse_args()
    
    # Convert data
    data = convert_synthea_data(args.input)
    
    # Group by patient
    grouped = group_by_patient(data)
    
    # Save to file
    save_to_json(grouped, args.output)
    
    # Upload if requested
    if args.upload:
        upload_to_cyborgdb(grouped)
    else:
        print("\n💡 Tip: Use --upload flag to upload directly to CyborgDB")


if __name__ == "__main__":
    main()
