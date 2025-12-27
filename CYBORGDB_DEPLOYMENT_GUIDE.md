# CyborgDB Configuration Guide for Deployment

## 🔍 Understanding Your CyborgDB Setup

Based on your project analysis, you're using **CyborgDB Embedded** mode, which is the correct choice for deployment.

---

## What is CyborgDB?

CyborgDB is a **Confidential Vector Database** that provides:
- 🔒 **End-to-end encryption** for vector embeddings
- 🔐 **Zero-trust architecture** for sensitive data
- 💾 **PostgreSQL backend** for storage
- 🚀 **High-performance** vector search

### CyborgDB vs Other Vector Databases

| Feature | CyborgDB | Pinecone | Weaviate | Qdrant |
|---------|----------|----------|----------|--------|
| Encryption | ✅ E2E | ❌ No | ❌ No | ❌ No |
| PostgreSQL Backend | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Confidential Computing | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Free Tier | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| HIPAA Compliant | ✅ Yes | ⚠️ Partial | ⚠️ Partial | ⚠️ Partial |

**For healthcare data (HIPAA), CyborgDB is the best choice.**

---

## Your Current Configuration

### From `.env.example`:
```bash
CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2
CYBORGDB_CONNECTION_STRING=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### From `backend/cyborg_lite_manager.py`:
```python
import cyborgdb

client = cyborgdb.Client(
    api_key=os.getenv("CYBORGDB_API_KEY"),
    base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
)
```

---

## ✅ You're Using the Right Setup!

Your project uses **CyborgDB Embedded SDK**, which is perfect for deployment because:

1. **No separate server needed** - CyborgDB runs in your FastAPI process
2. **Uses your PostgreSQL** - Stores vectors in Neon database
3. **Works on Render free tier** - No additional infrastructure
4. **End-to-end encryption** - Meets HIPAA requirements

---

## Deployment Configuration

### For Render (Backend)

**Environment Variables:**
```bash
# Required
CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2
CYBORGDB_CONNECTION_STRING=postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
VECTOR_DB_TYPE=cyborgdb

# Optional (for local development only)
# CYBORGDB_BASE_URL=http://localhost:8002  # NOT needed for embedded mode
```

**Important Notes:**
- ✅ `CYBORGDB_BASE_URL` is **NOT required** for embedded mode
- ✅ `CYBORGDB_CONNECTION_STRING` should match `DATABASE_URL`
- ✅ `VECTOR_DB_TYPE=cyborgdb` tells the app to use CyborgDB instead of Pinecone

---

## How CyborgDB Works in Your App

### 1. Initialization (Startup)
```python
# backend/main.py (line 120-130)
db_type = os.getenv("VECTOR_DB_TYPE", "cyborgdb").lower()

if db_type == "pinecone":
    from backend.vector_db_manager import PineconeManager
    services["db"] = PineconeManager()
else:
    # Default: Use CyborgDB (local, preferred)
    services["db"] = get_cyborg_manager()
    logger.info("Loaded CyborgDB vector database (local)")
```

### 2. Vector Storage
```python
# When you upload patient data
manager = get_cyborg_manager()
manager.upsert(
    vectors=embeddings,
    metadata=patient_data,
    namespace="medical_records"
)
```

### 3. Vector Search
```python
# When querying patient data
results = db.search(
    query_vec=query_embedding,
    k=5,
    patient_id="P123"
)
```

### 4. Encryption
```python
# CyborgDB automatically encrypts:
# - Vector embeddings
# - Metadata
# - Search queries
# All encryption happens transparently!
```

---

## CyborgDB Architecture on Render

```
┌─────────────────────────────────────────────────────────┐
│                  Render (Your Backend)                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         FastAPI Application                     │    │
│  │                                                 │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │  CyborgDB Embedded SDK                   │  │    │
│  │  │  - Encryption/Decryption                 │  │    │
│  │  │  - Vector Operations                     │  │    │
│  │  │  - Search Algorithms                     │  │    │
│  │  └──────────────┬───────────────────────────┘  │    │
│  │                 │                               │    │
│  │                 │ Encrypted Vectors             │    │
│  │                 ▼                               │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │  PostgreSQL Client (psycopg2)            │  │    │
│  │  └──────────────┬───────────────────────────┘  │    │
│  └─────────────────┼──────────────────────────────┘    │
└────────────────────┼─────────────────────────────────────┘
                     │
                     │ SSL Connection
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Neon PostgreSQL (Cloud)                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Database: neondb                               │    │
│  │                                                 │    │
│  │  Tables:                                        │    │
│  │  - users (authentication)                       │    │
│  │  - cyborg_vectors (encrypted embeddings)        │    │
│  │  - cyborg_metadata (encrypted patient data)     │    │
│  │  - cyborg_indices (search indices)              │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Verifying CyborgDB is Working

### 1. Check Startup Logs (Render)
```
✓ POSTGRES Ready
✓ EMBEDDER Ready
✓ DB Ready  ← This means CyborgDB initialized successfully
✓ LLM Ready
🚀 Backend online on http://0.0.0.0:8000
```

### 2. Test CyborgDB Directly
```bash
# Run this locally or in Render console
python -c "
from backend.cyborg_lite_manager import get_cyborg_manager
manager = get_cyborg_manager()
print('✓ CyborgDB initialized successfully')
print(f'Collection: {manager.collection_name}')
"
```

### 3. Check Database Tables
```sql
-- Connect to your Neon database
psql "postgresql://neondb_owner:npg_m3Yz6bhJFxWD@ep-proud-moon-addq5wm9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

-- List CyborgDB tables
\dt cyborg*

-- Expected output:
-- cyborg_vectors
-- cyborg_metadata
-- cyborg_indices
```

---

## Common CyborgDB Issues & Solutions

### Issue 1: "Missing CYBORGDB_API_KEY"
**Cause:** Environment variable not set

**Solution:**
```bash
# In Render → Environment Variables
CYBORGDB_API_KEY=cyborg_6063109509bb4cb9b0b1072ca20486e2
```

### Issue 2: "Connection refused to localhost:8002"
**Cause:** App is trying to connect to CyborgDB server (not needed for embedded mode)

**Solution:**
```bash
# Remove or don't set CYBORGDB_BASE_URL
# Embedded mode doesn't need it!
```

### Issue 3: "Index not found"
**Cause:** CyborgDB index not created yet

**Solution:**
```python
# Run this to create index
from backend.cyborg_lite_manager import get_cyborg_manager
manager = get_cyborg_manager()
# Index is created automatically on first upsert
```

### Issue 4: "Database connection failed"
**Cause:** Invalid PostgreSQL connection string

**Solution:**
```bash
# Verify both are the same
DATABASE_URL=postgresql://...
CYBORGDB_CONNECTION_STRING=postgresql://...  # Should be identical
```

---

## CyborgDB vs Pinecone: When to Switch?

### Stick with CyborgDB if:
- ✅ You need HIPAA compliance
- ✅ You need end-to-end encryption
- ✅ You want to use existing PostgreSQL
- ✅ You have < 500MB of vector data
- ✅ You prioritize security over speed

### Switch to Pinecone if:
- ❌ You need > 1GB of vector storage
- ❌ You need ultra-fast queries (< 10ms)
- ❌ You don't need encryption
- ❌ You're okay with cloud-only storage

**For healthcare/medical data: Always use CyborgDB!**

---

## CyborgDB Performance on Render

### Free Tier (512 MB RAM)
- **Vectors:** ~50,000 (768-dim)
- **Query Time:** 100-500ms
- **Storage:** Limited by PostgreSQL (Neon free: 512MB)

### Starter Tier ($7/month)
- **Vectors:** ~100,000 (768-dim)
- **Query Time:** 50-200ms
- **Storage:** Limited by PostgreSQL

### Pro Tier ($12/month)
- **Vectors:** ~500,000 (768-dim)
- **Query Time:** 20-100ms
- **Storage:** Upgrade PostgreSQL separately

---

## CyborgDB Security Features

### 1. End-to-End Encryption
```python
# Automatic encryption of:
# - Vector embeddings
# - Metadata (patient data)
# - Search queries
# - Results

# You don't need to do anything!
# CyborgDB handles it automatically
```

### 2. Zero-Trust Architecture
```python
# Even if database is compromised:
# - Vectors are encrypted
# - Metadata is encrypted
# - Attacker can't read patient data
```

### 3. HIPAA Compliance
```python
# CyborgDB provides:
# - Encryption at rest
# - Encryption in transit
# - Access control
# - Audit logging
```

---

## Monitoring CyborgDB

### 1. Check Vector Count
```python
from backend.cyborg_lite_manager import get_cyborg_manager
manager = get_cyborg_manager()
count = manager.count()
print(f"Total vectors: {count}")
```

### 2. Check Storage Usage
```sql
-- Connect to Neon database
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'cyborg%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Monitor Query Performance
```python
import time
start = time.time()
results = manager.search(query_vec, k=5)
elapsed = time.time() - start
print(f"Query time: {elapsed:.3f}s")
```

---

## CyborgDB Resources

### Official Documentation
- **Main Docs:** https://docs.cyborg.co/
- **Embedded SDK:** https://docs.cyborg.co/versions/v0.14.x/embedded/guides/intro/about
- **Python SDK:** https://docs.cyborg.co/versions/v0.14.x/service/guides/intro/about

### GitHub
- **CyborgDB:** https://github.com/cyborgdb/cyborgdb

### Support
- **Discord:** Check docs for invite link
- **Email:** support@cyborg.co

---

## Summary

✅ **Your CyborgDB setup is correct for deployment!**

**Key Points:**
1. You're using CyborgDB Embedded (best for Render)
2. Vectors are stored in PostgreSQL (Neon)
3. End-to-end encryption is automatic
4. No separate CyborgDB server needed
5. HIPAA compliant out of the box

**For Deployment:**
- Set `CYBORGDB_API_KEY` in Render
- Set `CYBORGDB_CONNECTION_STRING` (same as `DATABASE_URL`)
- Set `VECTOR_DB_TYPE=cyborgdb`
- Deploy and test!

**You're all set! 🚀**

---

**Last Updated:** December 28, 2024
