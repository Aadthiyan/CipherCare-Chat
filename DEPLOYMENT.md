# Deployment Guide

## Local Deployment (Docker)
1.  **Build**: `docker-compose build`
2.  **Run**: `docker-compose up -d`
3.  **Access**: Frontend at `http://localhost:3000`, API at `http://localhost:8000`.

## Production Deployment (Hypothetical)

### 1. Database
- Provision PostgreSQL (e.g., Neon or AWS RDS).
- Apply migrations: `alembic upgrade head`.

### 2. Backend
- Deploy FastAPI container to AWS ECS or Kubernetes.
- Inject secrets via AWS Secrets Manager.
- Ensure connectivity to CyborgDB instance.

### 3. Frontend
- Build static assets: `npm run build`.
- Deploy to AWS S3/CloudFront or Vercel.

### 4. Key Management
- Ensure production keys are strictly managed in KMS/Vault.
- **NEVER** commit prod keys to the repo.
