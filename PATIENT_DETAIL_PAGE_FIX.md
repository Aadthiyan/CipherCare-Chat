# Patient Record Detail Page - Fix Required

## Problem
The individual patient record page (`/dashboard/records/[id]/page.tsx`) is hardcoded to show mock data for only 6 patients (MRN-2301 through MRN-2306). When you click on any real patient (like PID-101), it falls back to showing John Doe's data.

## Root Cause
Line 254:
```typescript
const patient = PATIENT_DATA[id as keyof typeof PATIENT_DATA] || PATIENT_DATA['MRN-2301'];
```

This looks up the ID in a hardcoded object and defaults to John Doe if not found.

## Solution Required
The page needs to be refactored to:

1. **Fetch patient data from the API** using the patient ID from the URL
2. **Query the chatbot/database** for the patient's:
   - Demographics (from `/api/v1/patients` endpoint - already exists)
   - Vitals (from clinical records in CyborgDB)
   - Medications (from clinical records)
   - Conditions/Medical History (from clinical records)
   - Documents (if you have a documents API)

3. **Transform the data** from your Synthea format to match the UI expectations

## Quick Fix Option
Since this is a complex refactor, I recommend:

**Option 1: Disable the detail view temporarily**
- Remove the link from the records list page
- Or show a "Coming Soon" message on the detail page

**Option 2: Implement basic detail view**
- Fetch patient demographics from `/api/v1/patients/{id}`
- Show basic info only (name, age, gender, conditions)
- Add a note: "Detailed records coming soon"

## Full Implementation (Recommended)
Create a new API endpoint `/api/v1/patients/{id}/details` that returns:
```json
{
  "demographics": {...},
  "vitals": [...],
  "medications": [...],
  "conditions": [...],
  "recentVisits": [...]
}
```

This would query CyborgDB for all records belonging to that patient_id and structure them appropriately.

Would you like me to implement Option 2 (basic view) or help you build the full API endpoint?
