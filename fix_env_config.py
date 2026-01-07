"""
Quick fix script to update .env with correct CyborgDB URL
"""

import os
from pathlib import Path

# Determine which URL to use
print("=" * 70)
print("🔧 CyborgDB Configuration Fix")
print("=" * 70)

print("\nWhich environment are you configuring?")
print("1. Local development (CyborgDB running on localhost:8002)")
print("2. Render deployment (CyborgDB on Render)")
print("3. Hybrid (Backend on Render, CyborgDB local)")

choice = input("\nSelect option [1]: ").strip() or "1"

# URLs
LOCAL_URL = "http://localhost:8002"
RENDER_INTERNAL_URL = "http://ciphercare-cyborgdb:10000"  # Internal Render networking
RENDER_PUBLIC_URL = "https://cyborgdb-toj5.onrender.com"  # Public URL

if choice == "1":
    new_url = LOCAL_URL
    print(f"\n✓ Using LOCAL CyborgDB: {new_url}")
    print("\n⚠️  Make sure to start local CyborgDB:")
    print("   cyborgdb serve --port 8002")
    
elif choice == "2":
    new_url = RENDER_INTERNAL_URL
    print(f"\n✓ Using RENDER internal URL: {new_url}")
    print("\n⚠️  This is for backend deployed on Render")
    print("   The backend will connect to CyborgDB via internal networking")
    
elif choice == "3":
    new_url = RENDER_PUBLIC_URL
    print(f"\n✓ Using RENDER public URL: {new_url}")
    print("\n⚠️  This is for local backend connecting to Render CyborgDB")
    print("   Make sure your CyborgDB service is running on Render")
else:
    print("\n✗ Invalid choice, using local")
    new_url = LOCAL_URL

# Read current .env
env_file = Path(".env")
if not env_file.exists():
    print(f"\n✗ .env file not found at {env_file.absolute()}")
    print("   Creating new .env file...")
    env_content = f"CYBORGDB_BASE_URL={new_url}\n"
else:
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Update or add CYBORGDB_BASE_URL
    if "CYBORGDB_BASE_URL" in env_content:
        # Replace existing
        lines = env_content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith("CYBORGDB_BASE_URL"):
                new_lines.append(f"CYBORGDB_BASE_URL={new_url}")
                print(f"\n✓ Updated CYBORGDB_BASE_URL")
            else:
                new_lines.append(line)
        env_content = '\n'.join(new_lines)
    else:
        # Add new
        env_content += f"\nCYBORGDB_BASE_URL={new_url}\n"
        print(f"\n✓ Added CYBORGDB_BASE_URL")

# Write back
with open(env_file, 'w') as f:
    f.write(env_content)

print(f"\n✅ Configuration updated!")
print(f"   CYBORGDB_BASE_URL={new_url}")

# Next steps
print("\n" + "=" * 70)
print("📋 NEXT STEPS")
print("=" * 70)

if choice == "1":
    print("\n1. Start local CyborgDB:")
    print("   cyborgdb serve --port 8002")
    print("\n2. Upload data:")
    print("   python upload_to_render.py")
    print("\n3. Start backend:")
    print("   python run_backend.py")
    
elif choice == "2":
    print("\n1. This configuration is for Render deployment")
    print("   Your backend on Render will use this automatically")
    print("\n2. To upload data to Render CyborgDB:")
    print("   - Temporarily set CYBORGDB_BASE_URL to public URL")
    print("   - Run: python upload_to_render.py")
    print("   - Then change back to internal URL")
    
elif choice == "3":
    print("\n1. Verify Render CyborgDB is running:")
    print("   python diagnose_cyborgdb.py")
    print("\n2. Upload data:")
    print("   python upload_to_render.py")
    print("\n3. Start local backend:")
    print("   python run_backend.py")

print("\n" + "=" * 70)
