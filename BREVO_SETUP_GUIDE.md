# 📧 Brevo Email Setup Guide for CipherCare

## What is Brevo?

Brevo (formerly Sendinblue) is a trusted email service provider that CipherCare uses for:
- ✉️ Email verification when users sign up
- 🔑 Password reset links
- 👋 Welcome emails
- 🔔 Security alerts

## 🆓 Free Tier Benefits

**Brevo Free Plan Includes:**
- ✅ 300 emails per day
- ✅ Unlimited contacts
- ✅ Professional email templates
- ✅ Delivery tracking
- ✅ Full API access
- ✅ No credit card required

Perfect for development and small-scale deployments!

---

## 🚀 Step-by-Step Setup (5 minutes)

### Step 1: Create Brevo Account

1. Go to: **https://app.brevo.com/account/register**
2. Sign up with your email
3. Verify your email address
4. Complete the basic profile setup

### Step 2: Get Your API Key

1. Login to Brevo dashboard
2. Click your profile (top right) → **SMTP & API**
3. OR go directly to: **https://app.brevo.com/settings/keys/api**
4. Click **"Create a new API Key"**
5. Give it a name: `CipherCare Development`
6. Copy the API key (starts with `xkeysib-`)

**IMPORTANT:** Copy it now - you can't see it again!

### Step 3: Add to CipherCare

1. Open your `.env` file:
   ```
   c:\Users\AADHITHAN\Downloads\Cipercare\.env
   ```

2. Find the line:
   ```
   BREVO_API_KEY=your_brevo_api_key_here
   ```

3. Replace with your actual key:
   ```
   BREVO_API_KEY=xkeysib-abc123...your_key
   ```

4. Save the file

### Step 4: Configure Sender Email (Optional but Recommended)

1. In Brevo dashboard → **Senders & IP**
2. Add sender email: `noreply@yourdomain.com`
3. Verify domain (or use Brevo's default for testing)

4. Update `.env`:
   ```
   SENDER_EMAIL=noreply@yourdomain.com
   SENDER_NAME=CipherCare
   ```

### Step 5: Test Email Service

```powershell
# Test from Python
python -c "from backend.email_service import email_service; print('✅ Enabled' if email_service.enabled else '❌ Disabled')"
```

You should see: `✅ Enabled`

---

## 📨 Email Templates Included

### 1. Email Verification
Sent when user signs up:
```
Subject: Verify Your CipherCare Account
Content: Welcome message + verification link
Expires: 24 hours
```

### 2. Password Reset
Sent when user requests password reset:
```
Subject: Reset Your CipherCare Password  
Content: Security notice + reset link
Expires: 1 hour
```

### 3. Welcome Email
Sent after email verification:
```
Subject: Welcome to CipherCare!
Content: Getting started guide
```

### 4. Login Alert (Optional)
Sent on login from new device:
```
Subject: New Login to Your Account
Content: Login details + security tips
```

All emails are **responsive HTML** and look professional!

---

## 🧪 Testing Emails

### Test Verification Email

```powershell
# In Python
from backend.email_service import email_service

email_service.send_verification_email(
    email="your.email@example.com",
    full_name="Test Doctor",
    verification_token="test123"
)
```

### Test via Signup

1. Go to: http://localhost:3000/auth/signup
2. Fill form with YOUR real email
3. Submit
4. Check your inbox (and spam folder)
5. Click verification link

---

## 📊 Monitor Email Delivery

### Brevo Dashboard

1. Go to: **https://app.brevo.com/statistics/email**
2. View:
   - Emails sent today
   - Delivery rate
   - Opens and clicks
   - Bounce rate
   - Failed emails

### Check Specific Email

1. Go to: **Email → Statistics**
2. Filter by recipient email
3. See delivery status

---

## 🔍 Troubleshooting

### Problem: "BREVO_API_KEY not set - email features disabled"

**Solution:**
1. Check `.env` file has `BREVO_API_KEY=xkeysib-...`
2. Restart backend server
3. Verify no extra spaces or quotes

```powershell
# Verify environment variable
python -c "import os; print(os.getenv('BREVO_API_KEY')[:20] if os.getenv('BREVO_API_KEY') else 'NOT SET')"
```

### Problem: "Failed to send email: 401 Unauthorized"

**Solution:**
- API key is invalid or expired
- Regenerate API key in Brevo dashboard
- Update `.env` file
- Restart backend

### Problem: "Failed to send email: 403 Forbidden"

**Solution:**
- Daily limit reached (300 emails on free plan)
- Wait until tomorrow
- Upgrade plan if needed

### Problem: "Email not received"

**Check:**
1. ✅ Spam/junk folder
2. ✅ Email address is correct
3. ✅ Brevo dashboard shows "Delivered"
4. ✅ Domain not blacklisted
5. ✅ Mailbox not full

### Problem: "Emails marked as spam"

**Solutions:**
- Verify sender domain in Brevo
- Set up SPF and DKIM records
- Use a verified domain email
- Don't send from @gmail.com in production

---

## 🎛️ Configuration Options

### Customize Email Appearance

Edit `backend/email_service.py`:

```python
# Change colors
"background-color": "#0066cc",  # Header color
"color": "white",                # Text color

# Change button style
"background-color": "#28a745",   # Green button
"padding": "15px 40px",          # Bigger button
```

### Change Email Content

```python
# In EmailService class
def send_verification_email(self, ...):
    # Customize HTML content
    html_content = f"""
    <h2>Welcome {full_name}!</h2>
    <p>Your custom message here...</p>
    """
```

### Add Custom Email Types

```python
def send_custom_email(self, email, subject, content):
    return self.send_email(
        to_email=email,
        to_name="User",
        subject=subject,
        html_content=content
    )
```

---

## 📈 Production Recommendations

### For Production Deployment:

1. **Verify Domain**
   - Add SPF record: `v=spf1 include:spf.brevo.com ~all`
   - Add DKIM records (provided by Brevo)
   - Verify in Brevo dashboard

2. **Use Professional Email**
   - ❌ NOT: `noreply@gmail.com`
   - ✅ YES: `noreply@yourhospital.com`

3. **Monitor Deliverability**
   - Check bounce rate (keep < 2%)
   - Monitor spam complaints
   - Maintain sender reputation

4. **Upgrade if Needed**
   ```
   Free:     300 emails/day
   Lite:     $25/month = 10,000 emails/month
   Business: $65/month = 20,000 emails/month
   ```

5. **Set Up Webhooks**
   - Get real-time delivery notifications
   - Track opens and clicks
   - Handle bounces automatically

---

## 🔐 Security Best Practices

### Protect Your API Key

1. **Never commit to Git**
   ```bash
   # .gitignore should include:
   .env
   *.env
   ```

2. **Use environment variables only**
   ```python
   # ✅ GOOD
   BREVO_API_KEY = os.getenv("BREVO_API_KEY")
   
   # ❌ BAD
   BREVO_API_KEY = "xkeysib-abc123..."
   ```

3. **Rotate keys regularly**
   - Every 90 days in production
   - Immediately if compromised

4. **Restrict API key permissions**
   - Brevo allows scoping keys
   - Only enable "Send emails" permission

---

## 📝 Email Compliance

### HIPAA Considerations

⚠️ **Do NOT send PHI (Protected Health Information) in emails!**

**Safe to send:**
- ✅ Verification links
- ✅ Password reset links
- ✅ Login alerts with IP/time
- ✅ Account status changes

**NEVER send:**
- ❌ Patient names
- ❌ Medical records
- ❌ Diagnosis information
- ❌ Treatment details

### CAN-SPAM Compliance

All emails include:
- ✅ Valid sender address
- ✅ Accurate subject line
- ✅ Clear identification (automated message)
- ✅ Unsubscribe not required (transactional)

---

## 🎨 Customize Email Templates

### Edit HTML Templates

Located in `backend/email_service.py`:

```python
# Find the send_verification_email method
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Edit CSS here */
        .header {{ background-color: #0066cc; }}
        .button {{ background-color: #28a745; }}
    </style>
</head>
<body>
    <!-- Edit HTML here -->
</body>
</html>
"""
```

### Use External Templates

For advanced needs:
1. Create templates in Brevo dashboard
2. Use Brevo's template API
3. Pass template ID instead of HTML

---

## 📞 Support

### Brevo Support
- Email: support@brevo.com
- Documentation: https://developers.brevo.com
- Status page: https://status.brevo.com

### CipherCare Email Issues
1. Check `backend.log` for errors
2. Review Brevo dashboard statistics
3. Test with `backend/email_service.py` directly

---

## ✅ Verification Checklist

Before going live:

- [ ] Brevo account created
- [ ] API key added to `.env`
- [ ] Test email sent successfully
- [ ] Sender domain verified (production)
- [ ] SPF/DKIM records configured (production)
- [ ] Email templates reviewed
- [ ] Delivery monitoring set up
- [ ] Daily limit sufficient for usage
- [ ] Backup email service ready (optional)

---

## 🎉 You're All Set!

Your CipherCare application now has professional email capabilities powered by Brevo!

**Quick Test:**
```powershell
# Run setup
python setup_auth.py

# Should see: ✅ Brevo email service is configured
```

**Need Help?**
- Brevo docs: https://developers.brevo.com
- API reference: https://developers.brevo.com/reference
- CipherCare guide: AUTH_IMPLEMENTATION_GUIDE.md

**Happy emailing! 📧**
