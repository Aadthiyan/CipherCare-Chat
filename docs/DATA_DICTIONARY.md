# Data Dictionary: Synthetic FHIR Dataset

**Dataset Location**: `data/synthetic/synthetic_fhir_dataset.json`
**Format**: FHIR R4 Bundle (Collection)
**Volume**: 300 Resources (100 Patients)

## Resources

### 1. Patient
Core demographic information.
- **id**: UUID (Synthetic)
- **name**: Official name (Family, Given)
- **gender**: Male/Female
- **birthDate**: ISO 8601 Date (YYYY-MM-DD)
- **address**: Home address (Synthetic US addresses)

### 2. Condition
Active problems or diagnoses.
- **code**: ICD-10 Code
  - `I10`: Essential hypertension
  - `E11.9`: Type 2 Diabetes
  - `J45.909`: Asthma
  - `M54.5`: Low back pain
  - `E78.5`: Hyperlipidemia
  - `F41.1`: Anxiety
- **clinicalStatus**: Active
- **verificationStatus**: Confirmed
- **subject**: Reference to Patient

### 3. DocumentReference (Clinical Note)
Unstructured clinical text notes.
- **type**: LOINC 11506-3 "Progress note"
- **description**: Plain text content (for developer convenience)
- **content.attachment.data**: Base64 encoded UTF-8 text
- **Structure**: SOAP (Subjective, Objective, Assessment, Plan) format.

## Relationships
- `Condition.subject` -> `Patient.id`
- `DocumentReference.subject` -> `Patient.id`
