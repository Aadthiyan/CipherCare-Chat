#!/usr/bin/env python3
"""
Direct test of the query endpoint without relying on web requests
"""
import sys
import os
import asyncio
import json
import jwt

# Add project root to path
sys.path.insert(0, '/Users/AADHITHAN/Downloads/Cipercare')

from backend.models import PatientSearchRequest, TokenData
from backend.auth_enhanced import create_access_token, get_user

async def main():
    # Create a test token for attending user
    print("Creating test token...")
    user_data = {"sub": "attending", "roles": ["attending", "admin"], "type": "access"}
    token = create_access_token(user_data)
    print(f"✓ Token created: {token[:50]}...")
    
    # Verify token
    print("\nVerifying token...")
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hackathon_secret_key_change_me_in_production")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"✓ Token verified: {json.dumps(payload, indent=2)}")
    except Exception as e:
        print(f"✗ Token verification failed: {e}")
        return
    
    # Check user exists
    print("\nChecking user...")
    user = get_user("attending")
    if user:
        print(f"✓ User found: {user['full_name']}")
    else:
        print("✗ User not found")
        return
    
    # Import and test the query endpoint directly
    print("\nTesting query endpoint directly...")
    try:
        from backend.main import query_patient_data, app
        from backend.models import PatientSearchRequest
        from fastapi import Request
        from unittest.mock import MagicMock
        
        # Create a mock request
        mock_request = MagicMock(spec=Request)
        
        # Create query request
        query_req = PatientSearchRequest(
            patient_id="P123",
            question="What are the active conditions?",
            retrieve_k=3,
            temperature=0.1
        )
        
        # Create mock TokenData
        current_user = TokenData(
            username="attending",
            email="attending@cipercare.com",
            roles=["attending", "admin"],
            full_name="Dr. Smith"
        )
        
        # Call endpoint directly (without HTTP layer)
        print("Calling endpoint...")
        result = await query_patient_data(mock_request, query_req, current_user)
        print(f"\n✓ Query succeeded!")
        print(f"Answer: {result.answer[:200]}...")
        print(f"Confidence: {result.confidence}")
        
    except Exception as e:
        print(f"✗ Endpoint test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
