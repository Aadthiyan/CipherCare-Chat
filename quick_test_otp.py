#!/usr/bin/env python3
"""
Quick test to verify OTP email sending works
This will register a user and confirm email is sent
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_registration_with_otp():
    """Test user registration"""
    print("\n" + "="*60)
    print("  Quick OTP Email Test")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate unique username and email
    timestamp = datetime.now().strftime("%H%M%S")
    username = f"quicktest_{timestamp}"
    
    signup_data = {
        "username": username,
        "email": "aadhiks9595@gmail.com",  # Use your test email
        "password": "TestPassword123!",
        "full_name": "Quick Test User",
        "role": "resident"
    }
    
    print(f"\n📝 Registering user: {username}")
    print(f"📧 Email: {signup_data['email']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json=signup_data,
            timeout=10
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Registration successful!")
            print(f"   Message: {data.get('message')}")
            print(f"   Email Sent: {'✅ YES' if data.get('email_sent') else '❌ NO'}")
            print(f"   User ID: {data.get('user', {}).get('id')}")
            print(f"   Username: {data.get('user', {}).get('username')}")
            
            # Show next steps
            print("\n" + "="*60)
            print("  NEXT STEPS")
            print("="*60)
            if data.get('email_sent'):
                print("✅ Email has been sent!")
                print("   1. Check your inbox for the OTP email")
                print("   2. Email subject: 'Your CipherCare Account Verification Code'")
                print("   3. The OTP code will expire in 15 minutes")
                print("   4. Enter the OTP on the verification page to complete signup")
            else:
                print("⚠️  Email sending may have failed")
                print("   Check backend logs for more details")
            
            return True
        else:
            print(f"\n❌ Registration failed!")
            error = response.json()
            print(f"   Error: {error.get('detail', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_registration_with_otp()
    exit(0 if success else 1)
