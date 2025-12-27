# Open Source Patient Records for CipherCare

## 🎯 Quick Answer: Best Sources for Your System

### ✅ Already Available (Use These First!)
Your system already has synthetic patient data at:
- `data/synthetic/synthetic_fhir_dataset.json` (270 KB, ~100 patients)
- `data/synthetic/deidentified_dataset.json` (275 KB)

**To use existing data:**
```bash
python upload_embeddings.py
```

---

## 🌐 Top Open Source Patient Record Datasets

### 1. **Synthea™ - Synthetic Patient Generator** ⭐ RECOMMENDED
**Best Match for Your System**

**What:** The most realistic synthetic patient data generator, used by hospitals, startups, and researchers.

**Format:** FHIR R4 (same as your system!)

**Includes:**
- Patient demographics
- Conditions (ICD-10 codes)
- Medications (RxNorm)
- Lab results
- Clinical notes
- Encounters, procedures, allergies

**How to Get Data:**

#### Option A: Use Pre-Generated Datasets
```bash
# Download from Synthea's public datasets
# 1K patients (FHIR format) - ~50 MB
wget https://synthetichealth.github.io/synthea-sample-data/downloads/10k_synthea_covid19_csv.zip

# or visit: https://synthea.mitre.org/downloads
```

#### Option B: Generate Custom Data (More Flexible)
```bash
# Install Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea

# Generate 50 patients in Massachusetts
./run_synthea Massachusetts -p 50

# Output location: output/fhir/
# Files: Patient.ndjson, Condition.ndjson, Medication.ndjson, etc.
```

**Convert to CipherCare Format:**
```python
# See script: convert_synthea_to_cipercare.py (below)
python convert_synthea_to_cipercare.py --input output/fhir/ --output patient_data.json
```

---

### 2. **MIMIC-III Clinical Database** 🏥
**Real De-Identified Hospital Data**

**What:** Real patient data from Beth Israel Deaconess Medical Center (60,000+ ICU admissions)

**Format:** CSV tables (easily convertible)

**Access:** Free with PhysioNet account (requires training certificate)

**Website:** https://physionet.org/content/mimiciii/1.4/

**Includes:**
- Demographics
- Diagnoses (ICD-9 codes)
- Medications
- Lab results
- Vital signs
- ICU stay details

**How to Get:**
1. Create PhysioNet account: https://physionet.org/register/
2. Complete CITI Data/Specimens training (2 hours): https://physionet.org/about/citi-course/
3. Sign Data Use Agreement
4. Download dataset

**Why Use:** Most realistic data (actual hospital records), comprehensive

---

### 3. **CMS Synthetic Patient Data** 🇺🇸
**Government-Provided Test Data**

**What:** CMS (Medicare/Medicaid) test data for developers

**Format:** FHIR, CSV

**Access:** Public, no registration

**Website:** https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files

**Includes:**
- Claims data
- Diagnoses
- Procedures
- Prescriptions
- Demographics

**How to Get:**
```bash
# Download directly
wget https://www.cms.gov/files/zip/2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf.zip
```

---

### 4. **Open Health Data (NHS UK)** 🇬🇧
**UK National Health Service Test Data**

**What:** Anonymized NHS patient records

**Format:** FHIR, JSON

**Access:** Public

**Website:** https://digital.nhs.uk/services/fhir-apis

**Test Data Portal:** https://digital.nhs.uk/developer/api-catalogue

**Includes:**
- GP records
- Hospital episodes
- Prescriptions
- Referrals

---

### 5. **SMART Health IT Sample Patients** 💡
**Quick Demo Data**

**What:** 20 pre-built FHIR patient records for testing

**Format:** FHIR R4 (perfect for your system!)

**Access:** Public, instant

**Website:** https://docs.smarthealthit.org/

**How to Get:**
```bash
# API Access (no auth needed)
curl https://r4.smarthealthit.org/Patient

# Or download sample bundle
wget https://github.com/smart-on-fhir/sample-patients-stu3/archive/master.zip
```

**Why Use:** Fast setup, FHIR native, works immediately

---

### 6. **Healthcare.gov Sample Test Data** 🏛️
**Insurance Marketplace Test Data**

**What:** Test data for healthcare applications

**Format:** XML, JSON

**Access:** Public

**Website:** https://www.healthcare.gov/

---

## 📊 Comparison Table

| Source | Format | Size | Realism | Setup Time | Privacy |
|--------|--------|------|---------|------------|---------|
| **Synthea** ⭐ | FHIR | Custom | High | 15 min | Synthetic ✅ |
| **MIMIC-III** | CSV | 60K pts | Highest | 3 hours | De-identified ✅ |
| **CMS Synthetic** | FHIR/CSV | 2M pts | Medium | 10 min | Synthetic ✅ |
| **SMART Health IT** | FHIR | 20 pts | Medium | 5 min | Synthetic ✅ |
| **NHS Open Data** | FHIR | Various | High | 20 min | Anonymized ✅ |

---

## 🚀 Quick Start: Add Synthea Data to CipherCare

### Step 1: Generate Data (Choose One)

#### Option A: Use Existing Synthea Sample Data
```bash
# Download pre-generated dataset
mkdir -p temp_data
cd temp_data
wget https://storage.googleapis.com/synthea-public/synthea_sample_data_fhir_latest.zip
unzip synthea_sample_data_fhir_latest.zip
```

#### Option B: Generate Fresh Data (Requires Java)
```bash
# Clone and run Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./run_synthea -p 100  # Generate 100 patients
```

### Step 2: Convert to CipherCare Format
Use the conversion script below (`convert_synthea_to_cipercare.py`)

### Step 3: Upload to Your System
```bash
python upload_synthea_data.py
```

---

## 📝 Required Data Fields for CipherCare

Your system expects FHIR-compatible data with these fields:

```json
{
  "resourceType": "Patient",
  "id": "unique-id",
  "name": [{"given": ["John"], "family": "Doe"}],
  "gender": "male",
  "birthDate": "1980-01-01",
  "condition": [
    {
      "code": {"coding": [{"system": "ICD-10", "code": "E11.9"}]},
      "display": "Type 2 diabetes"
    }
  ],
  "notes": "Clinical text for embeddings"
}
```

---

## 🔒 Privacy & Compliance

All recommended sources are:
- ✅ **HIPAA-compliant** (synthetic or de-identified)
- ✅ **Safe for development/testing**
- ✅ **No real patient data**
- ✅ **Free to use**

---

## 🎓 Recommended Learning Path

### For Quick Demo (Today):
1. Use existing `data/synthetic/` files → `python upload_embeddings.py`
2. Or download SMART Health IT samples (5 min setup)

### For Realistic Testing (This Week):
1. Generate Synthea data (100-1000 patients)
2. Convert and upload to CipherCare
3. Test queries and UI

### For Production Simulation (Next Week):
1. Request MIMIC-III access
2. Complete training
3. Use for comprehensive testing

---

## 📞 Need Help?

- **Synthea Issues:** https://github.com/synthetichealth/synthea/issues
- **MIMIC-III:** https://mimic.mit.edu/
- **FHIR Spec:** https://www.hl7.org/fhir/

---

## Next Steps

1. **Quick Test:** Run `python generate_data.py` to create more synthetic data
2. **Download Synthea:** Follow Step 1 above
3. **Use Conversion Scripts:** See scripts below
