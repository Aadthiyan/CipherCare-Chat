# 🚀 Quick Deployment Checklist

## Pre-Deployment (5 minutes)

### 1. Verify Your Setup
- [ ] Git repository is up to date
- [ ] All changes committed and pushed to GitHub
- [ ] `.env.example` file exists with all required variables
- [ ] `requirements.txt` is complete
- [ ] `frontend/package.json` is complete

### 2. Generate Secrets
```bash
# JWT Secret (copy this for Render)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Auth0 Secret (if using Auth0)
openssl rand -hex 32
```

---

## Backend Deployment on Render (10 minutes)

### Step 1: Create Service
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Select your repository

### Step 2: Configure
```
Name: cipercare-backend
Runtime: Python 3.11
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1
Instance: Free (or Starter $7/month for no sleep)
```

### Step 3: Environment Variables
Copy-paste these (replace placeholders):

```bash
DATABASE_URL=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2
CYBORGDB_CONNECTION_STRING=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
VECTOR_DB_TYPE=cyborgdb
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
JWT_SECRET_KEY=<PASTE_YOUR_GENERATED_SECRET_HERE>
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Step 4: Deploy
- [ ] Click "Create Web Service"
- [ ] Wait 3-5 minutes for deployment
- [ ] Copy your backend URL: `https://cipercare-backend-xxxxx.onrender.com`

### Step 5: Test
```bash
# Replace with your actual URL
curl https://cipercare-backend-xxxxx.onrender.com/health
# Expected: {"status":"ok","service":"CiperCare Backend"}
```

---

## Frontend Deployment on Vercel (5 minutes)

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
vercel login
```

### Step 2: Deploy
```bash
cd c:\Users\AADHITHAN\Downloads\Cipercare\frontend
vercel
```

Follow prompts:
- Set up and deploy? **Y**
- Link to existing project? **N**
- Project name? **cipercare**
- Override settings? **N**

### Step 3: Set Environment Variable
```bash
# In Vercel Dashboard → Settings → Environment Variables
NEXT_PUBLIC_API_URL=https://cipercare-backend-xxxxx.onrender.com
```

### Step 4: Redeploy
```bash
vercel --prod
```

### Step 5: Copy URL
- [ ] Copy your frontend URL: `https://cipercare.vercel.app`

---

## Post-Deployment (5 minutes)

### 1. Update Backend CORS
In Render → Environment Variables, add:
```bash
FRONTEND_URL=https://cipercare.vercel.app
```

### 2. Test End-to-End
1. Open `https://cipercare.vercel.app`
2. Try signup
3. Try login
4. Test patient query

### 3. Monitor Logs
- **Render:** Dashboard → Logs
- **Vercel:** Dashboard → Deployments → Logs

---

## ✅ Success Criteria

Your deployment is successful when:
- [ ] Backend `/health` returns 200 OK
- [ ] Frontend loads without errors
- [ ] No CORS errors in browser console
- [ ] Signup flow works
- [ ] Login flow works
- [ ] Patient queries return results

---

## 🆘 Quick Troubleshooting

### Backend won't start
→ Check Render logs for errors
→ Verify all environment variables are set
→ Check DATABASE_URL is correct

### Frontend can't reach backend
→ Verify `NEXT_PUBLIC_API_URL` in Vercel
→ Check CORS settings in backend
→ Ensure backend is running (not sleeping)

### CyborgDB errors
→ Verify `CYBORGDB_API_KEY` is set
→ Verify `CYBORGDB_CONNECTION_STRING` matches `DATABASE_URL`
→ Check PostgreSQL database is active

### Cold starts (504 timeout)
→ Normal for Render free tier
→ First request after sleep takes 60s
→ Upgrade to Starter ($7/month) to prevent sleep

---

## 📞 Need Help?

1. Check full guide: `DEPLOYMENT_GUIDE_COMPLETE.md`
2. Check CyborgDB docs: https://docs.cyborg.co/
3. Check Render docs: https://render.com/docs
4. Check Vercel docs: https://vercel.com/docs

---

**Total Time:** ~25 minutes
**Cost:** $0/month (free tier) or $7/month (no sleep)
