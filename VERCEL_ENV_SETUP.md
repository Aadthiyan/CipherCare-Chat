# Vercel Environment Variables Setup Guide

## Critical: Your deployment is failing because environment variables are not configured in Vercel!

### Step-by-Step Setup:

#### 1. Go to Vercel Dashboard
- Visit: https://vercel.com/dashboard
- Select your "ciphercare-chat" project (or the Vercel project name)

#### 2. Navigate to Settings → Environment Variables
- Click on "Settings" tab
- Scroll down to "Environment Variables"

#### 3. Add These Variables (Copy & Paste Exactly):

| Variable Name | Value | Environment |
|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `https://ciphercare-chat.onrender.com` | All (Preview, Production, Development) |
| `AUTH0_DOMAIN` | `dev-1uff34efey2efv7j.us.auth0.com` | All |
| `AUTH0_CLIENT_ID` | `2GACR0k4usHACfvm7g1EPHVatAfY3Hwv` | All |
| `AUTH0_CLIENT_SECRET` | `vXC4JVer4iegW8gohYtcxsKCIMWoPdNIzZ5SiVwxT7EKfyo-_6GsCWCYpxGNHaav` | Production only |
| `AUTH0_SECRET` | `7ca67041764653551876543212345678` | Production only |
| `AUTH0_BASE_URL` | `https://ciphercare-chat.vercel.app` | Production only |

**Important**: Make sure `NEXT_PUBLIC_BACKEND_URL` is available in ALL environments (Preview, Production, Development) because it starts with `NEXT_PUBLIC_`

#### 4. Verify Auth0 Configuration
Go to your Auth0 dashboard (https://manage.auth0.com):
- Select your application
- Go to Settings
- Add to "Allowed Callback URLs": `https://ciphercare-chat.vercel.app/api/auth/callback`
- Add to "Allowed Logout URLs": `https://ciphercare-chat.vercel.app`
- Click Save

#### 5. Redeploy
After adding environment variables:
1. Go back to your Vercel project
2. Click "Deployments"
3. Find the latest failed deployment
4. Click the three dots (•••) menu
5. Select "Redeploy" 
   - **OR** Push a new commit to trigger automatic redeploy

#### 6. Verify Deployment
- Wait for the build to complete (should be green checkmark)
- Visit: `https://ciphercare-chat.vercel.app`
- Try to sign up - it should now connect to your Render backend

### Troubleshooting:

**Still getting ERR_CONNECTION_REFUSED?**
- Make sure `NEXT_PUBLIC_BACKEND_URL` matches your Render deployment URL exactly
- Check that your Render backend is still running: `https://ciphercare-chat.onrender.com/api/v1/health`

**Auth0 errors?**
- Verify `AUTH0_CLIENT_ID` and `AUTH0_DOMAIN` are correct
- Make sure callback URL is added to Auth0 settings
- Note: `AUTH0_BASE_URL` MUST be your Vercel production URL

**Build fails after adding variables?**
- Clear Vercel cache: Project Settings → Git → Ignore Build Cache (toggle)
- Redeploy

