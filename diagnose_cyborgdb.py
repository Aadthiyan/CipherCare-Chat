"""
Diagnostic script to check CyborgDB deployment status and data
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

# Configuration
CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL", "https://cyborgdb-toj5.onrender.com")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print("=" * 70)
print("🔍 CyborgDB Deployment Diagnostics")
print("=" * 70)

# 1. Check environment variables
print("\n1. Environment Variables:")
print(f"   CYBORGDB_BASE_URL: {CYBORGDB_URL}")
print(f"   CYBORGDB_API_KEY: {'✓ Set' if CYBORGDB_API_KEY else '✗ Missing'}")

# 2. Check if CyborgDB service is reachable
print("\n2. Service Reachability:")
try:
    # Try health endpoint
    health_url = f"{CYBORGDB_URL}/health"
    print(f"   Testing: {health_url}")
    response = requests.get(health_url, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
    
    if response.status_code == 200:
        print("   ✓ CyborgDB service is UP")
    elif response.status_code == 502:
        print("   ✗ 502 Bad Gateway - Service is DOWN or not deployed correctly")
    else:
        print(f"   ⚠ Unexpected status: {response.status_code}")
        
except requests.exceptions.Timeout:
    print("   ✗ Request timed out - service may be starting or down")
except requests.exceptions.ConnectionError as e:
    print(f"   ✗ Connection error: {str(e)[:100]}")
except Exception as e:
    print(f"   ✗ Error: {str(e)[:100]}")

# 3. Try to list indexes
print("\n3. Index Status:")
if CYBORGDB_API_KEY:
    try:
        headers = {"Authorization": f"Bearer {CYBORGDB_API_KEY}"}
        indexes_url = f"{CYBORGDB_URL}/v1/indexes"
        print(f"   Testing: {indexes_url}")
        response = requests.get(indexes_url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Indexes found: {data}")
            except:
                print(f"   Response: {response.text[:200]}")
        elif response.status_code == 502:
            print("   ✗ 502 Bad Gateway - Cannot access indexes")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ✗ Error: {str(e)[:100]}")
else:
    print("   ✗ Skipped - API key not set")

# 4. Check local data file
print("\n4. Local Data File:")
data_file = "synthea_structured_cipercare.json"
if os.path.exists(data_file):
    file_size = os.path.getsize(data_file) / (1024 * 1024)  # MB
    print(f"   ✓ Found: {data_file} ({file_size:.1f} MB)")
    
    # Count records
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        print(f"   Records: {len(data)}")
        
        # Show sample
        if len(data) > 0:
            sample = data[0]
            print(f"   Sample keys: {list(sample.keys())[:5]}")
    except Exception as e:
        print(f"   ⚠ Could not read file: {str(e)[:100]}")
else:
    print(f"   ✗ Not found: {data_file}")

# 5. Recommendations
print("\n" + "=" * 70)
print("📋 DIAGNOSIS & RECOMMENDATIONS")
print("=" * 70)

if CYBORGDB_API_KEY:
    print("\n✓ API Key is configured")
else:
    print("\n✗ CRITICAL: CYBORGDB_API_KEY is missing in .env")
    print("  Action: Add CYBORGDB_API_KEY to your .env file")

print("\n🔧 Next Steps:")
print("\n1. Check Render Dashboard:")
print("   - Go to https://dashboard.render.com")
print("   - Find your 'cyborgdb' web service")
print("   - Check if it's running or crashed")
print("   - Review the logs for errors")

print("\n2. If service is DOWN:")
print("   - The service may have crashed due to memory limits")
print("   - Check Render logs for out-of-memory errors")
print("   - You may need to upgrade to a paid plan for more RAM")

print("\n3. If service is UP but returning 502:")
print("   - The service may not be binding to the correct port")
print("   - Check that your CyborgDB service uses PORT from environment")
print("   - Verify the service is listening on 0.0.0.0:$PORT")

print("\n4. Data Upload:")
print("   - Even if service is up, you need to upload data first")
print("   - Run: python upload_to_render.py")
print("   - This will populate the CyborgDB with patient records")

print("\n5. Alternative - Use Local CyborgDB:")
print("   - If Render free tier doesn't work, run CyborgDB locally")
print("   - Set CYBORGDB_BASE_URL=http://localhost:8002")
print("   - Start local CyborgDB service")

print("\n" + "=" * 70)
