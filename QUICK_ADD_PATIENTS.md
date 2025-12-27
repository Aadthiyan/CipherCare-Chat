# 🚀 Quick Start: Add Patient Records to CipherCare

## Option 1: Use Existing Data (FASTEST - 1 minute)

```bash
# Your system already has synthetic patient data
python upload_embeddings.py
```

**Includes:** ~100 synthetic patients with conditions, medications, and clinical notes

---

## Option 2: Interactive Quick Setup (5 minutes)

```bash
# Run interactive script - it will guide you
python quick_add_synthea_data.py
```

**What it does:**
- Downloads or uses existing patient data
- Converts to your format
- Uploads to CyborgDB automatically

---

## Option 3: Download Synthea Samples (10 minutes)

### Step 1: Download Pre-Generated Data
```bash
# Download from Synthea GitHub
wget https://github.com/synthetichealth/synthea-sample-data/archive/refs/heads/master.zip
unzip master.zip
```

### Step 2: Convert and Upload
```bash
python convert_synthea_to_cipercare.py --input synthea-sample-data-master/fhir/ --upload
```

**Gets you:** 20+ realistic FHIR patient records

---

## Option 4: Generate Custom Synthea Data (30 minutes)

### Step 1: Install Synthea
```bash
# Requires Java 11+
git clone https://github.com/synthetichealth/synthea.git
cd synthea
```

### Step 2: Generate Patients
```bash
# Generate 100 patients in Massachusetts
./run_synthea Massachusetts -p 100

# Or Windows:
run_synthea.bat Massachusetts -p 100
```

### Step 3: Convert and Upload
```bash
cd ..
python convert_synthea_to_cipercare.py --input synthea/output/fhir/ --upload
```

**Gets you:** Custom number of patients, US state demographics

---

## Option 5: MIMIC-III Real Hospital Data (3 hours setup)

### Step 1: Get Access
1. Register at https://physionet.org/register/
2. Complete CITI training: https://physionet.org/about/citi-course/
3. Sign Data Use Agreement
4. Download MIMIC-III: https://physionet.org/content/mimiciii/1.4/

### Step 2: Convert and Upload
```bash
# Convert 100 patients for testing
python convert_mimic_to_cipercare.py --mimic-dir /path/to/mimic --limit 100

# Upload
python upload_embeddings.py --input mimic_converted.json
```

**Gets you:** 60,000+ real ICU patient records (de-identified)

---

## Quick Commands Reference

| Task | Command |
|------|---------|
| **Use existing data** | `python upload_embeddings.py` |
| **Interactive setup** | `python quick_add_synthea_data.py` |
| **Convert Synthea** | `python convert_synthea_to_cipercare.py --input <path> --upload` |
| **Convert MIMIC** | `python convert_mimic_to_cipercare.py --mimic-dir <path> --limit 100` |
| **Generate more synthetic** | `python generate_data.py` |

---

## Verify Upload

After uploading, verify data is in your system:

```bash
# Start backend
python run_backend.py

# In another terminal, test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "MIMIC-12345",
    "query": "What conditions does this patient have?"
  }'
```

Or use the frontend:
```bash
cd frontend
npm run dev
# Open http://localhost:3000
```

---

## Data Format Your System Expects

```json
{
  "patient_id": "string (required)",
  "clinical_text": "string for embeddings",
  "metadata": {
    "patient_name": "string",
    "gender": "male|female|unknown",
    "conditions": ["condition1", "condition2"],
    "medications": ["med1", "med2"]
  }
}
```

---

## Troubleshooting

### "No patients found"
```bash
# Check if data exists
ls data/synthetic/

# If empty, generate new data
python generate_data.py
```

### "CyborgDB connection failed"
```bash
# Check .env file has correct settings
cat .env | grep CYBORGDB

# Start CyborgDB if needed
docker-compose up cyborgdb
```

### "Import error: sentence_transformers"
```bash
pip install sentence-transformers
```

---

## Next Steps After Adding Data

1. ✅ **Test Queries:** Try different medical questions in the UI
2. ✅ **Check Embeddings:** Verify semantic search works
3. ✅ **Test RBAC:** Create different user roles and test access
4. ✅ **Performance:** Load test with larger datasets
5. ✅ **Production:** Use MIMIC-III or real EHR data

---

## Need More Help?

- **Synthea Docs:** https://github.com/synthetichealth/synthea/wiki
- **MIMIC-III:** https://mimic.mit.edu/docs/
- **FHIR Spec:** https://www.hl7.org/fhir/
- **Your Docs:** See `OPEN_SOURCE_PATIENT_DATA_GUIDE.md`
