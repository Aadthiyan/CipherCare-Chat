
# HIPAA-Compliant Encrypted Medical Chatbot

A privacy-preserving medical chatbot that enables clinicians to safely query patient Electronic Health Records (EHR) and FHIR data through encrypted vector search.

**Hackathon Sprint: Phase 1 - Foundation & Data Infrastructure**

## Live Demo : https://cipher-care.vercel.app/

## Overview
This project uses a Zero-Trust architecture where patient data is never persisted in plaintext. It uses CyborgDB for encrypted vector storage and retrieval.

## Quick Start

1.  **Setup Environment**:
    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

2.  **Run with Docker Compose**:
    ```bash
    docker-compose up -d
    ```

3.  **Ingest Data**:
    (Instructions coming in Phase 2)

## Documentation
- [Setup Guide](SETUP.md)
- [Architecture](docs/ARTCHITECTURE.md) (Coming soon)
