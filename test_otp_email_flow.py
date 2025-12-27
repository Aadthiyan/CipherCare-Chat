#!/usr/bin/env python3
"""
Test OTP registration and email sending flow
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def print_ok(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def test_signup_with_email():
    """Test user registration with email verification"""
    print_section("TEST 1: User Registration (OTP Generation & Email Sending)")
    
    signup_data = {
        "username": "test_otp_user",
        "email": "aadhiks9595@gmail.com",  # Your email
        "password": "SecurePassword123!",
        "full_name": "Test OTP User",
        "role": "resident"
    }
    
    print_info(f"Signing up: {signup_data['username']}")
    print_info(f"Email: {signup_data['email']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json=signup_data
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_ok("Registration successful!")
            print_info(f"Message: {data.get('message', 'N/A')}")
            print_info(f"Email sent: {data.get('email_sent', 'N/A')}")
            
            user_id = data.get('user', {}).get('id')
            print_ok(f"User ID: {user_id}")
            
            return user_id, data
        else:
            print_error(f"Registration failed!")
            print_error(f"Response: {response.text}")
            return None, None
    except Exception as e:
        print_error(f"Error during signup: {e}")
        return None, None

def test_verify_otp(user_id, otp_code):
    """Test OTP verification"""
    print_section("TEST 2: OTP Verification")
    
    print_info(f"Verifying OTP for user: {user_id}")
    print_info(f"OTP Code: {otp_code}")
    
    verify_data = {
        "user_id": user_id,
        "otp_code": otp_code
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/verify-otp",
            json=verify_data
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_ok("OTP verification successful!")
            print_info(f"Message: {data.get('message', 'N/A')}")
            return True
        else:
            print_error("OTP verification failed!")
            error_data = response.json()
            print_error(f"Error: {error_data.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print_error(f"Error during OTP verification: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "="*60)
    print("  CipherCare OTP Email Verification Test")
    print("="*60)
    print_info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Base URL: {BASE_URL}")
    
    # Test 1: Register user and trigger email
    print_section("STEP 1: Register New User")
    user_id, signup_response = test_signup_with_email()
    
    if not user_id:
        print_error("Registration failed, cannot proceed with verification test")
        return
    
    # Test 2: Get OTP and verify
    print_section("STEP 2: Manual OTP Verification")
    
    # For testing, we'll ask for the OTP from email
    print_info("Check your email (aadhiks9595@gmail.com) for the OTP code")
    print_info("You should have received an email with subject: 'Your CipherCare Account Verification Code'")
    
    # For automated testing, we could query the DB to get the OTP
    # But for this test, we'll simulate with a test OTP
    otp_input = input("\nEnter the OTP code from your email (or type 'skip' to skip verification): ").strip()
    
    if otp_input.lower() == 'skip':
        print_info("Skipping OTP verification test")
    else:
        if len(otp_input) == 6 and otp_input.isdigit():
            test_verify_otp(user_id, otp_input)
        else:
            print_error("Invalid OTP format. OTP should be 6 digits")
    
    # Summary
    print_section("TEST SUMMARY")
    print_ok("Signup test completed - check your email for the OTP")
    print_ok("If you received the email, the email service is working correctly!")
    
    # Troubleshooting
    print_section("TROUBLESHOOTING")
    print_info("If you didn't receive the email:")
    print("  1. Check spam/junk folder")
    print("  2. Verify BREVO_API_KEY in .env file")
    print("  3. Check backend logs for email sending errors")
    print("  4. Verify SENDER_EMAIL and FRONTEND_URL in .env")

if __name__ == "__main__":
    main()
