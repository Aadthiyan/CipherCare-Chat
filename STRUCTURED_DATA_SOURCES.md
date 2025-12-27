# Structured Clinical Data Sources for CipherCare

## 🎯 Your Requirements

You need **granular, structured clinical data** with:

✅ **Individual observation records** (not bundled summaries)  
✅ **Standardized codes** (LOINC, SNOMED, RxNorm, ICD)  
✅ **Normalized values** with units (UCUM standard)  
✅ **Rich metadata** (timestamps, provenance, reference ranges)  
✅ **Separate records** for each vital, lab, medication, condition  

---

## 🏆 **Best Data Sources (Ranked)**

### **1. MIMIC-IV (Properly Parsed) - BEST FOR PRODUCTION**

**Why it matches your requirements:**
- ✅ Individual `chartevents` records for each vital sign
- ✅ Individual `labevents` records for each lab test
- ✅ **LOINC codes** already mapped in `d_labitems` table
- ✅ Reference ranges, units, timestamps, provenance
- ✅ Real clinical data (de-identified)

**What you need:**
```
MIMIC-IV Directory Structure:
mimic-iv/
├── hosp/
│   ├── patients.csv.gz
│   ├── admissions.csv.gz
│   ├── labevents.csv.gz          ← Labs with LOINC codes
│   ├── d_labitems.csv.gz          ← LOINC mappings
│   ├── prescriptions.csv.gz       ← Medications with NDC codes
│   ├── diagnoses_icd.csv.gz       ← Conditions with ICD codes
│   └── d_icd_diagnoses.csv.gz     ← ICD descriptions
└── icu/
    ├── chartevents.csv.gz         ← Vitals (HR, BP, Temp, etc.)
    └── d_items.csv.gz             ← Vital sign definitions
```

**How to get it:**
1. Register at [PhysioNet](https://physionet.org/)
2. Complete CITI training (required for access)
3. Download MIMIC-IV v2.2: https://physionet.org/content/mimiciv/2.2/

**Use the parser I created:**
```bash
python parse_mimic_structured.py
```

**Output format:**
```json
{
  "patient_id": "PID-102",
  "record_id": "obs-0001",
  "record_type": "observation",
  "data_source": "MIMIC-IV",
  "effective_date": "2024-06-18T08:32:00Z",
  "code": {
    "system": "LOINC",
    "code": "8310-5",
    "display": "Body temperature"
  },
  "loinc_code": "8310-5",
  "value": 38.2,
  "value_normalized": 38.2,
  "unit": "Cel",
  "status": "final",
  "method": "oral",
  "provenance": "nurse-123",
  "text_for_embedding": "2024-06-18: Body temperature 38.2 Cel",
  "text_summary": "Body temperature: 38.2 Cel"
}
```

---

### **2. Synthea (Properly Parsed) - BEST FOR DEVELOPMENT**

**Why it matches your requirements:**
- ✅ FHIR R4 format with full LOINC/SNOMED/RxNorm codes
- ✅ Individual `Observation` resources for each vital/lab
- ✅ Reference ranges, units, interpretations
- ✅ Privacy-safe synthetic data
- ✅ Easy to generate custom datasets

**How to generate:**
```bash
# Install Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea

# Generate 100 patients in FHIR format
./run_synthea -p 100

# Output: output/fhir/*.json (one bundle per patient)
```

**Use the parser I created:**
```bash
python parse_synthea_structured.py
```

**What you get:**
- Individual observations for each vital sign
- Individual lab results with LOINC codes
- Medications with RxNorm codes
- Conditions with SNOMED codes
- Procedures with SNOMED codes

---

### **3. CMS Synthetic Data - BEST FOR REALISTIC VOLUME**

**Source:** https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf

**Why it's good:**
- ✅ 30,000+ synthetic Medicare beneficiaries
- ✅ Claims data with ICD codes
- ✅ Prescription data with NDC codes
- ✅ Large volume for testing

**Download:**
```bash
wget https://www.cms.gov/files/zip/de1_0_2008_beneficiary_summary_file_sample_1.zip
```

**Format:** CSV files that need conversion to your format

---

### **4. i2b2 Clinical Notes - BEST FOR NLP/EMBEDDINGS**

**Source:** https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/

**Why it's good:**
- ✅ Real clinical notes (de-identified)
- ✅ Annotated with medical concepts
- ✅ Perfect for training embeddings
- ✅ Used in medical NLP research

**How to get:**
1. Register at i2b2 portal
2. Request access (usually approved in 1-2 days)
3. Download datasets (2018 Cohort Selection recommended)

**What you get:**
- Clinical notes with annotations
- Disease mentions with offsets
- Medication mentions with offsets
- Lab results mentioned in text

---

### **5. FHIR Test Servers - BEST FOR QUICK TESTING**

**Public FHIR servers with structured data:**

#### **Hapi FHIR Test Server**
```
URL: http://hapi.fhir.org/baseR4
Format: FHIR R4
```

**Example queries:**
```bash
# Get observations (vitals/labs)
curl "http://hapi.fhir.org/baseR4/Observation?_count=100"

# Get specific patient's vitals
curl "http://hapi.fhir.org/baseR4/Observation?patient=123&category=vital-signs"

# Get lab results
curl "http://hapi.fhir.org/baseR4/Observation?patient=123&category=laboratory"
```

#### **SMART Health IT Sandbox**
```
URL: https://launch.smarthealthit.org/
Format: FHIR R4
```

Pre-populated with sample patients including:
- Vitals with LOINC codes
- Labs with reference ranges
- Medications with RxNorm
- Conditions with SNOMED

---

## 📊 **Comparison Table**

| Source | Granularity | LOINC | SNOMED | RxNorm | Volume | Privacy | Setup Time |
|--------|-------------|-------|--------|--------|--------|---------|------------|
| **MIMIC-IV** | ✅ Individual | ✅ Yes | ⚠️ Partial | ⚠️ NDC | 🔥 Millions | ✅ De-ID | 2-3 days |
| **Synthea** | ✅ Individual | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Hundreds | ✅ Synthetic | 30 min |
| **CMS Synthetic** | ⚠️ Claims | ⚠️ Limited | ❌ No | ⚠️ NDC | 🔥 30K+ | ✅ Synthetic | 1 hour |
| **i2b2** | ⚠️ Text-based | ⚠️ Extracted | ⚠️ Extracted | ⚠️ Extracted | 🔥 Thousands | ✅ De-ID | 2-3 days |
| **FHIR Servers** | ✅ Individual | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Dozens | ✅ Test | 5 min |

---

## 🚀 **Quick Start Guide**

### **Option A: Start with Synthea (Recommended)**

**Why:** Easiest to get structured data matching your exact requirements

```bash
# 1. Generate Synthea data
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./run_synthea -p 50  # Generate 50 patients

# 2. Parse to CipherCare format
cd ../Cipercare
python parse_synthea_structured.py

# 3. Upload to CyborgDB
python upload_structured_data.py synthea_structured_cipercare.json
```

**Time:** 1 hour  
**Result:** 50+ patients with hundreds of structured observations

---

### **Option B: Use MIMIC-IV (Production Quality)**

**Why:** Real clinical data with maximum detail

```bash
# 1. Download MIMIC-IV (requires PhysioNet access)
# Follow: https://physionet.org/content/mimiciv/2.2/

# 2. Parse to CipherCare format
python parse_mimic_structured.py

# 3. Upload to CyborgDB
python upload_structured_data.py mimic_structured_cipercare.json
```

**Time:** 2-3 days (including approval)  
**Result:** Thousands of patients with millions of observations

---

### **Option C: Quick Test with FHIR Server**

**Why:** Instant access, no downloads

```bash
# 1. Fetch from public FHIR server
python fetch_from_fhir_server.py

# 2. Upload to CyborgDB
python upload_structured_data.py fhir_server_data.json
```

**Time:** 15 minutes  
**Result:** 10-20 patients with structured data

---

## 🔧 **What I Created for You**

### **1. `parse_mimic_structured.py`**
- Parses MIMIC-IV into your exact format
- Extracts vitals from `chartevents`
- Extracts labs from `labevents` with LOINC codes
- Extracts medications from `prescriptions`
- Extracts conditions from `diagnoses_icd`

### **2. `parse_synthea_structured.py`**
- Parses Synthea FHIR bundles
- Extracts individual Observation resources
- Extracts Condition, Medication, Procedure resources
- Maps all codes (LOINC, SNOMED, RxNorm)

### **3. Next: Create upload script**
- Will upload structured records to CyborgDB
- Creates embeddings from `text_for_embedding` field
- Preserves all metadata for filtering

---

## 💡 **Why Your Previous Attempts Failed**

### **MIMIC Issues:**
1. ❌ You were using summary tables instead of `chartevents`/`labevents`
2. ❌ Not extracting LOINC codes from `d_labitems`
3. ❌ Bundling multiple vitals into one record

### **Synthea Issues:**
1. ❌ Not parsing FHIR bundles properly
2. ❌ Not extracting individual Observation resources
3. ❌ Not mapping codes from `coding` arrays

### **✅ Solution:**
Use the parsers I created - they extract **individual observations** with **all metadata**

---

## 📝 **Sample Output**

### **Vital Sign (Temperature):**
```json
{
  "patient_id": "PID-102",
  "encounter_id": "ENC-12345",
  "record_id": "obs-uuid",
  "record_type": "vital",
  "data_source": "MIMIC-IV",
  "effective_date": "2024-06-18T08:32:00Z",
  "code": {
    "system": "LOINC",
    "code": "8310-5",
    "display": "Body temperature"
  },
  "loinc_code": "8310-5",
  "value": 38.2,
  "value_normalized": 38.2,
  "unit": "Cel",
  "value_type": "Quantity",
  "status": "final",
  "method": "oral",
  "provenance": "nurse-123",
  "text_for_embedding": "2024-06-18: Body temperature 38.2 Cel, oral",
  "text_summary": "Body temperature: 38.2 Cel"
}
```

### **Lab Result (Glucose):**
```json
{
  "patient_id": "PID-102",
  "record_id": "lab-uuid",
  "record_type": "laboratory",
  "effective_date": "2024-06-18T09:15:00Z",
  "code": {
    "system": "LOINC",
    "code": "2345-7",
    "display": "Glucose"
  },
  "loinc_code": "2345-7",
  "value": 145,
  "value_normalized": 145,
  "unit": "mg/dL",
  "reference_range": "70 - 100",
  "interpretation": "H",
  "status": "final",
  "text_for_embedding": "2024-06-18: Glucose 145 mg/dL (H)",
  "text_summary": "Glucose: 145 mg/dL"
}
```

---

## 🎯 **My Recommendation**

**For immediate testing:**
1. ✅ Use **Synthea** with `parse_synthea_structured.py`
2. ✅ Generate 50 patients
3. ✅ Upload to CyborgDB
4. ✅ Test queries

**For production:**
1. ✅ Get **MIMIC-IV** access
2. ✅ Use `parse_mimic_structured.py`
3. ✅ Extract 1000+ patients
4. ✅ Deploy

**Time to working system:** 2-3 hours with Synthea

---

## 📞 **Next Steps**

1. Choose your data source (I recommend Synthea to start)
2. Run the appropriate parser
3. Let me know when you have the JSON output
4. I'll create the upload script for CyborgDB

**Questions?** Let me know which source you want to use!
