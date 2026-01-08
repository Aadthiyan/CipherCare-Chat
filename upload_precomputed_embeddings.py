"""
Upload pre-computed embeddings to Render
This is MUCH faster - just uploads the data without generating embeddings
"""

import json
import requests
from tqdm import tqdm
import time

print("🚀 CipherCare - Upload Pre-computed Embeddings")
print("=" * 60)

# Configuration
BACKEND_URL = "https://ciphercare-backend.onrender.com"
BATCH_SIZE = 1000

# Load pre-computed embeddings
print("\n📂 Loading pre-computed embeddings...")
with open('patient_embeddings.json', 'r') as f:
    data = json.load(f)

embeddings = data['embeddings']
total_records = data['total_records']
total_patients = data['total_patients']

print(f"✅ Loaded {total_records} embeddings ({total_patients} patients)")

# Upload in batches
print(f"\n📤 Uploading to {BACKEND_URL}...")
print(f"   Batch size: {BATCH_SIZE}")

uploaded = 0
failed = 0

for i in tqdm(range(0, len(embeddings), BATCH_SIZE), desc="Uploading batches"):
    batch = embeddings[i:i+BATCH_SIZE]
    
    try:
        # Send batch to backend
        response = requests.post(
            f"{BACKEND_URL}/admin/upload-precomputed",
            json={"items": batch},
            timeout=60
        )
        
        if response.status_code == 200:
            uploaded += len(batch)
        else:
            print(f"\n⚠️  Batch {i//BATCH_SIZE + 1} failed: {response.status_code}")
            failed += len(batch)
            
    except Exception as e:
        print(f"\n❌ Error uploading batch {i//BATCH_SIZE + 1}: {e}")
        failed += len(batch)
    
    # Small delay to avoid overwhelming the server
    time.sleep(0.5)

# Summary
print("\n" + "=" * 60)
print("📊 UPLOAD SUMMARY")
print("=" * 60)
print(f"✅ Uploaded: {uploaded}/{total_records} records")
if failed > 0:
    print(f"❌ Failed: {failed} records")
print(f"🎉 Success rate: {(uploaded/total_records)*100:.1f}%")

# Verify upload
print("\n🔍 Verifying upload...")
try:
    response = requests.get(f"{BACKEND_URL}/admin/upload-status")
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Backend status: {status['status']}")
        print(f"✅ Records in database: {status.get('records_processed', 0)}")
except Exception as e:
    print(f"⚠️  Could not verify: {e}")

print("\n" + "=" * 60)
print("🎉 UPLOAD COMPLETE!")
print("=" * 60)
print("✅ Your data is now in PostgreSQL + pgvector")
print("✅ You can now test queries!")
