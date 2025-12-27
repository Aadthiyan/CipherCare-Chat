"""
Email Service for CipherCare using Brevo (formerly Sendinblue)
Handles email verification, password reset, and notifications
"""

import os
import logging
from typing import Optional
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Brevo API configuration
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@cipercare.com")
SENDER_NAME = os.getenv("SENDER_NAME", "CipherCare")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class EmailService:
    """Email service using Brevo API"""
    
    def __init__(self):
        if not BREVO_API_KEY:
            logger.warning("⚠️ BREVO_API_KEY not set - email features disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.headers = {
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            }
            logger.info("✓ Brevo email service initialized")
    
    def send_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        """Send email via Brevo API"""
        if not self.enabled:
            logger.warning(f"Email not sent (service disabled): {subject} to {to_email}")
            return False
        
        payload = {
            "sender": {
                "name": SENDER_NAME,
                "email": SENDER_EMAIL
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }
        
        try:
            response = requests.post(BREVO_API_URL, json=payload, headers=self.headers)
            
            if response.status_code in [200, 201]:
                logger.info(f"✓ Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_verification_email(self, email: str, full_name: str, verification_token: str) -> bool:
        """Send email verification link"""
        verification_link = f"{FRONTEND_URL}/auth/verify-email?token={verification_token}"
        
        subject = "Verify Your CipherCare Account"
        html_content = f"""
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
                    background-color: #0066cc;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #0066cc;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 CipherCare</h1>
                </div>
                <div class="content">
                    <h2>Welcome, {full_name}!</h2>
                    <p>Thank you for registering with CipherCare. Please verify your email address to activate your account.</p>
                    <p>Click the button below to verify your email:</p>
                    <center>
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #0066cc;">{verification_link}</p>
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    <p>If you didn't create this account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} CipherCare - Secure Healthcare Platform</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, full_name, subject, html_content)
    
    def send_password_reset_email(self, email: str, full_name: str, reset_token: str) -> bool:
        """Send password reset link"""
        reset_link = f"{FRONTEND_URL}/auth/reset-password?token={reset_token}"
        
        subject = "Reset Your CipherCare Password"
        html_content = f"""
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
                    background-color: #cc0000;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #cc0000;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hello, {full_name}</h2>
                    <p>We received a request to reset your CipherCare account password.</p>
                    <p>Click the button below to reset your password:</p>
                    <center>
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #cc0000;">{reset_link}</p>
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <ul>
                            <li>This link expires in 1 hour</li>
                            <li>If you didn't request this, please ignore this email</li>
                            <li>Your password won't change until you create a new one</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} CipherCare - Secure Healthcare Platform</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, full_name, subject, html_content)
    
    def send_welcome_email(self, email: str, full_name: str) -> bool:
        """Send welcome email after email verification"""
        subject = "Welcome to CipherCare!"
        html_content = f"""
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
                    background-color: #28a745;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #28a745;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Account Verified!</h1>
                </div>
                <div class="content">
                    <h2>Welcome to CipherCare, {full_name}!</h2>
                    <p>Your email has been successfully verified. You can now access all CipherCare features.</p>
                    <h3>Getting Started:</h3>
                    <ul>
                        <li>🔍 Query patient medical records securely</li>
                        <li>🤖 Get AI-powered clinical insights</li>
                        <li>🔒 All data is encrypted end-to-end</li>
                        <li>📊 Access comprehensive patient analytics</li>
                    </ul>
                    <center>
                        <a href="{FRONTEND_URL}/dashboard" class="button">Go to Dashboard</a>
                    </center>
                    <p><strong>Need Help?</strong> Check our documentation or contact support.</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} CipherCare - Secure Healthcare Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, full_name, subject, html_content)
    
    def send_login_alert(self, email: str, full_name: str, ip_address: str, timestamp: str) -> bool:
        """Send login notification for security"""
        subject = "New Login to Your CipherCare Account"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>🔔 New Login Detected</h2>
                <p>Hello {full_name},</p>
                <p>A new login to your CipherCare account was detected:</p>
                <ul>
                    <li><strong>Time:</strong> {timestamp}</li>
                    <li><strong>IP Address:</strong> {ip_address}</li>
                </ul>
                <p>If this was you, no action is needed.</p>
                <p><strong>If you don't recognize this activity:</strong></p>
                <ol>
                    <li>Reset your password immediately</li>
                    <li>Contact our security team</li>
                </ol>
                <p style="font-size: 12px; color: #666; margin-top: 20px;">
                    © {datetime.now().year} CipherCare - This is an automated security notification
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, full_name, subject, html_content)
    
    def send_otp_email(self, email: str, full_name: str, otp_code: str) -> bool:
        """Send OTP code via email for account verification"""
        subject = "Your CipherCare Account Verification Code"
        html_content = f"""
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
                    <p>© {datetime.now().year} CipherCare - Secure Healthcare Platform</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, full_name, subject, html_content)


# Global instance
email_service = EmailService()
