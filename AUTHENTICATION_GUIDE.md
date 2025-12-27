# CipherCare Authentication System Overview

## Current Authentication Status

### ✅ What Exists Today

**Authentication System**: JWT-based with RBAC (Role-Based Access Control)

**Current Implementation**:
- Backend uses **OAuth2 with JWT tokens**
- Mock database with hardcoded doctor credentials
- Credentials stored in `backend/auth.py`:
  ```
  Username: attending | Password: password123
  Username: resident  | Password: password123
  ```
- Frontend dashboard is **NOT protected** - No login page yet
- Anyone can access `/dashboard` without authentication

---

## Who Is This For? 👨‍⚕️👩‍⚕️

### **TARGET USERS: DOCTORS & CLINICIANS**

This is a **healthcare provider application**, NOT a patient-facing app.

**User Types**:
- **Attending Physicians** - Full access to all patients
- **Resident Doctors** - Access only to assigned patients
- **Future: Nurses, Healthcare Administrators**

**NOT For Patients**:
- Patients should NOT have access to this system
- This is clinical decision support for medical staff only
- HIPAA compliance requires clinician-only access

---

## Current Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (Next.js)                                          │
│ - No login page                                             │
│ - Open access to /dashboard                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ POST /api/query
                       │ (No credentials passed)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ NEXT.JS API ROUTE (/api/query)                             │
│ - Hardcoded credentials: attending/password123             │
│ - Gets JWT token automatically                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ POST /token
                       │ + Username: attending
                       │ + Password: password123
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (FastAPI)                                           │
│ - Validates credentials against FAKE_USERS_DB              │
│ - Returns JWT token with roles                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Token: eyJhbGc...
                       │ Roles: ["attending", "admin"]
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND ENDPOINTS (/api/v1/query)                          │
│ - Validates Bearer token                                    │
│ - Checks user roles (require_role decorator)               │
│ - Implements patient access control                         │
└─────────────────────────────────────────────────────────────┘
```

---

## What Needs to Be Built: Login/Signup Pages

### ❌ Missing: User-Facing Authentication UI

Currently, authentication is **hardcoded in the Next.js API route**. For production:

#### 1. **Frontend Login Page** (`/app/auth/login/page.tsx`)
```
┌─────────────────────────────┐
│   CipherCare Login          │
│                             │
│  👤 Username: [____]        │
│  🔒 Password: [____]        │
│                             │
│  [ Login ] [ Sign Up ]      │
│                             │
│  Forgot password?           │
│  Need account? Contact...   │
└─────────────────────────────┘
```

**Features Needed**:
- Username/password input
- "Remember me" checkbox (optional)
- Link to password reset
- Error messages for invalid credentials
- Redirect to dashboard on success
- Session persistence

#### 2. **Frontend Signup Page** (`/app/auth/signup/page.tsx`)
```
┌─────────────────────────────┐
│   Create Clinician Account  │
│                             │
│  Full Name: [__________]    │
│  Email: [__________]        │
│  Username: [__________]     │
│  Password: [__________]     │
│  Confirm: [__________]      │
│  Role: [Attending ▼]        │
│                             │
│  [ Create Account ]         │
│  Already have account?      │
│  [ Login ]                  │
└─────────────────────────────┘
```

**Features Needed**:
- Form validation (email format, password strength)
- Role selection (Attending, Resident, Nurse, Admin)
- Hospital/Institution field
- Credential verification
- Email confirmation (optional)

---

## Backend Authentication Components

### 1. **Token Generation** (`/token` endpoint)
**Current Implementation**:
```python
# User submits: username, password
POST /token
Content-Type: application/x-www-form-urlencoded

username=attending&password=password123

# Backend returns:
{
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### 2. **User Database** (`FAKE_USERS_DB`)
**Current**:
```python
FAKE_USERS_DB = {
    "attending": {
        "username": "attending",
        "full_name": "Dr. Smith",
        "email": "smith@cipercare.com",
        "roles": ["attending", "admin"],
        "assigned_patients": ["any"]  # Can access all
    },
    "resident": {
        "username": "resident",
        "full_name": "Dr. Doe",
        "email": "doe@cipercare.com",
        "roles": ["resident"],
        "assigned_patients": ["P123", "P456"]  # Only these patients
    }
}
```

**Needs**:
- Real database (PostgreSQL table for users)
- Hashed passwords (bcrypt, not plaintext)
- User registration endpoint
- Password reset flow
- Email verification

### 3. **RBAC (Role-Based Access Control)**
**Currently Implemented**:
```python
# Role-based endpoint protection
@app.get("/api/v1/admin-only")
async def admin_endpoint(user = Depends(require_role("admin"))):
    return {"message": "Only admins can see this"}

# Patient access control
def check_patient_access(user: TokenData, patient_id: str):
    # Resident can only see assigned patients
    # Attending can see any patient (assigned_patients: ["any"])
    # Admin can see any patient
```

---

## RBAC Roles Structure

### **Available Roles**:
1. **Admin** 
   - Access: All patients, all operations
   - Can manage users, create reports
   - Example: IT Admin, Compliance Officer

2. **Attending**
   - Access: All assigned patients (usually all)
   - Full query and analysis permissions
   - Example: Consulting Physician, Department Head

3. **Resident**
   - Access: Only assigned patients
   - Limited to querying, no admin functions
   - Example: Medical Resident, Junior Doctor

4. **Nurse** (Future)
   - Access: Assigned patient groups
   - Read-only or limited query access

5. **Patient** ❌ (Should NOT have access)
   - This is clinical-use only
   - Patients access their data through separate patient portal

---

## Implementation Roadmap

### Phase 1 ✅ (Current - Done)
- [x] Backend JWT authentication
- [x] RBAC system with roles
- [x] Patient access control
- [x] Mock user database
- [x] Token validation

### Phase 2 ⏳ (Recommended Next Steps)

#### 2a. Frontend Login UI
```
Create: frontend/app/auth/
├── login/page.tsx        - Login form
├── signup/page.tsx       - Registration form
├── layout.tsx            - Auth layout wrapper
└── components/
    ├── LoginForm.tsx     - Login component
    ├── SignupForm.tsx    - Signup component
    └── ProtectedRoute.tsx - Route guard
```

**Implementation Checklist**:
- [ ] Create login page with form
- [ ] Create signup page with form
- [ ] Add form validation (client-side)
- [ ] Add error handling
- [ ] Add session/token storage (localStorage or httpOnly cookie)
- [ ] Create middleware to protect /dashboard route
- [ ] Add logout button
- [ ] Add password reset flow (optional)

#### 2b. Backend User Management
```
Database Schema:
users/
├── id (UUID)
├── username (unique)
├── email (unique)
├── password_hash (bcrypt)
├── full_name
├── role (attending, resident, nurse, admin)
├── assigned_patients (JSON array)
├── department
├── created_at
├── updated_at
├── is_active
```

**Endpoints to Create**:
- [ ] `POST /auth/signup` - Register new clinician
- [ ] `POST /auth/login` - Login (replaces /token)
- [ ] `POST /auth/logout` - Logout
- [ ] `POST /auth/refresh` - Refresh token
- [ ] `POST /auth/password-reset` - Reset password
- [ ] `GET /auth/me` - Get current user
- [ ] `PUT /auth/profile` - Update profile
- [ ] `POST /admin/users` - Admin: create user
- [ ] `DELETE /admin/users/{id}` - Admin: delete user

### Phase 3 🔄 (Security Hardening)
- [ ] Auth0 integration (external auth provider)
- [ ] Multi-factor authentication (MFA/2FA)
- [ ] Email verification for signup
- [ ] LDAP/Active Directory integration (for hospitals)
- [ ] OAuth2 with external providers
- [ ] API key authentication (for integrations)
- [ ] Rate limiting on auth endpoints
- [ ] Audit logging for auth events
- [ ] Password complexity requirements
- [ ] Session management/token revocation

---

## Quick Answer to Your Questions

### ❓ Do We Need Login/Signup Pages?

**YES** - For production use:
- ✅ **Login Page**: Required for clinicians to authenticate
- ✅ **Signup Page**: Required for hospital to onboard new clinicians (with approval)
- ❌ **Patient Signup**: Never - patients should NOT have access

### ❓ Is It Doctors or Patients?

**DOCTORS ONLY** 👨‍⚕️
- Attending Physicians
- Resident Doctors  
- Hospital Staff (Nurses, Admins)
- **NOT Patients** - Patient access requires separate secure portal

### ❓ What About Current State?

**Current State** (Hackathon MVP):
- ✅ Backend auth system built
- ✅ RBAC implemented
- ❌ Frontend has no login page
- ⚠️ Anyone can access dashboard
- ⚠️ Hardcoded credentials

**Production Ready** requires:
1. Frontend login/signup pages
2. Real user database
3. Password hashing
4. Email verification
5. Session management

---

## Testing Current Authentication

### Test with Backend directly:
```bash
# Get token
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attending&password=password123"

# Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}

# Use token to query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "P123", "query": "diabetes treatment"}'
```

### Test Frontend API route:
```bash
# Frontend automatically handles auth
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "P123", "query": "diabetes"}'

# Frontend route gets token and calls backend
```

---

## Security Considerations

### ✅ Already Implemented
- JWT token-based auth (stateless)
- RBAC with role enforcement
- Patient access control
- Bearer token validation
- Encryption of medical data (Vault Transit)

### ⚠️ Still Needed
- Password hashing (bcrypt, not plaintext)
- HTTPS only (not HTTP in production)
- HttpOnly cookies for tokens
- CORS protection (already done)
- Rate limiting on auth endpoints
- Audit logging
- Session timeout (auto-logout)
- HIPAA audit logs
- Database encryption at rest

---

## Recommendation

**Next Steps Priority**:
1. **HIGH**: Create frontend login page (add security)
2. **HIGH**: Create real user database (remove hardcoded credentials)
3. **MEDIUM**: Add password hashing
4. **MEDIUM**: Add email verification for signup
5. **LOW**: Add MFA/2FA
6. **LOW**: Add Auth0 integration

Would you like me to **create the login and signup pages** for the frontend?
