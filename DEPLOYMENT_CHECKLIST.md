# ✅ Render Deployment Checklist

## Pre-Deployment (Do These First)

### 1. Verify Code Changes
```bash
# Check that all new files exist:
ls backend/vector_db_manager.py       # ✓
ls backend/phi_scrubber_light.py      # ✓
ls requirements-render-free.txt       # ✓
ls render.yaml                        # ✓
ls .env.render-free                  # ✓
ls RENDER_DEPLOYMENT_GUIDE.md        # ✓
```

### 2. Test Locally (Optional but Recommended)
```bash
# Install lightweight dependencies
pip install -r requirements-render-free.txt

# Test embedder with MiniLM
python -c "
from embeddings.embedder import ClinicalEmbedder
embedder = ClinicalEmbedder()
print(f'✓ Embedder ready (dim: {embedder.embedding_dim})')
"

# Your backend should start without memory issues
# python backend/main.py
```

### 3. Create External Accounts

#### Pinecone (Required)
- [ ] Go to https://pinecone.io
- [ ] Click "Sign Up Free"
- [ ] Create account (email + password)
- [ ] Go to "API Keys" in dashboard
- [ ] Copy your API key
- [ ] Note environment: `gcp-starter` (for free tier)
- [ ] **Save these values** for Render setup

#### Render (Required)
- [ ] Go to https://render.com
- [ ] Sign up with GitHub
- [ ] Authorize GitHub access

### 4. Prepare GitHub Repository
```bash
# Ensure all changes are committed
git add .
git commit -m "feat: Render free tier optimizations"
git push origin main

# Verify on GitHub:
# - requirements-render-free.txt exists
# - backend/vector_db_manager.py exists
# - render.yaml exists
```

---

## Deployment Steps

### Step 1: Create Render Service (5 min)

- [ ] Log into https://dashboard.render.com
- [ ] Click "New +" button (top right)
- [ ] Select "Web Service"
- [ ] Select "Build and deploy from Git repository"
- [ ] Authorize GitHub (if not already)
- [ ] Select your CipherCare repository
- [ ] Select "main" branch

### Step 2: Configure Service Settings (5 min)

Fill in these fields:

- [ ] **Name:** `cipercare-backend` (or your preference)
- [ ] **Region:** Keep default (closest to you)
- [ ] **Runtime:** `Python 3.11`
- [ ] **Build Command:** `pip install -r requirements-render-free.txt`
- [ ] **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

### Step 3: Add Environment Variables (5 min)

Click "Advanced" → "Add Environment Variable" for each:

- [ ] `EMBEDDING_MODEL` = `sentence-transformers/all-MiniLM-L6-v2`
- [ ] `VECTOR_DB_TYPE` = `pinecone`
- [ ] `PINECONE_API_KEY` = (from Pinecone dashboard)
- [ ] `PINECONE_ENV` = `gcp-starter`
- [ ] `JWT_SECRET_KEY` = (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `DISABLE_SPACY` = `true`
- [ ] `DISABLE_PREFECT` = `true`
- [ ] `ENVIRONMENT` = `production`

### Step 4: Deploy (2 min)

- [ ] Review settings one final time
- [ ] Click "Create Web Service"
- [ ] Wait for deployment to complete (2-3 min)
- [ ] Check logs for "✓ Backend online" message
- [ ] **Copy your Render URL** (e.g., `https://cipercare-backend-xxxxx.onrender.com`)

---

## Post-Deployment Testing

### Test 1: Health Check
```bash
curl https://your-render-url/health

# Expected response:
# {"status": "ready", "database": "connected"}
```

- [ ] Status: 200 OK
- [ ] Response shows "connected"

### Test 2: Authentication
```bash
curl -X POST https://your-render-url/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=resident&password=password123"

# Expected: JWT token in response
```

- [ ] Status: 200 OK
- [ ] Returns `access_token`
- [ ] Save token for next test

### Test 3: Search Endpoint
```bash
# Replace TOKEN with token from Test 2
curl -X POST https://your-render-url/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "diabetes", "patient_id": "P123"}'

# Expected: Search results
```

- [ ] Status: 200 OK
- [ ] Returns search results
- [ ] No CORS errors

### Test 4: Wait for Cold Start
```
First request after deployment:
- [ ] Takes 60 seconds (container cold start)
- [ ] Eventually returns successful response
- [ ] Subsequent requests are fast (2-3s)

This is normal on free tier!
```

### Test 5: Check Pinecone
```
Go to https://pinecone.io dashboard:
- [ ] Your index is listed
- [ ] Shows 0 vectors (until you upload data)
- [ ] API key works
```

---

## Monitoring & Verification

### 24-Hour Monitoring Checklist

- [ ] Check Render logs daily for first 24 hours
- [ ] Monitor Pinecone usage in dashboard
- [ ] Verify no "MemoryError" in logs
- [ ] Verify no "CORS" errors
- [ ] Test search functionality multiple times
- [ ] Check that vectors persist (search data after restart)

### Logs Location
```
Render Dashboard → Your Service → Logs
Look for:
✓ "✓ Backend online"
✓ "✓ Pinecone initialized"
✓ "Models initialized: ['embedder', 'db', ...]"
```

---

## Connecting Frontend

### Update Frontend Configuration

In your Next.js frontend (or wherever API is called):

```javascript
// Old (local)
const API_URL = "http://localhost:8000"

// New (Render)
const API_URL = "https://your-render-url"

// Update CORS origin in Render env if needed
```

### Frontend Tests
- [ ] Login works
- [ ] Search returns results
- [ ] No CORS errors in browser console
- [ ] UI displays patient data
- [ ] Rate limiting works

---

## Troubleshooting

### If Deployment Fails

**Error: MemoryError**
- [ ] Verify `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
- [ ] Check `requirements-render-free.txt` is being used
- [ ] Ensure `DISABLE_SPACY=true`

**Error: Module not found**
- [ ] Verify `backend/vector_db_manager.py` exists
- [ ] Verify `backend/phi_scrubber_light.py` exists
- [ ] Check git push completed

**Error: Pinecone connection failed**
- [ ] Verify `PINECONE_API_KEY` is correct
- [ ] Verify `PINECONE_ENV=gcp-starter`
- [ ] Check Pinecone dashboard for API key validity

### If Tests Fail

**Health check returns 500**
- [ ] Check logs: `Render Dashboard → Logs`
- [ ] Look for initialization errors
- [ ] Verify all environment variables set

**Search returns 401 (Unauthorized)**
- [ ] Token expired (normal)
- [ ] Get new token from /api/token endpoint
- [ ] Verify JWT_SECRET_KEY is set

**Search returns 504 (Gateway Timeout)**
- [ ] Normal on first request (cold start)
- [ ] Container is spinning up, be patient
- [ ] Try again in 60 seconds

---

## Success Indicators ✅

After all tests pass, you should see:

- [ ] Health check: 200 OK
- [ ] Auth endpoint returns JWT
- [ ] Search endpoint returns results
- [ ] No memory errors in logs
- [ ] Pinecone shows connection active
- [ ] Cold start time: 30-60 seconds (normal)
- [ ] Warm requests: 1-3 seconds
- [ ] Zero cost (free tier)

---

## Final Checklist

Before announcing deployment complete:

- [ ] All tests passing
- [ ] Logs show no errors
- [ ] Pinecone connected
- [ ] Frontend working
- [ ] Team can access API
- [ ] Documentation updated
- [ ] GitHub repo updated
- [ ] Monitoring setup

---

## Maintenance Tasks

### Weekly
- [ ] Check Render logs for errors
- [ ] Verify Pinecone usage (should be low)
- [ ] Test basic functionality

### Monthly
- [ ] Review performance metrics
- [ ] Check if scaling needed
- [ ] Update documentation

### As Needed
- [ ] Update model to all-mpnet-base-v2 (requires paid tier)
- [ ] Add more Pinecone storage
- [ ] Upgrade Render to Hobby plan

---

## Support

If you get stuck:

1. **Check logs first:** Render Dashboard → Logs
2. **Read deployment guide:** [RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md)
3. **Check issues doc:** [RENDER_DEPLOYMENT_ISSUES.md](RENDER_DEPLOYMENT_ISSUES.md)
4. **Review fixes:** [FIXES_APPLIED.md](FIXES_APPLIED.md)

---

## Timeline

- [ ] Step 1 (Verify changes): 5 min
- [ ] Step 2 (Pinecone signup): 5 min
- [ ] Step 3 (Render signup): 2 min
- [ ] Step 4 (Deploy): 10 min
- [ ] Step 5 (Testing): 10 min
- [ ] **Total: ~32 minutes**

---

## You're Done! 🎉

Once all tests pass, your CipherCare backend is live on Render free tier!

**Your backend URL:**
```
https://your-app.onrender.com
```

Share this with your team and start using it!

