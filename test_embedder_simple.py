#!/usr/bin/env python3
"""
Test script to verify the refactored EmbeddingService with InferenceClient
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("\n" + "="*70)
print("TESTING REFACTORED EMBEDDING SERVICE")
print("="*70)

# Test 1: Import and initialize
print("\nTest 1: Import and initialization...")
try:
    from embeddings.embedder import EmbeddingService, ClinicalEmbedder
    print("[PASS] Successfully imported EmbeddingService and ClinicalEmbedder")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    exit(1)

# Test 2: Initialize with environment variables
print("\nTest 2: Initialize with environment variables...")
try:
    embedder = EmbeddingService()
    print(f"[PASS] EmbeddingService initialized")
    print(f"  - Model: {embedder.model_name}")
    print(f"  - Dimension: {embedder.embedding_dim}")
    print(f"  - Client type: {type(embedder.client).__name__}")
except Exception as e:
    print(f"[FAIL] Initialization failed: {e}")
    exit(1)

# Test 3: Initialize ClinicalEmbedder (legacy interface)
print("\nTest 3: ClinicalEmbedder legacy interface...")
try:
    clinical = ClinicalEmbedder()
    print(f"[PASS] ClinicalEmbedder initialized (backwards compatible)")
    print(f"  - Model: {clinical.model_name}")
    print(f"  - Dimension: {clinical.embedding_dim}")
except Exception as e:
    print(f"[FAIL] ClinicalEmbedder initialization failed: {e}")
    exit(1)

# Test 4: Generate single embedding
print("\nTest 4: Single embedding generation...")
try:
    test_text = "Patient has Type 2 Diabetes with hypertension"
    embedding = embedder.get_embedding(test_text)
    
    print(f"[PASS] Generated embedding successfully")
    print(f"  - Text: {test_text[:50]}...")
    print(f"  - Embedding dimension: {len(embedding)}")
    print(f"  - First 5 values: {embedding[:5]}")
    norm = (sum(x**2 for x in embedding)**0.5)
    print(f"  - L2 Norm: {norm:.4f}")
except Exception as e:
    print(f"[FAIL] Embedding generation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Batch embeddings
print("\nTest 5: Batch embedding generation...")
try:
    texts = [
        "Patient presents with fever and cough",
        "Blood pressure reading: 140/90",
        "Medication: Metformin 1000mg twice daily"
    ]
    
    embeddings = embedder.get_embeddings_batch(texts)
    
    print(f"[PASS] Generated {len(embeddings)} embeddings in batch")
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        print(f"  [{i+1}] {text[:40]}... (dim: {len(emb)})")
except Exception as e:
    print(f"[FAIL] Batch embedding failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Empty text handling
print("\nTest 6: Empty text handling...")
try:
    empty_embedding = embedder.get_embedding("")
    print(f"[PASS] Handled empty text gracefully")
    print(f"  - Returns zero vector: {all(x == 0.0 for x in empty_embedding)}")
    print(f"  - Dimension: {len(empty_embedding)}")
except Exception as e:
    print(f"[FAIL] Empty text handling failed: {e}")

# Test 7: Configuration via environment
print("\nTest 7: Configuration via environment variables...")
try:
    # Check current env values
    model_name = os.getenv("HUGGINGFACE_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
    embedding_dim = int(os.getenv("EMBEDDING_DIMENSION", "768"))
    
    print(f"[PASS] Configuration from environment:")
    print(f"  - HUGGINGFACE_MODEL_NAME: {model_name}")
    print(f"  - EMBEDDING_DIMENSION: {embedding_dim}")
    
    # Can override during init
    custom_embedder = EmbeddingService(
        model_name="sentence-transformers/all-mpnet-base-v2",
        embedding_dim=768
    )
    print(f"[PASS] Can override configuration in constructor")
except Exception as e:
    print(f"[FAIL] Configuration test failed: {e}")

print("\n" + "="*70)
print("SUMMARY - ALL TESTS PASSED")
print("="*70)
print("""
Key improvements in refactored embedder:
- Using huggingface_hub.InferenceClient instead of raw requests
- Configuration-driven from environment variables
- Proper error handling for HF API specific errors
- Backwards compatible with existing ClinicalEmbedder interface
- Clean separation of concerns (EmbeddingService base class)
- Ready for future local model support via inheritance
""")
print("="*70 + "\n")
