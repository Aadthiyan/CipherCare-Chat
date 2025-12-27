"""
Fast batch upload of detailed clinical records to CyborgDB
Uploads records in batches of 50 for much better performance
"""
import json
import os
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import get_cyborg_manager
from tqdm import tqdm
import uuid

# Load environment
load_dotenv()

# Initialize embedding model
print("Loading embedding model...")
embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def prepare_patient_records(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prepare all records for a patient (to be batched later)"""
    # Support both flat (Synthea) and nested (MIMIC) patient formats
    patient_id = patient_data.get('patient_id')
    patient_obj = None
    if not patient_id and isinstance(patient_data.get('patient'), dict):
        patient_obj = patient_data.get('patient')
        patient_id = patient_obj.get('id')
    if not patient_id:
        patient_id = patient_data.get('original_id', 'Unknown')

    demographics = patient_data.get('demographics', {})
    # If demographics missing, try to pull from nested patient object
    if not demographics and patient_obj:
        demographics = {
            'gender': patient_obj.get('gender', 'unknown'),
            'birthDate': patient_obj.get('birthDate', 'unknown')
        }
    records = []
    
    # Prepare conditions
    conditions = patient_data.get('conditions', [])
    for condition in conditions:
        code = condition.get('code', 'Unknown')
        display = condition.get('display', 'Unknown condition')
        status = condition.get('status', 'unknown')
        onset = condition.get('onset', 'unknown date')
        
        text = f"Patient {patient_id} has condition: {display} (Code: {code}, Status: {status}, Onset: {onset})"
        embedding = embedder.encode(text).tolist()
        
        records.append({
            'id': f"{patient_id}_condition_{code}_{str(uuid.uuid4())[:8]}",
            'patient_id': patient_id,
            'vector': embedding,
            'metadata': {
                'patient_id': patient_id,
                'record_type': 'condition',
                'code': code,
                'display': display,
                'status': status,
                'onset_date': onset,
                'gender': demographics.get('gender', 'unknown'),
                'birth_date': demographics.get('birthDate', 'unknown'),
                'data_source': patient_data.get('data_source', 'Unknown')
            }
        })
    
    # Prepare medications
    medications = patient_data.get('medications', [])
    for medication in medications:
        code = medication.get('code', 'Unknown')
        display = medication.get('display', 'Unknown medication')
        status = medication.get('status', 'unknown')
        start = medication.get('start', 'unknown date')
        
        text = f"Patient {patient_id} is prescribed medication: {display} (Code: {code}, Status: {status}, Started: {start})"
        embedding = embedder.encode(text).tolist()
        
        records.append({
            'id': f"{patient_id}_medication_{code}_{str(uuid.uuid4())[:8]}",
            'patient_id': patient_id,
            'vector': embedding,
            'metadata': {
                'patient_id': patient_id,
                'record_type': 'medication',
                'code': code,
                'display': display,
                'status': status,
                'start_date': start,
                'gender': demographics.get('gender', 'unknown'),
                'birth_date': demographics.get('birthDate', 'unknown'),
                'data_source': patient_data.get('data_source', 'Unknown')
            }
        })
    
    # Prepare observations (limit to 10 per patient)
    observations = patient_data.get('observations', [])[:10]
    for observation in observations:
        code = observation.get('code', 'Unknown')
        display = observation.get('display', 'Unknown observation')
        value = observation.get('value', 'N/A')
        unit = observation.get('unit', '')
        date = observation.get('date', 'unknown date')
        
        text = f"Patient {patient_id} observation: {display} value: {value} {unit} (Code: {code}, Date: {date})"
        embedding = embedder.encode(text).tolist()
        
        records.append({
            'id': f"{patient_id}_observation_{code}_{str(uuid.uuid4())[:8]}",
            'patient_id': patient_id,
            'vector': embedding,
            'metadata': {
                'patient_id': patient_id,
                'record_type': 'observation',
                'code': code,
                'display': display,
                'value': str(value),
                'unit': unit,
                'date': date,
                'gender': demographics.get('gender', 'unknown'),
                'birth_date': demographics.get('birthDate', 'unknown'),
                'data_source': patient_data.get('data_source', 'Unknown')
            }
        })
    
    return records

def main():
    print("\n=== Fast Batch Upload to CyborgDB ===\n")
    
    # Initialize CyborgDB
    print("Connecting to CyborgDB...")
    cyborg_manager = get_cyborg_manager()
    print("✅ Connected\n")
    
    # Load patient data files - prefer preprocessed .ready.json if available
    files = []
    if os.path.exists('mimic_patients_100.ready.json'):
        files.append(('mimic_patients_100.ready.json', 'MIMIC-III'))
    elif os.path.exists('mimic_patients_100.json'):
        files.append(('mimic_patients_100.json', 'MIMIC-III'))

    if os.path.exists('synthea_patients_221.ready.json'):
        files.append(('synthea_patients_221.ready.json', 'Synthea'))
    elif os.path.exists('synthea_patients_221.json'):
        files.append(('synthea_patients_221.json', 'Synthea'))
    
    # Allow overriding batch size via env var to tune performance on CI/servers
    try:
        BATCH_SIZE = int(os.getenv("UPLOAD_BATCH_SIZE", "2000"))
    except Exception:
        BATCH_SIZE = 2000
    all_records = []
    total_patients = 0
    
    for filename, source in files:
        if not os.path.exists(filename):
            print(f"⚠️  Skipping {filename} - file not found")
            continue
        
        print(f"📂 Processing {filename} ({source})...")
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Convert to list if it's a dict
        if isinstance(data, dict):
            patients = list(data.values())
        else:
            patients = data
        
        print(f"Found {len(patients)} patients\n")
        
        # Prepare records for all patients
        for patient in tqdm(patients, desc=f"Preparing {source}"):
            records = prepare_patient_records(patient)
            all_records.extend(records)
            total_patients += 1
    
    print(f"\n📊 Prepared {len(all_records):,} records from {total_patients} patients")
    print(f"🚀 Uploading in batches of {BATCH_SIZE}...\n")
    
    # Upload in batches
    uploaded = 0
    for i in tqdm(range(0, len(all_records), BATCH_SIZE), desc="Uploading batches"):
        batch = all_records[i:i+BATCH_SIZE]
        try:
            result = cyborg_manager.batch_upsert(batch, collection="patient_records")
            uploaded += result
        except Exception as e:
            print(f"\n⚠️  Batch {i//BATCH_SIZE + 1} failed: {str(e)[:100]}")
            continue
    
    print(f"\n✅ Upload Complete!")
    print(f"📈 Uploaded {uploaded:,} records")
    print(f"📊 From {total_patients} patients")
    print(f"🗄️  Collection: patient_records")

if __name__ == "__main__":
    main()
