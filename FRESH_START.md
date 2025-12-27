# CiperCare - Fresh Start Guide

**Date:** December 26, 2025  
**Status:** Ready to set up from scratch

---

## Current State
✅ Database: Clean (all users deleted)  
✅ Backend: Running on http://127.0.0.1:8000  
✅ Frontend: Running on http://127.0.0.1:3000  
✅ Real Patient Data: 221 Synthea patients loaded  

---

## Step 1: Create Your First User (Signup)

Go to: http://localhost:3000/auth/signup

Fill in the form:
- **Username:** Enter your username (e.g., `doctor1`)
- **Email:** Enter your email (e.g., `doctor@hospital.com`)
- **Full Name:** Your name (e.g., `Dr. John Smith`)
- **Password:** Create a secure password (minimum 8 characters)
- **Department:** Select your department
- **License Number:** Enter your medical license

Click **Create Account**

### What happens:
1. Account created in database
2. You'll get an OTP code (shown on screen for testing)
3. Enter the OTP code to verify
4. Account is verified and ready

---

## Step 2: Login with Your Account

Go to: http://localhost:3000/auth/login

Enter:
- **Username:** The username you just created
- **Password:** The password you just created

Click **Sign In**

### What happens:
1. Backend validates credentials
2. JWT token is generated
3. Token saved in localStorage
4. You're redirected to `/dashboard`
5. Dashboard loads with 221 real patients

---

## Step 3: Access the Dashboard

Once logged in, you'll see:
- **Sidebar** with navigation
- **Patient Selector** to choose which patient to query
- **Chat Interface** to ask questions about patients
- **Medical Records** showing real Synthea data

---

## Available Pages After Login

1. **Dashboard** (`/dashboard`)
   - Main chat interface
   - Patient selector
   - Query patient data
   - AI-powered responses

2. **Patients** (`/dashboard/patients`)
   - List of all 221 patients
   - Patient search
   - Patient details

3. **Records** (`/dashboard/records`)
   - Medical records display
   - Patient history
   - Conditions and medications

4. **Settings** (`/dashboard/settings`)
   - Account settings
   - Preferences

---

## Testing the System

### Login Credentials (After Signup)
Use the credentials you just created

### Real Patient Data
- **Total Patients:** 221 Synthea patients
- **Patient Structure:** 
  - Demographics (age, gender, address)
  - Conditions (multiple per patient)
  - Medications (multiple per patient)

### Example Queries
Once logged in, try these queries:
- "What conditions does this patient have?"
- "What medications is the patient taking?"
- "Summarize this patient's medical history"
- "Are there any drug interactions?"

---

## Troubleshooting

### Signup Page Blank
- Refresh the page: `Ctrl + F5`
- Check browser console for errors
- Ensure backend is running

### Login Failed
- Check credentials are correct
- Ensure you completed the OTP verification
- Try logging out and logging back in

### Dashboard Blank
- Wait for page to load (auto-redirect if not logged in)
- Check browser console for errors
- Ensure token is in localStorage

### Patient Data Not Showing
- Verify you're logged in
- Check that 221 patients are in the JSON file
- Refresh the page

---

## Quick Commands

**Check if user exists:**
```bash
python check_user.py
```

**Create a test user directly:**
```bash
python create_user_direct.py
```

**Delete all users:**
```bash
python delete_all_users_v2.py
```

**Test patient data:**
```bash
python check_patient_system.py
```

**Test API endpoints:**
```bash
python test_query_with_patient.py
```

---

## System Status

| Component | Status | URL |
|-----------|--------|-----|
| Frontend | ✅ Running | http://localhost:3000 |
| Backend | ✅ Running | http://localhost:8000 |
| Database | ✅ Connected | PostgreSQL (Neon) |
| Patient Data | ✅ Loaded | 221 Synthea patients |
| Authentication | ✅ Ready | JWT tokens |
| LLM | ✅ Ready | Groq API |

---

## Next Steps

1. ✅ Go to http://localhost:3000/auth/signup
2. ✅ Create your account
3. ✅ Complete OTP verification
4. ✅ Login with your credentials
5. ✅ Access the dashboard
6. ✅ Query patient data

**Enjoy CiperCare!**
