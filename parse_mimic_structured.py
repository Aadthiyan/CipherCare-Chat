"""
Parse MIMIC-IV data into CipherCare's structured format
Extracts vitals, labs, medications, conditions with full LOINC/SNOMED codes
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import uuid


class MIMICStructuredParser:
    """Parse MIMIC-IV into granular observation records"""
    
    # LOINC mappings for common vitals
    VITAL_LOINC_MAP = {
        'Heart Rate': {'loinc': '8867-4', 'unit': 'beats/min', 'display': 'Heart rate'},
        'Respiratory Rate': {'loinc': '9279-1', 'unit': 'breaths/min', 'display': 'Respiratory rate'},
        'Temperature Fahrenheit': {'loinc': '8310-5', 'unit': 'degF', 'display': 'Body temperature'},
        'Temperature Celsius': {'loinc': '8310-5', 'unit': 'Cel', 'display': 'Body temperature'},
        'SpO2': {'loinc': '59408-5', 'unit': '%', 'display': 'Oxygen saturation'},
        'Non Invasive Blood Pressure systolic': {'loinc': '8480-6', 'unit': 'mm[Hg]', 'display': 'Systolic blood pressure'},
        'Non Invasive Blood Pressure diastolic': {'loinc': '8462-4', 'unit': 'mm[Hg]', 'display': 'Diastolic blood pressure'},
        'Arterial Blood Pressure systolic': {'loinc': '8480-6', 'unit': 'mm[Hg]', 'display': 'Systolic blood pressure'},
        'Arterial Blood Pressure diastolic': {'loinc': '8462-4', 'unit': 'mm[Hg]', 'display': 'Diastolic blood pressure'},
        'Weight': {'loinc': '29463-7', 'unit': 'kg', 'display': 'Body weight'},
        'Height': {'loinc': '8302-2', 'unit': 'cm', 'display': 'Body height'},
        'Pain Level': {'loinc': '38208-5', 'unit': '{score}', 'display': 'Pain severity'},
        'Glucose': {'loinc': '2345-7', 'unit': 'mg/dL', 'display': 'Glucose'},
    }
    
    # Common lab LOINC codes
    LAB_LOINC_MAP = {
        'Glucose': '2345-7',
        'Creatinine': '2160-0',
        'Sodium': '2951-2',
        'Potassium': '2823-3',
        'Chloride': '2075-0',
        'Hemoglobin': '718-7',
        'Hematocrit': '4544-3',
        'White Blood Cells': '6690-2',
        'Platelets': '777-3',
    }
    
    def __init__(self, mimic_dir: str):
        """Initialize with MIMIC-IV directory path"""
        self.mimic_dir = Path(mimic_dir)
        self.patients_df = None
        self.admissions_df = None
        
    def load_core_tables(self):
        """Load core MIMIC tables"""
        print("📥 Loading MIMIC-IV core tables...")
        
        try:
            # Load patients
            self.patients_df = pd.read_csv(self.mimic_dir / 'hosp' / 'patients.csv.gz')
            print(f"  ✓ Loaded {len(self.patients_df)} patients")
            
            # Load admissions
            self.admissions_df = pd.read_csv(self.mimic_dir / 'hosp' / 'admissions.csv.gz')
            print(f"  ✓ Loaded {len(self.admissions_df)} admissions")
            
        except Exception as e:
            print(f"❌ Error loading core tables: {e}")
            raise
    
    def parse_chartevents(self, limit: Optional[int] = None) -> List[Dict]:
        """Parse chartevents (vitals) into observation records"""
        print("🔄 Parsing chartevents (vitals)...")
        
        try:
            # Load chartevents (this is a LARGE file)
            chartevents_path = self.mimic_dir / 'icu' / 'chartevents.csv.gz'
            
            # Read in chunks for memory efficiency
            chunk_size = 100000
            observations = []
            
            for chunk in pd.read_csv(chartevents_path, chunksize=chunk_size, nrows=limit):
                # Merge with item definitions to get labels
                d_items = pd.read_csv(self.mimic_dir / 'icu' / 'd_items.csv.gz')
                chunk = chunk.merge(d_items, on='itemid', how='left')
                
                for _, row in chunk.iterrows():
                    label = row.get('label', 'Unknown')
                    
                    # Check if this is a vital we care about
                    vital_info = self.VITAL_LOINC_MAP.get(label)
                    
                    if vital_info:
                        obs = self._create_observation_record(
                            patient_id=f"PID-{row['subject_id']}",
                            encounter_id=f"ENC-{row['hadm_id']}" if pd.notna(row.get('hadm_id')) else None,
                            record_type="observation",
                            effective_date=row['charttime'],
                            code_system="LOINC",
                            code=vital_info['loinc'],
                            display=vital_info['display'],
                            value=row.get('valuenum'),
                            value_text=row.get('value'),
                            unit=vital_info['unit'],
                            status="final",
                            method=self._infer_method(label),
                            provenance=f"caregiver-{row.get('cgid', 'unknown')}",
                            data_source="MIMIC-IV"
                        )
                        observations.append(obs)
                
                if limit and len(observations) >= limit:
                    break
            
            print(f"  ✓ Parsed {len(observations)} vital observations")
            return observations
            
        except Exception as e:
            print(f"❌ Error parsing chartevents: {e}")
            return []
    
    def parse_labevents(self, limit: Optional[int] = None) -> List[Dict]:
        """Parse labevents into observation records"""
        print("🔄 Parsing labevents (laboratory)...")
        
        try:
            labevents_path = self.mimic_dir / 'hosp' / 'labevents.csv.gz'
            d_labitems = pd.read_csv(self.mimic_dir / 'hosp' / 'd_labitems.csv.gz')
            
            observations = []
            
            for chunk in pd.read_csv(labevents_path, chunksize=100000, nrows=limit):
                chunk = chunk.merge(d_labitems, on='itemid', how='left')
                
                for _, row in chunk.iterrows():
                    label = row.get('label', 'Unknown')
                    loinc_code = row.get('loinc_code')  # MIMIC-IV has LOINC codes!
                    
                    obs = self._create_observation_record(
                        patient_id=f"PID-{row['subject_id']}",
                        encounter_id=f"ENC-{row.get('hadm_id')}" if pd.notna(row.get('hadm_id')) else None,
                        record_type="laboratory",
                        effective_date=row['charttime'],
                        code_system="LOINC",
                        code=loinc_code or self.LAB_LOINC_MAP.get(label, 'unknown'),
                        display=label,
                        value=row.get('valuenum'),
                        value_text=row.get('value'),
                        unit=row.get('valueuom'),
                        status="final",
                        reference_range=f"{row.get('ref_range_lower', '')} - {row.get('ref_range_upper', '')}",
                        specimen_type=row.get('specimen_id'),
                        provenance="laboratory",
                        data_source="MIMIC-IV"
                    )
                    observations.append(obs)
                
                if limit and len(observations) >= limit:
                    break
            
            print(f"  ✓ Parsed {len(observations)} lab observations")
            return observations
            
        except Exception as e:
            print(f"❌ Error parsing labevents: {e}")
            return []
    
    def parse_prescriptions(self, limit: Optional[int] = None) -> List[Dict]:
        """Parse prescriptions into medication records"""
        print("🔄 Parsing prescriptions (medications)...")
        
        try:
            prescriptions_path = self.mimic_dir / 'hosp' / 'prescriptions.csv.gz'
            medications = []
            
            df = pd.read_csv(prescriptions_path, nrows=limit)
            
            for _, row in df.iterrows():
                med = {
                    "patient_id": f"PID-{row['subject_id']}",
                    "encounter_id": f"ENC-{row['hadm_id']}" if pd.notna(row.get('hadm_id')) else None,
                    "record_id": f"med-{uuid.uuid4()}",
                    "record_type": "medication",
                    "data_source": "MIMIC-IV",
                    "created_at": row.get('starttime'),
                    "effective_date": row.get('starttime'),
                    "end_date": row.get('stoptime'),
                    
                    # Medication details
                    "medication_code": {
                        "system": "RxNorm",
                        "code": row.get('ndc', 'unknown'),  # NDC code
                        "display": row.get('drug')
                    },
                    "display": row.get('drug'),
                    "dose": row.get('dose_val_rx'),
                    "dose_unit": row.get('dose_unit_rx'),
                    "route": row.get('route'),
                    "frequency": row.get('frequency'),
                    "status": "active" if pd.isna(row.get('stoptime')) else "completed",
                    "form": row.get('form_val_disp'),
                    
                    # Text for embedding
                    "text_for_embedding": f"{row.get('drug')} {row.get('dose_val_rx')} {row.get('dose_unit_rx')} {row.get('route')} {row.get('frequency')}",
                    "text_summary": f"{row.get('drug')} - {row.get('dose_val_rx')} {row.get('dose_unit_rx')}"
                }
                medications.append(med)
            
            print(f"  ✓ Parsed {len(medications)} medication records")
            return medications
            
        except Exception as e:
            print(f"❌ Error parsing prescriptions: {e}")
            return []
    
    def parse_diagnoses(self, limit: Optional[int] = None) -> List[Dict]:
        """Parse diagnoses into condition records"""
        print("🔄 Parsing diagnoses (conditions)...")
        
        try:
            diagnoses_path = self.mimic_dir / 'hosp' / 'diagnoses_icd.csv.gz'
            d_icd = pd.read_csv(self.mimic_dir / 'hosp' / 'd_icd_diagnoses.csv.gz')
            
            conditions = []
            df = pd.read_csv(diagnoses_path, nrows=limit)
            df = df.merge(d_icd, on='icd_code', how='left')
            
            for _, row in df.iterrows():
                condition = {
                    "patient_id": f"PID-{row['subject_id']}",
                    "encounter_id": f"ENC-{row['hadm_id']}",
                    "record_id": f"cond-{uuid.uuid4()}",
                    "record_type": "condition",
                    "data_source": "MIMIC-IV",
                    
                    # Condition details
                    "code": {
                        "system": f"ICD-{row.get('icd_version', '10')}",
                        "code": row.get('icd_code'),
                        "display": row.get('long_title')
                    },
                    "display": row.get('long_title'),
                    "icd_code": row.get('icd_code'),
                    "icd_version": row.get('icd_version'),
                    "status": "active",
                    "sequence": row.get('seq_num'),  # Primary vs secondary diagnosis
                    
                    # Text for embedding
                    "text_for_embedding": f"{row.get('long_title')} (ICD-{row.get('icd_version')}: {row.get('icd_code')})",
                    "text_summary": row.get('long_title')
                }
                conditions.append(condition)
            
            print(f"  ✓ Parsed {len(conditions)} condition records")
            return conditions
            
        except Exception as e:
            print(f"❌ Error parsing diagnoses: {e}")
            return []
    
    def _create_observation_record(
        self,
        patient_id: str,
        encounter_id: Optional[str],
        record_type: str,
        effective_date: str,
        code_system: str,
        code: str,
        display: str,
        value: Optional[float],
        value_text: Optional[str],
        unit: Optional[str],
        status: str,
        method: Optional[str] = None,
        reference_range: Optional[str] = None,
        specimen_type: Optional[str] = None,
        provenance: Optional[str] = None,
        data_source: str = "MIMIC-IV"
    ) -> Dict:
        """Create a standardized observation record"""
        
        # Normalize value
        value_normalized = value
        if value and unit:
            # Convert Fahrenheit to Celsius if needed
            if unit == 'degF' and code == '8310-5':
                value_normalized = (value - 32) * 5/9
                
        # Determine value type
        value_type = "Quantity" if value is not None else "String"
        
        # Create embedding text
        text_for_embedding = f"{effective_date}: {display} {value} {unit or ''}"
        if value_text:
            text_for_embedding += f" ({value_text})"
        
        return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "record_id": f"obs-{uuid.uuid4()}",
            "record_type": record_type,
            "data_source": data_source,
            "created_at": effective_date,
            "effective_date": effective_date,
            "provenance": provenance,
            "language": "en",
            
            # Coded value
            "code": {
                "system": code_system,
                "code": code,
                "display": display
            },
            "display": display,
            "loinc_code": code if code_system == "LOINC" else None,
            
            # Value
            "value": value,
            "value_normalized": value_normalized,
            "value_text": value_text,
            "value_type": value_type,
            "unit": unit,
            
            # Status and metadata
            "status": status,
            "method": method,
            "reference_range": reference_range,
            "specimen_type": specimen_type,
            
            # For search
            "text_for_embedding": text_for_embedding,
            "text_summary": f"{display}: {value} {unit or ''}" if value else display
        }
    
    def _infer_method(self, label: str) -> str:
        """Infer measurement method from label"""
        if 'Non Invasive' in label:
            return 'non-invasive'
        elif 'Arterial' in label:
            return 'arterial-line'
        elif 'Temperature' in label:
            if 'Oral' in label:
                return 'oral'
            elif 'Axillary' in label:
                return 'axillary'
            elif 'Rectal' in label:
                return 'rectal'
            return 'unknown'
        return 'automatic'


def main():
    """Main execution"""
    print("🏥 MIMIC-IV Structured Parser for CipherCare")
    print("="*60)
    
    # Configuration
    MIMIC_DIR = input("Enter MIMIC-IV directory path (or press Enter for './mimic-iv'): ").strip()
    if not MIMIC_DIR:
        MIMIC_DIR = "./mimic-iv"
    
    LIMIT = input("Limit records per type (or press Enter for 1000): ").strip()
    LIMIT = int(LIMIT) if LIMIT else 1000
    
    # Initialize parser
    parser = MIMICStructuredParser(MIMIC_DIR)
    
    # Parse all data types
    all_records = []
    
    print("\n" + "="*60)
    print("PARSING DATA")
    print("="*60)
    
    # Vitals
    vitals = parser.parse_chartevents(limit=LIMIT)
    all_records.extend(vitals)
    
    # Labs
    labs = parser.parse_labevents(limit=LIMIT)
    all_records.extend(labs)
    
    # Medications
    meds = parser.parse_prescriptions(limit=LIMIT)
    all_records.extend(meds)
    
    # Conditions
    conditions = parser.parse_diagnoses(limit=LIMIT)
    all_records.extend(conditions)
    
    # Save output
    output_file = "mimic_structured_cipercare.json"
    with open(output_file, 'w') as f:
        json.dump(all_records, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ PARSING COMPLETE")
    print("="*60)
    print(f"Total records: {len(all_records)}")
    print(f"  - Vitals: {len(vitals)}")
    print(f"  - Labs: {len(labs)}")
    print(f"  - Medications: {len(meds)}")
    print(f"  - Conditions: {len(conditions)}")
    print(f"\nSaved to: {output_file}")
    
    # Show sample
    if all_records:
        print("\n📄 SAMPLE RECORD:")
        print("="*60)
        print(json.dumps(all_records[0], indent=2))


if __name__ == "__main__":
    main()
