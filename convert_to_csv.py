"""
Convert structured JSON to CSV for faster bulk upload
CSV is 3-4x faster than JSON for large datasets
"""

import json
import csv
from pathlib import Path


def json_to_csv(input_file="synthea_structured_FIXED.json", output_file="synthea_structured.csv"):
    """Convert structured JSON to CSV format"""
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    print(f"Converting {len(data)} records to CSV...")
    
    # Define CSV columns
    fieldnames = [
        'patient_id', 'record_id', 'record_type', 'data_source',
        'effective_date', 'created_at', 'provenance', 'language',
        'code_system', 'code', 'display', 'loinc_code', 'snomed_code', 'rxnorm_code',
        'value', 'value_normalized', 'unit', 'value_type', 'status',
        'text_for_embedding', 'text_summary'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            # Flatten the record
            row = {
                'patient_id': record.get('patient_id', ''),
                'record_id': record.get('record_id', ''),
                'record_type': record.get('record_type', ''),
                'data_source': record.get('data_source', ''),
                'effective_date': record.get('effective_date', ''),
                'created_at': record.get('created_at', ''),
                'provenance': record.get('provenance', ''),
                'language': record.get('language', ''),
                'display': record.get('display', ''),
                'loinc_code': record.get('loinc_code', ''),
                'snomed_code': record.get('snomed_code', ''),
                'rxnorm_code': record.get('rxnorm_code', ''),
                'value': record.get('value', ''),
                'value_normalized': record.get('value_normalized', ''),
                'unit': record.get('unit', ''),
                'value_type': record.get('value_type', ''),
                'status': record.get('status', ''),
                'text_for_embedding': record.get('text_for_embedding', ''),
                'text_summary': record.get('text_summary', '')
            }
            
            # Extract code info
            code = record.get('code', {})
            if isinstance(code, dict):
                row['code_system'] = code.get('system', '')
                row['code'] = code.get('code', '')
            
            # Handle medication_code
            med_code = record.get('medication_code', {})
            if isinstance(med_code, dict):
                row['code_system'] = med_code.get('system', '')
                row['code'] = med_code.get('code', '')
            
            writer.writerow(row)
    
    print(f"✓ Saved to {output_file}")
    
    # Show file size
    size_mb = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"  File size: {size_mb:.2f} MB")
    
    print("\n✓ CSV is ready for fast upload!")
    print(f"  Estimated upload time: {len(data)/200:.1f} minutes (vs {len(data)/13:.1f} min with JSON)")


if __name__ == "__main__":
    json_to_csv()
