# CyborgDB 502 Error - Complete Diagnosis & Solution

## 🔍 Problem Summary

You're getting **502 Bad Gateway** errors when querying patient data because:

1. **Your `.env` file points to `localhost:8002`** but local CyborgDB is not running
2. **The Render CyborgDB service** at `https://cyborgdb-toj5.onrender.com` is returning 502 (service down/crashed)
3. **No patient data has been uploaded** to CyborgDB yet (even if it were running)

## 📊 Current Status

### ✓ What's Working
- **Patient data file exists**: `synthea_structured_cipercare.json` (111,060 records, 75.7 MB)
- **Backend is deployed** on Render and running
- **Frontend is deployed** on Vercel
- **PostgreSQL database** is working (for authentication)
- **API keys are configured**

### ✗ What's Broken
- **CyborgDB service on Render**: Returning 502 Bad Gateway
- **Local CyborgDB**: Not running
- **No data in CyborgDB**: Database is empty (no uploads completed)
- **Wrong .env configuration**: Points to localhost instead of Render

## 🎯 Solution Options

### Option 1: Fix Render Deployment (Recommended for Production)

**Best for**: Production deployment, team collaboration

#### Step 1: Check Render Dashboard

1. Go to https://dashboard.render.com
2. Find your `ciphercare-cyborgdb` service
3. Check status:
   - **If RUNNING**: Proceed to Step 2
   - **If CRASHED**: Check logs, likely out-of-memory on free tier
   - **If NOT DEPLOYED**: You need to deploy CyborgDB first

#### Step 2: Verify CyborgDB Service Configuration

In Render dashboard for `ciphercare-cyborgdb`:

**Environment Variables:**
```
CYBORGDB_API_KEY=<your-api-key>
```

**Start Command:**
```bash
cyborgdb serve --host 0.0.0.0 --port $PORT
```

**Health Check:**
```
Path: /v1/health
```

#### Step 3: Update Local .env for Data Upload

To upload data to Render, temporarily use public URL:

```bash
# Run the fix script
python fix_env_config.py
# Select option 3 (Hybrid - local backend, Render CyborgDB)
```

Or manually edit `.env`:
```bash
CYBORGDB_BASE_URL=https://cyborgdb-toj5.onrender.com
```

#### Step 4: Test Connection

```bash
python diagnose_cyborgdb.py
```

Expected output:
```
✓ CyborgDB service is UP
✓ Can access indexes
```

#### Step 5: Upload Patient Data

```bash
python upload_to_render.py
```

Start with option 1 (100 records) for testing, then option 4 (all records).

#### Step 6: Update Backend .env on Render

In Render dashboard for `ciphercare-backend`, set:
```
CYBORGDB_BASE_URL=http://ciphercare-cyborgdb:10000
```

This uses internal Render networking (faster, more secure).

---

### Option 2: Run CyborgDB Locally (Quick Fix)

**Best for**: Local development, testing, free tier limitations

#### Step 1: Install CyborgDB

```bash
pip install cyborgdb
```

#### Step 2: Start Local CyborgDB

In a **separate terminal**:
```bash
cyborgdb serve --port 8002
```

Keep this running!

#### Step 3: Update .env

```bash
# Run the fix script
python fix_env_config.py
# Select option 1 (Local development)
```

Or manually edit `.env`:
```bash
CYBORGDB_BASE_URL=http://localhost:8002
```

#### Step 4: Upload Data

```bash
python upload_to_render.py
```

#### Step 5: Start Backend

```bash
python run_backend.py
```

---

## 🔧 Quick Commands

### Diagnose Issues
```bash
python diagnose_cyborgdb.py
```

### Fix .env Configuration
```bash
python fix_env_config.py
```

### Upload Data
```bash
python upload_to_render.py
```

### Test Backend
```bash
curl http://localhost:8000/health
```

---

## 🐛 Common Issues & Fixes

### Issue: "502 Bad Gateway" from Render CyborgDB

**Cause**: Service crashed or not deployed correctly

**Fix**:
1. Check Render logs for errors
2. Verify service is using correct start command
3. May need paid plan (free tier has memory limits)
4. Consider running CyborgDB locally instead

### Issue: "Connection refused" to localhost:8002

**Cause**: Local CyborgDB not running

**Fix**:
```bash
# Start CyborgDB in separate terminal
cyborgdb serve --port 8002
```

### Issue: "401 Unauthorized" when uploading

**Cause**: Wrong API key

**Fix**:
1. Check `CYBORGDB_API_KEY` in `.env`
2. Ensure it matches in Render environment variables
3. Regenerate key if needed

### Issue: "No results found" when querying

**Cause**: No data uploaded to CyborgDB

**Fix**:
```bash
python upload_to_render.py
```

### Issue: "JSONDecodeError: Expecting value"

**Cause**: CyborgDB returning HTML error page instead of JSON

**Fix**:
1. This means CyborgDB is down or misconfigured
2. Run `python diagnose_cyborgdb.py` to identify issue
3. Fix the underlying problem (usually 502 error)

---

## ✅ Verification Checklist

After fixing, verify everything works:

- [ ] `python diagnose_cyborgdb.py` shows service is UP
- [ ] Data uploaded successfully (run `upload_to_render.py`)
- [ ] Backend can connect to CyborgDB
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Query test works (use frontend or Postman)
- [ ] No 500/502 errors in backend logs

---

## 📝 Recommended Approach

**For immediate testing:**
1. Run CyborgDB locally (Option 2)
2. Upload 100 test records
3. Test queries from frontend

**For production:**
1. Fix Render CyborgDB deployment (Option 1)
2. Upload all 111,060 records
3. Configure backend to use internal Render networking

---

## 🆘 Still Having Issues?

If problems persist after following this guide:

1. **Share Render logs**: 
   - Go to Render dashboard → ciphercare-cyborgdb → Logs
   - Copy last 50 lines

2. **Run diagnostic**:
   ```bash
   python diagnose_cyborgdb.py > diagnostic_output.txt
   ```

3. **Check backend logs**:
   - Look for specific error messages
   - Share relevant stack traces

4. **Verify environment**:
   - Ensure all API keys are set
   - Check that services can communicate
   - Verify network/firewall settings

---

## 📚 Additional Resources

- **CyborgDB Documentation**: https://github.com/CyborgDB/cyborgdb
- **Render Documentation**: https://render.com/docs
- **Your deployment guide**: `DEPLOYMENT_GUIDE_COMPLETE.md`

---

**Last Updated**: 2026-01-07
**Status**: Awaiting user action to fix Render deployment or run locally
