#!/usr/bin/env python3
"""Test querying the uploaded data from CyborgDB"""

import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager

load_dotenv()

# Initialize
embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
manager = CyborgLiteManager()

# Test query
query_text = "What conditions does the patient have?"
query_vector = embedder.encode(query_text).tolist()

print("\n=== CyborgDB Query Test ===\n")
print(f"Query: {query_text}")
print(f"Vector dimension: {len(query_vector)}\n")

# Search for patient P123
print("Searching for P123 records...")
results = manager.search(query_vector, k=3, patient_id="P123", collection="patient_embeddings")

print(f"\nFound {len(results)} records for P123:")
for i, result in enumerate(results, 1):
    metadata = result.get("metadata", {})
    print(f"\n{i}. {metadata.get('condition', 'Unknown')}")
    print(f"   Patient: {result.get('patient_id')}")
    print(f"   Status: {metadata.get('status')}")
    print(f"   Score: {result.get('score', 'N/A'):.4f}")

# Search for patient P456
print("\n\n" + "="*50)
print("Searching for P456 records...")
results = manager.search(query_vector, k=3, patient_id="P456", collection="patient_embeddings")

print(f"\nFound {len(results)} records for P456:")
for i, result in enumerate(results, 1):
    metadata = result.get("metadata", {})
    print(f"\n{i}. {metadata.get('condition', 'Unknown')}")
    print(f"   Patient: {result.get('patient_id')}")
    print(f"   Status: {metadata.get('status')}")
    print(f"   Score: {result.get('score', 'N/A'):.4f}")

print("\n\n=== Test Complete ===")
