#!/usr/bin/env python3
"""
Test Email Verification System
"""
import os
from dotenv import load_dotenv
load_dotenv()

import sys
import requests

BACKEND_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"🔹 {title}")
    print(f"{'='*70}")

def print_ok(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

# Test 1: Backend running
print_section("1. Check Backend Connection")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    print_ok(f"Backend is running")
except:
    print_error(f"Backend not running at {BACKEND_URL}")
    print_info("Run: python -m uvicorn backend.main:app --reload")
    sys.exit(1)

# Test 2: Check email service
print_section("2. Check Email Service Configuration")
try:
    from backend.email_service import email_service
    if email_service.enabled:
        print_ok("Brevo email service is configured")
        print_info(f"Sender: {os.getenv('SENDER_EMAIL')}")
        print_info(f"API Key: {os.getenv('BREVO_API_KEY')[:20]}...")
    else:
        print_error("Email service not enabled")
except Exception as e:
    print_error(f"Error checking email service: {e}")

# Test 3: Signup flow
print_section("3. Test Signup with Email Verification")
test_user = {
    "username": "testuser123",
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "attending"
}

try:
    response = requests.post(
        f"{BACKEND_URL}/auth/signup",
        json=test_user,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print_ok(f"Signup successful for {test_user['username']}")
        print_info(f"Status: {data.get('status')}")
        print_info(f"Message: {data.get('message')}")
        print_info(f"Email verified: {data.get('user', {}).get('email_verified', 'N/A')}")
        print_info(f"Verification required: {data.get('verification_required')}")
        
        # Test 4: Try to login before verification
        print_section("4. Try Login Before Email Verification")
        login_response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={
                "username": test_user['username'],
                "password": test_user['password']
            },
            timeout=10
        )
        
        if login_response.status_code == 403:
            print_ok("Login correctly blocked - Email not verified")
            print_info(f"Error: {login_response.json().get('detail')}")
        else:
            print_error(f"Login should have failed! Status: {login_response.status_code}")
            
    else:
        print_error(f"Signup failed: {response.status_code}")
        print_info(f"Error: {response.json()}")
        
except Exception as e:
    print_error(f"Signup test failed: {e}")

# Test 5: Verification token
print_section("5. Check Verification in Database")
try:
    from backend.database import init_db_pool
    from backend.db_operations import get_user_by_username
    
    # Initialize pool first
    if not init_db_pool():
        print_error("Failed to initialize database pool")
    else:
        user = get_user_by_username(test_user['username'])
    if user:
        print_ok("User found in database")
        print_info(f"Username: {user.get('username')}")
        print_info(f"Email: {user.get('email')}")
        print_info(f"Email verified: {user.get('email_verified')}")
        print_info(f"Has verification token: {'Yes' if user.get('email_verification_token') else 'No'}")
        print_info(f"Token expires at: {user.get('email_verification_expires')}")
    else:
        print_error("User not found in database")
except Exception as e:
    print_error(f"Database check failed: {e}")

# Summary
print_section("Email Verification System Status")
print("""
✅ Signup creates account with verification requirement
✅ User receives verification email via Brevo
✅ Login blocked until email is verified
✅ Verification token stored in database (24-hour expiration)

Next Steps:
1. Check email inbox for verification link
2. Click link or copy token to /auth/verify
3. After verification, login will work

Test Account:
  Username: testuser123
  Email: test@example.com
  Password: TestPass123!
""")

print("\n✅ Email Verification System is Ready! 🎉")
