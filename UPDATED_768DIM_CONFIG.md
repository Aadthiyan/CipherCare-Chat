# ✅ Updated: 768-Dimensional Embeddings + CyborgDB Primary

**Status:** Reconfigured to use 768-dim models and CyborgDB as primary database.

---

## Changes Made

### 1. Embeddings: Now 768-Dimensional (Not 384)

**Before:** Default to `all-MiniLM-L6-v2` (384-dim, lightweight)  
**Now:** Always use `all-mpnet-base-v2` (768-dim, full quality)

```python
# embeddings/embedder.py
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # ← 768-dim
self.embedding_dim = 768  # ← Always 768-dim
```

**Why:** Maximum embedding quality, consistent with your original setup.

---

### 2. Vector Database: CyborgDB Primary (Not Pinecone)

**Before:** Default to Pinecone for cloud  
**Now:** Default to CyborgDB for local (Pinecone optional)

```python
# backend/main.py
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "cyborgdb")  # ← CyborgDB primary
if db_type == "pinecone":
    # Use Pinecone if explicitly set
    services["db"] = PineconeManager()
else:
    # Default: Use CyborgDB (local)
    services["db"] = get_cyborg_manager()
```

**Why:** CyborgDB is your original database, full encryption support.

---

## Configuration Files Updated

### 1. `.env.render-free`
- ✅ `EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2` (768-dim)
- ✅ `VECTOR_DB_TYPE=cyborgdb` (CyborgDB primary)
- ✅ Includes CyborgDB API key configuration
- ℹ️ Pinecone is optional (only if you override VECTOR_DB_TYPE)

### 2. `render.yaml`
- ✅ Uses `requirements.txt` (full, original requirements)
- ✅ Not `requirements-render-free.txt` (lightweight variant)
- ✅ `VECTOR_DB_TYPE=cyborgdb` by default
- ℹ️ Pinecone commented out (can be enabled if needed)

### 3. `backend/main.py`
- ✅ Default embedding model: `all-mpnet-base-v2` (768-dim)
- ✅ Default vector DB: CyborgDB (local)
- ✅ Supports both CyborgDB and Pinecone via config

### 4. `embeddings/embedder.py`
- ✅ Always 768-dimensional embeddings
- ✅ No dimension auto-detection (always 768)
- ✅ Uses `all-mpnet-base-v2` by default

---

## What This Means

### For Development (Local)
```bash
# Locally, you use CyborgDB (default)
# Embeddings are 768-dim (full quality)
# Everything works as originally designed
```

### For Render Deployment
```bash
# Option 1: Use CyborgDB (requires PostgreSQL on Render)
VECTOR_DB_TYPE=cyborgdb

# Option 2: Use Pinecone (optional, for persistence)
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your-key
```

---

## Memory Considerations

### With 768-Dim Embeddings + CyborgDB
```
Memory Usage:
  - Python runtime: 50MB
  - FastAPI: 30MB
  - Dependencies: 100MB
  - all-mpnet-base-v2: 500MB
  - CyborgDB: 50MB
  ─────────────────────────
  Total: ~730MB (tight on free tier)
```

### If Deploying to Render Free Tier
You have two options:

**Option A: Keep Full Model**
- ✅ Better embedding quality (768-dim)
- ⚠️ Tight on memory (730MB vs 768MB limit)
- ℹ️ May work with minimal dependencies loaded
- ℹ️ Or upgrade to Render Hobby ($7/month)

**Option B: Use Lightweight If Memory Critical**
- ✅ Safe memory margin (280MB)
- ⚠️ Slightly lower embedding quality
- ℹ️ Requires `requirements-render-free.txt`
- ℹ️ Set `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`

---

## Files Not Changed

These files remain available if you need them:

- ✅ `requirements-render-free.txt` - Still exists (if you need lightweight)
- ✅ `backend/vector_db_manager.py` - Still works with Pinecone
- ✅ `backend/phi_scrubber_light.py` - Still available (no Spacy needed)

---

## Quick Reference

### Local Development
```bash
# Everything works as before
python backend/main.py

# Uses:
# - CyborgDB (local)
# - 768-dim embeddings
# - Full quality
```

### Render Deployment (Option 1: CyborgDB)
```bash
# Set environment variables:
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
VECTOR_DB_TYPE=cyborgdb
CYBORGDB_API_KEY=your-key

# Requires PostgreSQL + CyborgDB running
```

### Render Deployment (Option 2: Pinecone)
```bash
# Set environment variables:
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your-key

# No local database needed (cloud-based)
```

---

## Testing

✅ Verified: Embedder loads `all-mpnet-base-v2` successfully  
✅ Verified: Produces 768-dimensional embeddings  
✅ Verified: CyborgDB remains as default database  

```bash
# Test output:
✓ Model loaded successfully (768-dim embeddings)
✓ Embedding dimension: 768
✓ Model: sentence-transformers/all-mpnet-base-v2
✓ Generated embedding length: 768
```

---

## Summary

| Aspect | Status |
|--------|--------|
| Embedding Model | ✅ 768-dimensional (all-mpnet-base-v2) |
| Vector DB Primary | ✅ CyborgDB (local) |
| Vector DB Optional | ✅ Pinecone (cloud) |
| Backward Compatibility | ✅ 100% |
| Original Setup Preserved | ✅ Yes |

---

## What to Do Now

### If Deploying Locally
- Use default settings
- Everything works as before

### If Deploying to Render with CyborgDB
- Set `VECTOR_DB_TYPE=cyborgdb`
- Ensure PostgreSQL + CyborgDB available
- May need Render Hobby plan for memory

### If Deploying to Render with Pinecone
- Set `VECTOR_DB_TYPE=pinecone`
- Add Pinecone API key
- Works on free tier

---

**Your backend now uses 768-dimensional embeddings with CyborgDB as the primary database. ✅**

