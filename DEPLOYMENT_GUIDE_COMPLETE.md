# Complete Deployment Guide: CipherCare
## Backend (Render) + Frontend (Vercel)

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Backend Deployment (Render)](#backend-deployment-render)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [CyborgDB Configuration](#cyborgdb-configuration)
6. [Environment Variables](#environment-variables)
7. [Testing Deployment](#testing-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Overview

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    Vercel (Frontend)                     │
│                    Next.js Application                   │
│                  https://your-app.vercel.app             │
└────────────────────┬────────────────────────────────────┘
                     │ API Calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Render (Backend)                        │
│              FastAPI + Python 3.11                       │
│        https://cipercare-backend.onrender.com            │
└──────────┬──────────────────────┬───────────────────────┘
           │                      │
           ▼                      ▼
    ┌──────────────┐      ┌──────────────────┐
    │  PostgreSQL  │      │    CyborgDB      │
    │  (Neon.tech) │      │ Vector Database  │
    │  User Data   │      │ Medical Records  │
    └──────────────┘      └──────────────────┘
```

---

## Prerequisites

### Required Accounts
- ✅ **Render Account** - [Sign up](https://render.com)
- ✅ **Vercel Account** - [Sign up](https://vercel.com)
- ✅ **GitHub Account** - For deployment
- ✅ **Neon PostgreSQL** - Already configured (from .env.example)
- ✅ **CyborgDB API Key** - Already have: `cyborg_6063109509bb4cb9b0b1072ca20486e2`

### Optional Services
- 📧 **Brevo** (Email service) - For OTP verification
- 🤖 **Groq API** - For LLM responses

---

## Backend Deployment (Render)

### Step 1: Prepare Your Repository

1. **Ensure all files are committed:**
```bash
cd c:\Users\AADHITHAN\Downloads\Cipercare
git add .
git commit -m "feat: prepare for Render and Vercel deployment"
git push origin main
```

### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
```
Name: cipercare-backend
Runtime: Python 3.11
Region: Choose closest to your users (e.g., Oregon, Frankfurt)
Branch: main
Root Directory: (leave empty)
```

**Build & Deploy:**
```
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1
```

**Instance Type:**
```
Free (512 MB RAM, 0.1 CPU)
OR
Starter ($7/month - 512 MB RAM, 0.5 CPU, no sleep)
```

### Step 3: Configure Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** and add these:

#### Core Configuration
```bash
# Database
DATABASE_URL=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# CyborgDB Configuration
CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2
CYBORGDB_CONNECTION_STRING=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
VECTOR_DB_TYPE=cyborgdb

# Embedding Model (768-dim for quality, or 384-dim for free tier)
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Security
JWT_SECRET_KEY=<generate using: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### Optional Services
```bash
# Email Service (Brevo)
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=noreply@cipercare.com
SENDER_NAME=CipherCare
FRONTEND_URL=https://your-app.vercel.app

# LLM Service (Groq)
GROQ_API_KEY=your_groq_api_key_here
```

**Generate JWT Secret:**
```bash
# Run this locally to generate a secure key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Deploy Backend

1. Click **"Create Web Service"**
2. Wait for deployment (3-5 minutes)
3. Monitor logs for successful startup:
   ```
   ✓ POSTGRES Ready
   ✓ EMBEDDER Ready
   ✓ DB Ready
   ✓ LLM Ready
   🚀 Backend online on http://0.0.0.0:8000
   ```

4. **Copy your backend URL:**
   ```
   Example: https://cipercare-backend-xxxxx.onrender.com
   ```

### Step 5: Test Backend

```bash
# Health check
curl https://cipercare-backend-xxxxx.onrender.com/health

# Expected response:
# {"status":"ok","service":"CiperCare Backend"}

# Readiness check
curl https://cipercare-backend-xxxxx.onrender.com/ready

# Expected response:
# {"status":"ready","database":"connected"}
```

---

## Frontend Deployment (Vercel)

### Step 1: Prepare Frontend

1. **Create/Update `vercel.json` in frontend directory:**

```bash
# Navigate to frontend
cd frontend
```

Create `vercel.json`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://cipercare-backend-xxxxx.onrender.com/:path*"
    }
  ]
}
```

2. **Update `.env.local` (for local development):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 2: Deploy to Vercel

#### Option A: Using Vercel CLI (Recommended)

1. **Install Vercel CLI:**
```bash
npm install -g vercel
```

2. **Login to Vercel:**
```bash
vercel login
```

3. **Deploy:**
```bash
cd c:\Users\AADHITHAN\Downloads\Cipercare\frontend
vercel
```

4. **Follow prompts:**
   - Set up and deploy? **Y**
   - Which scope? **Your account**
   - Link to existing project? **N**
   - Project name? **cipercare** (or your choice)
   - Directory? **./frontend** or **./** (if already in frontend)
   - Override settings? **N**

#### Option B: Using Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure:
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   ```

### Step 3: Configure Environment Variables in Vercel

1. In Vercel Dashboard → Your Project → **"Settings"** → **"Environment Variables"**

2. Add these variables:

```bash
# Backend API URL (CRITICAL!)
NEXT_PUBLIC_API_URL=https://cipercare-backend-xxxxx.onrender.com

# Optional: Auth0 (if using)
AUTH0_SECRET=<generate using: openssl rand -hex 32>
AUTH0_BASE_URL=https://your-app.vercel.app
AUTH0_ISSUER_BASE_URL=https://your-tenant.auth0.com
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
```

**Important:** 
- Set environment for: **Production**, **Preview**, and **Development**
- Replace `xxxxx` with your actual Render backend URL

### Step 4: Deploy Frontend

1. Click **"Deploy"**
2. Wait for deployment (2-3 minutes)
3. **Copy your frontend URL:**
   ```
   Example: https://cipercare.vercel.app
   ```

### Step 5: Update Backend CORS

Go back to **Render** → Your Backend Service → **Environment Variables**

Add/Update:
```bash
FRONTEND_URL=https://cipercare.vercel.app
```

**Update `backend/main.py` CORS origins** (if not dynamic):
```python
origins = [
    "http://localhost:3000",
    "https://cipercare.vercel.app",  # Add your Vercel URL
    "https://*.vercel.app",  # Allow all Vercel preview deployments
]
```

Commit and push changes:
```bash
git add backend/main.py
git commit -m "feat: add Vercel URL to CORS origins"
git push origin main
```

Render will auto-deploy the update.

---

## CyborgDB Configuration

### Understanding Your Setup

Based on your `.env.example`, you're using **CyborgDB Embedded** with PostgreSQL backend:

```bash
CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2
CYBORGDB_CONNECTION_STRING=postgresql://neondb_owner:...
```

### CyborgDB Deployment Options

#### Option 1: CyborgDB Embedded (Current Setup) ✅ RECOMMENDED

**What it is:**
- Uses `cyborgdb` Python library directly
- Stores vectors in your PostgreSQL database (Neon)
- No separate CyborgDB server needed
- Perfect for Render deployment

**Configuration:**
```bash
VECTOR_DB_TYPE=cyborgdb
CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2
CYBORGDB_CONNECTION_STRING=postgresql://...
```

**Pros:**
- ✅ No additional infrastructure
- ✅ Uses existing PostgreSQL (Neon)
- ✅ End-to-end encryption
- ✅ Works on Render free tier

**Cons:**
- ⚠️ Limited by PostgreSQL storage (Neon free: 512MB)
- ⚠️ Slower than dedicated vector DB

#### Option 2: Pinecone (Cloud Alternative)

If you need more storage or better performance:

**Configuration:**
```bash
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=gcp-starter
```

**Pros:**
- ✅ 1GB free storage
- ✅ Faster queries
- ✅ Persistent storage

**Cons:**
- ❌ No encryption (unlike CyborgDB)
- ❌ Requires separate account

### Recommended: Stick with CyborgDB Embedded

Your current setup is optimal for deployment. CyborgDB provides:
- 🔒 End-to-end encryption
- 🔐 Confidential vector search
- 💾 Uses existing PostgreSQL
- 🚀 No additional services needed

---

## Environment Variables

### Complete Environment Variable Reference

#### Backend (Render)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | `postgresql://...` | PostgreSQL connection string |
| `CYBORGDB_API_KEY` | ✅ Yes | `cyborg_xxx` | CyborgDB API key |
| `CYBORGDB_CONNECTION_STRING` | ✅ Yes | `postgresql://...` | Same as DATABASE_URL |
| `VECTOR_DB_TYPE` | ✅ Yes | `cyborgdb` | Vector DB type |
| `EMBEDDING_MODEL` | ✅ Yes | `sentence-transformers/all-mpnet-base-v2` | Embedding model |
| `JWT_SECRET_KEY` | ✅ Yes | `<random-string>` | JWT signing key |
| `ENVIRONMENT` | ✅ Yes | `production` | Environment name |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `BREVO_API_KEY` | No | `xkeysib-xxx` | Email service key |
| `SENDER_EMAIL` | No | `noreply@cipercare.com` | Email sender |
| `SENDER_NAME` | No | `CipherCare` | Email sender name |
| `FRONTEND_URL` | No | `https://cipercare.vercel.app` | Frontend URL for CORS |
| `GROQ_API_KEY` | No | `gsk_xxx` | LLM API key |

#### Frontend (Vercel)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | `https://cipercare-backend.onrender.com` | Backend API URL |
| `AUTH0_SECRET` | No | `<random-hex>` | Auth0 secret |
| `AUTH0_BASE_URL` | No | `https://cipercare.vercel.app` | Your app URL |
| `AUTH0_ISSUER_BASE_URL` | No | `https://tenant.auth0.com` | Auth0 domain |
| `AUTH0_CLIENT_ID` | No | `xxx` | Auth0 client ID |
| `AUTH0_CLIENT_SECRET` | No | `xxx` | Auth0 client secret |

---

## Testing Deployment

### 1. Test Backend Endpoints

```bash
# Set your backend URL
BACKEND_URL=https://cipercare-backend-xxxxx.onrender.com

# Health check
curl $BACKEND_URL/health

# Readiness check
curl $BACKEND_URL/ready

# Test signup
curl -X POST $BACKEND_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "role": "resident",
    "department": "Emergency Medicine"
  }'

# Test login (after email verification)
curl -X POST $BACKEND_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

### 2. Test Frontend

1. Open your Vercel URL: `https://cipercare.vercel.app`
2. Test signup flow
3. Check email for OTP (if Brevo configured)
4. Test login
5. Test patient search/query

### 3. Test Integration

1. Open browser console (F12)
2. Check Network tab for API calls
3. Verify API calls go to Render backend
4. Check for CORS errors (should be none)

---

## Troubleshooting

### Backend Issues

#### Issue: "MemoryError" on Render
**Cause:** Embedding model too large for free tier (512MB RAM)

**Solution:**
```bash
# Use smaller model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# OR upgrade to Render Starter ($7/month)
```

#### Issue: "Database connection failed"
**Cause:** Invalid DATABASE_URL or Neon database sleeping

**Solution:**
1. Verify `DATABASE_URL` in Render environment variables
2. Check Neon dashboard - database should be active
3. Test connection:
   ```bash
   psql "postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
   ```

#### Issue: "CyborgDB initialization failed"
**Cause:** Missing API key or connection string

**Solution:**
1. Verify `CYBORGDB_API_KEY` is set
2. Verify `CYBORGDB_CONNECTION_STRING` matches `DATABASE_URL`
3. Check Render logs for specific error

#### Issue: "Cold start timeout" (504)
**Cause:** Render free tier sleeps after 15 minutes of inactivity

**Solution:**
- **Accept it:** First request after sleep takes 60s (normal for free tier)
- **Upgrade:** Render Starter ($7/month) prevents sleep
- **Workaround:** Use a cron job to ping `/health` every 10 minutes

### Frontend Issues

#### Issue: "Failed to fetch" or CORS errors
**Cause:** Backend URL not configured or CORS not allowing frontend

**Solution:**
1. Verify `NEXT_PUBLIC_API_URL` in Vercel environment variables
2. Update backend CORS origins in `backend/main.py`
3. Redeploy both frontend and backend

#### Issue: "Environment variable not found"
**Cause:** Environment variables not set in Vercel

**Solution:**
1. Go to Vercel → Settings → Environment Variables
2. Add `NEXT_PUBLIC_API_URL`
3. Redeploy (Vercel → Deployments → Redeploy)

#### Issue: "404 Not Found" on routes
**Cause:** Next.js routing issue

**Solution:**
1. Check `vercel.json` configuration
2. Ensure `framework: "nextjs"` is set
3. Verify build output in deployment logs

### CyborgDB Issues

#### Issue: "Index not found"
**Cause:** CyborgDB index not created

**Solution:**
```python
# Run this script to create index (locally or via Render console)
python -c "
from backend.cyborg_lite_manager import get_cyborg_manager
manager = get_cyborg_manager()
print('Index created successfully')
"
```

#### Issue: "Encryption key not found"
**Cause:** CyborgDB encryption key not initialized

**Solution:**
- CyborgDB handles encryption automatically
- Verify `CYBORGDB_API_KEY` is correct
- Check CyborgDB documentation: https://docs.cyborg.co/

---

## Post-Deployment Checklist

### Backend (Render)
- [ ] Health endpoint returns 200 OK
- [ ] Database connection successful
- [ ] CyborgDB initialized
- [ ] Embedding model loaded
- [ ] LLM service initialized (optional)
- [ ] Logs show no errors
- [ ] CORS configured for Vercel URL

### Frontend (Vercel)
- [ ] Application loads successfully
- [ ] API calls reach backend
- [ ] No CORS errors in console
- [ ] Signup flow works
- [ ] Login flow works
- [ ] Patient search works
- [ ] Environment variables set

### Integration
- [ ] End-to-end signup → login → query works
- [ ] Email verification works (if Brevo configured)
- [ ] Patient data queries return results
- [ ] LLM responses generated (if Groq configured)

---

## Monitoring & Maintenance

### Render Monitoring
1. **Logs:** Render Dashboard → Your Service → Logs
2. **Metrics:** Monitor CPU, Memory, Response Time
3. **Alerts:** Set up email alerts for failures

### Vercel Monitoring
1. **Analytics:** Vercel Dashboard → Analytics
2. **Logs:** Vercel Dashboard → Deployments → View Logs
3. **Performance:** Check Core Web Vitals

### Database Monitoring (Neon)
1. **Usage:** Neon Dashboard → Your Project → Usage
2. **Storage:** Monitor storage usage (free tier: 512MB)
3. **Connections:** Monitor active connections

---

## Scaling & Upgrades

### When to Upgrade

#### Render Free → Starter ($7/month)
**Upgrade when:**
- Cold starts are annoying users
- Need 99.9% uptime
- Want faster deployments

#### Render Starter → Pro ($12/month)
**Upgrade when:**
- Need more memory (1GB+)
- Need better embedding model (all-mpnet-base-v2)
- Need multiple workers

#### Neon Free → Pro ($25/month)
**Upgrade when:**
- Storage exceeds 512MB
- Need more connections
- Need better performance

---

## Security Best Practices

1. **Never commit `.env` files**
   ```bash
   # Verify .gitignore includes:
   .env
   .env.local
   .env.*.local
   ```

2. **Rotate secrets regularly**
   - JWT_SECRET_KEY every 90 days
   - API keys every 6 months

3. **Use strong passwords**
   - Minimum 12 characters
   - Include uppercase, lowercase, numbers, symbols

4. **Enable HTTPS only**
   - Render and Vercel provide free SSL
   - Never use HTTP in production

5. **Monitor logs for suspicious activity**
   - Failed login attempts
   - Unusual API usage
   - Database errors

---

## Support & Resources

### Documentation
- **CyborgDB:** https://docs.cyborg.co/
- **Render:** https://render.com/docs
- **Vercel:** https://vercel.com/docs
- **Next.js:** https://nextjs.org/docs
- **FastAPI:** https://fastapi.tiangolo.com/

### Community
- **CyborgDB Discord:** Check docs for invite
- **Render Community:** https://community.render.com/
- **Vercel Discord:** https://vercel.com/discord

---

## Quick Reference

### Useful Commands

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Auth0 secret
openssl rand -hex 32

# Test backend locally
cd backend
uvicorn backend.main:app --reload

# Test frontend locally
cd frontend
npm run dev

# Deploy to Vercel
cd frontend
vercel --prod

# View Render logs
# Go to: https://dashboard.render.com → Your Service → Logs
```

### Important URLs

```
Backend (Render): https://cipercare-backend-xxxxx.onrender.com
Frontend (Vercel): https://cipercare.vercel.app
Database (Neon): https://console.neon.tech/
CyborgDB Docs: https://docs.cyborg.co/
```

---

## Conclusion

You now have:
- ✅ Backend deployed on Render
- ✅ Frontend deployed on Vercel
- ✅ CyborgDB configured for encrypted vector search
- ✅ PostgreSQL database on Neon
- ✅ Secure authentication with JWT
- ✅ Email verification (optional)
- ✅ LLM integration (optional)

**Next Steps:**
1. Test all functionality end-to-end
2. Set up monitoring and alerts
3. Configure custom domain (optional)
4. Enable email service (Brevo)
5. Add more patient data
6. Invite team members

**Questions?** Check the troubleshooting section or refer to the official documentation links above.

---

**Last Updated:** December 28, 2024
**Version:** 1.0.0
