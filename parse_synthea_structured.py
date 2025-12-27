Parse Synthea FHIR bundles into CipherCare's structured format
Extracts granular observations with LOINC codes, vitals, labs, meds, conditions
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import uuid
from datetime import datetime


class SyntheaStructuredParser:
    """Parse Synthea FHIR bundles into granular observation records"""
    
    def __init__(self, synthea_dir: str):
        """Initialize with Synthea output directory"""
        self.synthea_dir = Path(synthea_dir)
        
    def parse_all_bundles(self, limit: Optional[int] = None) -> List[Dict]:
        """Parse all FHIR bundles in directory"""
        print("📥 Loading Synthea FHIR bundles...")
        
        bundle_files = list(self.synthea_dir.glob("*.json"))
        
        if not bundle_files:
            print(f"❌ No JSON files found in {self.synthea_dir}")
            return []
        
        print(f"  Found {len(bundle_files)} bundle files")
        
        all_records = []
        
        for bundle_file in bundle_files[:limit] if limit else bundle_files:
            try:
                with open(bundle_file, 'r') as f:
                    bundle = json.load(f)
                
                records = self.parse_bundle(bundle)
                all_records.extend(records)
                
                print(f"  ✓ Parsed {bundle_file.name}: {len(records)} records")
                
            except Exception as e:
                print(f"  ⚠️  Error parsing {bundle_file.name}: {e}")
        
        print(f"\n✓ Total records parsed: {len(all_records)}")
        return all_records
    
    def parse_bundle(self, bundle: Dict) -> List[Dict]:
        """Parse a single FHIR bundle"""
        records = []
        
        # Extract patient ID first
        patient_id = None
        for entry in bundle.get('entry', []):
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Patient':
                patient_id = f"PID-{resource.get('id')}"
                break
        
        if not patient_id:
            return []
        
        # Parse each resource type
        for entry in bundle.get('entry', []):
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType')
            
            if resource_type == 'Observation':
                obs = self._parse_observation(resource, patient_id)
                if obs:
                    records.append(obs)
            
            elif resource_type == 'Condition':
                cond = self._parse_condition(resource, patient_id)
                if cond:
                    records.append(cond)
            
            elif resource_type == 'MedicationRequest':
                med = self._parse_medication(resource, patient_id)
                if med:
                    records.append(med)
            
            elif resource_type == 'Procedure':
                proc = self._parse_procedure(resource, patient_id)
                if proc:
                    records.append(proc)
        
        return records
    
    def _parse_observation(self, resource: Dict, patient_id: str) -> Optional[Dict]:
        """Parse FHIR Observation into structured record"""
        
        # Extract code (LOINC)
        code_obj = resource.get('code', {})
        loinc_code = None
        display = None
        
        for coding in code_obj.get('coding', []):
            if coding.get('system') == 'http://loinc.org':
                loinc_code = coding.get('code')
                display = coding.get('display')
                break
        
        if not loinc_code:
            # Fallback to text
            display = code_obj.get('text', 'Unknown')
        
        # Extract value
        value = None
        value_text = None
        unit = None
        value_type = None
        
        if 'valueQuantity' in resource:
            value_qty = resource['valueQuantity']
            value = value_qty.get('value')
            unit = value_qty.get('unit') or value_qty.get('code')
            value_type = "Quantity"
        
        elif 'valueCodeableConcept' in resource:
            value_concept = resource['valueCodeableConcept']
            value_text = value_concept.get('text')
            if value_concept.get('coding'):
                value_text = value_concept['coding'][0].get('display', value_text)
            value_type = "CodeableConcept"
        
        elif 'valueString' in resource:
            value_text = resource['valueString']
            value_type = "String"
        
        # Extract dates
        effective_date = resource.get('effectiveDateTime') or resource.get('issued')
        
        # Extract encounter reference
        encounter_id = None
        if 'encounter' in resource:
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = f"ENC-{encounter_ref.split('/')[-1]}" if encounter_ref else None
        
        # Determine record type (vital vs lab)
        record_type = self._classify_observation(loinc_code, display)
        
        # Extract reference range
        reference_range = None
        if 'referenceRange' in resource:
            ref_ranges = resource['referenceRange']
            if ref_ranges:
                low = ref_ranges[0].get('low', {}).get('value')
                high = ref_ranges[0].get('high', {}).get('value')
                if low or high:
                    reference_range = f"{low or ''} - {high or ''}"
        
        # Extract interpretation
        interpretation = None
        if 'interpretation' in resource:
            interp_codings = resource['interpretation'][0].get('coding', [])
            if interp_codings:
                interpretation = interp_codings[0].get('code')  # e.g., "H", "L", "N"
        
        # Create embedding text
        text_for_embedding = f"{effective_date}: {display}"
        if value:
            text_for_embedding += f" {value} {unit or ''}"
        if value_text:
            text_for_embedding += f" {value_text}"
        if interpretation:
            text_for_embedding += f" ({interpretation})"
        
        return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "record_id": f"obs-{resource.get('id', uuid.uuid4())}",
            "record_type": record_type,
            "data_source": "Synthea",
            "created_at": effective_date,
            "effective_date": effective_date,
            "provenance": "synthea-generator",
            "language": "en",
            
            # Coded value
            "code": {
                "system": "LOINC",
                "code": loinc_code or "unknown",
                "display": display
            },
            "display": display,
            "loinc_code": loinc_code,
            
            # Value
            "value": value,
            "value_normalized": value,  # Already in standard units from Synthea
            "value_text": value_text,
            "value_type": value_type,
            "unit": unit,
            
            # Status and metadata
            "status": resource.get('status', 'final'),
            "method": resource.get('method', {}).get('text'),
            "reference_range": reference_range,
            "interpretation": interpretation,
            
            # For search
            "text_for_embedding": text_for_embedding,
            "text_summary": f"{display}: {value} {unit or ''}" if value else display
        }
    
    def _parse_condition(self, resource: Dict, patient_id: str) -> Optional[Dict]:
        """Parse FHIR Condition into structured record"""
        
        # Extract code (SNOMED)
        code_obj = resource.get('code', {})
        snomed_code = None
        icd_code = None
        display = None
        
        for coding in code_obj.get('coding', []):
            system = coding.get('system', '')
            if 'snomed' in system.lower():
                snomed_code = coding.get('code')
                display = coding.get('display')
            elif 'icd' in system.lower():
                icd_code = coding.get('code')
                if not display:
                    display = coding.get('display')
        
        if not display:
            display = code_obj.get('text', 'Unknown')
        
        # Extract dates
        onset_date = resource.get('onsetDateTime') or resource.get('recordedDate')
        abatement_date = resource.get('abatementDateTime')
        
        # Extract status
        clinical_status = None
        if 'clinicalStatus' in resource:
            status_codings = resource['clinicalStatus'].get('coding', [])
            if status_codings:
                clinical_status = status_codings[0].get('code')  # active, resolved, etc.
        
        # Extract severity
        severity = None
        if 'severity' in resource:
            severity_codings = resource['severity'].get('coding', [])
            if severity_codings:
                severity = severity_codings[0].get('display')
        
        # Extract encounter
        encounter_id = None
        if 'encounter' in resource:
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = f"ENC-{encounter_ref.split('/')[-1]}" if encounter_ref else None
        
        # Create embedding text
        text_for_embedding = f"{onset_date}: {display}"
        if clinical_status:
            text_for_embedding += f" (status: {clinical_status})"
        if severity:
            text_for_embedding += f" (severity: {severity})"
        
        return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "record_id": f"cond-{resource.get('id', uuid.uuid4())}",
            "record_type": "condition",
            "data_source": "Synthea",
            "created_at": resource.get('recordedDate'),
            "effective_date": onset_date,
            "end_date": abatement_date,
            "provenance": "synthea-generator",
            "language": "en",
            
            # Coded value
            "code": {
                "system": "SNOMED-CT",
                "code": snomed_code or icd_code or "unknown",
                "display": display
            },
            "display": display,
            "snomed_code": snomed_code,
            "icd_code": icd_code,
            
            # Status
            "status": clinical_status or "active",
            "severity": severity,
            
            # For search
            "text_for_embedding": text_for_embedding,
            "text_summary": display
        }
    
    def _parse_medication(self, resource: Dict, patient_id: str) -> Optional[Dict]:
        """Parse FHIR MedicationRequest into structured record"""
        
        # Extract medication code (RxNorm)
        med_obj = resource.get('medicationCodeableConcept', {})
        rxnorm_code = None
        display = None
        
        for coding in med_obj.get('coding', []):
            if 'rxnorm' in coding.get('system', '').lower():
                rxnorm_code = coding.get('code')
                display = coding.get('display')
                break
        
        if not display:
            display = med_obj.get('text', 'Unknown')
        
        # Extract dosage
        dose = None
        dose_unit = None
        route = None
        frequency = None
        
        if 'dosageInstruction' in resource and resource['dosageInstruction']:
            dosage = resource['dosageInstruction'][0]
            
            # Route
            if 'route' in dosage:
                route_codings = dosage['route'].get('coding', [])
                if route_codings:
                    route = route_codings[0].get('display')
            
            # Dose
            if 'doseAndRate' in dosage and dosage['doseAndRate']:
                dose_qty = dosage['doseAndRate'][0].get('doseQuantity', {})
                dose = dose_qty.get('value')
                dose_unit = dose_qty.get('unit')
            
            # Frequency
            if 'timing' in dosage:
                timing = dosage['timing']
                if 'code' in timing:
                    freq_codings = timing['code'].get('coding', [])
                    if freq_codings:
                        frequency = freq_codings[0].get('display')
        
        # Extract dates
        start_date = resource.get('authoredOn')
        
        # Extract encounter
        encounter_id = None
        if 'encounter' in resource:
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = f"ENC-{encounter_ref.split('/')[-1]}" if encounter_ref else None
        
        # Create embedding text
        text_for_embedding = f"{start_date}: {display}"
        if dose:
            text_for_embedding += f" {dose} {dose_unit or ''}"
        if route:
            text_for_embedding += f" {route}"
        if frequency:
            text_for_embedding += f" {frequency}"
        
        return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "record_id": f"med-{resource.get('id', uuid.uuid4())}",
            "record_type": "medication",
            "data_source": "Synthea",
            "created_at": start_date,
            "effective_date": start_date,
            "provenance": "synthea-generator",
            "language": "en",
            
            # Medication details
            "medication_code": {
                "system": "RxNorm",
                "code": rxnorm_code or "unknown",
                "display": display
            },
            "display": display,
            "rxnorm_code": rxnorm_code,
            "dose": dose,
            "dose_unit": dose_unit,
            "route": route,
            "frequency": frequency,
            "status": resource.get('status', 'active'),
            
            # For search
            "text_for_embedding": text_for_embedding,
            "text_summary": f"{display} - {dose} {dose_unit or ''}" if dose else display
        }
    
    def _parse_procedure(self, resource: Dict, patient_id: str) -> Optional[Dict]:
        """Parse FHIR Procedure into structured record"""
        
        # Extract code (SNOMED)
        code_obj = resource.get('code', {})
        snomed_code = None
        display = None
        
        for coding in code_obj.get('coding', []):
            if 'snomed' in coding.get('system', '').lower():
                snomed_code = coding.get('code')
                display = coding.get('display')
                break
        
        if not display:
            display = code_obj.get('text', 'Unknown')
        
        # Extract date
        performed_date = resource.get('performedDateTime') or resource.get('performedPeriod', {}).get('start')
        
        # Extract encounter
        encounter_id = None
        if 'encounter' in resource:
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = f"ENC-{encounter_ref.split('/')[-1]}" if encounter_ref else None
        
        return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "record_id": f"proc-{resource.get('id', uuid.uuid4())}",
            "record_type": "procedure",
            "data_source": "Synthea",
            "created_at": performed_date,
            "effective_date": performed_date,
            "provenance": "synthea-generator",
            "language": "en",
            
            # Procedure details
            "code": {
                "system": "SNOMED-CT",
                "code": snomed_code or "unknown",
                "display": display
            },
            "display": display,
            "snomed_code": snomed_code,
            "status": resource.get('status', 'completed'),
            
            # For search
            "text_for_embedding": f"{performed_date}: {display}",
            "text_summary": display
        }
    
    def _classify_observation(self, loinc_code: Optional[str], display: str) -> str:
        """Classify observation as vital, laboratory, or other"""
        
        # Common vital LOINC codes
        vital_codes = {
            '8867-4',  # Heart rate
            '9279-1',  # Respiratory rate
            '8310-5',  # Body temperature
            '59408-5', '2708-6',  # SpO2
            '8480-6',  # Systolic BP
            '8462-4',  # Diastolic BP
            '29463-7', # Weight
            '8302-2',  # Height
            '38208-5', # Pain
        }
        
        if loinc_code in vital_codes:
            return "vital"
        
        # Check display text
        vital_keywords = ['heart rate', 'blood pressure', 'temperature', 'respiratory', 'spo2', 'oxygen', 'weight', 'height', 'pain']
        if any(keyword in display.lower() for keyword in vital_keywords):
            return "vital"
        
        return "laboratory"


def main():
    """Main execution"""
    print("🏥 Synthea Structured Parser for CipherCare")
    print("="*60)
    
    # Configuration
    SYNTHEA_DIR = input("Enter Synthea output directory (or press Enter for './synthea/output/fhir'): ").strip()
    if not SYNTHEA_DIR:
        SYNTHEA_DIR = "./synthea/output/fhir"
    
    LIMIT = input("Limit number of bundles (or press Enter for all): ").strip()
    LIMIT = int(LIMIT) if LIMIT else None
    
    # Initialize parser
    parser = SyntheaStructuredParser(SYNTHEA_DIR)
    
    # Parse all bundles
    all_records = parser.parse_all_bundles(limit=LIMIT)
    
    # Save output
    output_file = "synthea_structured_cipercare.json"
    with open(output_file, 'w') as f:
        json.dump(all_records, f, indent=2)
    
    # Statistics
    record_types = {}
    for record in all_records:
        rtype = record.get('record_type', 'unknown')
        record_types[rtype] = record_types.get(rtype, 0) + 1
    
    print("\n" + "="*60)
    print("✅ PARSING COMPLETE")
    print("="*60)
    print(f"Total records: {len(all_records)}")
    for rtype, count in sorted(record_types.items()):
        print(f"  - {rtype}: {count}")
    print(f"\nSaved to: {output_file}")
    
    # Show sample
    if all_records:
        print("\n📄 SAMPLE RECORD:")
        print("="*60)
        print(json.dumps(all_records[0], indent=2))


if __name__ == "__main__":
    main()
