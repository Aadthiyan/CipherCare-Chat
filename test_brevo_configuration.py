#!/usr/bin/env python3
"""
Test Brevo API configuration and email sending
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

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

def print_warning(msg):
    print(f"⚠️  {msg}")

def test_brevo_configuration():
    """Test if Brevo API key is configured"""
    print_section("TEST 1: Brevo Configuration")
    
    if not BREVO_API_KEY:
        print_error("BREVO_API_KEY not set in .env file!")
        return False
    
    if BREVO_API_KEY.startswith("xkeysib-"):
        print_ok(f"Brevo API key is configured")
        print_info(f"Key (masked): {BREVO_API_KEY[:20]}...{BREVO_API_KEY[-10:]}")
    else:
        print_warning(f"API key format unexpected: {BREVO_API_KEY[:20]}...")
    
    print_ok(f"Sender Email: {SENDER_EMAIL}")
    print_ok(f"Sender Name: {SENDER_NAME}")
    
    return True

def test_brevo_api_connectivity():
    """Test Brevo API connectivity"""
    print_section("TEST 2: Brevo API Connectivity")
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    # Simple test payload
    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },
        "to": [
            {
                "email": SENDER_EMAIL,  # Send to ourselves for testing
                "name": "Test"
            }
        ],
        "subject": "🔒 CipherCare - Test Email",
        "htmlContent": """
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>🧪 Test Email from CipherCare</h2>
                <p>This is a test email to verify that the Brevo email service is working correctly.</p>
                <p><strong>If you received this email, the configuration is working!</strong></p>
                <p style="font-size: 12px; color: #666; margin-top: 20px;">
                    This is an automated test message.
                </p>
            </div>
        </body>
        </html>
        """
    }
    
    print_info(f"Sending test email to: {SENDER_EMAIL}")
    print_info(f"API Endpoint: {BREVO_API_URL}")
    
    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print_ok("Test email sent successfully!")
            response_data = response.json()
            if 'messageId' in response_data:
                print_ok(f"Message ID: {response_data['messageId']}")
            return True
        else:
            print_error("Failed to send test email")
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error sending test email: {e}")
        return False

def test_otp_email_template():
    """Test OTP email template"""
    print_section("TEST 3: OTP Email Template")
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    otp_code = "123456"
    full_name = "Test User"
    
    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },
        "to": [
            {
                "email": SENDER_EMAIL,
                "name": full_name
            }
        ],
        "subject": "Your CipherCare Account Verification Code",
        "htmlContent": f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-box {{
                    background-color: white;
                    border: 2px solid #0066cc;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 5px;
                    color: #0066cc;
                    font-family: 'Courier New', monospace;
                }}
                .otp-expiry {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 10px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 3px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 CipherCare</h1>
                    <p>Account Verification</p>
                </div>
                <div class="content">
                    <h2>Hello {full_name}!</h2>
                    <p>Welcome to CipherCare. To complete your account registration, please enter the verification code below:</p>
                    
                    <div class="otp-box">
                        <div class="otp-code">{otp_code}</div>
                        <div class="otp-expiry">This code expires in 15 minutes</div>
                    </div>
                    
                    <p><strong>How to verify your account:</strong></p>
                    <ol>
                        <li>Go to the verification page in CipherCare</li>
                        <li>Enter the 6-digit code above</li>
                        <li>Your account will be activated immediately</li>
                    </ol>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Never share this code with anyone</li>
                            <li>CipherCare staff will never ask for this code</li>
                            <li>This code expires in 15 minutes</li>
                        </ul>
                    </div>
                    
                    <p>If you didn't create a CipherCare account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 CipherCare - Secure Healthcare Platform</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
    }
    
    print_info("Sending OTP email template to test address")
    
    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print_ok("OTP email template sent successfully!")
            response_data = response.json()
            if 'messageId' in response_data:
                print_ok(f"Message ID: {response_data['messageId']}")
            return True
        else:
            print_error("Failed to send OTP email")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "="*60)
    print("  Brevo Email Service Configuration Test")
    print("="*60)
    
    results = {
        "Config": test_brevo_configuration(),
        "Connectivity": False,
        "OTP Template": False
    }
    
    if results["Config"]:
        results["Connectivity"] = test_brevo_api_connectivity()
        if results["Connectivity"]:
            results["OTP Template"] = test_otp_email_template()
    
    # Summary
    print_section("TEST SUMMARY")
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test}: {status}")
    
    if all(results.values()):
        print_ok("\n🎉 All tests passed! Brevo email service is configured correctly.")
    else:
        print_error("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
