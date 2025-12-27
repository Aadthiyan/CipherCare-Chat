# 🚀 Final Steps to Deploy

## ✅ Git Setup Complete!

Your code is now committed locally. Here are the final steps to deploy:

---

## Step 1: Create GitHub Repository

### Option A: Using GitHub Website (Recommended)
1. Go to https://github.com/new
2. Repository name: `cipercare` (or your choice)
3. Description: "HIPAA-Compliant Medical Chatbot with CyborgDB"
4. **Keep it Private** (contains sensitive config)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### Option B: Using GitHub CLI
```bash
gh repo create cipercare --private --source=. --remote=origin
```

---

## Step 2: Add Remote and Push

After creating the GitHub repository, run these commands:

```bash
# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cipercare.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Example:**
```bash
git remote add origin https://github.com/johndoe/cipercare.git
git branch -M main
git push -u origin main
```

---

## Step 3: Deploy Backend to Render

### 3.1 Generate JWT Secret
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
**Copy the output** - you'll need it for Render.

### 3.2 Create Render Web Service
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect GitHub"** (authorize if needed)
4. Select your `cipercare` repository
5. Configure:
   ```
   Name: cipercare-backend
   Runtime: Python 3.11
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1
   Instance Type: Free (or Starter $7/month)
   ```

### 3.3 Add Environment Variables
Click **"Advanced"** → **"Add Environment Variable"**

**Copy-paste these** (replace `<JWT_SECRET>` with the secret you generated):

```bash
DATABASE_URL=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2

CYBORGDB_CONNECTION_STRING=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

VECTOR_DB_TYPE=cyborgdb

EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

JWT_SECRET_KEY=<PASTE_YOUR_JWT_SECRET_HERE>

ENVIRONMENT=production

LOG_LEVEL=INFO
```

### 3.4 Deploy
1. Click **"Create Web Service"**
2. Wait 3-5 minutes for deployment
3. **Copy your backend URL**: `https://cipercare-backend-xxxxx.onrender.com`

### 3.5 Test Backend
```bash
# Replace with your actual URL
curl https://cipercare-backend-xxxxx.onrender.com/health

# Expected: {"status":"ok","service":"CiperCare Backend"}
```

---

## Step 4: Deploy Frontend to Vercel

### 4.1 Install Vercel CLI
```bash
npm install -g vercel
```

### 4.2 Login to Vercel
```bash
vercel login
```

### 4.3 Deploy Frontend
```bash
cd frontend
vercel
```

**Follow the prompts:**
- Set up and deploy? **Y**
- Which scope? **Your account**
- Link to existing project? **N**
- Project name? **cipercare**
- In which directory is your code located? **./frontend** (or just press Enter if already in frontend)
- Override settings? **N**

### 4.4 Set Environment Variable
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add:
   ```
   Key: NEXT_PUBLIC_API_URL
   Value: https://cipercare-backend-xxxxx.onrender.com
   ```
   (Replace with your actual Render backend URL)
5. Select: **Production**, **Preview**, **Development**
6. Click **Save**

### 4.5 Deploy to Production
```bash
vercel --prod
```

**Copy your frontend URL**: `https://cipercare.vercel.app`

---

## Step 5: Update Backend CORS

1. Go back to Render Dashboard
2. Select your backend service
3. Go to **Environment** tab
4. Add new environment variable:
   ```
   Key: FRONTEND_URL
   Value: https://cipercare.vercel.app
   ```
   (Replace with your actual Vercel URL)
5. Click **Save Changes**
6. Render will automatically redeploy

---

## Step 6: Test End-to-End

### Test Backend
```bash
curl https://cipercare-backend-xxxxx.onrender.com/health
# Expected: {"status":"ok","service":"CiperCare Backend"}

curl https://cipercare-backend-xxxxx.onrender.com/ready
# Expected: {"status":"ready","database":"connected"}
```

### Test Frontend
1. Open your Vercel URL in browser: `https://cipercare.vercel.app`
2. Open browser console (F12) → Network tab
3. Try to signup:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `SecurePass123!`
   - Full Name: `Test User`
   - Role: `resident`
   - Department: `Emergency Medicine`
4. Check for:
   - ✅ No CORS errors
   - ✅ API calls reach backend
   - ✅ Signup succeeds

---

## ✅ Success Criteria

Your deployment is successful when:

### Backend (Render)
- [ ] `/health` returns `{"status":"ok"}`
- [ ] `/ready` returns `{"status":"ready","database":"connected"}`
- [ ] Logs show: `✓ POSTGRES Ready`, `✓ DB Ready`, `✓ LLM Ready`
- [ ] No errors in logs

### Frontend (Vercel)
- [ ] Application loads without errors
- [ ] No CORS errors in browser console
- [ ] API calls reach backend (check Network tab)
- [ ] Signup flow works

### Integration
- [ ] Signup → Verify → Login → Query works end-to-end

---

## 🎉 You're Done!

**Your URLs:**
- Backend: `https://cipercare-backend-xxxxx.onrender.com`
- Frontend: `https://cipercare.vercel.app`

**Next Steps:**
1. ✅ Test all functionality
2. ✅ Invite team members
3. ✅ Add more patient data
4. ✅ Monitor logs (Render + Vercel dashboards)
5. ✅ Set up monitoring alerts

---

## 🆘 Troubleshooting

### "Cold start timeout (504)"
- **Cause:** Render free tier sleeps after 15 minutes
- **Solution:** Wait 60 seconds for first request, or upgrade to Starter ($7/month)

### "CORS error"
- **Cause:** `FRONTEND_URL` not set in Render
- **Solution:** Add `FRONTEND_URL` environment variable in Render

### "Failed to fetch"
- **Cause:** `NEXT_PUBLIC_API_URL` not set in Vercel
- **Solution:** Add environment variable in Vercel → Settings → Environment Variables → Redeploy

### "Database connection failed"
- **Cause:** Invalid `DATABASE_URL`
- **Solution:** Verify connection string in Render environment variables

---

## 📚 Documentation Reference

- **Complete Guide:** `DEPLOYMENT_GUIDE_COMPLETE.md`
- **Quick Checklist:** `QUICK_DEPLOY_CHECKLIST.md`
- **CyborgDB Guide:** `CYBORGDB_DEPLOYMENT_GUIDE.md`
- **Stack Validation:** `STACK_VALIDATION.md`

---

## 💰 Current Cost

**Free Tier:**
- Render Free: $0/month
- Vercel Free: $0/month
- Neon Free: $0/month
- **Total: $0/month** ✅

**Upgrade when needed:**
- Render Starter: $7/month (no sleep)
- Neon Pro: $19/month (8GB storage)

---

**Good luck! 🚀**

If you encounter issues, check the comprehensive guides or the troubleshooting sections.
