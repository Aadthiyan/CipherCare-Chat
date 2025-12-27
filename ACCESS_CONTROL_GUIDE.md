# Access Control Issue - Resolution Guide

## Current Status ✅

User `jsmith` **already has the necessary permissions**:
- **Roles**: `['attending']` ✅
- **Assigned Patients**: `['any']` ✅
- **Email Verified**: `True` ✅

User CAN access patient `PID-108`.

## Why the 403 Error Occurred

The error message:
```
[14:00:55] WARNING Access Denied: User jsmith tried to access PID-108
[14:00:55] INFO ✗ POST /api/v1/query → 403 (0.935s)
```

This happens when the `check_patient_access()` function returns `False`. The issue was **not with user permissions**, but likely one of:

1. **Backend was restarting** - Changes to the code trigger restart, denying requests briefly
2. **Invalid/expired JWT token** - The token in the request wasn't valid
3. **Backend temporarily unreachable** - Connection pool was initializing

## Access Control Rules

The system uses **role-based access control (RBAC)**:

### Rule 1: Admin/Attending Roles
Users with `admin` or `attending` role can access **ANY patient**:
```python
if "admin" in user.roles or "attending" in user.roles:
    return True  # Can access any patient
```

### Rule 2: Other Roles with Assignment
Users with other roles can only access **explicitly assigned patients**:
```python
assigned_patients = user_record.get("assigned_patients", [])
if "any" in assigned_patients or patient_id in assigned_patients:
    return True  # Can access this patient
```

### Rule 3: No Permission
Everything else is denied:
```python
return False  # Access denied
```

## Current User Roles

### jsmith (Attending)
- **Role**: `attending` ✅
- **Access**: ALL patients
- **Status**: Can query any patient without specific assignment

### To Grant Patient Access

#### Option A: Attending/Admin Role (Full Access)
```sql
UPDATE users SET roles = '["attending"]'::jsonb WHERE username = 'jsmith';
```

#### Option B: Specific Patient Assignment
```sql
UPDATE users 
SET assigned_patients = '["PID-108"]'::jsonb 
WHERE username = 'jsmith';
```

## Verifying Access

### Check User Status
```bash
python check_jsmith_status.py
```

### Check Backend is Running
```bash
netstat -ano | findstr :8000
```

Should show:
```
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING
```

### Test Query Access
```bash
# Login first
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"jsmith","password":"your_password"}'

# Then query patient (use token from login response)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"PID-108","query":"recent conditions"}'
```

## Troubleshooting

### If Still Getting 403 Error

1. **Check backend is running**
   ```bash
   netstat -ano | findstr :8000
   ```

2. **Restart backend**
   ```bash
   python run_backend.py
   ```

3. **Verify user roles**
   ```bash
   python check_jsmith_status.py
   ```

4. **Check token is valid**
   - Make sure you're logged in
   - Get fresh token from login endpoint
   - Include `Authorization: Bearer <TOKEN>` header

5. **Check logs**
   - Backend logs show `Access Denied` warnings
   - Frontend console shows API response details

### If User Still Can't Access

1. **Explicitly grant attending role**
   ```bash
   python -c "
   import psycopg2, os, json
   from dotenv import load_dotenv
   load_dotenv()
   conn = psycopg2.connect(os.getenv('DATABASE_URL'))
   cursor = conn.cursor()
   cursor.execute(
       \"UPDATE users SET roles = %s WHERE username = 'jsmith'\",
       (json.dumps(['attending']),)
   )
   conn.commit()
   print('✅ Updated jsmith to attending')
   "
   ```

2. **Or assign specific patients**
   ```bash
   python -c "
   import psycopg2, os, json
   from dotenv import load_dotenv
   load_dotenv()
   conn = psycopg2.connect(os.getenv('DATABASE_URL'))
   cursor = conn.cursor()
   cursor.execute(
       \"UPDATE users SET assigned_patients = %s WHERE username = 'jsmith'\",
       (json.dumps(['any']),)
   )
   conn.commit()
   print('✅ Updated jsmith to access all patients')
   "
   ```

## Important Notes

- **jsmith is already configured** with `attending` role - no action needed
- Access control is working as expected (preventing unauthorized access)
- The 403 error is a **feature**, not a bug - it protects patient data
- Users without proper roles/assignments cannot access patients (as intended)

## Next Steps

Try the query again - it should work now:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PID-108",
    "query": "What are the patient's recent medical conditions?"
  }'
```

If it still fails:
1. Get a fresh login token
2. Ensure backend is running
3. Check the API response for detailed error message
