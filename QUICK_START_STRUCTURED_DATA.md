# Quick Start: Get Structured Clinical Data for CipherCare

## 🎯 Problem Solved

You needed **granular, structured clinical data** with:
- ✅ Individual observation records (not summaries)
- ✅ LOINC codes for vitals and labs
- ✅ SNOMED codes for conditions
- ✅ RxNorm codes for medications
- ✅ Normalized values with units
- ✅ Full metadata (timestamps, provenance, reference ranges)

**MIMIC and Synthea CAN provide this** - you just needed the right parsers!

---

## 🚀 Three Ways to Get Data (Choose One)

### **Option 1: Quick Test (15 minutes) - RECOMMENDED TO START**

Fetch data from public FHIR server - no downloads needed!

```bash
# 1. Fetch data from FHIR server
python fetch_from_fhir_server.py

# 2. Upload to CyborgDB
python upload_structured_data.py
```

**What you get:**
- 10-20 patients
- Hundreds of observations
- Real FHIR format with LOINC/SNOMED codes
- Ready to query immediately

---

### **Option 2: Synthea (1 hour) - BEST FOR DEVELOPMENT**

Generate synthetic patients with full clinical data

```bash
# 1. Install Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea

# 2. Generate 50 patients
./run_synthea -p 50

# 3. Parse to CipherCare format
cd ../Cipercare
python parse_synthea_structured.py

# 4. Upload to CyborgDB
python upload_structured_data.py
```

**What you get:**
- 50+ patients
- Thousands of observations
- Full LOINC, SNOMED, RxNorm codes
- Privacy-safe synthetic data

---

### **Option 3: MIMIC-IV (2-3 days) - PRODUCTION QUALITY**

Real clinical data from ICU patients

```bash
# 1. Get PhysioNet access
# - Register at https://physionet.org/
# - Complete CITI training
# - Download MIMIC-IV v2.2

# 2. Parse to CipherCare format
python parse_mimic_structured.py

# 3. Upload to CyborgDB
python upload_structured_data.py
```

**What you get:**
- Thousands of patients
- Millions of observations
- Real clinical data (de-identified)
- Production-ready quality

---

## 📁 Files I Created for You

### **Parsers:**
1. **`parse_synthea_structured.py`** - Parse Synthea FHIR bundles
2. **`parse_mimic_structured.py`** - Parse MIMIC-IV tables
3. **`fetch_from_fhir_server.py`** - Fetch from public FHIR servers

### **Uploader:**
4. **`upload_structured_data.py`** - Upload any structured data to CyborgDB

### **Documentation:**
5. **`STRUCTURED_DATA_SOURCES.md`** - Complete guide to data sources

---

## 📊 Output Format

All parsers create the **exact format you specified**:

```json
{
  "patient_id": "PID-102",
  "encounter_id": "ENC-12345",
  "record_id": "obs-uuid",
  "record_type": "observation",
  "data_source": "MIMIC-IV",
  "effective_date": "2024-06-18T08:32:00Z",
  "created_at": "2024-06-18T08:32:00Z",
  "provenance": "nurse-123",
  "language": "en",
  
  "code": {
    "system": "LOINC",
    "code": "8310-5",
    "display": "Body temperature"
  },
  "display": "Body temperature",
  "loinc_code": "8310-5",
  
  "value": 38.2,
  "value_normalized": 38.2,
  "value_text": null,
  "value_type": "Quantity",
  "unit": "Cel",
  
  "status": "final",
  "method": "oral",
  "reference_range": "36.5 - 37.5",
  "interpretation": "H",
  
  "text_for_embedding": "2024-06-18: Body temperature 38.2 Cel, oral",
  "text_summary": "Body temperature: 38.2 Cel"
}
```

---

## ✅ Next Steps

### **Right Now (15 minutes):**

```bash
# Test with FHIR server data
python fetch_from_fhir_server.py
python upload_structured_data.py
```

### **This Week (if you want more data):**

```bash
# Generate Synthea data
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./run_synthea -p 100
cd ../Cipercare
python parse_synthea_structured.py
python upload_structured_data.py
```

### **For Production:**

1. Apply for MIMIC-IV access
2. Complete CITI training
3. Download MIMIC-IV
4. Run `parse_mimic_structured.py`

---

## 🔍 Why This Solves Your Problem

### **Before (What Wasn't Working):**
- ❌ MIMIC: Using summary tables instead of granular `chartevents`
- ❌ Synthea: Not parsing FHIR bundles properly
- ❌ Missing LOINC codes from observations
- ❌ Bundling multiple vitals into one record

### **After (What Works Now):**
- ✅ Each vital sign is a separate record
- ✅ Each lab result is a separate record
- ✅ LOINC codes extracted from proper fields
- ✅ Values normalized with units
- ✅ Full metadata preserved
- ✅ Perfect for semantic search

---

## 💡 Pro Tips

1. **Start small:** Use FHIR server data first (10 patients)
2. **Test queries:** Make sure embeddings work before scaling up
3. **Then scale:** Generate 100+ Synthea patients
4. **Production:** Move to MIMIC-IV when ready

---

## 🆘 Troubleshooting

### "No LOINC codes found"
- ✅ **Fixed:** Parsers extract from `coding` arrays properly

### "Values not normalized"
- ✅ **Fixed:** Parsers convert units (e.g., F to C)

### "Queries return irrelevant results"
- ✅ **Fixed:** Using `text_for_embedding` field with rich context

### "Missing metadata"
- ✅ **Fixed:** All parsers extract provenance, timestamps, reference ranges

---

## 📞 Questions?

Run into issues? Check:
1. `STRUCTURED_DATA_SOURCES.md` - Detailed guide
2. Parser scripts - Have inline comments
3. Sample output - Shows expected format

**Ready to start?** Run this now:

```bash
python fetch_from_fhir_server.py
```

This will get you working data in 15 minutes! 🚀
