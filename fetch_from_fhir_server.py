"""
Fetch structured clinical data from public FHIR servers
Quick way to get properly formatted data for testing CipherCare
"""

import requests
import json
from typing import List, Dict, Optional
from pathlib import Path
import uuid


class FHIRServerFetcher:
    """Fetch structured data from public FHIR servers"""
    
    def __init__(self, base_url: str = "http://hapi.fhir.org/baseR4"):
        """Initialize with FHIR server URL"""
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json"
        }
        print(f"✓ Connected to FHIR server: {self.base_url}")
    
    def fetch_patients(self, count: int = 10) -> List[str]:
        """Fetch patient IDs"""
        print(f"📥 Fetching {count} patients...")
        
        url = f"{self.base_url}/Patient"
        params = {"_count": count}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            bundle = response.json()
            patient_ids = []
            
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Patient':
                    patient_ids.append(resource.get('id'))
            
            print(f"  ✓ Found {len(patient_ids)} patients")
            return patient_ids
        
        except Exception as e:
            print(f"  ❌ Error fetching patients: {e}")
            return []
    
    def fetch_observations(self, patient_id: str) -> List[Dict]:
        """Fetch observations (vitals and labs) for a patient"""
        
        url = f"{self.base_url}/Observation"
        params = {
            "patient": patient_id,
            "_count": 100
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            bundle = response.json()
            observations = []
            
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Observation':
                    obs = self._parse_observation(resource, f"PID-{patient_id}")
                    if obs:
                        observations.append(obs)
            
            return observations
        
        except Exception as e:
            print(f"    ⚠️  Error fetching observations for {patient_id}: {e}")
            return []
    
    def fetch_conditions(self, patient_id: str) -> List[Dict]:
        """Fetch conditions for a patient"""
        
        url = f"{self.base_url}/Condition"
        params = {
            "patient": patient_id,
            "_count": 50
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            bundle = response.json()
            conditions = []
            
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Condition':
                    cond = self._parse_condition(resource, f"PID-{patient_id}")
                    if cond:
                        conditions.append(cond)
            
            return conditions
        
        except Exception as e:
            print(f"    ⚠️  Error fetching conditions for {patient_id}: {e}")
            return []
    
    def fetch_medications(self, patient_id: str) -> List[Dict]:
        """Fetch medications for a patient"""
        
        url = f"{self.base_url}/MedicationRequest"
        params = {
            "patient": patient_id,
            "_count": 50
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            bundle = response.json()
            medications = []
            
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'MedicationRequest':
                    med = self._parse_medication(resource, f"PID-{patient_id}")
                    if med:
                        medications.append(med)
            
            return medications
        
        except Exception as e:
            print(f"    ⚠️  Error fetching medications for {patient_id}: {e}")
            return []
    
    def _parse_observation(self, resource: Dict, patient_id: str) -> Optional[Dict]:
        """Parse FHIR Observation (same as Synthea parser)"""
        
        # Extract code (LOINC)
        code_obj = resource.get('code', {})
        loinc_code = None
        display = None
        
        for coding in code_obj.get('coding', []):
            if 'loinc' in coding.get('system', '').lower():
                loinc_code = coding.get('code')
                display = coding.get('display')
                break
        
        if not loinc_code:
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
            value_type = "CodeableConcept"
        elif 'valueString' in resource:
            value_text = resource['valueString']
            value_type = "String"
        
        # Extract dates
        effective_date = resource.get('effectiveDateTime') or resource.get('issued')
        
        # Extract encounter
        encounter_id = None
        if 'encounter' in resource:
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = f"ENC-{encounter_ref.split('/')[-1]}" if encounter_ref else None
        
        # Determine record type
        category = resource.get('category', [{}])[0] if resource.get('category') else {}
        category_code = None
        if category.get('coding'):
            category_code = category['coding'][0].get('code')
        
        record_type = "vital" if category_code == "vital-signs" else "laboratory"
        
        # Reference range
        reference_range = None
        if 'referenceRange' in resource and resource['referenceRange']:
            ref_range = resource['referenceRange'][0]
            low = ref_range.get('low', {}).get('value')
            high = ref_range.get('high', {}).get('value')
            if low or high:
                reference_range = f"{low or ''} - {high or ''}"
        
        # Interpretation
        interpretation = None
        if 'interpretation' in resource and resource['interpretation']:
            interp_codings = resource['interpretation'][0].get('coding', [])
            if interp_codings:
                interpretation = interp_codings[0].get('code')
        
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
            "data_source": "FHIR-Server",
            "created_at": effective_date,
            "effective_date": effective_date,
            "provenance": "fhir-server",
            "language": "en",
            
            "code": {
                "system": "LOINC",
                "code": loinc_code or "unknown",
                "display": display
            },
            "display": display,
            "loinc_code": loinc_code,
            
            "value": value,
            "value_normalized": value,
            "value_text": value_text,
            "value_type": value_type,
            "unit": unit,
            
            "status": resource.get('status', 'final'),
            "reference_range": reference_range,
            "interpretation": interpretation,
            
            "text_for_embedding": text_for_embedding,
            "text_summary": f"{display}: {value} {unit or ''}" if value else display
        }
    
    def _parse_condition(self, resource: Dict, patient_id: str) -> Optional[Dict]:
        """Parse FHIR Condition"""
        
        code_obj = resource.get('code', {})
        snomed_code = None
        icd_code = None
        display = None
        
        for coding in code_obj.get('coding', []):
            system = coding.get('system', '').lower()
            if 'snomed' in system:
                snomed_code = coding.get('code')
                display = coding.get('display')
            elif 'icd' in system:
                icd_code = coding.get('code')
                if not display:
                    display = coding.get('display')
        
        if not display:
            display = code_obj.get('text', 'Unknown')
        
        onset_date = resource.get('onsetDateTime') or resource.get('recordedDate')
        
        clinical_status = None
        if 'clinicalStatus' in resource:
            status_codings = resource['clinicalStatus'].get('coding', [])
            if status_codings:
                clinical_status = status_codings[0].get('code')
        
        text_for_embedding = f"{onset_date}: {display}"
        if clinical_status:
            text_for_embedding += f" (status: {clinical_status})"
        
        return {
            "patient_id": patient_id,
            "record_id": f"cond-{resource.get('id', uuid.uuid4())}",
            "record_type": "condition",
            "data_source": "FHIR-Server",
            "effective_date": onset_date,
            "code": {
                "system": "SNOMED-CT",
                "code": snomed_code or icd_code or "unknown",
                "display": display
            },
            "display": display,
            "snomed_code": snomed_code,
            "icd_code": icd_code,
            "status": clinical_status or "active",
            "text_for_embedding": text_for_embedding,
            "text_summary": display
        }
    
    def _parse_medication(self, resource: Dict, patient_id: str) -> Optional[Dict]:
        """Parse FHIR MedicationRequest"""
        
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
        
        start_date = resource.get('authoredOn')
        
        text_for_embedding = f"{start_date}: {display}"
        
        return {
            "patient_id": patient_id,
            "record_id": f"med-{resource.get('id', uuid.uuid4())}",
            "record_type": "medication",
            "data_source": "FHIR-Server",
            "effective_date": start_date,
            "medication_code": {
                "system": "RxNorm",
                "code": rxnorm_code or "unknown",
                "display": display
            },
            "display": display,
            "rxnorm_code": rxnorm_code,
            "status": resource.get('status', 'active'),
            "text_for_embedding": text_for_embedding,
            "text_summary": display
        }


def main():
    """Main execution"""
    print("🏥 FHIR Server Data Fetcher for CipherCare")
    print("="*60)
    
    # Configuration
    print("\nFHIR Server Options:")
    print("  1. Hapi FHIR (http://hapi.fhir.org/baseR4)")
    print("  2. Custom URL")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    if choice == "2":
        base_url = input("Enter FHIR server URL: ").strip()
    else:
        base_url = "http://hapi.fhir.org/baseR4"
    
    patient_count = input("Number of patients to fetch [10]: ").strip() or "10"
    patient_count = int(patient_count)
    
    # Initialize fetcher
    fetcher = FHIRServerFetcher(base_url)
    
    # Fetch patients
    patient_ids = fetcher.fetch_patients(count=patient_count)
    
    if not patient_ids:
        print("❌ No patients found")
        return
    
    # Fetch data for each patient
    all_records = []
    
    print(f"\n🔄 Fetching data for {len(patient_ids)} patients...")
    
    for i, patient_id in enumerate(patient_ids, 1):
        print(f"\n  Patient {i}/{len(patient_ids)}: {patient_id}")
        
        # Fetch observations
        observations = fetcher.fetch_observations(patient_id)
        print(f"    ✓ Observations: {len(observations)}")
        all_records.extend(observations)
        
        # Fetch conditions
        conditions = fetcher.fetch_conditions(patient_id)
        print(f"    ✓ Conditions: {len(conditions)}")
        all_records.extend(conditions)
        
        # Fetch medications
        medications = fetcher.fetch_medications(patient_id)
        print(f"    ✓ Medications: {len(medications)}")
        all_records.extend(medications)
    
    # Save output
    output_file = "fhir_server_data.json"
    with open(output_file, 'w') as f:
        json.dump(all_records, f, indent=2)
    
    # Statistics
    record_types = {}
    for record in all_records:
        rtype = record.get('record_type', 'unknown')
        record_types[rtype] = record_types.get(rtype, 0) + 1
    
    print("\n" + "="*60)
    print("✅ FETCH COMPLETE")
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
    
    print("\n✅ NEXT STEP:")
    print("="*60)
    print("Upload to CyborgDB:")
    print(f"  python upload_structured_data.py")
    print("="*60)


if __name__ == "__main__":
    main()
