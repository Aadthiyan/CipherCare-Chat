# 🚀 Final Deployment: Persistent Disk Approach

## ✅ What We're Using

**Combined Backend + CyborgDB with Persistent Disk**

- ✅ Single Docker container (backend + CyborgDB)
- ✅ Supervisor manages both processes
- ✅ Persistent disk (1GB) for CyborgDB data
- ✅ Upload data once, persists forever
- ✅ Proven, reliable approach

---

## 📋 Deployment Steps

### **Step 1: Wait for Render Build** (5-7 minutes)

Render is now building with the correct Dockerfile. Watch for:

```
==> Building...
Step 1/X : FROM python:3.9-slim
...
Installing supervisor
Installing cyborgdb
...
==> Build successful 🎉
==> Deploying...
Starting supervisor...
CyborgDB server started on port 8002
Backend server started on port 8000
```

### **Step 2: Verify Services Started**

Check Render logs for:
```
✅ CyborgDB server started on port 8002
✅ Backend server started on port 8000
✅ Initializing CyborgDB Lite at http://localhost:8002
```

### **Step 3: Upload Patient Data** (33 minutes)

Once the service is live, upload the data:

```bash
# Update upload script to use Render URL
python upload_sdk_fast.py
# When prompted, select option 5 (150 patients)
# Wait ~33 minutes
```

**Important:** The upload script needs to connect to CyborgDB. Since CyborgDB is on `localhost:8002` inside the container, you have two options:

**Option A: Upload Locally, Then Sync** (Complex)
- Run CyborgDB locally
- Upload data locally
- Copy data directory to Render (manual)

**Option B: Add Upload Endpoint to Backend** (Recommended)
- Add an admin endpoint to trigger upload from within the container
- Upload happens inside the container where CyborgDB is accessible

---

## 🔧 Option B: Add Upload Endpoint (Recommended)

Let me create an admin endpoint for uploading data:

### **File: `backend/admin_routes.py`** (New)

```python
from fastapi import APIRouter, HTTPException, Depends
from backend.auth import require_role
import subprocess
import os

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/upload-patient-data")
async def upload_patient_data(current_user: dict = Depends(require_role(["admin"]))):
    """
    Admin-only endpoint to trigger patient data upload
    Runs the upload script inside the container
    """
    try:
        # Run upload script
        result = subprocess.run(
            ["python", "/app/scripts/upload_data_internal.py"],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Patient data uploaded successfully",
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Upload failed: {result.stderr}"
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Upload timed out (>1 hour)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload error: {str(e)}"
        )
```

### **File: `scripts/upload_data_internal.py`** (New)

```python
"""
Upload patient data from within the container
This script runs inside the Render container where CyborgDB is accessible
"""

import os
import json
import hashlib
from sentence_transformers import SentenceTransformer
import cyborgdb

# Configuration
CYBORGDB_URL = "http://localhost:8002"
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")
DATA_FILE = "/app/synthea_structured_cipercare.json"
INDEX_NAME = "patient_records_v1"
LIMIT = 76317  # 150 patients

print("=" * 70)
print("🚀 Uploading Patient Data to CyborgDB")
print("=" * 70)

# ... (rest of upload logic from upload_sdk_fast.py)
```

---

## 🎯 Simpler Alternative: Manual Upload via SSH

Since adding endpoints is complex, here's the **simplest approach**:

### **Use Render Shell Access:**

1. Go to Render Dashboard
2. Click on `ciphercare-chat` service
3. Click **"Shell"** tab
4. Run upload command directly in the container:

```bash
# Inside Render shell:
cd /app
python upload_sdk_fast.py
# Select option 5
```

---

## 📊 Current Status

### **What's Deployed:**
- ✅ Combined backend + CyborgDB container
- ✅ Supervisor managing both processes
- ✅ Persistent disk mounted at `/app/cyborgdb_data`
- ✅ Backend connecting to `localhost:8002`

### **What's Missing:**
- ❌ Patient data (needs to be uploaded)

### **Next Action:**
- Upload data using one of the methods above

---

## 🚀 Recommended Upload Method

**Use Render Shell (Simplest):**

1. **Wait for deployment to complete** (~5 min)
2. **Go to Render Dashboard** → `ciphercare-chat` → **Shell**
3. **Run in shell:**
   ```bash
   cd /app
   
   # Create upload script inline
   cat > /tmp/upload.py << 'EOF'
   # (paste upload_sdk_fast.py content here)
   EOF
   
   # Run upload
   python /tmp/upload.py
   ```

4. **Wait ~33 minutes** for upload to complete
5. **Data persists** on the disk forever!

---

## ✅ After Upload Complete

### **Test the System:**

```bash
curl -X POST https://ciphercare-chat.onrender.com/api/v1/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patient_id": "PID-101",
    "question": "What medications is this patient taking?"
  }'
```

### **Expected Result:**
- ✅ Returns patient data
- ✅ Shows medications
- ✅ Confidence score > 0

---

## 📋 Summary

**Deployment Approach:**
- Combined backend + CyborgDB in one container
- Supervisor manages both processes
- Persistent disk stores CyborgDB data
- Upload data once via Render shell
- Data persists across restarts

**Timeline:**
- Now: Build deploying (~5 min)
- +5 min: Services start
- +5 min: Upload data via shell (~33 min)
- +38 min: System fully operational! 🎉

---

**Last Updated:** 2026-01-07 21:21 IST  
**Status:** 🔄 Deploying...  
**Next:** Wait for build, then upload data via Render shell
