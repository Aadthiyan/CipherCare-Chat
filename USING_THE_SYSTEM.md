# Using Cipercare - Complete Guide

## Authentication System

### Sign Up
1. Navigate to the signup page
2. Enter your credentials:
   - Username (unique)
   - Email address
   - Password (will be bcrypt hashed)
   - Full name
   - Role (Admin, Doctor, Nurse, Receptionist)
   - Department (Optional)
3. Click Sign Up
4. You'll be redirected to verify your OTP

### OTP Verification
1. A 6-digit OTP code is generated and displayed (for testing)
2. **In production**: You would receive the OTP via SMS or email
3. Enter the 6-digit code
4. If incorrect, you get up to 5 attempts
5. OTP expires after 15 minutes
6. Once verified, you can login

### Login
1. Navigate to the login page
2. Enter your username and password
3. Click Login
4. You'll be redirected to the Dashboard
5. Your session token is stored in:
   - **localStorage** (for React state)
   - **cookies** (for middleware authentication)

## Dashboard Features

### Medical Records
The Medical Records page now fetches real patient data from your database.

**Current Status**: Empty (no patients uploaded yet)

**To add patient data**:
1. Use the data upload scripts (see below)
2. Patient records will automatically appear in the Records page
3. You can search and filter by name, MRN, or condition

### Patient Upload Methods

#### Method 1: Using Synthea Data
Synthea generates realistic patient data.

```bash
# Install Synthea (if not already installed)
# Download from: https://github.com/synthetichealth/synthea

# Generate patient data
synthea -p 100 -c 50 Massachusetts

# The output will be in: output/fhir/
```

#### Method 2: Using MIMIC Data
Convert MIMIC-III clinical data to Cipercare format.

```bash
# Edit the import statement in convert_mimic_to_cipercare.py
# Point to your MIMIC CSV files

python convert_mimic_to_cipercare.py
```

#### Method 3: Using Sample Data
We provide scripts to quickly add sample patients:

```bash
# Quick add via Synthea
python quick_add_synthea_data.py

# Generate random test data
python generate_data.py

# Upload directly from Python
python upload_to_cyborgdb.py
```

## Security Features

### Authentication
- **JWT Tokens**: 30-minute expiration
- **Refresh Tokens**: 7-day expiration
- **Password Hashing**: bcrypt with 12 rounds
- **OTP Codes**: 6-digit random codes, 15-minute expiration, 5 attempts max

### Route Protection
- **Public Routes**: `/auth/login`, `/auth/signup`, `/auth/verify-otp`
- **Protected Routes**: `/dashboard/*` (requires valid JWT in cookies)
- **Middleware**: Checks token validity and redirects to login if expired

### Data Encryption
- Medical records are marked as HIPAA-compliant
- All patient data in transit uses HTTPS
- Database credentials stored as environment variables

## API Endpoints

### Authentication
```
POST /auth/signup
POST /auth/verify-otp
POST /auth/login
POST /auth/refresh
POST /auth/logout
```

### Patient Data
```
GET /api/v1/patients          # Get all patients
GET /api/v1/patients?search=<query>  # Search patients
GET /api/v1/patients/<id>     # Get specific patient
```

### Admin
```
GET /api/admin/audit-logs
GET /api/admin/sessions
```

## Troubleshooting

### "No records found" message
- This is normal if you haven't uploaded any patient data yet
- Use one of the upload methods above to add patients

### "Please log in again" error
- Your session has expired
- Login with your credentials again

### Login not working
- Verify your credentials are correct
- Check that you've completed OTP verification
- Clear cookies/cache and try again

### Backend connection errors
- Ensure the backend is running: `python run_backend.py`
- Check that PostgreSQL is accessible
- Verify DATABASE_URL environment variable

## Next Steps

1. **Upload Patient Data**: Use any of the methods above to add real patients
2. **Access Medical Records**: They'll appear automatically on the Records page
3. **Manage Users**: Create additional staff accounts with different roles
4. **Configure Settings**: Set up your organization profile and preferences

## Environment Configuration

Required environment variables:
```
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
GROQ_API_KEY=...
BREVO_API_KEY=...
CYBORG_URL=...
CYBORG_API_KEY=...
```

## Support

For issues or questions:
1. Check the logs: `backend/error.log`
2. Review API responses in browser DevTools
3. Refer to TESTING.md for test procedures
