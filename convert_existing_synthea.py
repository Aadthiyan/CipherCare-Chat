"""
Convert existing synthea_patients_221.json to structured CipherCare format
Extracts granular observations with LOINC codes from pre-processed Synthea data
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import uuid
from datetime import datetime


class SyntheaConverterFromProcessed:
    """Convert pre-processed Synthea data to structured format"""
    
    def __init__(self, input_file: str = "synthea_patients_221.json"):
        """Initialize with input file"""
        self.input_file = Path(input_file)
        
    def load_data(self) -> Dict:
        """Load pre-processed Synthea data"""
        print(f"📥 Loading {self.input_file}...")
        
        with open(self.input_file, 'r') as f:
            data = json.load(f)
        
        print(f"  ✓ Loaded {len(data)} patients")
        return data
    
    def convert_to_structured(self, data: Dict) -> List[Dict]:
        """Convert to structured observation records"""
        print("🔄 Converting to structured format...")
        
        all_records = []
        
        for patient_id, patient_data in data.items():
            # Extract conditions
            if 'conditions' in patient_data:
                for condition in patient_data['conditions']:
                    record = self._create_condition_record(patient_id, condition)
                    if record:
                        all_records.append(record)
            
            # Extract observations (if present)
            if 'observations' in patient_data:
                for obs in patient_data['observations']:
                    record = self._create_observation_record(patient_id, obs)
                    if record:
                        all_records.append(record)
            
            # Extract medications (if present)
            if 'medications' in patient_data:
                for med in patient_data['medications']:
                    record = self._create_medication_record(patient_id, med)
                    if record:
                        all_records.append(record)
        
        print(f"  ✓ Created {len(all_records)} structured records")
        return all_records
    
    def _create_condition_record(self, patient_id: str, condition: Dict) -> Optional[Dict]:
        """Create structured condition record"""
        
        display = condition.get('condition', 'Unknown')
        code = condition.get('code', 'unknown')
        onset_date = condition.get('onset', datetime.now().isoformat())
        status = condition.get('status', 'active')
        
        text_for_embedding = f"{onset_date}: {display} (status: {status})"
        
        return {
            "patient_id": patient_id,
            "record_id": f"cond-{uuid.uuid4()}",
            "record_type": "condition",
            "data_source": "Synthea",
            "created_at": onset_date,
            "effective_date": onset_date,
            "provenance": "synthea-generator",
            "language": "en",
            
            "code": {
                "system": "SNOMED-CT",
                "code": code,
                "display": display
            },
            "display": display,
            "snomed_code": code,
            "status": status,
            
            "text_for_embedding": text_for_embedding,
            "text_summary": display
        }
    
    def _create_observation_record(self, patient_id: str, obs: Dict) -> Optional[Dict]:
        """Create structured observation record"""
        
        display = obs.get('type', obs.get('observation', 'Unknown'))
        value = obs.get('value')
        unit = obs.get('unit', '')
        date = obs.get('date', obs.get('effective_date', datetime.now().isoformat()))
        
        # Try to infer LOINC code from display
        loinc_code = self._infer_loinc_code(display)
        
        text_for_embedding = f"{date}: {display}"
        if value:
            text_for_embedding += f" {value} {unit}"
        
        return {
            "patient_id": patient_id,
            "record_id": f"obs-{uuid.uuid4()}",
            "record_type": "observation",
            "data_source": "Synthea",
            "created_at": date,
            "effective_date": date,
            "provenance": "synthea-generator",
            "language": "en",
            
            "code": {
                "system": "LOINC",
                "code": loinc_code,
                "display": display
            },
            "display": display,
            "loinc_code": loinc_code,
            
            "value": value,
            "value_normalized": value,
            "unit": unit,
            "value_type": "Quantity" if value else "String",
            "status": "final",
            
            "text_for_embedding": text_for_embedding,
            "text_summary": f"{display}: {value} {unit}" if value else display
        }
    
    def _create_medication_record(self, patient_id: str, med: Dict) -> Optional[Dict]:
        """Create structured medication record"""
        
        display = med.get('medication', med.get('drug', 'Unknown'))
        start_date = med.get('start', med.get('start_date', datetime.now().isoformat()))
        status = med.get('status', 'active')
        
        text_for_embedding = f"{start_date}: {display}"
        
        return {
            "patient_id": patient_id,
            "record_id": f"med-{uuid.uuid4()}",
            "record_type": "medication",
            "data_source": "Synthea",
            "created_at": start_date,
            "effective_date": start_date,
            "provenance": "synthea-generator",
            "language": "en",
            
            "medication_code": {
                "system": "RxNorm",
                "code": "unknown",
                "display": display
            },
            "display": display,
            "status": status,
            
            "text_for_embedding": text_for_embedding,
            "text_summary": display
        }
    
    def _infer_loinc_code(self, display: str) -> str:
        """Infer LOINC code from display text"""
        
        display_lower = display.lower()
        
        loinc_map = {
            'temperature': '8310-5',
            'heart rate': '8867-4',
            'respiratory rate': '9279-1',
            'blood pressure': '85354-9',
            'systolic': '8480-6',
            'diastolic': '8462-4',
            'oxygen': '59408-5',
            'spo2': '59408-5',
            'weight': '29463-7',
            'height': '8302-2',
            'glucose': '2345-7',
            'pain': '38208-5',
        }
        
        for keyword, loinc in loinc_map.items():
            if keyword in display_lower:
                return loinc
        
        return 'unknown'


def main():
    """Main execution"""
    print("🏥 Synthea Data Converter for CipherCare")
    print("="*60)
    
    # Check if file exists
    input_file = "synthea_patients_221.json"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        print("\nLooking for alternative Synthea files...")
        
        # Look for other Synthea files
        synthea_files = list(Path(".").glob("synthea*.json"))
        
        if synthea_files:
            print(f"\nFound {len(synthea_files)} Synthea files:")
            for i, file in enumerate(synthea_files, 1):
                print(f"  {i}. {file.name}")
            
            choice = input("\nSelect file number (or press Enter to cancel): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(synthea_files):
                input_file = str(synthea_files[int(choice) - 1])
            else:
                print("❌ Cancelled")
                return
        else:
            print("❌ No Synthea files found")
            print("\n💡 You need to either:")
            print("  1. Generate Synthea FHIR data")
            print("  2. Use fetch_from_fhir_server.py for quick testing")
            return
    
    # Initialize converter
    converter = SyntheaConverterFromProcessed(input_file)
    
    # Load data
    data = converter.load_data()
    
    # Convert to structured format
    records = converter.convert_to_structured(data)
    
    # Save output
    output_file = "synthea_structured_cipercare.json"
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)
    
    # Statistics
    record_types = {}
    by_patient = {}
    
    for record in records:
        rtype = record.get('record_type', 'unknown')
        record_types[rtype] = record_types.get(rtype, 0) + 1
        
        patient_id = record.get('patient_id', 'unknown')
        by_patient[patient_id] = by_patient.get(patient_id, 0) + 1
    
    print("\n" + "="*60)
    print("✅ CONVERSION COMPLETE")
    print("="*60)
    print(f"Total records: {len(records)}")
    print(f"Total patients: {len(by_patient)}")
    
    print(f"\nRecords by type:")
    for rtype, count in sorted(record_types.items()):
        print(f"  - {rtype}: {count}")
    
    print(f"\nSaved to: {output_file}")
    
    # Show sample
    if records:
        print("\n📄 SAMPLE RECORD:")
        print("="*60)
        print(json.dumps(records[0], indent=2))
    
    print("\n✅ NEXT STEP:")
    print("="*60)
    print("Upload to CyborgDB:")
    print(f"  python upload_structured_data.py")
    print("="*60)


if __name__ == "__main__":
    main()
