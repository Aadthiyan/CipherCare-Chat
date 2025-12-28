# Vercel Environment Variables Setup

Add these environment variables in your Vercel project settings:
https://vercel.com/dashboard/[YOUR-TEAM]/[ciphercare-chat]/settings/environment-variables

## Required Variables:

AUTH0_DOMAIN=dev-1uff34efey2efv7j.us.auth0.com
AUTH0_CLIENT_ID=2GACR0k4usHACfvm7g1EPHVatAfY3Hwv
AUTH0_CLIENT_SECRET=vXC4JVer4iegW8gohYtcxsKCIMWoPdNIzZ5SiVwxT7EKfyo-_6GsCWCYpxGNHaav
AUTH0_SECRET=7ca67041764653551876543212345678
AUTH0_BASE_URL=https://ciphercare-chat.vercel.app
NEXT_PUBLIC_BACKEND_URL=https://ciphercare-chat.onrender.com

## Steps to add in Vercel Dashboard:

1. Go to your project: https://vercel.com/dashboard
2. Select the "ciphercare-chat" project
3. Go to Settings → Environment Variables
4. Add each variable above with the exact values
5. Make sure NEXT_PUBLIC_* variables are checked for all environments (Preview, Production, Development)
6. Redeploy the project for changes to take effect

## Note:
- Replace "https://ciphercare-chat.vercel.app" with your actual Vercel deployment URL if different
- AUTH0_BASE_URL must match your Vercel URL for Auth0 to work correctly
