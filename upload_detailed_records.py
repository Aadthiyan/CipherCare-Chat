"""
Upload detailed clinical records (conditions, medications, observations) to CyborgDB
Each condition/medication/observation becomes a separate embedding for better clinical queries
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

def create_condition_text(condition: Dict[str, Any], patient_id: str) -> str:
    """Create text for condition embedding"""
    code = condition.get('code', 'Unknown')
    display = condition.get('display', 'Unknown condition')
    status = condition.get('status', 'unknown')
    onset = condition.get('onset', 'unknown date')
    
    text = f"Patient {patient_id} has condition: {display} "
    text += f"(Code: {code}, Status: {status}, Onset: {onset})"
    return text

def create_medication_text(medication: Dict[str, Any], patient_id: str) -> str:
    """Create text for medication embedding"""
    code = medication.get('code', 'Unknown')
    display = medication.get('display', 'Unknown medication')
    status = medication.get('status', 'unknown')
    start = medication.get('start', 'unknown date')
    
    text = f"Patient {patient_id} is prescribed medication: {display} "
    text += f"(Code: {code}, Status: {status}, Started: {start})"
    return text

def create_observation_text(observation: Dict[str, Any], patient_id: str) -> str:
    """Create text for observation embedding"""
    code = observation.get('code', 'Unknown')
    display = observation.get('display', 'Unknown observation')
    value = observation.get('value', 'N/A')
    unit = observation.get('unit', '')
    date = observation.get('date', 'unknown date')
    
    text = f"Patient {patient_id} observation: {display} "
    text += f"value: {value} {unit} (Code: {code}, Date: {date})"
    return text

def upload_patient_records(patient_data: Dict[str, Any], cyborg_manager, collection: str = "patient_records"):
    """Upload all clinical records for a patient"""
    patient_id = patient_data.get('patient_id', 'Unknown')
    demographics = patient_data.get('demographics', {})
    
    records_uploaded = 0
    
    # Get index once at the start to avoid repeated "already exists" warnings
    try:
        index = cyborg_manager.get_index(collection)
    except Exception as e:
        if "already exists" not in str(e).lower():
            print(f"  ⚠️  Warning getting index: {str(e)[:100]}")
    
    # Upload conditions
    conditions = patient_data.get('conditions', [])
    for condition in conditions:
        try:
            # Create clinical text
            text = create_condition_text(condition, patient_id)
            
            # Generate embedding
            embedding = embedder.encode(text).tolist()
            
            # Prepare metadata
            metadata = {
                'patient_id': patient_id,
                'record_type': 'condition',
                'code': condition.get('code', 'Unknown'),
                'display': condition.get('display', 'Unknown'),
                'status': condition.get('status', 'unknown'),
                'onset_date': condition.get('onset', 'unknown'),
                'gender': demographics.get('gender', 'unknown'),
                'birth_date': demographics.get('birthDate', 'unknown'),
                'data_source': patient_data.get('data_source', 'Unknown')
            }
            
            # Upload to CyborgDB
            record_id = f"{patient_id}_condition_{condition.get('code', str(uuid.uuid4())[:8])}"
            cyborg_manager.upsert(
                record_id=record_id,
                patient_id=patient_id,
                embedding=embedding,
                metadata=metadata,
                collection=collection
            )
            records_uploaded += 1
            
        except Exception as e:
            print(f"  ⚠️  Failed to upload condition {condition.get('display', 'unknown')}: {str(e)[:100]}")
            continue
    
    # Upload medications
    medications = patient_data.get('medications', [])
    for medication in medications:
        try:
            # Create clinical text
            text = create_medication_text(medication, patient_id)
            
            # Generate embedding
            embedding = embedder.encode(text).tolist()
            
            # Prepare metadata
            metadata = {
                'patient_id': patient_id,
                'record_type': 'medication',
                'code': medication.get('code', 'Unknown'),
                'display': medication.get('display', 'Unknown'),
                'status': medication.get('status', 'unknown'),
                'start_date': medication.get('start', 'unknown'),
                'gender': demographics.get('gender', 'unknown'),
                'birth_date': demographics.get('birthDate', 'unknown'),
                'data_source': patient_data.get('data_source', 'Unknown')
            }
            
            # Upload to CyborgDB
            record_id = f"{patient_id}_medication_{medication.get('code', str(uuid.uuid4())[:8])}"
            cyborg_manager.upsert(
                record_id=record_id,
                patient_id=patient_id,
                embedding=embedding,
                metadata=metadata,
                collection=collection
            )
            records_uploaded += 1
            
        except Exception as e:
            print(f"  ⚠️  Failed to upload medication {medication.get('display', 'unknown')}: {str(e)[:100]}")
            continue
    
    # Upload observations (limit to first 20 to avoid too many records)
    observations = patient_data.get('observations', [])[:20]
    for observation in observations:
        try:
            # Create clinical text
            text = create_observation_text(observation, patient_id)
            
            # Generate embedding
            embedding = embedder.encode(text).tolist()
            
            # Prepare metadata
            metadata = {
                'patient_id': patient_id,
                'record_type': 'observation',
                'code': observation.get('code', 'Unknown'),
                'display': observation.get('display', 'Unknown'),
                'value': str(observation.get('value', 'N/A')),
                'unit': observation.get('unit', ''),
                'date': observation.get('date', 'unknown'),
                'gender': demographics.get('gender', 'unknown'),
                'birth_date': demographics.get('birthDate', 'unknown'),
                'data_source': patient_data.get('data_source', 'Unknown')
            }
            
            # Upload to CyborgDB
            record_id = f"{patient_id}_observation_{observation.get('code', str(uuid.uuid4())[:8])}"
            cyborg_manager.upsert(
                record_id=record_id,
                patient_id=patient_id,
                embedding=embedding,
                metadata=metadata,
                collection=collection
            )
            records_uploaded += 1
            
        except Exception as e:
            print(f"  ⚠️  Failed to upload observation {observation.get('display', 'unknown')}: {str(e)[:100]}")
            continue
    
    return records_uploaded

def main():
    print("\n=== Uploading Detailed Clinical Records to CyborgDB ===\n")
    
    # Initialize CyborgDB
    print("Connecting to CyborgDB...")
    cyborg_manager = get_cyborg_manager()
    print("✅ Connected to CyborgDB\n")
    
    # Load patient data files
    files = [
        ('mimic_patients_100.json', 'MIMIC-III'),
        ('synthea_patients_221.json', 'Synthea')
    ]
    
    total_patients = 0
    total_records = 0
    
    for filename, source in files:
        if not os.path.exists(filename):
            print(f"⚠️  Skipping {filename} - file not found")
            continue
        
        print(f"\n📂 Processing {filename} ({source})...")
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Convert to list if it's a dict
        if isinstance(data, dict):
            patients = list(data.values())
        else:
            patients = data
        
        print(f"Found {len(patients)} patients\n")
        
        # Upload each patient's records
        for patient in tqdm(patients, desc=f"Uploading {source}"):
            try:
                records = upload_patient_records(patient, cyborg_manager)
                total_patients += 1
                total_records += records
            except Exception as e:
                patient_id = patient.get('patient_id', 'Unknown')
                print(f"\n❌ Failed to upload patient {patient_id}: {str(e)[:100]}")
                continue
    
    print(f"\n\n=== Upload Complete ===")
    print(f"✅ Uploaded {total_records} clinical records from {total_patients} patients")
    print(f"📊 Average {total_records/total_patients:.1f} records per patient")
    print(f"\nCollection: patient_records")

if __name__ == "__main__":
    main()
