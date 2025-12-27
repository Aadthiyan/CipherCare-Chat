# Where to Find & Upload Patient Data for CipherCare

## Data Sources by Category

### 🟢 **Option 1: FHIR Test Datasets** (Recommended for Demo)
Best for: Quick testing, demos, hackathons

#### Public FHIR Test Servers
```
1. Hapi FHIR Test Server
   URL: http://hapi.fhir.org/baseR4
   Use: Query FHIR resources, test samples
   Format: HL7 FHIR R4 (standard medical format)

2. IBM FHIR Server
   URL: https://github.com/IBM/FHIR
   Use: Open-source FHIR reference implementation
   Format: HL7 FHIR R4

3. Cerner Code Console
   URL: https://code.cerner.com/developer/smart-on-fhir/apps
   Use: SMART on FHIR apps, sample data
   Format: HL7 FHIR R4
```

#### How to Use with CipherCare
```python
# Example: Query from public FHIR server
import requests

# Get patient data from Hapi FHIR
response = requests.get(
    "http://hapi.fhir.org/baseR4/Patient",
    params={"_count": 10}  # Get 10 sample patients
)

fhir_bundle = response.json()

# Upload to CipherCare
# python upload_embeddings.py
```

---

### 🟡 **Option 2: Synthetic FHIR Data Generators** (Best for Privacy)
Best for: Testing without privacy concerns, scalable datasets

#### Synthea - The Gold Standard
```
Website: https://github.com/synthetichealth/synthea
What: Generates synthetic patient records (FHIR format)
Why: Realistic, privacy-safe, widely used
```

**Install & Generate Data:**
```bash
# Download Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea

# Generate 100 synthetic patients in FHIR format
./run_synthea Massachusetts -p 100

# Output: output/fhir/Patient.ndjson (FHIR format)
```

**Format Output:**
```bash
# Convert to CipherCare format
python convert_synthea_to_cipercare.py \
  --input output/fhir/Patient.ndjson \
  --output patient_data.json
```

#### Other Generators
```
1. SMART Sample Patients
   URL: https://gallery.healthsamurai.io/
   Format: FHIR JSON
   Count: 20+ pre-made patients

2. Google Synthetic Health Data
   URL: https://health.google/
   Format: FHIR
   Features: De-identified, realistic

3. Mirthful Synthea Alternative
   URL: https://github.com/sarareid/synthea-python
   Format: FHIR
   Language: Python
```

---

### 🔴 **Option 3: Real EHR Systems** (Production)
Best for: Live clinical environments

#### Common EHR Systems
```
1. Epic Systems
   API: FHIR R4 REST APIs
   Endpoint: /interconnect-fhir-oauth/api/FHIR/R4
   Auth: OAuth 2.0

2. Cerner
   API: FHIR R4 (via Code Console)
   Endpoint: /cds-services endpoint
   Auth: API Key + OAuth

3. Athenahealth
   API: FHIR R4 endpoints
   URL: https://api.platform.athenahealth.com/fhir/
   Auth: OAuth 2.0

4. NextGen Healthcare
   API: HL7 FHIR support
   Format: FHIR R4
   Auth: API token

5. Medidata
   API: FHIR R4
   Format: Clinical trial data
   Auth: OAuth 2.0
```

#### Integration Pattern
```python
# backend/data-pipeline/ehr_connector.py

from fhir.resources.bundle import Bundle
import requests

class EHRConnector:
    def __init__(self, ehr_type: str, api_key: str):
        self.ehr = ehr_type  # "epic", "cerner", "athena"
        self.api_key = api_key
        self.base_url = self._get_base_url()
    
    def fetch_patient_data(self, patient_id: str):
        """Fetch FHIR bundle from EHR"""
        endpoint = f"{self.base_url}/Patient/{patient_id}"
        response = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def sync_to_cybercare(self, fhir_bundle):
        """Process and upload to CipherCare"""
        # 1. Validate FHIR
        # 2. Extract medical data
        # 3. Encrypt (Vault Transit)
        # 4. Embed vectors
        # 5. Store in CyborgDB
```

---

### 🔵 **Option 4: Current CipherCare Format** (What Works Now)
Best for: Getting started immediately

#### Current Mock Data Format
```json
{
  "patient_id": "P123",
  "condition": "Type 2 Diabetes Mellitus",
  "status": "active",
  "onset_date": "2020-03-15",
  "medication": "Metformin 1000mg",
  "icd_code": "E11.9",
  "notes": "Well-controlled, HbA1c 7.2%"
}
```

**Upload Script:**
```bash
python upload_embeddings.py
```

**Where It's Stored:**
```
data/synthetic/synthetic_fhir_dataset.json
```

---

## Data Format Requirements for CipherCare

### ✅ Supported Formats
```
1. FHIR R4 (Primary)
   - HL7 standard format
   - JSON or XML
   - Bundles or individual resources

2. JSON (Simplified)
   - Condition/diagnosis data
   - Medication info
   - Lab results

3. CSV (Can be converted)
   - Patient ID, Condition, Date, Notes
```

### Required Fields
```json
{
  "patient_id": "string",           // Required: P123, P456, etc
  "condition": "string",             // Required: Diabetes, Asthma, etc
  "status": "active/inactive",       // Optional
  "onset_date": "YYYY-MM-DD",       // Optional
  "medication": "string",            // Optional
  "notes": "string"                 // Optional: clinical notes
}
```

---

## Step-by-Step: Add Patient Data

### **Method A: Use Existing Sample Data** (5 minutes)
```bash
# Already in the system
cd c:\Users\AADHITHAN\Downloads\Cipercare

# Just run the upload
python upload_embeddings.py
```

**Available Patients:**
- P123: Diabetes, Hypertension, Hyperlipidemia
- P456: Asthma, Allergic Rhinitis

---

### **Method B: Add Your Own Data** (15 minutes)

#### Step 1: Create JSON file
```json
// patient_data.json
{
  "patients": [
    {
      "patient_id": "P789",
      "condition": "Chronic Kidney Disease",
      "status": "active",
      "onset_date": "2018-05-10",
      "medication": "Metoprolol 50mg",
      "notes": "Stage 3 CKD, stable renal function"
    },
    {
      "patient_id": "P789",
      "condition": "Hypertension",
      "status": "active",
      "onset_date": "2015-01-20",
      "medication": "Lisinopril 20mg",
      "notes": "Blood pressure controlled"
    }
  ]
}
```

#### Step 2: Create upload script
```python
# upload_custom_data.py

import os
import json
import uuid
from pathlib import Path
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager

embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
db = CyborgLiteManager()

# Load your data
with open("patient_data.json") as f:
    data = json.load(f)

# Upload each patient record
for patient in data["patients"]:
    # Create embedding from condition text
    text = f"{patient['condition']}. {patient.get('notes', '')}"
    vector = embedder.encode(text).tolist()
    
    # Upload to CyborgDB
    db.upsert(
        record_id=str(uuid.uuid4()),
        patient_id=patient["patient_id"],
        embedding=vector,
        metadata=patient,
        collection="patient_embeddings"
    )
    print(f"✓ Uploaded: {patient['patient_id']} - {patient['condition']}")

print("✓ All data uploaded successfully!")
```

#### Step 3: Run it
```bash
python upload_custom_data.py
```

---

### **Method C: From Public FHIR Server** (30 minutes)

```python
# fetch_from_fhir_server.py

import requests
import json
from fhir.resources.bundle import Bundle

# 1. Fetch from public FHIR server
response = requests.get(
    "http://hapi.fhir.org/baseR4/Patient?_count=5",
    headers={"Accept": "application/fhir+json"}
)

bundle_data = response.json()
bundle = Bundle(**bundle_data)

# 2. Extract conditions for each patient
patients_data = []

for entry in bundle.entry:
    patient = entry.resource
    patient_id = patient.id
    
    # Fetch conditions for this patient
    conditions_response = requests.get(
        f"http://hapi.fhir.org/baseR4/Condition?patient={patient_id}",
        headers={"Accept": "application/fhir+json"}
    )
    
    conditions = conditions_response.json()
    
    for cond_entry in conditions.get("entry", []):
        condition = cond_entry["resource"]
        patients_data.append({
            "patient_id": patient_id,
            "condition": condition.get("code", {}).get("text", "Unknown"),
            "onset_date": condition.get("onsetDateTime", "unknown"),
            "status": condition.get("clinicalStatus", {}).get("coding", [{}])[0].get("code")
        })

# 3. Save and upload
with open("fhir_extracted_data.json", "w") as f:
    json.dump(patients_data, f, indent=2)

print(f"✓ Extracted {len(patients_data)} conditions from FHIR server")
```

---

## Best Practices

### ✅ DO
- Use FHIR format (what CipherCare expects)
- De-identify real patient data
- Validate data before uploading
- Encrypt sensitive fields (Vault)
- Keep audit trail

### ❌ DON'T
- Upload real patient PHI (privacy risk)
- Use unencrypted data transmission
- Skip validation
- Upload duplicate records
- Mix formats

---

## Recommended Setup for Your Project

### For Development/Demo:
```
✓ Use built-in sample data (P123, P456)
✓ Add 2-3 custom test patients
✓ Validate with small dataset
```

### For Testing:
```
✓ Use Synthea to generate 100 patients
✓ Test embedding performance
✓ Validate search accuracy
```

### For Production:
```
✓ Connect to real EHR (Epic, Cerner, etc.)
✓ Implement FHIR sync
✓ Set up scheduled imports
✓ Full encryption with Vault
```

---

## Data Sources Summary

| Source | Format | Privacy | Setup Time | Best For |
|--------|--------|---------|-----------|----------|
| Built-in (P123, P456) | JSON | ✅ Safe | 0 min | Testing |
| Synthea | FHIR R4 | ✅ Safe | 15 min | Dev/QA |
| Hapi FHIR Server | FHIR R4 | ⚠️ Sample | 5 min | Demo |
| Epic/Cerner | FHIR R4 | ✅ Real | 2 weeks | Production |
| Custom JSON | JSON | Your choice | 10 min | Specific use case |

---

## Quick Start: Add 3 More Patients

Edit [upload_embeddings.py](upload_embeddings.py#L100):

```python
sample_patients = {
    "P123": [...existing...],
    "P456": [...existing...],
    "P789": [  # NEW
        {
            "text": "Chronic Kidney Disease Stage 3. Patient on Metoprolol 50mg. Stable renal function.",
            "metadata": {
                "condition": "Chronic Kidney Disease",
                "status": "active",
                "medication": "Metoprolol",
                "patient_id": "P789"
            }
        }
    ],
    "P101": [  # NEW
        {
            "text": "COPD exacerbation history. On Albuterol inhaler. FEV1 65% predicted.",
            "metadata": {
                "condition": "COPD",
                "status": "active",
                "medication": "Albuterol",
                "patient_id": "P101"
            }
        }
    ]
}
```

Then run:
```bash
python upload_embeddings.py
```

---

## My Recommendation

**For Your Current Project:**

1. **Start with:** Current mock data (P123, P456)
   - Already tested
   - No setup needed

2. **Add next:** 3-5 Synthea-generated patients
   - Realistic medical data
   - Privacy-safe
   - Good for demos

3. **Eventually:** Connect to real EHR
   - Full FHIR integration
   - Production-ready
   - Requires Epic/Cerner API

This progression from demo → realistic → production is what enterprise healthcare uses.

