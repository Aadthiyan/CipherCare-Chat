"""
Test Frontend -> Backend connectivity
Checks configuration and connection
"""
import requests
import os
from dotenv import load_dotenv

# Load frontend .env.local
load_dotenv('frontend/.env.local')

def test_configuration():
    print("=" * 60)
    print("Configuration Check")
    print("=" * 60)
    
    backend_url = os.getenv('NEXT_PUBLIC_BACKEND_URL', 'http://localhost:8000')
    print(f"\n✓ Backend URL: {backend_url}")
    
    # Test backend health
    print("\n[1/3] Testing backend health endpoint...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Backend is UP and responding")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Backend returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to backend: {e}")
        return False
    
    # Test CORS preflight
    print("\n[2/3] Testing CORS configuration...")
    try:
        response = requests.options(
            f"{backend_url}/api/v1/query",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Authorization,Content-Type'
            },
            timeout=5
        )
        cors_headers = {
            k: v for k, v in response.headers.items() 
            if k.lower().startswith('access-control')
        }
        if cors_headers:
            print(f"✓ CORS headers present:")
            for header, value in cors_headers.items():
                print(f"  {header}: {value}")
        else:
            print(f"⚠ No CORS headers found (status: {response.status_code})")
    except Exception as e:
        print(f"✗ CORS test failed: {e}")
    
    # Test authentication flow
    print("\n[3/3] Testing authentication...")
    try:
        login_response = requests.post(
            f"{backend_url}/auth/login",
            json={"username": "attending", "password": "password123"},
            timeout=5
        )
        if login_response.status_code == 200:
            print(f"✓ Authentication working")
            token = login_response.json().get('access_token', '')[:30]
            print(f"  Token: {token}...")
        else:
            print(f"✗ Authentication failed: {login_response.status_code}")
            print(f"  {login_response.text}")
    except Exception as e:
        print(f"✗ Auth test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Configuration Check Complete!")
    print("=" * 60)
    print("\nNext step: Start frontend with 'npm run dev' in frontend/ folder")
    return True

if __name__ == "__main__":
    test_configuration()
