# 🚨 CyborgDB 502 Error - Quick Start Fix

## The Problem

You're getting **502 Bad Gateway** errors when querying patient data. This happens because:

1. Your CyborgDB service on Render is down/crashed (returning 502)
2. Your local `.env` points to `localhost:8002` but CyborgDB isn't running locally
3. No patient data has been uploaded to CyborgDB yet

## Quick Fix (Choose One)

### Option A: Run Locally (Fastest - 5 minutes)

```bash
# 1. Fix .env configuration
python fix_env_config.py
# Select option 1 (Local development)

# 2. Start CyborgDB (in separate terminal, keep it running)
cyborgdb serve --port 8002

# 3. Upload test data
python upload_to_render.py
# Select option 1 (100 records for quick test)

# 4. Verify it works
python check_cyborgdb_data.py

# 5. Start backend
python run_backend.py
```

### Option B: Fix Render Deployment (Production - 30 minutes)

```bash
# 1. Check Render dashboard
# Go to https://dashboard.render.com
# Find 'ciphercare-cyborgdb' service
# If crashed: Check logs, may need paid plan

# 2. Fix .env for upload
python fix_env_config.py
# Select option 3 (Hybrid)

# 3. Test connection
python diagnose_cyborgdb.py
# Should show "✓ Service is UP"

# 4. Upload data
python upload_to_render.py
# Select option 1 first (test), then option 4 (all data)

# 5. Verify
python check_cyborgdb_data.py
```

## Diagnostic Tools

```bash
# Check what's wrong
python diagnose_cyborgdb.py

# Check if data exists
python check_cyborgdb_data.py

# Fix .env configuration
python fix_env_config.py
```

## Full Documentation

See **[CYBORGDB_FIX_GUIDE.md](./CYBORGDB_FIX_GUIDE.md)** for:
- Complete diagnosis
- Step-by-step solutions
- Troubleshooting common issues
- Verification checklist

## Need Help?

1. Run diagnostics: `python diagnose_cyborgdb.py`
2. Check the full guide: `CYBORGDB_FIX_GUIDE.md`
3. Share Render logs if issue persists
