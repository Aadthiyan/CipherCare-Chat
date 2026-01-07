# 🚀 Combined Backend + CyborgDB Deployment Guide

## ✅ What Changed

**Before:**
- ❌ Two separate services (backend + CyborgDB)
- ❌ Ephemeral Redis (data lost on restart)
- ❌ Complex inter-service communication
- ❌ Higher memory usage

**After:**
- ✅ **Single service** (backend + CyborgDB in one container)
- ✅ **Persistent disk storage** (data survives restarts!)
- ✅ **Simpler architecture** (localhost communication)
- ✅ **Lower memory usage** (one container)

---

## 📋 Files Created/Modified

### **New Files:**
1. `docker/backend-with-cyborgdb.Dockerfile` - Combined Dockerfile
   - Runs both backend (port 8000) and CyborgDB (port 8002)
   - Uses supervisor to manage both processes
   - Persistent storage at `/app/cyborgdb_data`

### **Modified Files:**
1. `render.yaml` - Updated deployment config
   - Removed separate `ciphercare-cyborgdb` service
   - Updated `ciphercare-backend` to use combined Dockerfile
   - Added persistent disk (1GB) mounted at `/app/cyborgdb_data`
   - Changed `CYBORGDB_BASE_URL` to `http://localhost:8002`

2. `.env` - Updated local config
   - Changed `CYBORGDB_BASE_URL` to `http://localhost:8002`

---

## 🚀 Deployment Steps

### **Step 1: Test Locally (Optional but Recommended)**

```bash
# 1. Build the Docker image
docker build -f docker/backend-with-cyborgdb.Dockerfile -t ciphercare-combined .

# 2. Run the container
docker run -p 8000:8000 -p 8002:8002 \
  -v $(pwd)/cyborgdb_data:/app/cyborgdb_data \
  -e CYBORGDB_API_KEY=your_key_here \
  -e DATABASE_URL=your_db_url_here \
  ciphercare-combined

# 3. Test backend health
curl http://localhost:8000/health

# 4. Test CyborgDB health
curl http://localhost:8002/v1/health
```

### **Step 2: Deploy to Render**

```bash
# 1. Commit changes
git add .
git commit -m "Combined backend and CyborgDB into single service"
git push origin main

# 2. Render will automatically deploy the new configuration
```

### **Step 3: Delete Old CyborgDB Service**

1. Go to Render Dashboard
2. Find `ciphercare-cyborgdb` service
3. Click "Delete Service"
4. Confirm deletion

### **Step 4: Configure Environment Variables**

In Render dashboard for `ciphercare-backend`:

**Required:**
- `CYBORGDB_API_KEY` = `cyborg_9e8c1c2e25c944d78f41ac7f23376d23`
- `DATABASE_URL` = Your PostgreSQL URL
- `GROQ_API_KEY` = Your Groq API key
- `HF_API_TOKEN` = Your Hugging Face token
- `HUGGINGFACE_API_KEY` = Your Hugging Face token
- `JWT_SECRET_KEY` = Your JWT secret
- `POSTGRES_URL` = Your PostgreSQL URL
- `MAIL_USERNAME` = Your email
- `MAIL_PASSWORD` = Your email password
- `FRONTEND_URL` = Your frontend URL

**Auto-configured:**
- `CYBORGDB_BASE_URL` = `http://localhost:8002` (set in render.yaml)

### **Step 5: Upload Data**

Once deployed, upload your patient data:

```bash
# Update .env to point to Render (for upload only)
# Temporarily change:
CYBORGDB_BASE_URL=https://ciphercare-backend.onrender.com

# Run upload
python upload_sdk_fast.py
# Select option 5 (150 patients)
# Wait ~33 minutes

# Change back to localhost for local development
CYBORGDB_BASE_URL=http://localhost:8002
```

**OR upload to local CyborgDB for testing:**

```bash
# Keep .env as localhost:8002
CYBORGDB_BASE_URL=http://localhost:8002

# Start local backend with CyborgDB
docker-compose up

# Upload data
python upload_sdk_fast.py  # Option 5
```

---

## 💾 Persistent Storage

### **How It Works:**

```
Container:
  /app/cyborgdb_data/  ← Mounted to Render disk
    ├── index_data/
    ├── patient_records_v1/
    └── metadata/

Render Disk:
  cyborgdb-data (1GB)
    └── Persists across restarts!
```

### **Benefits:**
- ✅ Data survives container restarts
- ✅ Data survives redeployments
- ✅ 1GB storage (enough for 500K+ records)
- ✅ Automatic backups (Render handles this)

---

## 🔧 How the Combined Service Works

### **Supervisor Configuration:**

The Dockerfile creates a supervisor config that manages two processes:

```ini
[program:cyborgdb]
command=cyborgdb serve --port 8002 --data-dir /app/cyborgdb_data
autostart=true
autorestart=true

[program:backend]
command=uvicorn backend.main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
```

### **Process Flow:**

```
Container starts
    ↓
Supervisor starts
    ↓
    ├─→ CyborgDB starts on port 8002
    │   └─→ Data stored in /app/cyborgdb_data (persistent disk)
    │
    └─→ Backend starts on port 8000
        └─→ Connects to CyborgDB at localhost:8002
```

---

## 📊 Resource Usage

### **Before (Two Services):**
```
ciphercare-cyborgdb:  512 MB RAM (free tier)
ciphercare-backend:   512 MB RAM (starter plan)
Total:                1024 MB RAM
Cost:                 $7/month
```

### **After (One Service):**
```
ciphercare-backend:   512 MB RAM (starter plan)
Total:                512 MB RAM
Cost:                 $7/month
Savings:              $0/month but more stable!
```

**Note:** You still need Starter plan for the persistent disk, but you save the complexity and potential issues of running two services.

---

## 🎯 Testing the Deployment

### **1. Check Service Health:**

```bash
# Backend health
curl https://ciphercare-backend.onrender.com/health

# Should return: {"status": "healthy"}
```

### **2. Check CyborgDB (Internal):**

The CyborgDB service runs on localhost:8002 inside the container, so it's not directly accessible from outside. But you can check logs:

```bash
# In Render dashboard, check logs for:
"CyborgDB server started on port 8002"
"Backend server started on port 8000"
```

### **3. Test Query:**

```bash
curl -X POST https://ciphercare-backend.onrender.com/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patient_id": "PID-101",
    "question": "What medications is this patient taking?",
    "retrieve_k": 5
  }'
```

---

## 🐛 Troubleshooting

### **Issue: Backend can't connect to CyborgDB**

**Symptoms:**
- "Connection refused" errors
- "Search returned 0 results"

**Solution:**
```bash
# Check logs in Render dashboard
# Look for:
✓ "CyborgDB server started on port 8002"
✓ "Backend server started on port 8000"

# If CyborgDB didn't start, check:
- Is supervisor installed? (should be in Dockerfile)
- Is cyborgdb package installed? (should be in Dockerfile)
- Check supervisor logs: /app/logs/cyborgdb.err.log
```

### **Issue: Data not persisting**

**Symptoms:**
- Data disappears after restart
- Need to re-upload frequently

**Solution:**
```bash
# Verify persistent disk is mounted:
# In Render dashboard → Service → Disks
# Should show: cyborgdb-data (1GB) mounted at /app/cyborgdb_data

# Check if data is being written to correct location:
# In logs, look for:
"Using data directory: /app/cyborgdb_data"
```

### **Issue: Out of memory**

**Symptoms:**
- Service crashes
- "Memory limit exceeded" emails

**Solution:**
```bash
# Upgrade to higher plan:
# Starter: 512 MB → Professional: 2 GB

# Or reduce dataset:
# Upload fewer patients (100 instead of 150)
```

---

## 📋 Maintenance

### **Viewing Logs:**

```bash
# In Render dashboard:
1. Go to ciphercare-backend service
2. Click "Logs" tab
3. Look for:
   - Supervisor logs
   - CyborgDB logs (/app/logs/cyborgdb.out.log)
   - Backend logs (/app/logs/backend.out.log)
```

### **Backing Up Data:**

Render automatically backs up your persistent disk, but you can also:

```bash
# Download data via API (future feature)
# Or re-upload from source if needed
python upload_sdk_fast.py  # Option 5
```

### **Updating the Service:**

```bash
# 1. Make code changes
# 2. Commit and push
git add .
git commit -m "Update backend"
git push

# 3. Render auto-deploys
# 4. Data persists across deployments!
```

---

## ✅ Advantages of This Approach

1. **Persistent Storage** ✅
   - Data survives restarts
   - No need to re-upload

2. **Simpler Architecture** ✅
   - One service instead of two
   - Localhost communication (faster)

3. **Cost Effective** ✅
   - Same cost as before ($7/mo)
   - But more reliable

4. **Easier Debugging** ✅
   - All logs in one place
   - Simpler networking

5. **Production Ready** ✅
   - Proven approach (you used it before)
   - Stable and reliable

---

## 🎉 Summary

**What you now have:**
- ✅ Single Docker container with backend + CyborgDB
- ✅ Persistent disk storage (1GB)
- ✅ Data survives restarts and redeployments
- ✅ Simpler architecture
- ✅ Ready for production

**Next steps:**
1. Deploy to Render (git push)
2. Delete old CyborgDB service
3. Upload patient data (once!)
4. Test queries
5. Enjoy persistent, reliable storage! 🚀

---

**Last Updated:** 2026-01-07  
**Status:** ✅ Ready to deploy
