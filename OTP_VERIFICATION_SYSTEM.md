# OTP-Based Email Verification System

## Overview
The system now uses **One-Time Password (OTP)** codes instead of email verification links. This eliminates dependency on email delivery and provides a faster, more reliable verification process.

## How It Works

### 1. User Signup
- User fills out signup form with credentials
- Backend validates input and creates user account
- **6-digit OTP code is generated and stored** in the database
- OTP expires in **15 minutes**
- User is redirected to OTP verification page with OTP displayed (for testing)

### 2. OTP Verification
- User enters the 6-digit OTP code
- Code is validated against stored OTP
- **Maximum 5 attempts** allowed
- On successful verification:
  - Email is marked as verified
  - OTP is cleared from database
  - User can now login

### 3. Login After Verification
- User logs in with username/password
- System checks if `email_verified` is `true`
- Access token is issued for authenticated requests

## Database Schema

### OTP Columns Added to Users Table
```sql
otp_code VARCHAR(6)              -- Current OTP code
otp_expires TIMESTAMP            -- When OTP expires
otp_attempts INTEGER DEFAULT 0   -- Number of failed attempts
```

## API Endpoints

### Sign Up
**POST** `/auth/signup`

Request:
```json
{
  "username": "johnsmith",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Smith",
  "role": "resident",
  "department": "Cardiology"
}
```

Response:
```json
{
  "status": "success",
  "message": "Account created! Please enter the OTP code to verify.",
  "otp_code": "820651",
  "user": {
    "id": "uuid...",
    "username": "johnsmith",
    "email": "john@example.com",
    "full_name": "John Smith",
    "roles": ["resident"],
    "email_verified": false
  },
  "verification_required": true
}
```

### Verify OTP
**POST** `/auth/verify-otp`

Request:
```json
{
  "user_id": "uuid...",
  "otp_code": "820651"
}
```

Response:
```json
{
  "status": "success",
  "message": "Account verified successfully! You can now login.",
  "user_id": "uuid..."
}
```

## Flow Diagram

```
1. User Signs Up
   ↓
2. Account Created + OTP Generated
   ↓
3. User Shown OTP (or receives via email in production)
   ↓
4. User Enters OTP
   ↓
5. OTP Verified
   ↓
6. Email Marked as Verified
   ↓
7. User Can Login
```

## Testing

### Manual Testing
1. Navigate to `/auth/signup`
2. Fill in form and submit
3. OTP code will be displayed on screen
4. Copy and paste OTP into verification form
5. Click verify
6. You'll be redirected to login page
7. Login with your credentials

### Automated Testing
```bash
python test_otp_flow.py
```

## Error Handling

### Invalid OTP
- **Error:** "Invalid or expired OTP code"
- **Attempts:** Limited to 5
- **Action:** Clear OTP input and ask user to try again

### Expired OTP
- **Expiration:** 15 minutes
- **Action:** User must sign up again to get new OTP

### Too Many Attempts
- **Limit:** 5 failed attempts
- **Action:** Prevent further verification attempts

## Configuration

### OTP Settings (in `backend/db_operations.py`)
```python
store_otp(user_id, otp_code, expires_in_minutes=15)  # Expiration time
verify_otp(user_id, otp_code)                         # Verification
```

### Frontend Settings (in `frontend/app/auth/verify-otp/page.tsx`)
```javascript
const timeLeft = useState(900);  // 15 minutes in seconds
```

## Production Deployment

In production, OTP codes should NOT be displayed on screen. Instead:

1. **Send via Email:**
   ```python
   email_service.send_otp(email, otp_code)
   ```

2. **Send via SMS:**
   ```python
   sms_service.send_otp(phone, otp_code)
   ```

3. **Update Frontend:** Remove the OTP display from verification page

## Security Features

✅ **6-digit OTP** - Random secure code  
✅ **15-minute expiration** - Time-limited access  
✅ **5-attempt limit** - Brute-force protection  
✅ **Database storage** - Secure OTP persistence  
✅ **Clear on verification** - OTP deleted after use  

## Migration from Email Verification

### Previous System (Email Links)
- Sent verification link to email
- User clicks link to verify
- Issue: Email delivery unreliable

### New System (OTP Codes)
- Generate 6-digit code
- Display or send via email/SMS
- User enters code to verify
- Benefit: Instant, reliable, no email dependency

## Future Enhancements

- [ ] Send OTP via SMS using Twilio
- [ ] Send OTP via email with HTML template
- [ ] Resend OTP functionality
- [ ] Remember verified devices
- [ ] 2FA setup during verification
