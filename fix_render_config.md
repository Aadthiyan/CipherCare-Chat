# Fix CyborgDB Render Deployment

## Problem
Your CyborgDB service on Render is returning 502 Bad Gateway errors, preventing queries from working.

## Root Causes
1. **Wrong .env configuration** - Points to localhost instead of Render URL
2. **CyborgDB service may be down** - 502 indicates service crash or misconfiguration
3. **No data uploaded** - Even if service works, it has no patient data

## Solution Steps

### Step 1: Update .env File

Update your `.env` file with the correct Render URL:

```bash
# Change FROM:
CYBORGDB_BASE_URL=http://localhost:8002

# Change TO:
CYBORGDB_BASE_URL=https://cyborgdb-toj5.onrender.com
```

### Step 2: Check Render Dashboard

1. Go to https://dashboard.render.com
2. Find your `cyborgdb-toj5` web service
3. Check the status:
   - **If CRASHED**: Check logs for errors (likely out of memory)
   - **If RUNNING**: Proceed to Step 3
   - **If NOT EXISTS**: You need to deploy CyborgDB first

### Step 3: Verify CyborgDB Deployment

Your CyborgDB service needs:

**Environment Variables (in Render dashboard):**
```
CYBORGDB_API_KEY=<your-api-key>
PORT=10000  # Render assigns this automatically
```

**Start Command:**
```bash
uvicorn cyborgdb.server:app --host 0.0.0.0 --port $PORT
```

**Health Check Path:**
```
/health
```

### Step 4: Test Connection

After fixing the .env, run:
```bash
python diagnose_cyborgdb.py
```

You should see:
- ✓ Service is UP (status 200)
- ✓ Can access indexes

### Step 5: Upload Patient Data

Once service is confirmed working:
```bash
python upload_to_render.py
```

Select option 1 (100 records) for quick test, then option 4 (all records) for full upload.

## Alternative: Use Local CyborgDB (Quick Fix)

If Render free tier doesn't support CyborgDB (memory limits), run locally:

### 1. Install CyborgDB locally
```bash
pip install cyborgdb
```

### 2. Start local CyborgDB server
```bash
# In a separate terminal
cyborgdb serve --port 8002
```

### 3. Keep .env pointing to localhost
```bash
CYBORGDB_BASE_URL=http://localhost:8002
```

### 4. Upload data locally
```bash
python upload_to_render.py
```

## Common Issues

### Issue: 502 Bad Gateway
**Cause**: Service crashed or not deployed
**Fix**: Check Render logs, may need paid plan for more RAM

### Issue: 401 Unauthorized
**Cause**: Wrong API key
**Fix**: Ensure CYBORGDB_API_KEY matches in both .env and Render

### Issue: Connection Refused
**Cause**: Wrong URL or service not running
**Fix**: Verify CYBORGDB_BASE_URL in .env matches deployment

### Issue: No results from queries
**Cause**: No data uploaded
**Fix**: Run upload_to_render.py to populate database

## Verification Checklist

- [ ] .env has correct CYBORGDB_BASE_URL
- [ ] Render service is running (not crashed)
- [ ] Can access /health endpoint (200 OK)
- [ ] Data uploaded successfully
- [ ] Backend can query and get results
- [ ] Frontend receives responses (not 500 errors)

## Next Steps

1. **Immediate**: Update .env with Render URL
2. **Check**: Render dashboard for service status
3. **Test**: Run diagnose_cyborgdb.py
4. **Upload**: Run upload_to_render.py
5. **Verify**: Test a query from frontend

## Need Help?

If issues persist:
1. Share Render logs from CyborgDB service
2. Share output of diagnose_cyborgdb.py
3. Check if you need to upgrade Render plan (free tier may be insufficient)
