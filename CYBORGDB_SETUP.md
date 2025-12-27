# CyborgDB Implementation Guide

## Overview

This project uses **PostgreSQL with pgvector** as the encrypted vector database for HIPAA-compliant patient record search. While we use the `cyborgdb` Python package for utility functions, the core implementation leverages PostgreSQL's native vector capabilities for production reliability.

## Architecture

### Database Schema

```sql
CREATE TABLE patient_embeddings (
    id UUID PRIMARY KEY,
    patient_id TEXT NOT NULL,
    embedding vector(768),           -- 768-dimensional vectors from all-mpnet-base-v2
    encrypted_metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_patient_id ON patient_embeddings(patient_id);
CREATE INDEX idx_embedding_cosine ON patient_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Data Flow

1. **Embedding Generation**: Patient records → Sentence Transformer → 768-dim vectors
2. **Encryption**: Metadata encrypted with AES-256
3. **Storage**: Vectors (plaintext for search) + Encrypted metadata in PostgreSQL
4. **Search**: Cosine similarity search on vectors
5. **Decryption**: Encrypted metadata decrypted only when needed

## Configuration

### Environment Variables (.env)

```bash
# Database (Required)
CYBORGDB_CONNECTION_STRING=postgresql://user:pass@host/db
CYBORGDB_API_KEY=your_cyborg_api_key

# Embedding Model (768-dimensional)
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# LLM Configuration
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
LLM_ANSWER_GENERATION_ENABLED=true
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.7
```

### Encryption Key

The system automatically generates and stores a 32-byte encryption key at `config/cyborg_index_key.bin`.

**⚠️ PRODUCTION WARNING**: In production, use:
- AWS KMS (Key Management Service)
- HashiCorp Vault
- Azure Key Vault
- Never commit the key file to git!

## API Usage

### Initialize Manager

```python
from backend.cyborg_manager import CyborgDBManager

manager = CyborgDBManager()
```

### Upsert Records

```python
# Single record
manager.upsert_patient_record(
    record_id="uuid-123",
    patient_id="P12345",
    embedding=[0.1, 0.2, ...],  # 768 dimensions
    encrypted_content={
        "ciphertext": "...",
        "iv": "...",
        "wrapped_key": "...",
        "algo": "AES-256-GCM"
    }
)

# Bulk upload from JSON
manager.upload_encrypted_data("embeddings/encrypted/vectors_enc.json")
```

### Search Records

```python
# Search with patient filter
results = manager.search(
    query_vec=[0.1, 0.2, ...],
    k=5,
    patient_id="P12345"
)

# Results format
[
    {
        "id": "uuid-123",
        "patient_id": "P12345",
        "metadata": {...},  # Encrypted
        "score": 0.95      # Cosine similarity
    }
]
```

### Utility Methods

```python
# Get patient record count
count = manager.get_patient_records_count("P12345")

# Get all patient IDs
patient_ids = manager.get_all_patient_ids()
```

## Performance Optimization

### IVFFlat Index

The system uses an **IVFFlat index** for fast approximate nearest neighbor search:

```sql
CREATE INDEX idx_embedding_cosine ON patient_embeddings 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);
```

**Parameters**:
- `lists`: Number of clusters (rule of thumb: rows/1000, max 1000)
- Adjust based on your dataset size

### Query Performance

- **Exact search**: O(n) linear scan
- **With IVFFlat**: O(log n) approximate search
- Trade-off: Speed vs. accuracy (typically 95%+ recall)

## Production Deployment Checklist

### Database Setup

- [ ] Enable pgvector extension: `CREATE EXTENSION vector;`
- [ ] Create table and indexes (see schema above)
- [ ] Set up connection pooling (recommended: PgBouncer)
- [ ] Configure SSL/TLS for connections

### Security

- [ ] Move encryption keys to KMS/Vault
- [ ] Enable database encryption at rest
- [ ] Set up audit logging for all vector queries
- [ ] Implement row-level security (RLS) for patient data
- [ ] Use IAM roles instead of password auth

### Monitoring

- [ ] Track query latency (target: <100ms)
- [ ] Monitor index performance
- [ ] Alert on encryption/decryption failures
- [ ] Log all patient data access (HIPAA requirement)

### Scaling

- [ ] Use read replicas for query scaling
- [ ] Consider partitioning by patient_id for large datasets
- [ ] Implement caching layer (Redis) for frequent queries
- [ ] Set up automated VACUUM and index maintenance

## CyborgDB Lite vs. Full

### Current Implementation (PostgreSQL + pgvector)
✅ **Recommended for production**
- Mature, battle-tested
- No vendor lock-in
- Cost-effective
- Full control over infrastructure

### CyborgDB Lite (Evaluation)
- Free for non-commercial use
- Good for rapid prototyping
- Limited to evaluation/testing
- Requires license for production

### CyborgDB Service (Future)
- Fully managed service
- Auto-scaling
- Multi-language SDKs
- Higher cost

## Troubleshooting

### Index Creation Fails

```sql
-- Check if extension is loaded
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Create extension if missing
CREATE EXTENSION IF NOT EXISTS vector;
```

### Slow Queries

```sql
-- Check if index is being used
EXPLAIN ANALYZE 
SELECT * FROM patient_embeddings 
ORDER BY embedding <=> '[0.1, 0.2, ...]' 
LIMIT 5;

-- Rebuild index if needed
REINDEX INDEX idx_embedding_cosine;
```

### Connection Issues

- Verify `CYBORGDB_CONNECTION_STRING` in .env
- Check SSL requirements (`sslmode=require`)
- Test connection: `psql $CYBORGDB_CONNECTION_STRING`

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [CyborgDB Official Docs](https://docs.cyborg.co/)
- [Sentence Transformers](https://www.sbert.net/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

## Support

For issues related to:
- **PostgreSQL/pgvector**: [pgvector GitHub](https://github.com/pgvector/pgvector/issues)
- **CyborgDB**: [CyborgDB Docs](https://docs.cyborg.co/)
- **This implementation**: Check `backend/cyborg_manager.py` comments
