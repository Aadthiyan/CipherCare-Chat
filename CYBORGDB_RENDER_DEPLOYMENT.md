# CyborgDB Deployment Guide for Render

## Quick Fix: Deploy CyborgDB as Separate Render Service

### Option 1: Using Render Blueprint (Recommended - One Click)

1. **Push the updated code to GitHub** (you already did this!)
   ```bash
   git add .
   git commit -m "Added render.yaml for CyborgDB deployment"
   git push origin main
   ```

2. **Create New Blueprint on Render**
   - Go to https://dashboard.render.com/
   - Click **"New" → "Blueprint"**
   - Connect your GitHub repo: `Aadthiyan/CipherCare-Chat`
   - Render will detect the `render.yaml` file
   - Click **"Apply"**

3. **Set Environment Variables**
   For **ciphercare-cyborgdb** service:
   - `CYBORGDB_API_KEY`: Your CyborgDB API key (generate one or use existing)
   - `DATABASE_URL`: (optional) If CyborgDB needs database

   For **ciphercare-backend** service:
   - All your existing env vars (GROQ_API_KEY, HF_API_TOKEN, etc.)
   - `CYBORGDB_BASE_URL` is already set to `http://ciphercare-cyborgdb:8002`

4. **Deploy!**
   - Render will deploy both services
   - Backend will connect to CyborgDB via internal network
   - No localhost issues!

---

### Option 2: Manual Deployment (If Blueprint doesn't work)

#### Step 1: Deploy CyborgDB Service

1. Go to Render Dashboard → **New** → **Web Service**
2. Connect your repo
3. Configure:
   - **Name**: `ciphercare-cyborgdb`
   - **Environment**: `Docker`
   - **Docker Build Context**: `.`
   - **Dockerfile Path**: `./docker/cyborgdb.Dockerfile`
   - **Plan**: Starter ($7/month)
   
4. Add Environment Variables:
   - `CYBORGDB_API_KEY`: [Your API Key]
   - `CYBORGDB_DATA_DIR`: `/data`
   
5. **Add Persistent Disk** (Optional but recommended):
   - Name: `cyborgdb-data`
   - Mount Path: `/data`
   - Size: 1 GB

6. Click **Create Web Service**

#### Step 2: Update Backend Service

1. Go to your existing backend service on Render
2. Go to **Environment** tab
3. Update or add this variable:
   ```
   CYBORGDB_BASE_URL=http://ciphercare-cyborgdb:8002
   ```
   Note: Using internal Render URL (service name), NOT localhost!

4. **Manual Deploy** to apply changes

---

### Option 3: Use CyborgDB Managed Cloud (Enterprise)

If you want to avoid managing infrastructure entirely:

1. **Contact CyborgDB Sales**: https://www.cyborg.co
2. **Sign up for Enterprise Plan** (managed cloud service)
3. They'll provide you with a **cloud endpoint URL**
4. Update your `.env`:
   ```
   CYBORGDB_BASE_URL=https://your-managed-instance.cyborgdb.cloud
   CYBORGDB_API_KEY=your_cloud_api_key
   ```
5. No need to deploy CyborgDB yourself!

---

## Verification Steps

After deployment, verify the connection:

1. **Check CyborgDB Health**
   ```bash
   curl https://ciphercare-cyborgdb.onrender.com/health
   ```

2. **Check Backend Logs** on Render
   - Should see: `CyborgDB Lite client initialized successfully`
   - Should NOT see: `Connection refused to localhost:8002`

3. **Test Query Endpoint**
   - Try a patient query from your frontend
   - Should work without mock data fallback

---

## What Changed?

### Before (Local Dev):
```
Backend → localhost:8002 → CyborgDB (local)
```

### After (Render):
```
Backend Service → http://ciphercare-cyborgdb:8002 → CyborgDB Service
(Internal Render Network)
```

---

## Troubleshooting

### Issue: "Connection refused"
**Solution**: Make sure both services are deployed and `CYBORGDB_BASE_URL` uses the service name (not localhost)

### Issue: "Index creation failed"
**Solution**: Add persistent disk to CyborgDB service (see Step 1, point 5)

### Issue: "Out of memory"
**Solution**: Upgrade CyborgDB service plan to Standard ($25/month) for more RAM

---

## Cost Estimate

- **CyborgDB Service**: $7/month (Starter) or $25/month (Standard)
- **Backend Service**: $7/month (Starter) or $25/month (Standard)
- **Persistent Disk** (1GB): Free
- **Total**: ~$14-50/month depending on plan

---

## Alternative: Switch to Alternative Vector DB

If you want to avoid CyborgDB costs, you could switch to:

1. **Pinecone** (Free tier: 100K vectors)
2. **Weaviate Cloud** (Free tier available)
3. **Qdrant Cloud** (Free tier: 1GB cluster)

Let me know if you want me to implement any of these alternatives!
