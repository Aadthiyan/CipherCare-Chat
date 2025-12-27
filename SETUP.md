# Setup Guide

## Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Git

## 1. Environment Configuration

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

2.  Update `.env` with your credentials:
    - **DATABASE_URL**: Your Neon PostgreSQL connection string.
    - **CYBORGDB_API_KEY**: Your CyborgDB API key.
    - **CYBORGDB_CONNECTION_STRING**: Same as DATABASE_URL (usually).

## 2. Docker Services

Start the infrastructure (CyborgDB Service):

```bash
docker-compose up -d
```

## 3. Python Environment

Install dependencies:

```bash
pip install -r requirements.txt
```

(Note: `requirements.txt` will be populated in Phase 2)

## 4. Directory Structure

- `backend/`: FastAPI application
- `data-pipeline/`: Ingestion workflows
- `embeddings/`: Model scripts
- `frontend/`: React UI
- `docs/`: Documentation

## Troubleshooting

- **Database Connection**: Ensure the Neon URL includes `sslmode=require`.
- **CyborgDB**: Check if the API key is valid.
