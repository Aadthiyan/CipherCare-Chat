#!/usr/bin/env python3
"""
Upload converted MIMIC and Synthea patient data to CipherCare system
Supports both CyborgDB Lite (local) and CyborgDB Cloud
"""

import os
import json
import sys
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
COLLECTION_NAME = "patient_records"


class PatientDataUploader:
    """Upload patient records with embeddings to CyborgDB"""
    
    def __init__(self):
        """Initialize uploader"""
        logger.info("=== CipherCare Patient Data Uploader ===\n")
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("✓ Model loaded\n")
        
        # Initialize CyborgDB manager
        logger.info("Initializing CyborgDB Lite...")
        self.manager = CyborgLiteManager()
        logger.info("✓ CyborgDB ready\n")
        
    def create_clinical_text(self, patient_data: Dict) -> str:
        """Create searchable clinical text from patient data"""
        
        patient = patient_data.get('patient', {})
        conditions = patient_data.get('conditions', [])
        medications = patient_data.get('medications', [])
        observations = patient_data.get('observations', [])
        
        # Build comprehensive text
        text_parts = []
        
        # Patient info
        patient_id = patient.get('id', 'Unknown')
        gender = patient.get('gender', 'unknown')
        text_parts.append(f"Patient ID: {patient_id}")
        text_parts.append(f"Gender: {gender}")
        
        # Conditions
        if conditions:
            text_parts.append("\nMedical Conditions:")
            for condition in conditions[:10]:  # Limit to first 10
                # Handle both formats: Synthea (code is string) vs MIMIC (code is dict)
                if isinstance(condition.get('code'), dict):
                    display = condition.get('display', condition.get('code', {}).get('text', 'Unknown'))
                else:
                    display = condition.get('display', 'Unknown')
                status = condition.get('clinical_status', condition.get('status', 'unknown'))
                text_parts.append(f"  - {display} ({status})")
        
        # Medications
        if medications:
            text_parts.append("\nMedications:")
            for med in medications[:10]:  # Limit to first 10
                display = med.get('display', med.get('drug', 'Unknown'))
                text_parts.append(f"  - {display}")
        
        # Vital observations (if Synthea data)
        if observations:
            vitals = [obs for obs in observations if obs.get('code') in [
                '8867-4',  # Heart rate
                '8480-6',  # Systolic BP
                '8462-4',  # Diastolic BP
                '8310-5',  # Body temperature
                '9279-1',  # Respiratory rate
                '2708-6',  # Oxygen saturation
            ]]
            if vitals:
                text_parts.append("\nRecent Vitals:")
                for vital in vitals[:6]:
                    display = vital.get('display', 'Unknown')
                    value = vital.get('value', '')
                    unit = vital.get('unit', '')
                    text_parts.append(f"  - {display}: {value} {unit}")
        
        return "\n".join(text_parts)
    
    def upload_patient(self, patient_id: str, patient_data: Dict) -> bool:
        """Upload single patient record"""
        try:
            # Debug: Log the type and structure
            if not isinstance(patient_data, dict):
                logger.error(f"patient_data is not a dict, it's {type(patient_data)}: {patient_data}")
                return False
            # Create clinical text
            clinical_text = patient_data.get('clinical_summary', 
                                            self.create_clinical_text(patient_data))
            
            # Generate embedding
            embedding = self.embedder.encode(clinical_text).tolist()
            
            # Handle both MIMIC and Synthea formats
            # MIMIC has nested 'patient' key, Synthea has 'demographics' at root
            if 'patient' in patient_data:
                # MIMIC format
                patient = patient_data.get('patient', {})
                demographics = patient
            else:
                # Synthea format
                demographics = patient_data.get('demographics', {})
                patient = demographics
            
            conditions = patient_data.get('conditions', [])
            medications = patient_data.get('medications', [])
            
            metadata = {
                'patient_id': patient_id,
                'gender': demographics.get('gender', 'unknown'),
                'birth_date': demographics.get('birthDate', 'unknown'),
                'num_conditions': len(conditions),
                'num_medications': len(medications),
                'data_source': 'MIMIC-III' if patient_id.startswith('PID-0') and int(patient_id.split('-')[1]) <= 100 else 'Synthea',
                'record_type': 'patient_summary'
            }
            
            # Add condition summary
            if conditions:
                primary_conds = []
                for c in conditions[:3]:
                    if isinstance(c.get('code'), dict):
                        display = c.get('display', c.get('code', {}).get('text', ''))
                    else:
                        display = c.get('display', '')
                    primary_conds.append(display[:50])
                metadata['primary_conditions'] = ', '.join(primary_conds)
            
            # Generate record ID
            record_id = str(uuid.uuid4())
            
            # Upsert to database
            success = self.manager.upsert(
                record_id=record_id,
                patient_id=patient_id,
                embedding=embedding,
                metadata=metadata,
                collection=COLLECTION_NAME
            )
            
            if success:
                logger.info(f"✓ Uploaded {patient_id} ({metadata['data_source']})")
            else:
                logger.error(f"✗ Failed to upload {patient_id}")
            
            return success
            
        except Exception as e:
            import traceback
            logger.error(f"Error uploading {patient_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def upload_from_file(self, file_path: str) -> Dict[str, int]:
        """Upload all patients from JSON file"""
        
        logger.info(f"Loading patients from: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                patients = json.load(f)
            
            total = len(patients)
            logger.info(f"Found {total} patients\n")
            
            # Upload each patient
            success_count = 0
            failed_count = 0
            
            for i, (patient_id, patient_data) in enumerate(patients.items(), 1):
                if self.upload_patient(patient_id, patient_data):
                    success_count += 1
                else:
                    failed_count += 1
                
                # Progress update
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{total} patients processed")
            
            return {
                'total': total,
                'success': success_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            return {'total': 0, 'success': 0, 'failed': 0}
    
    def upload_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Upload patients from multiple files"""
        
        results = {
            'files': {},
            'total_patients': 0,
            'total_success': 0,
            'total_failed': 0
        }
        
        for file_path in file_paths:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {Path(file_path).name}")
            logger.info(f"{'='*60}\n")
            
            file_results = self.upload_from_file(file_path)
            
            results['files'][file_path] = file_results
            results['total_patients'] += file_results['total']
            results['total_success'] += file_results['success']
            results['total_failed'] += file_results['failed']
        
        return results


def main():
    """Main upload function"""
    
    if len(sys.argv) < 2:
        print("\n📤 CipherCare Patient Data Uploader")
        print("\nUsage:")
        print("  python upload_patient_data.py <file1.json> [file2.json] ...")
        print("\nExamples:")
        print("  python upload_patient_data.py mimic_patients_100.json")
        print("  python upload_patient_data.py mimic_patients_100.json synthea_patients_221.json")
        print("\nThis will upload all patient records to CyborgDB with embeddings.\n")
        sys.exit(1)
    
    # Get file paths
    file_paths = sys.argv[1:]
    
    # Validate files exist
    for file_path in file_paths:
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
    
    # Initialize uploader
    uploader = PatientDataUploader()
    
    # Upload data
    logger.info(f"\n{'='*60}")
    logger.info("Starting Upload")
    logger.info(f"{'='*60}\n")
    
    results = uploader.upload_multiple_files(file_paths)
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("Upload Complete!")
    logger.info(f"{'='*60}\n")
    
    for file_path, file_results in results['files'].items():
        logger.info(f"📁 {Path(file_path).name}")
        logger.info(f"   Total: {file_results['total']}")
        logger.info(f"   Success: {file_results['success']}")
        logger.info(f"   Failed: {file_results['failed']}\n")
    
    logger.info(f"📊 Overall Summary:")
    logger.info(f"   Total Patients: {results['total_patients']}")
    logger.info(f"   Successfully Uploaded: {results['total_success']}")
    logger.info(f"   Failed: {results['total_failed']}")
    
    success_rate = (results['total_success'] / results['total_patients'] * 100) if results['total_patients'] > 0 else 0
    logger.info(f"   Success Rate: {success_rate:.1f}%\n")
    
    if results['total_success'] > 0:
        logger.info("✅ Data is now searchable in CipherCare!")
    

if __name__ == "__main__":
    main()
