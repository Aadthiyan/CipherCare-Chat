# 🚀 Fresh Start Guide - CipherCare Authentication

## Current Situation
Your system has mock users (`attending` and `resident`) that were created for testing. You want to remove them and start fresh with real users.

---

## Step-by-Step Guide

### Step 1: View Current Users

```powershell
# See what users currently exist
python clean_database.py --list
```

This will show all users in the database.

---

### Step 2: Clean the Database

```powershell
# Remove ALL users and start fresh
python clean_database.py
```

**What this does:**
- ✅ Deletes all users
- ✅ Deletes all audit logs
- ✅ Deletes all refresh tokens
- ✅ Deletes all sessions
- ✅ Clears password history
- ✅ Resets database sequences

**Warning:** This is permanent! Type `YES` to confirm.

---

### Step 3: Start Backend Server

```powershell
# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1

# Start backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Keep this terminal open.

---

### Step 4: Start Frontend (New Terminal)

```powershell
cd frontend
npm run dev
```

Keep this terminal open.

---

### Step 5: Register Your First User

1. **Open browser:** http://localhost:3000/auth/signup

2. **Fill registration form:**
   - Full Name: `Dr. John Smith`
   - Username: `jsmith` (or your choice)
   - Email: `your.real.email@example.com` (use real email!)
   - Password: `SecurePassword123!` (minimum 8 chars, strong)
   - Role: `admin` or `attending` (for full access)
   - Department: `Administration` (optional)

3. **Submit:** Click "Create Account"

4. **Check email:** Look for verification email from CipherCare
   - Subject: "Verify Your CipherCare Account"
   - Click the verification link

5. **Login:** http://localhost:3000/auth/login
   - Use your username and password

---

## Understanding User Roles

### Admin
- **Access:** Everything
- **Permissions:** 
  - All patient records
  - User management
  - System configuration
- **Use for:** System administrators, IT staff

### Attending Physician
- **Access:** All patients
- **Permissions:**
  - Query all patient records
  - Full clinical access
  - Cannot manage other users
- **Use for:** Senior doctors, department heads

### Resident
- **Access:** Only assigned patients
- **Permissions:**
  - Query only specific patients (P123, P456, etc.)
  - Limited clinical access
- **Use for:** Junior doctors, medical residents

### Nurse (Future)
- **Access:** Assigned patient groups
- **Permissions:**
  - Read-only access
  - Limited queries
- **Use for:** Nursing staff

---

## Creating Additional Users

### Option 1: Via Signup Page (Self-Registration)

Users can register themselves at `/auth/signup` but:
- ⚠️ They must verify email before access
- ⚠️ They start with default role (resident)
- ⚠️ Admin can upgrade their role later

### Option 2: Via Backend API (Admin Only)

As an admin, you can create users via API:

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "username": "drsmith",
    "email": "smith@hospital.com",
    "password": "SecurePass123!",
    "full_name": "Dr. Jane Smith",
    "role": "attending",
    "department": "Cardiology"
  }'
```

### Option 3: Direct Database Insert (Advanced)

Only if you need to bypass email verification:

```python
from backend.db_operations import create_user_db
import bcrypt

password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()

create_user_db(
    username="emergency_admin",
    email="admin@hospital.com",
    password_hash=password_hash,
    full_name="Emergency Admin",
    roles=["admin"],
    assigned_patients=["any"],
    department="IT"
)
```

---

## Workflow Examples

### Scenario 1: Hospital IT Administrator Setup

1. **Clean database:** `python clean_database.py`
2. **Create first admin account** via signup
3. **Verify email** from Brevo
4. **Login as admin**
5. **Configure system settings**
6. **Add other users** as needed

### Scenario 2: Multiple Doctor Setup

1. **Admin creates accounts** for doctors
2. **Doctors receive invitation emails**
3. **Doctors verify emails**
4. **Admin assigns patient access:**
   - Attendings: all patients
   - Residents: specific patients

### Scenario 3: Department-Based Access

1. **Create department groups** (e.g., Cardiology, Surgery)
2. **Assign patients to departments**
3. **Users in department** get access to department patients
4. **Attendings** can cross-department access

---

## Managing Users After Creation

### Update User Role

```sql
-- Via database (as admin)
UPDATE users 
SET roles = '["admin", "attending"]'::jsonb
WHERE username = 'jsmith';
```

### Assign Patients to Resident

```sql
-- Give resident access to specific patients
UPDATE users 
SET assigned_patients = '["P123", "P456", "P789"]'::jsonb
WHERE username = 'resident_doc';
```

### Deactivate User

```sql
-- Disable user without deleting
UPDATE users 
SET is_active = false
WHERE username = 'inactive_user';
```

### Reset Failed Login Attempts

```sql
-- Unlock locked account
UPDATE users 
SET failed_login_attempts = 0,
    locked_until = NULL
WHERE username = 'locked_user';
```

---

## Email Verification Setup

### If Email Not Sending

1. **Check Brevo API key** in `.env`:
   ```
   BREVO_API_KEY=xkeysib-your_key_here
   ```

2. **Test email service:**
   ```powershell
   python -c "from backend.email_service import email_service; print('✅ OK' if email_service.enabled else '❌ Disabled')"
   ```

3. **Check Brevo dashboard:**
   - https://app.brevo.com/statistics/email
   - View sent emails and delivery status

### Manual Email Verification (Development Only)

If you can't receive emails:

```sql
-- Manually verify user (DEVELOPMENT ONLY!)
UPDATE users 
SET email_verified = true
WHERE username = 'your_username';
```

---

## Security Best Practices

### For Your First Admin Account

✅ **DO:**
- Use strong password (12+ chars, mixed case, numbers, symbols)
- Use real email you can access
- Store credentials in password manager
- Enable MFA when available
- Change password after first login

❌ **DON'T:**
- Use simple passwords like "admin123"
- Share admin credentials
- Use personal email for production
- Leave default passwords
- Skip email verification

### For Patient Data Access

✅ **DO:**
- Assign minimal required patient access
- Review access logs regularly
- Remove access when no longer needed
- Audit who accessed what data

❌ **DON'T:**
- Give everyone admin access
- Use "any" patients for residents
- Share login credentials
- Disable audit logging

---

## Monitoring Your System

### View Recent Logins

```sql
SELECT username, event_type, ip_address, timestamp
FROM audit_logs
WHERE event_type = 'login'
ORDER BY timestamp DESC
LIMIT 10;
```

### Check Active Sessions

```sql
SELECT u.username, s.ip_address, s.last_activity
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = true;
```

### Failed Login Attempts

```sql
SELECT username, failed_login_attempts, locked_until
FROM users
WHERE failed_login_attempts > 0;
```

---

## Troubleshooting

### "Database connection failed"

```powershell
# Test database connection
python -c "from backend.database import init_db_pool; print('✅ OK' if init_db_pool() else '❌ Failed')"
```

### "Table does not exist"

```powershell
# Run database setup
python setup_auth.py
```

### "Email verification not working"

1. Check `.env` has `BREVO_API_KEY`
2. Check Brevo dashboard for errors
3. Look in spam folder
4. Manually verify (see above)

### "Cannot login after signup"

- Did you verify email?
- Is account active?
- Check for account lockout
- View audit logs for errors

---

## Quick Commands Reference

```powershell
# View current users
python clean_database.py --list

# Clean database (with confirmation)
python clean_database.py

# Clean database (no confirmation)
python clean_database.py --force

# Setup database from scratch
python setup_auth.py

# Start backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend
cd frontend && npm run dev

# Test email service
python -c "from backend.email_service import email_service; print(email_service.enabled)"

# Test database
python -c "from backend.database import init_db_pool; init_db_pool()"
```

---

## Next Steps After Fresh Start

1. ✅ Clean database
2. ✅ Register first admin user
3. ✅ Verify email
4. ✅ Login successfully
5. ⬜ Add patient data (if needed)
6. ⬜ Create additional users
7. ⬜ Configure patient access
8. ⬜ Test queries
9. ⬜ Review security settings
10. ⬜ Set up backups

---

## Production Deployment Checklist

Before going live:

- [ ] Change all default passwords
- [ ] Use production database
- [ ] Enable HTTPS/TLS
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure real email domain
- [ ] Set up automated backups
- [ ] Enable monitoring/alerts
- [ ] Review audit logs
- [ ] Test disaster recovery
- [ ] Complete HIPAA compliance
- [ ] Load test authentication
- [ ] Document admin procedures

---

## Support

**Need help?**
- Check logs: `backend.log`
- View audit logs in database
- Test with provided commands
- Review error messages carefully

**Common Issues:**
- Port 8000 in use: Stop other backend
- Port 3000 in use: Stop other frontend
- Database errors: Check DATABASE_URL in .env
- Email errors: Check BREVO_API_KEY

---

## Summary

You're now starting with a **completely clean system**. Here's the workflow:

1. **Clean:** Remove all mock users
2. **Register:** Create your first real admin account
3. **Verify:** Click email verification link
4. **Login:** Access the system
5. **Build:** Add users and patients as needed

**Your system is now production-ready!** 🚀
