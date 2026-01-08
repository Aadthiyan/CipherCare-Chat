"""
Generate embeddings locally and save to file
This is MUCH faster than using HF Inference API
"""

import json
import os
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np

print("🚀 CipherCare - Local Embedding Generator")
print("=" * 60)

# Load the same model that backend uses
print("\n📥 Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print("✅ Model loaded!")

# Load patient data
print("\n📂 Loading patient data...")
with open('synthea_structured_cipercare.json', 'r') as f:
    data = json.load(f)

records = data['records']
print(f"✅ Loaded {len(records)} records")

# Get unique patients
patient_ids = set(record.get('patient_id', '') for record in records)
print(f"✅ Found {len(patient_ids)} unique patients")

# Generate embeddings
print("\n🔄 Generating embeddings...")
print("   This will take ~20-30 minutes on your PC")
print("   (Much faster than 2-3 hours on Render!)")

embeddings_data = []

for i, record in enumerate(tqdm(records, desc="Processing")):
    # Create text for embedding (same as backend)
    text = f"{record.get('record_type', '')}: {record.get('display', '')} {record.get('description', '')}"
    
    # Generate embedding
    embedding = model.encode(text, show_progress_bar=False)
    
    # Prepare data structure
    embeddings_data.append({
        "id": str(record.get('record_id', f"record_{i}")),
        "patient_id": record.get('patient_id', ''),
        "vector": embedding.tolist(),  # Convert numpy to list
        "metadata": {
            "record_type": record.get('record_type', ''),
            "display": record.get('display', ''),
            "description": record.get('description', ''),
            "date": record.get('date', ''),
            "code": record.get('code', ''),
            "system": record.get('system', '')
        }
    })

# Save to file
print("\n💾 Saving embeddings to file...")
output_file = 'patient_embeddings.json'

with open(output_file, 'w') as f:
    json.dump({
        'total_records': len(embeddings_data),
        'total_patients': len(patient_ids),
        'embeddings': embeddings_data
    }, f)

file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"✅ Saved to {output_file} ({file_size_mb:.1f} MB)")

print("\n" + "=" * 60)
print("🎉 SUCCESS!")
print("=" * 60)
print(f"✅ Generated {len(embeddings_data)} embeddings")
print(f"✅ Saved to {output_file}")
print(f"\n📤 Next step: Run upload_precomputed_embeddings.py")
print("   This will upload to Render in ~5 minutes!")
