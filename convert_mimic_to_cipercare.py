"""
Convert MIMIC-III CSV data to CipherCare format

MIMIC-III is a real de-identified ICU database from Beth Israel Deaconess Medical Center.
Access: https://physionet.org/content/mimiciii/1.4/ (requires free PhysioNet account)

This script converts MIMIC-III tables to CipherCare FHIR-like format.

Required MIMIC-III files:
- PATIENTS.csv
- DIAGNOSES_ICD.csv
- PRESCRIPTIONS.csv (optional)
- ADMISSIONS.csv (optional)

Usage:
    python convert_mimic_to_cipercare.py --mimic-dir /path/to/mimic --limit 100
"""

import pandas as pd
import json
import argparse
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List


# ICD-9 to ICD-10 common mappings (abbreviated)
ICD9_TO_ICD10 = {
    '4019': 'I10',      # Hypertension
    '25000': 'E11.9',   # Diabetes Type 2
    '42731': 'I48.91',  # Atrial fibrillation
    '41401': 'I25.10',  # Coronary artery disease
    '49390': 'J44.9',   # COPD
    '5849': 'N18.9',    # Chronic kidney disease
    '53081': 'K21.9',   # GERD
    '5990': 'N39.0',    # UTI
}


def load_mimic_patients(mimic_dir: Path, limit: int = None) -> pd.DataFrame:
    """Load MIMIC-III PATIENTS.csv"""
    print("📄 Loading PATIENTS.csv...")
    patients_file = mimic_dir / "PATIENTS.csv"
    
    if not patients_file.exists():
        raise FileNotFoundError(f"PATIENTS.csv not found in {mimic_dir}")
    
    df = pd.read_csv(patients_file)
    df.columns = df.columns.str.upper()  # Normalize to uppercase
    
    if limit:
        df = df.head(limit)
    
    print(f"   ✓ Loaded {len(df)} patients")
    return df


def load_mimic_diagnoses(mimic_dir: Path, patient_ids: List) -> pd.DataFrame:
    """Load MIMIC-III DIAGNOSES_ICD.csv"""
    print("📄 Loading DIAGNOSES_ICD.csv...")
    diagnoses_file = mimic_dir / "DIAGNOSES_ICD.csv"
    
    if not diagnoses_file.exists():
        print("   ⚠️  DIAGNOSES_ICD.csv not found, skipping diagnoses")
        return pd.DataFrame()
    
    df = pd.read_csv(diagnoses_file)
    df.columns = df.columns.str.upper()  # Normalize to uppercase
    
    # Filter to our patient IDs
    df = df[df['SUBJECT_ID'].isin(patient_ids)]
    
    print(f"   ✓ Loaded {len(df)} diagnoses")
    return df


def load_mimic_prescriptions(mimic_dir: Path, patient_ids: List) -> pd.DataFrame:
    """Load MIMIC-III PRESCRIPTIONS.csv"""
    print("📄 Loading PRESCRIPTIONS.csv...")
    prescriptions_file = mimic_dir / "PRESCRIPTIONS.csv"
    
    if not prescriptions_file.exists():
        print("   ⚠️  PRESCRIPTIONS.csv not found, skipping prescriptions")
        return pd.DataFrame()
    
    df = pd.read_csv(prescriptions_file)
    df.columns = df.columns.str.upper()  # Normalize to uppercase
    df = df[df['SUBJECT_ID'].isin(patient_ids)]
    
    print(f"   ✓ Loaded {len(df)} prescriptions")
    return df


def load_mimic_icd_descriptions(mimic_dir: Path) -> Dict:
    """Load D_ICD_DIAGNOSES.csv for diagnosis descriptions"""
    print("📄 Loading D_ICD_DIAGNOSES.csv...")
    icd_file = mimic_dir / "D_ICD_DIAGNOSES.csv"
    
    if not icd_file.exists():
        print("   ⚠️  D_ICD_DIAGNOSES.csv not found, using codes only")
        return {}
    
    df = pd.read_csv(icd_file)
    df.columns = df.columns.str.upper()  # Normalize to uppercase
    
    # Create lookup dictionary
    lookup = dict(zip(df['ICD9_CODE'], df['SHORT_TITLE']))
    
    print(f"   ✓ Loaded {len(lookup)} ICD-9 descriptions")
    return lookup


def convert_patient_to_fhir(row: pd.Series, pid_number: int) -> Dict:
    """Convert MIMIC patient to FHIR Patient resource"""
    
    # Use unified PID format: PID-001, PID-002, etc.
    patient_id = f"PID-{pid_number:03d}"
    
    # Calculate age at admission (if DOB available)
    gender = row['GENDER'] if pd.notna(row['GENDER']) else 'unknown'
    gender_map = {'M': 'male', 'F': 'female'}
    
    return {
        'resourceType': 'Patient',
        'id': patient_id,
        'identifier': [{
            'system': 'MIMIC-III',
            'value': str(row['SUBJECT_ID'])
        }],
        'gender': gender_map.get(gender, 'unknown'),
        'birthDate': 'unknown',  # MIMIC dates are shifted for privacy
        'deceasedBoolean': row['EXPIRE_FLAG'] == 1 if pd.notna(row.get('EXPIRE_FLAG')) else False
    }


def convert_diagnosis_to_fhir(row: pd.Series, icd_lookup: Dict) -> Dict:
    """Convert MIMIC diagnosis to FHIR Condition resource"""
    
    patient_id = f"MIMIC-{row['SUBJECT_ID']}"
    icd9_code = str(row['ICD9_CODE'])
    
    # Get description
    description = icd_lookup.get(icd9_code, f"ICD-9: {icd9_code}")
    
    # Try to map to ICD-10
    icd10_code = ICD9_TO_ICD10.get(icd9_code, icd9_code)
    
    return {
        'resourceType': 'Condition',
        'id': str(uuid.uuid4()),
        'subject': {'reference': f'Patient/{patient_id}'},
        'code': {
            'coding': [
                {
                    'system': 'http://hl7.org/fhir/sid/icd-9-cm',
                    'code': icd9_code,
                    'display': description
                },
                {
                    'system': 'http://hl7.org/fhir/sid/icd-10',
                    'code': icd10_code
                }
            ],
            'text': description
        },
        'clinicalStatus': {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                'code': 'active'
            }]
        },
        'category': [{
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/condition-category',
                'code': 'encounter-diagnosis'
            }]
        }]
    }


def convert_prescription_to_fhir(row: pd.Series) -> Dict:
    """Convert MIMIC prescription to FHIR MedicationRequest resource"""
    
    patient_id = f"MIMIC-{row['SUBJECT_ID']}"
    drug = row['DRUG'] if pd.notna(row['DRUG']) else 'Unknown medication'
    
    return {
        'resourceType': 'MedicationRequest',
        'id': str(uuid.uuid4()),
        'status': 'active',
        'subject': {'reference': f'Patient/{patient_id}'},
        'medicationCodeableConcept': {
            'text': drug
        },
        'dosageInstruction': [{
            'text': row['DOSE_VAL_RX'] if pd.notna(row.get('DOSE_VAL_RX')) else ''
        }]
    }


def create_clinical_summary(patient: Dict, conditions: List[Dict], medications: List[Dict]) -> str:
    """Create clinical text summary for embedding"""
    
    lines = []
    
    # Patient info
    lines.append(f"Patient ID: {patient['id']}")
    lines.append(f"Gender: {patient['gender']}")
    
    if patient.get('deceasedBoolean'):
        lines.append("Status: Deceased")
    
    # Diagnoses
    if conditions:
        lines.append("\nDiagnoses:")
        for cond in conditions:
            display = cond['code'].get('text', 'Unknown condition')
            lines.append(f"- {display}")
    
    # Medications
    if medications:
        lines.append("\nMedications:")
        for med in medications:
            drug = med['medicationCodeableConcept']['text']
            lines.append(f"- {drug}")
    
    return "\n".join(lines)


def convert_mimic_to_cipercare(mimic_dir: str, limit: int = None) -> Dict:
    """
    Convert MIMIC-III data to CipherCare format
    
    Args:
        mimic_dir: Path to MIMIC-III CSV files
        limit: Limit number of patients (for testing)
    
    Returns:
        Dict with patient bundles
    """
    
    mimic_path = Path(mimic_dir)
    
    if not mimic_path.exists():
        raise FileNotFoundError(f"MIMIC directory not found: {mimic_dir}")
    
    print(f"\n🏥 Converting MIMIC-III data from: {mimic_dir}")
    print(f"{'='*60}\n")
    
    # Load data (column normalization happens in each load function)
    patients_df = load_mimic_patients(mimic_path, limit)
    patient_ids = patients_df['SUBJECT_ID'].tolist()
    
    diagnoses_df = load_mimic_diagnoses(mimic_path, patient_ids)
    prescriptions_df = load_mimic_prescriptions(mimic_path, patient_ids)
    icd_lookup = load_mimic_icd_descriptions(mimic_path)
    
    # Convert to FHIR
    print(f"\n🔄 Converting to FHIR format...")
    
    result = {}
    pid_counter = 1  # Start from PID-001
    
    for _, patient_row in patients_df.iterrows():
        subject_id = patient_row['SUBJECT_ID']
        patient_id = f"PID-{pid_counter:03d}"  # Format: PID-001, PID-002, etc.
        
        # Convert patient
        patient = convert_patient_to_fhir(patient_row, pid_counter)
        
        # Get diagnoses for this patient
        patient_diagnoses = diagnoses_df[diagnoses_df['SUBJECT_ID'] == subject_id]
        conditions = [convert_diagnosis_to_fhir(row, icd_lookup) for _, row in patient_diagnoses.iterrows()]
        
        # Get prescriptions for this patient
        patient_prescriptions = prescriptions_df[prescriptions_df['SUBJECT_ID'] == subject_id]
        medications = [convert_prescription_to_fhir(row) for _, row in patient_prescriptions.iterrows()]
        
        # Create clinical summary
        clinical_text = create_clinical_summary(patient, conditions, medications)
        
        pid_counter += 1  # Increment for next patient
        
        result[patient_id] = {
            'patient': patient,
            'conditions': conditions,
            'medications': medications,
            'clinical_text': clinical_text
        }
    
    print(f"\n✅ Converted {len(result)} patients")
    print(f"   - Total diagnoses: {len(diagnoses_df)}")
    print(f"   - Total medications: {len(prescriptions_df)}")
    
    return result


def save_to_json(data: Dict, output_path: str):
    """Save to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\n💾 Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Convert MIMIC-III data to CipherCare format')
    parser.add_argument('--mimic-dir', required=True, help='Path to MIMIC-III CSV directory')
    parser.add_argument('--output', default='mimic_converted.json', help='Output JSON file')
    parser.add_argument('--limit', type=int, help='Limit number of patients (for testing)')
    
    args = parser.parse_args()
    
    try:
        # Convert
        data = convert_mimic_to_cipercare(args.mimic_dir, args.limit)
        
        # Save
        save_to_json(data, args.output)
        
        print(f"\n{'='*60}")
        print("✅ Conversion complete!")
        print(f"{'='*60}")
        print("\n📤 To upload to CyborgDB:")
        print(f"   python upload_embeddings.py --input {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
