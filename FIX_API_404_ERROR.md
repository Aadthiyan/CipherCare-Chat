# Fix for API 404 Error - Medical Records Page

## Problem
The Medical Records page was showing a 404 error when trying to fetch patient data from the backend API.

**Error**: `Request failed with status code 404`

**Root Cause**: The frontend was using a relative URL `/api/v1/patients` without specifying the backend server URL (http://127.0.0.1:8000). This caused the browser to request `http://localhost:3000/api/v1/patients` instead of the correct backend URL.

## Solution
Updated the Medical Records page to use the properly configured axios instance from the auth context, which already has:
- Correct `baseURL` pointing to the backend
- JWT token automatically added to all requests
- Proper error handling and interceptors

## Changes Made

### 1. Frontend Environment Variable (`.env.local`)
```dotenv
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

### 2. Records Page (`frontend/app/dashboard/records/page.tsx`)

**Before**:
```tsx
import axios from 'axios';

const fetchPatients = async () => {
    const response = await axios.get('/api/v1/patients', {
        headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
    });
};
```

**After**:
```tsx
import { useAuth } from '@/lib/auth-context';

export default function RecordsPage() {
    const { axiosInstance } = useAuth();
    
    const fetchPatients = async () => {
        const response = await axiosInstance.get('/api/v1/patients');
    };
    
    useEffect(() => {
        // ... fetch logic
    }, [axiosInstance]);
}
```

## Why This Works

1. **Auth Context Provides Configured Instance**
   - The auth context creates an axios instance with `baseURL` set to `NEXT_PUBLIC_BACKEND_URL`
   - All requests automatically use the full URL: `http://127.0.0.1:8000/api/v1/patients`

2. **Authentication Handled Automatically**
   - The auth context's axios interceptor automatically adds the JWT token
   - No need to manually set `Authorization` header

3. **Proper Error Handling**
   - The auth context handles token refresh on 401 errors
   - Consistent error handling across the app

## Verification

The endpoint `/api/v1/patients` now:
- ✅ Returns HTTP 200 with patient data
- ✅ Is properly authenticated with JWT token
- ✅ Has correct base URL configuration
- ✅ Handles authorization properly

Example response:
```json
{
  "total": 0,
  "patients": [],
  "message": "No patients uploaded yet. Use the upload endpoint to add patient data."
}
```

## Next Steps

1. **To add real patient data**:
   ```bash
   python quick_add_synthea_data.py
   # or
   python generate_data.py
   ```

2. **Medical Records page will then**:
   - Automatically fetch real patient data on load
   - Display patients with search/filter capabilities
   - Replace mock data with actual database records

## How to Debug Future Issues

1. **Check API is accessible**:
   ```bash
   netstat -ano | findstr :8000  # Backend running?
   netstat -ano | findstr :3000  # Frontend running?
   ```

2. **Verify token in browser DevTools**:
   - Open DevTools (F12)
   - Go to Application → Cookies
   - Check if `access_token` cookie exists
   - Check if `localStorage` has `access_token`

3. **Check network requests**:
   - Go to DevTools → Network tab
   - Refresh page
   - Look for API requests to `/api/v1/patients`
   - Check response status and body

4. **Enable debug logging**:
   - Add `console.log` in the fetch function
   - Check browser console for error details

## Common Issues & Solutions

### Still Showing 404?
1. Frontend wasn't restarted after `.env.local` change
   - Kill: `Stop-Process -Id <PID> -Force`
   - Restart: `npm run dev`

2. Backend isn't running
   - Start: `python run_backend.py`

3. Wrong backend URL
   - Check `.env.local` has correct `NEXT_PUBLIC_BACKEND_URL`

### Still Not Showing Patient Data?
1. No patients in database yet
   - Run: `python generate_data.py` or `python quick_add_synthea_data.py`

2. Search/filter active
   - Try clearing search and filters

3. Token expired
   - Logout and login again

