# System Architecture

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    User[Clinician / User] -->|HTTPS| Frontend[Frontend UI (React)]
    Frontend -->|REST API| Backend[Backend API (FastAPI)]
    
    subgraph "Trust Boundary: Secure VPC"
        Backend -->|Auth Check| AuthProvider[Auth0 / Cognito]
        
        subgraph "Data Pipeline"
            Ingestion[Ingestion Service] -->|Raw Data| DeID[De-Identification (Presidio)]
            DeID -->|De-ID Text| EmbedModel[Embedding Model (BioBERT)]
            EmbedModel -->|Plain Vector| Encrypt[Encryption Service (AES-GCM)]
        end
        
        Backend -->|Query| LLM[Private LLM (Llama 2 / GPT-NeoX)]
        Backend -->|Audit| AuditLog[Audit Log DB (Postgres)]
        
        Encrypt -->|Encrypted Vector| CyborgDB[(CyborgDB)]
        Backend -->|Search (Encrypted)| CyborgDB
        
        KeyManager[KMS / Vault] -->|Keys| Encrypt
        KeyManager -->|Keys| Backend
    end
    
    Source[EHR / FHIR Server] -->|Sensitive Data| Ingestion
```

## 2. Core Components

| Component | Responsibility | Tech Stack |
|:---|:---|:---|
| **Frontend** | User Interface for querying and viewing results | React, Tailwind |
| **Backend API** | Orchestrates requests, auth, and logic | FastAPI, Python |
| **Ingestion** | ETL pipeline for EHR data | Python (Prefect/Scripts) |
| **De-Identification** | Removes PHI from text | Presidio, spaCy |
| **Embedding Model** | Converts text to vectors | BioBERT / ClinicalBERT |
| **Encryption Service** | Encrypts vectors and metadata | AES-256-GCM |
| **CyborgDB** | Stores encrypted vectors & performs search | CyborgDB (Postgres-based) |
| **Private LLM** | Generates answers (No external data sent) | Llama 2 / GPT-J |
| **Key Manager** | Manages encryption keys securely | AWS KMS / Vault (Simulated) |
| **Audit Log** | Records all access and queries | PostgreSQL |

## 3. Data Flow Workflows

### A. Data Ingestion & Indexing
1.  **Extract**: Ingestion service pulls FHIR resources from source.
2.  **De-Identify**: `[Raw Text] -> Presidio -> [De-ID Text]`
3.  **Embed**: `[De-ID Text] -> BioBERT -> [Vector]`
4.  **Encrypt**: `[Vector] + [Metadata] + [Key] -> AES-GCM -> [Ciphertext]`
5.  **Store**: `[Ciphertext]` is stored in CyborgDB.
    *   *Security*: Plaintext PHI never leaves the memory of the ingestion process.

### B. Encrypted Query
1.  **Auth**: User authenticates via Frontend -> Backend.
2.  **Query Processing**: 
    - User asks: "How is the patient's diabetes?"
    - Backend generates query embedding (Plantext vector of query).
3.  **Search**:
    - Backend sends query vector to CyborgDB.
    - CyborgDB performs encrypted similarity search.
    - Returns **Encrypted** results.
4.  **Decryption**:
    - Backend retrieves keys from Key Manager.
    - Decrypts results in-memory.
5.  **Generation**:
    - Decrypted context + Query sent to Private LLM.
    - LLM generates response.
6.  **Response**: Answer sent to Frontend.

## 4. Security Boundaries

*   **Public Zone**: Frontend (Browser).
*   **DMZ**: Backend API (exposed via HTTPS).
*   **Secure Zone (Private Subnet)**:
    - **CyborgDB**: Only accepts connections from Backend.
    - **LLM Service**: Only accepts connections from Backend.
    - **Key Manager**: Strictly controlled access.
    - **Audit Log**: Append-only access.

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|:---|:---|:---|
| **Key Leakage** | Determining factors could decrypt all data | Rotate keys quarterly; Use HSM/KMS; Never log keys. |
| **Model Inversion** | Reconstructing text from vectors | Vectors are encrypted; Access controls preventing bulk retrieval. |
| **LLM Hallucination** | Incorrect medical advice | Strict prompt engineering; "Draft only" watermarks; Citations required. |
| **PHI Leakage in Logs** | Compliance violation | Scrub logs; Audit log contains only IDs, not clinical text. |

## 6. API Interfaces

### `POST /api/v1/query`
- **Input**: `{ "query": "string", "patient_id": "uuid" }`
- **Headers**: `Authorization: Bearer <token>`
- **Output**: `{ "answer": "string", "sources": [ { "id": "...", "score": 0.95 } ] }`

### `POST /api/v1/ingest` (Admin)
- **Input**: `{ "source_path": "string" }`
- **Output**: `{ "status": "started", "job_id": "uuid" }`

